from __future__ import annotations

import inspect
from pathlib import Path
from uuid import UUID

import app.connectors.public_wiring as public_wiring_module
from app.connectors import (
    build_fixture_workflow_with_public_lane_services,
    build_fixture_workflow_with_public_services,
)
from app.domain.enums import EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceContract,
    SourceDatasetContract,
    SourceDatasetVersionContract,
    SourceRetrievalRunContract,
)
from app.evidence_ledger.service import EvidenceService
from app.source_registry.provenance_repo import InMemorySourceProvenanceRepository
from app.source_registry.provenance_service import SourceProvenanceService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class PublicWiringRetrievalPort:
    def __init__(self) -> None:
        self.recorded_runs: list[SourceRetrievalRunContract] = []
        self._stored: dict[UUID, SourceRetrievalRunContract] = {}

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        return ingest_run_id in self._stored

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        self.recorded_runs.append(retrieval_run)
        self._stored[retrieval_run.ingest_run_id] = retrieval_run
        return retrieval_run


class PublicWiringEvidenceRepository:
    def __init__(self) -> None:
        self._stored: dict[UUID, EvidenceContract] = {}

    def add(self, evidence: EvidenceContract) -> EvidenceContract:
        if evidence.evidence_id in self._stored:
            raise ValueError(f"Evidence '{evidence.evidence_id}' is already stored")
        self._stored[evidence.evidence_id] = evidence
        return evidence

    def get(self, evidence_id: UUID) -> EvidenceContract | None:
        return self._stored.get(evidence_id)

    def exists(self, evidence_id: UUID) -> bool:
        return evidence_id in self._stored

    def mark_superseded(
        self,
        evidence_id: UUID,
        superseded_by: UUID,
    ) -> EvidenceContract:
        evidence = self._stored[evidence_id].model_copy(
            update={"superseded_by": superseded_by},
        )
        self._stored[evidence_id] = evidence
        return evidence

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._stored.values()
            if evidence.area_id == area_id
        ]

    def list_by_source(self, source_id: UUID) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._stored.values()
            if evidence.source_id == source_id
        ]

    def list_by_type(self, evidence_type: EvidenceType) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._stored.values()
            if evidence.evidence_type == evidence_type
        ]

    def list_all(self) -> list[EvidenceContract]:
        return list(self._stored.values())


class PublicWiringSourceChecker:
    def source_is_registered(self, source_id: UUID) -> bool:
        return True

    def source_production_use_allowed(self, source_id: UUID) -> bool:
        return True


class PublicWiringAreaChecker:
    def area_is_registered(self, area_id: UUID) -> bool:
        return True


def _evidence_service() -> EvidenceService:
    return EvidenceService(
        PublicWiringEvidenceRepository(),
        PublicWiringSourceChecker(),
        PublicWiringAreaChecker(),
    )


def _source_provenance_service_for_fixture() -> SourceProvenanceService:
    source_repo = InMemorySourceRepository()
    source_service = SourceService(source_repo)
    source_service.register(
        SourceContract(
            source_id=UUID("55555555-5555-4555-8555-555555555555"),
            name="Fixture FEMA NFHL",
            organization="FEMA",
            domain="flood",
        )
    )
    provenance_repo = InMemorySourceProvenanceRepository()
    provenance_service = SourceProvenanceService(
        source_service=source_service,
        repo=provenance_repo,
    )
    dataset = SourceDatasetContract(
        dataset_id=UUID("11111111-2222-4333-8444-555555555555"),
        source_id=UUID("55555555-5555-4555-8555-555555555555"),
        dataset_name="Fixture Flood Dataset",
        domain="flood",
    )
    provenance_repo.add_dataset(dataset)
    provenance_repo.add_dataset_version(
        SourceDatasetVersionContract(
            dataset_version_id=UUID("22222222-2222-4222-8222-222222222222"),
            dataset_id=dataset.dataset_id,
            version_label="fixture-2026-06-04",
        )
    )
    return provenance_service


def test_public_wiring_uses_lane_c_evidence_service_for_normal_evidence() -> None:
    retrieval_port = PublicWiringRetrievalPort()
    workflow = build_fixture_workflow_with_public_services(
        retrieval_provenance_port=retrieval_port,
        evidence_service=_evidence_service(),
    )

    first = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")
    second = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")

    assert retrieval_port.recorded_runs == [first.connector_result.retrieval_run]
    assert first.evidence_ingestion.created_evidence == first.connector_result.evidence_inputs
    assert second.retrieval_provenance.recorded_run is None
    assert second.evidence_ingestion.created_evidence == ()
    assert second.evidence_ingestion.skipped_evidence == first.connector_result.evidence_inputs


def test_public_lane_service_wiring_preserves_retrieval_run_identity() -> None:
    source_provenance_service = _source_provenance_service_for_fixture()
    workflow = build_fixture_workflow_with_public_lane_services(
        source_provenance_service=source_provenance_service,
        evidence_service=_evidence_service(),
    )

    first = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")
    second = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")

    assert first.retrieval_provenance.recorded_run is not None
    assert (
        first.retrieval_provenance.recorded_run.ingest_run_id
        == first.connector_result.retrieval_run.ingest_run_id
    )
    assert second.retrieval_provenance.recorded_run is None
    assert second.retrieval_provenance.skipped_run == first.connector_result.retrieval_run


def test_public_wiring_uses_lane_c_evidence_service_for_source_failures() -> None:
    retrieval_port = PublicWiringRetrievalPort()
    workflow = build_fixture_workflow_with_public_services(
        retrieval_provenance_port=retrieval_port,
        evidence_service=_evidence_service(),
    )

    first = workflow.ingest_fixture(FIXTURE_DIR / "flood_failure.json")
    second = workflow.ingest_fixture(FIXTURE_DIR / "flood_failure.json")

    assert retrieval_port.recorded_runs == [first.connector_result.retrieval_run]
    assert first.evidence_ingestion.created_evidence[0].is_source_failure is True
    assert second.retrieval_provenance.recorded_run is None
    assert second.evidence_ingestion.created_evidence == ()
    assert second.evidence_ingestion.skipped_evidence == first.evidence_ingestion.created_evidence


def test_public_wiring_keeps_lane_a_identity_preservation_explicit() -> None:
    signature = inspect.signature(build_fixture_workflow_with_public_services)

    assert "retrieval_provenance_port" in signature.parameters
    assert "evidence_service" in signature.parameters


def test_public_wiring_uses_public_services_without_repositories_or_live_io() -> None:
    source = inspect.getsource(public_wiring_module)

    assert "app.evidence_ledger.service" in source
    assert "app.source_registry.provenance_service" in source
    assert "app.evidence_ledger.evidence_repo" not in source
    assert "app.source_registry.provenance_repo" not in source
    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
