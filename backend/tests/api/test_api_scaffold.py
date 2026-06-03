from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


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
    area_id = str(uuid4())

    create_response = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "homestead_feasibility"},
    )

    assert create_response.status_code == 201
    report_run = create_response.json()
    assert report_run["area_id"] == area_id
    assert report_run["status"] == "queued"

    get_response = client.get(f"/report-runs/{report_run['report_run_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["report_run_id"] == report_run["report_run_id"]


def test_api_scaffold_returns_422_for_bad_input() -> None:
    client = TestClient(create_app())

    assert client.post("/sources", json={"name": "Missing domain"}).status_code == 422
    assert client.post(
        "/areas",
        json={"geom_geojson": load_geometry("wrong_type.geojson")},
    ).status_code == 422
    assert client.post("/report-runs", json={"intent_code": "missing area"}).status_code == 422
    assert client.get("/evidence").status_code == 422
