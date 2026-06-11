from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from urllib.error import HTTPError, URLError
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

FCC_BROADBAND_CONNECTOR_NAME = "fcc_broadband_live"
FCC_BROADBAND_METHOD_CODE = "live_fcc_bdc_availability_screen"
FCC_BROADBAND_METHOD_VERSION = "0.1.0"
FCC_BROADBAND_API_URL = "https://broadbandmap.fcc.gov/api/public/map/listAvailability"
FCC_BROADBAND_MAX_BBOX_DEGREES = 0.5
FCC_BROADBAND_SPATIAL_PRECISION_METERS = 1000.0
FCC_BROADBAND_CAVEAT = (
    "FCC Broadband Data Collection availability screening only. Provider-reported coverage "
    "does not guarantee service availability at every location; rural coverage claims are "
    "frequently overstated by ISPs. Verify availability directly with providers before "
    "purchasing or developing a parcel. Satellite broadband (including low-earth-orbit "
    "services) may be available regardless of this screen. Data: Federal Communications "
    "Commission Broadband Data Collection (broadbandmap.fcc.gov); cite retrieval date "
    "with every use."
)

_NAMESPACE = UUID("d7f2a4c1-8e3b-4a27-9f15-6b8c3e7d2a91")

_TECH_NAMES: dict[int, str] = {
    10: "dsl", 11: "dsl", 12: "dsl",
    40: "cable", 41: "cable", 42: "cable",
    50: "fiber",
    60: "satellite",
    61: "fixed_wireless", 62: "fixed_wireless", 70: "fixed_wireless",
    300: "lte", 301: "lte", 302: "lte",
}
_HIGH_SPEED_TECHS: frozenset[int] = frozenset({40, 41, 42, 50})  # cable and fiber
_HIGH_SPEED_MBPS_THRESHOLD = 100

JsonFetcher = Callable[[str, float], Mapping[str, object]]


class FccBroadbandConnectorError(ValueError):
    """Raised when an FCC Broadband connector request is invalid before source I/O."""


@dataclass(frozen=True)
class FccBroadbandBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise FccBroadbandConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise FccBroadbandConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise FccBroadbandConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise FccBroadbandConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > FCC_BROADBAND_MAX_BBOX_DEGREES:
            raise FccBroadbandConnectorError("bbox longitude span exceeds FCC Broadband limit")
        if self.ymax - self.ymin > FCC_BROADBAND_MAX_BBOX_DEGREES:
            raise FccBroadbandConnectorError("bbox latitude span exceeds FCC Broadband limit")

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"

    @property
    def bbox_str(self) -> str:
        return f"{self.xmin:.6f},{self.ymin:.6f},{self.xmax:.6f},{self.ymax:.6f}"


