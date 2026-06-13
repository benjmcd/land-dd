from __future__ import annotations

import inspect
from typing import Any
from uuid import UUID, uuid4

import pytest

import app.connectors.usgs_tnm as usgs_tnm_module
from app.connectors.evidence_ingestion import ConnectorEvidenceIngestionAdapter
from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.observability import ConnectorEventType
from app.connectors.retrieval_provenance import ConnectorRetrievalProvenanceAdapter
from app.connectors.usgs_tnm import (
    USGS_TNM_CAVEAT,
    USGS_TNM_CONNECTOR_NAME,
    USGS_TNM_EPQS_URL,
    USGS_TNM_MAX_SAMPLE_POINTS,
    USGS_TNM_METHOD_CODE,
    UsgsTnmBbox,
    UsgsTnmConnectorError,
    UsgsTnmElevationConnector,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="USGS The National Map",
        organization="USGS",
        source_type="Public official",
        domain="Terrain/elevation/hydro/boundaries",
        geographic_scope="US",
        license_status=license_status,
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        attribution_required=True,
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        freshness_class="current-effective",
        last_checked_at="2026-06-05",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-001"},
    )


def _bbox() -> UsgsTnmBbox:
    return UsgsTnmBbox(xmin=-77.10, ymin=38.80, xmax=-77.00, ymax=38.90)


def _payload(elevation_m: float, *, acquisition_date: str = "11/3/2022") -> dict[str, object]:
    return {
        "location": {
            "x": -77.05,
            "y": 38.85,
            "spatialReference": {"wkid": 4326, "latestWkid": 4326},
        },
        "locationId": 0,
        "value": str(elevation_m),
        "rasterId": 20689,
        "resolution": 1,
        "attributes": {"AcquisitionDate": acquisition_date},
    }


class RecordingRetrievalPort:
    def __init__(self) -> None:
        self.recorded_runs: list[SourceRetrievalRunContract] = []

    def retrieval_run_exists(self, _ingest_run_id: UUID) -> bool:
        return False

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        self.recorded_runs.append(retrieval_run)
        return retrieval_run


class RecordingEvidencePort:
    def __init__(self) -> None:
        self.created_observations: list[EvidenceContract] = []

    def create_observation(self, evidence: EvidenceContract) -> EvidenceContract:
        self.created_observations.append(evidence)
        return evidence

    def create_source_failure(
        self,
        *,
        evidence_id: UUID | None = None,
        area_id: UUID,
        source_id: UUID,
        method_code: str,
        caveat: str,
        evidence_code: str = "SOURCE_FAILURE",
        domain: str = "unknown",
        observation: str | None = None,
        observed_value: dict[str, object] | None = None,
        source_ingest_run_id: UUID | None = None,
    ) -> EvidenceContract:
        raise AssertionError("success path should not create source failure")

    def evidence_exists(self, _evidence_id: UUID) -> bool:
        return False

    def list_by_area(self, _area_id: UUID) -> list[EvidenceContract]:
        return []


def test_success_query_samples_bounded_epqs_points_and_emits_relief_metric() -> None:
    urls: list[str] = []
    elevations = iter([9.0, 10.0, 12.0, 8.0, 11.0])
    source = _source()

    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        urls.append(url)
        assert timeout_seconds == 30.0
        return _payload(next(elevations))

    area_id = uuid4()
    result = UsgsTnmElevationConnector(
        source=source,
        fetch_json=fetch_json,
    ).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert len(urls) == 5
    assert all(url.startswith(f"{USGS_TNM_EPQS_URL}?") for url in urls)
    assert all("units=Meters" in url for url in urls)
    assert all("wkid=4326" in url for url in urls)
    assert all("includeDate=true" in url for url in urls)

    assert result.retrieval_run.connector_name == USGS_TNM_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 5
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-001"
    assert result.retrieval_run.metrics["service_url"] == USGS_TNM_EPQS_URL
    assert result.retrieval_run.metrics["sample_count"] == 5
    assert result.retrieval_run.metrics["min_elevation_m"] == 8.0
    assert result.retrieval_run.metrics["max_elevation_m"] == 12.0
    assert result.retrieval_run.metrics["relief_m"] == 4.0

    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.source_id == source.source_id
    assert evidence.evidence_type == EvidenceType.DERIVED_METRIC
    assert evidence.evidence_code == "USGS_TNM_EPQS_RELIEF_SCREEN"
    assert evidence.domain == "buildability"
    assert evidence.method_code == USGS_TNM_METHOD_CODE
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.caveat == USGS_TNM_CAVEAT
    assert evidence.source_ingest_run_id == result.retrieval_run.ingest_run_id
    assert evidence.source_date == "2022-11-03"
    assert evidence.observed_value == {
        "metric_code": "tnm_epqs_sampled_relief_m",
        "value": 4.0,
        "unit": "m",
        "mean_elevation_m": 10.0,
        "calculation_method": "center_and_corner_epqs_point_sample_relief",
    }

    assert len(result.observability_log.events_of_type(ConnectorEventType.run_started)) == 1
    assert len(result.observability_log.events_of_type(ConnectorEventType.evidence_stored)) == 1
    assert len(result.observability_log.events_of_type(ConnectorEventType.run_succeeded)) == 1


