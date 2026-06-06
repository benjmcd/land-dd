from __future__ import annotations

import inspect
import os
from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import app.connectors.review_queue as review_queue_module
from app.connectors import (
    CONNECTOR_REVIEW_STATUS_JOB_TYPE,
    ConnectorEvidenceIngestionAdapter,
    ConnectorRetrievalProvenanceAdapter,
    ConnectorRunReviewStatus,
    FixtureConnectorIngestWorkflow,
    InMemoryConnectorReviewQueueRepository,
    SqlAlchemyConnectorReviewQueueRepository,
    StaticFloodFixtureConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
    evaluate_flood_fixture_quality,
)
from app.db.engine import build_engine
from app.domain.enums import ConfidenceBand, EvidenceType, JobStatus
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class QueueRetrievalProvenancePort:
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


class QueueEvidencePort:
    def __init__(self) -> None:
        self._stored: dict[UUID, EvidenceContract] = {}
        self._source_failure_counter = 1

    def create_observation(self, evidence: EvidenceContract) -> EvidenceContract:
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
        source_ingest_run_id: UUID | None = None,
    ) -> EvidenceContract:
        created = EvidenceContract(
            evidence_id=evidence_id or UUID(int=self._source_failure_counter),
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
            source_ingest_run_id=source_ingest_run_id,
        )
        self._source_failure_counter += 1
        self._stored[created.evidence_id] = created
        return created

    def evidence_exists(self, evidence_id: UUID) -> bool:
        return evidence_id in self._stored

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._stored.values()
            if evidence.area_id == area_id
        ]


def _workflow() -> FixtureConnectorIngestWorkflow:
    return FixtureConnectorIngestWorkflow(
        connector=StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            QueueRetrievalProvenancePort(),
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(
            QueueEvidencePort(),
        ),
    )


def _review_status(fixture_name: str) -> ConnectorRunReviewStatus:
    result = _workflow().ingest_fixture(FIXTURE_DIR / fixture_name)
    packet = build_connector_run_review_packet(result)
    handoff = build_connector_review_handoff(packet)
    quality = evaluate_flood_fixture_quality(result.connector_result)
    return build_connector_run_review_status(handoff, quality)


def test_in_memory_review_queue_enqueues_idempotent_success_status() -> None:
    review_status = _review_status("flood_success.json")
    repo = InMemoryConnectorReviewQueueRepository()

    first = repo.enqueue_review_status(review_status)
    second = repo.enqueue_review_status(review_status)

    assert first == second
    assert first.job_type == CONNECTOR_REVIEW_STATUS_JOB_TYPE
    assert first.status == JobStatus.QUEUED
    assert first.priority == 100
    assert first.ingest_run_id == review_status.handoff.packet.ingest_run_id
    assert first.payload["ingest_run_id"] == str(review_status.handoff.packet.ingest_run_id)
    assert first.payload["area_id"] == str(review_status.handoff.packet.area_id)
    assert first.payload["review_required"] is False


def test_in_memory_review_queue_rejects_cross_workspace_idempotency_collision() -> None:
    review_status = _review_status("flood_success.json")
    repo = InMemoryConnectorReviewQueueRepository()
    first_workspace_id = uuid4()
    second_workspace_id = uuid4()

    repo.enqueue_review_status(review_status, workspace_id=first_workspace_id)

    with pytest.raises(ValueError, match="insert did not round-trip"):
        repo.enqueue_review_status(review_status, workspace_id=second_workspace_id)

    assert repo.get_by_ingest_run_id(
        review_status.handoff.packet.ingest_run_id,
        workspace_id=second_workspace_id,
    ) is None


def test_sqlalchemy_review_queue_insert_uses_idempotency_conflict_guard() -> None:
    source = inspect.getsource(review_queue_module.SqlAlchemyConnectorReviewQueueRepository)

    assert "ON CONFLICT (idempotency_key) DO NOTHING" in source


