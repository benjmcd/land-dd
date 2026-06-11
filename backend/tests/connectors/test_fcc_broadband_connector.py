from __future__ import annotations

from urllib.error import HTTPError, URLError
from uuid import uuid4

import pytest

from app.connectors.fcc_broadband import (
    FCC_BROADBAND_API_URL,
    FCC_BROADBAND_CAVEAT,
    FCC_BROADBAND_CONNECTOR_NAME,
    FccBroadbandBbox,
    FccBroadbandConnector,
    FccBroadbandConnectorError,
    _bbox_center,
    _build_request_url,
)
from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.observability import ConnectorEventType
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="FCC Broadband Map",
        organization="FCC",
        source_type="Public official",
        domain="Broadband",
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
        last_checked_at="2026-06-11",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-021"},
    )


def _bbox() -> FccBroadbandBbox:
    return FccBroadbandBbox(xmin=-79.10, ymin=35.80, xmax=-79.00, ymax=35.90)


def _mock_providers_found(url: str, timeout: float) -> dict[str, object]:
    return {"availability": [
        {"brand_name": "AT&T Fiber", "technology": 50,
         "max_download_speed": 1000, "max_upload_speed": 500},
        {"brand_name": "Charter/Spectrum", "technology": 40,
         "max_download_speed": 300, "max_upload_speed": 30},
    ]}


def _mock_satellite_only(url: str, timeout: float) -> dict[str, object]:
    return {"availability": [
        {"brand_name": "Starlink", "technology": 60,
         "max_download_speed": 100, "max_upload_speed": 20},
    ]}


def _mock_empty_availability(url: str, timeout: float) -> dict[str, object]:
    return {"availability": []}


def _mock_network_error(url: str, timeout: float) -> dict[str, object]:
    raise URLError("connection refused")


def _mock_http_error(url: str, timeout: float) -> dict[str, object]:
    raise HTTPError(url, 503, "Service Unavailable", {}, None)  # type: ignore[arg-type]


def _mock_missing_availability(url: str, timeout: float) -> dict[str, object]:
    return {"data": "unexpected"}


# --- BBox validation ---


def test_bbox_rejects_xmin_ge_xmax() -> None:
    with pytest.raises(FccBroadbandConnectorError, match="xmin must be less than xmax"):
        FccBroadbandBbox(xmin=-79.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_ymin_ge_ymax() -> None:
    with pytest.raises(FccBroadbandConnectorError, match="ymin must be less than ymax"):
        FccBroadbandBbox(xmin=-79.1, ymin=35.9, xmax=-79.0, ymax=35.8)


def test_bbox_rejects_longitude_out_of_range() -> None:
    with pytest.raises(FccBroadbandConnectorError, match="longitude values"):
        FccBroadbandBbox(xmin=-181.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_latitude_out_of_range() -> None:
    with pytest.raises(FccBroadbandConnectorError, match="latitude values"):
        FccBroadbandBbox(xmin=-79.1, ymin=-91.0, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_oversized_longitude_span() -> None:
    with pytest.raises(FccBroadbandConnectorError, match="longitude span"):
        FccBroadbandBbox(xmin=-79.9, ymin=35.0, xmax=-79.3, ymax=35.4)


def test_bbox_rejects_oversized_latitude_span() -> None:
    with pytest.raises(FccBroadbandConnectorError, match="latitude span"):
        FccBroadbandBbox(xmin=-79.1, ymin=35.0, xmax=-79.0, ymax=35.6)


def test_bbox_valid_passes() -> None:
    bbox = FccBroadbandBbox(xmin=-79.1, ymin=35.8, xmax=-79.0, ymax=35.9)
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


# --- _bbox_center ---


def test_bbox_center_calculation() -> None:
    bbox = FccBroadbandBbox(xmin=-79.10, ymin=35.80, xmax=-79.00, ymax=35.90)
    lat, lon = _bbox_center(bbox)
    assert abs(lat - 35.85) < 1e-6
    assert abs(lon - -79.05) < 1e-6


# --- Provider found ---


def test_providers_found_emits_source_observation_with_has_any_broadband_true() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.connector_name == FCC_BROADBAND_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 2
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-021"

    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "FCC_BROADBAND_AVAILABILITY_SCREEN"
    assert evidence.domain == "broadband"
    assert evidence.observed_value["has_any_broadband"] is True
    assert evidence.observed_value["provider_count"] == 2
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.is_source_failure is False


def test_providers_found_correct_technology_types() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    evidence = result.evidence_inputs[0]
    tech_types = evidence.observed_value["technology_types"]
    assert isinstance(tech_types, list)
    assert "fiber" in tech_types
    assert "cable" in tech_types


def test_providers_found_correct_max_download_mbps() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["max_download_mbps"] == 1000


def test_high_speed_broadband_detected_fiber() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["has_high_speed_broadband"] is True


def test_high_speed_broadband_detected_by_speed_threshold() -> None:
    # technology=60 (satellite) is not in _HIGH_SPEED_TECHS, but speed >= 100 triggers high-speed
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_satellite_only
    ).query_bbox(area_id=area_id, bbox=_bbox())
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["has_high_speed_broadband"] is True


# --- Empty availability list ---


def test_empty_availability_emits_source_observation_with_has_any_broadband_false() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_empty_availability
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 0
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.observed_value["has_any_broadband"] is False
    assert evidence.observed_value["provider_count"] == 0
    assert evidence.is_source_failure is False


# --- Network error ---


def test_network_error_emits_source_failure() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.error_count == 1
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.is_source_failure is True
    assert evidence.observed_value["failure_reason"] == "fcc_broadband_request_error"


def test_http_error_emits_source_failure() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_http_error
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True


def test_missing_availability_key_emits_malformed_response_failure() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_missing_availability
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True
    assert evidence.observed_value["failure_reason"] == "fcc_broadband_malformed_response"


# --- Observability log ---


def test_observability_log_has_run_started_and_run_succeeded_on_success() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=_bbox())

    event_types = [event.event_type for event in result.observability_log.events]
    assert ConnectorEventType.run_started in event_types
    assert ConnectorEventType.run_succeeded in event_types


def test_observability_log_has_source_failure_and_run_failed_on_error() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=area_id, bbox=_bbox())

    event_types = [event.event_type for event in result.observability_log.events]
    assert ConnectorEventType.source_failure_stored in event_types
    assert ConnectorEventType.run_failed in event_types


