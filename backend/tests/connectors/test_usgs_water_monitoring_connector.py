from __future__ import annotations

import inspect
from urllib.error import HTTPError, URLError
from uuid import uuid4

import pytest

import app.connectors.usgs_water_monitoring as usgs_water_module
from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.observability import ConnectorEventType
from app.connectors.usgs_water_monitoring import (
    USGS_WATER_CONNECTOR_NAME,
    USGS_WATER_METHOD_CODE,
    USGS_WATER_SITE_SERVICE_URL,
    UsgsWaterBbox,
    UsgsWaterConnectorError,
    UsgsWaterMonitoringConnector,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="USGS Water Data APIs",
        organization="U.S. Geological Survey",
        source_type="Public official",
        domain="Water monitoring",
        geographic_scope="US",
        license_status=license_status,
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        attribution_required=True,
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        freshness_class="current-live",
        last_checked_at="2026-06-10",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-005"},
    )


def _bbox() -> UsgsWaterBbox:
    return UsgsWaterBbox(xmin=-79.10, ymin=35.80, xmax=-79.00, ymax=35.90)


def _mock_stations_found(url: str, timeout: float) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"site_no": "02082770"}, "geometry": None},
            {"type": "Feature", "properties": {"site_no": "02082950"}, "geometry": None},
        ],
    }


def _mock_no_stations(url: str, timeout: float) -> dict[str, object]:
    return {"type": "FeatureCollection", "features": []}


def _mock_network_error(url: str, timeout: float) -> dict[str, object]:
    raise URLError("connection refused")


def _mock_http_error(url: str, timeout: float) -> dict[str, object]:
    raise HTTPError(url, 503, "Service Unavailable", {}, None)  # type: ignore[arg-type]


def _mock_timeout_error(url: str, timeout: float) -> dict[str, object]:
    raise TimeoutError("timed out")


def _mock_os_error(url: str, timeout: float) -> dict[str, object]:
    raise OSError("connection reset")


def _mock_non_dict(url: str, timeout: float) -> dict[str, object]:
    raise ValueError("USGS water service response root must be a JSON object")


# --- BBox validation ---


