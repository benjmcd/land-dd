from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.connectors import (
    CONNECTOR_REVIEW_STATUS_JOB_TYPE,
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
from app.domain.enums import ConfidenceBand, EvidenceType, JobStatus
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"
_WORKSPACE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_USER_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
_OTHER_WORKSPACE_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
_OTHER_USER_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")


def _auth_headers(
    workspace_id: UUID = _WORKSPACE_ID,
    user_id: UUID = _USER_ID,
) -> dict[str, str]:
    return {"X-Workspace-Id": str(workspace_id), "X-User-Id": str(user_id)}


def _client(app: FastAPI | None = None) -> TestClient:
    client = TestClient(app or create_app())
    client.headers.update(_auth_headers())
    return client


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
    workspace_id: UUID = _WORKSPACE_ID,
    requested_by: UUID = _USER_ID,
) -> ConnectorReviewQueueItem:
    services = cast(ApiServices, app.state.services)
    review_status = _build_review_status(fixture_name)
    return services.connector_review_queue_repo.enqueue_review_status(
        review_status,
        workspace_id=workspace_id,
        requested_by=requested_by,
    )


def test_list_connector_review_queue_returns_empty_list_when_no_items() -> None:
    client = _client()

    response = client.get("/connector-review-queue")

    assert response.status_code == 200
    assert response.json() == []


def test_list_connector_review_queue_requires_identity() -> None:
    client = TestClient(create_app())

    response = client.get("/connector-review-queue")

    assert response.status_code == 401


def test_list_connector_review_queue_returns_enqueued_items() -> None:
    app = create_app()
    client = _client(app)
    services = cast(ApiServices, app.state.services)
    review_status = _build_review_status("flood_success.json")
    services.connector_review_queue_repo.enqueue_review_status(
        review_status,
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )

    response = client.get("/connector-review-queue")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["workspace_id"] == str(_WORKSPACE_ID)
    assert body[0]["job_type"] == "connector_review_status"
    assert body[0]["status"] == "queued"
    assert body[0]["payload"]["workspace_id"] == str(_WORKSPACE_ID)
    assert body[0]["payload"]["requested_by"] == str(_USER_ID)


