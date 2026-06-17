from __future__ import annotations

from urllib.error import URLError
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.area_contracts import AreaContract
from app.domain.enums import EvidenceType
from app.domain.source_contracts import SourceContract
from app.main import create_app

_WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
_VALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
    "X-Workspace-Id": str(_WORKSPACE_ID),
    "X-User-Id": str(_USER_ID),
}


def _area(area_id: UUID, *, workspace_id: UUID | None = _WORKSPACE_ID) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        workspace_id=workspace_id,
        label="Buncombe parcels API test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-82.60, 35.50],
                    [-82.40, 35.50],
                    [-82.40, 35.65],
                    [-82.60, 35.65],
                    [-82.60, 35.50],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


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
        last_checked_at="2026-06-06",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-010"},
    )


def _feature() -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {
            "pinnum": "9876543210",
            "Acreage": 2.3,
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-82.55, 35.55],
                    [-82.50, 35.55],
                    [-82.50, 35.60],
                    [-82.55, 35.60],
                    [-82.55, 35.55],
                ]
            ],
        },
    }


def _body(area_id: UUID) -> dict[str, object]:
    return {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -82.60,
            "ymin": 35.50,
            "xmax": -82.40,
            "ymax": 35.65,
        },
        "max_features": 100,
    }


def _client_with_seeded_services(
    *,
    fetch_payload: dict[str, object] | None = None,
    fetch_error: Exception | None = None,
) -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id))

    def fetch_json(url: str, _timeout_seconds: float) -> dict[str, object]:
        if fetch_error is not None:
            raise fetch_error
        assert fetch_payload is not None
        return fetch_payload

    services.buncombe_parcels_fetch_json = fetch_json
    return TestClient(app), services, area_id


def test_buncombe_parcels_query_bbox_returns_202_and_persists_evidence() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )

    response = client.post(
        "/connector-runs/buncombe-parcels/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "buncombe_parcels_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 1
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["source_registry_id"] == "DS-010"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence[0].domain == "parcels"
    assert evidence[0].is_source_failure is False
    assert evidence[0].observed_value.get("parcel_pin") == "9876543210"


def test_buncombe_parcels_query_bbox_empty_response_emits_source_failure() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )

    response = client.post(
        "/connector-runs/buncombe-parcels/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["retrieval_status"] == "failed"
    assert body["source_failure_created_count"] == 1
    assert body["review_required"] is True

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence[0].is_source_failure is True
    assert evidence[0].observed_value.get("failure_reason") == "buncombe_parcels_no_features"


def test_buncombe_parcels_query_bbox_connection_error_emits_source_failure() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_error=URLError("connection refused"),
    )

    response = client.post(
        "/connector-runs/buncombe-parcels/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["retrieval_status"] == "failed"
    assert body["source_failure_created_count"] == 1
    assert body["review_required"] is True

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence[0].observed_value.get("failure_reason") == "buncombe_parcels_request_error"


def test_buncombe_parcels_query_bbox_rejects_unregistered_area() -> None:
    client, _services, _area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )
    missing_id = uuid4()

    response = client.post(
        "/connector-runs/buncombe-parcels/query-bbox",
        json={
            "area_id": str(missing_id),
            "bbox": {"xmin": -82.60, "ymin": 35.50, "xmax": -82.40, "ymax": 35.65},
            "max_features": 10,
        },
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_buncombe_parcels_query_bbox_rejects_missing_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )

    response = client.post(
        "/connector-runs/buncombe-parcels/query-bbox",
        json=_body(area_id),
    )

    assert response.status_code in (401, 403)
