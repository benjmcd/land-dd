from __future__ import annotations

from urllib.error import HTTPError, URLError
from uuid import uuid4

import pytest

import app.connectors.epa_echo as epa_echo_module
from app.connectors.epa_echo import (
    EPA_ECHO_CONNECTOR_NAME,
    EPA_FRS_REST_URL,
    EpaEchoBbox,
    EpaEchoConnector,
    EpaEchoConnectorError,
    _bbox_center_and_radius_miles,
    _build_query_url,
    _parse_facility_count,
)
from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.observability import ConnectorEventType
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="EPA ECHO",
        organization="U.S. Environmental Protection Agency",
        source_type="Public official",
        domain="Environmental compliance",
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
        last_checked_at="2026-06-11",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-006"},
    )


def _bbox() -> EpaEchoBbox:
    return EpaEchoBbox(xmin=-79.10, ymin=35.80, xmax=-79.00, ymax=35.90)


def _mock_facilities_found(url: str, timeout: float) -> dict[str, object]:
    return {
        "Results": {
            "TotalFacilityCount": "3",
            "FRSFacility": [
                {"RegistryId": "110012345678"},
                {"RegistryId": "110012345679"},
                {"RegistryId": "110012345680"},
            ],
        }
    }


def _mock_no_facilities(url: str, timeout: float) -> dict[str, object]:
    return {
        "Results": {
            "TotalFacilityCount": "0",
            "FRSFacility": [],
        }
    }


def _mock_network_error(url: str, timeout: float) -> dict[str, object]:
    raise URLError("connection refused")


def _mock_http_error(url: str, timeout: float) -> dict[str, object]:
    raise HTTPError(url, 503, "Service Unavailable", {}, None)  # type: ignore[arg-type]


def _mock_timeout_error(url: str, timeout: float) -> dict[str, object]:
    raise TimeoutError("timed out")


def _mock_os_error(url: str, timeout: float) -> dict[str, object]:
    raise OSError("connection reset")


def _mock_missing_results(url: str, timeout: float) -> dict[str, object]:
    return {"SomeOtherKey": "unexpected"}


def _mock_value_error(url: str, timeout: float) -> dict[str, object]:
    raise ValueError("EPA FRS response root must be a JSON object")


# --- BBox validation ---


