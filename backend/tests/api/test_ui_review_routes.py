from __future__ import annotations

import json
import re
from dataclasses import replace as _dc_replace
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
_CSRF_FIELD = "csrf_token"


def _csrf_token_from(html: str) -> str:
    match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


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
    assert 'name="viewport"' in response.text
    assert "href='/ui/'" in response.text
    assert "<select name='status'>" in response.text
    assert "Connector Review Queue" in response.text
    assert "No connector review items" in response.text


def test_ui_review_queue_list_renders_items() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.get("/ui/connector-review-queue")
    assert response.status_code == 200
    assert str(item.ingest_run_id)[:8] in response.text
    assert "class='review-queue-table-wrap'" in response.text
    assert "class='review-queue-table'" in response.text


def test_ui_review_queue_list_shows_needs_review_triage_and_next_action() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")

    response = tc.get("/ui/connector-review-queue")

    assert response.status_code == 200
    assert "<th>Triage</th>" in response.text
    assert "<th>Next Action</th>" in response.text
    assert "needs_human_review" in response.text
    assert "retrieval_not_succeeded" in response.text
    assert "Review connector retrieval status" in response.text
    assert "Blocking: 0" in response.text
    assert "Evidence: 1 created / 0 skipped" in response.text
    assert "Source failures: 1 created / 0 skipped" in response.text
    assert f"href='/ui/connector-review-queue/{item.ingest_run_id}'" in response.text
    assert "Review item" in response.text


def test_ui_review_queue_list_shows_failed_triage_and_requeue_action() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    services = cast(ApiServices, app.state.services)
    failed = services.connector_review_queue.request_fixture_fix(
        item.job_id,
        reviewer_id=_FIXTURE_REVIEWER_ID,
        reason="Needs fixture update",
    )

    response = tc.get("/ui/connector-review-queue?status=failed")

    assert response.status_code == 200
    assert str(failed.ingest_run_id)[:8] in response.text
    assert "needs_human_review" in response.text
    assert "source_failure_evidence_present" in response.text
    assert "Requeue or cancel" in response.text
    assert f"href='/ui/connector-review-queue/{failed.ingest_run_id}'" in response.text


def test_ui_review_queue_list_shows_succeeded_triage_and_resume_action() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_success.json")
    services = cast(ApiServices, app.state.services)
    succeeded = services.connector_review_queue.approve_for_connector_qa(
        item.job_id,
        reviewer_id=_FIXTURE_REVIEWER_ID,
    )

    response = tc.get("/ui/connector-review-queue?status=succeeded")

    assert response.status_code == 200
    assert str(succeeded.ingest_run_id)[:8] in response.text
    assert "ready_for_connector_qa" in response.text
    assert "Confirm connector provenance and evidence counts before promotion." in (
        response.text
    )
    assert "Evidence: 1 created / 0 skipped" in response.text
    assert "Source failures: 0 created / 0 skipped" in response.text
    assert "Resume report" in response.text
    assert f"href='/ui/connector-review-queue/{succeeded.ingest_run_id}'" in response.text


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


def test_ui_review_queue_list_invalid_status_fails_closed() -> None:
    app = create_app()
    tc = TestClient(app)
    response = tc.get("/ui/connector-review-queue?status=bogus")
    assert response.status_code == 422
    assert "text/html" in response.headers["content-type"]
    assert "Invalid Status Filter" in response.text
    assert "bogus" in response.text
    assert "queued" in response.text


# ---------------------------------------------------------------------------
# Detail page tests
# ---------------------------------------------------------------------------


def test_ui_review_detail_not_found() -> None:
    app = create_app()
    tc = TestClient(app)
    response = tc.get(f"/ui/connector-review-queue/{uuid4()}")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "href='/ui/connector-review-queue'" in response.text
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


