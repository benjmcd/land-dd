from __future__ import annotations

from urllib.error import URLError
from uuid import uuid4

import pytest

from app.connectors.buncombe_parcels import (
    BUNCOMBE_PARCELS_CONNECTOR_NAME,
    BUNCOMBE_PARCELS_SERVICE_URL,
    BuncombeParcelsBbox,
    BuncombeParcelsConnector,
    BuncombeParcelsConnectorError,
    _build_query_url,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source() -> SourceContract:
    return SourceContract(
        name="Buncombe County GIS Parcels",
        organization="Buncombe County GIS",
        source_type="Local official",
        domain="Parcels",
        geographic_scope="County",
        license_status="approved-with-restrictions",
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


def _bbox() -> BuncombeParcelsBbox:
    return BuncombeParcelsBbox(xmin=-82.55, ymin=35.58, xmax=-82.54, ymax=35.59)


def _success_payload() -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"pinnum": "9641273894012", "Acreage": 5.2},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-82.55, 35.58],
                            [-82.54, 35.58],
                            [-82.54, 35.59],
                            [-82.55, 35.59],
                            [-82.55, 35.58],
                        ]
                    ],
                },
            }
        ],
    }


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


def test_success_returns_succeeded_retrieval_run_and_evidence() -> None:
    source = _source()
    area_id = uuid4()

    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return _success_payload()

    result = BuncombeParcelsConnector(source=source, fetch_json=fetch_json).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert result.retrieval_run.connector_name == BUNCOMBE_PARCELS_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-011"

    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.source_id == source.source_id
    assert evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence.evidence_code == "COUNTY_PARCEL_INTERSECTION"
    assert evidence.domain == "parcels"
    assert evidence.is_source_failure is False
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.observed_value["intersects"] is True
    assert evidence.observed_value["parcel_pin"] == "9641273894012"
    assert evidence.observed_value["parcel_acres"] == 5.2
    assert evidence.observed_value["parcel_zoning"] is None


def test_success_parcel_zoning_is_always_none() -> None:
    source = _source()

    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return _success_payload()

    result = BuncombeParcelsConnector(source=source, fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    for ev in result.evidence_inputs:
        assert ev.observed_value["parcel_zoning"] is None


def test_success_url_contains_pinnum_acreage_outfields() -> None:
    url = _build_query_url(bbox=_bbox(), max_features=100)

    assert "pinnum%2CAcreage" in url or "pinnum,Acreage" in url
    assert BUNCOMBE_PARCELS_SERVICE_URL in url


# ---------------------------------------------------------------------------
# Request error
# ---------------------------------------------------------------------------


def test_request_error_emits_source_failure_evidence() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        raise URLError("connection refused")

    result = BuncombeParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.error_count == 1
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.evidence_code == "BUNCOMBE_PARCELS_SOURCE_FAILURE"
    assert evidence.is_source_failure is True
    assert evidence.observed_value["failure_reason"] == "buncombe_parcels_request_error"
    assert evidence.observed_value["retryable"] is True


# ---------------------------------------------------------------------------
# Service error
# ---------------------------------------------------------------------------


def test_service_error_response_emits_source_failure_evidence() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return {"error": {"message": "Service unavailable"}}

    result = BuncombeParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "BUNCOMBE_PARCELS_SOURCE_FAILURE"
    assert evidence.observed_value["failure_reason"] == "buncombe_parcels_service_error"
    assert evidence.observed_value["retryable"] is True


# ---------------------------------------------------------------------------
# exceededTransferLimit
# ---------------------------------------------------------------------------


def test_exceeded_transfer_limit_emits_non_retryable_source_failure() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return {"exceededTransferLimit": True, "features": []}

    result = BuncombeParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["failure_reason"] == "buncombe_parcels_transfer_limit_exceeded"
    assert evidence.observed_value["retryable"] is False


# ---------------------------------------------------------------------------
# Malformed responses
# ---------------------------------------------------------------------------


def test_malformed_response_no_features_list_emits_source_failure() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection"}

    result = BuncombeParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["failure_reason"] == "buncombe_parcels_malformed_response"
    assert evidence.observed_value["retryable"] is True


def test_malformed_response_non_object_feature_emits_source_failure() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": ["not-an-object"]}

    result = BuncombeParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["failure_reason"] == "buncombe_parcels_malformed_response"
    assert evidence.observed_value["retryable"] is True


# ---------------------------------------------------------------------------
# No features
# ---------------------------------------------------------------------------


def test_empty_features_list_emits_non_retryable_source_failure() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": []}

    result = BuncombeParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "BUNCOMBE_PARCELS_SOURCE_FAILURE"
    assert evidence.observed_value["failure_reason"] == "buncombe_parcels_no_features"
    assert evidence.observed_value["retryable"] is False


# ---------------------------------------------------------------------------
# Invalid bbox validation
# ---------------------------------------------------------------------------


def test_invalid_bbox_xmin_ge_xmax_raises_error() -> None:
    with pytest.raises(BuncombeParcelsConnectorError, match="xmin must be less than xmax"):
        BuncombeParcelsBbox(xmin=-82.54, ymin=35.58, xmax=-82.55, ymax=35.59)


def test_invalid_bbox_span_exceeds_limit_raises_error() -> None:
    with pytest.raises(BuncombeParcelsConnectorError, match="span exceeds Buncombe Parcels limit"):
        BuncombeParcelsBbox(xmin=-83.0, ymin=35.58, xmax=-81.9, ymax=35.59)


# ---------------------------------------------------------------------------
# max_features=0 raises error
# ---------------------------------------------------------------------------


def test_max_features_zero_raises_error() -> None:
    with pytest.raises(BuncombeParcelsConnectorError, match="max_features"):
        BuncombeParcelsConnector(
            source=_source(),
            fetch_json=lambda url, t: _success_payload(),
        ).query_bbox(area_id=uuid4(), bbox=_bbox(), max_features=0)


# ---------------------------------------------------------------------------
# Deterministic ingest_run_id
# ---------------------------------------------------------------------------


def test_ingest_run_id_is_deterministic_for_same_inputs() -> None:
    source = _source()
    area_id = uuid4()
    bbox = _bbox()

    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return _success_payload()

    connector = BuncombeParcelsConnector(source=source, fetch_json=fetch_json)
    first = connector.query_bbox(area_id=area_id, bbox=bbox)
    second = connector.query_bbox(area_id=area_id, bbox=bbox)

    assert first.retrieval_run.ingest_run_id == second.retrieval_run.ingest_run_id
    assert first.evidence_inputs[0].evidence_id == second.evidence_inputs[0].evidence_id


# ---------------------------------------------------------------------------
# evidence_code checks
# ---------------------------------------------------------------------------


def test_success_evidence_code_is_county_parcel_intersection() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        return _success_payload()

    result = BuncombeParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.evidence_inputs[0].evidence_code == "COUNTY_PARCEL_INTERSECTION"


def test_source_failure_evidence_code_is_buncombe_parcels_source_failure() -> None:
    def fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        raise URLError("timeout")

    result = BuncombeParcelsConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.evidence_inputs[0].evidence_code == "BUNCOMBE_PARCELS_SOURCE_FAILURE"
