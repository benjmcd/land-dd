from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.main import create_app

client = TestClient(create_app())

_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def _valid_geojson() -> dict[str, object]:
    data = json.loads((_FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _make_app_client_with_report() -> tuple[FastAPI, TestClient, str]:
    app = create_app()
    tc = TestClient(app)
    area_resp = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]
    run_resp = tc.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert run_resp.status_code == 202
    return app, tc, run_resp.json()["report_run_id"]


def test_ui_index_returns_200_html() -> None:
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Land Diligence" in response.text


def test_ui_index_has_intent_form() -> None:
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "rural_land_purchase" in response.text
    assert "homestead_feasibility" in response.text


def test_ui_report_run_returns_404_page_for_unknown_id() -> None:
    response = client.get(f"/ui/report-runs/{uuid4()}")
    assert response.status_code == 200  # We return 200 HTML with "not found" message
    assert "text/html" in response.headers["content-type"]
    assert "Not Found" in response.text


def test_ui_report_run_invalid_uuid_returns_422() -> None:
    response = client.get("/ui/report-runs/not-a-uuid")
    assert response.status_code == 422


def test_ui_report_run_shows_pending_approval_for_unapproved_report() -> None:
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.get(f"/ui/report-runs/{report_run_id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Pending" in response.text or "pending" in response.text
    assert "Executive Summary" not in response.text


def test_ui_report_run_shows_dossier_after_approval() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(UUID(report_run_id), reviewer_id="test-reviewer")
    response = tc.get(f"/ui/report-runs/{report_run_id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Executive Summary" in response.text


def test_ui_report_run_list_returns_html_table() -> None:
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.get("/ui/report-runs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert report_run_id[:8] in response.text


def test_ui_report_run_list_empty_state() -> None:
    tc = TestClient(create_app())
    response = tc.get("/ui/report-runs")
    assert response.status_code == 200
    assert "No report runs yet" in response.text


def test_ui_approve_report_run_redirects_on_success() -> None:
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Approved" in response.text
    # Dossier now accessible
    dossier_resp = tc.get(f"/ui/report-runs/{report_run_id}")
    assert "Executive Summary" in dossier_resp.text


def test_ui_approve_report_run_unknown_id() -> None:
    tc = TestClient(create_app())
    response = tc.post(f"/ui/report-runs/{uuid4()}/approve")
    assert response.status_code == 200
    assert "Not Found" in response.text
