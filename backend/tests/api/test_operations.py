from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.connectors.live_jobs import InMemoryLiveConnectorJobStore
from app.core.config import Settings
from app.domain.enums import IntentCode, JobStatus
from app.domain.job_health import STALE_RUNNING_THRESHOLD_SECONDS
from app.main import create_app
from app.operations.recovery_preview import RECOVERY_PREVIEW_REDACTED_ERROR_MESSAGE

VALID_REVIEWER_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}


def test_queue_health_requires_reviewer_auth() -> None:
    client = TestClient(create_app())

    response = client.get("/operations/queue-health")

    assert response.status_code == 401


def test_queue_health_rejects_reviewer_without_operations_read_scope() -> None:
    client = TestClient(
        create_app(
            Settings(
                REVIEWER_ACCOUNTS="runner:runner-token",
                REVIEWER_ACCOUNT_SCOPES="runner:connector:run",
            )
        )
    )

    response = client.get(
        "/operations/queue-health",
        headers={
            "X-Reviewer-Id": "runner",
            "X-Reviewer-Token": "runner-token",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "reviewer scope is required: operations:read"


def test_recovery_preview_requires_reviewer_auth() -> None:
    client = TestClient(create_app())

    response = client.get("/operations/recovery-preview")

    assert response.status_code == 401


def test_recovery_preview_rejects_reviewer_without_operations_read_scope() -> None:
    client = TestClient(
        create_app(
            Settings(
                REVIEWER_ACCOUNTS="runner:runner-token",
                REVIEWER_ACCOUNT_SCOPES="runner:connector:run",
            )
        )
    )

    response = client.get(
        "/operations/recovery-preview",
        headers={
            "X-Reviewer-Id": "runner",
            "X-Reviewer-Token": "runner-token",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "reviewer scope is required: operations:read"


def test_queue_health_reports_both_job_queues_without_mutating_jobs() -> None:
    app = create_app()
    client = TestClient(app)
    services = cast(ApiServices, app.state.services)
    area_id = uuid4()
    failed_report = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    queued_report = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    running_report = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    services.async_report_jobs.mark_failed(
        failed_report.report_run_id,
        error_msg="fixture failure",
    )
    services.async_report_jobs.mark_running(running_report.report_run_id)
    running_live_job = services.live_connector_jobs.enqueue_nwi(
        area_id=area_id,
        max_features=1,
    )
    leased_live_job = services.live_connector_jobs.lease_next(worker_id="ops-test-worker")
    assert leased_live_job is not None
    assert leased_live_job.job_id == running_live_job.job_id
    queued_live_job = services.live_connector_jobs.enqueue_fema_nfhl(
        area_id=area_id,
        max_features=1,
    )

    response = client.get(
        "/operations/queue-health",
        headers=VALID_REVIEWER_HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "operations_queue_health_v1"
    assert body["report_jobs"] == {
        "job_type": "report_run",
        "total": 3,
        "queued": 1,
        "running": 1,
        "succeeded": 0,
        "failed": 1,
        "cancelled": 0,
        "needs_review": 0,
        "oldest_queued_age_seconds": body["report_jobs"]["oldest_queued_age_seconds"],
        "oldest_running_age_seconds": body["report_jobs"]["oldest_running_age_seconds"],
        "oldest_running_job_id": str(running_report.report_run_id),
        "stale_running": 0,
        "stale_running_threshold_seconds": STALE_RUNNING_THRESHOLD_SECONDS,
    }
    assert body["report_jobs"]["oldest_queued_age_seconds"] >= 0
    assert body["report_jobs"]["oldest_running_age_seconds"] >= 0
    assert body["live_connector_jobs"]["job_type"] == "live_connector_run"
    assert body["live_connector_jobs"]["total"] == 2
    assert body["live_connector_jobs"]["queued"] == 1
    assert body["live_connector_jobs"]["running"] == 1
    assert body["live_connector_jobs"]["failed"] == 0
    assert body["live_connector_jobs"]["oldest_queued_age_seconds"] >= 0
    assert body["live_connector_jobs"]["oldest_running_age_seconds"] >= 0
    assert body["live_connector_jobs"]["oldest_running_job_id"] == str(
        running_live_job.job_id,
    )
    assert body["live_connector_jobs"]["stale_running"] == 0
    assert (
        body["live_connector_jobs"]["stale_running_threshold_seconds"]
        == STALE_RUNNING_THRESHOLD_SECONDS
    )

    assert services.async_report_jobs.get(queued_report.report_run_id) is queued_report
    stored_running_report = services.async_report_jobs.get(running_report.report_run_id)
    assert stored_running_report is not None
    assert stored_running_report.status == JobStatus.RUNNING
    stored_live_job = services.live_connector_jobs.get(queued_live_job.job_id)
    assert stored_live_job is not None
    assert stored_live_job.status == JobStatus.QUEUED
    stored_running_live_job = services.live_connector_jobs.get(running_live_job.job_id)
    assert stored_running_live_job is not None
    assert stored_running_live_job.status == JobStatus.RUNNING


def test_recovery_preview_reports_failed_and_stale_running_candidates_read_only() -> None:
    app = create_app()
    client = TestClient(app)
    services = cast(ApiServices, app.state.services)
    area_id = uuid4()
    stale_started_at = datetime.now(UTC) - timedelta(
        seconds=STALE_RUNNING_THRESHOLD_SECONDS + 30,
    )

    failed_report = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    stale_report = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    fresh_report = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    services.async_report_jobs.mark_failed(
        failed_report.report_run_id,
        error_msg="report failed",
    )
    services.async_report_jobs.mark_running(stale_report.report_run_id)
    services.async_report_jobs.mark_running(fresh_report.report_run_id)
    stale_report.started_at = stale_started_at

    failed_live_job = services.live_connector_jobs.enqueue_nwi(
        area_id=area_id,
        max_features=1,
    )
    leased_failed_live_job = services.live_connector_jobs.lease_next(
        worker_id="ops-preview-failed",
    )
    assert leased_failed_live_job is not None
    assert leased_failed_live_job.job_id == failed_live_job.job_id
    services.live_connector_jobs.mark_failed(
        failed_live_job.job_id,
        error_msg="connector failed",
    )

    stale_live_job = services.live_connector_jobs.enqueue_fema_nfhl(
        area_id=area_id,
        max_features=1,
    )
    leased_stale_live_job = services.live_connector_jobs.lease_next(
        worker_id="ops-preview-stale",
    )
    assert leased_stale_live_job is not None
    assert leased_stale_live_job.job_id == stale_live_job.job_id
    live_store = cast(InMemoryLiveConnectorJobStore, services.live_connector_jobs)
    with live_store._lock:
        current = live_store._jobs[stale_live_job.job_id]
        live_store._jobs[stale_live_job.job_id] = replace(
            current,
            started_at=stale_started_at,
        )

    response = client.get(
        "/operations/recovery-preview",
        headers=VALID_REVIEWER_HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "operations_recovery_preview_v1"
    assert body["stale_running_threshold_seconds"] == STALE_RUNNING_THRESHOLD_SECONDS
    assert body["candidate_limit_per_state"] == 25
    assert body["report_jobs"]["failed_count"] == 1
    assert body["report_jobs"]["stale_running_count"] == 1
    assert body["report_jobs"]["failed_candidates_truncated"] is False
    assert body["report_jobs"]["stale_running_candidates_truncated"] is False
    assert body["live_connector_jobs"]["failed_count"] == 1
    assert body["live_connector_jobs"]["stale_running_count"] == 1
    assert body["live_connector_jobs"]["failed_candidates_truncated"] is False
    assert body["live_connector_jobs"]["stale_running_candidates_truncated"] is False

    report_candidates = {
        candidate["job_id"]: candidate for candidate in body["report_jobs"]["candidates"]
    }
    assert set(report_candidates) == {
        str(failed_report.report_run_id),
        str(stale_report.report_run_id),
    }
    assert report_candidates[str(failed_report.report_run_id)]["reason_code"] == "failed"
    assert report_candidates[str(stale_report.report_run_id)]["reason_code"] == "stale_running"
    assert (
        report_candidates[str(failed_report.report_run_id)]["recommended_action"] == "retry_report"
    )
    assert (
        report_candidates[str(stale_report.report_run_id)]["recommended_action"]
        == "inspect_report_worker"
    )
    assert report_candidates[str(failed_report.report_run_id)]["detail_ui_path"] == (
        f"/ui/report-runs/{failed_report.report_run_id}"
    )

    connector_candidates = {
        candidate["job_id"]: candidate for candidate in body["live_connector_jobs"]["candidates"]
    }
    assert set(connector_candidates) == {
        str(failed_live_job.job_id),
        str(stale_live_job.job_id),
    }
    assert connector_candidates[str(failed_live_job.job_id)]["reason_code"] == "failed"
    assert connector_candidates[str(stale_live_job.job_id)]["reason_code"] == "stale_running"
    assert (
        connector_candidates[str(failed_live_job.job_id)]["recommended_action"]
        == "inspect_live_connector_failure"
    )
    assert (
        connector_candidates[str(stale_live_job.job_id)]["recommended_action"]
        == "inspect_live_connector_worker"
    )
    assert connector_candidates[str(failed_live_job.job_id)]["detail_api_path"] == (
        f"/connector-runs/live-jobs/{failed_live_job.job_id}"
    )

    stored_failed_report = services.async_report_jobs.get(failed_report.report_run_id)
    stored_stale_report = services.async_report_jobs.get(stale_report.report_run_id)
    stored_failed_live_job = services.live_connector_jobs.get(failed_live_job.job_id)
    stored_stale_live_job = services.live_connector_jobs.get(stale_live_job.job_id)
    assert stored_failed_report is not None
    assert stored_failed_report.status == JobStatus.FAILED
    assert stored_stale_report is not None
    assert stored_stale_report.status == JobStatus.RUNNING
    assert stored_failed_live_job is not None
    assert stored_failed_live_job.status == JobStatus.FAILED
    assert stored_stale_live_job is not None
    assert stored_stale_live_job.status == JobStatus.RUNNING


def test_recovery_preview_reports_candidate_truncation_metadata() -> None:
    app = create_app()
    client = TestClient(app)
    services = cast(ApiServices, app.state.services)
    area_id = uuid4()

    for index in range(26):
        report = services.async_report_jobs.create(
            area_id=area_id,
            intent_code=IntentCode.RURAL_LAND_PURCHASE,
        )
        services.async_report_jobs.mark_failed(
            report.report_run_id,
            error_msg=f"failure {index}",
        )

    response = client.get(
        "/operations/recovery-preview",
        headers=VALID_REVIEWER_HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["candidate_limit_per_state"] == 25
    assert body["report_jobs"]["failed_count"] == 26
    assert body["report_jobs"]["failed_candidates_truncated"] is True
    assert body["report_jobs"]["stale_running_candidates_truncated"] is False
    assert len(body["report_jobs"]["candidates"]) == 25


def test_recovery_preview_redacts_sensitive_error_details_without_mutating_jobs() -> None:
    app = create_app()
    client = TestClient(app)
    services = cast(ApiServices, app.state.services)
    area_id = uuid4()
    raw_report_error = (
        'Traceback (most recent call last):\n'
        '  File "C:\\Users\\benny\\repo\\worker.py", line 1, in <module>\n'
        "RuntimeError: API_KEY=super-secret-token"
    )
    raw_connector_error = (
        '{"Authorization":"Bearer secret-token","raw_payload":{"path":"/app/source.json"}}'
    )

    failed_report = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    services.async_report_jobs.mark_failed(
        failed_report.report_run_id,
        error_msg=raw_report_error,
    )

    failed_live_job = services.live_connector_jobs.enqueue_nwi(
        area_id=area_id,
        max_features=1,
    )
    leased_failed_live_job = services.live_connector_jobs.lease_next(
        worker_id="ops-preview-sensitive",
    )
    assert leased_failed_live_job is not None
    services.live_connector_jobs.mark_failed(
        failed_live_job.job_id,
        error_msg=raw_connector_error,
    )

    response = client.get(
        "/operations/recovery-preview",
        headers=VALID_REVIEWER_HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    report_candidate = next(
        candidate
        for candidate in body["report_jobs"]["candidates"]
        if candidate["job_id"] == str(failed_report.report_run_id)
    )
    connector_candidate = next(
        candidate
        for candidate in body["live_connector_jobs"]["candidates"]
        if candidate["job_id"] == str(failed_live_job.job_id)
    )
    assert report_candidate["error_message"] == RECOVERY_PREVIEW_REDACTED_ERROR_MESSAGE
    assert connector_candidate["error_message"] == RECOVERY_PREVIEW_REDACTED_ERROR_MESSAGE
    serialized = response.text
    for leaked in (
        "Traceback",
        "C:\\Users",
        "API_KEY",
        "super-secret-token",
        "Authorization",
        "Bearer",
        "raw_payload",
        "/app/source.json",
    ):
        assert leaked not in serialized

    stored_report = services.async_report_jobs.get(failed_report.report_run_id)
    stored_live_job = services.live_connector_jobs.get(failed_live_job.job_id)
    assert stored_report is not None
    assert stored_report.error_msg == raw_report_error
    assert stored_live_job is not None
    assert stored_live_job.last_error == raw_connector_error
