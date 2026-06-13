from __future__ import annotations

import inspect
from urllib.error import URLError
from uuid import uuid4

import pytest

import app.connectors.osm_road_access as osm_module
from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.observability import ConnectorEventType
from app.connectors.osm_road_access import (
    OSM_OVERPASS_URL,
    OSM_ROAD_ACCESS_CONNECTOR_NAME,
    OSM_ROAD_ACCESS_MAX_FEATURES,
    OSM_ROAD_ACCESS_METHOD_CODE,
    OsmRoadAccessBbox,
    OsmRoadAccessConnector,
    OsmRoadAccessConnectorError,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="OpenStreetMap via Overpass API",
        organization="OpenStreetMap Foundation",
        source_type="Community open data",
        domain="Roads",
        geographic_scope="Global",
        license_status=license_status,
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        attribution_required=True,
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        freshness_class="current-live",
        last_checked_at="2026-06-11",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-016"},
    )


def _bbox() -> OsmRoadAccessBbox:
    return OsmRoadAccessBbox(xmin=-79.10, ymin=35.80, xmax=-79.00, ymax=35.90)


def _mock_road_present(url: str, timeout: float) -> dict[str, object]:
    return {
        "elements": [
            {"type": "way", "id": 1, "tags": {"highway": "primary"}},
            {"type": "way", "id": 2, "tags": {"highway": "residential"}},
            {"type": "way", "id": 3, "tags": {"highway": "primary"}},
        ]
    }


def _mock_no_road(url: str, timeout: float) -> dict[str, object]:
    return {"elements": []}


def _mock_network_error(url: str, timeout: float) -> dict[str, object]:
    raise URLError("connection refused")


# --- BBox validation ---


