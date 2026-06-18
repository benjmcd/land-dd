from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Final

from app.domain.evidence_contracts import EvidenceContract
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
RESTRICTED_REPORT_EXPOSURE_STATUSES: Final[frozenset[str]] = frozenset(
    {"restricted", "approved-with-restrictions"}
)
REPORT_EXPOSURE_SENSITIVE_KEY_FRAGMENTS: Final[tuple[str, ...]] = (
    "owner",
    "pii",
    "valuation",
    "assessed",
    "assessment",
    "appraisal",
    "appraised_value",
    "bldg_value",
    "building_value",
    "improvement_value",
    "land_value",
    "market_value",
    "property_value",
    "tax_value",
    "taxable_value",
    "total_value",
    "mailing",
    "situs",
    "address",
    "sale",
    "sold",
    "comps",
    "comparable",
    "raw",
    "vendor",
    "taxpayer",
    "phone",
    "email",
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


def source_report_exposure_allowed(
    source: SourceContract,
    evidence: EvidenceContract,
) -> bool:
    return source_report_exposure_blocking_fields(source, evidence) == ()


def source_report_exposure_blocking_fields(
    source: SourceContract,
    evidence: EvidenceContract,
) -> tuple[str, ...]:
    blocked_fields: list[str] = []
    sensitive_fields = source_report_exposure_sensitive_fields(evidence)

    if source.source_id != evidence.source_id:
        blocked_fields.append("source_id")

    if evidence.is_source_failure:
        return (*blocked_fields, *_observed_value_field_names(sensitive_fields))

    blocked_fields.extend(source_production_use_blocking_fields(source))
    if _source_has_restricted_report_exposure(source):
        blocked_fields.extend(_observed_value_field_names(sensitive_fields))
    return tuple(blocked_fields)


def source_report_exposure_sensitive_fields(
    evidence: EvidenceContract,
) -> tuple[str, ...]:
    return tuple(sorted(_sensitive_observed_value_paths(evidence.observed_value)))


def _status_allows(status: str, allowed_values: frozenset[str]) -> bool:
    return status.strip().lower() in allowed_values


def _source_has_restricted_report_exposure(source: SourceContract) -> bool:
    statuses = [
        source.review_status,
        *(getattr(source, field) for field in PRODUCTION_USAGE_FIELDS),
    ]
    return any(
        isinstance(status, str)
        and _status_allows(status, RESTRICTED_REPORT_EXPOSURE_STATUSES)
        for status in statuses
    )


def _is_sensitive_report_exposure_key(key: str) -> bool:
    normalized = _normalize_observed_value_key(key)
    return any(fragment in normalized for fragment in REPORT_EXPOSURE_SENSITIVE_KEY_FRAGMENTS)


def _normalize_observed_value_key(key: str) -> str:
    normalized = key.strip()
    normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", normalized)
    normalized = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", normalized)
    return normalized.lower().replace("-", "_").replace(" ", "_")


def _sensitive_observed_value_paths(
    value: object,
    *,
    path: str = "",
) -> set[str]:
    sensitive_paths: set[str] = set()
    if isinstance(value, Mapping):
        for raw_key, nested_value in value.items():
            key = str(raw_key)
            nested_path = f"{path}.{key}" if path else key
            if _is_sensitive_report_exposure_key(key):
                sensitive_paths.add(nested_path)
            sensitive_paths.update(
                _sensitive_observed_value_paths(nested_value, path=nested_path)
            )
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}.{index}" if path else str(index)
            sensitive_paths.update(
                _sensitive_observed_value_paths(nested_value, path=nested_path)
            )
    return sensitive_paths


def _observed_value_field_names(field_names: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"observed_value.{field_name}" for field_name in field_names)
