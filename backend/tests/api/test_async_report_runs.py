from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.core.config import Settings
from app.domain.enums import IntentCode
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"
VALID_REVIEWER_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}


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


def _make_app_client_with_area(
    settings: Settings | None = None,
) -> tuple[FastAPI, TestClient, str]:
    app = create_app(settings)
    client = TestClient(app)
    resp = client.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert resp.status_code == 201
    return app, client, resp.json()["area_id"]


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


def test_retry_failed_report_run_creates_new_job_with_lineage() -> None:
    app, client, area_id = _make_app_client_with_area()
    services = cast(ApiServices, app.state.services)
    failed_job = services.async_report_jobs.create(
        area_id=UUID(area_id),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    services.async_report_jobs.mark_failed(
        failed_job.report_run_id,
        error_msg="fixture report failure",
    )

    retry = client.post(
        f"/report-runs/{failed_job.report_run_id}/retry",
        headers=VALID_REVIEWER_HEADERS,
    )

    assert retry.status_code == 202
    body = retry.json()
    assert body["status"] == "queued"
    assert body["report_run_id"] != str(failed_job.report_run_id)
    assert body["retry_of_report_run_id"] == str(failed_job.report_run_id)

    original = client.get(f"/report-runs/{failed_job.report_run_id}")
    assert original.status_code == 200
    assert original.json()["status"] == "failed"
    retried = services.async_report_jobs.get(UUID(body["report_run_id"]))
    assert retried is not None
    assert retried.retry_of_report_run_id == failed_job.report_run_id


def test_retry_report_run_requires_reviewer_auth() -> None:
    _app, client, area_id = _make_app_client_with_area()
    services = cast(ApiServices, _app.state.services)
    failed_job = services.async_report_jobs.create(
        area_id=UUID(area_id),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    services.async_report_jobs.mark_failed(failed_job.report_run_id, error_msg="boom")

    response = client.post(f"/report-runs/{failed_job.report_run_id}/retry")

    assert response.status_code == 401


def test_retry_report_run_rejects_reviewer_without_retry_scope() -> None:
    app, client, area_id = _make_app_client_with_area(
        settings=Settings(
            REVIEWER_ACCOUNTS="runner:runner-token",
            REVIEWER_ACCOUNT_SCOPES="runner:connector:run",
        )
    )
    services = cast(ApiServices, app.state.services)
    failed_job = services.async_report_jobs.create(
        area_id=UUID(area_id),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    services.async_report_jobs.mark_failed(failed_job.report_run_id, error_msg="boom")

    response = client.post(
        f"/report-runs/{failed_job.report_run_id}/retry",
        headers={
            "X-Reviewer-Id": "runner",
            "X-Reviewer-Token": "runner-token",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "reviewer scope is required: report:retry"


def test_retry_report_run_rejects_non_failed_job() -> None:
    _app, client, area_id = _make_app_client_with_area()
    services = cast(ApiServices, _app.state.services)
    queued_job = services.async_report_jobs.create(
        area_id=UUID(area_id),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )

    response = client.post(
        f"/report-runs/{queued_job.report_run_id}/retry",
        headers=VALID_REVIEWER_HEADERS,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "report run retry requires a failed report job"