def test_success_result_uses_existing_provenance_and_evidence_adapters() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return _payload(10.0)

    result = UsgsTnmElevationConnector(
        source=_source(),
        fetch_json=fetch_json,
    ).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )
    retrieval_port = RecordingRetrievalPort()
    evidence_port = RecordingEvidencePort()

    provenance = ConnectorRetrievalProvenanceAdapter(retrieval_port).record(result)
    ingestion = ConnectorEvidenceIngestionAdapter(evidence_port).ingest(result)

    assert provenance.recorded_run == result.retrieval_run
    assert retrieval_port.recorded_runs == [result.retrieval_run]
    assert ingestion.created_evidence == result.evidence_inputs
    assert evidence_port.created_observations == list(result.evidence_inputs)


def test_success_query_is_idempotent_for_same_source_area_bbox_and_sample_count() -> None:
    source = _source()
    area_id = uuid4()

    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return _payload(10.0)

    connector = UsgsTnmElevationConnector(source=source, fetch_json=fetch_json)
    first = connector.query_bbox(area_id=area_id, bbox=_bbox(), max_sample_points=1)
    second = connector.query_bbox(area_id=area_id, bbox=_bbox(), max_sample_points=1)

    assert first.retrieval_run.ingest_run_id == second.retrieval_run.ingest_run_id
    assert first.evidence_inputs[0].evidence_id == second.evidence_inputs[0].evidence_id


def test_no_data_elevation_emits_source_failure() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return _payload(-1000000.0)

    result = UsgsTnmElevationConnector(
        source=_source(),
        fetch_json=fetch_json,
    ).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.metrics["failure_reason"] == "usgs_tnm_no_elevation"
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.is_source_failure is True
    assert evidence.domain == "buildability"
    assert evidence.observed_value["failure_reason"] == "usgs_tnm_no_elevation"
    assert evidence.observed_value["retryable"] is False


def test_malformed_sample_emits_source_failure_instead_of_raising() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"value": "not-a-number"}

    result = UsgsTnmElevationConnector(
        source=_source(),
        fetch_json=fetch_json,
    ).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.metrics["failure_reason"] == "usgs_tnm_malformed_sample"
    assert result.evidence_inputs[0].observed_value["retryable"] is True


def test_license_blocked_before_fetch() -> None:
    called = False

    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        nonlocal called
        called = True
        return _payload(10.0)

    with pytest.raises(ConnectorLicenseBlockedError):
        UsgsTnmElevationConnector(
            source=_source(license_status="unknown"),
            fetch_json=fetch_json,
        ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert called is False


@pytest.mark.parametrize(
    ("bbox_values", "message"),
    [
        ((-77.0, 38.0, -76.7, 38.1), "longitude span"),
        ((-77.0, 38.0, -76.9, 38.3), "latitude span"),
    ],
)
def test_bbox_rejects_oversized_queries(
    bbox_values: tuple[float, float, float, float],
    message: str,
) -> None:
    with pytest.raises(UsgsTnmConnectorError, match=message):
        UsgsTnmBbox(*bbox_values)


def test_rejects_unbounded_sample_count() -> None:
    with pytest.raises(UsgsTnmConnectorError, match="max_sample_points"):
        UsgsTnmElevationConnector(source=_source()).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
            max_sample_points=USGS_TNM_MAX_SAMPLE_POINTS + 1,
        )


def test_connector_stays_before_claims_reports_and_api() -> None:
    source = inspect.getsource(usgs_tnm_module)

    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "app.api" not in source


def test_fetcher_type_alias_accepts_mapping_payload() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, Any]:
        return _payload(10.0)

    result = UsgsTnmElevationConnector(
        source=_source(),
        fetch_json=fetch_json,
    ).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
        max_sample_points=1,
    )

    assert result.retrieval_run.row_count == 1
