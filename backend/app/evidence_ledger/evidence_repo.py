from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.enums import EvidenceType
from app.domain.evidence_contracts import EvidenceContract


class EvidenceRepository(Protocol):
    def add(self, evidence: EvidenceContract) -> EvidenceContract: ...

    def get(self, evidence_id: UUID) -> EvidenceContract | None: ...

    def exists(self, evidence_id: UUID) -> bool: ...

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]: ...

    def list_by_source(self, source_id: UUID) -> list[EvidenceContract]: ...

    def list_by_type(self, evidence_type: EvidenceType) -> list[EvidenceContract]: ...

    def list_all(self) -> list[EvidenceContract]: ...


class InMemoryEvidenceRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, EvidenceContract] = {}

    def add(self, evidence: EvidenceContract) -> EvidenceContract:
        if evidence.evidence_id in self._store:
            raise ValueError(f"Evidence '{evidence.evidence_id}' is already stored")
        self._store[evidence.evidence_id] = evidence
        return evidence

    def get(self, evidence_id: UUID) -> EvidenceContract | None:
        return self._store.get(evidence_id)

    def exists(self, evidence_id: UUID) -> bool:
        return evidence_id in self._store

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._store.values()
            if evidence.area_id == area_id
        ]

    def list_by_source(self, source_id: UUID) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._store.values()
            if evidence.source_id == source_id
        ]

    def list_by_type(self, evidence_type: EvidenceType) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._store.values()
            if evidence.evidence_type == evidence_type
        ]

    def list_all(self) -> list[EvidenceContract]:
        return list(self._store.values())


__all__ = ["EvidenceRepository", "InMemoryEvidenceRepository"]
