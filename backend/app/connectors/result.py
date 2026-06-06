from __future__ import annotations

from typing import Protocol

from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract


class ConnectorResult(Protocol):
    @property
    def retrieval_run(self) -> SourceRetrievalRunContract: ...

    @property
    def evidence_inputs(self) -> tuple[EvidenceContract, ...]: ...


__all__ = ["ConnectorResult"]
