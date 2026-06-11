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

CENSUS_TIGER_CONNECTOR_NAME = "census_tiger_geography_live"
CENSUS_TIGER_METHOD_CODE = "live_census_tigerweb_geography_context"
CENSUS_TIGER_METHOD_VERSION = "0.1.0"
CENSUS_TIGER_SERVICE_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/Tracts_Blocks/MapServer"
)
CENSUS_TIGER_MAX_BBOX_DEGREES = 0.5
CENSUS_TIGER_MAX_FEATURES = 50
CENSUS_TIGER_SPATIAL_PRECISION_METERS = 500.0
CENSUS_TIGER_CAVEAT = (
    "Census TIGERweb geography-context screening only. This connector records tract "
    "and block-group identifiers/names for administrative context; it does not use ACS "
    "demographic variables, protected-class characteristics, neighborhood desirability, "
    "market value, investment suitability, or residential steering signals. Census API "
    "terms require non-endorsement notice and prohibit re-identification attempts. Data: "
    "U.S. Census Bureau TIGERweb GeoServices; cite retrieval date and vintage."
)

_NAMESPACE = UUID("9a3f49f6-1c85-47fb-84d1-9712a0a8a1aa")

JsonFetcher = Callable[[str, float], Mapping[str, object]]


class CensusTigerConnectorError(ValueError):
    """Raised when a Census TIGERweb request is invalid before source I/O."""


@dataclass(frozen=True)
class CensusTigerBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise CensusTigerConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise CensusTigerConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise CensusTigerConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise CensusTigerConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > CENSUS_TIGER_MAX_BBOX_DEGREES:
            raise CensusTigerConnectorError("bbox longitude span exceeds Census TIGER limit")
        if self.ymax - self.ymin > CENSUS_TIGER_MAX_BBOX_DEGREES:
            raise CensusTigerConnectorError("bbox latitude span exceeds Census TIGER limit")

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"

    @property
    def envelope(self) -> str:
        return f"{self.xmin:.6f},{self.ymin:.6f},{self.xmax:.6f},{self.ymax:.6f}"


