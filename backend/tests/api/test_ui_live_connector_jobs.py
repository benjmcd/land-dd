from __future__ import annotations

from typing import cast
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.main import create_app

_FIXTURE_REVIEWER_ID = "fixture-reviewer"
_FIXTURE_REVIEWER_TOKEN = "fixture-token-123"


def test_ui_live_connector_jobs_requires_operations_session() -> None:
    tc = TestClient(create_app())

    resp = tc.get("/ui/live-connector-jobs")

    assert resp.status_code == 401
    assert "Authentication Required" in resp.text
    assert "href='/ui/operations'" in resp.text


def test_ui_live_connector_jobs_lists_and_opens_running_job() -> None:
    app = create_app()
    tc = TestClient(app)
    services = cast(ApiServices, app.state.services)
    job = services.live_connector_jobs.enqueue_nwi(
        area_id=uuid4(),
        max_features=1,
    )
    leased = services.live_connector_jobs.lease_next(worker_id="ui-live-worker")
    assert leased is not None
    assert leased.job_id == job.job_id
    login = tc.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )
    assert login.status_code == 303

    list_resp = tc.get("/ui/live-connector-jobs?status=running")
    detail_resp = tc.get(f"/ui/live-connector-jobs/{job.job_id}")

    assert list_resp.status_code == 200
    assert "Live Connector Jobs" in list_resp.text
    assert str(job.job_id)[:8] in list_resp.text
    assert "nwi_live" in list_resp.text
    assert "Running Age" in list_resp.text
    assert detail_resp.status_code == 200
    assert str(job.job_id) in detail_resp.text
    assert "ui-live-worker" in detail_resp.text
    assert "&quot;source_registry_id&quot;: &quot;DS-004&quot;" in detail_resp.text
