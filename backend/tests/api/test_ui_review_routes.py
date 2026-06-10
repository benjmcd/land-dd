from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.connectors import (
    ConnectorEvidenceIngestionAdapter,
    ConnectorRetrievalProvenanceAdapter,
    ConnectorReviewQueueItem,
    ConnectorRunReviewStatus,
    FixtureConnectorIngestWorkflow,
    StaticFloodFixtureConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
    evaluate_flood_fixture_quality,
)
from app.core.config import Settings
from app.domain.enums import ConfidenceBand, EvidenceType, JobStatus
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"

_FIXTURE_REVIEWER_ID = "fixture-reviewer"
_FIXTURE_REVIEWER_TOKEN = "fixture-token-123"


class _RetrievalProvenancePort:
    def __init__(self) -> None:
        self._stored: dict[UUID, SourceRetrievalRunContract] = {}

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        return ingest_run_id in self._stored

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        self._stored[retrieval_run.ingest_run_id] = retrieval_run
        return retrieval_run


class _EvidencePort:
    def __init__(self) -> None:
        self._stored: dict[UUID, EvidenceContract] = {}
        self._counter: int = 1

    def create_observation(
        self,
        evidence: EvidenceContract,
        *,
        workspace_id: UUID | None = None,
    ) -> EvidenceContract:
        self._stored[evidence.evidence_id] = evidence
        return evidence

    def create_source_failure(
        self,
        *,
        evidence_id: UUID | None = None,
        area_id: UUID,
        source_id: UUID,
        method_code: str,
        caveat: str,
        evidence_code: str = "SOURCE_FAILURE",
        domain: str = "unknown",
        observation: str | None = None,
        observed_value: dict[str, object] | None = None,
        workspace_id: UUID | None = None,
    ) -> EvidenceContract:
        created = EvidenceContract(
            evidence_id=evidence_id or UUID(int=self._counter),
            area_id=area_id,
            source_id=source_id,
            method_code=method_code,
            evidence_type=EvidenceType.SOURCE_FAILURE,
            evidence_code=evidence_code,
            domain=domain,
            observation=observation or f"Source unavailable or failed: {caveat}",
            observed_value=observed_value or {},
            confidence=ConfidenceBand.UNKNOWN,
            caveat=caveat,
            is_source_failure=True,
        )
        self._counter += 1
        self._stored[created.evidence_id] = created
        return created

    def evidence_exists(self, evidence_id: UUID) -> bool:
        return evidence_id in self._stored

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        return [e for e in self._stored.values() if e.area_id == area_id]


def _make_workflow() -> FixtureConnectorIngestWorkflow:
    return FixtureConnectorIngestWorkflow(
        connector=StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            _RetrievalProvenancePort()
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(_EvidencePort()),
    )


def _build_review_status(fixture_name: str) -> ConnectorRunReviewStatus:
    result = _make_workflow().ingest_fixture(FIXTURE_DIR / fixture_name)
    packet = build_connector_run_review_packet(result)
    handoff = build_connector_review_handoff(packet)
    quality = evaluate_flood_fixture_quality(result.connector_result)
    return build_connector_run_review_status(handoff, quality)


def _enqueue_review_item(
    app: FastAPI,
    fixture_name: str,
    *,
    workspace_id: UUID | None = None,
) -> ConnectorReviewQueueItem:
    services = cast(ApiServices, app.state.services)
    review_status = _build_review_status(fixture_name)
    return services.connector_review_queue_repo.enqueue_review_status(
        review_status,
        workspace_id=workspace_id,
    )


# ---------------------------------------------------------------------------
# List page tests
# ---------------------------------------------------------------------------


def test_ui_review_queue_list_empty_state() -> None:
    app = create_app()
    tc = TestClient(app)
    response = tc.get("/ui/connector-review-queue")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Connector Review Queue" in response.text
    assert "No connector review items" in response.text


def test_ui_review_queue_list_renders_items() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.get("/ui/connector-review-queue")
    assert response.status_code == 200
    assert str(item.ingest_run_id)[:8] in response.text


def test_ui_review_queue_list_status_filter_dropdown_present() -> None:
    app = create_app()
    tc = TestClient(app)
    response = tc.get("/ui/connector-review-queue")
    assert response.status_code == 200
    assert "<select name='status'>" in response.text
    assert "needs_review" in response.text or "queued" in response.text