def test_bbox_rejects_xmin_ge_xmax() -> None:
    with pytest.raises(OsmRoadAccessConnectorError, match="xmin must be less than xmax"):
        OsmRoadAccessBbox(xmin=-79.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_ymin_ge_ymax() -> None:
    with pytest.raises(OsmRoadAccessConnectorError, match="ymin must be less than ymax"):
        OsmRoadAccessBbox(xmin=-79.1, ymin=35.9, xmax=-79.0, ymax=35.8)


def test_bbox_rejects_longitude_out_of_range() -> None:
    with pytest.raises(OsmRoadAccessConnectorError, match="longitude values"):
        OsmRoadAccessBbox(xmin=-181.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_latitude_out_of_range() -> None:
    with pytest.raises(OsmRoadAccessConnectorError, match="latitude values"):
        OsmRoadAccessBbox(xmin=-79.1, ymin=-91.0, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_oversized_longitude_span() -> None:
    with pytest.raises(OsmRoadAccessConnectorError, match="longitude span"):
        OsmRoadAccessBbox(xmin=-80.0, ymin=35.0, xmax=-79.0, ymax=35.4)


def test_bbox_rejects_oversized_latitude_span() -> None:
    with pytest.raises(OsmRoadAccessConnectorError, match="latitude span"):
        OsmRoadAccessBbox(xmin=-79.1, ymin=35.0, xmax=-79.0, ymax=35.6)


def test_overpass_bbox_property_is_s_w_n_e_order() -> None:
    bbox = _bbox()
    assert bbox.overpass_bbox == f"{bbox.ymin},{bbox.xmin},{bbox.ymax},{bbox.xmax}"


# --- Road present ---


def test_road_present_emits_spatial_intersection_evidence() -> None:
    area_id = uuid4()
    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=_mock_road_present
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.connector_name == OSM_ROAD_ACCESS_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 3
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-016"
    assert result.retrieval_run.metrics["road_count"] == 3
    assert result.retrieval_run.metrics["lookup_type"] == "live_overpass"

    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence.evidence_code == "ACCESS_ROAD_ADJACENCY_SCREEN"
    assert evidence.domain == "access"
    assert evidence.method_code == OSM_ROAD_ACCESS_METHOD_CODE
    assert evidence.confidence == ConfidenceBand.MEDIUM
    assert evidence.is_source_failure is False
    assert evidence.observed_value["has_public_road_adjacency"] is True
    assert evidence.observed_value["public_road_adjacency"] is True
    assert evidence.observed_value["road_distance_m"] == 0.0
    assert evidence.observed_value["road_count"] == 3
    assert evidence.observed_value["lookup_type"] == "live_overpass"
    assert evidence.observed_value["highway_types"] == ["primary", "residential"]


def test_road_present_request_url_contains_overpass_base() -> None:
    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=_mock_road_present
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert OSM_OVERPASS_URL in result.request_url
    assert "data=" in result.request_url


def test_road_present_caveat_contains_openstreetmap_and_verify() -> None:
    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=_mock_road_present
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    caveat = result.evidence_inputs[0].caveat
    assert caveat is not None
    assert "OpenStreetMap" in caveat
    assert "verify" in caveat.lower()


def test_road_present_retrieval_run_has_road_count_in_metrics() -> None:
    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=_mock_road_present
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert "road_count" in result.retrieval_run.metrics
    assert result.retrieval_run.metrics["road_count"] == 3


# --- No road found ---


def test_no_road_emits_low_confidence_spatial_intersection_evidence() -> None:
    area_id = uuid4()
    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=_mock_no_road
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 0

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ACCESS_ROAD_ADJACENCY_SCREEN"
    assert evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.is_source_failure is False
    assert evidence.observed_value["has_public_road_adjacency"] is False
    assert evidence.observed_value["public_road_adjacency"] is False
    assert evidence.observed_value["no_public_road_adjacency"] is True
    assert "road_distance_m" not in evidence.observed_value
    assert evidence.observed_value["road_count"] == 0
    assert evidence.observed_value["highway_types"] == []


# --- Network error ---


def test_network_error_returns_source_failure_evidence() -> None:
    area_id = uuid4()
    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.row_count == 0
    assert result.retrieval_run.error_count == 1

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ACCESS_SOURCE_UNAVAILABLE"
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.is_source_failure is True
    assert evidence.area_id == area_id
    assert "connection refused" in str(evidence.observed_value["error_message"])


def test_network_error_source_failure_status_is_failed() -> None:
    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True
    assert evidence.confidence == ConfidenceBand.UNKNOWN


def test_overpass_remark_error_returns_source_failure() -> None:
    def fetch_remark(url: str, timeout: float) -> dict[str, object]:
        return {
            "remark": "Query run time limit exceeded",
            "elements": [],
        }

    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=fetch_remark
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True
    assert evidence.evidence_code == "ACCESS_SOURCE_UNAVAILABLE"


def test_empty_elements_emits_no_road_adjacency_evidence() -> None:
    def fetch_empty(url: str, timeout: float) -> dict[str, object]:
        return {"elements": []}

    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=fetch_empty
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 0
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is False
    assert evidence.observed_value["has_public_road_adjacency"] is False
    assert evidence.observed_value["highway_types"] == []


def test_missing_elements_key_returns_source_failure() -> None:
    def fetch_no_elements(url: str, timeout: float) -> dict[str, object]:
        return {"version": 0.6}

    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=fetch_no_elements
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].is_source_failure is True


# --- Deterministic IDs ---


def test_same_inputs_produce_deterministic_evidence_id() -> None:
    source = _source()
    area_id = uuid4()
    bbox = _bbox()

    connector = OsmRoadAccessConnector(source=source, fetch_json=_mock_road_present)
    first = connector.query_bbox(area_id=area_id, bbox=bbox)
    second = connector.query_bbox(area_id=area_id, bbox=bbox)

    assert first.retrieval_run.ingest_run_id == second.retrieval_run.ingest_run_id
    assert first.evidence_inputs[0].evidence_id == second.evidence_inputs[0].evidence_id


def test_different_area_id_produces_different_evidence_id() -> None:
    source = _source()
    bbox = _bbox()

    r1 = OsmRoadAccessConnector(source=source, fetch_json=_mock_road_present).query_bbox(
        area_id=uuid4(), bbox=bbox
    )
    r2 = OsmRoadAccessConnector(source=source, fetch_json=_mock_road_present).query_bbox(
        area_id=uuid4(), bbox=bbox
    )

    assert r1.evidence_inputs[0].evidence_id != r2.evidence_inputs[0].evidence_id


# --- Observability ---


def test_success_path_records_run_started_evidence_stored_run_succeeded() -> None:
    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=_mock_road_present
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    log = result.observability_log
    assert len(log.events_of_type(ConnectorEventType.run_started)) == 1
    assert len(log.events_of_type(ConnectorEventType.evidence_stored)) == 1
    assert len(log.events_of_type(ConnectorEventType.run_succeeded)) == 1


def test_failure_path_records_source_failure_stored_and_run_failed() -> None:
    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    log = result.observability_log
    assert len(log.events_of_type(ConnectorEventType.source_failure_stored)) == 1
    assert len(log.events_of_type(ConnectorEventType.run_failed)) == 1


# --- License guard ---


def test_license_blocked_before_fetch() -> None:
    called = False

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        nonlocal called
        called = True
        return _mock_road_present(url, timeout)

    with pytest.raises(ConnectorLicenseBlockedError):
        OsmRoadAccessConnector(
            source=_source(license_status="unknown"),
            fetch_json=fetch_json,
        ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert called is False


# --- Source date is dynamic ---


def test_source_date_is_todays_date_for_success() -> None:
    from datetime import UTC, datetime

    result = OsmRoadAccessConnector(
        source=_source(), fetch_json=_mock_road_present
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    today = datetime.now(UTC).date().isoformat()
    assert result.evidence_inputs[0].source_date == today


# --- Module boundary ---


def test_connector_stays_before_claims_reports_and_api() -> None:
    source = inspect.getsource(osm_module)

    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "app.api" not in source


# --- Max features default ---


def test_default_max_features_constant_is_correct() -> None:
    assert OSM_ROAD_ACCESS_MAX_FEATURES == 500
