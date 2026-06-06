from __future__ import annotations

from typing import Final

from app.domain.source_contracts import SourceContract

ALLOWED_REVIEW_STATUSES: Final[frozenset[str]] = frozenset(
    {"approved", "approved-with-restrictions"}
)
ALLOWED_USAGE_STATUSES: Final[frozenset[str]] = frozenset(
    {"yes", "allowed", "approved", "approved-with-restrictions", "restricted"}
)
PRODUCTION_USAGE_FIELDS: Final[tuple[str, ...]] = (
    "license_status",
    "commercial_use_status",
    "redistribution_status",
    "cache_allowed",
    "export_allowed",
    "raw_data_allowed",
    "ai_use_allowed",
)


def source_production_use_allowed(source: SourceContract) -> bool:
    return source_production_use_blocking_fields(source) == ()


def source_production_use_blocking_fields(source: SourceContract) -> tuple[str, ...]:
    blocked_fields: list[str] = []
    if not _status_allows(source.review_status, ALLOWED_REVIEW_STATUSES):
        blocked_fields.append("review_status")
    for field_name in PRODUCTION_USAGE_FIELDS:
        status = getattr(source, field_name)
        if not isinstance(status, str) or not _status_allows(
            status, ALLOWED_USAGE_STATUSES
        ):
            blocked_fields.append(field_name)
    return tuple(blocked_fields)


def _status_allows(status: str, allowed_values: frozenset[str]) -> bool:
    return status.strip().lower() in allowed_values
