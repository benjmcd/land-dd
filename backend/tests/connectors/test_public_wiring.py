from __future__ import annotations

import inspect
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import app.connectors.public_wiring as public_wiring_module
from app.area_geometry.area_repo import SqlAlchemyAreaRepository
from app.area_geometry.service import AreaService
from app.connectors import (
    build_fixture_workflow_with_public_lane_services,
    build_fixture_workflow_with_public_services,
)
from app.db.engine import build_engine
from app.domain.area_contracts import AreaContract
from app.domain.enums import EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceContract,
    SourceDatasetContract,
    SourceDatasetVersionContract,
    SourceRetrievalRunContract,
)
from app.evidence_ledger.audit_log import SqlAlchemyEvidenceAuditLog
from app.evidence_ledger.evidence_repo import SqlAlchemyEvidenceRepository
from app.evidence_ledger.service import EvidenceService
from app.source_registry.provenance_repo import (
    InMemorySourceProvenanceRepository,
    SqlAlchemySourceProvenanceRepository,
)
from app.source_registry.provenance_service import SourceProvenanceService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import (
    InMemorySourceRepository,
    SqlAlchemySourceRepository,
)

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"
FIXTURE_SOURCE_ID = UUID("55555555-5555-4555-8555-555555555555")
FIXTURE_DATASET_ID = UUID("11111111-2222-4333-8444-555555555555")
FIXTURE_DATASET_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")
FIXTURE_INGEST_RUN_ID = UUID("11111111-1111-4111-8111-111111111111")
FIXTURE_FAILURE_INGEST_RUN_ID = UUID("66666666-6666-4666-8666-666666666666")
FIXTURE_AREA_ID = UUID("44444444-4444-4444-8444-444444444444")
FIXTURE_EVIDENCE_ID = UUID("33333333-3333-4333-8333-333333333333")
FIXTURE_FAILURE_EVIDENCE_ID = UUID("77777777-7777-4777-8777-777777777777")
FIXTURE_AREA_GEOMETRY: dict[str, object] = {
    "type": "Polygon",
    "coordinates": [
        [
            [-120.0, 38.0],
            [-119.9, 38.0],
            [-119.9, 38.1],
            [-120.0, 38.1],
            [-120.0, 38.0],
        ]
    ],
}


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
    def area_is_registered(
        self,
        area_id: UUID,
        *,
        workspace_id: UUID | None = None,
    ) -> bool:
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
            source_id=FIXTURE_SOURCE_ID,
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
        dataset_id=FIXTURE_DATASET_ID,
        source_id=FIXTURE_SOURCE_ID,
        dataset_name="Fixture Flood Dataset",
        domain="flood",
    )
    provenance_repo.add_dataset(dataset)
    provenance_repo.add_dataset_version(
        SourceDatasetVersionContract(
            dataset_version_id=FIXTURE_DATASET_VERSION_ID,
            dataset_id=dataset.dataset_id,
            version_label="fixture-2026-06-04",
        )
    )
    return provenance_service


def _db_public_lane_services(
    session: Session,
) -> tuple[SourceProvenanceService, EvidenceService]:
    source_service = SourceService(SqlAlchemySourceRepository(session))
    area_service = AreaService(SqlAlchemyAreaRepository(session))
    return (
        SourceProvenanceService(
            source_service=source_service,
            repo=SqlAlchemySourceProvenanceRepository(session),
        ),
        EvidenceService(
            SqlAlchemyEvidenceRepository(session),
            source_service,
            area_service,
            SqlAlchemyEvidenceAuditLog(session),
        ),
    )


