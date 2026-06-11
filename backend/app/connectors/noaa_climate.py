from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
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

NOAA_CLIMATE_CONNECTOR_NAME = "noaa_nws_climate_live"
NOAA_CLIMATE_METHOD_CODE = "live_noaa_nws_point_query"
NOAA_CLIMATE_METHOD_VERSION = "0.1.0"
NOAA_NWS_POINTS_URL = "https://api.weather.gov/points/{lat},{lon}"
NOAA_CLIMATE_MAX_BBOX_DEGREES = 1.0
NOAA_CLIMATE_SPATIAL_PRECISION_METERS = 50000.0
NOAA_CLIMATE_CAVEAT = (
    "NOAA NWS forecast zone coverage only. This connector provides administrative weather "
    "service metadata (forecast office, zone classification, timezone) but does not provide "
    "historical climate normals, frost dates, growing season length, or agricultural risk data. "
    "For homestead and agricultural planning, consult NOAA NCEI 1991–2020 climate normals "
    "and the USDA Plant Hardiness Zone Map. Data: NOAA National Weather Service "
    "(api.weather.gov); cite retrieval date with every use."
)

_NAMESPACE = UUID("b3e1f7c2-9d4a-4b82-a031-7c5e2d8f1b64")

_USER_AGENT = "land-diligence/0.1.0 (contact: contact@example.com)"
_ACCEPT = "application/geo+json"

JsonFetcher = Callable[[str, float], Mapping[str, object]]


class NoaaClimateConnectorError(ValueError):
    """Raised when a NOAA NWS climate connector request is invalid before source I/O."""


@dataclass(frozen=True)
class NoaaClimateBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise NoaaClimateConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise NoaaClimateConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise NoaaClimateConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise NoaaClimateConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > NOAA_CLIMATE_MAX_BBOX_DEGREES:
            raise NoaaClimateConnectorError("bbox longitude span exceeds NOAA climate limit")
        if self.ymax - self.ymin > NOAA_CLIMATE_MAX_BBOX_DEGREES:
            raise NoaaClimateConnectorError("bbox latitude span exceeds NOAA climate limit")

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"

    @property
    def centroid(self) -> tuple[float, float]:
        return _bbox_center(self)


