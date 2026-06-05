from __future__ import annotations

from uuid import UUID

from app.domain.source_contracts import SourceRetrievalRunContract
from app.evidence_ledger.service import EvidenceService
from app.source_registry.provenance_service import SourceProvenanceService

from .evidence_ingestion import ConnectorEvidenceIngestionAdapter
from .fixture_workflow import FixtureConnectorIngestWorkflow
from .flood_fixture import FixtureConnectorProtocol, StaticFloodFixtureConnector
from .retrieval_provenance import (
    ConnectorRetrievalProvenanceAdapter,
    SourceRetrievalProvenancePort,
)


class SourceProvenanceServiceRetrievalPort:
    def __init__(self, source_provenance_service: SourceProvenanceService) -> None:
        self._source_provenance_service = source_provenance_service

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        return self._source_provenance_service.retrieval_run_exists(ingest_run_id)

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        return self._source_provenance_service.record_retrieval_run_contract(
            retrieval_run,
        )


def build_fixture_workflow_with_public_services(
    *,
    retrieval_provenance_port: SourceRetrievalProvenancePort,
    evidence_service: EvidenceService,
    connector: FixtureConnectorProtocol | None = None,
) -> FixtureConnectorIngestWorkflow:
    _default: FixtureConnectorProtocol = StaticFloodFixtureConnector()
    resolved = connector if connector is not None else _default
    return FixtureConnectorIngestWorkflow(
        connector=resolved,
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            retrieval_provenance_port,
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(evidence_service),
    )


def build_fixture_workflow_with_public_lane_services(
    *,
    source_provenance_service: SourceProvenanceService,
    evidence_service: EvidenceService,
    connector: FixtureConnectorProtocol | None = None,
) -> FixtureConnectorIngestWorkflow:
    return build_fixture_workflow_with_public_services(
        retrieval_provenance_port=SourceProvenanceServiceRetrievalPort(
            source_provenance_service,
        ),
        evidence_service=evidence_service,
        connector=connector,
    )


__all__ = [
    "SourceProvenanceServiceRetrievalPort",
    "build_fixture_workflow_with_public_lane_services",
    "build_fixture_workflow_with_public_services",
]
