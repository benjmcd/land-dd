from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import UUID, uuid5

from app.connectors.license_guard import check_connector_source_license
from app.connectors.observability import (
    ConnectorEventType,
    ConnectorObservabilityEvent,
    ConnectorRunObservabilityLog,
    new_observability_log,
)
from app.connectors.policy import ConnectorPolicy
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)

EPA_ECHO_CONNECTOR_NAME = "epa_echo_live"
EPA_ECHO_METHOD_CODE = "live_epa_echo_frs_facility_screen"
EPA_ECHO_METHOD_VERSION = "0.1.0"
EPA_FRS_REST_URL = "https://ofmpub.epa.gov/frs_public2/frs_rest_services.get_facilities"
EPA_ECHO_MAX_BBOX_DEGREES = 0.5
EPA_ECHO_SPATIAL_PRECISION_METERS = 500.0
EPA_ECHO_CAVEAT = (
    "EPA ECHO facility-proximity screening only. A nearby regulated facility does not "
    "prove subject-property contamination, plume extent, exposure pathway, or legal "
    "liability. ECHO reflects records in EPA program databases; unreported or "
    "non-federally-regulated releases are outside scope. ECHO data may lag source "
    "entry by one week to three months. EPA warrants no accuracy, completeness, or "
    "currency of ECHO data. A Phase I/II ESA is required for regulatory and "
    "transactional environmental due diligence. Data: U.S. Environmental Protection "
    "Agency / ECHO (echo.epa.gov); cite facility IDs, retrieval date, and ECHO "
    "data-refresh date with every use."
)

_NAMESPACE = UUID("b4e2c7a1-5d3f-4b19-8e06-2a9d7c4f1b82")

JsonFetcher = Callable[[str, float], Mapping[str, object]]


class EpaEchoConnectorError(ValueError):
    """Raised when an EPA ECHO connector request is invalid before source I/O."""


@dataclass(frozen=True)
class EpaEchoBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise EpaEchoConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise EpaEchoConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise EpaEchoConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise EpaEchoConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > EPA_ECHO_MAX_BBOX_DEGREES:
            raise EpaEchoConnectorError("bbox longitude span exceeds EPA ECHO limit")
        if self.ymax - self.ymin > EPA_ECHO_MAX_BBOX_DEGREES:
            raise EpaEchoConnectorError("bbox latitude span exceeds EPA ECHO limit")

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"

    @property
    def bbox_str(self) -> str:
        return f"{self.xmin:.6f},{self.ymin:.6f},{self.xmax:.6f},{self.ymax:.6f}"


