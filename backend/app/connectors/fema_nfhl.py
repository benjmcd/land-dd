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

FEMA_NFHL_CONNECTOR_NAME = "fema_nfhl_live"
FEMA_NFHL_METHOD_CODE = "live_fema_nfhl_flood_hazard_zone_query"
FEMA_NFHL_METHOD_VERSION = "0.1.0"
FEMA_NFHL_SERVICE_URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer"
FEMA_NFHL_FLOOD_HAZARD_ZONES_LAYER_ID = 28
FEMA_NFHL_MAX_FEATURES = 1000
FEMA_NFHL_MAX_BBOX_DEGREES = 1.0
FEMA_NFHL_SPATIAL_PRECISION_METERS = 38 * 0.3048
FEMA_NFHL_CAVEAT = (
    "Effective FEMA NFHL screening only; not a final legal, insurance, lending, "
    "buildability, title, water-rights, wetland, or survey determination. Cite FEMA "
    "and state non-endorsement."
)
FEMA_NFHL_SOURCE_URL = f"{FEMA_NFHL_SERVICE_URL}/{FEMA_NFHL_FLOOD_HAZARD_ZONES_LAYER_ID}/query"

_NAMESPACE = UUID("48e579c8-d434-42fd-96b0-04882768d0f8")
_OUT_FIELDS = (
    "OBJECTID",
    "DFIRM_ID",
    "FLD_AR_ID",
    "FLD_ZONE",
    "ZONE_SUBTY",
    "SFHA_TF",
    "STATIC_BFE",
    "DEPTH",
    "LEN_UNIT",
    "VELOCITY",
    "VEL_UNIT",
    "SOURCE_CIT",
    "GFID",
    "GlobalID",
)


JsonFetcher = Callable[[str, float], Mapping[str, object]]


class FemaNfhlConnectorError(ValueError):
    """Raised when a FEMA NFHL connector request is invalid before source I/O."""


