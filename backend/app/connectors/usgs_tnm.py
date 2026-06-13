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

USGS_TNM_CONNECTOR_NAME = "usgs_tnm_elevation_live"
USGS_TNM_METHOD_CODE = "live_usgs_tnm_epqs_elevation_sample"
USGS_TNM_METHOD_VERSION = "0.1.0"
USGS_TNM_EPQS_URL = "https://epqs.nationalmap.gov/v1/json"
USGS_TNM_MAX_BBOX_DEGREES = 0.25
USGS_TNM_MAX_SAMPLE_POINTS = 9
USGS_TNM_NO_DATA_ELEVATION = -1000000.0
USGS_TNM_CAVEAT = (
    "USGS The National Map / 3DEP EPQS terrain screening only; point elevations are "
    "interpolated and are not official surveyed ground control, engineering design, "
    "site-plan approval, legal boundary, access, water-rights, wetland jurisdiction, "
    "buildability, lending, appraisal, or investment determinations. Cite U.S. "
    "Geological Survey / The National Map, retrieval date, service URL, sample points, "
    "and available acquisition/source metadata."
)

_NAMESPACE = UUID("f6d16b13-3cc8-47a3-8f19-cc6fba576b46")

UsgsTnmJsonFetcher = Callable[[str, float], Mapping[str, object]]


class UsgsTnmConnectorError(ValueError):
    """Raised when a USGS TNM connector request is invalid before source I/O."""


@dataclass(frozen=True)
class UsgsTnmBbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin >= self.xmax:
            raise UsgsTnmConnectorError("bbox xmin must be less than xmax")
        if self.ymin >= self.ymax:
            raise UsgsTnmConnectorError("bbox ymin must be less than ymax")
        if not (-180 <= self.xmin <= 180 and -180 <= self.xmax <= 180):
            raise UsgsTnmConnectorError("bbox longitude values must be within EPSG:4326")
        if not (-90 <= self.ymin <= 90 and -90 <= self.ymax <= 90):
            raise UsgsTnmConnectorError("bbox latitude values must be within EPSG:4326")
        if self.xmax - self.xmin > USGS_TNM_MAX_BBOX_DEGREES:
            raise UsgsTnmConnectorError("bbox longitude span exceeds USGS TNM limit")
        if self.ymax - self.ymin > USGS_TNM_MAX_BBOX_DEGREES:
            raise UsgsTnmConnectorError("bbox latitude span exceeds USGS TNM limit")

    @property
    def fingerprint(self) -> str:
        return f"{self.xmin:.8f},{self.ymin:.8f},{self.xmax:.8f},{self.ymax:.8f}"

    @property
    def sample_points(self) -> tuple[tuple[float, float], ...]:
        x_mid = (self.xmin + self.xmax) / 2
        y_mid = (self.ymin + self.ymax) / 2
        return (
            (x_mid, y_mid),
            (self.xmin, self.ymin),
            (self.xmin, self.ymax),
            (self.xmax, self.ymin),
            (self.xmax, self.ymax),
        )


@dataclass(frozen=True)
class UsgsTnmElevationSample:
    x: float
    y: float
    elevation_m: float
    data_source: str | None
    acquisition_date: str | None
    resolution_m: float | None


@dataclass(frozen=True)
class UsgsTnmConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog
    request_url: str


