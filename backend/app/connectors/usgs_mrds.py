from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import UUID, uuid5
from xml.etree import ElementTree

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

USGS_MRDS_CONNECTOR_NAME = "usgs_mrds_mineral_occurrence_live"
USGS_MRDS_METHOD_CODE = "live_usgs_mrds_wfs_mineral_occurrence_screen"
USGS_MRDS_METHOD_VERSION = "0.1.0"
USGS_MRDS_WFS_URL = "https://mrdata.usgs.gov/services/wfs/mrds"
USGS_MRDS_MAX_BBOX_DEGREES = 1.0
USGS_MRDS_MAX_FEATURES = 50
USGS_MRDS_SPATIAL_PRECISION_METERS = 1000.0
USGS_MRDS_CAVEAT = (
    "USGS MRDS historical mineral-occurrence screening only. MRDS systematic updates "
    "ceased in 2011, records vary in quality, and occurrence proximity does not "
    "establish mineral rights, severed mineral estate status, mine hazards, resource "
    "value, extraction feasibility, environmental liability, buildability, appraisal, "
    "lending suitability, insurance suitability, or investment suitability. Data: "
    "U.S. Geological Survey Mineral Resources Data System; cite retrieval date and "
    "record URLs. Treat as historical screening signal only."
)

_NAMESPACE = UUID("60a6a72f-4578-42a7-b7c0-9d760d7df57c")
_MS_NS = "http://mapserver.gis.umn.edu/mapserver"
_GML_NS = "http://www.opengis.net/gml"

TextFetcher = Callable[[str, float], str]


class UsgsMrdsConnectorError(ValueError):
    """Raised when an MRDS connector request is invalid before source I/O."""


@dataclass(frozen=True)
class UsgsMrdsBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise UsgsMrdsConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise UsgsMrdsConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise UsgsMrdsConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise UsgsMrdsConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > USGS_MRDS_MAX_BBOX_DEGREES:
            raise UsgsMrdsConnectorError("bbox longitude span exceeds USGS MRDS limit")
        if self.ymax - self.ymin > USGS_MRDS_MAX_BBOX_DEGREES:
            raise UsgsMrdsConnectorError("bbox latitude span exceeds USGS MRDS limit")

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"

    @property
    def wfs_bbox(self) -> str:
        return f"{self.xmin:.6f},{self.ymin:.6f},{self.xmax:.6f},{self.ymax:.6f}"