def test_connector_review_queue_hides_items_from_other_workspace() -> None:
    app = create_app()
    client = _client(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    other_headers = _auth_headers(
        workspace_id=_OTHER_WORKSPACE_ID,
        user_id=_OTHER_USER_ID,
    )

    listed = client.get("/connector-review-queue", headers=other_headers)
    fetched = client.get(
        f"/connector-review-queue/{item.ingest_run_id}",
        headers=other_headers,
    )

    assert listed.status_code == 200
    assert listed.json() == []
    assert fetched.status_code == 404


def test_list_connector_review_queue_filters_by_status() -> None:
    app = create_app()
    client = _client(app)
    services = cast(ApiServices, app.state.services)
    services.connector_review_queue_repo.enqueue_review_status(
        _build_review_status("flood_success.json"),
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )
    services.connector_review_queue_repo.enqueue_review_status(
        _build_review_status("flood_failure.json"),
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )

    queued = client.get("/connector-review-queue?status=queued")
    needs_review = client.get("/connector-review-queue?status=needs_review")

    assert queued.status_code == 200
    assert len(queued.json()) == 1
    assert queued.json()[0]["status"] == "queued"
    assert needs_review.status_code == 200
    assert len(needs_review.json()) == 1
    assert needs_review.json()[0]["status"] == "needs_review"


def test_list_connector_review_queue_filters_by_connector_name() -> None:
    app = create_app()
    client = _client(app)
    services = cast(ApiServices, app.state.services)
    services.connector_review_queue_repo.enqueue_review_status(
        _build_review_status("flood_success.json"),
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )

    match = client.get(
        "/connector-review-queue?connector_name=fixture_flood_static"
    )
    no_match = client.get(
        "/connector-review-queue?connector_name=other_connector"
    )

    assert match.status_code == 200
    assert len(match.json()) == 1
    assert no_match.status_code == 200
    assert no_match.json() == []


def test_list_connector_review_queue_respects_limit_and_offset() -> None:
    app = create_app()
    client = _client(app)
    services = cast(ApiServices, app.state.services)
    services.connector_review_queue_repo.enqueue_review_status(
        _build_review_status("flood_success.json"),
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )
    services.connector_review_queue_repo.enqueue_review_status(
        _build_review_status("flood_failure.json"),
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )

    first = client.get("/connector-review-queue?limit=1&offset=0")
    second = client.get("/connector-review-queue?limit=1&offset=1")
    all_items = client.get("/connector-review-queue")

    assert first.status_code == 200
    assert len(first.json()) == 1
    assert second.status_code == 200
    assert len(second.json()) == 1
    assert first.json()[0]["ingest_run_id"] != second.json()[0]["ingest_run_id"]
    assert len(all_items.json()) == 2


def test_list_connector_review_queue_rejects_invalid_status() -> None:
    client = _client()

    response = client.get("/connector-review-queue?status=not_a_status")

    assert response.status_code == 422


def test_list_connector_review_queue_rejects_invalid_pagination() -> None:
    client = _client()

    bad_limit = client.get("/connector-review-queue?limit=0")
    bad_offset = client.get("/connector-review-queue?offset=-1")

    assert bad_limit.status_code == 422
    assert bad_offset.status_code == 422


def test_get_connector_review_queue_item_returns_queued_status() -> None:
    app = create_app()
    client = _client(app)
    services = cast(ApiServices, app.state.services)
    review_status = _build_review_status("flood_success.json")
    item = services.connector_review_queue_repo.enqueue_review_status(
        review_status,
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )

    response = client.get(f"/connector-review-queue/{item.ingest_run_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["ingest_run_id"] == str(item.ingest_run_id)
    assert body["job_type"] == CONNECTOR_REVIEW_STATUS_JOB_TYPE
    assert body["status"] == JobStatus.QUEUED.value
    assert "idempotency_key" not in body


def test_get_connector_review_queue_item_returns_needs_review_for_failure_fixture() -> None:
    app = create_app()
    client = _client(app)
    services = cast(ApiServices, app.state.services)
    review_status = _build_review_status("flood_failure.json")
    item = services.connector_review_queue_repo.enqueue_review_status(
        review_status,
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
    )

    response = client.get(f"/connector-review-queue/{item.ingest_run_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == JobStatus.NEEDS_REVIEW.value
    assert body["payload"]["review_required"] is True
    assert body["payload"]["kind"] == CONNECTOR_REVIEW_STATUS_JOB_TYPE


def test_get_connector_review_queue_item_returns_404_for_unknown_ingest_run_id() -> None:
    client = _client()

    response = client.get(f"/connector-review-queue/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "connector review queue item not found"


def test_get_connector_review_queue_item_returns_422_for_non_uuid_path_segment() -> None:
    client = _client()

    response = client.get("/connector-review-queue/not-a-uuid")

    assert response.status_code == 422


def test_approve_connector_review_queue_item_records_reviewer_action() -> None:
    app = create_app()
    client = _client(app)
    item = _enqueue_review_item(app, "flood_failure.json")

    response = client.post(
        f"/connector-review-queue/{item.ingest_run_id}/approve",
        json={"reviewer_id": f" {str(_USER_ID)} ", "reason": "checked source packet"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == JobStatus.SUCCEEDED.value
    assert body["last_error"] is None
    action = body["payload"]["last_review_action"]
    assert action["action"] == "approve"
    assert action["reviewer_id"] == str(_USER_ID)
    assert action["reason"] == "checked source packet"
    assert body["payload"]["review_actions"] == [action]


def test_reject_connector_review_queue_item_records_reviewer_action() -> None:
    app = create_app()
    client = _client(app)
    item = _enqueue_review_item(app, "flood_failure.json")

    response = client.post(
        f"/connector-review-queue/{item.ingest_run_id}/reject",
        json={"reviewer_id": str(_USER_ID), "reason": "source packet rejected"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == JobStatus.FAILED.value
    assert body["last_error"] == "source packet rejected"
    action = body["payload"]["last_review_action"]
    assert action["action"] == "reject"
    assert action["reviewer_id"] == str(_USER_ID)
    assert action["reason"] == "source packet rejected"


def test_requeue_connector_review_queue_item_appends_second_reviewer_action() -> None:
    app = create_app()
    client = _client(app)
    item = _enqueue_review_item(app, "flood_failure.json")
    rejected = client.post(
        f"/connector-review-queue/{item.ingest_run_id}/reject",
        json={"reviewer_id": str(_USER_ID), "reason": "temporary source issue"},
    )
    assert rejected.status_code == 200

    response = client.post(
        f"/connector-review-queue/{item.ingest_run_id}/requeue",
        json={"reviewer_id": str(_USER_ID), "reason": "retry source packet"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == JobStatus.QUEUED.value
    assert body["last_error"] == "retry source packet"
    actions = body["payload"]["review_actions"]
    assert [action["action"] for action in actions] == ["reject", "requeue"]
    assert actions[-1]["reviewer_id"] == str(_USER_ID)


def test_cancel_connector_review_queue_item_records_reviewer_action() -> None:
    app = create_app()
    client = _client(app)
    item = _enqueue_review_item(app, "flood_failure.json")

    response = client.post(
        f"/connector-review-queue/{item.ingest_run_id}/cancel",
        json={"reviewer_id": str(_USER_ID), "reason": "duplicate packet"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == JobStatus.CANCELLED.value
    assert body["last_error"] == "duplicate packet"
    action = body["payload"]["last_review_action"]
    assert action["action"] == "cancel"
    assert action["reviewer_id"] == str(_USER_ID)


def test_connector_review_action_rejects_missing_reviewer_identity() -> None:
    app = create_app()
    client = _client(app)
    item = _enqueue_review_item(app, "flood_failure.json")

    response = client.post(
        f"/connector-review-queue/{item.ingest_run_id}/approve",
        json={"reviewer_id": " "},
    )

    assert response.status_code == 422
    assert "reviewer_id" in response.json()["detail"]


def test_connector_review_action_rejects_reviewer_identity_mismatch() -> None:
    app = create_app()
    client = _client(app)
    item = _enqueue_review_item(app, "flood_failure.json")

    response = client.post(
        f"/connector-review-queue/{item.ingest_run_id}/approve",
        json={"reviewer_id": str(_OTHER_USER_ID)},
    )

    assert response.status_code == 403
    assert "reviewer_id" in response.json()["detail"]


def test_connector_review_action_rejects_missing_reason_when_required() -> None:
    app = create_app()
    client = _client(app)
    item = _enqueue_review_item(app, "flood_failure.json")

    response = client.post(
        f"/connector-review-queue/{item.ingest_run_id}/reject",
        json={"reviewer_id": str(_USER_ID)},
    )

    assert response.status_code == 422
    assert "reason is required" in response.json()["detail"]
