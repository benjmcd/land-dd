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

NC_GEOLOGIC_MAP_CONNECTOR_NAME = "nc_geologic_map_context_live"
NC_GEOLOGIC_MAP_METHOD_CODE = "live_nc_geologic_map_unit_context"
NC_GEOLOGIC_MAP_METHOD_VERSION = "0.1.0"
NC_GEOLOGIC_MAP_LAYER_URL = (
    "https://services2.arcgis.com/kCu40SDxsCGcuUWO/arcgis/rest/services/"
    "Geologic_Map_of_North_Carolina/FeatureServer/3"
)
NC_GEOLOGIC_MAP_MAX_BBOX_DEGREES = 0.5
NC_GEOLOGIC_MAP_MAX_FEATURES = 50
NC_GEOLOGIC_MAP_SPATIAL_PRECISION_METERS = 250000.0
NC_GEOLOGIC_MAP_CAVEAT = (
    "North Carolina Geological Survey 1985 statewide geologic map context only. "
    "This data represents a deprecated statewide map at 1:500,000 scale, digitized "
    "from 1:250,000-scale base maps; it is not parcel-scale geology, engineering, "
    "geotechnical, hazard, mineral-resource, buildability, appraisal, lending, "
    "insurance, or investment advice. Data: North Carolina Geological Survey / "
    "NC Department of Environmental Quality; cite retrieval date and service URL."
)

_NAMESPACE = UUID("33fce1bd-7394-4c39-915a-5d4db10b9d61")

JsonFetcher = Callable[[str, float], Mapping[str, object]]


class NcGeologicMapConnectorError(ValueError):
    """Raised when an NC geologic map connector request is invalid before source I/O."""


@dataclass(frozen=True)
class NcGeologicMapBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise NcGeologicMapConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise NcGeologicMapConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise NcGeologicMapConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise NcGeologicMapConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > NC_GEOLOGIC_MAP_MAX_BBOX_DEGREES:
            raise NcGeologicMapConnectorError("bbox longitude span exceeds NC geologic map limit")
        if self.ymax - self.ymin > NC_GEOLOGIC_MAP_MAX_BBOX_DEGREES:
            raise NcGeologicMapConnectorError("bbox latitude span exceeds NC geologic map limit")

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"

    @property
    def envelope(self) -> str:
        return f"{self.xmin:.6f},{self.ymin:.6f},{self.xmax:.6f},{self.ymax:.6f}"