@dataclass(frozen=True)
class UsgsMrdsConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class UsgsMrdsConnector:
    """Bounded USGS MRDS mineral-occurrence WFS screening connector."""

    connector_name = USGS_MRDS_CONNECTOR_NAME
    domain = "minerals"

    def __init__(
        self,
        *,
        source: SourceContract,
        fetch_text: TextFetcher | None = None,
        policy: ConnectorPolicy | None = None,
    ) -> None:
        self._source = source
        self._fetch_text = fetch_text or _fetch_text
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
        bbox: UsgsMrdsBbox,
        max_features: int = USGS_MRDS_MAX_FEATURES,
    ) -> UsgsMrdsConnectorResult:
        if max_features <= 0:
            raise UsgsMrdsConnectorError("max_features must be positive")
        if max_features > USGS_MRDS_MAX_FEATURES:
            raise UsgsMrdsConnectorError("max_features exceeds USGS MRDS limit")

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
                message="starting USGS MRDS mineral occurrence WFS query",
                timestamp=started_at,
            )
        )

        check_connector_source_license(self._source)

        try:
            payload = self._fetch_text(request_url, self._policy.timeout_seconds)
            records = _parse_records(payload)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="usgs_mrds_request_or_parse_error",
                error_message=str(exc),
                retryable=True,
            )

        if len(records) >= max_features:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="usgs_mrds_response_may_be_truncated",
                error_message="MRDS WFS response reached max_features; use a smaller bbox",
                retryable=False,
            )

        finished_at = _utcnow()
        occurrence_count = len(records)
        has_context = occurrence_count > 0
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=occurrence_count,
            error_count=0,
            warning_count=0,
            log_uri=request_url,
            metrics={
                "source_registry_id": source_registry_id,
                "mineral_occurrence_count": occurrence_count,
                "mrds_bbox": bbox.wfs_bbox,
                "accessed_at": finished_at.isoformat(),
            },
        )

        observed_value: dict[str, object] = {
            "has_mineral_occurrence_context": has_context,
            "no_mineral_occurrence_context": not has_context,
            "mineral_occurrence_count": occurrence_count,
            "mrds_bbox": bbox.wfs_bbox,
            "mrds_systematic_updates_ceased": "2011",
            "mineral_rights_determined": False,
            "mineral_deposit_ids": [record["dep_id"] for record in records],
            "mineral_site_names": [record["site_name"] for record in records],
            "mineral_development_statuses": [record["dev_stat"] for record in records],
            "mineral_commodity_codes": [record["code_list"] for record in records],
            "mrds_record_urls": [record["url"] for record in records],
        }
        if records:
            observed_value["primary_mineral_deposit_id"] = records[0]["dep_id"]
            observed_value["primary_mineral_site_name"] = records[0]["site_name"]
            observed_value["primary_mineral_development_status"] = records[0]["dev_stat"]

        observation = (
            f"USGS MRDS WFS query found {occurrence_count} historical mineral "
            "occurrence record(s) intersecting the query bounding box."
        )
        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                source_registry_id,
                str(area_id),
                bbox.fingerprint,
                str(occurrence_count),
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="MRDS_MINERAL_OCCURRENCE_SCREEN",
            domain=self.domain,
            observation=observation,
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=USGS_MRDS_METHOD_CODE,
            method_version=USGS_MRDS_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=USGS_MRDS_CAVEAT,
            is_source_failure=False,
            source_date=finished_at.date().isoformat(),
            observed_at=finished_at,
            geometry_geojson=None,
            geometry_srid=4326,
            spatial_precision_meters=USGS_MRDS_SPATIAL_PRECISION_METERS,
        )

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.evidence_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"USGS MRDS minerals evidence: {evidence.evidence_id}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"USGS MRDS mineral occurrence screen: row_count={occurrence_count}",
                timestamp=finished_at,
            )
        )
        return UsgsMrdsConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: UsgsMrdsBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> UsgsMrdsConnectorResult:
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
                "mrds_bbox": bbox.wfs_bbox,
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
            evidence_code="USGS_MRDS_SOURCE_FAILURE",
            domain=self.domain,
            observation="USGS MRDS WFS query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
                "attempted_url": request_url,
                "connector": self.connector_name,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=USGS_MRDS_METHOD_CODE,
            method_version=USGS_MRDS_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=USGS_MRDS_CAVEAT,
            is_source_failure=True,
            source_date=finished_at.date().isoformat(),
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_failed,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"USGS MRDS source failure: {failure_reason}",
                timestamp=finished_at,
            )
        )
        return UsgsMrdsConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _parse_records(payload: str) -> tuple[dict[str, str], ...]:
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise ValueError(f"MRDS WFS XML parse error: {exc}") from exc
    exception_text = _exception_text(root)
    if exception_text:
        raise ValueError(f"MRDS WFS exception: {exception_text}")
    records: list[dict[str, str]] = []
    for feature in root.findall(f".//{{{_MS_NS}}}mrds"):
        record = {
            "dep_id": _child_text(feature, "dep_id"),
            "site_name": _child_text(feature, "site_name"),
            "dev_stat": _child_text(feature, "dev_stat"),
            "code_list": _child_text(feature, "code_list"),
            "url": _child_text(feature, "url"),
        }
        if not record["dep_id"]:
            raise ValueError("MRDS WFS feature missing dep_id")
        records.append(record)
    return tuple(records)


def _child_text(feature: ElementTree.Element, field_name: str) -> str:
    child = feature.find(f"{{{_MS_NS}}}{field_name}")
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _exception_text(root: ElementTree.Element) -> str | None:
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name in {"ExceptionText", "ServiceException"}:
            text = (element.text or "").strip()
            return text or "unspecified WFS exception"
    return None


def _build_query_url(*, bbox: UsgsMrdsBbox, max_features: int) -> str:
    query = urlencode(
        {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": "mrds",
            "bbox": bbox.wfs_bbox,
            "maxFeatures": str(max_features),
        }
    )
    return f"{USGS_MRDS_WFS_URL}?{query}"


def _fetch_text(url: str, timeout_seconds: float) -> str:
    with urlopen(url, timeout=timeout_seconds) as response:  # noqa: S310 - reviewed public URL
        payload = response.read()
    if not isinstance(payload, bytes):
        raise ValueError("MRDS WFS response body was not bytes")
    return payload.decode("utf-8")


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "USGS_MRDS_CAVEAT",
    "USGS_MRDS_CONNECTOR_NAME",
    "USGS_MRDS_MAX_BBOX_DEGREES",
    "USGS_MRDS_MAX_FEATURES",
    "USGS_MRDS_METHOD_CODE",
    "USGS_MRDS_WFS_URL",
    "TextFetcher",
    "UsgsMrdsBbox",
    "UsgsMrdsConnector",
    "UsgsMrdsConnectorError",
    "UsgsMrdsConnectorResult",
]