class UsgsTnmElevationConnector:
    """Bounded USGS The National Map EPQS connector for terrain screening.

    This connector samples a small fixed set of EPQS points inside an EPSG:4326 bbox
    and emits one derived relief metric. It intentionally does not download DEM rasters,
    infer parcel boundaries, or determine buildability.
    """

    connector_name = USGS_TNM_CONNECTOR_NAME
    domain = "buildability"

    def __init__(
        self,
        *,
        source: SourceContract,
        fetch_json: UsgsTnmJsonFetcher | None = None,
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
        bbox: UsgsTnmBbox,
        max_sample_points: int = USGS_TNM_MAX_SAMPLE_POINTS,
    ) -> UsgsTnmConnectorResult:
        if max_sample_points <= 0 or max_sample_points > USGS_TNM_MAX_SAMPLE_POINTS:
            raise UsgsTnmConnectorError("max_sample_points must be between 1 and 9")

        sample_points = bbox.sample_points[:max_sample_points]
        log = new_observability_log()
        started_at = _utcnow()
        ingest_run_id = _stable_uuid(
            "retrieval",
            str(self._source.source_id),
            str(area_id),
            bbox.fingerprint,
            str(len(sample_points)),
        )
        request_url = _build_query_url(*sample_points[0])
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_started,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message="starting bounded USGS TNM EPQS elevation sampling",
                timestamp=started_at,
            )
        )

        check_connector_source_license(self._source)

        samples: list[UsgsTnmElevationSample] = []
        try:
            for x, y in sample_points:
                sample_url = _build_query_url(x, y)
                payload = self._fetch_json(sample_url, self._policy.timeout_seconds)
                sample_result = _parse_sample(payload, x=x, y=y)
                if isinstance(sample_result, str):
                    return self._source_failure_result(
                        area_id=area_id,
                        bbox=bbox,
                        ingest_run_id=ingest_run_id,
                        request_url=sample_url,
                        started_at=started_at,
                        log=log,
                        failure_reason="usgs_tnm_malformed_sample",
                        error_message=sample_result,
                        retryable=True,
                    )
                if sample_result.elevation_m <= USGS_TNM_NO_DATA_ELEVATION:
                    return self._source_failure_result(
                        area_id=area_id,
                        bbox=bbox,
                        ingest_run_id=ingest_run_id,
                        request_url=sample_url,
                        started_at=started_at,
                        log=log,
                        failure_reason="usgs_tnm_no_elevation",
                        error_message="USGS TNM EPQS returned no usable elevation value",
                        retryable=False,
                    )
                samples.append(sample_result)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            return self._source_failure_result(
                area_id=area_id,
                bbox=bbox,
                ingest_run_id=ingest_run_id,
                request_url=request_url,
                started_at=started_at,
                log=log,
                failure_reason="usgs_tnm_request_error",
                error_message=str(exc),
                retryable=True,
            )

        finished_at = _utcnow()
        evidence = self._samples_to_evidence(
            samples=samples,
            area_id=area_id,
            bbox=bbox,
            ingest_run_id=ingest_run_id,
            observed_at=finished_at,
        )
        elevations = [sample.elevation_m for sample in samples]
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=len(samples),
            error_count=0,
            warning_count=0,
            log_uri=request_url,
            metrics={
                "source_registry_id": self._source.metadata.get("source_registry_id"),
                "service_url": USGS_TNM_EPQS_URL,
                "bbox": bbox.fingerprint,
                "sample_count": len(samples),
                "min_elevation_m": min(elevations),
                "max_elevation_m": max(elevations),
                "relief_m": max(elevations) - min(elevations),
                "accessed_at": finished_at.isoformat(),
                "official_source": "USGS The National Map Elevation Point Query Service",
            },
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.evidence_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"USGS TNM terrain screening evidence: {evidence.evidence_id}",
                timestamp=finished_at,
            )
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"USGS TNM EPQS sampled {len(samples)} points",
                timestamp=finished_at,
            )
        )
        return UsgsTnmConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )

    def _samples_to_evidence(
        self,
        *,
        samples: list[UsgsTnmElevationSample],
        area_id: UUID,
        bbox: UsgsTnmBbox,
        ingest_run_id: UUID,
        observed_at: datetime,
    ) -> EvidenceContract:
        elevations = [sample.elevation_m for sample in samples]
        relief_m = max(elevations) - min(elevations)
        mean_elevation_m = sum(elevations) / len(elevations)
        acquisition_dates = sorted(
            {sample.acquisition_date for sample in samples if sample.acquisition_date}
        )
        return EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(self._source.source_id),
                str(area_id),
                bbox.fingerprint,
                str(len(samples)),
                f"{relief_m:.3f}",
            ),
            area_id=area_id,
            evidence_type=EvidenceType.DERIVED_METRIC,
            evidence_code="USGS_TNM_EPQS_RELIEF_SCREEN",
            domain=self.domain,
            observation=(
                "USGS The National Map EPQS point samples estimate terrain relief "
                "inside the query area for physical screening."
            ),
            observed_value={
                "metric_code": "tnm_epqs_sampled_relief_m",
                "value": relief_m,
                "unit": "m",
                "min_elevation_m": round(min(elevations), 1),
                "max_elevation_m": round(max(elevations), 1),
                "mean_elevation_m": round(mean_elevation_m, 1),
                "sample_count": len(samples),
                "calculation_method": "center_and_corner_epqs_point_sample_relief",
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=USGS_TNM_METHOD_CODE,
            method_version=USGS_TNM_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=USGS_TNM_CAVEAT,
            is_source_failure=False,
            source_date=_latest_source_date(acquisition_dates) or observed_at.date().isoformat(),
            observed_at=observed_at,
        )

    def _source_failure_result(
        self,
        *,
        area_id: UUID,
        bbox: UsgsTnmBbox,
        ingest_run_id: UUID,
        request_url: str,
        started_at: datetime,
        log: ConnectorRunObservabilityLog,
        failure_reason: str,
        error_message: str,
        retryable: bool,
    ) -> UsgsTnmConnectorResult:
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
                "service_url": USGS_TNM_EPQS_URL,
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
            evidence_code="USGS_TNM_EPQS_SOURCE_FAILURE",
            domain=self.domain,
            observation="USGS The National Map EPQS query did not produce usable terrain data.",
            observed_value={
                "attempted_url": request_url,
                "failure_reason": failure_reason,
                "error_message": error_message,
                "retryable": retryable,
            },
            source_id=self._source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=USGS_TNM_METHOD_CODE,
            method_version=USGS_TNM_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=USGS_TNM_CAVEAT,
            is_source_failure=True,
            observed_at=finished_at,
        )
        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.source_failure_stored,
                connector_name=self.connector_name,
                ingest_run_id=ingest_run_id,
                message=f"USGS TNM source failure: {failure_reason}",
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
        return UsgsTnmConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
            observability_log=log,
            request_url=request_url,
        )