def test_in_memory_review_queue_prioritizes_human_review_status() -> None:
    review_status = _review_status("flood_failure.json")
    repo = InMemoryConnectorReviewQueueRepository()

    item = repo.enqueue_review_status(review_status)

    assert item.status == JobStatus.NEEDS_REVIEW
    assert item.priority == 10
    assert item.payload["review_required"] is True
    assert item.payload["disposition"] == "needs_human_review"
    assert item.payload["kind"] == CONNECTOR_REVIEW_STATUS_JOB_TYPE


def test_in_memory_review_queue_leases_and_finishes_items() -> None:
    success_status = _review_status("flood_success.json")
    failure_status = _review_status("flood_failure.json")
    repo = InMemoryConnectorReviewQueueRepository()
    success_item = repo.enqueue_review_status(success_status)
    failure_item = repo.enqueue_review_status(failure_status)

    first_lease = repo.lease_next(worker_id=" worker-1 ")
    second_lease = repo.lease_next(worker_id="worker-1")

    assert first_lease is not None
    assert first_lease.job_id == failure_item.job_id
    assert first_lease.status == JobStatus.RUNNING
    assert first_lease.attempts == 1
    assert first_lease.locked_by == "worker-1"
    assert first_lease.started_at is not None
    assert second_lease is not None
    assert second_lease.job_id == success_item.job_id
    assert second_lease.status == JobStatus.RUNNING
    assert repo.lease_next(worker_id="worker-1") is None

    succeeded = repo.mark_succeeded(first_lease.job_id)
    failed = repo.mark_failed(second_lease.job_id, error="fixture review rejected")

    assert succeeded.status == JobStatus.SUCCEEDED
    assert succeeded.finished_at is not None
    assert succeeded.last_error is None
    assert failed.status == JobStatus.FAILED
    assert failed.finished_at is not None
    assert failed.last_error == "fixture review rejected"


def test_in_memory_review_queue_rejects_invalid_worker_transitions() -> None:
    review_status = _review_status("flood_failure.json")
    repo = InMemoryConnectorReviewQueueRepository()
    item = repo.enqueue_review_status(review_status)

    with pytest.raises(ValueError, match="worker_id is required"):
        repo.lease_next(worker_id=" ")
    with pytest.raises(ValueError, match="not running"):
        repo.mark_succeeded(item.job_id)
    leased = repo.lease_next(worker_id="worker-1")
    assert leased is not None
    with pytest.raises(ValueError, match="failure error is required"):
        repo.mark_failed(leased.job_id, error="")


def test_in_memory_review_queue_requeues_failed_jobs_with_remaining_attempts() -> None:
    review_status = _review_status("flood_failure.json")
    repo = InMemoryConnectorReviewQueueRepository()
    item = repo.enqueue_review_status(review_status)
    repo._store[item.ingest_run_id] = replace(item, max_attempts=2)

    first_lease = repo.lease_next(worker_id="worker-1")
    assert first_lease is not None
    first_failure = repo.mark_failed(first_lease.job_id, error="temporary review error")
    requeued = repo.requeue_failed(
        first_failure.job_id,
        reason="retry after reviewer handoff",
        reviewer_id="reviewer-1",
    )

    assert requeued.status == JobStatus.QUEUED
    assert requeued.attempts == 1
    assert requeued.max_attempts == 2
    assert requeued.locked_by is None
    assert requeued.locked_at is None
    assert requeued.finished_at is None
    assert requeued.last_error == "retry after reviewer handoff"
    assert requeued.payload["review_action_history"][0]["action"] == "requeue_after_fix"
    assert requeued.payload["review_action_history"][0]["reviewer_id"] == "reviewer-1"

    second_lease = repo.lease_next(worker_id="worker-2")
    assert second_lease is not None
    assert second_lease.attempts == 2
    second_failure = repo.mark_failed(second_lease.job_id, error="permanent error")
    with pytest.raises(ValueError, match="no retry attempts remaining"):
        repo.requeue_failed(second_failure.job_id, reason="retry not allowed")


