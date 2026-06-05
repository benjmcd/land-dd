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
            name="Fixture Source",
            domain="fixture",
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


def test_flood_ingest_then_report_produces_flood_high_risk_claim() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    ingest = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "flood_success"},
    )
    assert ingest.status_code == 201

    report = client.post(
        "/report-runs",
        json={"area_id": str(_FIXTURE_AREA_ID), "intent_code": "homestead_feasibility"},
    )
    assert report.status_code == 201
    body = report.json()

    flood_red_flags = [c for c in body["red_flags"] if c["domain"] == "flood"]
    assert len(flood_red_flags) >= 1, (
        "expected a flood red-flag claim after ingesting AE zone evidence"
    )
    assert flood_red_flags[0]["claim_code"] == "FLOOD_001"
    assert flood_red_flags[0]["severity"] == "high"


def test_flood_failure_ingest_then_report_produces_flood_unknown_claim() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    ingest = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "flood_failure"},
    )
    assert ingest.status_code == 201

    report = client.post(
        "/report-runs",
        json={"area_id": str(_FIXTURE_AREA_ID), "intent_code": "homestead_feasibility"},
    )
    assert report.status_code == 201
    body = report.json()

    flood_unknowns = [c for c in body["unknowns"] if c["domain"] == "flood"]
    assert len(flood_unknowns) >= 1, (
        "expected a flood unknown claim after source failure"
    )
    assert any(
        c["claim_code"] == "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN" for c in flood_unknowns
    )


def test_zoning_prohibited_ingest_then_report_produces_zoning_red_flag() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    ingest = client.post(
        "/connector-runs",
        json={
            "connector_name": "fixture_zoning_static",
            "fixture_key": "zoning_prohibited",
        },
    )
    assert ingest.status_code == 201

    report = client.post(
        "/report-runs",
        json={"area_id": str(_FIXTURE_AREA_ID), "intent_code": "homestead_feasibility"},
    )
    assert report.status_code == 201
    body = report.json()

    zoning_red_flags = [c for c in body["red_flags"] if c["domain"] == "zoning"]
    assert len(zoning_red_flags) >= 1, (
        "expected a zoning red-flag claim after ingesting prohibited-use evidence"
    )
    assert zoning_red_flags[0]["claim_code"] == "ZONING_001"
    assert zoning_red_flags[0]["severity"] == "critical"


def test_zoning_allowed_ingest_then_report_has_no_zoning_red_flag() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    ingest = client.post(
        "/connector-runs",
        json={
            "connector_name": "fixture_zoning_static",
            "fixture_key": "zoning_allowed",
        },
    )
    assert ingest.status_code == 201

    report = client.post(
        "/report-runs",
        json={"area_id": str(_FIXTURE_AREA_ID), "intent_code": "homestead_feasibility"},
    )
    assert report.status_code == 201
    body = report.json()

    zoning_red_flags = [c for c in body["red_flags"] if c["domain"] == "zoning"]
    assert len(zoning_red_flags) == 0, (
        "expected no zoning red-flag claim when use is allowed"
    )


def test_access_no_road_ingest_then_report_produces_access_red_flag() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    ingest = client.post(
        "/connector-runs",
        json={
            "connector_name": "fixture_access_static",
            "fixture_key": "access_no_road",
        },
    )
    assert ingest.status_code == 201

    report = client.post(
        "/report-runs",
        json={"area_id": str(_FIXTURE_AREA_ID), "intent_code": "homestead_feasibility"},
    )
    assert report.status_code == 201
    body = report.json()

    access_red_flags = [c for c in body["red_flags"] if c["domain"] == "access"]
    assert len(access_red_flags) >= 1, (
        "expected an access red-flag claim after no-road-adjacency evidence"
    )
    assert access_red_flags[0]["claim_code"] == "ACCESS_001"
    assert access_red_flags[0]["severity"] == "critical"


def test_access_road_ingest_then_report_has_no_access_red_flag() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    ingest = client.post(
        "/connector-runs",
        json={
            "connector_name": "fixture_access_static",
            "fixture_key": "access_road",
        },
    )
    assert ingest.status_code == 201

    report = client.post(
        "/report-runs",
        json={"area_id": str(_FIXTURE_AREA_ID), "intent_code": "homestead_feasibility"},
    )
    assert report.status_code == 201
    body = report.json()

    access_red_flags = [c for c in body["red_flags"] if c["domain"] == "access"]
    assert len(access_red_flags) == 0, (
        "expected no access red-flag claim when road adjacency is present"
    )
