from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.area_contracts import AreaContract
from app.domain.source_contracts import SourceContract
from app.main import create_app

_VALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}


def _assessor_source() -> SourceContract:
    return SourceContract(
        name="County assessor",
        organization="County",
        source_type="local_official",
        domain="assessor",
        license_status="approved-with-restrictions",
        commercial_use_status="restricted",
        metadata={"source_registry_id": "DS-011"},
    )


def _area(area_id: object) -> AreaContract:
    return AreaContract(
        area_id=area_id,  # type: ignore[arg-type]
        label="Assessor not-evaluated API test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-79.30, 35.65],
                    [-79.25, 35.65],
                    [-79.25, 35.70],
                    [-79.30, 35.70],
                    [-79.30, 35.65],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


def _client_with_seeded_services() -> tuple[TestClient, ApiServices, object]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_assessor_source())
    services.area_service.create(_area(area_id))
    return TestClient(app), services, area_id


def test_query_assessor_not_evaluated_requires_auth() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/connector-runs/assessor-not-evaluated/query",
        json={"area_id": str(uuid4())},
    )
    assert response.status_code in (401, 403, 422)


def test_query_assessor_not_evaluated_unregistered_area_returns_422() -> None:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    services.source_service.register(_assessor_source())
    client = TestClient(app)
    missing_id = uuid4()

    response = client.post(
        "/connector-runs/assessor-not-evaluated/query",
        json={"area_id": str(missing_id)},
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422
    assert "not registered" in response.json()["detail"]


def test_query_assessor_not_evaluated_valid_area_returns_202() -> None:
    client, services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/assessor-not-evaluated/query",
        json={"area_id": str(area_id)},
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "county_assessor_not_evaluated"
    assert body["retrieval_status"] == "succeeded"
    assert body["evidence_code"] == "ASSESSOR_NOT_EVALUATED"
    assert body["source_registry_id"] == "DS-011"
    assert "ingest_run_id" in body
