from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

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
    assert first.payload["review_required"] is False


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


def test_in_memory_review_queue_reviewer_approval_records_action() -> None:
    review_status = _review_status("flood_failure.json")
    repo = InMemoryConnectorReviewQueueRepository()
    item = repo.enqueue_review_status(review_status)

    with pytest.raises(ValueError, match="reviewer_id is required"):
        repo.approve_review(item.job_id, reviewer_id=" ")
    approved = repo.approve_review(
        item.job_id,
        reviewer_id=" reviewer-1 ",
        reason="checked packet",
    )

    assert approved.status == JobStatus.SUCCEEDED
    assert approved.last_error is None
    action = approved.payload["last_review_action"]
    assert action["action"] == "approve"
    assert action["reviewer_id"] == "reviewer-1"
    assert action["reason"] == "checked packet"
    assert approved.payload["review_actions"] == [action]


def test_in_memory_review_queue_reviewer_rejects_and_requeues() -> None:
    review_status = _review_status("flood_failure.json")
    repo = InMemoryConnectorReviewQueueRepository()
    item = repo.enqueue_review_status(review_status)

    with pytest.raises(ValueError, match="reason is required"):
        repo.reject_review(item.job_id, reviewer_id="reviewer-1", reason=" ")
    rejected = repo.reject_review(
        item.job_id,
        reviewer_id="reviewer-1",
        reason="temporary source issue",
    )
    requeued = repo.requeue_failed(
        rejected.job_id,
        reviewer_id="reviewer-2",
        reason="retry source",
    )

    assert rejected.status == JobStatus.FAILED
    assert rejected.last_error == "temporary source issue"
    assert requeued.status == JobStatus.QUEUED
    assert requeued.last_error == "retry source"
    actions = requeued.payload["review_actions"]
    assert [action["action"] for action in actions] == ["reject", "requeue"]
    assert actions[-1]["reviewer_id"] == "reviewer-2"


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
    )

    assert requeued.status == JobStatus.QUEUED
    assert requeued.attempts == 1
    assert requeued.max_attempts == 2
    assert requeued.locked_by is None
    assert requeued.locked_at is None
    assert requeued.finished_at is None
    assert requeued.last_error == "retry after reviewer handoff"

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
    cancelled = repo.cancel(item.job_id, reason="review no longer required")

    assert cancelled.status == JobStatus.CANCELLED
    assert cancelled.finished_at is not None
    assert cancelled.last_error == "review no longer required"
    assert repo.lease_next(worker_id="worker-1") is None
    with pytest.raises(ValueError, match="cannot be cancelled"):
        repo.cancel(cancelled.job_id, reason="already cancelled")


def test_in_memory_review_queue_reviewer_cancel_records_action() -> None:
    review_status = _review_status("flood_failure.json")
    repo = InMemoryConnectorReviewQueueRepository()
    item = repo.enqueue_review_status(review_status)

    cancelled = repo.cancel(
        item.job_id,
        reviewer_id="reviewer-1",
        reason="duplicate packet",
    )

    assert cancelled.status == JobStatus.CANCELLED
    assert cancelled.last_error == "duplicate packet"
    action = cancelled.payload["last_review_action"]
    assert action["action"] == "cancel"
    assert action["reviewer_id"] == "reviewer-1"


def test_in_memory_review_queue_rejects_invalid_status_filter() -> None:
    repo = InMemoryConnectorReviewQueueRepository()

    with pytest.raises(ValueError, match="unsupported connector review queue status"):
        repo.list_connector_runs(status="not_a_status")


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
def test_sqlalchemy_review_queue_rejects_invalid_status_filter() -> None:
    engine = build_engine()

    with Session(engine) as session:
        repo = SqlAlchemyConnectorReviewQueueRepository(session)

        with pytest.raises(ValueError, match="unsupported connector review queue status"):
            repo.list_connector_runs(status="not_a_status")


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
            )

            assert requeued.status == JobStatus.QUEUED
            assert requeued.attempts == 1
            assert requeued.max_attempts == 2
            assert requeued.locked_by is None
            assert requeued.locked_at is None
            assert requeued.finished_at is None
            assert requeued.last_error == "retry after db reviewer handoff"

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
            )
            session.commit()

            assert cancelled.status == JobStatus.CANCELLED
            assert cancelled.finished_at is not None
            assert cancelled.last_error == "connector review superseded"
    finally:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            session.commit()


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_review_queue_reviewer_actions_update_payload() -> None:
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
            rejected = repo.reject_review(
                item.job_id,
                reviewer_id="reviewer-1",
                reason="temporary source issue",
            )
            requeued = repo.requeue_failed(
                rejected.job_id,
                reviewer_id="reviewer-2",
                reason="retry source",
            )
            session.commit()

            assert rejected.status == JobStatus.FAILED
            assert requeued.status == JobStatus.QUEUED
            assert requeued.last_error == "retry source"
            actions = requeued.payload["review_actions"]
            assert [action["action"] for action in actions] == ["reject", "requeue"]
            assert actions[-1]["reviewer_id"] == "reviewer-2"
    finally:
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_type = :job_type"),
                {"job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE},
            )
            session.commit()
