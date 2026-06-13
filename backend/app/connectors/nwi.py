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

NWI_CONNECTOR_NAME = "nwi_live"
NWI_METHOD_CODE = "live_usfws_nwi_wetland_intersection_query"
NWI_METHOD_VERSION = "0.1.0"
NWI_SERVICE_URL = (
    "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/"
    "Wetlands/MapServer"
)
NWI_WETLANDS_LAYER_ID = 0
NWI_MAX_FEATURES = 1000
NWI_MAX_BBOX_DEGREES = 0.5
NWI_SPATIAL_PRECISION_METERS = 30.0
NWI_CAVEAT = (
    "USFWS National Wetlands Inventory screening only; not a jurisdictional "
    "wetland delineation, Clean Water Act determination, permit decision, legal "
    "conclusion, buildability conclusion, survey, lending, appraisal, or investment "
    "advice. Cite USFWS/NWI and preserve metadata, published-date, source-date, "
    "project, and exclusion caveats."
)
NWI_SOURCE_URL = f"{NWI_SERVICE_URL}/{NWI_WETLANDS_LAYER_ID}/query"
ACRE_TO_SQ_M = 4046.8564224

_NAMESPACE = UUID("316fbefb-9b12-40fd-9343-47b3a698cfb0")
_OUT_FIELDS = (
    "Wetlands.OBJECTID",
    "Wetlands.ATTRIBUTE",
    "Wetlands.WETLAND_TYPE",
    "Wetlands.ACRES",
    "Wetlands.GLOBALID",
    "NWI_Wetland_Codes.SYSTEM_NAME",
    "NWI_Wetland_Codes.CLASS_NAME",
    "NWI_Wetland_Codes.WATER_REGIME_NAME",
)

NwiJsonFetcher = Callable[[str, float], Mapping[str, object]]


class NwiConnectorError(ValueError):
    """Raised when an NWI connector request is invalid before source I/O."""