@dataclass(frozen=True)
class NcGeologicMapConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class NcGeologicMapConnector:
    """Bounded NC Geological Survey map-unit context connector."""

    connector_name = NC_GEOLOGIC_MAP_CONNECTOR_NAME
    domain = "geology"

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
        bbox: NcGeologicMapBbox,
        max_features: int = NC_GEOLOGIC_MAP_MAX_FEATURES,
    ) -> NcGeologicMapConnectorResult:
        if max_features <= 0:
            raise NcGeologicMapConnectorError("max_features must be positive")
        if max_features > NC_GEOLOGIC_MAP_MAX_FEATURES:
            raise NcGeologicMapConnectorError("max_features exceeds NC geologic map limit")

        log = new_observability_log()
        started_at = _utcnow()
        source_registry_id = str(self._source.metadata.get("source_registry_id", ""))
        ingest_run_id = _stable_uuid(
            "retrieval",
            source_registry_id,
            str(area_id),
            bbox.fingerprint,
            str(max_features),
        )
        request_url = _build_query_url(bbox=bbox, max_features=max_features)
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_started,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message="starting NC geologic map unit context query",
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
                failure_reason="nc_geologic_map_request_error",
                error_message=str(exc),
                retryable=True,
            )

        if payload.get("error") is not None:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="nc_geologic_map_service_error",
                error_message=str(payload.get("error")),
                retryable=True,
            )
        if payload.get("exceededTransferLimit") is True:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="nc_geologic_map_response_truncated",
                error_message=(
                    "NC geologic map response exceeded transfer limit; use a smaller bbox"
                ),
                retryable=False,
            )

        try:
            records = _feature_records(payload)
        except ValueError as exc:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="nc_geologic_map_malformed_response",
                error_message=str(exc),
                retryable=True,
            )

        finished_at = _utcnow()
        row_count = len(records)
        has_context = row_count > 0
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=row_count,
            error_count=0,
            warning_count=0,
            log_uri=request_url,
            metrics={
                "source_registry_id": source_registry_id,
                "geologic_unit_count": row_count,
                "nc_geologic_map_bbox": bbox.envelope,
                "accessed_at": finished_at.isoformat(),
            },
        )
        observed_value: dict[str, object] = {
            "has_geologic_map_context": has_context,
            "no_geologic_map_context": not has_context,
            "geologic_unit_count": row_count,
            "geologic_unit_labels": [record["unit_label"] for record in records],
            "geologic_belts": [record["belt"] for record in records],
            "geologic_types": [record["type"] for record in records],
            "geologic_formations": [record["formation"] for record in records],
            "geologic_descriptions": [record["description"] for record in records],
            "nc_geologic_map_bbox": bbox.envelope,
            "nc_geologic_map_year": "1985",
            "nc_geologic_map_deprecated": True,
            "geologic_hazard_determined": False,
            "buildability_determined": False,
        }
        if records:
            observed_value["primary_geologic_unit_label"] = records[0]["unit_label"]
            observed_value["primary_geologic_formation"] = records[0]["formation"]

        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                source_registry_id,
                str(area_id),
                bbox.fingerprint,
                str(row_count),
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="NC_GEOLOGIC_MAP_UNIT_CONTEXT",
            domain=self.domain,
            observation=(
                f"NCGS 1985 geologic map query found {row_count} map unit(s) "
                "intersecting the query bounding box."
            ),
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=NC_GEOLOGIC_MAP_METHOD_CODE,
            method_version=NC_GEOLOGIC_MAP_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=NC_GEOLOGIC_MAP_CAVEAT,
            is_source_failure=False,
            source_date=finished_at.date().isoformat(),
            observed_at=finished_at,
            geometry_geojson=None,
            geometry_srid=4326,
            spatial_precision_meters=NC_GEOLOGIC_MAP_SPATIAL_PRECISION_METERS,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.evidence_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"NC geologic map evidence: {evidence.evidence_id}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"NC geologic map context: row_count={row_count}",
                timestamp=finished_at,
            )
        )
        return NcGeologicMapConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: NcGeologicMapBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> NcGeologicMapConnectorResult:
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
                "failure_reason": failure_reason,
                "nc_geologic_map_bbox": bbox.envelope,
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
            evidence_code="NC_GEOLOGIC_MAP_SOURCE_FAILURE",
            domain=self.domain,
            observation="NCGS geologic map query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
                "attempted_url": request_url,
                "connector": self.connector_name,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=NC_GEOLOGIC_MAP_METHOD_CODE,
            method_version=NC_GEOLOGIC_MAP_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=NC_GEOLOGIC_MAP_CAVEAT,
            is_source_failure=True,
            source_date=finished_at.date().isoformat(),
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_failed,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"NC geologic map source failure: {failure_reason}",
                timestamp=finished_at,
            )
        )
        return NcGeologicMapConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _feature_records(payload: Mapping[str, object]) -> tuple[dict[str, str], ...]:
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("NC geologic map response missing features list")
    records: list[dict[str, str]] = []
    for feature in features:
        if not isinstance(feature, Mapping):
            raise ValueError("NC geologic map feature must be an object")
        attributes = feature.get("attributes")
        if not isinstance(attributes, Mapping):
            raise ValueError("NC geologic map feature missing attributes")
        object_id = _attribute_text(attributes, "OBJECTID")
        unit_label = _attribute_text(attributes, "UnitLabel")
        if not object_id or not unit_label:
            raise ValueError("NC geologic map feature missing OBJECTID or UnitLabel")
        records.append(
            {
                "object_id": object_id,
                "unit_label": unit_label,
                "belt": _attribute_text(attributes, "Belt"),
                "type": _attribute_text(attributes, "Type"),
                "formation": _attribute_text(attributes, "Formation"),
                "description": _attribute_text(attributes, "Description"),
            }
        )
    return tuple(records)


def _attribute_text(attributes: Mapping[str, object], key: str) -> str:
    value = attributes.get(key)
    if value is None:
        return ""
    return str(value).strip()


def _build_query_url(*, bbox: NcGeologicMapBbox, max_features: int) -> str:
    geometry = json.dumps(
        {
            "xmin": bbox.xmin,
            "ymin": bbox.ymin,
            "xmax": bbox.xmax,
            "ymax": bbox.ymax,
            "spatialReference": {"wkid": 4326},
        },
        separators=(",", ":"),
    )
    query = urlencode(
        {
            "where": "1=1",
            "geometry": geometry,
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "inSR": "4326",
            "outSR": "4326",
            "outFields": "OBJECTID,UnitLabel,Belt,Type,Formation,Description",
            "returnGeometry": "false",
            "f": "json",
            "resultRecordCount": str(max_features),
        }
    )
    return f"{NC_GEOLOGIC_MAP_LAYER_URL}/query?{query}"


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    with urlopen(url, timeout=timeout_seconds) as response:  # noqa: S310 - reviewed public URL
        payload = response.read()
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("NC geologic map response was not a JSON object")
    return cast(Mapping[str, object], data)


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "NC_GEOLOGIC_MAP_CAVEAT",
    "NC_GEOLOGIC_MAP_CONNECTOR_NAME",
    "NC_GEOLOGIC_MAP_LAYER_URL",
    "NC_GEOLOGIC_MAP_MAX_BBOX_DEGREES",
    "NC_GEOLOGIC_MAP_MAX_FEATURES",
    "NC_GEOLOGIC_MAP_METHOD_CODE",
    "JsonFetcher",
    "NcGeologicMapBbox",
    "NcGeologicMapConnector",
    "NcGeologicMapConnectorError",
    "NcGeologicMapConnectorResult",
]
