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
_WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
_VALID_HEADERS.update(
    {
        "X-Workspace-Id": str(_WORKSPACE_ID),
        "X-User-Id": str(_USER_ID),
    }
)


def _area(area_id: UUID, *, workspace_id: UUID | None = _WORKSPACE_ID) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        workspace_id=workspace_id,
        label="Census TIGER API test area",
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
        name="Census TIGER/ACS",
        organization="Census",
        source_type="Public official",
        domain="Boundaries/demographics",
        geographic_scope="US",
        license_status="approved-with-restrictions",
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
        metadata={"source_registry_id": "DS-022"},
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


def _tract_payload() -> dict[str, object]:
    return {
        "features": [
            {
                "attributes": {
                    "GEOID": "37037020105",
                    "NAME": "Census Tract 201.05",
                    "STATE": "37",
                    "COUNTY": "037",
                    "TRACT": "020105",
                }
            }
        ]
    }


def _block_group_payload() -> dict[str, object]:
    return {
        "features": [
            {
                "attributes": {
                    "GEOID": "370370201051",
                    "NAME": "Block Group 1",
                    "STATE": "37",
                    "COUNTY": "037",
                    "TRACT": "020105",
                    "BLKGRP": "1",
                }
            }
        ]
    }


class _TwoLayerFetch:
    def __call__(self, url: str, _timeout_seconds: float) -> dict[str, object]:
        if "/0/query" in url:
            return _tract_payload()
        if "/1/query" in url:
            return _block_group_payload()
        raise AssertionError(f"unexpected layer URL: {url}")


def _client_with_seeded_services() -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id))
    services.census_tiger_fetch_json = _TwoLayerFetch()
    return TestClient(app), services, area_id


def test_census_tiger_query_bbox_returns_202_with_geography_context() -> None:
    client, services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/census-tiger/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "census_tiger_geography_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 2
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["source_registry_id"] == "DS-022"
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence[0].domain == "census_geography"
    assert evidence[0].observed_value["primary_census_tract_geoid"] == "37037020105"
    assert evidence[0].observed_value["census_demographics_used"] is False


def test_census_tiger_query_bbox_returns_422_for_missing_area() -> None:
    client, _services, _area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/census-tiger/query-bbox",
        json=_body(uuid4()),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_census_tiger_query_bbox_rejects_oversized_bbox() -> None:
    client, _services, area_id = _client_with_seeded_services()
    bad_body = {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -80.00,
            "ymin": 35.80,
            "xmax": -79.00,
            "ymax": 35.90,
        },
    }

    response = client.post(
        "/connector-runs/census-tiger/query-bbox",
        json=bad_body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_census_tiger_query_bbox_rejects_excessive_max_features() -> None:
    client, _services, area_id = _client_with_seeded_services()
    body = _body(area_id)
    body["max_features"] = 51

    response = client.post(
        "/connector-runs/census-tiger/query-bbox",
        json=body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_census_tiger_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/census-tiger/query-bbox",
        json=_body(area_id),
    )

    assert response.status_code == 401


def test_census_tiger_query_bbox_request_url_in_response() -> None:
    client, _services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/census-tiger/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    assert "tigerweb.geo.census.gov" in response.json()["request_url"]
