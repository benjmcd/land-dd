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

BLM_MLRS_CONNECTOR_NAME = "blm_mlrs_active_mining_claims_live"
BLM_MLRS_METHOD_CODE = "live_blm_mlrs_active_mining_claim_context"
BLM_MLRS_METHOD_VERSION = "0.1.0"
BLM_MLRS_LAYER_URL = (
    "https://gis.blm.gov/nlsdb/rest/services/Mining_Claims/MiningClaims/MapServer/1"
)
BLM_MLRS_MAX_BBOX_DEGREES = 0.5
BLM_MLRS_MAX_FEATURES = 50
BLM_MLRS_SPATIAL_PRECISION_METERS = 100000.0
BLM_MLRS_CAVEAT = (
    "BLM MLRS Active Mining Claims geospatial context only. MLRS case geometries are "
    "derived from legal land descriptions and PLSS mapping; some records may be "
    "approximate, missing geometry, or mapped only to section/county-level context. "
    "This evidence does not determine private mineral rights, claim-boundary "
    "precision, title status, mine hazards, resource value, extraction feasibility, "
    "environmental liability, buildability, appraisal, lending suitability, "
    "insurance suitability, or investment suitability. Data: U.S. Department of the "
    "Interior, Bureau of Land Management MLRS / Mining Claims service; cite retrieval "
    "date and service URL."
)

_NAMESPACE = UUID("cde8dd69-8fa8-4731-b9ca-131ecde9f1e5")

JsonFetcher = Callable[[str, float], Mapping[str, object]]


class BlmMlrsConnectorError(ValueError):
    """Raised when a BLM MLRS connector request is invalid before source I/O."""


@dataclass(frozen=True)
class BlmMlrsBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise BlmMlrsConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise BlmMlrsConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise BlmMlrsConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise BlmMlrsConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > BLM_MLRS_MAX_BBOX_DEGREES:
            raise BlmMlrsConnectorError("bbox longitude span exceeds BLM MLRS limit")
        if self.ymax - self.ymin > BLM_MLRS_MAX_BBOX_DEGREES:
            raise BlmMlrsConnectorError("bbox latitude span exceeds BLM MLRS limit")

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"

    @property
    def envelope(self) -> str:
        return f"{self.xmin:.6f},{self.ymin:.6f},{self.xmax:.6f},{self.ymax:.6f}"


@dataclass(frozen=True)
class BlmMlrsConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


@dataclass(frozen=True)
class _BlmMlrsRecord:
    object_id: str
    case_serial_number: str
    legacy_case_serial_number: str
    case_name: str
    case_disposition: str
    case_type_number: str
    product: str
    data_quality_note: str
    recorded_acres: float | None


