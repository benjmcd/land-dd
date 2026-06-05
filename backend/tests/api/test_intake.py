from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def _valid_geojson() -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _wrong_type_geojson() -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / "wrong_type.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_intake_returns_202_with_ids() -> None:
    client = TestClient(create_app())
    resp = client.post(
        "/intake",
        json={"area_geojson": _valid_geojson(), "intent_code": "rural_land_purchase"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "report_run_id" in data
    assert "area_id" in data
    assert data["status"] == "queued"


def test_intake_report_completes_after_background_task() -> None:
    client = TestClient(create_app())
    post = client.post(
        "/intake",
        json={"area_geojson": _valid_geojson(), "intent_code": "rural_land_purchase"},
    )
    assert post.status_code == 202
    report_run_id = post.json()["report_run_id"]

    get = client.get(f"/report-runs/{report_run_id}")
    assert get.status_code == 200
    assert get.json()["status"] == "succeeded"


def test_intake_invalid_geojson_returns_422() -> None:
    client = TestClient(create_app())
    resp = client.post(
        "/intake",
        json={"area_geojson": _wrong_type_geojson(), "intent_code": "rural_land_purchase"},
    )
    assert resp.status_code == 422


def test_intake_unknown_intent_code_returns_422() -> None:
    client = TestClient(create_app())
    resp = client.post(
        "/intake",
        json={"area_geojson": _valid_geojson(), "intent_code": "not_a_real_intent"},
    )
    assert resp.status_code == 422


def test_intake_area_id_differs_per_call() -> None:
    client = TestClient(create_app())
    r1 = client.post(
        "/intake",
        json={"area_geojson": _valid_geojson(), "intent_code": "rural_land_purchase"},
    )
    r2 = client.post(
        "/intake",
        json={"area_geojson": _valid_geojson(), "intent_code": "rural_land_purchase"},
    )
    assert r1.json()["area_id"] != r2.json()["area_id"]
    assert r1.json()["report_run_id"] != r2.json()["report_run_id"]
