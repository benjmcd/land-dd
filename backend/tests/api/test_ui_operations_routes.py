from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.connectors.live_jobs import InMemoryLiveConnectorJobStore
from app.core.config import Settings
from app.domain.enums import IntentCode, JobStatus
from app.domain.job_health import STALE_RUNNING_THRESHOLD_SECONDS
from app.main import create_app

_FIXTURE_REVIEWER_ID = "fixture-reviewer"
_FIXTURE_REVIEWER_TOKEN = "fixture-token-123"


def _client() -> TestClient:
    return TestClient(create_app())


def _seed_recovery_candidates(services: ApiServices) -> tuple[UUID, UUID]:
    area_id = uuid4()
    stale_started_at = datetime.now(UTC) - timedelta(
        seconds=STALE_RUNNING_THRESHOLD_SECONDS + 30,
    )
    report_job = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    services.async_report_jobs.mark_failed(
        report_job.report_run_id,
        error_msg="report failed",
    )

    live_job = services.live_connector_jobs.enqueue_nwi(
        area_id=area_id,
        max_features=1,
    )
    leased = services.live_connector_jobs.lease_next(worker_id="ui-preview-worker")
    assert leased is not None
    assert leased.job_id == live_job.job_id
    live_store = cast(InMemoryLiveConnectorJobStore, services.live_connector_jobs)
    with live_store._lock:
        current = live_store._jobs[live_job.job_id]
        live_store._jobs[live_job.job_id] = replace(
            current,
            started_at=stale_started_at,
        )
    return report_job.report_run_id, live_job.job_id


def test_ui_operations_get_returns_200_with_form() -> None:
    tc = _client()
    resp = tc.get("/ui/operations")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert 'name="viewport"' in resp.text
    assert "href='/ui/report-runs'" in resp.text
    assert "action='/ui/operations'" in resp.text
    assert "Operations Dashboard" in resp.text
    assert "Recovery Preview" in resp.text
    assert "reviewer_id" in resp.text
    assert "reviewer_token" in resp.text


def test_ui_operations_post_no_credentials_returns_401() -> None:
    tc = _client()
    resp = tc.post("/ui/operations", data={})
    assert resp.status_code == 401
    assert "text/html" in resp.headers["content-type"]
    assert 'name="viewport"' in resp.text
    assert "href='/ui/operations'" in resp.text
    assert "Authentication Error" in resp.text


def test_ui_operations_post_wrong_token_returns_403() -> None:
    tc = _client()
    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": "wrong-token",
        },
    )
    assert resp.status_code == 403
    assert "text/html" in resp.headers["content-type"]
    assert "Authentication Error" in resp.text


def test_ui_operations_post_valid_creds_without_operations_scope_returns_403() -> None:
    settings = Settings(
        REVIEWER_ACCOUNTS="ops-reviewer:ops-token",
        REVIEWER_ACCOUNT_SCOPES="ops-reviewer:report:approve",
    )
    tc = TestClient(create_app(settings))
    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": "ops-reviewer",
            "reviewer_token": "ops-token",
        },
    )
    assert resp.status_code == 403
    assert "text/html" in resp.headers["content-type"]
    assert "Authentication Error" in resp.text


def test_ui_operations_post_valid_creds_renders_counts() -> None:
    tc = _client()
    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert 'name="viewport"' in resp.text
    assert "href='/ui/report-runs'" in resp.text
    assert "Operations Dashboard" in resp.text
    assert "View Dashboard" not in resp.text
    # Should render both queue sections
    assert "Report Jobs" in resp.text
    assert "Live Connector Jobs" in resp.text
    assert "href='/ui/operations/recovery-preview'" in resp.text
    # Table headers present
    assert "Queued" in resp.text
    assert "Running" in resp.text
    assert "Failed" in resp.text
    assert "Oldest Running Age" in resp.text
    assert "Stale Running" in resp.text


def test_ui_operations_tables_have_responsive_scroll_wrapper() -> None:
    tc = _client()
    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )

    assert resp.status_code == 200
    assert resp.text.count("class='ops-table-wrap'") == 2
    assert "overflow-x: auto" in resp.text
    assert "min-width: 920px" in resp.text


def test_ui_operations_post_accepts_reviewer_session_without_form_credentials() -> None:
    tc = _client()
    reviewer_login = tc.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )
    assert reviewer_login.status_code == 303

    resp = tc.post("/ui/operations", data={})

    assert resp.status_code == 200
    assert "Operations Dashboard" in resp.text
    assert _FIXTURE_REVIEWER_ID in resp.text
    assert "Using reviewer session" in resp.text
    assert "reviewer_token" not in resp.text
    assert "View Dashboard" not in resp.text


def test_ui_operations_get_with_reviewer_session_renders_dashboard() -> None:
    tc = _client()
    reviewer_login = tc.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )
    assert reviewer_login.status_code == 303

    resp = tc.get("/ui/operations")

    assert resp.status_code == 200
    assert "Operations Dashboard" in resp.text
    assert "Report Jobs" in resp.text
    assert "Live Connector Jobs" in resp.text
    assert "Using reviewer session" in resp.text
    assert _FIXTURE_REVIEWER_ID in resp.text
    assert "reviewer_token" not in resp.text
    assert "View Dashboard" not in resp.text


