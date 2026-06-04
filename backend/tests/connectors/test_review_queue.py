from __future__ import annotations

import os
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
            evidence_id=UUID(int=self._source_failure_counter),
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
