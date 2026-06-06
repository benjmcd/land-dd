from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
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

SSURGO_CONNECTOR_NAME = "ssurgo_live"
SSURGO_METHOD_CODE = "live_usda_ssurgo_soil_mapunit_query"
SSURGO_METHOD_VERSION = "0.1.0"
SSURGO_POST_REST_URL = "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest"
SSURGO_MAX_ROWS = 1000
SSURGO_MAX_BBOX_DEGREES = 0.25
SSURGO_CAVEAT = (
    "USDA NRCS Web Soil Survey/SSURGO screening only; not a site-specific soil "
    "test, septic/percolation approval, engineering report, permitting decision, "
    "legal/buildability conclusion, wetland delineation, lending, appraisal, or "
    "investment advice. Cite Soil Survey Staff, Natural Resources Conservation "
    "Service, United States Department of Agriculture, Web Soil Survey, source URL, "
    "access date, and preserve survey/refresh, map-unit, scale, and component caveats."
)

_NAMESPACE = UUID("52c199a5-94b6-4216-8157-bc859fd3e676")

SsurgoJsonFetcher = Callable[[str, float], Mapping[str, object]]


class SsurgoConnectorError(ValueError):
    """Raised when a SSURGO connector request is invalid before source I/O."""


@dataclass(frozen=True)
class SsurgoBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise SsurgoConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise SsurgoConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise SsurgoConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise SsurgoConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > SSURGO_MAX_BBOX_DEGREES:
            raise SsurgoConnectorError("bbox longitude span exceeds SSURGO limit")
        if self.ymax - self.ymin > SSURGO_MAX_BBOX_DEGREES:
            raise SsurgoConnectorError("bbox latitude span exceeds SSURGO limit")

    @property
    def wkt_polygon(self) -> str:
        return (
            "polygon(("
            f"{self.xmin:.8f} {self.ymin:.8f},"
            f"{self.xmin:.8f} {self.ymax:.8f},"
            f"{self.xmax:.8f} {self.ymax:.8f},"
            f"{self.xmax:.8f} {self.ymin:.8f},"
            f"{self.xmin:.8f} {self.ymin:.8f}"
            "))"
        )

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"


@dataclass(frozen=True)
class SsurgoConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str
    request_query: str


