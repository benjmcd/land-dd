from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.connectors import (
    CONNECTOR_REVIEW_STATUS_JOB_TYPE,
    ConnectorEvidenceIngestionAdapter,
    ConnectorRetrievalProvenanceAdapter,
    ConnectorRunReviewStatus,
    FixtureConnectorIngestWorkflow,
    SqlAlchemyConnectorReviewQueueRepository,
    StaticFloodFixtureConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
    evaluate_flood_fixture_quality,
)
from app.core.config import Settings
from app.db.engine import build_engine
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class DbApiQueueRetrievalPort:
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


class DbApiQueueEvidencePort:
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


def _review_status() -> ConnectorRunReviewStatus:
    workflow = FixtureConnectorIngestWorkflow(
        connector=StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            DbApiQueueRetrievalPort(),
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(
            DbApiQueueEvidencePort(),
        ),
    )
    result = workflow.ingest_fixture(FIXTURE_DIR / "flood_failure.json")
    packet = build_connector_run_review_packet(result)
    return build_connector_run_review_status(
        build_connector_review_handoff(packet),
        evaluate_flood_fixture_quality(result.connector_result),
    )


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_connector_review_queue_endpoint_reads_persisted_queue_item(
    tmp_path: Path,
) -> None:
    engine = build_engine()
    review_status = _review_status()
    ingest_run_id = review_status.handoff.packet.ingest_run_id
    idempotency_key = f"{CONNECTOR_REVIEW_STATUS_JOB_TYPE}:{ingest_run_id}"
    app = create_app(
        settings=Settings(OBJECT_STORE_ROOT=str(tmp_path / "object-store")),
        use_db_services=True,
    )
    client = TestClient(app)

    try:
        with Session(engine) as session:
            session.execute(
                text(
                    "DELETE FROM jobs.job_queue "
                    "WHERE idempotency_key = :idempotency_key"
                ),
                {"idempotency_key": idempotency_key},
            )
            SqlAlchemyConnectorReviewQueueRepository(session).enqueue_review_status(
                review_status,
            )
            session.commit()

        response = client.get(f"/connector-runs/{ingest_run_id}/review-queue")

        assert response.status_code == 200
        record = response.json()
        assert record["ingest_run_id"] == str(ingest_run_id)
        assert record["job_type"] == CONNECTOR_REVIEW_STATUS_JOB_TYPE
        assert record["status"] == "needs_review"
        assert record["priority"] == 10
        assert record["idempotency_key"] == idempotency_key
        assert record["payload"]["ingest_run_id"] == str(ingest_run_id)
        assert record["attempts"] == 0
        assert record["max_attempts"] == 1
        assert record["locked_by"] is None
        assert record["locked_at"] is None
        assert record["started_at"] is None
        assert record["finished_at"] is None
        assert record["last_error"] is None
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
def test_db_connector_review_queue_endpoint_surfaces_worker_state(
    tmp_path: Path,
) -> None:
    engine = build_engine()
    review_status = _review_status()
    ingest_run_id = review_status.handoff.packet.ingest_run_id
    idempotency_key = f"{CONNECTOR_REVIEW_STATUS_JOB_TYPE}:{ingest_run_id}"
    app = create_app(
        settings=Settings(OBJECT_STORE_ROOT=str(tmp_path / "object-store")),
        use_db_services=True,
    )
    client = TestClient(app)

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
            repo.enqueue_review_status(review_status)
            leased = repo.lease_next(worker_id="db-api-worker")
            assert leased is not None
            repo.mark_failed(leased.job_id, error="review packet rejected")
            session.commit()

        response = client.get(f"/connector-runs/{ingest_run_id}/review-queue")

        assert response.status_code == 200
        record = response.json()
        assert record["ingest_run_id"] == str(ingest_run_id)
        assert record["job_type"] == CONNECTOR_REVIEW_STATUS_JOB_TYPE
        assert record["status"] == "failed"
        assert record["attempts"] == 1
        assert record["max_attempts"] == 1
        assert record["locked_by"] == "db-api-worker"
        assert record["locked_at"] is not None
        assert record["started_at"] is not None
        assert record["finished_at"] is not None
        assert record["last_error"] == "review packet rejected"
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