def _parse_sample(
    payload: Mapping[str, object],
    *,
    x: float,
    y: float,
) -> UsgsTnmElevationSample | str:
    value = payload.get("value")
    data_source = _optional_text(payload.get("rasterId"))
    acquisition_date: str | None = None
    attributes = payload.get("attributes")
    if isinstance(attributes, Mapping):
        acquisition_date = _optional_text(attributes.get("AcquisitionDate"))
    resolution_m = _optional_number(payload.get("resolution"))

    legacy_root = payload.get("USGS_Elevation_Point_Query_Service")
    if value is None and isinstance(legacy_root, Mapping):
        legacy_query = legacy_root.get("Elevation_Query")
        if isinstance(legacy_query, Mapping):
            value = legacy_query.get("Elevation")
            data_source = _optional_text(legacy_query.get("Data_Source"))

    elevation_m = _optional_number(value)
    if elevation_m is None:
        return "USGS TNM EPQS response did not include a numeric elevation value"

    return UsgsTnmElevationSample(
        x=x,
        y=y,
        elevation_m=elevation_m,
        data_source=data_source,
        acquisition_date=acquisition_date,
        resolution_m=resolution_m,
    )


def _build_query_url(x: float, y: float) -> str:
    return f"{USGS_TNM_EPQS_URL}?{urlencode(_query_params(x, y))}"


def _query_params(x: float, y: float) -> dict[str, object]:
    return {
        "x": f"{x:.8f}",
        "y": f"{y:.8f}",
        "units": "Meters",
        "wkid": 4326,
        "includeDate": "true",
    }


def _fetch_json(url: str, timeout_seconds: float) -> Mapping[str, object]:
    with urlopen(url, timeout=timeout_seconds) as response:
        payload = json.load(response)
    if not isinstance(payload, Mapping):
        raise ValueError("USGS TNM EPQS response was not a JSON object")
    return cast(Mapping[str, object], payload)


def _latest_source_date(values: list[str]) -> str | None:
    parsed: list[datetime] = []
    for value in values:
        try:
            parsed.append(datetime.strptime(value, "%m/%d/%Y"))
        except ValueError:
            continue
    if not parsed:
        return None
    return max(parsed).date().isoformat()


def _optional_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "USGS_TNM_CAVEAT",
    "USGS_TNM_CONNECTOR_NAME",
    "USGS_TNM_EPQS_URL",
    "USGS_TNM_MAX_BBOX_DEGREES",
    "USGS_TNM_MAX_SAMPLE_POINTS",
    "USGS_TNM_METHOD_CODE",
    "UsgsTnmBbox",
    "UsgsTnmConnectorError",
    "UsgsTnmConnectorResult",
    "UsgsTnmElevationConnector",
    "UsgsTnmElevationSample",
]