def test_in_memory_review_queue_cancels_nonfinal_jobs() -> None:
    review_status = _review_status("flood_success.json")
    repo = InMemoryConnectorReviewQueueRepository()
    item = repo.enqueue_review_status(review_status)

    with pytest.raises(ValueError, match="reason is required"):
        repo.cancel(item.job_id, reason=" ")
    cancelled = repo.cancel(
        item.job_id,
        reason="review no longer required",
        reviewer_id="reviewer-1",
    )

    assert cancelled.status == JobStatus.CANCELLED
    assert cancelled.finished_at is not None
    assert cancelled.last_error == "review no longer required"
    assert cancelled.payload["review_action_history"][0]["action"] == "cancel_review"
    assert cancelled.payload["review_action_history"][0]["reviewer_id"] == "reviewer-1"
    assert repo.lease_next(worker_id="worker-1") is None
    with pytest.raises(ValueError, match="cannot be cancelled"):
        repo.cancel(cancelled.job_id, reason="already cancelled")


def test_in_memory_review_queue_manual_closeout_records_reviewer_decision() -> None:
    success_status = _review_status("flood_success.json")
    failure_status = _review_status("flood_failure.json")
    repo = InMemoryConnectorReviewQueueRepository()
    approve_candidate = repo.enqueue_review_status(success_status)
    fix_candidate = repo.enqueue_review_status(failure_status)

    approved = repo.approve_for_connector_qa(
        approve_candidate.job_id,
        reviewer_id=" reviewer-1 ",
        reason="connector output is acceptable",
    )
    fix_requested = repo.request_fixture_fix(
        fix_candidate.job_id,
        reviewer_id="reviewer-2",
        reason="source-failure payload needs correction",
    )

    assert approved.status == JobStatus.SUCCEEDED
    assert approved.locked_by == "reviewer-1"
    assert approved.payload["review_decision"]["action"] == "approve_for_connector_qa"
    assert approved.payload["review_decision"]["reason"] == "connector output is acceptable"
    assert approved.payload["review_action_history"][0] == approved.payload[
        "review_decision"
    ]
    assert fix_requested.status == JobStatus.FAILED
    assert fix_requested.locked_by == "reviewer-2"
    assert fix_requested.last_error == "source-failure payload needs correction"
    assert fix_requested.payload["review_decision"]["action"] == "request_fixture_fix"
    assert fix_requested.payload["review_action_history"][0] == fix_requested.payload[
        "review_decision"
    ]

    with pytest.raises(ValueError, match="cannot be approved"):
        repo.approve_for_connector_qa(
            approved.job_id,
            reviewer_id="reviewer-1",
        )
    with pytest.raises(ValueError, match="reason is required"):
        repo.request_fixture_fix(
            fix_requested.job_id,
            reviewer_id="reviewer-2",
            reason=" ",
        )