class BlmMlrsConnector:
    """Bounded BLM MLRS active mining-claim context connector."""

    connector_name = BLM_MLRS_CONNECTOR_NAME
    domain = "minerals"

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
        bbox: BlmMlrsBbox,
        max_features: int = BLM_MLRS_MAX_FEATURES,
    ) -> BlmMlrsConnectorResult:
        if max_features <= 0:
            raise BlmMlrsConnectorError("max_features must be positive")
        if max_features > BLM_MLRS_MAX_FEATURES:
            raise BlmMlrsConnectorError("max_features exceeds BLM MLRS limit")

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
                message="starting BLM MLRS active mining claims query",
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
                failure_reason="blm_mlrs_request_error",
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
                failure_reason="blm_mlrs_service_error",
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
                failure_reason="blm_mlrs_response_truncated",
                error_message="BLM MLRS response exceeded transfer limit; use a smaller bbox",
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
                failure_reason="blm_mlrs_malformed_response",
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
                "blm_active_mining_claim_count": row_count,
                "blm_mlrs_bbox": bbox.envelope,
                "accessed_at": finished_at.isoformat(),
            },
        )
        observed_value: dict[str, object] = {
            "has_blm_active_mining_claim_context": has_context,
            "no_blm_active_mining_claim_context": not has_context,
            "blm_active_mining_claim_count": row_count,
            "blm_mlrs_bbox": bbox.envelope,
            "blm_mlrs_layer_url": BLM_MLRS_LAYER_URL,
            "mineral_rights_determined": False,
            "blm_mlrs_case_serial_numbers": [
                record.case_serial_number for record in records
            ],
            "blm_mlrs_legacy_case_serial_numbers": [
                record.legacy_case_serial_number for record in records
            ],
            "blm_mlrs_case_names": [record.case_name for record in records],
            "blm_mlrs_case_dispositions": [
                record.case_disposition for record in records
            ],
            "blm_mlrs_case_type_numbers": [
                record.case_type_number for record in records
            ],
            "blm_mlrs_products": [record.product for record in records],
            "blm_mlrs_data_quality_notes": [
                record.data_quality_note for record in records
            ],
            "blm_mlrs_recorded_acres": [
                record.recorded_acres
                for record in records
                if record.recorded_acres is not None
            ],
        }
        if records:
            observed_value["primary_blm_mlrs_case_serial_number"] = (
                records[0].case_serial_number
            )
            observed_value["primary_blm_mlrs_case_name"] = records[0].case_name

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
            evidence_code="BLM_MLRS_ACTIVE_MINING_CLAIM_CONTEXT",
            domain=self.domain,
            observation=(
                f"BLM MLRS Active Mining Claims query found {row_count} active "
                "mining claim record(s) intersecting the query bounding box."
            ),
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=BLM_MLRS_METHOD_CODE,
            method_version=BLM_MLRS_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=BLM_MLRS_CAVEAT,
            is_source_failure=False,
            source_date=finished_at.date().isoformat(),
            observed_at=finished_at,
            geometry_geojson=None,
            geometry_srid=4326,
            spatial_precision_meters=BLM_MLRS_SPATIAL_PRECISION_METERS,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.evidence_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"BLM MLRS active mining claim evidence: {evidence.evidence_id}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"BLM MLRS active mining claim context: row_count={row_count}",
                timestamp=finished_at,
            )
        )
        return BlmMlrsConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: BlmMlrsBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> BlmMlrsConnectorResult:
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
                "blm_mlrs_bbox": bbox.envelope,
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
            evidence_code="BLM_MLRS_SOURCE_FAILURE",
            domain=self.domain,
            observation="BLM MLRS Active Mining Claims query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
                "attempted_url": request_url,
                "connector": self.connector_name,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=BLM_MLRS_METHOD_CODE,
            method_version=BLM_MLRS_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=BLM_MLRS_CAVEAT,
            is_source_failure=True,
            source_date=finished_at.date().isoformat(),
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_failed,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"BLM MLRS source failure: {failure_reason}",
                timestamp=finished_at,
            )
        )
        return BlmMlrsConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _feature_records(payload: Mapping[str, object]) -> tuple[_BlmMlrsRecord, ...]:
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("BLM MLRS response missing features list")
    records: list[_BlmMlrsRecord] = []
    for feature in features:
        if not isinstance(feature, Mapping):
            raise ValueError("BLM MLRS feature must be an object")
        attributes = feature.get("attributes")
        if not isinstance(attributes, Mapping):
            raise ValueError("BLM MLRS feature missing attributes")
        object_id = _attribute_text(attributes, "OBJECTID")
        case_serial_number = _attribute_text(attributes, "CSE_NR")
        if not object_id or not case_serial_number:
            raise ValueError("BLM MLRS feature missing OBJECTID or CSE_NR")
        records.append(
            _BlmMlrsRecord(
                object_id=object_id,
                case_serial_number=case_serial_number,
                legacy_case_serial_number=_attribute_text(attributes, "LEG_CSE_NR"),
                case_name=_attribute_text(attributes, "CSE_NAME"),
                case_disposition=_attribute_text(attributes, "CSE_DISP"),
                case_type_number=_attribute_text(attributes, "CSE_TYPE_NR"),
                product=_attribute_text(attributes, "BLM_PROD"),
                data_quality_note=_attribute_text(attributes, "QLTY"),
                recorded_acres=_attribute_float(attributes, "RCRD_ACRS"),
            )
        )
    return tuple(records)


def _attribute_text(attributes: Mapping[str, object], key: str) -> str:
    value = attributes.get(key)
    if value is None:
        return ""
    return " ".join(str(value).split())


def _attribute_float(attributes: Mapping[str, object], key: str) -> float | None:
    value = attributes.get(key)
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _build_query_url(*, bbox: BlmMlrsBbox, max_features: int) -> str:
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
            "outFields": (
                "OBJECTID,CSE_NR,LEG_CSE_NR,CSE_NAME,CSE_DISP,CSE_TYPE_NR,"
                "BLM_PROD,QLTY,RCRD_ACRS"
            ),
            "returnGeometry": "false",
            "f": "json",
            "resultRecordCount": str(max_features),
        }
    )
    return f"{BLM_MLRS_LAYER_URL}/query?{query}"


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    with urlopen(url, timeout=timeout_seconds) as response:  # noqa: S310 - reviewed public URL
        payload = response.read()
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("BLM MLRS response was not a JSON object")
    return cast(Mapping[str, object], data)


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "BLM_MLRS_CAVEAT",
    "BLM_MLRS_CONNECTOR_NAME",
    "BLM_MLRS_LAYER_URL",
    "BLM_MLRS_MAX_BBOX_DEGREES",
    "BLM_MLRS_MAX_FEATURES",
    "BLM_MLRS_METHOD_CODE",
    "BLM_MLRS_SPATIAL_PRECISION_METERS",
    "BlmMlrsBbox",
    "BlmMlrsConnector",
    "BlmMlrsConnectorError",
    "BlmMlrsConnectorResult",
    "JsonFetcher",
]