class SsurgoConnector:
    """Bounded USDA NRCS Soil Data Access connector for SSURGO mapunit screening."""

    connector_name = SSURGO_CONNECTOR_NAME
    domain = "soil_septic"

    def __init__(
        self,
        *,
        source: SourceContract,
        fetch_json: SsurgoJsonFetcher | None = None,
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
        bbox: SsurgoBbox,
        max_rows: int = SSURGO_MAX_ROWS,
    ) -> SsurgoConnectorResult:
        if max_rows <= 0 or max_rows > SSURGO_MAX_ROWS:
            raise SsurgoConnectorError("max_rows must be between 1 and 1000")

        log = new_observability_log()
        started_at = _utcnow()
        ingest_run_id = _stable_uuid(
            "retrieval",
            str(self._source.source_id),
            str(area_id),
            bbox.fingerprint,
            str(max_rows),
        )
        request_query = _build_query(bbox=bbox, max_rows=max_rows)
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_started,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message="starting bounded USDA NRCS SSURGO mapunit query",
                timestamp=started_at,
            )
        )

        check_connector_source_license(self._source)

        try:
            payload = self._fetch_json(request_query, self._policy.timeout_seconds)
        except HTTPError as exc:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_query=request_query,
                started_at=started_at,
                log=log,
                failure_reason="ssurgo_http_error",
                error_message=str(exc),
                retryable=True,
                status_code=exc.code,
            )
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_query=request_query,
                started_at=started_at,
                log=log,
                failure_reason="ssurgo_request_error",
                error_message=str(exc),
                retryable=True,
                status_code=None,
            )

        if "error" in payload:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_query=request_query,
                started_at=started_at,
                log=log,
                failure_reason="ssurgo_service_error",
                error_message=_error_message(payload["error"]),
                retryable=True,
                status_code=None,
            )

        rows_result = _table_rows(payload)
        if isinstance(rows_result, str):
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_query=request_query,
                started_at=started_at,
                log=log,
                failure_reason="ssurgo_malformed_response",
                error_message=rows_result,
                retryable=True,
                status_code=None,
            )
        rows = rows_result
        if not rows:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_query=request_query,
                started_at=started_at,
                log=log,
                failure_reason="ssurgo_no_mapunits",
                error_message="SSURGO query returned no intersecting mapunit rows",
                retryable=False,
                status_code=None,
            )

        finished_at = _utcnow()
        evidence_result = self._rows_to_evidence(
            rows=rows,
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
                request_query=request_query,
                started_at=started_at,
                log=log,
                failure_reason="ssurgo_malformed_row",
                error_message=evidence_result,
                retryable=True,
                status_code=None,
            )
        evidence_inputs = evidence_result
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=len(rows),
            error_count=0,
            warning_count=0,
            log_uri=SSURGO_POST_REST_URL,
            metrics={
                "source_registry_id": self._source.metadata.get("source_registry_id"),
                "service_url": SSURGO_POST_REST_URL,
                "bbox": bbox.fingerprint,
                "max_rows": max_rows,
                "format": "JSON+COLUMNNAME",
                "accessed_at": finished_at.isoformat(),
                "official_source": "USDA NRCS Soil Data Access / SSURGO",
            },
        )
        for evidence in evidence_inputs:
            log.record(
                ConnectorObservabilityEvent(
                    event_type=ConnectorEventType.evidence_stored,
                    connector_name=self.connector_name,
                    ingest_run_id=ingest_run_id,
                    message=f"SSURGO soil mapunit evidence: {evidence.evidence_id}",
                    timestamp=finished_at,
                )
            )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"SSURGO query returned {len(evidence_inputs)} mapunit rows",
                timestamp=finished_at,
            )
        )
        return SsurgoConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=evidence_inputs,
            observability_log=log,
            request_url=SSURGO_POST_REST_URL,
            request_query=request_query,
        )

    def _rows_to_evidence(
        self,
        *,
        rows: list[Mapping[str, object]],
        area_id: UUID,
        bbox: SsurgoBbox,
        ingest_run_id: UUID,
        observed_at: datetime,
    ) -> tuple[EvidenceContract, ...] | str:
        evidence_inputs: list[EvidenceContract] = []
        for row in rows:
            mukey = _optional_text(row.get("mukey"))
            if mukey is None:
                return "SSURGO row did not include mukey"
            cokey = _optional_text(row.get("cokey")) or "no-component"
            evidence_inputs.append(
                EvidenceContract(
                    evidence_id=_stable_uuid(
                        "evidence",
                        str(self._source.source_id),
                        str(area_id),
                        bbox.fingerprint,
                        mukey,
                        cokey,
                    ),
                    area_id=area_id,
                    evidence_type=EvidenceType.SPATIAL_INTERSECTION,
                    evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
                    domain=self.domain,
                    observation=(
                        "USDA NRCS SSURGO mapunit intersects the query area for "
                        "soil/septic/ag screening."
                    ),
                    observed_value={
                        "intersects_soil_mapunit": True,
                        "soil_mapunit_key": mukey,
                        "soil_mapunit_symbol": _optional_text(row.get("musym")),
                        "soil_mapunit_name": _optional_text(row.get("muname")),
                        "soil_component_key": _optional_text(row.get("cokey")),
                        "soil_component_name": _optional_text(row.get("compname")),
                        "soil_component_percent": _optional_number(row.get("comppct_r")),
                        "soil_major_component": _yes_no(row.get("majcompflag")),
                        "hydric_rating": _optional_text(row.get("hydricrating")),
                        "drainage_class": _optional_text(row.get("drainagecl")),
                        "hydrologic_group": _optional_text(row.get("hydgrp")),
                        "slope_percent": _optional_number(row.get("slope_r")),
                    },
                    source_id=self._source.source_id,
                    source_ingest_run_id=ingest_run_id,
                    method_code=SSURGO_METHOD_CODE,
                    method_version=SSURGO_METHOD_VERSION,
                    confidence=ConfidenceBand.MEDIUM,
                    caveat=SSURGO_CAVEAT,
                    is_source_failure=False,
                    source_date=observed_at.date().isoformat(),
                    observed_at=observed_at,
                )
            )
        return tuple(evidence_inputs)

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: SsurgoBbox,
        ingest_run_id: UUID,
        request_query: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
        status_code: int | None,
    ) -> SsurgoConnectorResult:
        finished_at = _utcnow()
        observed_value: dict[str, object] = {
            "attempted_url": SSURGO_POST_REST_URL,
            "failure_reason": failure_reason,
            "error_message": error_message,
            "retryable": retryable,
        }
        if status_code is not None:
            observed_value["status_code"] = status_code
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.FAILED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=0,
            error_count=1,
            warning_count=0,
            log_uri=SSURGO_POST_REST_URL,
            metrics={
                "source_registry_id": self._source.metadata.get("source_registry_id"),
                "service_url": SSURGO_POST_REST_URL,
                "bbox": bbox.fingerprint,
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
                "status_code": status_code,
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
            evidence_code="SSURGO_SOURCE_FAILURE",
            domain=self.domain,
            observation="USDA NRCS SSURGO query did not produce usable source data.",
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=SSURGO_METHOD_CODE,
            method_version=SSURGO_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=SSURGO_CAVEAT,
            is_source_failure=True,
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.source_failure_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"SSURGO source failure: {failure_reason}",
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
        return SsurgoConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=SSURGO_POST_REST_URL,
            request_query=request_query,
        )


