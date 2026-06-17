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
        label="BLM MLRS API test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-118.0, 37.0],
                    [-117.5, 37.0],
                    [-117.5, 37.5],
                    [-118.0, 37.5],
                    [-118.0, 37.0],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


def _source() -> SourceContract:
    return SourceContract(
        name="BLM MLRS",
        organization="BLM",
        source_type="Public official",
        domain="Mineral/land records",
        geographic_scope="Federal lands/US",
        license_status="approved-with-restrictions",
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        update_cadence="continuous",
        freshness_class="current-effective",
        last_checked_at="2026-06-11",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-007"},
    )


def _body(area_id: UUID) -> dict[str, object]:
    return {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -118.0,
            "ymin": 37.0,
            "xmax": -117.5,
            "ymax": 37.5,
        },
    }


def _feature_payload() -> dict[str, object]:
    return {
        "features": [
            {
                "attributes": {
                    "OBJECTID": 4601950,
                    "CSE_NR": "NV105228507",
                    "LEG_CSE_NR": "",
                    "CSE_NAME": "Rosemalis Mine",
                    "CSE_DISP": "Active",
                    "CSE_TYPE_NR": "384101",
                    "BLM_PROD": "Lode Claim",
                    "QLTY": "0: 25 sections retrieved",
                    "RCRD_ACRS": 20.66115702,
                }
            }
        ]
    }


def _client_with_seeded_services() -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id))
    services.blm_mlrs_fetch_json = lambda _url, _timeout_seconds: _feature_payload()
    return TestClient(app), services, area_id


def test_blm_mlrs_query_bbox_returns_202_with_active_claim_context() -> None:
    client, services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/blm-mlrs/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "blm_mlrs_active_mining_claims_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 1
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["source_registry_id"] == "DS-007"
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence[0].domain == "minerals"
    assert evidence[0].observed_value["primary_blm_mlrs_case_serial_number"] == (
        "NV105228507"
    )
    assert evidence[0].observed_value["mineral_rights_determined"] is False
    assert evidence[0].observed_value["has_blm_active_mining_claim_context"] is True


def test_blm_mlrs_query_bbox_returns_422_for_missing_area() -> None:
    client, _services, _area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/blm-mlrs/query-bbox",
        json=_body(uuid4()),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_blm_mlrs_query_bbox_rejects_oversized_bbox() -> None:
    client, _services, area_id = _client_with_seeded_services()
    bad_body = {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -118.0,
            "ymin": 37.0,
            "xmax": -117.4,
            "ymax": 37.5,
        },
    }

    response = client.post(
        "/connector-runs/blm-mlrs/query-bbox",
        json=bad_body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_blm_mlrs_query_bbox_rejects_excessive_max_features() -> None:
    client, _services, area_id = _client_with_seeded_services()
    body = _body(area_id)
    body["max_features"] = 51

    response = client.post(
        "/connector-runs/blm-mlrs/query-bbox",
        json=body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_blm_mlrs_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/blm-mlrs/query-bbox",
        json=_body(area_id),
    )

    assert response.status_code == 401


def test_blm_mlrs_query_bbox_request_url_in_response() -> None:
    client, _services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/blm-mlrs/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    assert "Mining_Claims" in response.json()["request_url"]
