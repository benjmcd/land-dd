from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, cast
from uuid import UUID

from app.domain.source_contracts import SourceRetrievalRunContract

from .result import ConnectorResult


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
        connector_result: ConnectorResult,
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

        recorded = _record_retrieval_run(self._provenance_port, retrieval_run)
        return ConnectorRetrievalProvenanceResult(
            recorded_run=recorded,
            skipped_run=None,
        )


def _record_retrieval_run(
    provenance_port: SourceRetrievalProvenancePort,
    retrieval_run: SourceRetrievalRunContract,
) -> SourceRetrievalRunContract:
    contract_recorder = getattr(
        provenance_port,
        "record_retrieval_run_contract",
        None,
    )
    if callable(contract_recorder):
        return cast(
            SourceRetrievalRunContract,
            contract_recorder(retrieval_run),
        )
    return cast(
        SourceRetrievalRunContract,
        cast(Any, provenance_port).record_retrieval_run(retrieval_run),
    )


__all__ = [
    "ConnectorRetrievalProvenanceAdapter",
    "ConnectorRetrievalProvenanceResult",
    "SourceRetrievalProvenancePort",
]
