from __future__ import annotations

import inspect
from pathlib import Path
from uuid import UUID

import app.connectors.review_handoff as review_handoff_module
from app.connectors import (
    ConnectorEvidenceIngestionAdapter,
    ConnectorRetrievalProvenanceAdapter,
    ConnectorReviewDisposition,
    ConnectorReviewPriority,
    FixtureConnectorIngestWorkflow,
    StaticFloodFixtureConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class HandoffRetrievalProvenancePort:
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


class HandoffEvidencePort:
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


def _workflow(
    *,
    retrieval_port: HandoffRetrievalProvenancePort,
    evidence_port: HandoffEvidencePort,
) -> FixtureConnectorIngestWorkflow:
    return FixtureConnectorIngestWorkflow(
        connector=StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            retrieval_port,
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(evidence_port),
    )


def test_review_handoff_marks_success_packet_ready_for_connector_qa() -> None:
    result = _workflow(
        retrieval_port=HandoffRetrievalProvenancePort(),
        evidence_port=HandoffEvidencePort(),
    ).ingest_fixture(FIXTURE_DIR / "flood_success.json")
    packet = build_connector_run_review_packet(result)

    handoff = build_connector_review_handoff(packet)
    record = handoff.to_review_record()

    assert handoff.disposition == ConnectorReviewDisposition.READY_FOR_CONNECTOR_QA
    assert handoff.priority == ConnectorReviewPriority.NORMAL
    assert handoff.queue_name == "connector-quality-review"
    assert handoff.tasks == packet.human_review_tasks
    assert handoff.signal_codes == ()
    assert record["disposition"] == "ready_for_connector_qa"
    assert record["ingest_run_id"] == str(packet.ingest_run_id)
    assert record["area_id"] == str(packet.area_id)
    assert record["review_required"] is False


def test_review_handoff_routes_source_failure_packet_to_human_review() -> None:
    result = _workflow(
        retrieval_port=HandoffRetrievalProvenancePort(),
        evidence_port=HandoffEvidencePort(),
    ).ingest_fixture(FIXTURE_DIR / "flood_failure.json")
    packet = build_connector_run_review_packet(result)

    handoff = build_connector_review_handoff(packet)
    record = handoff.to_review_record()

    assert handoff.disposition == ConnectorReviewDisposition.NEEDS_HUMAN_REVIEW
    assert handoff.priority == ConnectorReviewPriority.HIGH
    assert handoff.queue_name == "connector-human-review"
    assert record["review_required"] is True
    assert record["signal_codes"] == (
        "retrieval_not_succeeded",
        "retrieval_errors_present",
        "source_failure_evidence_present",
    )
    assert "blocked" in handoff.title
    assert "source failures observed" in handoff.summary


def test_review_handoff_routes_repeated_fixture_to_idempotency_log() -> None:
    retrieval_port = HandoffRetrievalProvenancePort()
    evidence_port = HandoffEvidencePort()
    workflow = _workflow(retrieval_port=retrieval_port, evidence_port=evidence_port)

    workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")
    repeated = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")
    packet = build_connector_run_review_packet(repeated)

    handoff = build_connector_review_handoff(packet)
    record = handoff.to_review_record()

    assert handoff.disposition == ConnectorReviewDisposition.IDEMPOTENT_NOOP
    assert handoff.priority == ConnectorReviewPriority.NORMAL
    assert handoff.queue_name == "connector-idempotency-log"
    assert record["evidence_created_count"] == 0
    assert record["evidence_skipped_count"] == 1
    assert record["signal_codes"] == ("idempotent_skip_observed",)


def test_review_handoff_stays_connector_owned_and_before_api_persistence() -> None:
    source = inspect.getsource(review_handoff_module)

    assert "app.source_registry" not in source
    assert "app.evidence_ledger" not in source
    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "app.api" not in source
    assert "app.db" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