def test_ui_review_detail_renders_failed_decision_context() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")

    response = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")

    assert response.status_code == 200
    assert "Decision Context" in response.text
    assert "fixture_flood_static blocked run 66666666" in response.text
    assert (
        "1 evidence created, 0 evidence skipped, 1 source failures observed."
        in response.text
    )
    assert "Review connector retrieval status" in response.text
    assert "source_failure_evidence_present" in response.text
    assert "<div class='context-label'>Rows</div><div class='context-value'>0</div>" in (
        response.text
    )
    assert "<div class='context-label'>Errors</div><div class='context-value'>1</div>" in (
        response.text
    )
    assert "<div class='context-label'>Warnings</div><div class='context-value'>0</div>" in (
        response.text
    )
    assert "fixture://connectors/flood_failure" in response.text
    assert "failure_reason" in response.text
    assert "fixture_source_unavailable" in response.text
    assert "FLOOD_SOURCE_UNAVAILABLE" in response.text
    assert "Fixture flood source retrieval was unavailable." in response.text
    assert "Fixture-only source failure; flood status is not evaluated." in response.text
    assert "<div class='context-label'>Evidence Created</div>" in response.text
    assert "<div class='context-value'>1</div>" in response.text
    assert "1 created, 0 skipped" in response.text
    assert "77777777-7777-4777-8777-777777777777" in response.text
    assert "<span class='evidence-pill'>source failure</span>" in response.text


def test_ui_review_detail_renders_success_evidence_context_without_failure_framing() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_success.json")

    response = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")

    assert response.status_code == 200
    assert "Decision Context" in response.text
    assert "fixture_flood_static succeeded run 11111111" in response.text
    assert (
        "1 evidence created, 0 evidence skipped, 0 source failures observed."
        in response.text
    )
    assert "Confirm connector provenance and evidence counts before promotion." in response.text
    assert "<div class='context-label'>Rows</div><div class='context-value'>1</div>" in (
        response.text
    )
    assert "<div class='context-label'>Errors</div><div class='context-value'>0</div>" in (
        response.text
    )
    assert "<div class='context-label'>Warnings</div><div class='context-value'>0</div>" in (
        response.text
    )
    assert "fixture://connectors/flood_success" in response.text
    assert "FLOOD_ZONE_SCREEN" in response.text
    assert "Fixture flood geometry intersects the subject area." in response.text
    assert "Fixture-only flood screening; not a final flood determination." in response.text
    assert "33333333-3333-4333-8333-333333333333" in response.text
    assert "<span class='evidence-pill'>evidence</span>" in response.text
    assert "<span class='evidence-pill'>source failure</span>" not in response.text
    assert "source_failure_evidence_present" not in response.text
    assert (
        "Confirm source-failure evidence before downstream claim or report use."
        not in response.text
    )


def test_ui_review_detail_decision_context_does_not_dump_secret_payload_keys() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    services = cast(ApiServices, app.state.services)
    repo = services.connector_review_queue_repo
    payload = dict(item.payload)
    payload["api_key"] = "super-secret-value"
    metrics = dict(cast(dict[str, object], payload["metrics"]))
    metrics["access_token"] = "nested-secret-value"
    payload["metrics"] = metrics
    patched = _dc_replace(item, payload=payload)
    repo._store[item.ingest_run_id] = patched  # type: ignore[attr-defined]

    response = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")

    assert response.status_code == 200
    assert "Decision Context" in response.text
    assert "super-secret-value" not in response.text
    assert "nested-secret-value" not in response.text


def test_ui_review_detail_has_action_forms() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")
    assert response.status_code == 200
    assert 'name="viewport"' in response.text
    assert "href='/ui/connector-review-queue'" in response.text
    assert "Approve" in response.text
    assert "reject" in response.text.lower() or "Request Fix" in response.text
    assert "Cancel" in response.text
    base_action = f"/ui/connector-review-queue/{item.ingest_run_id}"
    assert f"action='{base_action}/approve'" in response.text
    assert f"action='{base_action}/reject'" in response.text
    assert f"action='{base_action}/requeue'" not in response.text
    assert f"action='{base_action}/cancel'" in response.text
    assert "reviewer_id" in response.text
    assert "reviewer_token" in response.text