def _seed_db_fixture_prerequisites(session: Session) -> None:
    source_service = SourceService(SqlAlchemySourceRepository(session))
    area_service = AreaService(SqlAlchemyAreaRepository(session))
    provenance_repo = SqlAlchemySourceProvenanceRepository(session)

    area_service.create(
        AreaContract(
            area_id=FIXTURE_AREA_ID,
            label="Connector DB smoke fixture area",
            geom_geojson=FIXTURE_AREA_GEOMETRY,
            geom_source="fixture",
            geom_validated=True,
        )
    )
    source_service.register(
        SourceContract(
            source_id=FIXTURE_SOURCE_ID,
            name=f"Fixture FEMA NFHL DB Smoke {uuid4()}",
            organization="FEMA fixture",
            domain="flood",
            geographic_scope="fixture",
            license_status="allowed",
            commercial_use_status="allowed",
            redistribution_status="allowed",
            cache_allowed="allowed",
            export_allowed="allowed",
            raw_data_allowed="allowed",
            ai_use_allowed="allowed",
            review_status="approved",
            metadata={"fixture_only": True},
        )
    )
    provenance_repo.add_dataset(
        SourceDatasetContract(
            dataset_id=FIXTURE_DATASET_ID,
            source_id=FIXTURE_SOURCE_ID,
            dataset_name="Fixture Flood Dataset",
            domain="flood",
            legal_caveat="Fixture-only flood screening; not a determination.",
        )
    )
    provenance_repo.add_dataset_version(
        SourceDatasetVersionContract(
            dataset_version_id=FIXTURE_DATASET_VERSION_ID,
            dataset_id=FIXTURE_DATASET_ID,
            version_label="fixture-2026-06-04",
            retrieved_at=datetime(2026, 6, 4, 9, 0, tzinfo=UTC),
            manifest={"fixture": "flood_success.json"},
            is_current=True,
        )
    )
    session.commit()


