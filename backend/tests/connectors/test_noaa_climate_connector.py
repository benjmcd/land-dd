from __future__ import annotations

from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from uuid import uuid4

import pytest

from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.noaa_climate import (
    NOAA_CLIMATE_CAVEAT,
    NOAA_CLIMATE_CONNECTOR_NAME,
    NoaaClimateBbox,
    NoaaClimateConnector,
    NoaaClimateConnectorError,
)
from app.connectors.observability import ConnectorEventType
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="NOAA climate/weather",
        organization="NOAA",
        source_type="Public official",
        domain="Climate/weather",
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
        metadata={"source_registry_id": "DS-020"},
    )


def _bbox() -> NoaaClimateBbox:
    return NoaaClimateBbox(xmin=-79.10, ymin=35.80, xmax=-79.00, ymax=35.90)


def _nws_points_response(
    *,
    cwa: str = "RAH",
    forecast_zone_url: str = "https://api.weather.gov/zones/forecast/NCZ087",
    timezone: str = "America/New_York",
    radar_station: str = "KRAX",
    nearest_city: str = "Pittsboro",
    nearest_state: str = "NC",
) -> Mapping[str, object]:
    return {
        "type": "Feature",
        "properties": {
            "cwa": cwa,
            "forecastZone": forecast_zone_url,
            "timeZone": timezone,
            "radarStation": radar_station,
            "relativeLocation": {
                "type": "Feature",
                "properties": {
                    "city": nearest_city,
                    "state": nearest_state,
                },
            },
        },
    }


def _nws_zone_response(*, zone_name: str = "Southern Chatham County") -> Mapping[str, object]:
    return {
        "type": "Feature",
        "properties": {
            "name": zone_name,
        },
    }


# Two-call fetch mock: first call = points endpoint, second = zone endpoint.
class _TwoCallMock:
    def __init__(
        self,
        points_response: Mapping[str, object],
        zone_response: Mapping[str, object],
    ) -> None:
        self._responses = [points_response, zone_response]
        self._idx = 0

    def __call__(self, url: str, timeout: float) -> Mapping[str, object]:
        resp = self._responses[self._idx]
        self._idx += 1
        return resp


def _mock_nws_full(url: str, timeout: float) -> Mapping[str, object]:
    return _TwoCallMock(
        _nws_points_response(),
        _nws_zone_response(),
    )(url, timeout)


def _mock_network_error(url: str, timeout: float) -> Mapping[str, object]:
    raise URLError("connection refused")


def _mock_http_error(url: str, timeout: float) -> Mapping[str, object]:
    raise HTTPError(url, 503, "Service Unavailable", {}, None)  # type: ignore[arg-type]


def _mock_missing_properties(url: str, timeout: float) -> Mapping[str, object]:
    return {"type": "Feature"}  # no "properties"


# --- BBox validation ---


