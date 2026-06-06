from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.connectors import router as connectors_router
from app.api.dependencies import create_api_services, get_services
from app.connectors.review_queue import (
    ConnectorReviewQueueItem,
    InMemoryConnectorReviewQueueRepository,
)
from app.core.config import Settings
from app.domain.enums import JobStatus

_VALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}
_INVALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "wrong-token",
}
_REASON_BODY = {"reason": "reviewed connector output and found a correction needed"}


def _make_queue_item(ingest_run_id: UUID, job_status: JobStatus) -> ConnectorReviewQueueItem:
    return ConnectorReviewQueueItem(
        job_id=ingest_run_id,
        ingest_run_id=ingest_run_id,
        job_type="connector_review_status",
        status=job_status,
        priority=10,
        idempotency_key=f"connector_review_status:{ingest_run_id}",
        payload={"ingest_run_id": str(ingest_run_id)},
        created_at=datetime.now(UTC),
        max_attempts=3,
    )


def _make_app(
    ingest_run_id: UUID | None = None,
    job_status: JobStatus | None = None,
    *,
    reviewer_accounts: str | None = None,
    reviewer_account_scopes: str | None = None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(connectors_router)
    settings = (
        Settings(
            REVIEWER_ACCOUNTS=reviewer_accounts,
            REVIEWER_ACCOUNT_SCOPES=reviewer_account_scopes,
        )
        if reviewer_accounts is not None and reviewer_account_scopes is not None
        else None
    )
    base_services = create_api_services(settings)
    if ingest_run_id is not None and job_status is not None:
        repo = cast(InMemoryConnectorReviewQueueRepository, base_services.connector_review_queue)
        item = _make_queue_item(ingest_run_id, job_status)
        repo._store[ingest_run_id] = item
    app.dependency_overrides[get_services] = lambda: base_services
    return app


# ---------------------------------------------------------------------------
# approve_for_connector_qa
# ---------------------------------------------------------------------------


def test_approve_for_connector_qa_marks_review_succeeded() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.NEEDS_REVIEW))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
        json={"reason": "spatial evidence is acceptable for connector QA"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "approve_for_connector_qa"
    assert body["ingest_run_id"] == str(ingest_run_id)
    assert body["reviewer_id"] == "fixture-reviewer"
    assert body["new_status"] == "succeeded"
    assert body["queue_item"]["status"] == "succeeded"
    assert body["queue_item"]["locked_by"] == "fixture-reviewer"
    assert body["queue_item"]["payload"]["review_decision"]["action"] == (
        "approve_for_connector_qa"
    )
    assert body["queue_item"]["payload"]["review_action_history"] == [
        {
            "action": "approve_for_connector_qa",
            "reviewer_id": "fixture-reviewer",
            "reason": "spatial evidence is acceptable for connector QA",
            "decided_at": body["queue_item"]["payload"]["review_decision"][
                "decided_at"
            ],
        }
    ]


def test_approve_for_connector_qa_returns_409_for_final_job() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.SUCCEEDED))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "queue item cannot be approved"


# ---------------------------------------------------------------------------
# request_fixture_fix
# ---------------------------------------------------------------------------


def test_request_fixture_fix_marks_review_failed_with_reason() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.NEEDS_REVIEW))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/request_fixture_fix",
        headers=_VALID_HEADERS,
        json=_REASON_BODY,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "request_fixture_fix"
    assert body["ingest_run_id"] == str(ingest_run_id)
    assert body["reviewer_id"] == "fixture-reviewer"
    assert body["new_status"] == "failed"
    assert body["reason"] == _REASON_BODY["reason"]
    assert body["queue_item"]["status"] == "failed"
    assert body["queue_item"]["last_error"] == _REASON_BODY["reason"]
    assert body["queue_item"]["payload"]["review_decision"]["reviewer_id"] == (
        "fixture-reviewer"
    )
    assert body["queue_item"]["payload"]["review_action_history"][0]["action"] == (
        "request_fixture_fix"
    )
    assert body["queue_item"]["payload"]["review_action_history"][0]["reviewer_id"] == (
        "fixture-reviewer"
    )


def test_request_fixture_fix_uses_settings_backed_reviewer_accounts() -> None:
    ingest_run_id = uuid4()
    client = TestClient(
        _make_app(
            ingest_run_id,
            JobStatus.NEEDS_REVIEW,
            reviewer_accounts="ops-reviewer:ops-token",
            reviewer_account_scopes="ops-reviewer:connector:review",
        )
    )

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/request_fixture_fix",
        headers={
            "X-Reviewer-Id": "ops-reviewer",
            "X-Reviewer-Token": "ops-token",
        },
        json=_REASON_BODY,
    )

    assert response.status_code == 200
    assert response.json()["reviewer_id"] == "ops-reviewer"


