from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.enums import IntentCode
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def _valid_geojson() -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _make_app_client_with_area() -> tuple[FastAPI, TestClient, str]:
    app = create_app()
    client = TestClient(app)
    resp = client.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert resp.status_code == 201
    return app, client, resp.json()["area_id"]


def test_get_dossier_returns_markdown_after_report_completes() -> None:
    """TestClient runs BackgroundTasks synchronously, so report is complete on return."""
    app, client, area_id = _make_app_client_with_area()

    post = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert post.status_code == 202
    report_run_id = post.json()["report_run_id"]

    # Dossier requires APPROVED status — approve via service before fetching.
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(UUID(report_run_id), reviewer_id="test-reviewer")

    resp = client.get(f"/report-runs/{report_run_id}/dossier")

    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    assert "## 1. Executive Summary" in resp.text


def test_get_dossier_returns_202_when_job_pending() -> None:
    app, client, area_id = _make_app_client_with_area()
    services = cast(ApiServices, app.state.services)

    # Create a job but leave it in QUEUED state (do not run background task)
    job = services.async_report_jobs.create(
        area_id=UUID(area_id),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )

    resp = client.get(f"/report-runs/{job.report_run_id}/dossier")

    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "pending"
    assert body["report_run_id"] == str(job.report_run_id)


def test_get_dossier_returns_404_for_unknown_id() -> None:
    _app, client, _area_id = _make_app_client_with_area()

    resp = client.get(f"/report-runs/{uuid4()}/dossier")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "report run not found"


def test_get_dossier_returns_409_for_needs_review_report() -> None:
    """Unapproved (NEEDS_REVIEW) reports must not be served as final dossiers."""
    _app, client, area_id = _make_app_client_with_area()

    post = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert post.status_code == 202
    report_run_id = post.json()["report_run_id"]

    resp = client.get(f"/report-runs/{report_run_id}/dossier")

    assert resp.status_code == 409
    assert "not approved" in resp.json()["detail"]


def test_get_dossier_returns_markdown_after_approval() -> None:
    """Only APPROVED reports should yield a final Markdown dossier."""
    app, client, area_id = _make_app_client_with_area()

    post = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert post.status_code == 202
    report_run_id = post.json()["report_run_id"]

    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(UUID(report_run_id), reviewer_id="test-reviewer")

    resp = client.get(f"/report-runs/{report_run_id}/dossier")

    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    assert "## 1. Executive Summary" in resp.text
