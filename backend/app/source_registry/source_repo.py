from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.source_contracts import SourceContract


class SourceRepository(Protocol):
    def add(self, source: SourceContract) -> SourceContract: ...

    def get(self, source_id: UUID) -> SourceContract | None: ...

    def list_all(self) -> list[SourceContract]: ...

    def exists_by_name_org(self, name: str, organization: str | None) -> bool: ...


class InMemorySourceRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, SourceContract] = {}

    def add(self, source: SourceContract) -> SourceContract:
        self._store[source.source_id] = source
        return source

    def get(self, source_id: UUID) -> SourceContract | None:
        return self._store.get(source_id)

    def list_all(self) -> list[SourceContract]:
        return list(self._store.values())

    def exists_by_name_org(self, name: str, organization: str | None) -> bool:
        return any(
            s.name == name and s.organization == organization
            for s in self._store.values()
        )