def test_ui_operations_get_under_scoped_session_shows_credential_fallback() -> None:
    settings = Settings(
        REVIEWER_ACCOUNTS="ops-reviewer:ops-token",
        REVIEWER_ACCOUNT_SCOPES="ops-reviewer:report:approve",
    )
    tc = TestClient(create_app(settings))
    reviewer_login = tc.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": "ops-reviewer",
            "reviewer_token": "ops-token",
        },
        follow_redirects=False,
    )
    assert reviewer_login.status_code == 303

    resp = tc.get("/ui/operations")

    assert resp.status_code == 200
    assert "Operations Dashboard" in resp.text
    assert "ops-reviewer" in resp.text
    assert "lacks <code>operations:read</code>" in resp.text
    assert "reviewer_token" in resp.text
    assert "View Dashboard" in resp.text
    assert "Report Jobs" not in resp.text


def test_ui_operations_post_valid_creds_renders_drilldown_links() -> None:
    tc = _client()
    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )

    assert resp.status_code == 200
    assert "<td><a href='/ui/report-runs'>0</a></td>" in resp.text
    assert "href='/ui/report-runs?status=queued'" in resp.text
    assert "href='/ui/report-runs?status=failed'" in resp.text
    assert "href='/ui/report-runs?status=needs_review'" in resp.text
    assert "<td><a href='/ui/live-connector-jobs'>0</a></td>" in resp.text
    assert "href='/ui/live-connector-jobs?status=queued'" in resp.text
    assert "href='/ui/live-connector-jobs?status=failed'" in resp.text
    assert "href='/ui/live-connector-jobs?status=needs_review'" in resp.text
    assert "href='/ui/live-connector-jobs?status=running&amp;stale=true'" in resp.text


def test_ui_operations_recovery_preview_get_returns_200_with_form() -> None:
    tc = _client()

    resp = tc.get("/ui/operations/recovery-preview")

    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Recovery Preview" in resp.text
    assert "action='/ui/operations/recovery-preview'" in resp.text
    assert "View Recovery Preview" in resp.text
    assert "reviewer_id" in resp.text
    assert "reviewer_token" in resp.text


def test_ui_operations_recovery_preview_with_session_renders_candidates() -> None:
    app = create_app()
    tc = TestClient(app)
    services = cast(ApiServices, app.state.services)
    report_run_id, live_job_id = _seed_recovery_candidates(services)
    reviewer_login = tc.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )
    assert reviewer_login.status_code == 303

    resp = tc.get("/ui/operations/recovery-preview")

    assert resp.status_code == 200
    assert "Recovery Preview" in resp.text
    assert "Report Jobs" in resp.text
    assert "Live Connector Jobs" in resp.text
    assert "Showing up to 25 failed and 25 stale-running candidates per queue." in resp.text
    assert f"href='/ui/report-runs/{report_run_id}'" in resp.text
    assert f"href='/ui/live-connector-jobs/{live_job_id}'" in resp.text
    assert "failed" in resp.text
    assert "stale_running" in resp.text
    assert "Report job failed" in resp.text
    assert "Live connector job is still running" in resp.text

    stored_report = services.async_report_jobs.get(report_run_id)
    assert stored_report is not None
    assert stored_report.status == JobStatus.FAILED
    stored_live_job = services.live_connector_jobs.get(live_job_id)
    assert stored_live_job is not None
    assert stored_live_job.status == JobStatus.RUNNING


def test_ui_operations_links_oldest_running_jobs_to_detail_pages() -> None:
    app = create_app()
    tc = TestClient(app)
    services = cast(ApiServices, app.state.services)
    area_id = uuid4()
    report_job = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    services.async_report_jobs.mark_running(report_job.report_run_id)
    live_job = services.live_connector_jobs.enqueue_nwi(area_id=area_id, max_features=1)
    leased = services.live_connector_jobs.lease_next(worker_id="ui-ops-worker")
    assert leased is not None
    assert leased.job_id == live_job.job_id

    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )

    assert resp.status_code == 200
    assert f"href='/ui/report-runs/{report_job.report_run_id}'" in resp.text
    assert f"href='/ui/live-connector-jobs/{live_job.job_id}'" in resp.text


def test_ui_operations_post_shows_authenticated_reviewer() -> None:
    tc = _client()
    resp = tc.post(
        "/ui/operations",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    assert resp.status_code == 200
    assert _FIXTURE_REVIEWER_ID in resp.text


def test_ui_operations_post_unconfigured_accounts_returns_503() -> None:
    from typing import cast
    from unittest.mock import patch

    from fastapi import HTTPException, status

    from app.api.dependencies import ApiServices

    app = create_app()
    tc = TestClient(app)
    services = cast(ApiServices, app.state.services)

    def _unconfigured(**kwargs: object) -> None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="connector reviewer auth is not configured",
        )

    with patch.object(services, "reviewer_auth", side_effect=_unconfigured):
        resp = tc.post(
            "/ui/operations",
            data={
                "reviewer_id": "any",
                "reviewer_token": "any",
            },
        )
    assert resp.status_code == 503
    assert "text/html" in resp.headers["content-type"]
    assert "Authentication Error" in resp.text