@dataclass(frozen=True)
class NoaaClimateConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class NoaaClimateConnector:
    """Bounded NOAA NWS point-query climate zone connector.

    Queries the NWS api.weather.gov /points endpoint for forecast zone
    administrative metadata at the center of a bounding box. Emits
    source-failure evidence for network errors or malformed responses so
    a missing result never becomes an implicit 'no NWS coverage' conclusion.
    """

    connector_name = NOAA_CLIMATE_CONNECTOR_NAME
    domain = "climate"

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
        bbox: NoaaClimateBbox,
    ) -> NoaaClimateConnectorResult:
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
        request_url = f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}"

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_started,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message="starting NOAA NWS point query",
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
                failure_reason="noaa_nws_request_error",
                error_message=str(exc),
                evidence_code="NOAA_NWS_SOURCE_FAILURE",
            )

        props = payload.get("properties")
        if not isinstance(props, Mapping):
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="noaa_nws_request_error",
                error_message="NWS response missing 'properties' object",
                evidence_code="NOAA_NWS_SOURCE_FAILURE",
            )

        cwa = str(props.get("cwa", ""))
        forecast_zone_url = str(props.get("forecastZone", ""))
        timezone = str(props.get("timeZone", ""))
        radar_station = str(props.get("radarStation", ""))

        # Extract zone ID from URL (last path segment)
        zone_id = forecast_zone_url.rstrip("/").rsplit("/", 1)[-1] if forecast_zone_url else ""

        # Extract nearest city/state from relativeLocation
        rel_location = props.get("relativeLocation")
        nws_nearest_city = ""
        nws_nearest_state = ""
        if isinstance(rel_location, Mapping):
            rel_props = rel_location.get("properties")
            if isinstance(rel_props, Mapping):
                nws_nearest_city = str(rel_props.get("city", ""))
                nws_nearest_state = str(rel_props.get("state", ""))

        # Try to fetch zone name from forecastZone URL
        zone_name = ""
        if forecast_zone_url:
            try:
                zone_payload = self._fetch_json(
                    forecast_zone_url, self._policy.timeout_seconds
                )
                zone_props = zone_payload.get("properties")
                if isinstance(zone_props, Mapping):
                    zone_name = str(zone_props.get("name", ""))
            except Exception:  # noqa: BLE001
                zone_name = ""

        finished_at = _utcnow()

        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=1,
            error_count=0,
            warning_count=0,
            log_uri=request_url,
            metrics={
                "source_registry_id": self._source.metadata.get("source_registry_id"),
                "nws_office_code": cwa,
                "nws_forecast_zone": zone_id,
                "lat": lat,
                "lon": lon,
                "accessed_at": finished_at.isoformat(),
            },
        )

        observed_value: dict[str, object] = {
            "has_nws_coverage": True,
            "nws_office_code": cwa,
            "nws_forecast_zone": zone_id,
            "nws_forecast_zone_name": zone_name,
            "nws_nearest_city": nws_nearest_city,
            "nws_nearest_state": nws_nearest_state,
            "nws_radar_station": radar_station,
            "timezone": timezone,
        }

        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                source_registry_id,
                str(area_id),
                bbox.fingerprint,
                cwa,
                zone_id,
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="NWS_CLIMATE_ZONE",
            domain=self.domain,
            observation=(
                f"NOAA NWS point query: office={cwa}, zone={zone_id}, "
                f"timezone={timezone}"
            ),
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=NOAA_CLIMATE_METHOD_CODE,
            method_version=NOAA_CLIMATE_METHOD_VERSION,
            confidence=ConfidenceBand.HIGH,
            caveat=NOAA_CLIMATE_CAVEAT,
            is_source_failure=False,
            source_date=_utcnow().date().isoformat(),
            observed_at=finished_at,
            geometry_geojson=None,
            geometry_srid=4326,
            spatial_precision_meters=NOAA_CLIMATE_SPATIAL_PRECISION_METERS,
        )

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.evidence_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"NOAA climate evidence: {evidence.evidence_id}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"NOAA NWS point query: office={cwa}, zone={zone_id}",
                timestamp=finished_at,
            )
        )
        return NoaaClimateConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: NoaaClimateBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        evidence_code: str,
    ) -> NoaaClimateConnectorResult:
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
            evidence_code=evidence_code,
            domain=self.domain,
            observation="NOAA NWS point query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=NOAA_CLIMATE_METHOD_CODE,
            method_version=NOAA_CLIMATE_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=NOAA_CLIMATE_CAVEAT,
            is_source_failure=True,
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.source_failure_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"NOAA climate source failure: {failure_reason}",
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
        return NoaaClimateConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _bbox_center(bbox: NoaaClimateBbox) -> tuple[float, float]:
    lat = (bbox.ymin + bbox.ymax) / 2.0
    lon = (bbox.xmin + bbox.xmax) / 2.0
    return lat, lon


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    req = UrlRequest(url)
    req.add_header("Accept", _ACCEPT)
    req.add_header("User-Agent", _USER_AGENT)
    with urlopen(req, timeout=timeout_seconds or None) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, Mapping):
        raise ValueError("NWS response root must be a JSON object")
    return cast(Mapping[str, object], parsed)


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "NOAA_CLIMATE_CAVEAT",
    "NOAA_CLIMATE_CONNECTOR_NAME",
    "NOAA_CLIMATE_MAX_BBOX_DEGREES",
    "NOAA_CLIMATE_METHOD_CODE",
    "NOAA_CLIMATE_SPATIAL_PRECISION_METERS",
    "NOAA_NWS_POINTS_URL",
    "NoaaClimateBbox",
    "NoaaClimateConnector",
    "NoaaClimateConnectorError",
    "NoaaClimateConnectorResult",
]
