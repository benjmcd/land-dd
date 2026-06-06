from __future__ import annotations

import inspect
from typing import Any
from uuid import UUID, uuid4

import pytest

import app.connectors.fema_nfhl as fema_nfhl_module
from app.connectors.evidence_ingestion import ConnectorEvidenceIngestionAdapter
from app.connectors.fema_nfhl import (
    FEMA_NFHL_CAVEAT,
    FEMA_NFHL_CONNECTOR_NAME,
    FEMA_NFHL_FLOOD_HAZARD_ZONES_LAYER_ID,
    FEMA_NFHL_MAX_FEATURES,
    FEMA_NFHL_METHOD_CODE,
    FEMA_NFHL_SERVICE_URL,
    FemaNfhlBbox,
    FemaNfhlConnector,
    FemaNfhlConnectorError,
)
from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.observability import ConnectorEventType
from app.connectors.retrieval_provenance import ConnectorRetrievalProvenanceAdapter
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="FEMA NFHL",
        organization="FEMA",
        source_type="Public official",
        domain="Flood",
        geographic_scope="US",
        license_status=license_status,
        commercial_use_status="restricted",
        redistribution_status="restricted",
        attribution_required=True,
        cache_allowed="restricted",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="restricted",
        freshness_class="current-effective",
        last_checked_at="2026-06-05",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-002"},
    )


def _bbox() -> FemaNfhlBbox:
    return FemaNfhlBbox(xmin=-77.10, ymin=38.80, xmax=-77.00, ymax=38.90)


def _feature() -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {
            "OBJECTID": 42,
            "DFIRM_ID": "11001C",
            "FLD_AR_ID": "11001C_FLD_42",
            "FLD_ZONE": "AE",
            "ZONE_SUBTY": "RIVERINE FLOODPLAIN",
            "SFHA_TF": "T",
            "STATIC_BFE": 12.5,
            "DEPTH": None,
            "LEN_UNIT": "Feet",
            "VELOCITY": None,
            "VEL_UNIT": None,
            "SOURCE_CIT": "11001C_STUDY",
            "GFID": "gfid-42",
            "GlobalID": "{global-42}",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-77.05, 38.82],
                    [-77.03, 38.82],
                    [-77.03, 38.84],
                    [-77.05, 38.84],
                    [-77.05, 38.82],
                ]
            ],
        },
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


def test_success_query_builds_bounded_fema_request_and_evidence() -> None:
    urls: list[str] = []
    source = _source()

    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        urls.append(url)
        assert timeout_seconds == 30.0
        return {"type": "FeatureCollection", "features": [_feature()]}

    area_id = uuid4()
    result = FemaNfhlConnector(source=source, fetch_json=fetch_json).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert urls
    assert f"{FEMA_NFHL_SERVICE_URL}/{FEMA_NFHL_FLOOD_HAZARD_ZONES_LAYER_ID}/query" in urls[0]
    assert "f=geojson" in urls[0]
    assert "geometryType=esriGeometryEnvelope" in urls[0]
    assert "spatialRel=esriSpatialRelIntersects" in urls[0]
    assert f"resultRecordCount={FEMA_NFHL_MAX_FEATURES}" in urls[0]

    assert result.retrieval_run.connector_name == FEMA_NFHL_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-002"
    assert result.retrieval_run.metrics["layer_id"] == FEMA_NFHL_FLOOD_HAZARD_ZONES_LAYER_ID

    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.source_id == source.source_id
    assert evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence.domain == "flood"
    assert evidence.method_code == FEMA_NFHL_METHOD_CODE
    assert evidence.confidence == ConfidenceBand.MEDIUM
    assert evidence.caveat == FEMA_NFHL_CAVEAT
    assert evidence.source_ingest_run_id == result.retrieval_run.ingest_run_id
    assert evidence.source_date == evidence.observed_at.date().isoformat()
    assert evidence.geometry_geojson is not None
    assert evidence.spatial_precision_meters is not None
    assert evidence.observed_value == {"flood_zone_code": "AE", "intersects": True}

    assert len(result.observability_log.events_of_type(ConnectorEventType.run_started)) == 1
    assert len(result.observability_log.events_of_type(ConnectorEventType.evidence_stored)) == 1
    assert len(result.observability_log.events_of_type(ConnectorEventType.run_succeeded)) == 1


