from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.connectors import router as connectors_router
from app.api.dependencies import ApiServices, create_api_services, get_services
from app.connectors.review_queue import (
    ConnectorReviewQueueItem,
    InMemoryConnectorReviewQueueRepository,
)
from app.core.config import Settings
from app.domain.area_contracts import AreaContract
from app.domain.enums import JobStatus

_WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
_OTHER_WORKSPACE_ID = UUID("33333333-3333-4333-8333-333333333333")
_OTHER_USER_ID = UUID("44444444-4444-4444-8444-444444444444")
_REVIEWER_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}
_VALID_HEADERS = {
    **_REVIEWER_HEADERS,
    "X-Workspace-Id": str(_WORKSPACE_ID),
    "X-User-Id": str(_USER_ID),
}
_OTHER_WORKSPACE_HEADERS = {
    **_REVIEWER_HEADERS,
    "X-Workspace-Id": str(_OTHER_WORKSPACE_ID),
    "X-User-Id": str(_OTHER_USER_ID),
}
_INVALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "wrong-token",
    "X-Workspace-Id": str(_WORKSPACE_ID),
    "X-User-Id": str(_USER_ID),
}
_REASON_BODY = {"reason": "reviewed connector output and found a correction needed"}


def _make_queue_item(
    ingest_run_id: UUID,
    job_status: JobStatus,
    *,
    area_id: UUID | None = None,
    workspace_id: UUID | None = _WORKSPACE_ID,
    requested_by: UUID | None = _USER_ID,
    approved_for_report: bool = False,
) -> ConnectorReviewQueueItem:
    payload: dict[str, object] = {"ingest_run_id": str(ingest_run_id)}
    if area_id is not None:
        payload["area_id"] = str(area_id)
    if workspace_id is not None:
        payload["workspace_id"] = str(workspace_id)
    if requested_by is not None:
        payload["requested_by"] = str(requested_by)
    if approved_for_report:
        decided_at = datetime.now(UTC).isoformat()
        payload["review_decision"] = {
            "action": "approve_for_connector_qa",
            "reviewer_id": "fixture-reviewer",
            "reason": "approved for connector QA",
            "decided_at": decided_at,
        }
        payload["review_action_history"] = [payload["review_decision"]]
    return ConnectorReviewQueueItem(
        job_id=ingest_run_id,
        workspace_id=workspace_id,
        ingest_run_id=ingest_run_id,
        job_type="connector_review_status",
        status=job_status,
        priority=10,
        idempotency_key=f"connector_review_status:{ingest_run_id}",
        payload=payload,
        created_at=datetime.now(UTC),
        max_attempts=3,
    )


def _make_app(
    ingest_run_id: UUID | None = None,
    job_status: JobStatus | None = None,
    *,
    area_id: UUID | None = None,
    workspace_id: UUID | None = _WORKSPACE_ID,
    requested_by: UUID | None = _USER_ID,
    approved_for_report: bool = False,
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
    resolved_settings = settings or Settings()
    app.state.settings = resolved_settings
    app.state.services = base_services
    if ingest_run_id is not None and job_status is not None:
        repo = cast(InMemoryConnectorReviewQueueRepository, base_services.connector_review_queue)
        item = _make_queue_item(
            ingest_run_id,
            job_status,
            area_id=area_id,
            workspace_id=workspace_id,
            requested_by=requested_by,
            approved_for_report=approved_for_report,
        )
        repo._store[ingest_run_id] = item
    app.dependency_overrides[get_services] = lambda: base_services
    return app


def _services(app: FastAPI) -> ApiServices:
    return cast(ApiServices, app.state.services)


def _area_contract(
    area_id: UUID,
    *,
    workspace_id: UUID = _WORKSPACE_ID,
    created_by: UUID = _USER_ID,
) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        workspace_id=workspace_id,
        created_by=created_by,
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-79.0, 35.0],
                    [-79.0, 35.01],
                    [-78.99, 35.01],
                    [-78.99, 35.0],
                    [-79.0, 35.0],
                ]
            ],
        },
    )


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


def test_approve_for_connector_qa_requires_workspace_identity() -> None:
    ingest_run_id = uuid4()
    client = TestClient(_make_app(ingest_run_id, JobStatus.NEEDS_REVIEW))

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_REVIEWER_HEADERS,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "X-Workspace-Id header is required"


def test_approve_for_connector_qa_hides_other_workspace_and_does_not_mutate() -> None:
    ingest_run_id = uuid4()
    app = _make_app(
        ingest_run_id,
        JobStatus.NEEDS_REVIEW,
        workspace_id=_OTHER_WORKSPACE_ID,
        requested_by=_OTHER_USER_ID,
    )
    client = TestClient(app)

    response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
        json={"reason": "should not see another workspace"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "connector review queue item not found"
    item = _services(app).connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    assert item is not None
    assert item.status == JobStatus.NEEDS_REVIEW
    assert item.locked_by is None
    assert "review_decision" not in item.payload


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
            "X-Workspace-Id": str(_WORKSPACE_ID),
            "X-User-Id": str(_USER_ID),
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
            "X-Workspace-Id": str(_WORKSPACE_ID),
            "X-User-Id": str(_USER_ID),
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


# ---------------------------------------------------------------------------
# report-runs
# ---------------------------------------------------------------------------


def test_connector_report_run_requires_workspace_identity() -> None:
    ingest_run_id = uuid4()
    area_id = uuid4()
    app = _make_app(
        ingest_run_id,
        JobStatus.SUCCEEDED,
        area_id=area_id,
        approved_for_report=True,
    )
    _services(app).area_service.create(_area_contract(area_id))
    client = TestClient(app)

    response = client.post(
        f"/connector-runs/{ingest_run_id}/report-runs",
        headers=_REVIEWER_HEADERS,
        json={"intent_code": "homestead_feasibility"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "X-Workspace-Id header is required"


def test_connector_report_run_hides_other_workspace_item() -> None:
    ingest_run_id = uuid4()
    area_id = uuid4()
    app = _make_app(
        ingest_run_id,
        JobStatus.SUCCEEDED,
        area_id=area_id,
        workspace_id=_OTHER_WORKSPACE_ID,
        requested_by=_OTHER_USER_ID,
        approved_for_report=True,
    )
    _services(app).area_service.create(
        _area_contract(
            area_id,
            workspace_id=_OTHER_WORKSPACE_ID,
            created_by=_OTHER_USER_ID,
        )
    )
    client = TestClient(app)

    response = client.post(
        f"/connector-runs/{ingest_run_id}/report-runs",
        headers=_VALID_HEADERS,
        json={"intent_code": "homestead_feasibility"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "connector review queue item not found"
    assert _services(app).async_report_jobs.list_recent() == []


def test_connector_report_run_stores_workspace_and_requester_identity() -> None:
    ingest_run_id = uuid4()
    area_id = uuid4()
    app = _make_app(
        ingest_run_id,
        JobStatus.SUCCEEDED,
        area_id=area_id,
        approved_for_report=True,
    )
    _services(app).area_service.create(_area_contract(area_id))
    client = TestClient(app)

    response = client.post(
        f"/connector-runs/{ingest_run_id}/report-runs",
        headers=_VALID_HEADERS,
        json={"intent_code": "homestead_feasibility"},
    )

    assert response.status_code == 202
    body = response.json()
    job = _services(app).async_report_jobs.get(UUID(body["report_run_id"]))
    assert job is not None
    assert job.workspace_id == _WORKSPACE_ID
    assert job.requested_by == _USER_ID
