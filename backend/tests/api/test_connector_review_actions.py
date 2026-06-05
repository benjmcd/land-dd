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
from app.domain.enums import JobStatus

_VALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}
_INVALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "wrong-token",
}


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


def _make_app(ingest_run_id: UUID | None = None, job_status: JobStatus | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(connectors_router)
    base_services = create_api_services()
    if ingest_run_id is not None and job_status is not None:
        repo = cast(InMemoryConnectorReviewQueueRepository, base_services.connector_review_queue)
        item = _make_queue_item(ingest_run_id, job_status)
        repo._store[ingest_run_id] = item
    app.dependency_overrides[get_services] = lambda: base_services
    return app


# ---------------------------------------------------------------------------
# request_fixture_fix
# ---------------------------------------------------------------------------


def test_request_fixture_fix_returns_200() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.NEEDS_REVIEW))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/request_fixture_fix",
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "request_fixture_fix"
    assert body["ingest_run_id"] == str(ingest_run_id)
    assert body["reviewer_id"] == "fixture-reviewer"
    assert body["queue_item_status"] == "needs_review"


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
    )

    assert response.status_code == 403


def test_request_fixture_fix_returns_404_for_unknown_run() -> None:
    client = TestClient(_make_app())

    response = client.post(
        f"/connector-runs/{uuid4()}/review-actions/request_fixture_fix",
        headers=_VALID_HEADERS,
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
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "requeue_after_fix"
    assert body["ingest_run_id"] == str(ingest_run_id)
    assert body["reviewer_id"] == "fixture-reviewer"
    assert body["new_status"] == "queued"


def test_requeue_after_fix_returns_409_for_non_failed_job() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.NEEDS_REVIEW))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/requeue_after_fix",
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "queue item cannot be requeued"


def test_requeue_after_fix_returns_404_for_unknown_run() -> None:
    client = TestClient(_make_app())

    response = client.post(
        f"/connector-runs/{uuid4()}/review-actions/requeue_after_fix",
        headers=_VALID_HEADERS,
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
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "cancel_review"
    assert body["ingest_run_id"] == str(ingest_run_id)
    assert body["reviewer_id"] == "fixture-reviewer"
    assert body["new_status"] == "cancelled"


def test_cancel_review_returns_409_for_already_cancelled() -> None:
    ingest_run_id = uuid4()
    app = _make_app(ingest_run_id, JobStatus.NEEDS_REVIEW)
    client = TestClient(app)

    # First cancel succeeds
    first = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/cancel_review",
        headers=_VALID_HEADERS,
    )
    assert first.status_code == 200

    # Second cancel on an already-cancelled item returns 409
    second = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/cancel_review",
        headers=_VALID_HEADERS,
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "queue item cannot be cancelled"


def test_cancel_review_returns_404_for_unknown_run() -> None:
    client = TestClient(_make_app())

    response = client.post(
        f"/connector-runs/{uuid4()}/review-actions/cancel_review",
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "connector review queue item not found"