def _build_query(*, bbox: SsurgoBbox, max_rows: int) -> str:
    wkt = bbox.wkt_polygon.replace("'", "''")
    return f"""
select top {max_rows}
  mu.mukey, mu.musym, mu.muname,
  co.cokey, co.compname, co.comppct_r, co.majcompflag,
  co.hydricrating, co.drainagecl, co.hydgrp, co.slope_r
from SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}') aoi
join mapunit mu on mu.mukey = aoi.mukey
left join component co on co.mukey = mu.mukey and co.majcompflag = 'Yes'
order by mu.mukey, co.comppct_r desc
""".strip()


def _fetch_json(query: str, timeout_seconds: float) -> Mapping[str, object]:
    data = urlencode({"query": query, "format": "JSON+COLUMNNAME"}).encode("utf-8")
    request = Request(SSURGO_POST_REST_URL, data=data, method="POST")
    with urlopen(request, timeout=timeout_seconds or None) as response:
        payload = response.read().decode("utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, Mapping):
        raise ValueError("SSURGO response root must be a JSON object")
    return cast(Mapping[str, object], parsed)


def _table_rows(payload: Mapping[str, object]) -> list[Mapping[str, object]] | str:
    table = payload.get("Table")
    if not isinstance(table, list):
        return "SSURGO response did not include a Table array"
    if not table:
        return []
    header = table[0]
    if not isinstance(header, list) or not all(isinstance(item, str) for item in header):
        return "SSURGO response Table did not start with a column-name row"
    rows: list[Mapping[str, object]] = []
    for raw_row in table[1:]:
        if not isinstance(raw_row, list):
            return "SSURGO response Table included a non-array data row"
        if len(raw_row) != len(header):
            return "SSURGO response Table row length did not match column-name row"
        rows.append(dict(zip(cast(list[str], header), raw_row, strict=True)))
    return rows


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_number(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _yes_no(value: object) -> bool | None:
    text = _optional_text(value)
    if text is None:
        return None
    if text.lower() == "yes":
        return True
    if text.lower() == "no":
        return False
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
    "SSURGO_CAVEAT",
    "SSURGO_CONNECTOR_NAME",
    "SSURGO_MAX_BBOX_DEGREES",
    "SSURGO_MAX_ROWS",
    "SSURGO_METHOD_CODE",
    "SSURGO_POST_REST_URL",
    "SsurgoBbox",
    "SsurgoConnector",
    "SsurgoConnectorError",
    "SsurgoConnectorResult",
]
