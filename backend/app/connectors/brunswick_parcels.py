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

BRUNSWICK_PARCELS_CONNECTOR_NAME = "brunswick_parcels_live"
BRUNSWICK_PARCELS_METHOD_CODE = "brunswick_gis_parcels"
BRUNSWICK_PARCELS_METHOD_VERSION = "0.1.0"
BRUNSWICK_PARCELS_SERVICE_URL = (
    "https://bcgis.brunswickcountync.gov/arcgis/rest/services/Layers/TaxParcels/FeatureServer/0/query"
)
BRUNSWICK_PARCELS_MAX_FEATURES = 1000
BRUNSWICK_PARCELS_MAX_BBOX_DEGREES = 1.0
BRUNSWICK_PARCELS_SPATIAL_PRECISION_METERS = 50.0
BRUNSWICK_PARCELS_CAVEAT = (
    "Parcel geometry from Brunswick County GIS; approximate only — not a survey, "
    "not a title determination, not buildability advice. Boundaries may not match "
    "recorded plat. Brunswick County assumes no legal responsibility for GIS data. "
    "Data as of county last update."
)

_NAMESPACE = UUID("c1e4b7a2-3f9d-4c8e-a5b1-2d6f8a0e3c7b")


JsonFetcher = Callable[[str, float], dict[str, object]]


class BrunswickParcelsConnectorError(ValueError):
    """Raised when a Brunswick Parcels connector request is invalid before source I/O."""


@dataclass(frozen=True)
class BrunswickParcelsBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise BrunswickParcelsConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise BrunswickParcelsConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise BrunswickParcelsConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise BrunswickParcelsConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > BRUNSWICK_PARCELS_MAX_BBOX_DEGREES:
            raise BrunswickParcelsConnectorError(
                "bbox longitude span exceeds Brunswick Parcels limit"
            )
        if self.ymax - self.ymin > BRUNSWICK_PARCELS_MAX_BBOX_DEGREES:
            raise BrunswickParcelsConnectorError(
                "bbox latitude span exceeds Brunswick Parcels limit"
            )

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"


