from __future__ import annotations

from dataclasses import replace
from typing import cast
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.connectors.live_jobs import InMemoryLiveConnectorJobStore
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


def test_ui_live_connector_job_detail_sanitizes_error_url_and_payload() -> None:
    app = create_app()
    tc = TestClient(app)
    services = cast(ApiServices, app.state.services)
    raw_error = (
        'Traceback (most recent call last):\n'
        '  File "C:\\Users\\benny\\connector\\worker.py", line 5, in run\n'
        "RuntimeError: password=raw-password {\"raw_payload\": true}"
    )
    job = services.live_connector_jobs.enqueue_nwi(
        area_id=uuid4(),
        max_features=1,
    )
    leased = services.live_connector_jobs.lease_next(worker_id="ui-live-worker")
    assert leased is not None
    failed = services.live_connector_jobs.mark_failed(job.job_id, error_msg=raw_error)
    store = services.live_connector_jobs
    assert isinstance(store, InMemoryLiveConnectorJobStore)
    with store._lock:
        store._jobs[job.job_id] = replace(
            failed,
            request_url="https://example.test/live?password=raw-password",
            payload={
                **failed.payload,
                "password": "raw-password",
                "local_path": r"C:\Users\benny\secret.json",
                "raw_payload": {"cookie": "session=raw"},
            },
        )
    login = tc.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )
    assert login.status_code == 303

    response = tc.get(f"/ui/live-connector-jobs/{job.job_id}")

    assert response.status_code == 200
    assert "Failure details withheld" in response.text
    assert "Traceback" not in response.text
    assert "raw-password" not in response.text
    assert "raw_payload" not in response.text
    assert "C:\\Users" not in response.text
    assert "https://example.test/live" in response.text
    assert "?password=" not in response.text
    assert "&quot;source_registry_id&quot;: &quot;DS-004&quot;" in response.text
    assert "&quot;password&quot;" not in response.text
    stored_job = services.live_connector_jobs.get(job.job_id)
    assert stored_job is not None
    assert stored_job.last_error == raw_error
    assert stored_job.payload["password"] == "raw-password"
