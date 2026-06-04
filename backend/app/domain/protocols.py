"""Shared service protocols for cross-lane validation.

Lane C (evidence/claims) uses these to validate that source and area IDs reference
registered records, without importing Lane A or Lane B implementation code.
Lane D (reports) uses these to wire real implementations into Lane C's services.
"""
from __future__ import annotations

from typing import Protocol
from uuid import UUID


class SourceExistsProtocol(Protocol):
    def source_is_registered(self, source_id: UUID) -> bool: ...

    def source_production_use_allowed(self, source_id: UUID) -> bool: ...


class AreaExistsProtocol(Protocol):
    def area_is_registered(self, area_id: UUID) -> bool: ...
