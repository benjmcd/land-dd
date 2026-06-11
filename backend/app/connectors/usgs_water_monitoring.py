from __future__ import annotations

import json
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

USGS_WATER_CONNECTOR_NAME = "usgs_water_monitoring_live"
USGS_WATER_METHOD_CODE = "live_usgs_water_monitoring_bbox_screen"
USGS_WATER_METHOD_VERSION = "0.1.0"
USGS_WATER_SITE_SERVICE_URL = "https://waterservices.usgs.gov/nwis/site/"
USGS_WATER_MAX_BBOX_DEGREES = 1.0  # USGS allows larger area than OSM
USGS_WATER_SPATIAL_PRECISION_METERS = 1000.0  # site locations, not survey-grade
USGS_WATER_CAVEAT = (
    "Water-monitoring proximity screening only. Monitoring station presence does not "
    "constitute evidence of water rights, well viability, supply adequacy, or legal "
    "water access. Provisional USGS data is subject to revision. Station proximity "
    "may be a weak proxy for actual water availability at the subject parcel. "
    "Data: U.S. Geological Survey / Water Data for the Nation "
    "(waterdata.usgs.gov). Cite site code(s) and retrieval date. "
    "Treat as screening signal only."
)

_NAMESPACE = UUID("a2b4c6d8-e0f2-4a6b-8c0e-1d2f3e4a5b6c")  # unique to this connector

JsonFetcher = Callable[[str, float], Mapping[str, object]]


class UsgsWaterConnectorError(ValueError):
    """Raised when a USGS water monitoring connector request is invalid before source I/O."""


@dataclass(frozen=True)
class UsgsWaterBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise UsgsWaterConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise UsgsWaterConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise UsgsWaterConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise UsgsWaterConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > USGS_WATER_MAX_BBOX_DEGREES:
            raise UsgsWaterConnectorError("bbox longitude span exceeds USGS water monitoring limit")
        if self.ymax - self.ymin > USGS_WATER_MAX_BBOX_DEGREES:
            raise UsgsWaterConnectorError("bbox latitude span exceeds USGS water monitoring limit")

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"

    @property
    def usgs_bbox(self) -> str:
        """Return bbox in W,S,E,N order for USGS bBox param."""
        return f"{self.xmin},{self.ymin},{self.xmax},{self.ymax}"


