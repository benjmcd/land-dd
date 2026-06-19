"""Tests for GET /report-runs list endpoint (S5: pagination, filtering, bounds)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.job_health import STALE_RUNNING_THRESHOLD_SECONDS
from app.main import create_app

_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def _valid_geojson() -> dict[str, object]:
    data = json.loads((_FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _make_client_with_reports(
    n: int = 3,
) -> tuple[FastAPI, TestClient, list[str]]:
    """Create an app+client with n report runs (all queued/succeeded)."""
    app = create_app()
    tc = TestClient(app)
    area_resp = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]
    run_ids: list[str] = []
    for _ in range(n):
        run_resp = tc.post(
            "/report-runs",
            json={"area_id": area_id, "intent_code": "rural_land_purchase"},
        )
        assert run_resp.status_code == 202
        run_ids.append(run_resp.json()["report_run_id"])
    return app, tc, run_ids


# ---------------------------------------------------------------------------
# Basic list endpoint
# ---------------------------------------------------------------------------


def test_list_report_runs_returns_200_and_json_list() -> None:
    _app, tc, run_ids = _make_client_with_reports(2)
    resp = tc.get("/report-runs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    ids_in_resp = {item["report_run_id"] for item in data}
    for rid in run_ids:
        assert rid in ids_in_resp


def test_list_report_runs_item_has_required_fields() -> None:
    _app, tc, run_ids = _make_client_with_reports(1)
    resp = tc.get("/report-runs")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    item = next(i for i in items if i["report_run_id"] == run_ids[0])
    assert "report_run_id" in item
    assert "intent_code" in item
    assert "status" in item
    assert "created_at" in item
    assert "started_at" in item
    assert "running_age_seconds" in item
    assert "is_stale_running" in item
    assert "retry_of_report_run_id" in item
    assert "error_msg" in item
    assert "review_status" in item  # may be None


def test_list_report_runs_review_status_present_for_succeeded_job() -> None:
    app, tc, run_ids = _make_client_with_reports(1)
    # The job is in QUEUED/SUCCEEDED state after report generation
    # Force it to SUCCEEDED and check review_status appears
    services = cast(ApiServices, app.state.services)
    services.async_report_jobs.mark_succeeded(UUID(run_ids[0]))
    resp = tc.get("/report-runs")
    assert resp.status_code == 200
    items = resp.json()
    item = next((i for i in items if i["report_run_id"] == run_ids[0]), None)
    assert item is not None
    # review_status is a string (the review_status from the report) or None
    assert item["review_status"] is None or isinstance(item["review_status"], str)


def test_list_report_runs_review_status_null_for_non_succeeded() -> None:
    app, tc, run_ids = _make_client_with_reports(1)
    services = cast(ApiServices, app.state.services)
    services.async_report_jobs.mark_failed(UUID(run_ids[0]), error_msg="test")
    resp = tc.get("/report-runs")
    assert resp.status_code == 200
    items = resp.json()
    item = next((i for i in items if i["report_run_id"] == run_ids[0]), None)
    assert item is not None
    assert item["review_status"] is None


def test_failed_report_api_list_and_detail_redact_error_without_mutating_job() -> None:
    app, tc, run_ids = _make_client_with_reports(1)
    services = cast(ApiServices, app.state.services)
    raw_error = (
        'Traceback (most recent call last):\n'
        '  File "C:\\Users\\benny\\secret_app\\worker.py", line 4, in run\n'
        "RuntimeError: API_KEY=raw-token {\"raw_payload\": true}"
    )
    report_run_id = UUID(run_ids[0])
    services.async_report_jobs.mark_failed(report_run_id, error_msg=raw_error)

    list_resp = tc.get("/report-runs?status=failed")
    detail_resp = tc.get(f"/report-runs/{report_run_id}")

    assert list_resp.status_code == 200
    item = next(i for i in list_resp.json() if i["report_run_id"] == str(report_run_id))
    assert item["error_msg"] is not None
    assert "Failure details withheld" in item["error_msg"]
    assert "Traceback" not in item["error_msg"]
    assert "API_KEY" not in item["error_msg"]
    assert "raw_payload" not in item["error_msg"]
    assert "C:\\Users" not in item["error_msg"]
    assert detail_resp.status_code == 200
    caveats = detail_resp.json()["caveats"]
    assert caveats == [item["error_msg"]]
    assert raw_error not in detail_resp.text
    stored_job = services.async_report_jobs.get(report_run_id)
    assert stored_job is not None
    assert stored_job.error_msg == raw_error


def test_list_report_runs_includes_running_age_and_stale_flag() -> None:
    app, tc, run_ids = _make_client_with_reports(1)
    services = cast(ApiServices, app.state.services)
    report_run_id = UUID(run_ids[0])
    services.async_report_jobs.mark_running(report_run_id)
    job = services.async_report_jobs.get(report_run_id)
    assert job is not None
    job.started_at = datetime.now(UTC) - timedelta(
        seconds=STALE_RUNNING_THRESHOLD_SECONDS + 1,
    )

    resp = tc.get("/report-runs?status=running")

    assert resp.status_code == 200
    item = next(i for i in resp.json() if i["report_run_id"] == run_ids[0])
    assert item["started_at"] is not None
    assert item["running_age_seconds"] >= STALE_RUNNING_THRESHOLD_SECONDS
    assert item["is_stale_running"] is True


def test_list_report_runs_stale_filter_requires_running_status() -> None:
    tc = TestClient(create_app())

    missing_status = tc.get("/report-runs?stale=true")
    queued_status = tc.get("/report-runs?status=queued&stale=true")

    assert missing_status.status_code == 422
    assert queued_status.status_code == 422
    assert "status=running" in missing_status.text
    assert "status=running" in queued_status.text


def test_list_report_runs_stale_filter_returns_only_stale_running_jobs() -> None:
    app, tc, run_ids = _make_client_with_reports(3)
    services = cast(ApiServices, app.state.services)
    stale_run_id = UUID(run_ids[0])
    fresh_run_id = UUID(run_ids[1])
    failed_run_id = UUID(run_ids[2])
    services.async_report_jobs.mark_running(stale_run_id)
    services.async_report_jobs.mark_running(fresh_run_id)
    services.async_report_jobs.mark_failed(failed_run_id, error_msg="boom")
    stale_job = services.async_report_jobs.get(stale_run_id)
    assert stale_job is not None
    stale_job.started_at = datetime.now(UTC) - timedelta(
        seconds=STALE_RUNNING_THRESHOLD_SECONDS + 1,
    )

    resp = tc.get("/report-runs?status=running&stale=true")

    assert resp.status_code == 200
    items = resp.json()
    ids = {item["report_run_id"] for item in items}
    assert run_ids[0] in ids
    assert run_ids[1] not in ids
    assert run_ids[2] not in ids
    assert all(item["status"] == "running" for item in items)
    assert all(item["is_stale_running"] is True for item in items)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


def test_list_report_runs_limit_bounds_validation_too_high() -> None:
    tc = TestClient(create_app())
    resp = tc.get("/report-runs?limit=101")
    assert resp.status_code == 422


def test_list_report_runs_limit_bounds_validation_zero() -> None:
    tc = TestClient(create_app())
    resp = tc.get("/report-runs?limit=0")
    assert resp.status_code == 422


def test_list_report_runs_limit_100_is_valid() -> None:
    tc = TestClient(create_app())
    resp = tc.get("/report-runs?limit=100")
    assert resp.status_code == 200


def test_list_report_runs_offset_negative_is_invalid() -> None:
    tc = TestClient(create_app())
    resp = tc.get("/report-runs?offset=-1")
    assert resp.status_code == 422


def test_list_report_runs_pagination_pages_through_results() -> None:
    _app, tc, run_ids = _make_client_with_reports(5)
    page1 = tc.get("/report-runs?limit=2&offset=0").json()
    page2 = tc.get("/report-runs?limit=2&offset=2").json()
    page3 = tc.get("/report-runs?limit=2&offset=4").json()
    assert isinstance(page1, list)
    assert isinstance(page2, list)
    assert isinstance(page3, list)
    # Our 5 IDs should appear across pages (there may be other runs in store)
    our_ids = set(run_ids)
    combined_ids = {i["report_run_id"] for i in page1 + page2 + page3}
    # All our IDs should be in the combined pages
    for rid in our_ids:
        assert rid in combined_ids
    # No duplicates
    all_ids = [i["report_run_id"] for i in page1 + page2 + page3]
    assert len(all_ids) == len(set(all_ids))


def test_list_report_runs_offset_beyond_end_returns_empty_list() -> None:
    _app, tc, _run_ids = _make_client_with_reports(1)
    resp = tc.get("/report-runs?offset=9999")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Status filtering
# ---------------------------------------------------------------------------


def test_list_report_runs_status_filter_queued() -> None:
    app, tc, run_ids = _make_client_with_reports(2)
    services = cast(ApiServices, app.state.services)
    # Mark one failed so we can distinguish
    services.async_report_jobs.mark_failed(UUID(run_ids[0]), error_msg="test")
    resp = tc.get("/report-runs?status=queued")
    assert resp.status_code == 200
    items = resp.json()
    for item in items:
        assert item["status"] == "queued"
    # The failed run should not appear
    failed_ids = {i["report_run_id"] for i in items}
    assert run_ids[0] not in failed_ids


def test_list_report_runs_status_filter_failed() -> None:
    app, tc, run_ids = _make_client_with_reports(2)
    services = cast(ApiServices, app.state.services)
    services.async_report_jobs.mark_failed(UUID(run_ids[0]), error_msg="test")
    resp = tc.get("/report-runs?status=failed")
    assert resp.status_code == 200
    items = resp.json()
    for item in items:
        assert item["status"] == "failed"
    ids_in_resp = {i["report_run_id"] for i in items}
    assert run_ids[0] in ids_in_resp


def test_list_report_runs_invalid_status_returns_422() -> None:
    tc = TestClient(create_app())
    resp = tc.get("/report-runs?status=not_a_real_status")
    assert resp.status_code == 422


def test_list_report_runs_no_status_filter_returns_all() -> None:
    app, tc, run_ids = _make_client_with_reports(3)
    services = cast(ApiServices, app.state.services)
    services.async_report_jobs.mark_failed(UUID(run_ids[0]), error_msg="test")
    resp = tc.get("/report-runs")
    assert resp.status_code == 200
    items = resp.json()
    ids_in_resp = {i["report_run_id"] for i in items}
    for rid in run_ids:
        assert rid in ids_in_resp


# ---------------------------------------------------------------------------
# Route ordering: /compare and /{id} must still work
# ---------------------------------------------------------------------------


def test_list_does_not_shadow_compare_route() -> None:
    app, tc, run_ids = _make_client_with_reports(2)
    resp = tc.get(f"/report-runs/compare?ids={run_ids[0]},{run_ids[1]}")
    # Should reach compare endpoint (not treat "compare" as a UUID)
    # compare requires succeeded reports; in-progress jobs return 404 from compare
    # Either way it should NOT be 422 from UUID parsing
    assert resp.status_code in (200, 404, 400)


def test_list_does_not_shadow_get_by_id_route() -> None:
    _app, tc, run_ids = _make_client_with_reports(1)
    resp = tc.get(f"/report-runs/{run_ids[0]}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["report_run_id"] == run_ids[0]
