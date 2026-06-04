from __future__ import annotations

from uuid import UUID

from app.domain.protocols import AreaExistsProtocol, SourceExistsProtocol


class SourceServiceProtocolAdapter:
    def __init__(self, source_service: SourceExistsProtocol) -> None:
        self._source_service = source_service

    def source_is_registered(self, source_id: UUID) -> bool:
        return self._source_service.source_is_registered(source_id)

    def source_production_use_allowed(self, source_id: UUID) -> bool:
        return self._source_service.source_production_use_allowed(source_id)


class AreaServiceProtocolAdapter:
    def __init__(self, area_service: AreaExistsProtocol) -> None:
        self._area_service = area_service

    def area_is_registered(self, area_id: UUID) -> bool:
        return self._area_service.area_is_registered(area_id)


__all__ = ["AreaServiceProtocolAdapter", "SourceServiceProtocolAdapter"]
