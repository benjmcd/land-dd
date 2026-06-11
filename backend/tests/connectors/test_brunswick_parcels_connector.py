from __future__ import annotations

from urllib.error import URLError
from uuid import uuid4

import pytest

from app.connectors.brunswick_parcels import (
    BRUNSWICK_PARCELS_CAVEAT,
    BRUNSWICK_PARCELS_CONNECTOR_NAME,
    BRUNSWICK_PARCELS_MAX_FEATURES,
    BRUNSWICK_PARCELS_METHOD_CODE,
    BRUNSWICK_PARCELS_SERVICE_URL,
    BrunswickParcelsBbox,
    BrunswickParcelsConnector,
    BrunswickParcelsConnectorError,
)
from app.connectors.observability import ConnectorEventType
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="Brunswick County GIS Tax Parcels",
        organization="Brunswick County GIS",
        source_type="Local official",
        domain="Parcels",
        geographic_scope="County",
        license_status=license_status,
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        attribution_required=True,
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        freshness_class="current-effective",
        last_checked_at="2026-06-10",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-011"},
    )


def _bbox() -> BrunswickParcelsBbox:
    return BrunswickParcelsBbox(xmin=-78.30, ymin=34.10, xmax=-78.29, ymax=34.11)


def _success_payload() -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"PIN": "00012345678901234", "CALCAC": 3.7, "Zoning": "R-15"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-78.30, 34.10],
                            [-78.29, 34.10],
                            [-78.29, 34.11],
                            [-78.30, 34.11],
                            [-78.30, 34.10],
                        ]
                    ],
                },
            }
        ],
    }


def test_success_returns_parcel_evidence_with_correct_fields() -> None:
    source = _source()
    area_id = uuid4()

    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        assert timeout_seconds == 30.0
        return _success_payload()

    result = BrunswickParcelsConnector(source=source, fetch_json=fetch_json).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert result.retrieval_run.connector_name == BRUNSWICK_PARCELS_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-011"
    assert result.retrieval_run.metrics["service_url"] == BRUNSWICK_PARCELS_SERVICE_URL

    assert len(result.evidence_inputs) == 1
    ev = result.evidence_inputs[0]
    assert ev.area_id == area_id
    assert ev.source_id == source.source_id
    assert ev.evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert ev.evidence_code == "COUNTY_PARCEL_INTERSECTION"
    assert ev.domain == "parcels"
    assert ev.method_code == BRUNSWICK_PARCELS_METHOD_CODE
    assert ev.confidence == ConfidenceBand.LOW
    assert ev.caveat == BRUNSWICK_PARCELS_CAVEAT
    assert ev.is_source_failure is False
    assert ev.geometry_geojson is not None
    assert ev.geometry_srid == 4326
    assert ev.observed_value["intersects"] is True
    assert ev.observed_value["parcel_pin"] == "00012345678901234"
    assert ev.observed_value["parcel_acres"] == 3.7
    assert ev.observed_value["parcel_zoning"] == "R-15"


def test_success_observability_log_has_expected_events() -> None:
    result = BrunswickParcelsConnector(
        source=_source(),
        fetch_json=lambda _url, _t: _success_payload(),
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert len(result.observability_log.events_of_type(ConnectorEventType.run_started)) == 1
    assert len(result.observability_log.events_of_type(ConnectorEventType.evidence_stored)) == 1
    assert len(result.observability_log.events_of_type(ConnectorEventType.run_succeeded)) == 1


def test_request_error_emits_source_failure() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        raise URLError("connection refused")

    result = BrunswickParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.error_count == 1
    assert result.retrieval_run.metrics["failure_reason"] == "brunswick_parcels_request_error"
    assert result.retrieval_run.metrics["retryable"] is True

    ev = result.evidence_inputs[0]
    assert ev.evidence_type == EvidenceType.SOURCE_FAILURE
    assert ev.evidence_code == "BRUNSWICK_PARCELS_SOURCE_FAILURE"
    assert ev.is_source_failure is True
    assert ev.observed_value["failure_reason"] == "brunswick_parcels_request_error"
    assert ev.observed_value["retryable"] is True


def test_service_error_payload_emits_retryable_source_failure() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return {"error": {"message": "Brunswick GIS service unavailable"}}

    result = BrunswickParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.metrics["failure_reason"] == "brunswick_parcels_service_error"
    assert result.retrieval_run.metrics["retryable"] is True

    ev = result.evidence_inputs[0]
    assert ev.evidence_code == "BRUNSWICK_PARCELS_SOURCE_FAILURE"
    assert ev.observed_value["failure_reason"] == "brunswick_parcels_service_error"
    assert "Brunswick GIS service unavailable" in str(ev.observed_value["error_message"])


def test_exceeded_transfer_limit_emits_non_retryable_source_failure() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return {"exceededTransferLimit": True, "features": []}

    result = BrunswickParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert (
        result.retrieval_run.metrics["failure_reason"]
        == "brunswick_parcels_transfer_limit_exceeded"
    )
    assert result.retrieval_run.metrics["retryable"] is False

    ev = result.evidence_inputs[0]
    assert ev.evidence_code == "BRUNSWICK_PARCELS_SOURCE_FAILURE"
    assert ev.observed_value["retryable"] is False


def test_malformed_response_missing_features_key_emits_source_failure() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection"}  # no "features" key

    result = BrunswickParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.metrics["failure_reason"] == "brunswick_parcels_malformed_response"

    ev = result.evidence_inputs[0]
    assert ev.evidence_code == "BRUNSWICK_PARCELS_SOURCE_FAILURE"
    assert ev.observed_value["failure_reason"] == "brunswick_parcels_malformed_response"


def test_empty_features_array_emits_source_failure() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": []}

    result = BrunswickParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.metrics["failure_reason"] == "brunswick_parcels_no_features"
    assert result.retrieval_run.metrics["retryable"] is False

    ev = result.evidence_inputs[0]
    assert ev.evidence_code == "BRUNSWICK_PARCELS_SOURCE_FAILURE"
    assert ev.observed_value["failure_reason"] == "brunswick_parcels_no_features"


@pytest.mark.parametrize(
    ("bbox_values", "message"),
    [
        ((-78.0, 34.0, -78.1, 34.1), "xmin must be less than xmax"),
        ((-78.3, 34.1, -78.2, 34.0), "ymin must be less than ymax"),
        ((-181.0, 34.0, -180.5, 34.1), "longitude values"),
        ((-78.3, -91.0, -78.2, -90.5), "latitude values"),
        ((-78.5, 34.0, -77.4, 34.1), "longitude span exceeds"),
        ((-78.3, 34.0, -78.2, 35.1), "latitude span exceeds"),
    ],
)
def test_invalid_bbox_raises_connector_error(
    bbox_values: tuple[float, float, float, float], message: str
) -> None:
    with pytest.raises(BrunswickParcelsConnectorError, match=message):
        BrunswickParcelsBbox(*bbox_values)


def test_max_features_zero_raises_connector_error() -> None:
    with pytest.raises(BrunswickParcelsConnectorError, match="max_features"):
        BrunswickParcelsConnector(
            source=_source(),
            fetch_json=lambda _url, _t: _success_payload(),
        ).query_bbox(area_id=uuid4(), bbox=_bbox(), max_features=0)


def test_max_features_over_limit_raises_connector_error() -> None:
    with pytest.raises(BrunswickParcelsConnectorError, match="max_features"):
        BrunswickParcelsConnector(
            source=_source(),
            fetch_json=lambda _url, _t: _success_payload(),
        ).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
            max_features=BRUNSWICK_PARCELS_MAX_FEATURES + 1,
        )