@dataclass(frozen=True)
class CensusTigerConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class CensusTigerConnector:
    """Bounded Census TIGERweb tract/block-group geography connector."""

    connector_name = CENSUS_TIGER_CONNECTOR_NAME
    domain = "census_geography"

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
        bbox: CensusTigerBbox,
        max_features: int = CENSUS_TIGER_MAX_FEATURES,
    ) -> CensusTigerConnectorResult:
        if max_features <= 0:
            raise CensusTigerConnectorError("max_features must be positive")
        if max_features > CENSUS_TIGER_MAX_FEATURES:
            raise CensusTigerConnectorError("max_features exceeds Census TIGER limit")

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
        request_url = _build_query_url(layer_id=0, bbox=bbox, max_features=max_features)

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_started,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message="starting Census TIGERweb geography context query",
                timestamp=started_at,
            )
        )

        check_connector_source_license(self._source)

        try:
            tracts_payload = self._fetch_json(request_url, self._policy.timeout_seconds)
            block_groups_url = _build_query_url(
                layer_id=1,
                bbox=bbox,
                max_features=max_features,
            )
            block_groups_payload = self._fetch_json(
                block_groups_url,
                self._policy.timeout_seconds,
            )
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="census_tiger_request_error",
                error_message=str(exc),
                retryable=True,
            )

        if _transfer_limit_exceeded(tracts_payload) or _transfer_limit_exceeded(
            block_groups_payload
        ):
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="census_tiger_response_truncated",
                error_message="TIGERweb response exceeded transfer limit; use a smaller bbox",
                retryable=False,
            )

        try:
            tracts = _feature_records(tracts_payload, level="tract")
            block_groups = _feature_records(block_groups_payload, level="block_group")
        except ValueError as exc:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="census_tiger_malformed_response",
                error_message=str(exc),
                retryable=True,
            )

        finished_at = _utcnow()
        tract_geoids = tuple(record["geoid"] for record in tracts)
        block_group_geoids = tuple(record["geoid"] for record in block_groups)
        row_count = len(tracts) + len(block_groups)

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
                "tract_count": len(tracts),
                "block_group_count": len(block_groups),
                "census_tiger_bbox": bbox.envelope,
                "accessed_at": finished_at.isoformat(),
            },
        )
        observed_value: dict[str, object] = {
            "has_census_geography_context": row_count > 0,
            "census_tract_count": len(tracts),
            "census_block_group_count": len(block_groups),
            "census_tract_geoids": list(tract_geoids),
            "census_block_group_geoids": list(block_group_geoids),
            "census_tiger_bbox": bbox.envelope,
            "census_tiger_vintage": "2025",
            "census_demographics_used": False,
        }
        if tracts:
            observed_value["primary_census_tract_geoid"] = tracts[0]["geoid"]
            observed_value["primary_census_tract_name"] = tracts[0]["name"]
        if block_groups:
            observed_value["primary_census_block_group_geoid"] = block_groups[0]["geoid"]
            observed_value["primary_census_block_group_name"] = block_groups[0]["name"]

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
            evidence_code="CENSUS_TIGER_GEOGRAPHY_CONTEXT",
            domain=self.domain,
            observation=(
                f"Census TIGERweb geography query found {len(tracts)} tract(s) and "
                f"{len(block_groups)} block group(s) intersecting the query area."
            ),
            observed_value=observed_value,
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=CENSUS_TIGER_METHOD_CODE,
            method_version=CENSUS_TIGER_METHOD_VERSION,
            confidence=ConfidenceBand.MEDIUM if row_count > 0 else ConfidenceBand.LOW,
            caveat=CENSUS_TIGER_CAVEAT,
            is_source_failure=False,
            source_date=finished_at.date().isoformat(),
            observed_at=finished_at,
            geometry_geojson=None,
            geometry_srid=4326,
            spatial_precision_meters=CENSUS_TIGER_SPATIAL_PRECISION_METERS,
        )

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.evidence_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"Census TIGER geography evidence: {evidence.evidence_id}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"Census TIGER geography query: row_count={row_count}",
                timestamp=finished_at,
            )
        )
        return CensusTigerConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: CensusTigerBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> CensusTigerConnectorResult:
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
                "census_tiger_bbox": bbox.envelope,
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
            evidence_code="CENSUS_TIGER_SOURCE_FAILURE",
            domain=self.domain,
            observation="Census TIGERweb geography query did not produce usable source data.",
            observed_value={
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
                "attempted_url": request_url,
                "connector": self.connector_name,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=CENSUS_TIGER_METHOD_CODE,
            method_version=CENSUS_TIGER_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=CENSUS_TIGER_CAVEAT,
            is_source_failure=True,
            source_date=finished_at.date().isoformat(),
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_failed,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"Census TIGER source failure: {failure_reason}",
                timestamp=finished_at,
            )
        )
        return CensusTigerConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _feature_records(payload: Mapping[str, object], *, level: str) -> tuple[dict[str, str], ...]:
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Census TIGERweb response missing 'features' list")
    records: list[dict[str, str]] = []
    for feature in features:
        if not isinstance(feature, Mapping):
            raise ValueError("Census TIGERweb feature is not an object")
        attributes = feature.get("attributes")
        if not isinstance(attributes, Mapping):
            raise ValueError("Census TIGERweb feature missing attributes")
        geoid = _string_attr(attributes, "GEOID")
        name = _string_attr(attributes, "NAME")
        record = {
            "geoid": geoid,
            "name": name,
            "state": _string_attr(attributes, "STATE"),
            "county": _string_attr(attributes, "COUNTY"),
            "tract": _string_attr(attributes, "TRACT"),
            "level": level,
        }
        block_group = attributes.get("BLKGRP")
        if block_group is not None:
            record["block_group"] = str(block_group)
        records.append(record)
    return tuple(records)


def _string_attr(attributes: Mapping[str, object], key: str) -> str:
    value = attributes.get(key)
    if value is None:
        raise ValueError(f"Census TIGERweb feature missing {key}")
    return str(value)


def _transfer_limit_exceeded(payload: Mapping[str, object]) -> bool:
    return payload.get("exceededTransferLimit") is True


def _build_query_url(
    *,
    layer_id: int,
    bbox: CensusTigerBbox,
    max_features: int,
) -> str:
    query = urlencode(
        {
            "f": "json",
            "where": "1=1",
            "geometry": bbox.envelope,
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": (
                "GEOID,BASENAME,NAME,STATE,COUNTY,TRACT"
                + (",BLKGRP" if layer_id == 1 else "")
            ),
            "returnGeometry": "false",
            "resultRecordCount": str(max_features),
        }
    )
    return f"{CENSUS_TIGER_SERVICE_URL}/{layer_id}/query?{query}"


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    with urlopen(url, timeout=timeout_seconds) as response:  # noqa: S310 - reviewed public URL
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Census TIGERweb response was not a JSON object")
    return cast(Mapping[str, object], payload)


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "CENSUS_TIGER_CAVEAT",
    "CENSUS_TIGER_CONNECTOR_NAME",
    "CENSUS_TIGER_MAX_BBOX_DEGREES",
    "CENSUS_TIGER_MAX_FEATURES",
    "CENSUS_TIGER_METHOD_CODE",
    "CENSUS_TIGER_SERVICE_URL",
    "CensusTigerBbox",
    "CensusTigerConnector",
    "CensusTigerConnectorError",
    "CensusTigerConnectorResult",
]
