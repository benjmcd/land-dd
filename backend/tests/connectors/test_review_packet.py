from __future__ import annotations

import inspect
from pathlib import Path
from uuid import UUID

import app.connectors.review_packet as review_packet_module
from app.connectors import (
    ConnectorEvidenceIngestionAdapter,
    ConnectorRetrievalProvenanceAdapter,
    ConnectorReviewSignalCode,
    FixtureConnectorIngestWorkflow,
    StaticFloodFixtureConnector,
    build_connector_run_review_packet,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract, SourceRetrievalStatus

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class ReviewPacketRetrievalProvenancePort:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self._stored: dict[UUID, SourceRetrievalRunContract] = {}

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        self.events.append("retrieval_run_exists")
        return ingest_run_id in self._stored

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        self.events.append("record_retrieval_run")
        self._stored[retrieval_run.ingest_run_id] = retrieval_run
        return retrieval_run


class ReviewPacketEvidencePort:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self._stored: dict[UUID, EvidenceContract] = {}
        self._source_failure_counter = 1

    def create_observation(self, evidence: EvidenceContract) -> EvidenceContract:
        self.events.append("create_observation")
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
        self.events.append("create_source_failure")
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
        self.events.append("evidence_exists")
        return evidence_id in self._stored

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        self.events.append("list_by_area")
        return [
            evidence
            for evidence in self._stored.values()
            if evidence.area_id == area_id
        ]


def _workflow(
    *,
    retrieval_port: ReviewPacketRetrievalProvenancePort,
    evidence_port: ReviewPacketEvidencePort,
) -> FixtureConnectorIngestWorkflow:
    return FixtureConnectorIngestWorkflow(
        connector=StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            retrieval_port,
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(evidence_port),
    )


def test_review_packet_summarizes_successful_fixture_workflow() -> None:
    events: list[str] = []
    result = _workflow(
        retrieval_port=ReviewPacketRetrievalProvenancePort(events),
        evidence_port=ReviewPacketEvidencePort(events),
    ).ingest_fixture(FIXTURE_DIR / "flood_success.json")

    packet = build_connector_run_review_packet(result)

    assert packet.connector_name == "fixture_flood_static"
    assert packet.ingest_run_id == result.connector_result.retrieval_run.ingest_run_id
    assert packet.dataset_version_id == (
        result.connector_result.retrieval_run.dataset_version_id
    )
    assert packet.retrieval_status == SourceRetrievalStatus.SUCCEEDED
    assert packet.retrieval_recorded is True
    assert packet.retrieval_skipped is False
    assert packet.evidence_input_count == 1
    assert packet.evidence_created_count == 1
    assert packet.evidence_skipped_count == 0
    assert packet.source_failure_created_count == 0
    assert packet.source_failure_skipped_count == 0
    assert packet.created_evidence_ids == (
        result.evidence_ingestion.created_evidence[0].evidence_id,
    )
    assert packet.skipped_evidence_ids == ()
    assert packet.source_failure_evidence_ids == ()
    assert packet.review_required is False
    assert packet.signals == ()
    assert packet.human_review_tasks == (
        "Confirm connector provenance and evidence counts before promotion.",
        "Keep fixture-only connector evidence out of claims and reports until "
        "the next approved workflow gate.",
    )


def test_review_packet_flags_blocked_source_failure_workflow() -> None:
    events: list[str] = []
    result = _workflow(
        retrieval_port=ReviewPacketRetrievalProvenancePort(events),
        evidence_port=ReviewPacketEvidencePort(events),
    ).ingest_fixture(FIXTURE_DIR / "flood_failure.json")

    packet = build_connector_run_review_packet(result)

    assert packet.retrieval_status == SourceRetrievalStatus.BLOCKED
    assert packet.error_count == 1
    assert packet.evidence_created_count == 1
    assert packet.source_failure_created_count == 1
    assert packet.review_required is True
    assert packet.source_failure_evidence_ids == (
        result.evidence_ingestion.created_evidence[0].evidence_id,
    )
    assert tuple(signal.code for signal in packet.signals) == (
        ConnectorReviewSignalCode.RETRIEVAL_NOT_SUCCEEDED,
        ConnectorReviewSignalCode.RETRIEVAL_ERRORS_PRESENT,
        ConnectorReviewSignalCode.SOURCE_FAILURE_EVIDENCE_PRESENT,
    )
    assert all(signal.requires_human_review for signal in packet.signals)
    assert packet.human_review_tasks == (
        "Review connector retrieval status, error counts, warnings, and log URI.",
        "Confirm source-failure evidence before downstream claim or report use.",
        "Verify fixture evidence counts against the connector source manifest.",
    )


def test_review_packet_marks_repeated_fixture_run_as_idempotent_skip() -> None:
    events: list[str] = []
    retrieval_port = ReviewPacketRetrievalProvenancePort(events)
    evidence_port = ReviewPacketEvidencePort(events)
    workflow = _workflow(retrieval_port=retrieval_port, evidence_port=evidence_port)

    first = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")
    second = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")
    packet = build_connector_run_review_packet(second)

    assert packet.retrieval_recorded is False
    assert packet.retrieval_skipped is True
    assert packet.evidence_created_count == 0
    assert packet.evidence_skipped_count == 1
    assert packet.created_evidence_ids == ()
    assert packet.skipped_evidence_ids == (
        first.evidence_ingestion.created_evidence[0].evidence_id,
    )
    assert packet.review_required is False
    assert tuple(signal.code for signal in packet.signals) == (
        ConnectorReviewSignalCode.IDEMPOTENT_SKIP_OBSERVED,
    )
    assert packet.signals[0].requires_human_review is False


def test_review_packet_stays_connector_owned_and_before_api_reports() -> None:
    source = inspect.getsource(review_packet_module)

    assert "app.source_registry" not in source
    assert "app.evidence_ledger" not in source
    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "app.api" not in source
    assert "app.db" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