def test_success_result_uses_existing_provenance_and_evidence_adapters() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": [_feature()]}

    result = FemaNfhlConnector(source=_source(), fetch_json=fetch_json).query_bbox(
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


def test_success_query_is_idempotent_for_same_source_area_and_bbox() -> None:
    source = _source()
    area_id = uuid4()

    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": [_feature()]}

    connector = FemaNfhlConnector(source=source, fetch_json=fetch_json)
    first = connector.query_bbox(area_id=area_id, bbox=_bbox())
    second = connector.query_bbox(area_id=area_id, bbox=_bbox())

    assert first.retrieval_run.ingest_run_id == second.retrieval_run.ingest_run_id
    assert first.evidence_inputs[0].evidence_id == second.evidence_inputs[0].evidence_id


def test_empty_feature_response_emits_source_failure_evidence() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": []}

    result = FemaNfhlConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.row_count == 0
    assert result.retrieval_run.error_count == 1
    assert result.retrieval_run.metrics["failure_reason"] == "fema_nfhl_no_features"

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.is_source_failure is True
    assert evidence.source_ingest_run_id == result.retrieval_run.ingest_run_id
    assert evidence.confidence == ConfidenceBand.UNKNOWN
    assert evidence.geometry_geojson is None
    assert evidence.spatial_precision_meters is None
    assert evidence.observed_value["failure_reason"] == "fema_nfhl_no_features"


def test_transfer_limit_response_emits_non_retryable_source_failure() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {
            "type": "FeatureCollection",
            "exceededTransferLimit": True,
            "features": [_feature()],
        }

    result = FemaNfhlConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.metrics["failure_reason"] == (
        "fema_nfhl_transfer_limit_exceeded"
    )
    assert evidence.observed_value["retryable"] is False


def test_service_error_response_emits_retryable_source_failure() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"error": {"message": "Service unavailable"}}

    result = FemaNfhlConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.metrics["failure_reason"] == "fema_nfhl_service_error"
    assert evidence.observed_value["error_message"] == "Service unavailable"
    assert evidence.observed_value["retryable"] is True


def test_malformed_feature_emits_source_failure_instead_of_raising() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": [{"properties": {}}]}

    result = FemaNfhlConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.metrics["failure_reason"] == "fema_nfhl_malformed_feature"
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.observed_value["failure_reason"] == "fema_nfhl_malformed_feature"


def test_license_blocked_before_fetch() -> None:
    called = False

    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        nonlocal called
        called = True
        return {"features": []}

    with pytest.raises(ConnectorLicenseBlockedError):
        FemaNfhlConnector(
            source=_source(license_status="unknown"),
            fetch_json=fetch_json,
        ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert called is False


@pytest.mark.parametrize(
    ("bbox_values", "message"),
    [
        ((-77.0, 38.0, -76.0, 39.1), "latitude span"),
        ((-77.0, 38.0, -75.9, 39.0), "longitude span"),
    ],
)
def test_bbox_rejects_oversized_queries(
    bbox_values: tuple[float, float, float, float],
    message: str,
) -> None:
    with pytest.raises(FemaNfhlConnectorError, match=message):
        FemaNfhlBbox(*bbox_values)


def test_rejects_unbounded_feature_count() -> None:
    with pytest.raises(FemaNfhlConnectorError, match="max_features"):
        FemaNfhlConnector(source=_source()).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
            max_features=FEMA_NFHL_MAX_FEATURES + 1,
        )


def test_connector_stays_before_claims_reports_and_api() -> None:
    source = inspect.getsource(fema_nfhl_module)

    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "app.api" not in source


def test_fetcher_type_alias_accepts_mapping_payload() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, Any]:
        return {"features": [_feature()]}

    result = FemaNfhlConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
        max_features=1,
    )

    assert result.retrieval_run.row_count == 1
