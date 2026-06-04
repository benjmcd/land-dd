from __future__ import annotations

import inspect
from pathlib import Path
from uuid import UUID

import app.connectors.fixture_workflow as fixture_workflow_module
from app.connectors import (
    ConnectorEvidenceIngestionAdapter,
    ConnectorRetrievalProvenanceAdapter,
    FixtureConnectorIngestWorkflow,
    StaticFloodFixtureConnector,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class WorkflowRetrievalProvenancePort:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.recorded_runs: list[SourceRetrievalRunContract] = []
        self._stored: dict[UUID, SourceRetrievalRunContract] = {}

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        self.events.append("retrieval_run_exists")
        return ingest_run_id in self._stored

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        self.events.append("record_retrieval_run")
        self.recorded_runs.append(retrieval_run)
        self._stored[retrieval_run.ingest_run_id] = retrieval_run
        return retrieval_run


class WorkflowEvidencePort:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.created_observations: list[EvidenceContract] = []
        self.source_failure_calls: list[dict[str, object]] = []
        self._stored: dict[UUID, EvidenceContract] = {}
        self._source_failure_counter = 1

    def create_observation(self, evidence: EvidenceContract) -> EvidenceContract:
        self.events.append("create_observation")
        self.created_observations.append(evidence)
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
        self.events.append("create_source_failure")
        self.source_failure_calls.append(
            {
                "area_id": area_id,
                "source_id": source_id,
                "method_code": method_code,
                "caveat": caveat,
                "evidence_code": evidence_code,
                "domain": domain,
                "observation": observation,
                "observed_value": observed_value,
            }
        )
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
    retrieval_port: WorkflowRetrievalProvenancePort,
    evidence_port: WorkflowEvidencePort,
) -> FixtureConnectorIngestWorkflow:
    return FixtureConnectorIngestWorkflow(
        connector=StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            retrieval_port,
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(evidence_port),
    )


def test_fixture_workflow_records_retrieval_before_evidence_ingestion() -> None:
    events: list[str] = []
    retrieval_port = WorkflowRetrievalProvenancePort(events)
    evidence_port = WorkflowEvidencePort(events)

    result = _workflow(
        retrieval_port=retrieval_port,
        evidence_port=evidence_port,
    ).ingest_fixture(FIXTURE_DIR / "flood_success.json")

    assert events == [
        "retrieval_run_exists",
        "record_retrieval_run",
        "evidence_exists",
        "create_observation",
    ]
    assert retrieval_port.recorded_runs == [result.connector_result.retrieval_run]
    assert tuple(evidence_port.created_observations) == (
        result.evidence_ingestion.created_evidence
    )
    assert result.retrieval_provenance.recorded_run == result.connector_result.retrieval_run
    assert result.evidence_ingestion.created_evidence == result.connector_result.evidence_inputs


def test_fixture_workflow_routes_source_failure_after_blocked_retrieval() -> None:
    events: list[str] = []
    retrieval_port = WorkflowRetrievalProvenancePort(events)
    evidence_port = WorkflowEvidencePort(events)

    result = _workflow(
        retrieval_port=retrieval_port,
        evidence_port=evidence_port,
    ).ingest_fixture(FIXTURE_DIR / "flood_failure.json")

    assert events == [
        "retrieval_run_exists",
        "record_retrieval_run",
        "evidence_exists",
        "list_by_area",
        "create_source_failure",
    ]
    assert result.retrieval_provenance.recorded_run == result.connector_result.retrieval_run
    assert len(evidence_port.source_failure_calls) == 1
    assert result.evidence_ingestion.created_evidence[0].is_source_failure is True


def test_fixture_workflow_is_idempotent_for_repeated_fixture_runs() -> None:
    events: list[str] = []
    retrieval_port = WorkflowRetrievalProvenancePort(events)
    evidence_port = WorkflowEvidencePort(events)
    workflow = _workflow(
        retrieval_port=retrieval_port,
        evidence_port=evidence_port,
    )

    first = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")
    second = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")

    assert retrieval_port.recorded_runs == [first.connector_result.retrieval_run]
    assert tuple(evidence_port.created_observations) == (
        first.evidence_ingestion.created_evidence
    )
    assert second.retrieval_provenance.recorded_run is None
    assert second.retrieval_provenance.skipped_run == first.connector_result.retrieval_run
    assert second.evidence_ingestion.created_evidence == ()
    assert second.evidence_ingestion.skipped_evidence == first.connector_result.evidence_inputs


def test_fixture_workflow_stays_connector_owned_and_fixture_only() -> None:
    source = inspect.getsource(fixture_workflow_module)

    assert "app.source_registry" not in source
    assert "app.evidence_ledger" not in source
    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
