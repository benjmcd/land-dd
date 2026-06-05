from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.source_contracts import SourceRetrievalRunContract

from .flood_fixture import FixtureConnectorResultProtocol


class SourceRetrievalProvenancePort(Protocol):
    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool: ...

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract: ...


@dataclass(frozen=True)
class ConnectorRetrievalProvenanceResult:
    recorded_run: SourceRetrievalRunContract | None
    skipped_run: SourceRetrievalRunContract | None


class ConnectorRetrievalProvenanceAdapter:
    def __init__(self, provenance_port: SourceRetrievalProvenancePort) -> None:
        self._provenance_port = provenance_port

    def record(
        self,
        connector_result: FixtureConnectorResultProtocol,
    ) -> ConnectorRetrievalProvenanceResult:
        return self.record_retrieval_run(connector_result.retrieval_run)

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> ConnectorRetrievalProvenanceResult:
        if self._provenance_port.retrieval_run_exists(retrieval_run.ingest_run_id):
            return ConnectorRetrievalProvenanceResult(
                recorded_run=None,
                skipped_run=retrieval_run,
            )

        recorded = self._provenance_port.record_retrieval_run(retrieval_run)
        return ConnectorRetrievalProvenanceResult(
            recorded_run=recorded,
            skipped_run=None,
        )


__all__ = [
    "ConnectorRetrievalProvenanceAdapter",
    "ConnectorRetrievalProvenanceResult",
    "SourceRetrievalProvenancePort",
]