@dataclass(frozen=True)
class NwiBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise NwiConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise NwiConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise NwiConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise NwiConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > NWI_MAX_BBOX_DEGREES:
            raise NwiConnectorError("bbox longitude span exceeds NWI limit")
        if self.ymax - self.ymin > NWI_MAX_BBOX_DEGREES:
            raise NwiConnectorError("bbox latitude span exceeds NWI limit")

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
class NwiConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class NwiConnector:
    """Bounded USFWS National Wetlands Inventory connector.

    The connector queries only the official FWS-linked Wetlands REST service with a
    small EPSG:4326 bounding box. Empty, errored, malformed, or transfer-limited
    responses become source-failure evidence so missing live data never becomes an
    implicit "no wetland issue" result.
    """

    connector_name = NWI_CONNECTOR_NAME
    domain = "wetlands"

    def __init__(
        self,
        *,
        source: SourceContract,
        fetch_json: NwiJsonFetcher | None = None,
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
        bbox: NwiBbox,
        max_features: int = NWI_MAX_FEATURES,
    ) -> NwiConnectorResult:
        if max_features <= 0 or max_features > NWI_MAX_FEATURES:
            raise NwiConnectorError("max_features must be between 1 and 1000")

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
                message="starting bounded USFWS NWI wetlands query",
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
                failure_reason="nwi_request_error",
                error_message=str(exc),
                retryable=True,
            )

        if "error" in payload:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="nwi_service_error",
                error_message=_error_message(payload["error"]),
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
                failure_reason="nwi_transfer_limit_exceeded",
                error_message="NWI response exceeded the configured transfer limit",
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
                failure_reason="nwi_malformed_response",
                error_message="NWI response did not include a features array",
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
                failure_reason="nwi_no_features",
                error_message="NWI query returned no wetland/deepwater features",
                retryable=False,
            )

        finished_at = _utcnow()
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
                failure_reason="nwi_malformed_feature",
                error_message=evidence_result,
                retryable=True,
            )

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
                "service_url": NWI_SERVICE_URL,
                "layer_id": NWI_WETLANDS_LAYER_ID,
                "layer_name": "Wetlands",
                "bbox": bbox.fingerprint,
                "max_features": max_features,
                "accessed_at": finished_at.isoformat(),
                "official_source": "USFWS National Wetlands Inventory REST service",
            },
        )
        for evidence in evidence_result:
            log.record(
                ConnectorObservabilityEvent(
                    event_type=ConnectorEventType.evidence_stored,
                    connector_name=self.connector_name,
                    ingest_run_id=ingest_run_id,
                    message=f"NWI wetlands evidence: {evidence.evidence_id}",
                    timestamp=finished_at,
                )
            )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"NWI query returned {len(evidence_result)} features",
                timestamp=finished_at,
            )
        )
        return NwiConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=evidence_result,
            observability_log=log,
            request_url=request_url,
        )

    def _features_to_evidence(
        self,
        *,
        features: list[object],
        area_id: UUID,
        bbox: NwiBbox,
        ingest_run_id: UUID,
        observed_at: datetime,
    ) -> tuple[EvidenceContract, ...] | str:
        evidence_inputs: list[EvidenceContract] = []
        for feature in features:
            if not isinstance(feature, Mapping):
                return "NWI response included a non-object feature"
            properties = _mapping_or_empty(feature.get("properties"))
            geometry = feature.get("geometry")
            if not isinstance(geometry, Mapping):
                return "NWI response included a feature without GeoJSON geometry"
            evidence_inputs.append(
                self._feature_to_evidence(
                    feature=cast(Mapping[str, object], feature),
                    properties=properties,
                    area_id=area_id,
                    bbox=bbox,
                    ingest_run_id=ingest_run_id,
                    observed_at=observed_at,
                )
            )
        return tuple(evidence_inputs)

    def _feature_to_evidence(
        self,
        *,
        feature: Mapping[str, object],
        properties: Mapping[str, object],
        area_id: UUID,
        bbox: NwiBbox,
        ingest_run_id: UUID,
        observed_at: datetime,
    ) -> EvidenceContract:
        feature_id = _feature_identifier(feature, properties)
        wetland_type = _optional_text(
            _first_present(properties, "Wetlands.WETLAND_TYPE", "WETLAND_TYPE")
        )
        class_name = _optional_text(
            _first_present(properties, "NWI_Wetland_Codes.CLASS_NAME", "CLASS_NAME")
        )
        system_name = _optional_text(
            _first_present(properties, "NWI_Wetland_Codes.SYSTEM_NAME", "SYSTEM_NAME")
        )
        observed_value: dict[str, object] = {
            "intersects_mapped_wetlands": True,
        }
        if wetland_type is not None:
            observed_value["wetland_type"] = wetland_type
        if class_name is not None:
            observed_value["wetland_class"] = class_name
        if system_name is not None:
            observed_value["wetland_system"] = system_name
        acres = _optional_number(_first_present(properties, "Wetlands.ACRES", "ACRES"))
        if acres is not None:
            observed_value["mapped_wetland_area_sq_m"] = acres * ACRE_TO_SQ_M

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
            evidence_code="NWI_MAPPED_WETLAND_INTERSECTION",
            domain=self.domain,
            observation="USFWS NWI mapped wetland/deepwater feature intersects the query area.",
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=NWI_METHOD_CODE,
            method_version=NWI_METHOD_VERSION,
            confidence=ConfidenceBand.MEDIUM,
            caveat=NWI_CAVEAT,
            is_source_failure=False,
            source_date=observed_at.date().isoformat(),
            observed_at=observed_at,
            geometry_geojson=cast(dict[str, object], feature["geometry"]),
            geometry_srid=4326,
            spatial_precision_meters=NWI_SPATIAL_PRECISION_METERS,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: NwiBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> NwiConnectorResult:
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
                "service_url": NWI_SERVICE_URL,
                "layer_id": NWI_WETLANDS_LAYER_ID,
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
            evidence_code="NWI_SOURCE_FAILURE",
            domain=self.domain,
            observation="USFWS NWI wetlands query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=NWI_METHOD_CODE,
            method_version=NWI_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=NWI_CAVEAT,
            is_source_failure=True,
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.source_failure_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"NWI source failure: {failure_reason}",
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
        return NwiConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _build_query_url(*, bbox: NwiBbox, max_features: int) -> str:
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
    return f"{NWI_SOURCE_URL}?{urlencode(params)}"


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    with urlopen(url, timeout=timeout_seconds or None) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, Mapping):
        raise ValueError("NWI response root must be a JSON object")
    return cast(Mapping[str, object], parsed)


def _mapping_or_empty(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    return {}


def _feature_identifier(
    feature: Mapping[str, object],
    properties: Mapping[str, object],
) -> str:
    for field_name in ("Wetlands.GLOBALID", "GLOBALID", "Wetlands.OBJECTID", "OBJECTID"):
        value = properties.get(field_name)
        if value is not None and str(value).strip():
            return f"{field_name}:{value}"
    value = feature.get("id")
    if value is not None and str(value).strip():
        return f"id:{value}"
    return json.dumps(dict(properties), default=str, sort_keys=True)


def _first_present(properties: Mapping[str, object], *field_names: str) -> object | None:
    for field_name in field_names:
        value = properties.get(field_name)
        if value is not None:
            return value
    return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_number(value: object) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
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
    "NWI_CAVEAT",
    "NWI_CONNECTOR_NAME",
    "NWI_MAX_BBOX_DEGREES",
    "NWI_MAX_FEATURES",
    "NWI_METHOD_CODE",
    "NWI_SERVICE_URL",
    "NWI_SOURCE_URL",
    "NWI_WETLANDS_LAYER_ID",
    "NwiBbox",
    "NwiConnector",
    "NwiConnectorError",
    "NwiConnectorResult",
    "NwiJsonFetcher",
]
