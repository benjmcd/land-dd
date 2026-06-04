from __future__ import annotations

from app.evidence_ledger.service import EvidenceService

from .evidence_ingestion import ConnectorEvidenceIngestionAdapter
from .fixture_workflow import FixtureConnectorIngestWorkflow
from .flood_fixture import StaticFloodFixtureConnector
from .retrieval_provenance import (
    ConnectorRetrievalProvenanceAdapter,
    SourceRetrievalProvenancePort,
)


def build_fixture_workflow_with_public_services(
    *,
    retrieval_provenance_port: SourceRetrievalProvenancePort,
    evidence_service: EvidenceService,
    connector: StaticFloodFixtureConnector | None = None,
) -> FixtureConnectorIngestWorkflow:
    return FixtureConnectorIngestWorkflow(
        connector=connector or StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            retrieval_provenance_port,
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(evidence_service),
    )


__all__ = ["build_fixture_workflow_with_public_services"]
