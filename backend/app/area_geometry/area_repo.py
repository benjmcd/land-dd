from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.area_contracts import AreaContract


class AreaRepository(Protocol):
    def add(self, area: AreaContract) -> AreaContract: ...

    def get(self, area_id: UUID) -> AreaContract | None: ...

    def list_all(self) -> list[AreaContract]: ...

    def exists(self, area_id: UUID) -> bool: ...


class InMemoryAreaRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, AreaContract] = {}

    def add(self, area: AreaContract) -> AreaContract:
        self._store[area.area_id] = area
        return area

    def get(self, area_id: UUID) -> AreaContract | None:
        return self._store.get(area_id)

    def list_all(self) -> list[AreaContract]:
        return list(self._store.values())

    def exists(self, area_id: UUID) -> bool:
        return area_id in self._store


__all__ = ["AreaRepository", "InMemoryAreaRepository"]
