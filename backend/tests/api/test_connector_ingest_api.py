from __future__ import annotations

from typing import cast
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.area_contracts import AreaContract
from app.domain.source_contracts import SourceContract
from app.main import create_app

_FIXTURE_SOURCE_ID = UUID("55555555-5555-4555-8555-555555555555")
_FIXTURE_AREA_ID = UUID("44444444-4444-4444-8444-444444444444")
_FIXTURE_AREA_GEOJSON: dict[str, object] = {
    "type": "Polygon",
    "coordinates": [
        [
            [-120.0, 38.0],
            [-119.9, 38.0],
            [-119.9, 38.1],
            [-120.0, 38.1],
            [-120.0, 38.0],
        ]
    ],
}


def _seed(services: ApiServices) -> None:
    services.source_service.register(
        SourceContract(
            source_id=_FIXTURE_SOURCE_ID,
            name="Fixture Flood Source",
            domain="flood",
            license_status="approved",
            commercial_use_status="approved",
            redistribution_status="approved",
            cache_allowed="approved",
            export_allowed="approved",
            raw_data_allowed="approved",
            ai_use_allowed="approved",
            review_status="approved",
        )
    )
    services.area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            geom_geojson=_FIXTURE_AREA_GEOJSON,
        )
    )


def test_run_flood_connector_success_creates_evidence() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    response = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "flood_success"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["ingest_run_id"] == "11111111-1111-4111-8111-111111111111"
    assert body["connector_name"] == "fixture_flood_static"
    assert body["retrieval_status"] == "succeeded"
    assert body["evidence_created"] == 1
    assert body["evidence_skipped"] == 0
    assert body["review_required"] is False
    assert body["queue_job_id"] is not None


def test_run_flood_connector_failure_sets_review_required() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    response = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "flood_failure"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["retrieval_status"] == "blocked"
    assert body["evidence_created"] == 1  # source-failure evidence is first-class
    assert body["review_required"] is True
    assert body["queue_job_id"] is not None


def test_run_connector_returns_422_for_unsupported_connector_name() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/connector-runs",
        json={"connector_name": "unknown_connector", "fixture_key": "flood_success"},
    )

    assert response.status_code == 422
    assert "unsupported connector" in response.json()["detail"]


def test_run_connector_returns_422_for_unknown_fixture_key() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    response = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "does_not_exist"},
    )

    assert response.status_code == 422
    assert "fixture not found" in response.json()["detail"]


def test_run_connector_returns_422_for_invalid_fixture_key_characters() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "../etc/passwd"},
    )

    assert response.status_code == 422
    assert "fixture_key" in response.json()["detail"]
