from __future__ import annotations

from uuid import UUID

from app.domain.source_contracts import SourceContract
from app.source_registry.source_repo import SourceRepository


class SourceService:
    def __init__(self, repo: SourceRepository) -> None:
        self._repo = repo

    def register(self, source: SourceContract) -> SourceContract:
        if self._repo.exists_by_name_org(source.name, source.organization):
            raise ValueError(
                f"Source '{source.name}' / '{source.organization}' is already registered"
            )
        return self._repo.add(source)

    def get(self, source_id: UUID) -> SourceContract | None:
        return self._repo.get(source_id)

    def list_all(self) -> list[SourceContract]:
        return self._repo.list_all()