@dataclass(frozen=True)
class UsgsWaterConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class UsgsWaterMonitoringConnector:
    """Bounded USGS water monitoring screening connector.

    Queries the USGS site service for active monitoring stations within a small
    EPSG:4326 bounding box. Emits source-failure evidence for network errors,
    empty, or malformed responses so a missing live result never becomes an
    implicit 'no monitoring station found' conclusion.
    """

    connector_name = USGS_WATER_CONNECTOR_NAME
    domain = "water"

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
            rate_limit_per_minute=5,
            timeout_seconds=30.0,
            max_retries=0,
            retry_backoff_seconds=0.0,
        )

    def query_bbox(
        self,
        *,
        area_id: UUID,
        bbox: UsgsWaterBbox,
    ) -> UsgsWaterConnectorResult:
        log = new_observability_log()
        started_at = _utcnow()
        ingest_run_id = _stable_uuid(
            "retrieval",
            str(self._source.source_id),
            str(area_id),
            bbox.fingerprint,
        )
        request_url = _build_query_url(bbox=bbox)
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_started,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message="starting bounded USGS water monitoring query",
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
                failure_reason="usgs_water_request_error",
                error_message=str(exc),
                retryable=True,
            )

        if not isinstance(payload, Mapping):
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="usgs_water_malformed_response",
                error_message="USGS water service response was not a JSON object",
                retryable=True,
            )

        features = payload.get("features")
        if features is None:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="usgs_water_malformed_response",
                error_message="USGS water service response did not include a 'features' key",
                retryable=True,
            )

        if not isinstance(features, list):
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="usgs_water_malformed_response",
                error_message="USGS water service 'features' value was not a list",
                retryable=True,
            )

        station_count = len(features)
        finished_at = _utcnow()

        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=station_count,
            error_count=0,
            warning_count=0,
            log_uri=request_url,
            metrics={
                "source_registry_id": self._source.metadata.get("source_registry_id"),
                "station_count": station_count,
                "lookup_type": "live_usgs",
                "usgs_bbox": bbox.usgs_bbox,
                "accessed_at": finished_at.isoformat(),
            },
        )

        if station_count > 0:
            observed_value: dict[str, object] = {
                "plausible_water_context": True,
                "monitoring_station_count": station_count,
                "water_context_status": "monitoring_stations_found",
            }
            observation = (
                f"USGS water monitoring query found {station_count} active monitoring "
                "station(s) within the query bounding box."
            )
        else:
            observed_value = {
                "no_plausible_water_context": True,
                "monitoring_station_count": 0,
                "water_context_status": "no_monitoring_stations_in_bbox",
            }
            observation = (
                "USGS water monitoring query found no active monitoring stations "
                "within the query bounding box."
            )

        confidence = ConfidenceBand.LOW  # proximity != water rights; LOW per DS-005

        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(self._source.source_id),
                str(area_id),
                bbox.fingerprint,
                str(station_count > 0),
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="WATER_MONITORING_SCREEN",
            domain=self.domain,
            observation=observation,
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=USGS_WATER_METHOD_CODE,
            method_version=USGS_WATER_METHOD_VERSION,
            confidence=confidence,
            caveat=USGS_WATER_CAVEAT,
            is_source_failure=False,
            source_date=_utcnow().date().isoformat(),
            observed_at=finished_at,
            geometry_geojson=None,
            geometry_srid=4326,
            spatial_precision_meters=USGS_WATER_SPATIAL_PRECISION_METERS,
        )

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.evidence_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"USGS water monitoring evidence: {evidence.evidence_id}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"USGS water monitoring query: station_count={station_count}",
                timestamp=finished_at,
            )
        )
        return UsgsWaterConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: UsgsWaterBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> UsgsWaterConnectorResult:
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
                "station_count": 0,
                "lookup_type": "live_usgs",
                "usgs_bbox": bbox.usgs_bbox,
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
                "accessed_at": finished_at.isoformat(),
            },
        )
        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "source-failure",
                str(self._source.source_id),
                str(area_id),
                bbox.fingerprint,
                failure_reason,
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_FAILURE,
            evidence_code="WATER_SOURCE_UNAVAILABLE",
            domain=self.domain,
            observation="USGS water monitoring query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=USGS_WATER_METHOD_CODE,
            method_version=USGS_WATER_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=USGS_WATER_CAVEAT,
            is_source_failure=True,
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.source_failure_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"USGS water monitoring source failure: {failure_reason}",
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
        return UsgsWaterConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _build_query_url(*, bbox: UsgsWaterBbox) -> str:
    params = {
        "format": "json",
        "bBox": bbox.usgs_bbox,
        "siteStatus": "active",
        "siteType": "ST,LK,GW",  # stream, lake, groundwater
    }
    return USGS_WATER_SITE_SERVICE_URL + "?" + urlencode(params)


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    with urlopen(url, timeout=timeout_seconds or None) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, Mapping):
        raise ValueError("USGS water service response root must be a JSON object")
    return cast(Mapping[str, object], parsed)


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "USGS_WATER_CAVEAT",
    "USGS_WATER_CONNECTOR_NAME",
    "USGS_WATER_MAX_BBOX_DEGREES",
    "USGS_WATER_METHOD_CODE",
    "USGS_WATER_METHOD_VERSION",
    "USGS_WATER_SITE_SERVICE_URL",
    "USGS_WATER_SPATIAL_PRECISION_METERS",
    "UsgsWaterBbox",
    "UsgsWaterConnectorError",
    "UsgsWaterConnectorResult",
    "UsgsWaterMonitoringConnector",
]
