from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices, get_db_services, get_services
from app.claims_engine.not_evaluated import (
    NOT_EVALUATED_CLAIM_CODES,
    NOT_EVALUATED_DOMAINS,
    NOT_EVALUATED_SOURCE_NAME,
)
from app.core.config import Settings
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def not_evaluated_claim_codes() -> list[str]:
    return [NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS]


def test_api_scaffold_exposes_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200


def test_api_scaffold_lists_empty_in_memory_resources() -> None:
    client = TestClient(create_app())
    area_id = uuid4()

    assert client.get("/sources").json() == []
    assert client.get("/areas").json() == []
    assert client.get(f"/evidence?area_id={area_id}").json() == []


def test_api_runtime_uses_memory_backend_by_default_for_isolated_tests() -> None:
    app = create_app(settings=Settings(APP_STORAGE_BACKEND="postgres"))

    assert app.state.storage_backend == "memory"
    assert get_services not in app.dependency_overrides
    assert hasattr(app.state, "services")


def test_api_runtime_can_use_configured_postgres_backend() -> None:
    app = create_app(
        settings=Settings(APP_STORAGE_BACKEND="postgres"),
        use_db_services=None,
    )

    assert app.state.storage_backend == "postgres"
    assert app.dependency_overrides[get_services] is get_db_services


def test_api_scaffold_creates_and_lists_sources() -> None:
    client = TestClient(create_app())

    create_response = client.post(
        "/sources",
        json={
            "name": "Fixture FEMA",
            "organization": "FEMA",
            "domain": "flood",
            "license_status": "approved",
            "commercial_use_status": "approved",
            "review_status": "approved",
        },
    )

    assert create_response.status_code == 201
    source_id = create_response.json()["source_id"]
    list_response = client.get("/sources")
    assert list_response.status_code == 200
    assert [source["source_id"] for source in list_response.json()] == [source_id]


def test_api_scaffold_creates_and_lists_areas() -> None:
    client = TestClient(create_app())

    create_response = client.post(
        "/areas",
        json={
            "label": "fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "api fixture",
        },
    )

    assert create_response.status_code == 201
    area_id = create_response.json()["area_id"]
    list_response = client.get("/areas")
    assert list_response.status_code == 200
    assert [area["area_id"] for area in list_response.json()] == [area_id]


def test_api_scaffold_creates_and_gets_report_run() -> None:
    client = TestClient(create_app())
    area_response = client.post(
        "/areas",
        json={
            "label": "fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "api fixture",
        },
    )
    area_id = area_response.json()["area_id"]

    create_response = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "homestead_feasibility"},
    )

    assert create_response.status_code == 201
    report_run = create_response.json()
    assert report_run["area_id"] == area_id
    assert report_run["status"] == "succeeded"
    assert [record["domain"] for record in report_run["evidence"]] == list(NOT_EVALUATED_DOMAINS)
    assert [claim["claim_code"] for claim in report_run["claims"]] == (not_evaluated_claim_codes())
    assert [claim["claim_code"] for claim in report_run["unknowns"]] == (
        not_evaluated_claim_codes()
    )
    assert report_run["source_manifest"]["source_names"] == [NOT_EVALUATED_SOURCE_NAME]
    assert report_run["source_manifest"]["evidence_count"] == 4
    assert report_run["source_manifest"]["claim_count"] == 4
    assert report_run["artifact_metadata"]["artifact_kind"] == "report_run"
    assert report_run["artifact_metadata"]["report_schema"] == "report_run_contract_v1"
    assert report_run["artifact_metadata"]["persistence"] == "memory"
    assert report_run["artifact_metadata"]["cost_metrics"]["unknown_count"] == 4

    get_response = client.get(f"/report-runs/{report_run['report_run_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["report_run_id"] == report_run["report_run_id"]

    list_response = client.get(
        f"/report-runs?area_id={area_id}&intent_code=homestead_feasibility"
    )
    assert list_response.status_code == 200
    assert [run["report_run_id"] for run in list_response.json()] == [
        report_run["report_run_id"]
    ]
    assert client.get(f"/report-runs?area_id={uuid4()}").json() == []
    assert client.get("/report-runs?limit=0").status_code == 422


def test_api_report_run_surfaces_source_failure_unknowns() -> None:
    app = create_app()
    client = TestClient(app)
    source_response = client.post(
        "/sources",
        json={
            "name": "Fixture FEMA failure source",
            "organization": "FEMA",
            "domain": "flood",
            "license_status": "approved",
            "commercial_use_status": "approved",
            "review_status": "approved",
        },
    )
    area_response = client.post(
        "/areas",
        json={
            "label": "fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "api fixture",
        },
    )
    source_id = UUID(source_response.json()["source_id"])
    area_id = UUID(area_response.json()["area_id"])
    services = cast(ApiServices, app.state.services)
    services.evidence_service.create_source_failure(
        area_id=area_id,
        source_id=source_id,
        method_code="fixture_flood_overlay",
        evidence_code="FLOOD_SOURCE_FAILURE",
        domain="flood",
        caveat="FEMA fixture endpoint returned 503.",
    )

    create_response = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
    )

    assert create_response.status_code == 201
    report_run = create_response.json()
    assert [claim["claim_code"] for claim in report_run["unknowns"]] == [
        "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        *not_evaluated_claim_codes(),
    ]
    assert report_run["artifact_metadata"]["cost_metrics"]["unknown_count"] == 5


def test_api_scaffold_returns_422_for_bad_input() -> None:
    client = TestClient(create_app())

    assert client.post("/sources", json={"name": "Missing domain"}).status_code == 422
    assert (
        client.post(
            "/areas",
            json={"geom_geojson": load_geometry("wrong_type.geojson")},
        ).status_code
        == 422
    )
    assert client.post("/report-runs", json={"intent_code": "missing area"}).status_code == 422
    assert client.get("/evidence").status_code == 422