def test_ui_review_detail_open_item_shows_review_actions_without_requeue() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")

    assert item.status in {JobStatus.NEEDS_REVIEW, JobStatus.QUEUED}
    response = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")

    assert response.status_code == 200
    base_action = f"/ui/connector-review-queue/{item.ingest_run_id}"
    assert f"action='{base_action}/approve'" in response.text
    assert f"action='{base_action}/reject'" in response.text
    assert f"action='{base_action}/cancel'" in response.text
    assert "reviewer_id" in response.text
    assert "reviewer_token" in response.text
    assert f"action='{base_action}/requeue'" not in response.text
    assert f"action='{base_action}/resume-report'" not in response.text


def test_ui_review_detail_failed_item_shows_requeue_and_cancel_only() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    services = cast(ApiServices, app.state.services)
    failed = services.connector_review_queue.request_fixture_fix(
        item.job_id,
        reviewer_id=_FIXTURE_REVIEWER_ID,
        reason="Needs fixture update",
    )

    assert failed.status == JobStatus.FAILED
    assert failed.attempts < failed.max_attempts
    response = tc.get(f"/ui/connector-review-queue/{failed.ingest_run_id}")

    assert response.status_code == 200
    base_action = f"/ui/connector-review-queue/{failed.ingest_run_id}"
    assert f"action='{base_action}/requeue'" in response.text
    assert f"action='{base_action}/cancel'" in response.text
    assert f"action='{base_action}/approve'" not in response.text
    assert f"action='{base_action}/reject'" not in response.text
    assert f"action='{base_action}/resume-report'" not in response.text


def test_ui_review_detail_succeeded_item_shows_resume_report_only() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    services = cast(ApiServices, app.state.services)
    succeeded = services.connector_review_queue.approve_for_connector_qa(
        item.job_id,
        reviewer_id=_FIXTURE_REVIEWER_ID,
    )

    assert succeeded.status == JobStatus.SUCCEEDED
    response = tc.get(f"/ui/connector-review-queue/{succeeded.ingest_run_id}")

    assert response.status_code == 200
    base_action = f"/ui/connector-review-queue/{succeeded.ingest_run_id}"
    assert f"action='{base_action}/resume-report'" in response.text
    assert f"action='{base_action}/approve'" not in response.text
    assert f"action='{base_action}/reject'" not in response.text
    assert f"action='{base_action}/requeue'" not in response.text
    assert f"action='{base_action}/cancel'" not in response.text


def test_ui_review_detail_cancelled_item_shows_no_actions_message() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    services = cast(ApiServices, app.state.services)
    cancelled = services.connector_review_queue.cancel(
        item.job_id,
        reason="No longer needed",
        reviewer_id=_FIXTURE_REVIEWER_ID,
    )

    assert cancelled.status == JobStatus.CANCELLED
    response = tc.get(f"/ui/connector-review-queue/{cancelled.ingest_run_id}")

    assert response.status_code == 200
    base_action = f"/ui/connector-review-queue/{cancelled.ingest_run_id}"
    assert f"action='{base_action}/approve'" not in response.text
    assert f"action='{base_action}/reject'" not in response.text
    assert f"action='{base_action}/requeue'" not in response.text
    assert f"action='{base_action}/cancel'" not in response.text
    assert f"action='{base_action}/resume-report'" not in response.text
    assert "No connector review actions are available for this status." in response.text


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


def test_ui_review_approve_accepts_reviewer_session_without_form_credentials() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    reviewer_login = tc.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )
    assert reviewer_login.status_code == 303

    detail = tc.get(f"/ui/connector-review-queue/{item.ingest_run_id}")
    assert "Using reviewer session" in detail.text
    assert "reviewer_token" not in detail.text
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/approve",
        data={_CSRF_FIELD: _csrf_token_from(detail.text)},
    )

    assert response.status_code == 200
    assert "Approved" in response.text
    services = cast(ApiServices, app.state.services)
    updated = services.connector_review_queue.get_by_ingest_run_id(item.ingest_run_id)
    assert updated is not None
    assert updated.status == JobStatus.SUCCEEDED
    assert updated.locked_by == _FIXTURE_REVIEWER_ID


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


def test_ui_review_requeue_missing_reason_returns_422() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/requeue",
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