def test_deterministic_ids_for_same_source_area_bbox() -> None:
    source = _source()
    area_id = uuid4()

    connector = BrunswickParcelsConnector(
        source=source,
        fetch_json=lambda _url, _t: _success_payload(),
    )
    first = connector.query_bbox(area_id=area_id, bbox=_bbox())
    second = connector.query_bbox(area_id=area_id, bbox=_bbox())

    assert first.retrieval_run.ingest_run_id == second.retrieval_run.ingest_run_id
    assert first.evidence_inputs[0].evidence_id == second.evidence_inputs[0].evidence_id


def test_success_evidence_code_is_county_parcel_intersection() -> None:
    result = BrunswickParcelsConnector(
        source=_source(),
        fetch_json=lambda _url, _t: _success_payload(),
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.evidence_inputs[0].evidence_code == "COUNTY_PARCEL_INTERSECTION"


def test_failure_evidence_code_is_brunswick_parcels_source_failure() -> None:
    result = BrunswickParcelsConnector(
        source=_source(),
        fetch_json=lambda _url, _t: {"type": "FeatureCollection", "features": []},
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.evidence_inputs[0].evidence_code == "BRUNSWICK_PARCELS_SOURCE_FAILURE"


def test_outfields_contains_pin_calcac_zoning() -> None:
    captured_url: list[str] = []

    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        captured_url.append(url)
        return _success_payload()

    BrunswickParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert captured_url
    assert "PIN%2CCALCAC%2CZoning" in captured_url[0] or "PIN,CALCAC,Zoning" in captured_url[0]


def test_parcel_zoning_field_populated_from_zoning_key() -> None:
    payload: dict[str, object] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"PIN": "99999999999999999", "CALCAC": 1.2, "Zoning": "R-15"},
                "geometry": None,
            }
        ],
    }

    result = BrunswickParcelsConnector(
        source=_source(),
        fetch_json=lambda _url, _t: payload,
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.evidence_inputs[0].observed_value["parcel_zoning"] == "R-15"


def test_source_failure_result_uses_distinct_evidence_id_per_failure_reason() -> None:
    source = _source()
    area_id = uuid4()
    bbox = _bbox()

    def no_features(_url: str, _t: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": []}

    def request_error(_url: str, _t: float) -> dict[str, object]:
        raise URLError("timeout")

    r1 = BrunswickParcelsConnector(source=source, fetch_json=no_features).query_bbox(
        area_id=area_id, bbox=bbox
    )
    r2 = BrunswickParcelsConnector(source=source, fetch_json=request_error).query_bbox(
        area_id=area_id, bbox=bbox
    )

    assert r1.evidence_inputs[0].evidence_id != r2.evidence_inputs[0].evidence_id


def test_request_url_points_to_brunswick_service() -> None:
    captured: list[str] = []

    def fetch_json(url: str, _t: float) -> dict[str, object]:
        captured.append(url)
        return _success_payload()

    BrunswickParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert captured
    assert "bcgis.brunswickcountync.gov" in captured[0]
    assert "TaxParcels" in captured[0]