@dataclass(frozen=True)
class FemaNfhlBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise FemaNfhlConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise FemaNfhlConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise FemaNfhlConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise FemaNfhlConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > FEMA_NFHL_MAX_BBOX_DEGREES:
            raise FemaNfhlConnectorError("bbox longitude span exceeds FEMA NFHL limit")
        if self.ymax - self.ymin > FEMA_NFHL_MAX_BBOX_DEGREES:
            raise FemaNfhlConnectorError("bbox latitude span exceeds FEMA NFHL limit")

    @property
    def arcgis_geometry(self) -> str:
        payload = {
            "xmin": self.xmin,
            "ymin": self.ymin,
            "xmax": self.xmax,
            "ymax": self.ymax,
            "spatialReference": {"wkid": 4326},
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"


@dataclass(frozen=True)
class FemaNfhlConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class FemaNfhlConnector:
    """Bounded FEMA NFHL effective flood hazard zone connector.

    The connector queries only the public effective-data NFHL ArcGIS REST service and
    requires a small EPSG:4326 bounding box. It emits source-failure evidence for empty,
    errored, malformed, or transfer-limited responses so missing live data never becomes
    an implicit "no flood issue" result.
    """

    connector_name = FEMA_NFHL_CONNECTOR_NAME
    domain = "flood"

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
            rate_limit_per_minute=30,
            timeout_seconds=30.0,
            max_retries=0,
            retry_backoff_seconds=0.0,
        )

    def query_bbox(
        self,
        *,
        area_id: UUID,
        bbox: FemaNfhlBbox,
        max_features: int = FEMA_NFHL_MAX_FEATURES,
    ) -> FemaNfhlConnectorResult:
        if max_features <= 0 or max_features > FEMA_NFHL_MAX_FEATURES:
            raise FemaNfhlConnectorError("max_features must be between 1 and 1000")

        log = new_observability_log()
        started_at = _utcnow()
        ingest_run_id = _stable_uuid(
            "retrieval",
            str(self._source.source_id),
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
                message="starting bounded FEMA NFHL flood hazard zone query",
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
                failure_reason="fema_nfhl_request_error",
                error_message=str(exc),
                retryable=True,
            )

        if "error" in payload:
            error = payload["error"]
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="fema_nfhl_service_error",
                error_message=_error_message(error),
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
                failure_reason="fema_nfhl_transfer_limit_exceeded",
                error_message="FEMA NFHL response exceeded the configured transfer limit",
                retryable=False,
            )

        features = payload.get("features")
        if not isinstance(features, list):
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="fema_nfhl_malformed_response",
                error_message="FEMA NFHL response did not include a features array",
                retryable=True,
            )

        if not features:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="fema_nfhl_no_features",
                error_message="FEMA NFHL query returned no flood hazard zone features",
                retryable=False,
            )

        finished_at = _utcnow()
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=len(features),
            error_count=0,
            warning_count=0,
            log_uri=request_url,
            metrics={
                "source_registry_id": self._source.metadata.get("source_registry_id"),
                "service_url": FEMA_NFHL_SERVICE_URL,
                "layer_id": FEMA_NFHL_FLOOD_HAZARD_ZONES_LAYER_ID,
                "layer_name": "Flood Hazard Zones",
                "bbox": bbox.fingerprint,
                "max_features": max_features,
                "accessed_at": finished_at.isoformat(),
                "official_source": "FEMA NFHL effective data only",
            },
        )
        evidence_result = self._features_to_evidence(
            features=features,
            area_id=area_id,
            bbox=bbox,
            ingest_run_id=ingest_run_id,
            observed_at=finished_at,
        )
        if isinstance(evidence_result, str):
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="fema_nfhl_malformed_feature",
                error_message=evidence_result,
                retryable=True,
            )
        evidence_inputs = evidence_result

        for evidence in evidence_inputs:
            log.record(
                ConnectorObservabilityEvent(
                    event_type=ConnectorEventType.evidence_stored,
                    connector_name=self.connector_name,
                    ingest_run_id=ingest_run_id,
                    message=f"FEMA NFHL flood hazard evidence: {evidence.evidence_id}",
                    timestamp=finished_at,
                )
            )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"FEMA NFHL query returned {len(evidence_inputs)} features",
                timestamp=finished_at,
            )
        )
        return FemaNfhlConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=evidence_inputs,
            observability_log=log,
            request_url=request_url,
        )

    def _features_to_evidence(
        self,
        *,
        features: list[object],
        area_id: UUID,
        bbox: FemaNfhlBbox,
        ingest_run_id: UUID,
        observed_at: datetime,
    ) -> tuple[EvidenceContract, ...] | str:
        evidence_inputs: list[EvidenceContract] = []
        for feature in features:
            if not isinstance(feature, Mapping):
                return "FEMA NFHL response included a non-object feature"
            try:
                evidence = self._feature_to_evidence(
                    feature=cast(Mapping[str, object], feature),
                    area_id=area_id,
                    bbox=bbox,
                    ingest_run_id=ingest_run_id,
                    observed_at=observed_at,
                )
            except ValueError as exc:
                return str(exc)
            if evidence.geometry_geojson is None:
                return "FEMA NFHL response included a feature without GeoJSON geometry"
            evidence_inputs.append(evidence)
        return tuple(evidence_inputs)

    def _feature_to_evidence(
        self,
        *,
        feature: Mapping[str, object],
        area_id: UUID,
        bbox: FemaNfhlBbox,
        ingest_run_id: UUID,
        observed_at: datetime,
    ) -> EvidenceContract:
        properties = _mapping_or_empty(feature.get("properties"))
        geometry = feature.get("geometry")
        feature_id = _feature_identifier(properties)
        return EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(self._source.source_id),
                str(area_id),
                bbox.fingerprint,
                feature_id,
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="FEMA_NFHL_FLOOD_HAZARD_ZONE_INTERSECTION",
            domain=self.domain,
            observation="FEMA NFHL effective flood hazard zone intersects the query area.",
            observed_value={
                "flood_zone_code": _optional_text(properties.get("FLD_ZONE")),
                "intersects": True,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=FEMA_NFHL_METHOD_CODE,
            method_version=FEMA_NFHL_METHOD_VERSION,
            confidence=ConfidenceBand.MEDIUM,
            caveat=FEMA_NFHL_CAVEAT,
            is_source_failure=False,
            source_date=observed_at.date().isoformat(),
            observed_at=observed_at,
            geometry_geojson=cast(dict[str, object], geometry)
            if isinstance(geometry, Mapping)
            else None,
            geometry_srid=4326,
            spatial_precision_meters=FEMA_NFHL_SPATIAL_PRECISION_METERS,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: FemaNfhlBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> FemaNfhlConnectorResult:
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
                "service_url": FEMA_NFHL_SERVICE_URL,
                "layer_id": FEMA_NFHL_FLOOD_HAZARD_ZONES_LAYER_ID,
                "bbox": bbox.fingerprint,
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
            evidence_code="FEMA_NFHL_SOURCE_FAILURE",
            domain=self.domain,
            observation="FEMA NFHL flood hazard zone query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=FEMA_NFHL_METHOD_CODE,
            method_version=FEMA_NFHL_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=FEMA_NFHL_CAVEAT,
            is_source_failure=True,
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.source_failure_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"FEMA NFHL source failure: {failure_reason}",
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
        return FemaNfhlConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _build_query_url(*, bbox: FemaNfhlBbox, max_features: int) -> str:
    params = {
        "f": "geojson",
        "where": "1=1",
        "outFields": ",".join(_OUT_FIELDS),
        "returnGeometry": "true",
        "geometry": bbox.arcgis_geometry,
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "resultRecordCount": str(max_features),
    }
    return f"{FEMA_NFHL_SOURCE_URL}?{urlencode(params)}"


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    with urlopen(url, timeout=timeout_seconds or None) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, Mapping):
        raise ValueError("FEMA NFHL response root must be a JSON object")
    return cast(Mapping[str, object], parsed)


def _mapping_or_empty(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    return {}


def _feature_identifier(properties: Mapping[str, object]) -> str:
    for field_name in ("GlobalID", "GFID", "OBJECTID", "FLD_AR_ID"):
        value = properties.get(field_name)
        if value is not None and str(value).strip():
            return f"{field_name}:{value}"
    return json.dumps(dict(properties), default=str, sort_keys=True)


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_number(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _error_message(error: object) -> str:
    if isinstance(error, Mapping):
        message = error.get("message")
        if message is not None:
            return str(message)
    return str(error)


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "FEMA_NFHL_CONNECTOR_NAME",
    "FEMA_NFHL_CAVEAT",
    "FEMA_NFHL_FLOOD_HAZARD_ZONES_LAYER_ID",
    "FEMA_NFHL_MAX_BBOX_DEGREES",
    "FEMA_NFHL_MAX_FEATURES",
    "FEMA_NFHL_METHOD_CODE",
    "FEMA_NFHL_SERVICE_URL",
    "FemaNfhlBbox",
    "FemaNfhlConnector",
    "FemaNfhlConnectorError",
    "FemaNfhlConnectorResult",
]
