from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def _valid_geojson() -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _make_client_with_area() -> tuple[TestClient, str]:
    app = create_app()
    client = TestClient(app)
    resp = client.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert resp.status_code == 201
    return client, resp.json()["area_id"]


def test_post_report_runs_returns_202() -> None:
    client, area_id = _make_client_with_area()
    resp = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "report_run_id" in data
    assert data["status"] == "queued"


def test_get_report_run_succeeds_after_background_task() -> None:
    """TestClient executes BackgroundTasks synchronously before returning the response."""
    client, area_id = _make_client_with_area()
    post = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert post.status_code == 202
    report_run_id = post.json()["report_run_id"]

    get = client.get(f"/report-runs/{report_run_id}")
    assert get.status_code == 200
    data = get.json()
    assert data["report_run_id"] == report_run_id
    assert data["status"] == "succeeded"
    assert "evidence" in data
    assert "claims" in data


def test_get_report_run_unknown_returns_404() -> None:
    client = TestClient(create_app())
    resp = client.get(f"/report-runs/{uuid4()}")
    assert resp.status_code == 404


def test_post_report_runs_unregistered_area_returns_422() -> None:
    client = TestClient(create_app())
    resp = client.post(
        "/report-runs",
        json={"area_id": str(uuid4()), "intent_code": "rural_land_purchase"},
    )
    assert resp.status_code == 422


def test_post_report_runs_missing_area_id_returns_422() -> None:
    client = TestClient(create_app())
    resp = client.post("/report-runs", json={"intent_code": "rural_land_purchase"})
    assert resp.status_code == 422