def _reset_db_fixture_rows(session: Session) -> None:
    session.execute(
        text(
            """
            DELETE FROM audit.events
            WHERE target_id IN (
                SELECT evidence_id
                FROM evidence.observations
                WHERE area_id = :area_id
            )
            """
        ),
        {"area_id": FIXTURE_AREA_ID},
    )
    session.execute(
        text("DELETE FROM evidence.observations WHERE area_id = :area_id"),
        {"area_id": FIXTURE_AREA_ID},
    )
    session.execute(
        text(
            """
            DELETE FROM source.ingest_runs
            WHERE ingest_run_id IN (:success_ingest_run_id, :failure_ingest_run_id)
            """
        ),
        {
            "success_ingest_run_id": FIXTURE_INGEST_RUN_ID,
            "failure_ingest_run_id": FIXTURE_FAILURE_INGEST_RUN_ID,
        },
    )
    session.execute(
        text(
            "DELETE FROM source.dataset_versions "
            "WHERE dataset_version_id = :dataset_version_id"
        ),
        {"dataset_version_id": FIXTURE_DATASET_VERSION_ID},
    )
    session.execute(
        text("DELETE FROM source.datasets WHERE dataset_id = :dataset_id"),
        {"dataset_id": FIXTURE_DATASET_ID},
    )
    session.execute(
        text("DELETE FROM source.sources WHERE source_id = :source_id"),
        {"source_id": FIXTURE_SOURCE_ID},
    )
    session.execute(
        text("DELETE FROM core.areas WHERE area_id = :area_id"),
        {"area_id": FIXTURE_AREA_ID},
    )
    session.commit()


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


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_backed_public_lane_service_fixture_workflow_is_idempotent() -> None:
    engine = build_engine()
    try:
        with Session(engine) as session:
            _reset_db_fixture_rows(session)
            _seed_db_fixture_prerequisites(session)
            source_provenance_service, evidence_service = _db_public_lane_services(
                session,
            )
            workflow = build_fixture_workflow_with_public_lane_services(
                source_provenance_service=source_provenance_service,
                evidence_service=evidence_service,
            )

            first = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")

            assert first.retrieval_provenance.recorded_run is not None
            assert (
                first.retrieval_provenance.recorded_run.ingest_run_id
                == FIXTURE_INGEST_RUN_ID
            )
            assert len(first.evidence_ingestion.created_evidence) == 1
            assert (
                first.evidence_ingestion.created_evidence[0].evidence_id
                == FIXTURE_EVIDENCE_ID
            )
            session.commit()

        with Session(engine) as session:
            source_provenance_service, evidence_service = _db_public_lane_services(
                session,
            )
            workflow = build_fixture_workflow_with_public_lane_services(
                source_provenance_service=source_provenance_service,
                evidence_service=evidence_service,
            )

            second = workflow.ingest_fixture(FIXTURE_DIR / "flood_success.json")
            stored_run = SqlAlchemySourceProvenanceRepository(session).get_retrieval_run(
                FIXTURE_INGEST_RUN_ID,
            )
            stored_evidence = evidence_service.get(FIXTURE_EVIDENCE_ID)
            audit_events = SqlAlchemyEvidenceAuditLog(session).list_by_evidence(
                FIXTURE_EVIDENCE_ID,
            )

            assert stored_run is not None
            assert stored_run.ingest_run_id == FIXTURE_INGEST_RUN_ID
            assert stored_evidence is not None
            assert stored_evidence.evidence_id == FIXTURE_EVIDENCE_ID
            assert audit_events
            assert second.retrieval_provenance.recorded_run is None
            assert second.retrieval_provenance.skipped_run == stored_run
            assert second.evidence_ingestion.created_evidence == ()
            assert second.evidence_ingestion.skipped_evidence == (
                second.connector_result.evidence_inputs[0],
            )
    finally:
        with Session(engine) as session:
            _reset_db_fixture_rows(session)


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_backed_public_lane_service_fixture_source_failure_is_idempotent() -> None:
    engine = build_engine()
    try:
        with Session(engine) as session:
            _reset_db_fixture_rows(session)
            _seed_db_fixture_prerequisites(session)
            source_provenance_service, evidence_service = _db_public_lane_services(
                session,
            )
            workflow = build_fixture_workflow_with_public_lane_services(
                source_provenance_service=source_provenance_service,
                evidence_service=evidence_service,
            )

            first = workflow.ingest_fixture(FIXTURE_DIR / "flood_failure.json")

            assert first.retrieval_provenance.recorded_run is not None
            assert (
                first.retrieval_provenance.recorded_run.ingest_run_id
                == FIXTURE_FAILURE_INGEST_RUN_ID
            )
            assert len(first.evidence_ingestion.created_evidence) == 1
            created_failure = first.evidence_ingestion.created_evidence[0]
            assert created_failure.evidence_id == FIXTURE_FAILURE_EVIDENCE_ID
            assert created_failure.is_source_failure is True
            assert created_failure.evidence_type == EvidenceType.SOURCE_FAILURE
            assert created_failure.evidence_code == "FLOOD_SOURCE_UNAVAILABLE"
            assert created_failure.observed_value == {
                "failure_reason": "fixture_source_unavailable",
                "error_message": "Fixture flood source unavailable.",
                "retryable": False,
            }
            session.commit()

        with Session(engine) as session:
            source_provenance_service, evidence_service = _db_public_lane_services(
                session,
            )
            workflow = build_fixture_workflow_with_public_lane_services(
                source_provenance_service=source_provenance_service,
                evidence_service=evidence_service,
            )

            second = workflow.ingest_fixture(FIXTURE_DIR / "flood_failure.json")
            stored_run = SqlAlchemySourceProvenanceRepository(session).get_retrieval_run(
                FIXTURE_FAILURE_INGEST_RUN_ID,
            )
            source_failures = [
                evidence
                for evidence in evidence_service.list_by_area(FIXTURE_AREA_ID)
                if evidence.is_source_failure
            ]

            assert stored_run is not None
            assert stored_run.ingest_run_id == FIXTURE_FAILURE_INGEST_RUN_ID
            assert stored_run.status == "blocked"
            assert len(source_failures) == 1
            assert source_failures[0].evidence_id == FIXTURE_FAILURE_EVIDENCE_ID
            assert source_failures[0].evidence_code == "FLOOD_SOURCE_UNAVAILABLE"
            assert source_failures[0].observed_value["failure_reason"] == (
                "fixture_source_unavailable"
            )
            assert SqlAlchemyEvidenceAuditLog(session).list_by_evidence(
                source_failures[0].evidence_id,
            )
            assert second.retrieval_provenance.recorded_run is None
            assert second.retrieval_provenance.skipped_run == stored_run
            assert second.evidence_ingestion.created_evidence == ()
            assert second.evidence_ingestion.skipped_evidence == (
                source_failures[0],
            )
    finally:
        with Session(engine) as session:
            _reset_db_fixture_rows(session)


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