@dataclass(frozen=True)
class EpaEchoConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class EpaEchoConnector:
    """Bounded EPA ECHO FRS facility-proximity screening connector.

    Queries the EPA Facility Registry Service REST API for regulated facilities
    within a search radius derived from a bounding box. Emits source-failure
    evidence for network errors or malformed responses so a missing result never
    becomes an implicit 'no hazard found' conclusion.
    """

    connector_name = EPA_ECHO_CONNECTOR_NAME
    domain = "env_hazard"

    def __init__(
        self,
        *,
        source: SourceContract,
        fetch_json: JsonFetcher | None = None,
        policy: ConnectorPolicy | None = None,
    ) -> None:
        self._source = source
        self._fetch_json = fetch_json or _fetch_json
        self._policy = policy or ConnectorPolicy(
            rate_limit_per_minute=3,
            timeout_seconds=30.0,
            max_retries=0,
            retry_backoff_seconds=0.0,
        )

    def query_bbox(
        self,
        *,
        area_id: UUID,
        bbox: EpaEchoBbox,
    ) -> EpaEchoConnectorResult:
        log = new_observability_log()
        started_at = _utcnow()
        center_lat, center_lon, radius_miles = _bbox_center_and_radius_miles(bbox)
        ingest_run_id = _stable_uuid(
            "retrieval",
            str(self._source.metadata.get("source_registry_id", "")),
            str(area_id),
            bbox.fingerprint,
        )
        request_url = _build_query_url(
            lat=center_lat,
            lon=center_lon,
            radius_miles=radius_miles,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_started,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message="starting EPA ECHO FRS facility proximity query",
                timestamp=started_at,
            )
        )

        check_connector_source_license(self._source)

        try:
            payload = self._fetch_json(request_url, self._policy.timeout_seconds)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="epa_echo_request_error",
                error_message=str(exc),
                retryable=True,
            )

        results = payload.get("Results")
        if not isinstance(results, Mapping):
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="epa_echo_malformed_response",
                error_message="EPA FRS response missing 'Results' object",
                retryable=True,
            )

        facility_count = _parse_facility_count(results)
        has_proximity = facility_count > 0
        finished_at = _utcnow()

        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=facility_count,
            error_count=0,
            warning_count=0,
            log_uri=request_url,
            metrics={
                "source_registry_id": self._source.metadata.get("source_registry_id"),
                "regulated_facility_count": facility_count,
                "center_lat": center_lat,
                "center_lon": center_lon,
                "radius_miles": radius_miles,
                "accessed_at": finished_at.isoformat(),
            },
        )

        if has_proximity:
            confidence = ConfidenceBand.MEDIUM
            observed_value: dict[str, object] = {
                "has_env_hazard_proximity": True,
                "env_hazard_status": "regulated_facilities_found",
                "regulated_facility_count": facility_count,
                "epa_echo_bbox": bbox.bbox_str,
            }
            observation = (
                f"EPA ECHO FRS query found {facility_count} regulated "
                "facility/facilities in proximity to the query area."
            )
            evidence_code = "ENV_HAZ_FACILITY_SCREEN"
        else:
            confidence = ConfidenceBand.LOW
            observed_value = {
                "no_env_hazard_proximity": True,
                "env_hazard_status": "no_regulated_facilities_found",
                "regulated_facility_count": 0,
                "epa_echo_bbox": bbox.bbox_str,
            }
            observation = "EPA ECHO FRS query found no regulated facilities in proximity to the query area."
            evidence_code = "ENV_HAZ_FACILITY_SCREEN"

        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(self._source.metadata.get("source_registry_id", "")),
                str(area_id),
                bbox.fingerprint,
                str(has_proximity),
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code=evidence_code,
            domain=self.domain,
            observation=observation,
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=EPA_ECHO_METHOD_CODE,
            method_version=EPA_ECHO_METHOD_VERSION,
            confidence=confidence,
            caveat=EPA_ECHO_CAVEAT,
            is_source_failure=False,
            source_date=_utcnow().date().isoformat(),
            observed_at=finished_at,
            geometry_geojson=None,
            geometry_srid=4326,
            spatial_precision_meters=EPA_ECHO_SPATIAL_PRECISION_METERS,
        )

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.evidence_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"EPA ECHO env_hazard evidence: {evidence.evidence_id}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"EPA ECHO facility screen: facility_count={facility_count}",
                timestamp=finished_at,
            )
        )
        return EpaEchoConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: EpaEchoBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> EpaEchoConnectorResult:
        finished_at = _utcnow()
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.FAILED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=0,
            error_count=1,
            warning_count=0,
            log_uri=request_url,
            metrics={
                "source_registry_id": self._source.metadata.get("source_registry_id"),
                "regulated_facility_count": 0,
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
                "accessed_at": finished_at.isoformat(),
            },
        )
        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "source-failure",
                str(self._source.metadata.get("source_registry_id", "")),
                str(area_id),
                bbox.fingerprint,
                failure_reason,
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_FAILURE,
            evidence_code="ENV_HAZ_SOURCE_UNAVAILABLE",
            domain=self.domain,
            observation="EPA ECHO facility proximity query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=EPA_ECHO_METHOD_CODE,
            method_version=EPA_ECHO_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=EPA_ECHO_CAVEAT,
            is_source_failure=True,
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.source_failure_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"EPA ECHO source failure: {failure_reason}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_failed,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=error_message,
                timestamp=finished_at,
            )
        )
        return EpaEchoConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _build_query_url(*, lat: float, lon: float, radius_miles: float) -> str:
    params = urlencode({
        "output": "JSON",
        "lat83": f"{lat:.6f}",
        "long83": f"{lon:.6f}",
        "search_radius": f"{radius_miles:.2f}",
    })
    return f"{EPA_FRS_REST_URL}?{params}"


def _bbox_center_and_radius_miles(bbox: EpaEchoBbox) -> tuple[float, float, float]:
    lat = (bbox.ymin + bbox.ymax) / 2.0
    lon = (bbox.xmin + bbox.xmax) / 2.0
    lat_span_miles = (bbox.ymax - bbox.ymin) * 69.0
    lon_span_miles = (bbox.xmax - bbox.xmin) * 69.0 * math.cos(math.radians(lat))
    radius = math.sqrt((lat_span_miles / 2.0) ** 2 + (lon_span_miles / 2.0) ** 2)
    radius = max(0.5, min(radius, 25.0))
    return lat, lon, radius


def _parse_facility_count(results: Mapping[str, object]) -> int:
    total = results.get("TotalFacilityCount")
    if total is not None:
        try:
            count = int(str(total))
            if count >= 0:
                return count
        except (ValueError, TypeError):
            pass
    facilities = results.get("FRSFacility")
    if isinstance(facilities, list):
        return len(facilities)
    return 0


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    with urlopen(url, timeout=timeout_seconds or None) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, Mapping):
        raise ValueError("EPA FRS response root must be a JSON object")
    return cast(Mapping[str, object], parsed)


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "EPA_ECHO_CAVEAT",
    "EPA_ECHO_CONNECTOR_NAME",
    "EPA_ECHO_MAX_BBOX_DEGREES",
    "EPA_ECHO_METHOD_CODE",
    "EPA_ECHO_SPATIAL_PRECISION_METERS",
    "EPA_FRS_REST_URL",
    "EpaEchoBbox",
    "EpaEchoConnector",
    "EpaEchoConnectorError",
    "EpaEchoConnectorResult",
]