def test_in_memory_review_queue_preserves_reviewer_action_history_sequence() -> None:
    review_status = _review_status("flood_failure.json")
    repo = InMemoryConnectorReviewQueueRepository()
    item = repo.enqueue_review_status(review_status)

    fix_requested = repo.request_fixture_fix(
        item.job_id,
        reviewer_id="reviewer-1",
        reason="source response needs fixture correction",
    )
    requeued = repo.requeue_failed(
        fix_requested.job_id,
        reason="fixture correction applied",
        reviewer_id="reviewer-2",
    )
    approved = repo.approve_for_connector_qa(
        requeued.job_id,
        reviewer_id="reviewer-3",
        reason="corrected connector output is acceptable",
    )

    assert approved.status == JobStatus.SUCCEEDED
    assert approved.payload["review_decision"]["action"] == "approve_for_connector_qa"
    assert [
        entry["action"]
        for entry in approved.payload["review_action_history"]
    ] == [
        "request_fixture_fix",
        "requeue_after_fix",
        "approve_for_connector_qa",
    ]
    assert [
        entry["reviewer_id"]
        for entry in approved.payload["review_action_history"]
    ] == [
        "reviewer-1",
        "reviewer-2",
        "reviewer-3",
    ]


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_review_queue_persists_status_in_job_queue() -> None:
    engine = build_engine()
    review_status = _review_status("flood_failure.json")
    ingest_run_id = review_status.handoff.packet.ingest_run_id
    idempotency_key = f"{CONNECTOR_REVIEW_STATUS_JOB_TYPE}:{ingest_run_id}"

    try:
        with Session(engine) as session:
            session.execute(
                text(
                    "DELETE FROM jobs.job_queue "
                    "WHERE idempotency_key = :idempotency_key"
                ),
                {"idempotency_key": idempotency_key},
            )
            repo = SqlAlchemyConnectorReviewQueueRepository(session)

            first = repo.enqueue_review_status(review_status)
            second = repo.enqueue_review_status(review_status)
            session.commit()

            assert second == first
            assert first.status == JobStatus.NEEDS_REVIEW
            assert first.priority == 10
            assert first.payload["kind"] == CONNECTOR_REVIEW_STATUS_JOB_TYPE
            assert first.payload["ingest_run_id"] == str(ingest_run_id)
            assert first.payload["area_id"] == str(review_status.handoff.packet.area_id)
            assert first.payload["review_required"] is True

        with Session(engine) as session:
            repo = SqlAlchemyConnectorReviewQueueRepository(session)
            stored = repo.get_by_ingest_run_id(ingest_run_id)

            assert stored is not None
            assert stored.idempotency_key == idempotency_key
            assert stored.ingest_run_id == ingest_run_id
            assert stored.status == JobStatus.NEEDS_REVIEW
    finally:
        with Session(engine) as session:
            session.execute(
                text(
                    "DELETE FROM jobs.job_queue "
                    "WHERE idempotency_key = :idempotency_key"
                ),
                {"idempotency_key": idempotency_key},
            )
            session.commit()


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_review_queue_manual_closeout_records_reviewer_decision() -> None:
    engine = build_engine()
    success_status = _review_status("flood_success.json")
    failure_status = _review_status("flood_failure.json")

    try:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            repo = SqlAlchemyConnectorReviewQueueRepository(session)
            approve_candidate = repo.enqueue_review_status(success_status)
            fix_candidate = repo.enqueue_review_status(failure_status)

            approved = repo.approve_for_connector_qa(
                approve_candidate.job_id,
                reviewer_id="db-reviewer-1",
                reason="db connector output accepted",
            )
            fix_requested = repo.request_fixture_fix(
                fix_candidate.job_id,
                reviewer_id="db-reviewer-2",
                reason="db connector output needs correction",
            )
            session.commit()

            assert approved.status == JobStatus.SUCCEEDED
            assert approved.locked_by == "db-reviewer-1"
            assert approved.payload["review_decision"]["action"] == (
                "approve_for_connector_qa"
            )
            assert approved.payload["review_action_history"][0] == (
                approved.payload["review_decision"]
            )
            assert fix_requested.status == JobStatus.FAILED
            assert fix_requested.locked_by == "db-reviewer-2"
            assert fix_requested.last_error == "db connector output needs correction"
            assert fix_requested.payload["review_decision"]["action"] == (
                "request_fixture_fix"
            )
            assert fix_requested.payload["review_action_history"][0] == (
                fix_requested.payload["review_decision"]
            )

        with Session(engine) as session:
            repo = SqlAlchemyConnectorReviewQueueRepository(session)
            stored_approved = repo.get_by_ingest_run_id(
                success_status.handoff.packet.ingest_run_id
            )
            stored_fix = repo.get_by_ingest_run_id(
                failure_status.handoff.packet.ingest_run_id
            )

            assert stored_approved is not None
            assert stored_approved.status == JobStatus.SUCCEEDED
            assert stored_approved.payload["review_decision"]["reviewer_id"] == (
                "db-reviewer-1"
            )
            assert stored_approved.payload["review_action_history"][0] == (
                stored_approved.payload["review_decision"]
            )
            assert stored_fix is not None
            assert stored_fix.status == JobStatus.FAILED
            assert stored_fix.payload["review_decision"]["reason"] == (
                "db connector output needs correction"
            )
            assert stored_fix.payload["review_action_history"][0] == (
                stored_fix.payload["review_decision"]
            )
    finally:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            session.commit()


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_review_queue_preserves_reviewer_action_history_sequence() -> None:
    engine = build_engine()
    review_status = _review_status("flood_failure.json")

    try:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            repo = SqlAlchemyConnectorReviewQueueRepository(session)
            item = repo.enqueue_review_status(review_status)

            fix_requested = repo.request_fixture_fix(
                item.job_id,
                reviewer_id="db-reviewer-1",
                reason="source response needs fixture correction",
            )
            requeued = repo.requeue_failed(
                fix_requested.job_id,
                reason="fixture correction applied",
                reviewer_id="db-reviewer-2",
            )
            approved = repo.approve_for_connector_qa(
                requeued.job_id,
                reviewer_id="db-reviewer-3",
                reason="corrected connector output is acceptable",
            )
            session.commit()

            assert approved.status == JobStatus.SUCCEEDED
            assert [
                entry["action"]
                for entry in approved.payload["review_action_history"]
            ] == [
                "request_fixture_fix",
                "requeue_after_fix",
                "approve_for_connector_qa",
            ]

        with Session(engine) as session:
            repo = SqlAlchemyConnectorReviewQueueRepository(session)
            stored = repo.get_by_ingest_run_id(review_status.handoff.packet.ingest_run_id)

            assert stored is not None
            assert stored.status == JobStatus.SUCCEEDED
            assert [
                entry["reviewer_id"]
                for entry in stored.payload["review_action_history"]
            ] == [
                "db-reviewer-1",
                "db-reviewer-2",
                "db-reviewer-3",
            ]
            assert stored.payload["review_decision"] == (
                stored.payload["review_action_history"][-1]
            )
    finally:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            session.commit()


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_review_queue_leases_and_completes_job_queue_item() -> None:
    engine = build_engine()
    review_status = _review_status("flood_failure.json")

    try:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            repo = SqlAlchemyConnectorReviewQueueRepository(session)
            queued = repo.enqueue_review_status(review_status)
            session.commit()

        with Session(engine) as session:
            repo = SqlAlchemyConnectorReviewQueueRepository(session)
            leased = repo.lease_next(worker_id="connector-worker-1")
            assert leased is not None
            assert leased.job_id == queued.job_id
            assert leased.status == JobStatus.RUNNING
            assert leased.attempts == 1
            assert leased.max_attempts == 1
            assert leased.locked_by == "connector-worker-1"
            assert leased.locked_at is not None
            assert leased.started_at is not None
            assert repo.lease_next(worker_id="connector-worker-1") is None

            finished = repo.mark_succeeded(leased.job_id)
            session.commit()

            assert finished.status == JobStatus.SUCCEEDED
            assert finished.finished_at is not None
            assert finished.last_error is None

        with Session(engine) as session:
            repo = SqlAlchemyConnectorReviewQueueRepository(session)
            stored = repo.get_by_ingest_run_id(review_status.handoff.packet.ingest_run_id)

            assert stored is not None
            assert stored.status == JobStatus.SUCCEEDED
            assert stored.attempts == 1
            assert stored.locked_by == "connector-worker-1"
            assert stored.finished_at is not None
    finally:
        with Session(engine) as session:
            session.execute(
                text(
                    "DELETE FROM jobs.job_queue WHERE job_type = :job_type"
                ),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            session.commit()


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_review_queue_rejects_cross_workspace_idempotency_collision() -> None:
    engine = build_engine()
    review_status = _review_status("flood_success.json")
    first_workspace_id = uuid4()
    second_workspace_id = uuid4()

    try:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            session.execute(
                text(
                    """
                    INSERT INTO core.workspaces (workspace_id, name)
                    VALUES
                        (:first_workspace_id, 'review queue collision test 1'),
                        (:second_workspace_id, 'review queue collision test 2')
                    ON CONFLICT (workspace_id) DO NOTHING
                    """
                ),
                {
                    "first_workspace_id": str(first_workspace_id),
                    "second_workspace_id": str(second_workspace_id),
                },
            )
            repo = SqlAlchemyConnectorReviewQueueRepository(session)
            first = repo.enqueue_review_status(
                review_status,
                workspace_id=first_workspace_id,
            )

            with pytest.raises(ValueError, match="insert did not round-trip"):
                repo.enqueue_review_status(
                    review_status,
                    workspace_id=second_workspace_id,
                )

            assert first.workspace_id == first_workspace_id
            assert repo.get_by_ingest_run_id(
                review_status.handoff.packet.ingest_run_id,
                workspace_id=second_workspace_id,
            ) is None
            session.rollback()
    finally:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            session.execute(
                text(
                    "DELETE FROM core.workspaces "
                    "WHERE workspace_id IN (:first_workspace_id, :second_workspace_id)"
                ),
                {
                    "first_workspace_id": str(first_workspace_id),
                    "second_workspace_id": str(second_workspace_id),
                },
            )
            session.commit()


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_review_queue_requeues_and_cancels_job_queue_items() -> None:
    engine = build_engine()
    failure_status = _review_status("flood_failure.json")
    success_status = _review_status("flood_success.json")

    try:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            repo = SqlAlchemyConnectorReviewQueueRepository(session)
            failed_candidate = repo.enqueue_review_status(failure_status)
            session.execute(
                text(
                    "UPDATE jobs.job_queue "
                    "SET max_attempts = 2 "
                    "WHERE job_id = :job_id"
                ),
                {"job_id": str(failed_candidate.job_id)},
            )
            session.flush()

            first_lease = repo.lease_next(worker_id="db-worker-1")
            assert first_lease is not None
            first_failure = repo.mark_failed(
                first_lease.job_id,
                error="temporary db review error",
            )
            requeued = repo.requeue_failed(
                first_failure.job_id,
                reason="retry after db reviewer handoff",
                reviewer_id="db-reviewer-1",
            )

            assert requeued.status == JobStatus.QUEUED
            assert requeued.attempts == 1
            assert requeued.max_attempts == 2
            assert requeued.locked_by is None
            assert requeued.locked_at is None
            assert requeued.finished_at is None
            assert requeued.last_error == "retry after db reviewer handoff"
            assert requeued.payload["review_action_history"][0]["action"] == (
                "requeue_after_fix"
            )
            assert requeued.payload["review_action_history"][0]["reviewer_id"] == (
                "db-reviewer-1"
            )

            second_lease = repo.lease_next(worker_id="db-worker-2")
            assert second_lease is not None
            assert second_lease.attempts == 2
            second_failure = repo.mark_failed(
                second_lease.job_id,
                error="permanent db review error",
            )
            with pytest.raises(ValueError, match="no retry attempts remaining"):
                repo.requeue_failed(
                    second_failure.job_id,
                    reason="retry not allowed",
                )

            cancel_candidate = repo.enqueue_review_status(success_status)
            cancelled = repo.cancel(
                cancel_candidate.job_id,
                reason="connector review superseded",
                reviewer_id="db-reviewer-3",
            )
            session.commit()

            assert cancelled.status == JobStatus.CANCELLED
            assert cancelled.finished_at is not None
            assert cancelled.last_error == "connector review superseded"
            assert cancelled.payload["review_action_history"][0]["action"] == (
                "cancel_review"
            )
            assert cancelled.payload["review_action_history"][0]["reviewer_id"] == (
                "db-reviewer-3"
            )
    finally:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            session.commit()
