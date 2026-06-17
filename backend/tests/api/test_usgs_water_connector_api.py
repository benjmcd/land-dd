from __future__ import annotations

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
        label="USGS Water API test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-79.10, 35.80],
                    [-79.00, 35.80],
                    [-79.00, 35.90],
                    [-79.10, 35.90],
                    [-79.10, 35.80],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


def _source() -> SourceContract:
    return SourceContract(
        name="USGS Water Data APIs",
        organization="U.S. Geological Survey",
        source_type="Public official",
        domain="Water monitoring",
        geographic_scope="US",
        license_status="approved-with-restrictions",
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


def _body(area_id: UUID) -> dict[str, object]:
    return {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -79.10,
            "ymin": 35.80,
            "xmax": -79.00,
            "ymax": 35.90,
        },
    }


def _client_with_seeded_services(
    *,
    fetch_payload: dict[str, object],
) -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id))

    def fetch_json(url: str, _timeout_seconds: float) -> dict[str, object]:
        return fetch_payload

    services.usgs_water_fetch_json = fetch_json
    return TestClient(app), services, area_id


def test_usgs_water_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )

    response = client.post(
        "/connector-runs/usgs-water-monitoring/query-bbox",
        json=_body(area_id),
    )

    assert response.status_code == 401


def test_usgs_water_query_bbox_returns_422_for_missing_area() -> None:
    client, _services, _area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )
    body = _body(uuid4())  # unregistered area

    response = client.post(
        "/connector-runs/usgs-water-monitoring/query-bbox",
        json=body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_usgs_water_query_bbox_stations_found_response() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {"site_no": "02082770"}, "geometry": None},
                {"type": "Feature", "properties": {"site_no": "02082950"}, "geometry": None},
            ],
        },
    )

    response = client.post(
        "/connector-runs/usgs-water-monitoring/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "usgs_water_monitoring_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 2
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["source_registry_id"] == "DS-005"
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence[0].domain == "water"
    assert evidence[0].observed_value["plausible_water_context"] is True
    assert evidence[0].observed_value["monitoring_station_count"] == 2


def test_usgs_water_query_bbox_no_stations_response() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )

    response = client.post(
        "/connector-runs/usgs-water-monitoring/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 0
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["source_registry_id"] == "DS-005"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].observed_value["no_plausible_water_context"] is True
    assert evidence[0].observed_value["monitoring_station_count"] == 0


def test_usgs_water_query_bbox_source_failure_response() -> None:
    from urllib.error import URLError

    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id))

    def fetch_error(url: str, _timeout_seconds: float) -> dict[str, object]:
        raise URLError("simulated network failure")

    services.usgs_water_fetch_json = fetch_error
    client = TestClient(app)

    response = client.post(
        "/connector-runs/usgs-water-monitoring/query-bbox",
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
    assert evidence[0].is_source_failure is True
    assert evidence[0].evidence_code == "WATER_SOURCE_UNAVAILABLE"
