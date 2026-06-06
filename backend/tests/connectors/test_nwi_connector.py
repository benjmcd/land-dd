from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

import app.connectors.nwi as nwi_module
from app.connectors.evidence_ingestion import ConnectorEvidenceIngestionAdapter
from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.nwi import (
    NWI_CAVEAT,
    NWI_CONNECTOR_NAME,
    NWI_MAX_FEATURES,
    NWI_METHOD_CODE,
    NWI_SERVICE_URL,
    NWI_WETLANDS_LAYER_ID,
    NwiBbox,
    NwiConnector,
    NwiConnectorError,
)
from app.connectors.observability import ConnectorEventType
from app.connectors.retrieval_provenance import ConnectorRetrievalProvenanceAdapter
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="National Wetlands Inventory",
        organization="USFWS",
        source_type="Public official",
        domain="Wetlands",
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
        metadata={"source_registry_id": "DS-004"},
    )


def _bbox() -> NwiBbox:
    return NwiBbox(xmin=-77.10, ymin=38.80, xmax=-77.00, ymax=38.90)


def _feature() -> dict[str, object]:
    return {
        "type": "Feature",
        "id": 2808733,
        "properties": {
            "Wetlands.OBJECTID": 2808733,
            "Wetlands.ATTRIBUTE": "L1UBH",
            "Wetlands.WETLAND_TYPE": "Lake",
            "Wetlands.ACRES": 106.82272375751111,
            "Wetlands.GLOBALID": "{3FE208B5-9945-4564-B466-FF415177DE3B}",
            "NWI_Wetland_Codes.SYSTEM_NAME": "Lacustrine",
            "NWI_Wetland_Codes.CLASS_NAME": "Unconsolidated Bottom",
            "NWI_Wetland_Codes.WATER_REGIME_NAME": "Permanently Flooded",
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


def _fixture_payload(name: str) -> dict[str, object]:
    payload = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


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


def test_success_query_builds_bounded_nwi_request_and_wetland_evidence() -> None:
    urls: list[str] = []
    source = _source()

    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        urls.append(url)
        assert timeout_seconds == 30.0
        return {"type": "FeatureCollection", "features": [_feature()]}

    area_id = uuid4()
    result = NwiConnector(source=source, fetch_json=fetch_json).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert urls
    assert f"{NWI_SERVICE_URL}/{NWI_WETLANDS_LAYER_ID}/query" in urls[0]
    assert "f=geojson" in urls[0]
    assert "geometryType=esriGeometryEnvelope" in urls[0]
    assert "spatialRel=esriSpatialRelIntersects" in urls[0]
    assert f"resultRecordCount={NWI_MAX_FEATURES}" in urls[0]

    assert result.retrieval_run.connector_name == NWI_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-004"
    assert result.retrieval_run.metrics["layer_id"] == NWI_WETLANDS_LAYER_ID

    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.source_id == source.source_id
    assert evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence.domain == "wetlands"
    assert evidence.method_code == NWI_METHOD_CODE
    assert evidence.confidence == ConfidenceBand.MEDIUM
    assert evidence.caveat == NWI_CAVEAT
    assert evidence.source_ingest_run_id == result.retrieval_run.ingest_run_id
    assert evidence.source_date == evidence.observed_at.date().isoformat()
    assert evidence.geometry_geojson is not None
    assert evidence.spatial_precision_meters is not None
    assert evidence.observed_value["intersects_mapped_wetlands"] is True
    assert evidence.observed_value["wetland_type"] == "Lake"
    assert evidence.observed_value["mapped_wetland_area_sq_m"] == pytest.approx(
        106.82272375751111 * 4046.8564224
    )

    assert len(result.observability_log.events_of_type(ConnectorEventType.run_started)) == 1
    assert len(result.observability_log.events_of_type(ConnectorEventType.evidence_stored)) == 1
    assert len(result.observability_log.events_of_type(ConnectorEventType.run_succeeded)) == 1


def test_success_query_accepts_file_backed_nwi_fixture_response() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return _fixture_payload("nwi_success.geojson")

    result = NwiConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 1
    assert evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence.domain == "wetlands"
    assert evidence.observed_value["intersects_mapped_wetlands"] is True
    assert evidence.observed_value["wetland_type"] == "Lake"


def test_success_result_uses_existing_provenance_and_evidence_adapters() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": [_feature()]}

    result = NwiConnector(source=_source(), fetch_json=fetch_json).query_bbox(
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

    connector = NwiConnector(source=source, fetch_json=fetch_json)
    first = connector.query_bbox(area_id=area_id, bbox=_bbox())
    second = connector.query_bbox(area_id=area_id, bbox=_bbox())

    assert first.retrieval_run.ingest_run_id == second.retrieval_run.ingest_run_id
    assert first.evidence_inputs[0].evidence_id == second.evidence_inputs[0].evidence_id


def test_empty_feature_response_emits_source_failure_evidence() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": []}

    result = NwiConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.row_count == 0
    assert result.retrieval_run.error_count == 1
    assert result.retrieval_run.metrics["failure_reason"] == "nwi_no_features"

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.is_source_failure is True
    assert evidence.source_ingest_run_id == result.retrieval_run.ingest_run_id
    assert evidence.confidence == ConfidenceBand.UNKNOWN
    assert evidence.geometry_geojson is None
    assert evidence.spatial_precision_meters is None
    assert evidence.observed_value["failure_reason"] == "nwi_no_features"


def test_empty_file_backed_nwi_fixture_response_emits_source_failure_evidence() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return _fixture_payload("nwi_empty.geojson")

    result = NwiConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.metrics["failure_reason"] == "nwi_no_features"
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.observed_value["failure_reason"] == "nwi_no_features"


def test_transfer_limit_response_emits_non_retryable_source_failure() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {
            "type": "FeatureCollection",
            "exceededTransferLimit": True,
            "features": [_feature()],
        }

    result = NwiConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.metrics["failure_reason"] == "nwi_transfer_limit_exceeded"
    assert evidence.observed_value["retryable"] is False


def test_service_error_response_emits_retryable_source_failure() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"error": {"message": "Service unavailable"}}

    result = NwiConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.metrics["failure_reason"] == "nwi_service_error"
    assert evidence.observed_value["error_message"] == "Service unavailable"
    assert evidence.observed_value["retryable"] is True


def test_malformed_feature_emits_source_failure_instead_of_raising() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": [{"properties": {}}]}

    result = NwiConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.metrics["failure_reason"] == "nwi_malformed_feature"
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.observed_value["failure_reason"] == "nwi_malformed_feature"


def test_license_blocked_before_fetch() -> None:
    called = False

    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, object]:
        nonlocal called
        called = True
        return {"features": []}

    with pytest.raises(ConnectorLicenseBlockedError):
        NwiConnector(
            source=_source(license_status="unknown"),
            fetch_json=fetch_json,
        ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert called is False


@pytest.mark.parametrize(
    ("bbox_values", "message"),
    [
        ((-77.0, 38.0, -76.0, 38.4), "longitude span"),
        ((-77.0, 38.0, -76.8, 38.6), "latitude span"),
    ],
)
def test_bbox_rejects_oversized_queries(
    bbox_values: tuple[float, float, float, float],
    message: str,
) -> None:
    with pytest.raises(NwiConnectorError, match=message):
        NwiBbox(*bbox_values)


def test_rejects_unbounded_feature_count() -> None:
    with pytest.raises(NwiConnectorError, match="max_features"):
        NwiConnector(source=_source()).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
            max_features=NWI_MAX_FEATURES + 1,
        )


def test_connector_stays_before_claims_reports_and_api() -> None:
    source = inspect.getsource(nwi_module)

    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "app.api" not in source


def test_fetcher_type_alias_accepts_mapping_payload() -> None:
    def fetch_json(_url: str, _timeout_seconds: float) -> dict[str, Any]:
        return {"features": [_feature()]}

    result = NwiConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
        max_features=1,
    )

    assert result.retrieval_run.row_count == 1