def test_bbox_rejects_xmin_ge_xmax() -> None:
    with pytest.raises(UsgsWaterConnectorError, match="xmin must be less than xmax"):
        UsgsWaterBbox(xmin=-79.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_ymin_ge_ymax() -> None:
    with pytest.raises(UsgsWaterConnectorError, match="ymin must be less than ymax"):
        UsgsWaterBbox(xmin=-79.1, ymin=35.9, xmax=-79.0, ymax=35.8)


def test_bbox_rejects_longitude_out_of_range() -> None:
    with pytest.raises(UsgsWaterConnectorError, match="longitude values"):
        UsgsWaterBbox(xmin=-181.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_latitude_out_of_range() -> None:
    with pytest.raises(UsgsWaterConnectorError, match="latitude values"):
        UsgsWaterBbox(xmin=-79.1, ymin=-91.0, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_oversized_longitude_span() -> None:
    with pytest.raises(UsgsWaterConnectorError, match="longitude span"):
        UsgsWaterBbox(xmin=-80.5, ymin=35.0, xmax=-79.4, ymax=35.4)


def test_bbox_rejects_oversized_latitude_span() -> None:
    with pytest.raises(UsgsWaterConnectorError, match="latitude span"):
        UsgsWaterBbox(xmin=-79.1, ymin=35.0, xmax=-79.0, ymax=36.1)


def test_bbox_valid_passes() -> None:
    bbox = UsgsWaterBbox(xmin=-79.1, ymin=35.8, xmax=-79.0, ymax=35.9)
    assert bbox.xmin == -79.1
    assert bbox.xmax == -79.0


def test_usgs_bbox_property_is_w_s_e_n_order() -> None:
    bbox = _bbox()
    assert bbox.usgs_bbox == f"{bbox.xmin},{bbox.ymin},{bbox.xmax},{bbox.ymax}"


# --- Stations found ---


def test_stations_found_emits_source_observation_evidence() -> None:
    area_id = uuid4()
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_stations_found
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.connector_name == USGS_WATER_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 2
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-005"
    assert result.retrieval_run.metrics["station_count"] == 2
    assert result.retrieval_run.metrics["lookup_type"] == "live_usgs"

    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "WATER_MONITORING_SCREEN"
    assert evidence.domain == "water"
    assert evidence.method_code == USGS_WATER_METHOD_CODE
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.is_source_failure is False
    assert evidence.observed_value["plausible_water_context"] is True
    assert evidence.observed_value["monitoring_station_count"] == 2
    assert evidence.observed_value["water_context_status"] == "monitoring_stations_found"


def test_stations_found_station_count_in_metrics() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_stations_found
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.metrics["station_count"] == 2


def test_stations_found_request_url_contains_site_service_base() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_stations_found
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert USGS_WATER_SITE_SERVICE_URL in result.request_url
    assert "bBox=" in result.request_url


def test_stations_found_caveat_contains_usgs_and_screening() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_stations_found
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    caveat = result.evidence_inputs[0].caveat
    assert caveat is not None
    assert "U.S. Geological Survey" in caveat
    assert "screening" in caveat.lower()


def test_stations_found_sets_plausible_water_context_true() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_stations_found
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.evidence_inputs[0].observed_value["plausible_water_context"] is True


# --- No stations found ---


def test_no_stations_emits_low_confidence_evidence() -> None:
    area_id = uuid4()
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_no_stations
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 0

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "WATER_MONITORING_SCREEN"
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.is_source_failure is False
    assert evidence.observed_value["no_plausible_water_context"] is True
    assert evidence.observed_value["monitoring_station_count"] == 0
    assert evidence.observed_value["water_context_status"] == "no_monitoring_stations_in_bbox"


def test_no_stations_sets_no_plausible_water_context_true() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_no_stations
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.evidence_inputs[0].observed_value["no_plausible_water_context"] is True


# --- Network errors ---


def test_urlerror_returns_source_failure() -> None:
    area_id = uuid4()
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.row_count == 0
    assert result.retrieval_run.error_count == 1

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "WATER_SOURCE_UNAVAILABLE"
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.is_source_failure is True
    assert evidence.area_id == area_id
    assert "connection refused" in str(evidence.observed_value["error_message"])


def test_httperror_returns_source_failure() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_http_error
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True
    assert evidence.evidence_code == "WATER_SOURCE_UNAVAILABLE"


def test_timeout_error_returns_source_failure() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_timeout_error
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].is_source_failure is True


def test_os_error_returns_source_failure() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_os_error
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].is_source_failure is True


def test_source_failure_has_unknown_confidence() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.evidence_inputs[0].confidence == ConfidenceBand.UNKNOWN


def test_source_failure_status_is_failed() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED


# --- Malformed responses ---


def test_missing_features_key_returns_source_failure() -> None:
    def fetch_no_features(url: str, timeout: float) -> dict[str, object]:
        return {"type": "FeatureCollection"}  # no "features" key

    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=fetch_no_features
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True
    assert evidence.observed_value["failure_reason"] == "usgs_water_malformed_response"


def test_non_list_features_returns_source_failure() -> None:
    def fetch_bad_features(url: str, timeout: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": "not-a-list"}

    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=fetch_bad_features
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True
    assert evidence.observed_value["failure_reason"] == "usgs_water_malformed_response"


def test_value_error_returns_source_failure() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_non_dict
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].is_source_failure is True


# --- Deterministic IDs ---


def test_same_inputs_produce_deterministic_evidence_id() -> None:
    source = _source()
    area_id = uuid4()
    bbox = _bbox()

    connector = UsgsWaterMonitoringConnector(source=source, fetch_json=_mock_stations_found)
    first = connector.query_bbox(area_id=area_id, bbox=bbox)
    second = connector.query_bbox(area_id=area_id, bbox=bbox)

    assert first.retrieval_run.ingest_run_id == second.retrieval_run.ingest_run_id
    assert first.evidence_inputs[0].evidence_id == second.evidence_inputs[0].evidence_id


def test_same_inputs_produce_deterministic_source_failure_id() -> None:
    source = _source()
    area_id = uuid4()
    bbox = _bbox()

    connector = UsgsWaterMonitoringConnector(source=source, fetch_json=_mock_network_error)
    first = connector.query_bbox(area_id=area_id, bbox=bbox)
    second = connector.query_bbox(area_id=area_id, bbox=bbox)

    assert first.evidence_inputs[0].evidence_id == second.evidence_inputs[0].evidence_id


def test_different_area_id_produces_different_evidence_id() -> None:
    source = _source()
    bbox = _bbox()

    r1 = UsgsWaterMonitoringConnector(source=source, fetch_json=_mock_stations_found).query_bbox(
        area_id=uuid4(), bbox=bbox
    )
    r2 = UsgsWaterMonitoringConnector(source=source, fetch_json=_mock_stations_found).query_bbox(
        area_id=uuid4(), bbox=bbox
    )

    assert r1.evidence_inputs[0].evidence_id != r2.evidence_inputs[0].evidence_id


# --- All success evidence has caveat ---


def test_success_evidence_has_caveat_set() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_stations_found
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    evidence = result.evidence_inputs[0]
    assert evidence.caveat is not None
    assert len(evidence.caveat) > 0


def test_no_stations_evidence_has_caveat_set() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_no_stations
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    evidence = result.evidence_inputs[0]
    assert evidence.caveat is not None
    assert len(evidence.caveat) > 0


# --- Observability ---


def test_success_path_records_run_started_evidence_stored_run_succeeded() -> None:
    result = UsgsWaterMonitoringConnector(
        source=_source(), fetch_json=_mock_stations_found
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    log = result.observability_log
    assert len(log.events_of_type(ConnectorEventType.run_started)) == 1
    assert len(log.events_of_type(ConnectorEventType.evidence_stored)) == 1
    assert len(log.events_of_type(ConnectorEventType.run_succeeded)) == 1


def test_failure_path_records_source_failure_stored_and_run_failed() -> None:
    result = UsgsWaterMonitoringConnector(
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
        return _mock_stations_found(url, timeout)

    with pytest.raises(ConnectorLicenseBlockedError):
        UsgsWaterMonitoringConnector(
            source=_source(license_status="unknown"),
            fetch_json=fetch_json,
        ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert called is False


# --- Module boundary ---


def test_connector_stays_before_claims_reports_and_api() -> None:
    source = inspect.getsource(usgs_water_module)

    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "app.api" not in source