def test_ui_review_cancel_missing_reason_returns_422() -> None:
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/cancel",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    assert response.status_code == 422
    assert "Reason is required" in response.text


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
# Resume-report action functional tests
# ---------------------------------------------------------------------------

_GEOM_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "tests" / "fixtures" / "geometries" / "valid_polygon.geojson"
)


def _register_area_and_enqueue_succeeded(
    app: FastAPI,
) -> tuple[TestClient, ConnectorReviewQueueItem, str]:
    """Create an area, enqueue an item, patch payload area_id, approve -> SUCCEEDED."""
    tc = TestClient(app)
    # Register an area via the API to get a valid area_id in the service
    geojson = json.loads(_GEOM_FIXTURE.read_text(encoding="utf-8"))
    area_resp = tc.post("/areas", json={"geom_geojson": geojson, "geom_source": "test fixture"})
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]

    # Enqueue a review item from the fixture
    item = _enqueue_review_item(app, "flood_failure.json")

    # Patch the payload area_id so the handler can find the registered area
    services = cast(ApiServices, app.state.services)
    repo = services.connector_review_queue_repo
    new_payload = dict(item.payload)
    new_payload["area_id"] = area_id
    patched = _dc_replace(item, payload=new_payload)
    repo._store[item.ingest_run_id] = patched  # type: ignore[attr-defined]

    # Approve the item (transitions to SUCCEEDED)
    services.connector_review_queue.approve_for_connector_qa(
        item.job_id,
        reviewer_id=_FIXTURE_REVIEWER_ID,
    )
    updated = services.connector_review_queue.get_by_ingest_run_id(item.ingest_run_id)
    assert updated is not None and updated.status == JobStatus.SUCCEEDED

    return tc, updated, area_id


def test_ui_review_resume_report_happy_path_queues_job_and_redirects_to_report() -> None:
    """Happy path: valid reviewer + SUCCEEDED item with registered area_id -> report redirect."""
    app = create_app()
    tc, item, _area_id = _register_area_and_enqueue_succeeded(app)

    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/resume-report",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
            "intent_code": "rural_land_purchase",
        },
        follow_redirects=False,
    )
    assert response.status_code in {302, 303, 307}
    location = response.headers["location"]
    assert location.startswith("/ui/report-runs/")
    report_run_id = location.removeprefix("/ui/report-runs/")

    # Verify the job was actually created
    services = cast(ApiServices, app.state.services)
    all_jobs = services.async_report_jobs.list_recent(limit=100)
    assert any(str(job.report_run_id) == report_run_id for job in all_jobs)


def test_ui_review_resume_report_non_succeeded_item_returns_409() -> None:
    """Connector review item not in SUCCEEDED state -> 409 error page."""
    app = create_app()
    tc = TestClient(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    # Item is in NEEDS_REVIEW or QUEUED — not SUCCEEDED
    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/resume-report",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
            "intent_code": "rural_land_purchase",
        },
    )
    assert response.status_code == 409
    assert "text/html" in response.headers["content-type"]


def test_ui_review_resume_report_unknown_intent_code_returns_422() -> None:
    """Unknown intent_code in payload -> 422 error page."""
    app = create_app()
    tc, item, _area_id = _register_area_and_enqueue_succeeded(app)

    response = tc.post(
        f"/ui/connector-review-queue/{item.ingest_run_id}/resume-report",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
            "intent_code": "not_a_real_intent",
        },
    )
    assert response.status_code == 422
    assert "text/html" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# Index page custom-intake JS handling
# ---------------------------------------------------------------------------


def test_ui_index_custom_intake_js_posts_form_action() -> None:
    app = create_app()
    tc = TestClient(app)
    response = tc.get("/ui/")
    assert response.status_code == 200
    assert "fetch(form.action" in response.text
    assert "new FormData(form)" in response.text
    assert "credentials: 'same-origin'" in response.text
    assert "fetch('/intake'" not in response.text


def test_ui_index_custom_intake_js_follows_server_redirect() -> None:
    app = create_app()
    tc = TestClient(app)
    response = tc.get("/ui/")
    assert response.status_code == 200
    html = response.text
    assert "response.redirected" in html
    assert "window.location.href = response.url" in html