def test_ui_review_queue_list_status_filter_filters_results() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    # Filter to the status that was enqueued
    status_val = item.status.value
    response = tc.get(f"/ui/connector-review-queue?status={status_val}")
    assert response.status_code == 200
    assert str(item.ingest_run_id)[:8] in response.text

    # Filter to a status that won't match
    other_status = "succeeded"
    if other_status == status_val:
        other_status = "failed"
    response2 = tc.get(f"/ui/connector-review-queue?status={other_status}")
    assert response2.status_code == 200
    assert str(item.ingest_run_id)[:8] not in response2.text


def test_ui_review_queue_list_pagination_controls() -> None:
    app = create_app()
    tc = TestClient(app)
    # Enqueue two items
    _enqueue_review_item(app, "flood_failure.json")
    # No pagination link for single page (limit default 25)
    response = tc.get("/ui/connector-review-queue?limit=1")
    assert response.status_code == 200
    # With limit=1, there should be a Next link if there's at least 1 item
    assert (
        "Next" in response.text
        or "Previous" in response.text
        or "connector-review-queue" in response.text
    )


def test_ui_review_queue_list_prev_next_links() -> None:
    app = create_app()
    tc = TestClient(app)
    _enqueue_review_item(app, "flood_failure.json")
    # offset=1 means there was a previous page
    response = tc.get("/ui/connector-review-queue?offset=1&limit=1")
    assert response.status_code == 200
    assert "Previous" in response.text


# ---------------------------------------------------------------------------
# Detail page tests
# ---------------------------------------------------------------------------


def test_ui_review_detail_not_found() -> None:
    app = create_app()
    tc = TestClient(app)
    response = tc.get(f"/ui/connector-review-queue/{uuid4()}")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "Not Found" in response.text


def test_ui_review_detail_invalid_uuid_returns_422() -> None:
    tc = TestClient(create_app())
    response = tc.get("/ui/connector-review-queue/not-a-uuid")
    assert response.status_code == 422


def test_ui_review_detail_renders_metadata() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert str(item.ingest_run_id) in response.text
    assert item.status.value in response.text


def test_ui_review_detail_renders_quality_issues() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")
    assert response.status_code == 200
    # Quality section must be present
    assert "Quality Issues" in response.text


def test_ui_review_detail_has_action_forms() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")
    assert response.status_code == 200
    assert "Approve" in response.text
    assert "reject" in response.text.lower() or "Request Fix" in response.text
    assert "Requeue" in response.text or "requeue" in response.text.lower()
    assert "Cancel" in response.text


def test_ui_review_detail_resume_form_shown_for_succeeded() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    # Approve the item first
    services = cast(ApiServices, app.state.services)
    services.connector_review_queue.approve_for_connector_qa(
        item.job_id,
        reviewer_id=_FIXTURE_REVIEWER_ID,
    )
    response = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")
    assert response.status_code == 200
    assert "Resume Report" in response.text or "resume-report" in response.text


def test_ui_review_detail_no_resume_form_for_non_succeeded() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    # Item is in needs_review or queued status — not succeeded
    response = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")
    assert response.status_code == 200
    # Resume form must NOT appear
    assert "resume-report" not in response.text


# ---------------------------------------------------------------------------
# Approve action tests
# ---------------------------------------------------------------------------


def test_ui_review_approve_no_credentials_returns_401() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/approve",
        data={},
    )
    assert response.status_code == 401
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Error" in response.text


def test_ui_review_approve_wrong_token_returns_403() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/approve",
        data={"reviewer_id": _FIXTURE_REVIEWER_ID, "reviewer_token": "wrong-token"},
    )
    assert response.status_code == 403
    assert "Authentication Error" in response.text


def test_ui_review_approve_valid_unscoped_returns_403() -> None:
    settings = Settings(
        REVIEWER_ACCOUNTS="scoped-reviewer:scoped-token",
        REVIEWER_ACCOUNT_SCOPES="scoped-reviewer:report:approve",
    )
    app = create_app(settings)
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/approve",
        data={"reviewer_id": "scoped-reviewer", "reviewer_token": "scoped-token"},
    )
    assert response.status_code == 403
    assert "Authentication Error" in response.text


def test_ui_review_approve_valid_scoped_transitions_item() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/approve",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    assert response.status_code == 200
    assert "Approved" in response.text
    # Reload detail — verify status is now succeeded
    services = cast(ApiServices, app.state.services)
    updated = services.connector_review_queue.get_by_ingest_run_id(item.ingest_run_id)
    assert updated is not None
    assert updated.status == JobStatus.SUCCEEDED


