from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote
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

OSM_ROAD_ACCESS_CONNECTOR_NAME = "osm_road_access_live"
OSM_ROAD_ACCESS_METHOD_CODE = "live_osm_road_adjacency_bbox_screen"
OSM_ROAD_ACCESS_METHOD_VERSION = "0.1.0"
OSM_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSM_ROAD_ACCESS_MAX_BBOX_DEGREES = 0.5
OSM_ROAD_ACCESS_MAX_FEATURES = 500
OSM_ROAD_ACCESS_SPATIAL_PRECISION_METERS = 30.0
OSM_ROAD_ACCESS_CAVEAT = (
    "Road-adjacency screening proxy only. Road presence in OSM does not constitute "
    "evidence of legal access, public road status, maintained road status, "
    "right-of-way, easement, title, survey accuracy, or any regulatory determination. "
    "Data: © OpenStreetMap contributors (openstreetmap.org/copyright), Open Database "
    "License (opendatacommons.org/licenses/odbl/). Include dataset vintage and "
    "retrieval date. Treat as screening signal only; verify legal access independently."
)

_NAMESPACE = UUID("c3a7f1b2-9e4d-4c58-a102-0f8e3d5a6b47")

_HIGHWAY_FILTER = (
    "^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|service"
    "|track|path|footway|cycleway|bridleway|motorway_link|trunk_link|primary_link"
    "|secondary_link|tertiary_link)$"
)

JsonFetcher = Callable[[str, float], Mapping[str, object]]


class OsmRoadAccessConnectorError(ValueError):
    """Raised when an OSM road access connector request is invalid before source I/O."""


@dataclass(frozen=True)
class OsmRoadAccessBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise OsmRoadAccessConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise OsmRoadAccessConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise OsmRoadAccessConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise OsmRoadAccessConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > OSM_ROAD_ACCESS_MAX_BBOX_DEGREES:
            raise OsmRoadAccessConnectorError("bbox longitude span exceeds OSM road access limit")
        if self.ymax - self.ymin > OSM_ROAD_ACCESS_MAX_BBOX_DEGREES:
            raise OsmRoadAccessConnectorError("bbox latitude span exceeds OSM road access limit")

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"

    @property
    def overpass_bbox(self) -> str:
        """Return bbox in Overpass S,W,N,E order."""
        return f"{self.ymin},{self.xmin},{self.ymax},{self.xmax}"