@dataclass(frozen=True)
class FccBroadbandConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class FccBroadbandConnector:
    """Bounded FCC Broadband Data Collection availability screening connector.

    Queries the FCC BDC public API for broadband provider availability at the
    center point of a bounding box. Emits source-failure evidence for network
    errors or malformed responses so a missing result never becomes an implicit
    'no broadband available' conclusion.
    """

    connector_name = FCC_BROADBAND_CONNECTOR_NAME
    domain = "broadband"

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
            rate_limit_per_minute=10,
            timeout_seconds=20.0,
            max_retries=0,
            retry_backoff_seconds=0.0,
        )

    def query_bbox(
        self,
        *,
        area_id: UUID,
        bbox: FccBroadbandBbox,
    ) -> FccBroadbandConnectorResult:
        log = new_observability_log()
        started_at = _utcnow()
        lat, lon = _bbox_center(bbox)
        source_registry_id = str(self._source.metadata.get("source_registry_id", ""))
        ingest_run_id = _stable_uuid(
            "retrieval",
            source_registry_id,
            str(area_id),
            bbox.fingerprint,
        )
        request_url = _build_request_url(lat, lon)

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_started,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message="starting FCC BDC broadband availability query",
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
                failure_reason="fcc_broadband_request_error",
                error_message=str(exc),
            )

        availability_list = payload.get("availability")
        if not isinstance(availability_list, list):
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="fcc_broadband_malformed_response",
                error_message="FCC BDC response missing 'availability' list",
            )

        provider_count = len(availability_list)
        technology_types = sorted(
            set(
                _TECH_NAMES.get(int(r.get("technology", 0)), "other")
                for r in availability_list
                if r.get("technology") is not None
            )
        )
        max_download_mbps: int | None = max(
            (int(r["max_download_speed"]) for r in availability_list
             if r.get("max_download_speed")),
            default=None,
        )
        max_upload_mbps: int | None = max(
            (int(r["max_upload_speed"]) for r in availability_list if r.get("max_upload_speed")),
            default=None,
        )
        has_any_broadband = provider_count > 0
        has_high_speed_broadband = any(
            int(r.get("technology", 0)) in _HIGH_SPEED_TECHS
            or (
                r.get("max_download_speed") is not None
                and int(r["max_download_speed"]) >= _HIGH_SPEED_MBPS_THRESHOLD
            )
            for r in availability_list
        )

        finished_at = _utcnow()

        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=provider_count,
            error_count=0,
            warning_count=0,
            log_uri=request_url,
            metrics={
                "source_registry_id": self._source.metadata.get("source_registry_id"),
                "provider_count": provider_count,
                "fcc_bdc_lat": lat,
                "fcc_bdc_lon": lon,
                "accessed_at": finished_at.isoformat(),
            },
        )

        observed_value: dict[str, object] = {
            "has_any_broadband": has_any_broadband,
            "has_high_speed_broadband": has_high_speed_broadband,
            "provider_count": provider_count,
            "max_download_mbps": max_download_mbps,
            "max_upload_mbps": max_upload_mbps,
            "technology_types": technology_types,
            "fcc_bdc_lat": lat,
            "fcc_bdc_lon": lon,
        }

        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                source_registry_id,
                str(area_id),
                bbox.fingerprint,
                str(has_any_broadband),
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="FCC_BROADBAND_AVAILABILITY_SCREEN",
            domain=self.domain,
            observation=(
                f"FCC BDC availability screen: {provider_count} provider(s) reported; "
                f"technologies: {technology_types}"
            ),
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=FCC_BROADBAND_METHOD_CODE,
            method_version=FCC_BROADBAND_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=FCC_BROADBAND_CAVEAT,
            is_source_failure=False,
            source_date=_utcnow().date().isoformat(),
            observed_at=finished_at,
            geometry_geojson=None,
            geometry_srid=4326,
            spatial_precision_meters=FCC_BROADBAND_SPATIAL_PRECISION_METERS,
        )

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.evidence_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"FCC broadband evidence: {evidence.evidence_id}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"FCC BDC availability screen: provider_count={provider_count}",
                timestamp=finished_at,
            )
        )
        return FccBroadbandConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: FccBroadbandBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
    ) -> FccBroadbandConnectorResult:
        finished_at = _utcnow()
        source_registry_id = str(self._source.metadata.get("source_registry_id", ""))
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
                "provider_count": 0,
                "failure_reason": failure_reason,
                "error_message": error_message,
                "accessed_at": finished_at.isoformat(),
            },
        )
        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "source-failure",
                source_registry_id,
                str(area_id),
                bbox.fingerprint,
                failure_reason,
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_FAILURE,
            evidence_code="BROADBAND_SOURCE_UNAVAILABLE",
            domain=self.domain,
            observation="FCC BDC broadband availability query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=FCC_BROADBAND_METHOD_CODE,
            method_version=FCC_BROADBAND_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=FCC_BROADBAND_CAVEAT,
            is_source_failure=True,
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.source_failure_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"FCC broadband source failure: {failure_reason}",
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
        return FccBroadbandConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _bbox_center(bbox: FccBroadbandBbox) -> tuple[float, float]:
    lat = (bbox.ymin + bbox.ymax) / 2.0
    lon = (bbox.xmin + bbox.xmax) / 2.0
    return lat, lon


def _build_request_url(lat: float, lon: float) -> str:
    return f"{FCC_BROADBAND_API_URL}?latitude={lat:.6f}&longitude={lon:.6f}&unit_count=1"


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    with urlopen(url, timeout=timeout_seconds or None) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, Mapping):
        raise ValueError("FCC BDC response root must be a JSON object")
    return cast(Mapping[str, object], parsed)


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "FCC_BROADBAND_API_URL",
    "FCC_BROADBAND_CAVEAT",
    "FCC_BROADBAND_CONNECTOR_NAME",
    "FCC_BROADBAND_MAX_BBOX_DEGREES",
    "FCC_BROADBAND_METHOD_CODE",
    "FCC_BROADBAND_SPATIAL_PRECISION_METERS",
    "FccBroadbandBbox",
    "FccBroadbandConnector",
    "FccBroadbandConnectorError",
    "FccBroadbandConnectorResult",
    "JsonFetcher",
]