def test_bbox_rejects_xmin_ge_xmax() -> None:
    with pytest.raises(EpaEchoConnectorError, match="xmin must be less than xmax"):
        EpaEchoBbox(xmin=-79.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_ymin_ge_ymax() -> None:
    with pytest.raises(EpaEchoConnectorError, match="ymin must be less than ymax"):
        EpaEchoBbox(xmin=-79.1, ymin=35.9, xmax=-79.0, ymax=35.8)


def test_bbox_rejects_longitude_out_of_range() -> None:
    with pytest.raises(EpaEchoConnectorError, match="longitude values"):
        EpaEchoBbox(xmin=-181.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_latitude_out_of_range() -> None:
    with pytest.raises(EpaEchoConnectorError, match="latitude values"):
        EpaEchoBbox(xmin=-79.1, ymin=-91.0, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_oversized_longitude_span() -> None:
    with pytest.raises(EpaEchoConnectorError, match="longitude span"):
        EpaEchoBbox(xmin=-79.9, ymin=35.0, xmax=-79.3, ymax=35.4)


def test_bbox_rejects_oversized_latitude_span() -> None:
    with pytest.raises(EpaEchoConnectorError, match="latitude span"):
        EpaEchoBbox(xmin=-79.1, ymin=35.0, xmax=-79.0, ymax=35.6)


def test_bbox_valid_passes() -> None:
    bbox = EpaEchoBbox(xmin=-79.1, ymin=35.8, xmax=-79.0, ymax=35.9)
    assert bbox.xmin == -79.1
    assert bbox.xmax == -79.0


def test_bbox_fingerprint_property() -> None:
    bbox = _bbox()
    fp = bbox.fingerprint
    assert fp == f"{bbox.xmin:.8f},{bbox.ymin:.8f},{bbox.xmax:.8f},{bbox.ymax:.8f}"


def test_bbox_str_property() -> None:
    bbox = _bbox()
    bs = bbox.bbox_str
    assert bs == f"{bbox.xmin:.6f},{bbox.ymin:.6f},{bbox.xmax:.6f},{bbox.ymax:.6f}"


# --- _bbox_center_and_radius_miles ---


def test_bbox_center_calculation() -> None:
    bbox = EpaEchoBbox(xmin=-79.10, ymin=35.80, xmax=-79.00, ymax=35.90)
    lat, lon, radius = _bbox_center_and_radius_miles(bbox)
    assert abs(lat - 35.85) < 1e-6
    assert abs(lon - -79.05) < 1e-6
    assert radius > 0


def test_bbox_radius_minimum_capped_at_0_5() -> None:
    # Very tiny bbox should produce at least 0.5 mile radius
    bbox = EpaEchoBbox(xmin=-79.001, ymin=35.800, xmax=-79.000, ymax=35.801)
    _, _, radius = _bbox_center_and_radius_miles(bbox)
    assert radius >= 0.5


def test_bbox_radius_maximum_capped_at_25() -> None:
    # Large (but within 0.5 degrees) bbox near equator
    bbox = EpaEchoBbox(xmin=-79.5, ymin=35.0, xmax=-79.0, ymax=35.5)
    _, _, radius = _bbox_center_and_radius_miles(bbox)
    assert radius <= 25.0


# --- _parse_facility_count ---


def test_parse_facility_count_from_total_string() -> None:
    results = {"TotalFacilityCount": "5"}
    assert _parse_facility_count(results) == 5


def test_parse_facility_count_from_frs_facility_list() -> None:
    results = {"FRSFacility": [{"id": "1"}, {"id": "2"}]}
    assert _parse_facility_count(results) == 2


def test_parse_facility_count_zero_when_missing_both() -> None:
    results: dict[str, object] = {}
    assert _parse_facility_count(results) == 0


def test_parse_facility_count_zero_total() -> None:
    results = {"TotalFacilityCount": "0"}
    assert _parse_facility_count(results) == 0


# --- Facilities found ---


def test_facilities_found_emits_source_observation_evidence() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_facilities_found
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.connector_name == EPA_ECHO_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 3
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-006"
    assert result.retrieval_run.metrics["regulated_facility_count"] == 3

    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "ENV_HAZ_FACILITY_SCREEN"
    assert evidence.domain == "env_hazard"
    assert evidence.observed_value["has_env_hazard_proximity"] is True
    assert evidence.observed_value["regulated_facility_count"] == 3
    assert evidence.confidence == ConfidenceBand.MEDIUM
    assert evidence.is_source_failure is False


def test_facilities_found_does_not_prove_contamination_in_caveat() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_facilities_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    evidence = result.evidence_inputs[0]
    assert "does not prove subject-property contamination" in evidence.caveat


# --- No facilities ---


def test_no_facilities_emits_no_proximity_evidence() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_no_facilities
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 0
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.observed_value["no_env_hazard_proximity"] is True
    assert evidence.observed_value["regulated_facility_count"] == 0
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.is_source_failure is False


# --- Network errors → source failure ---


def test_network_error_emits_source_failure_evidence() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.error_count == 1
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.is_source_failure is True
    assert evidence.observed_value["retryable"] is True
    assert evidence.observed_value["failure_reason"] == "epa_echo_request_error"


def test_http_error_emits_source_failure() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_http_error
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True


def test_missing_results_key_emits_malformed_response_failure() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_missing_results
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True
    assert evidence.observed_value["failure_reason"] == "epa_echo_malformed_response"


def test_value_error_from_fetch_json_emits_source_failure() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_value_error
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True


# --- Observability log ---


def test_observability_log_has_run_started_and_run_succeeded_on_success() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_facilities_found
    ).query_bbox(area_id=area_id, bbox=_bbox())

    event_types = [event.event_type for event in result.observability_log.events]
    assert ConnectorEventType.run_started in event_types
    assert ConnectorEventType.run_succeeded in event_types


def test_observability_log_has_source_failure_and_run_failed_on_error() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=area_id, bbox=_bbox())

    event_types = [event.event_type for event in result.observability_log.events]
    assert ConnectorEventType.source_failure_stored in event_types
    assert ConnectorEventType.run_failed in event_types


# --- Deterministic UUIDs ---


def test_same_inputs_produce_same_evidence_id() -> None:
    area_id = uuid4()
    bbox = _bbox()
    result1 = EpaEchoConnector(
        source=_source(), fetch_json=_mock_facilities_found
    ).query_bbox(area_id=area_id, bbox=bbox)
    result2 = EpaEchoConnector(
        source=_source(), fetch_json=_mock_facilities_found
    ).query_bbox(area_id=area_id, bbox=bbox)
    assert result1.evidence_inputs[0].evidence_id == result2.evidence_inputs[0].evidence_id


def test_different_area_ids_produce_different_evidence_ids() -> None:
    bbox = _bbox()
    result1 = EpaEchoConnector(
        source=_source(), fetch_json=_mock_facilities_found
    ).query_bbox(area_id=uuid4(), bbox=bbox)
    result2 = EpaEchoConnector(
        source=_source(), fetch_json=_mock_facilities_found
    ).query_bbox(area_id=uuid4(), bbox=bbox)
    assert result1.evidence_inputs[0].evidence_id != result2.evidence_inputs[0].evidence_id


# --- Source failure retrieval_run ---


def test_source_failure_retrieval_run_row_count_is_zero() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=area_id, bbox=_bbox())
    assert result.retrieval_run.row_count == 0


def test_success_retrieval_run_row_count_equals_facility_count() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_facilities_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    assert result.retrieval_run.row_count == 3


# --- Request URL ---


def test_request_url_contains_frs_rest_url() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_facilities_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    assert EPA_FRS_REST_URL in result.request_url


def test_request_url_contains_json_output_param() -> None:
    area_id = uuid4()
    result = EpaEchoConnector(
        source=_source(), fetch_json=_mock_facilities_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    assert "output=JSON" in result.request_url


# --- _build_query_url ---


def test_build_query_url_contains_lat_lon_and_radius() -> None:
    url = _build_query_url(lat=35.85, lon=-79.05, radius_miles=5.0)
    assert "lat83=35.850000" in url
    assert "long83=-79.050000" in url
    assert "search_radius=5.00" in url
    assert EPA_FRS_REST_URL in url


# --- license_guard is called ---


def test_license_blocked_before_fetch() -> None:
    fetch_called = False

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        nonlocal fetch_called
        fetch_called = True
        return _mock_facilities_found(url, timeout)

    with pytest.raises(ConnectorLicenseBlockedError):
        EpaEchoConnector(
            source=_source(license_status="unknown"),
            fetch_json=fetch_json,
        ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert fetch_called is False