# --- Deterministic UUIDs ---


def test_same_inputs_produce_same_evidence_id() -> None:
    area_id = uuid4()
    bbox = _bbox()
    result1 = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=bbox)
    result2 = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=bbox)
    assert result1.evidence_inputs[0].evidence_id == result2.evidence_inputs[0].evidence_id


def test_different_area_ids_produce_different_evidence_ids() -> None:
    bbox = _bbox()
    result1 = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=uuid4(), bbox=bbox)
    result2 = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=uuid4(), bbox=bbox)
    assert result1.evidence_inputs[0].evidence_id != result2.evidence_inputs[0].evidence_id


# --- Caveat ---


def test_caveat_includes_does_not_guarantee_service_availability() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    evidence = result.evidence_inputs[0]
    assert evidence.caveat is not None
    assert "does not guarantee service availability" in evidence.caveat


def test_fcc_broadband_caveat_constant_includes_expected_text() -> None:
    assert "does not guarantee service availability" in FCC_BROADBAND_CAVEAT


# --- License guard ---


def test_license_blocked_before_fetch() -> None:
    fetch_called = False

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        nonlocal fetch_called
        fetch_called = True
        return _mock_providers_found(url, timeout)

    with pytest.raises(ConnectorLicenseBlockedError):
        FccBroadbandConnector(
            source=_source(license_status="unknown"),
            fetch_json=fetch_json,
        ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert fetch_called is False


# --- Source failure retrieval_run ---


def test_source_failure_retrieval_run_row_count_is_zero() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_network_error
    ).query_bbox(area_id=area_id, bbox=_bbox())
    assert result.retrieval_run.row_count == 0


def test_success_retrieval_run_row_count_equals_provider_count() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    assert result.retrieval_run.row_count == 2


# --- Request URL ---


def test_request_url_contains_fcc_broadband_api_url() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    assert FCC_BROADBAND_API_URL in result.request_url


def test_request_url_contains_lat_lon_params() -> None:
    area_id = uuid4()
    result = FccBroadbandConnector(
        source=_source(), fetch_json=_mock_providers_found
    ).query_bbox(area_id=area_id, bbox=_bbox())
    assert "latitude=" in result.request_url
    assert "longitude=" in result.request_url


def test_build_request_url_contains_lat_lon() -> None:
    url = _build_request_url(35.85, -79.05)
    assert "latitude=35.850000" in url
    assert "longitude=-79.050000" in url
    assert FCC_BROADBAND_API_URL in url