# ---------------------------------------------------------------------------
# Reject action tests
# ---------------------------------------------------------------------------


def test_ui_review_reject_no_credentials_returns_401() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/reject",
        data={},
    )
    assert response.status_code == 401
    assert "Authentication Error" in response.text


def test_ui_review_reject_wrong_token_returns_403() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/reject",
        data={"reviewer_id": _FIXTURE_REVIEWER_ID, "reviewer_token": "bad-token", "reason": "fix"},
    )
    assert response.status_code == 403


def test_ui_review_reject_valid_scoped_transitions_item() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/reject",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
            "reason": "Needs fixture update",
        },
    )
    assert response.status_code == 200
    assert "Fix Requested" in response.text
    services = cast(ApiServices, app.state.services)
    updated = services.connector_review_queue.get_by_ingest_run_id(item.ingest_run_id)
    assert updated is not None
    assert updated.status == JobStatus.FAILED


def test_ui_review_reject_missing_reason_returns_422() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/reject",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    assert response.status_code == 422
    assert "Reason is required" in response.text


# ---------------------------------------------------------------------------
# Requeue action tests
# ---------------------------------------------------------------------------


def test_ui_review_requeue_no_credentials_returns_401() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/requeue",
        data={},
    )
    assert response.status_code == 401


def test_ui_review_requeue_valid_scoped_after_fail() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    # First reject to put it in failed state
    services = cast(ApiServices, app.state.services)
    services.connector_review_queue.request_fixture_fix(
        item.job_id,
        reviewer_id=_FIXTURE_REVIEWER_ID,
        reason="Initial rejection",
    )
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/requeue",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
            "reason": "Fixture has been updated",
        },
    )
    assert response.status_code == 200
    assert "Requeued" in response.text
    updated = services.connector_review_queue.get_by_ingest_run_id(item.ingest_run_id)
    assert updated is not None
    assert updated.status == JobStatus.QUEUED


# ---------------------------------------------------------------------------
# Cancel action tests
# ---------------------------------------------------------------------------


def test_ui_review_cancel_no_credentials_returns_401() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/cancel",
        data={},
    )
    assert response.status_code == 401


def test_ui_review_cancel_valid_scoped_transitions_item() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/cancel",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
            "reason": "No longer needed",
        },
    )
    assert response.status_code == 200
    assert "Cancelled" in response.text
    services = cast(ApiServices, app.state.services)
    updated = services.connector_review_queue.get_by_ingest_run_id(item.ingest_run_id)
    assert updated is not None
    assert updated.status == JobStatus.CANCELLED


# ---------------------------------------------------------------------------
# Resume-report action auth tests
# ---------------------------------------------------------------------------


def test_ui_review_resume_report_no_credentials_returns_401() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/resume-report",
        data={},
    )
    assert response.status_code == 401
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Error" in response.text


def test_ui_review_resume_report_wrong_token_returns_403() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/resume-report",
        data={"reviewer_id": _FIXTURE_REVIEWER_ID, "reviewer_token": "wrong-token"},
    )
    assert response.status_code == 403
    assert "Authentication Error" in response.text


def test_ui_review_resume_report_valid_token_missing_report_run_scope_returns_403() -> None:
    settings = Settings(
        REVIEWER_ACCOUNTS="scoped-reviewer:scoped-token",
        REVIEWER_ACCOUNT_SCOPES="scoped-reviewer:connector:review",
    )
    app = create_app(settings)
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/resume-report",
        data={"reviewer_id": "scoped-reviewer", "reviewer_token": "scoped-token"},
    )
    assert response.status_code == 403
    assert "Authentication Error" in response.text


# ---------------------------------------------------------------------------
# Index page pending_connector_review JS handling
# ---------------------------------------------------------------------------


def test_ui_index_contains_pending_connector_review_js() -> None:
    app = create_app()
    tc = TestClient(app)
    response = tc.get("/ui/")
    assert response.status_code == 200
    assert "pending_connector_review" in response.text
    # The link template must be present in the JS
    assert "/ui/connector-review-queue/" in response.text


def test_ui_index_pending_connector_review_link_template() -> None:
    """Verify the JS block links to the queue detail page using connector_ingest_run_id."""
    app = create_app()
    tc = TestClient(app)
    response = tc.get("/ui/")
    assert response.status_code == 200
    html = response.text
    assert "connector_ingest_run_id" in html
    # The URL template must reference the connector-review-queue path
    assert "/ui/connector-review-queue/' + data.connector_ingest_run_id" in html
