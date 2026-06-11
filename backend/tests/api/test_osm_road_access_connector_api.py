from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.area_contracts import AreaContract
from app.domain.enums import EvidenceType
from app.domain.source_contracts import SourceContract
from app.main import create_app

_VALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}


def _area(area_id: UUID) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        label="OSM Road Access API test area",
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
        name="OpenStreetMap/Overture",
        organization="OSM/Overture",
        source_type="Open community/open data",
        domain="Roads/buildings/base map",
        geographic_scope="Global",
        license_status="approved-with-restrictions",
        commercial_use_status="approved-with-restrictions",
        redistribution_status="restricted",
        attribution_required=True,
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="restricted",
        freshness_class="current-effective",
        last_checked_at="2026-06-10",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-016"},
    )


def _body(area_id: UUID, *, max_features: int = 500) -> dict[str, object]:
    return {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -79.10,
            "ymin": 35.80,
            "xmax": -79.00,
            "ymax": 35.90,
        },
        "max_features": max_features,
    }


def _overpass_roads_found(way_count: int = 3) -> dict[str, object]:
    return {
        "elements": [
            {
                "type": "count",
                "id": 0,
                "tags": {
                    "total": str(way_count),
                    "nodes": "0",
                    "ways": str(way_count),
                    "relations": "0",
                    "areas": "0",
                },
            }
        ]
    }


def _overpass_no_roads() -> dict[str, object]:
    return {
        "elements": [
            {
                "type": "count",
                "id": 0,
                "tags": {
                    "total": "0",
                    "nodes": "0",
                    "ways": "0",
                    "relations": "0",
                    "areas": "0",
                },
            }
        ]
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

    def fetch_json(url: str, _timeout: float) -> dict[str, object]:
        return fetch_payload

    services.osm_road_access_fetch_json = fetch_json
    return TestClient(app), services, area_id


def test_osm_road_access_query_bbox_returns_202_with_roads_found() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload=_overpass_roads_found(way_count=3),
    )

    response = client.post(
        "/connector-runs/osm-road-access/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "osm_road_access_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 3
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["source_registry_id"] == "DS-016"
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence[0].domain == "access"
    assert evidence[0].observed_value["has_public_road_adjacency"] is True


def test_osm_road_access_query_bbox_returns_422_for_missing_area() -> None:
    client, _services, _area_id = _client_with_seeded_services(
        fetch_payload=_overpass_roads_found(),
    )
    body = _body(uuid4())  # unregistered area

    response = client.post(
        "/connector-runs/osm-road-access/query-bbox",
        json=body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_osm_road_access_query_bbox_source_registry_id_is_ds016() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload=_overpass_roads_found(),
    )

    response = client.post(
        "/connector-runs/osm-road-access/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    assert response.json()["source_registry_id"] == "DS-016"


def test_osm_road_access_query_bbox_no_roads_returns_succeeded() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload=_overpass_no_roads(),
    )

    response = client.post(
        "/connector-runs/osm-road-access/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 0
    assert body["evidence_created_count"] == 1

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].observed_value["has_public_road_adjacency"] is False
    assert "road_distance_m" not in evidence[0].observed_value


def test_osm_road_access_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload=_overpass_roads_found(),
    )

    response = client.post(
        "/connector-runs/osm-road-access/query-bbox",
        json=_body(area_id),
    )

    assert response.status_code == 401


def test_osm_road_access_query_bbox_request_url_in_response() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload=_overpass_roads_found(),
    )

    response = client.post(
        "/connector-runs/osm-road-access/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    assert "overpass" in response.json()["request_url"]
