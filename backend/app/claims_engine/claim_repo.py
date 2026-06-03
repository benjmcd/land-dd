from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.claim_contracts import ClaimContract


class ClaimRepository(Protocol):
    def add(self, claim: ClaimContract) -> ClaimContract: ...

    def get(self, claim_id: UUID) -> ClaimContract | None: ...

    def exists(self, claim_id: UUID) -> bool: ...

    def list_by_area(self, area_id: UUID) -> list[ClaimContract]: ...

    def list_all(self) -> list[ClaimContract]: ...


class InMemoryClaimRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, ClaimContract] = {}

    def add(self, claim: ClaimContract) -> ClaimContract:
        if claim.claim_id in self._store:
            raise ValueError(f"Claim '{claim.claim_id}' is already stored")
        self._store[claim.claim_id] = claim
        return claim

    def get(self, claim_id: UUID) -> ClaimContract | None:
        return self._store.get(claim_id)

    def exists(self, claim_id: UUID) -> bool:
        return claim_id in self._store

    def list_by_area(self, area_id: UUID) -> list[ClaimContract]:
        return [
            claim
            for claim in self._store.values()
            if claim.area_id == area_id
        ]

    def list_all(self) -> list[ClaimContract]:
        return list(self._store.values())


__all__ = ["ClaimRepository", "InMemoryClaimRepository"]
