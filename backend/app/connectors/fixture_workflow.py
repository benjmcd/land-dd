from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .evidence_ingestion import (
    ConnectorEvidenceIngestionAdapter,
    ConnectorEvidenceIngestionResult,
)
from .fixture_quality import ConnectorFixtureQualityProfile, evaluate_flood_fixture_quality
from .flood_fixture import FixtureConnectorProtocol
from .result import ConnectorResult
from .retrieval_provenance import (
    ConnectorRetrievalProvenanceAdapter,
    ConnectorRetrievalProvenanceResult,
)


class FixtureConnectorIngestWorkflowError(ValueError):
    """Raised when a fixture run fails connector-owned quality checks."""


@dataclass(frozen=True)
class FixtureConnectorIngestWorkflowResult:
    connector_result: ConnectorResult
    retrieval_provenance: ConnectorRetrievalProvenanceResult
    evidence_ingestion: ConnectorEvidenceIngestionResult


class FixtureConnectorIngestWorkflow:
    def __init__(
        self,
        *,
        connector: FixtureConnectorProtocol,
        retrieval_provenance_adapter: ConnectorRetrievalProvenanceAdapter,
        evidence_ingestion_adapter: ConnectorEvidenceIngestionAdapter,
        quality_evaluator: Callable[
            [ConnectorResult],
            ConnectorFixtureQualityProfile,
        ] = evaluate_flood_fixture_quality,
    ) -> None:
        self._connector = connector
        self._retrieval_provenance_adapter = retrieval_provenance_adapter
        self._evidence_ingestion_adapter = evidence_ingestion_adapter
        self._quality_evaluator = quality_evaluator

    def ingest_fixture(
        self,
        fixture_path: str | Path,
    ) -> FixtureConnectorIngestWorkflowResult:
        connector_result = self._connector.load_fixture(fixture_path)
        quality = self._quality_evaluator(connector_result)
        if quality.blocking_issue_count:
            issue_codes = ", ".join(issue.code.value for issue in quality.issues)
            raise FixtureConnectorIngestWorkflowError(
                f"fixture quality gate failed: {issue_codes}",
            )
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
    "FixtureConnectorIngestWorkflowError",
    "FixtureConnectorIngestWorkflow",
    "FixtureConnectorIngestWorkflowResult",
]
