from __future__ import annotations

from typing import cast
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.core.config import Settings
from app.domain.enums import IntentCode, JobStatus
from app.main import create_app

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
    services.async_report_jobs.mark_failed(
        failed_report.report_run_id,
        error_msg="fixture failure",
    )
    live_job = services.live_connector_jobs.enqueue_fema_nfhl(
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
        "total": 2,
        "queued": 1,
        "running": 0,
        "succeeded": 0,
        "failed": 1,
        "cancelled": 0,
        "needs_review": 0,
        "oldest_queued_age_seconds": body["report_jobs"]["oldest_queued_age_seconds"],
    }
    assert body["report_jobs"]["oldest_queued_age_seconds"] >= 0
    assert body["live_connector_jobs"]["job_type"] == "live_connector_run"
    assert body["live_connector_jobs"]["total"] == 1
    assert body["live_connector_jobs"]["queued"] == 1
    assert body["live_connector_jobs"]["failed"] == 0
    assert body["live_connector_jobs"]["oldest_queued_age_seconds"] >= 0

    assert services.async_report_jobs.get(queued_report.report_run_id) is queued_report
    stored_live_job = services.live_connector_jobs.get(live_job.job_id)
    assert stored_live_job is not None
    assert stored_live_job.status == JobStatus.QUEUED