def test_request_fixture_fix_rejects_reviewer_without_review_scope() -> None:
    ingest_run_id = uuid4()
    client = TestClient(
        _make_app(
            ingest_run_id,
            JobStatus.NEEDS_REVIEW,
            reviewer_accounts="runner:runner-token",
            reviewer_account_scopes="runner:connector:run",
        )
    )

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/request_fixture_fix",
        headers={
            "X-Reviewer-Id": "runner",
            "X-Reviewer-Token": "runner-token",
        },
        json=_REASON_BODY,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "reviewer scope is required: connector:review"


def test_request_fixture_fix_requires_auth() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.NEEDS_REVIEW))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/request_fixture_fix",
    )

    assert response.status_code == 401


def test_request_fixture_fix_rejects_invalid_auth() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.NEEDS_REVIEW))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/request_fixture_fix",
        headers=_INVALID_HEADERS,
        json=_REASON_BODY,
    )

    assert response.status_code == 403


def test_request_fixture_fix_requires_reason() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.NEEDS_REVIEW))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/request_fixture_fix",
        headers=_VALID_HEADERS,
        json={"reason": " "},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "reason is required"


def test_required_review_actions_require_request_body_in_openapi() -> None:
    schema = _make_app().openapi()
    paths = schema["paths"]
    required_paths = [
        "/connector-runs/{ingest_run_id}/review-actions/request_fixture_fix",
        "/connector-runs/{ingest_run_id}/review-actions/requeue_after_fix",
        "/connector-runs/{ingest_run_id}/review-actions/cancel_review",
    ]

    for path in required_paths:
        request_body = paths[path]["post"]["requestBody"]
        assert request_body["required"] is True
        schema_ref = request_body["content"]["application/json"]["schema"]
        assert schema_ref == {
            "$ref": "#/components/schemas/RequiredConnectorReviewActionRequest"
        }


def test_request_fixture_fix_returns_404_for_unknown_run() -> None:
    client = TestClient(_make_app())

    response = client.post(
        f"/connector-runs/{uuid4()}/review-actions/request_fixture_fix",
        headers=_VALID_HEADERS,
        json=_REASON_BODY,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "connector review queue item not found"


# ---------------------------------------------------------------------------
# requeue_after_fix
# ---------------------------------------------------------------------------


def test_requeue_after_fix_returns_200() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.FAILED))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/requeue_after_fix",
        headers=_VALID_HEADERS,
        json={"reason": "fix was applied and review should run again"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "requeue_after_fix"
    assert body["ingest_run_id"] == str(ingest_run_id)
    assert body["reviewer_id"] == "fixture-reviewer"
    assert body["new_status"] == "queued"
    assert body["queue_item"]["last_error"] == "fix was applied and review should run again"
    assert body["queue_item"]["payload"]["review_action_history"][0]["action"] == (
        "requeue_after_fix"
    )
    assert body["queue_item"]["payload"]["review_action_history"][0]["reviewer_id"] == (
        "fixture-reviewer"
    )


def test_requeue_after_fix_returns_409_for_non_failed_job() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.NEEDS_REVIEW))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/requeue_after_fix",
        headers=_VALID_HEADERS,
        json={"reason": "no failed review exists"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "queue item cannot be requeued"


def test_requeue_after_fix_returns_404_for_unknown_run() -> None:
    client = TestClient(_make_app())

    response = client.post(
        f"/connector-runs/{uuid4()}/review-actions/requeue_after_fix",
        headers=_VALID_HEADERS,
        json={"reason": "unknown review"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "connector review queue item not found"


# ---------------------------------------------------------------------------
# cancel_review
# ---------------------------------------------------------------------------


def test_cancel_review_returns_200() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.NEEDS_REVIEW))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/cancel_review",
        headers=_VALID_HEADERS,
        json={"reason": "review superseded by a newer connector run"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "cancel_review"
    assert body["ingest_run_id"] == str(ingest_run_id)
    assert body["reviewer_id"] == "fixture-reviewer"
    assert body["new_status"] == "cancelled"
    assert body["reason"] == "review superseded by a newer connector run"
    assert body["queue_item"]["payload"]["review_action_history"][0]["action"] == (
        "cancel_review"
    )
    assert body["queue_item"]["payload"]["review_action_history"][0]["reviewer_id"] == (
        "fixture-reviewer"
    )


def test_cancel_review_returns_409_for_already_cancelled() -> None:
    ingest_run_id = uuid4()
    app = _make_app(ingest_run_id, JobStatus.NEEDS_REVIEW)
    client = TestClient(app)

    # First cancel succeeds
    first = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/cancel_review",
        headers=_VALID_HEADERS,
        json={"reason": "first cancellation"},
    )
    assert first.status_code == 200

    # Second cancel on an already-cancelled item returns 409
    second = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/cancel_review",
        headers=_VALID_HEADERS,
        json={"reason": "second cancellation"},
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "queue item cannot be cancelled"


def test_cancel_review_returns_404_for_unknown_run() -> None:
    client = TestClient(_make_app())

    response = client.post(
        f"/connector-runs/{uuid4()}/review-actions/cancel_review",
        headers=_VALID_HEADERS,
        json={"reason": "unknown review"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "connector review queue item not found"