@dataclass(frozen=True)
class OsmRoadAccessConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class OsmRoadAccessConnector:
    """Bounded OSM/Overpass road-adjacency screening connector.

    Queries the public Overpass API for ways with highway tags within a small
    EPSG:4326 bounding box. Emits source-failure evidence for network errors,
    empty, or malformed responses so a missing live result never becomes an
    implicit 'no road found' conclusion.
    """

    connector_name = OSM_ROAD_ACCESS_CONNECTOR_NAME
    domain = "access"

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
            rate_limit_per_minute=20,
            timeout_seconds=30.0,
            max_retries=0,
            retry_backoff_seconds=0.0,
        )

    def query_bbox(
        self,
        *,
        area_id: UUID,
        bbox: OsmRoadAccessBbox,
        max_features: int = OSM_ROAD_ACCESS_MAX_FEATURES,
    ) -> OsmRoadAccessConnectorResult:
        log = new_observability_log()
        started_at = _utcnow()
        ingest_run_id = _stable_uuid(
            "retrieval",
            str(self._source.source_id),
            str(area_id),
            bbox.fingerprint,
            str(max_features),
        )
        request_url = _build_query_url(bbox=bbox)
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_started,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message="starting bounded OSM road adjacency query",
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
                failure_reason="osm_road_access_request_error",
                error_message=str(exc),
                retryable=True,
            )

        elements = payload.get("elements")
        if not isinstance(elements, list):
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="osm_road_access_malformed_response",
                error_message="Overpass response did not include an elements array",
                retryable=True,
            )

        remark = payload.get("remark")
        if isinstance(remark, str) and remark.strip():
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="osm_road_access_overpass_error",
                error_message=remark.strip(),
                retryable=True,
            )

        road_count = len(elements)
        highway_types: list[str] = sorted({
            str(cast(Mapping[str, object], el).get("tags", {}).get("highway", ""))
            for el in elements
            if isinstance(el, Mapping)
            and isinstance(cast(Mapping[str, object], el).get("tags"), Mapping)
            and cast(Mapping[str, object], el).get("tags", {}).get("highway")
        })

        has_road = road_count > 0
        finished_at = _utcnow()

        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=road_count,
            error_count=0,
            warning_count=0,
            log_uri=request_url,
            metrics={
                "source_registry_id": self._source.metadata.get("source_registry_id"),
                "road_count": road_count,
                "lookup_type": "live_overpass",
                "osm_bbox": bbox.overpass_bbox,
                "accessed_at": finished_at.isoformat(),
            },
        )

        if has_road:
            confidence = ConfidenceBand.MEDIUM
            observed_value: dict[str, object] = {
                "has_public_road_adjacency": True,
                "public_road_adjacency": True,
                "road_distance_m": 0.0,
                "road_count": road_count,
                "highway_types": highway_types,
                "osm_query_bbox": bbox.overpass_bbox,
                "lookup_type": "live_overpass",
            }
            observation = "OSM Overpass query found road ways adjacent to the query area."
        else:
            confidence = ConfidenceBand.LOW
            observed_value = {
                "has_public_road_adjacency": False,
                "public_road_adjacency": False,
                "no_public_road_adjacency": True,
                "road_count": 0,
                "highway_types": [],
                "osm_query_bbox": bbox.overpass_bbox,
                "lookup_type": "live_overpass",
            }
            observation = "OSM Overpass query found no road ways adjacent to the query area."

        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(self._source.source_id),
                str(area_id),
                bbox.fingerprint,
                str(has_road),
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
            domain=self.domain,
            observation=observation,
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=OSM_ROAD_ACCESS_METHOD_CODE,
            method_version=OSM_ROAD_ACCESS_METHOD_VERSION,
            confidence=confidence,
            caveat=OSM_ROAD_ACCESS_CAVEAT,
            is_source_failure=False,
            source_date=_utcnow().date().isoformat(),
            observed_at=finished_at,
            geometry_geojson=None,
            geometry_srid=4326,
            spatial_precision_meters=OSM_ROAD_ACCESS_SPATIAL_PRECISION_METERS,
        )

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.evidence_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"OSM road adjacency evidence: {evidence.evidence_id}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"OSM road adjacency query: road_count={road_count}",
                timestamp=finished_at,
            )
        )
        return OsmRoadAccessConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: OsmRoadAccessBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> OsmRoadAccessConnectorResult:
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
                "road_count": 0,
                "lookup_type": "live_overpass",
                "osm_bbox": bbox.overpass_bbox,
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
            evidence_code="ACCESS_SOURCE_UNAVAILABLE",
            domain=self.domain,
            observation="OSM road adjacency query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=OSM_ROAD_ACCESS_METHOD_CODE,
            method_version=OSM_ROAD_ACCESS_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=OSM_ROAD_ACCESS_CAVEAT,
            is_source_failure=True,
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.source_failure_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"OSM road access source failure: {failure_reason}",
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
        return OsmRoadAccessConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _build_query_url(*, bbox: OsmRoadAccessBbox) -> str:
    query = (
        f'[out:json][timeout:25];way["highway"~"{_HIGHWAY_FILTER}"]'
        f'["access"!="private"]["access"!="no"]'
        f"({bbox.overpass_bbox});out tags;"
    )
    return f"{OSM_OVERPASS_URL}?data={quote(query)}"


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    with urlopen(url, timeout=timeout_seconds or None) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, Mapping):
        raise ValueError("Overpass response root must be a JSON object")
    return cast(Mapping[str, object], parsed)


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "OSM_OVERPASS_URL",
    "OSM_ROAD_ACCESS_CAVEAT",
    "OSM_ROAD_ACCESS_CONNECTOR_NAME",
    "OSM_ROAD_ACCESS_MAX_BBOX_DEGREES",
    "OSM_ROAD_ACCESS_MAX_FEATURES",
    "OSM_ROAD_ACCESS_METHOD_CODE",
    "OSM_ROAD_ACCESS_SPATIAL_PRECISION_METERS",
    "OsmRoadAccessBbox",
    "OsmRoadAccessConnector",
    "OsmRoadAccessConnectorError",
    "OsmRoadAccessConnectorResult",
]