@dataclass(frozen=True)
class BrunswickParcelsConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class BrunswickParcelsConnector:
    """Bounded Brunswick County GIS parcel connector.

    The connector queries the public Brunswick County ArcGIS REST FeatureServer for parcel
    boundaries and attributes. It emits source-failure evidence for empty, errored,
    malformed, or transfer-limited responses so missing live data never becomes an
    implicit result.
    """

    connector_name = BRUNSWICK_PARCELS_CONNECTOR_NAME
    domain = "parcels"

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
        bbox: BrunswickParcelsBbox,
        max_features: int = BRUNSWICK_PARCELS_MAX_FEATURES,
    ) -> BrunswickParcelsConnectorResult:
        if max_features <= 0 or max_features > BRUNSWICK_PARCELS_MAX_FEATURES:
            raise BrunswickParcelsConnectorError("max_features must be between 1 and 1000")

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
                message="starting bounded Brunswick County GIS parcel query",
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
                failure_reason="brunswick_parcels_request_error",
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
                failure_reason="brunswick_parcels_service_error",
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
                failure_reason="brunswick_parcels_transfer_limit_exceeded",
                error_message="Brunswick Parcels response exceeded the configured transfer limit",
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
                failure_reason="brunswick_parcels_malformed_response",
                error_message="Brunswick Parcels response did not include a features array",
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
                failure_reason="brunswick_parcels_no_features",
                error_message="Brunswick Parcels query returned no parcel features",
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
                "service_url": BRUNSWICK_PARCELS_SERVICE_URL,
                "bbox": bbox.fingerprint,
                "max_features": max_features,
                "accessed_at": finished_at.isoformat(),
            },
        )

        evidence_inputs: list[EvidenceContract] = []
        for feature in features:
            if not isinstance(feature, Mapping):
                return self._source_failure_result(
                    area_id=area_id,
                    bbox=bbox,
                    ingest_run_id=ingest_run_id,
                    request_url=request_url,
                    started_at=started_at,
                    log=log,
                    failure_reason="brunswick_parcels_malformed_response",
                    error_message="Brunswick Parcels response included a non-object feature",
                    retryable=True,
                )
            feature_map = cast(Mapping[str, object], feature)
            properties = feature_map.get("properties")
            if not isinstance(properties, Mapping):
                properties = {}
            props = cast(Mapping[str, object], properties)
            geometry = feature_map.get("geometry")
            geometry_geojson = (
                cast(dict[str, object], geometry) if isinstance(geometry, Mapping) else None
            )
            pin = props.get("PIN")
            feature_id = str(pin) if pin is not None else json.dumps(
                dict(props), default=str, sort_keys=True
            )
            evidence = EvidenceContract(
                evidence_id=_stable_uuid(
                    "evidence",
                    str(self._source.source_id),
                    str(area_id),
                    bbox.fingerprint,
                    feature_id,
                ),
                area_id=area_id,
                evidence_type=EvidenceType.SPATIAL_INTERSECTION,
                evidence_code="COUNTY_PARCEL_INTERSECTION",
                domain=self.domain,
                observation="Parcel boundary intersects the area of interest",
                observed_value={
                    "intersects": True,
                    "parcel_pin": props.get("PIN"),
                    "parcel_acres": props.get("CALCAC"),
                    "parcel_zoning": props.get("Zoning"),
                },
                source_id=self._source.source_id,
                source_ingest_run_id=ingest_run_id,
                method_code=BRUNSWICK_PARCELS_METHOD_CODE,
                method_version=BRUNSWICK_PARCELS_METHOD_VERSION,
                confidence=ConfidenceBand.LOW,
                caveat=BRUNSWICK_PARCELS_CAVEAT,
                is_source_failure=False,
                observed_at=finished_at,
                geometry_geojson=geometry_geojson,
                geometry_srid=4326,
                spatial_precision_meters=BRUNSWICK_PARCELS_SPATIAL_PRECISION_METERS,
            )
            evidence_inputs.append(evidence)
            log.record(
                ConnectorObservabilityEvent(
                    event_type=ConnectorEventType.evidence_stored,
                    connector_name=self.connector_name,
                    ingest_run_id=ingest_run_id,
                    message=f"Brunswick parcels evidence: {evidence.evidence_id}",
                    timestamp=finished_at,
                )
            )

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"Brunswick parcels query returned {len(evidence_inputs)} features",
                timestamp=finished_at,
            )
        )
        return BrunswickParcelsConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=tuple(evidence_inputs),
            observability_log=log,
            request_url=request_url,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: BrunswickParcelsBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> BrunswickParcelsConnectorResult:
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
                "service_url": BRUNSWICK_PARCELS_SERVICE_URL,
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
            evidence_code="BRUNSWICK_PARCELS_SOURCE_FAILURE",
            domain=self.domain,
            observation="Brunswick County parcel query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=BRUNSWICK_PARCELS_METHOD_CODE,
            method_version=BRUNSWICK_PARCELS_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=BRUNSWICK_PARCELS_CAVEAT,
            is_source_failure=True,
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.source_failure_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"Brunswick parcels source failure: {failure_reason}",
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
        return BrunswickParcelsConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _build_query_url(*, bbox: BrunswickParcelsBbox, max_features: int) -> str:
    params = {
        "where": "1=1",
        "geometry": f"{bbox.xmin},{bbox.ymin},{bbox.xmax},{bbox.ymax}",
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "PIN,CALCAC,Zoning",
        "returnGeometry": "true",
        "f": "geojson",
        "maxRecordCount": str(max_features),
    }
    return f"{BRUNSWICK_PARCELS_SERVICE_URL}?{urlencode(params)}"


def _fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
    with urlopen(url, timeout=timeout_seconds or None) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("Brunswick Parcels response root must be a JSON object")
    return cast(dict[str, object], parsed)


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
    "BRUNSWICK_PARCELS_CAVEAT",
    "BRUNSWICK_PARCELS_CONNECTOR_NAME",
    "BRUNSWICK_PARCELS_MAX_BBOX_DEGREES",
    "BRUNSWICK_PARCELS_MAX_FEATURES",
    "BRUNSWICK_PARCELS_METHOD_CODE",
    "BRUNSWICK_PARCELS_SERVICE_URL",
    "BRUNSWICK_PARCELS_SPATIAL_PRECISION_METERS",
    "BrunswickParcelsBbox",
    "BrunswickParcelsConnector",
    "BrunswickParcelsConnectorError",
    "BrunswickParcelsConnectorResult",
]
