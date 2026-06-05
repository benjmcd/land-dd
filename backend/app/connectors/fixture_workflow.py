from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .evidence_ingestion import (
    ConnectorEvidenceIngestionAdapter,
    ConnectorEvidenceIngestionResult,
)
from .flood_fixture import FixtureConnectorProtocol, FixtureConnectorResultProtocol
from .retrieval_provenance import (
    ConnectorRetrievalProvenanceAdapter,
    ConnectorRetrievalProvenanceResult,
)


@dataclass(frozen=True)
class FixtureConnectorIngestWorkflowResult:
    connector_result: FixtureConnectorResultProtocol
    retrieval_provenance: ConnectorRetrievalProvenanceResult
    evidence_ingestion: ConnectorEvidenceIngestionResult


class FixtureConnectorIngestWorkflow:
    def __init__(
        self,
        *,
        connector: FixtureConnectorProtocol,
        retrieval_provenance_adapter: ConnectorRetrievalProvenanceAdapter,
        evidence_ingestion_adapter: ConnectorEvidenceIngestionAdapter,
    ) -> None:
        self._connector = connector
        self._retrieval_provenance_adapter = retrieval_provenance_adapter
        self._evidence_ingestion_adapter = evidence_ingestion_adapter

    def ingest_fixture(
        self,
        fixture_path: str | Path,
    ) -> FixtureConnectorIngestWorkflowResult:
        connector_result = self._connector.load_fixture(fixture_path)
        retrieval_provenance = self._retrieval_provenance_adapter.record(
            connector_result,
        )
        evidence_ingestion = self._evidence_ingestion_adapter.ingest(connector_result)
        return FixtureConnectorIngestWorkflowResult(
            connector_result=connector_result,
            retrieval_provenance=retrieval_provenance,
            evidence_ingestion=evidence_ingestion,
        )


__all__ = [
    "FixtureConnectorIngestWorkflow",
    "FixtureConnectorIngestWorkflowResult",
]
