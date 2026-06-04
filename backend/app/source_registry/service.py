from __future__ import annotations

from uuid import UUID

from app.domain.source_contracts import SourceContract
from app.source_registry.source_repo import SourceRepository

_ALLOWED_REVIEW_STATUSES = {"approved", "approved-with-restrictions"}
_ALLOWED_USAGE_STATUSES = {"yes", "allowed", "approved", "approved-with-restrictions", "restricted"}

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

    def source_is_registered(self, source_id: UUID) -> bool:
        return self._repo.get(source_id) is not None

    def source_production_use_allowed(self, source_id: UUID) -> bool:
        source = self._repo.get(source_id)
        if source is None:
            return False
        usage_statuses = (
            source.license_status,
            source.commercial_use_status,
            source.redistribution_status,
            source.cache_allowed,
            source.export_allowed,
            source.raw_data_allowed,
            source.ai_use_allowed,
        )
        return (
            _status_allows(source.review_status, _ALLOWED_REVIEW_STATUSES)
            and all(
                _status_allows(status, _ALLOWED_USAGE_STATUSES)
                for status in usage_statuses
            )
        )


def _status_allows(status: str, allowed_values: set[str]) -> bool:
    return status.strip().lower() in allowed_values