def test_bbox_rejects_xmin_ge_xmax() -> None:
    with pytest.raises(NoaaClimateConnectorError, match="xmin must be less than xmax"):
        NoaaClimateBbox(xmin=-79.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_ymin_ge_ymax() -> None:
    with pytest.raises(NoaaClimateConnectorError, match="ymin must be less than ymax"):
        NoaaClimateBbox(xmin=-79.1, ymin=35.9, xmax=-79.0, ymax=35.8)


def test_bbox_rejects_longitude_out_of_range() -> None:
    with pytest.raises(NoaaClimateConnectorError, match="longitude values"):
        NoaaClimateBbox(xmin=-181.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_latitude_out_of_range() -> None:
    with pytest.raises(NoaaClimateConnectorError, match="latitude values"):
        NoaaClimateBbox(xmin=-79.1, ymin=-91.0, xmax=-79.0, ymax=35.9)


def test_bbox_rejects_oversized_longitude_span() -> None:
    with pytest.raises(NoaaClimateConnectorError, match="longitude span"):
        NoaaClimateBbox(xmin=-80.5, ymin=35.0, xmax=-79.0, ymax=35.4)


def test_bbox_rejects_oversized_latitude_span() -> None:
    with pytest.raises(NoaaClimateConnectorError, match="latitude span"):
        NoaaClimateBbox(xmin=-79.1, ymin=34.0, xmax=-79.0, ymax=35.2)


def test_bbox_valid_passes() -> None:
    bbox = NoaaClimateBbox(xmin=-79.1, ymin=35.8, xmax=-79.0, ymax=35.9)
    assert bbox.xmin == -79.1
    assert bbox.xmax == -79.0


def test_bbox_fingerprint_property() -> None:
    bbox = _bbox()
    fp = bbox.fingerprint
    assert fp == f"{bbox.xmin:.8f},{bbox.ymin:.8f},{bbox.xmax:.8f},{bbox.ymax:.8f}"


def test_bbox_centroid_property() -> None:
    bbox = NoaaClimateBbox(xmin=-79.10, ymin=35.80, xmax=-79.00, ymax=35.90)
    lat, lon = bbox.centroid
    assert abs(lat - 35.85) < 1e-6
    assert abs(lon - -79.05) < 1e-6


# --- Successful query ---


def test_successful_query_emits_source_observation() -> None:
    area_id = uuid4()
    two_call = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=_bbox()
    )

    assert result.retrieval_run.connector_name == NOAA_CLIMATE_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-020"

    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "NWS_CLIMATE_ZONE"
    assert evidence.domain == "climate"
    assert evidence.is_source_failure is False


def test_successful_query_has_nws_coverage_true() -> None:
    area_id = uuid4()
    two_call = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["has_nws_coverage"] is True


def test_successful_query_office_code_and_zone() -> None:
    area_id = uuid4()
    two_call = _TwoCallMock(_nws_points_response(cwa="RAH"), _nws_zone_response())
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["nws_office_code"] == "RAH"
    assert evidence.observed_value["nws_forecast_zone"] == "NCZ087"


def test_successful_query_zone_name_resolved() -> None:
    area_id = uuid4()
    two_call = _TwoCallMock(
        _nws_points_response(), _nws_zone_response(zone_name="Southern Chatham County")
    )
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["nws_forecast_zone_name"] == "Southern Chatham County"


def test_successful_query_timezone_and_radar() -> None:
    area_id = uuid4()
    two_call = _TwoCallMock(
        _nws_points_response(timezone="America/New_York", radar_station="KRAX"),
        _nws_zone_response(),
    )
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["timezone"] == "America/New_York"
    assert evidence.observed_value["nws_radar_station"] == "KRAX"


def test_successful_query_relative_location_parsed() -> None:
    area_id = uuid4()
    two_call = _TwoCallMock(
        _nws_points_response(nearest_city="Pittsboro", nearest_state="NC"),
        _nws_zone_response(),
    )
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["nws_nearest_city"] == "Pittsboro"
    assert evidence.observed_value["nws_nearest_state"] == "NC"


def test_successful_query_confidence_high() -> None:
    area_id = uuid4()
    two_call = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    evidence = result.evidence_inputs[0]
    assert evidence.confidence == ConfidenceBand.HIGH


# --- Zone name fetch failure → graceful fallback ---


def test_zone_name_fetch_failure_does_not_raise() -> None:
    """Zone endpoint failure is silently swallowed; zone_name falls back to empty string."""
    call_count = 0

    def fetch_fail_on_second(url: str, timeout: float) -> Mapping[str, object]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _nws_points_response()
        raise URLError("zone fetch failed")

    area_id = uuid4()
    result = NoaaClimateConnector(source=_source(), fetch_json=fetch_fail_on_second).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is False
    assert evidence.observed_value["nws_forecast_zone_name"] == ""


# --- Network / HTTP errors → source failure ---


def test_network_error_emits_source_failure() -> None:
    area_id = uuid4()
    result = NoaaClimateConnector(source=_source(), fetch_json=_mock_network_error).query_bbox(
        area_id=area_id, bbox=_bbox()
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.error_count == 1
    assert result.retrieval_run.row_count == 0
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.is_source_failure is True
    assert evidence.observed_value["failure_reason"] == "noaa_nws_request_error"


def test_http_error_emits_source_failure() -> None:
    area_id = uuid4()
    result = NoaaClimateConnector(source=_source(), fetch_json=_mock_http_error).query_bbox(
        area_id=area_id, bbox=_bbox()
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True


def test_missing_properties_emits_source_failure() -> None:
    area_id = uuid4()
    result = NoaaClimateConnector(
        source=_source(), fetch_json=_mock_missing_properties
    ).query_bbox(area_id=area_id, bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.is_source_failure is True
    assert evidence.observed_value["failure_reason"] == "noaa_nws_request_error"


def test_source_failure_evidence_code_is_noaa_nws_source_failure() -> None:
    area_id = uuid4()
    result = NoaaClimateConnector(source=_source(), fetch_json=_mock_network_error).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "NOAA_NWS_SOURCE_FAILURE"


def test_source_failure_confidence_is_unknown() -> None:
    area_id = uuid4()
    result = NoaaClimateConnector(source=_source(), fetch_json=_mock_network_error).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    evidence = result.evidence_inputs[0]
    assert evidence.confidence == ConfidenceBand.UNKNOWN


# --- Observability log ---


def test_observability_log_run_started_and_succeeded_on_success() -> None:
    area_id = uuid4()
    two_call = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    event_types = [e.event_type for e in result.observability_log.events]
    assert ConnectorEventType.run_started in event_types
    assert ConnectorEventType.run_succeeded in event_types


def test_observability_log_source_failure_and_run_failed_on_error() -> None:
    area_id = uuid4()
    result = NoaaClimateConnector(source=_source(), fetch_json=_mock_network_error).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    event_types = [e.event_type for e in result.observability_log.events]
    assert ConnectorEventType.source_failure_stored in event_types
    assert ConnectorEventType.run_failed in event_types


# --- Deterministic UUIDs ---


def test_same_inputs_produce_same_evidence_id() -> None:
    area_id = uuid4()
    bbox = _bbox()
    two_call_1 = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    two_call_2 = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    result1 = NoaaClimateConnector(source=_source(), fetch_json=two_call_1).query_bbox(
        area_id=area_id, bbox=bbox
    )
    result2 = NoaaClimateConnector(source=_source(), fetch_json=two_call_2).query_bbox(
        area_id=area_id, bbox=bbox
    )
    assert result1.evidence_inputs[0].evidence_id == result2.evidence_inputs[0].evidence_id


def test_different_area_ids_produce_different_evidence_ids() -> None:
    bbox = _bbox()
    two_call_1 = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    two_call_2 = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    result1 = NoaaClimateConnector(source=_source(), fetch_json=two_call_1).query_bbox(
        area_id=uuid4(), bbox=bbox
    )
    result2 = NoaaClimateConnector(source=_source(), fetch_json=two_call_2).query_bbox(
        area_id=uuid4(), bbox=bbox
    )
    assert result1.evidence_inputs[0].evidence_id != result2.evidence_inputs[0].evidence_id


def test_same_inputs_produce_same_ingest_run_id() -> None:
    area_id = uuid4()
    bbox = _bbox()
    two_call_1 = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    two_call_2 = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    result1 = NoaaClimateConnector(source=_source(), fetch_json=two_call_1).query_bbox(
        area_id=area_id, bbox=bbox
    )
    result2 = NoaaClimateConnector(source=_source(), fetch_json=two_call_2).query_bbox(
        area_id=area_id, bbox=bbox
    )
    assert result1.retrieval_run.ingest_run_id == result2.retrieval_run.ingest_run_id


# --- Caveat ---


def test_evidence_caveat_includes_noaa_nws_text() -> None:
    area_id = uuid4()
    two_call = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    evidence = result.evidence_inputs[0]
    assert evidence.caveat is not None
    assert "NOAA" in evidence.caveat


def test_noaa_climate_caveat_constant_includes_forecast_zone_text() -> None:
    assert "forecast zone" in NOAA_CLIMATE_CAVEAT.lower()


def test_noaa_climate_caveat_constant_mentions_ncei_normals() -> None:
    assert "NCEI" in NOAA_CLIMATE_CAVEAT


# --- License guard ---


def test_license_blocked_before_fetch() -> None:
    fetch_called = False

    def tracking_fetch(url: str, timeout: float) -> Mapping[str, object]:
        nonlocal fetch_called
        fetch_called = True
        return _nws_points_response()

    with pytest.raises(ConnectorLicenseBlockedError):
        NoaaClimateConnector(
            source=_source(license_status="unknown"),
            fetch_json=tracking_fetch,
        ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert fetch_called is False


# --- Request URL ---


def test_request_url_contains_weather_gov() -> None:
    area_id = uuid4()
    two_call = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=_bbox()
    )
    assert "api.weather.gov" in result.request_url


def test_request_url_contains_bbox_centroid() -> None:
    area_id = uuid4()
    bbox = _bbox()
    two_call = _TwoCallMock(_nws_points_response(), _nws_zone_response())
    result = NoaaClimateConnector(source=_source(), fetch_json=two_call).query_bbox(
        area_id=area_id, bbox=bbox
    )
    lat, lon = bbox.centroid
    assert f"{lat:.4f}" in result.request_url
    assert f"{lon:.4f}" in result.request_url
