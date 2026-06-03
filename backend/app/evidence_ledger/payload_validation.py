from __future__ import annotations

from typing import cast

from app.domain.enums import EvidenceType
from app.domain.evidence_contracts import EvidenceContract

SOURCE_FAILURE_ALLOWED_KEYS = {
    "attempted_url",
    "error_code",
    "error_message",
    "failure_reason",
    "retryable",
    "status_code",
}
SOURCE_OBSERVATION_ALLOWED_KEYS = {
    "flood_zone",
    "flood_zones",
    "flood_zone_code",
    "observed_status",
    "raw_value",
    "source_record_id",
    "source_stale",
    "source_url",
    "status",
    "value",
    "zone",
}
SPATIAL_INTERSECTION_KEYS = {
    "flood_zone",
    "flood_zones",
    "flood_zone_code",
    "geometry_relation",
    "intersection_area_sq_m",
    "intersection_ratio",
    "intersects",
    "intersects_high_risk_flood_zone",
    "source_stale",
}
SPATIAL_RESULT_KEYS = {
    "flood_zone",
    "flood_zones",
    "flood_zone_code",
    "geometry_relation",
    "intersects",
    "intersects_high_risk_flood_zone",
}
DERIVED_METRIC_KEYS = {
    "calculation_method",
    "metric_code",
    "unit",
    "value",
}
DOCUMENT_EXTRACT_KEYS = {
    "document_id",
    "document_title",
    "extract_text",
    "page",
    "section",
}
HUMAN_NOTE_ALLOWED_KEYS = {
    "note_status",
    "reviewer_role",
    "review_scope",
}


def validate_observed_value(evidence: EvidenceContract) -> None:
    _validate_payload_shape(evidence)
    match evidence.evidence_type:
        case EvidenceType.SOURCE_OBSERVATION:
            _validate_source_observation(evidence)
        case EvidenceType.SPATIAL_INTERSECTION:
            _validate_spatial_intersection(evidence)
        case EvidenceType.DERIVED_METRIC:
            _validate_derived_metric(evidence)
        case EvidenceType.DOCUMENT_EXTRACT:
            _validate_document_extract(evidence)
        case EvidenceType.SOURCE_FAILURE:
            _validate_source_failure(evidence)
        case EvidenceType.HUMAN_VERIFICATION | EvidenceType.MANUAL_NOTE:
            _validate_human_note(evidence)


def _validate_payload_shape(evidence: EvidenceContract) -> None:
    for key, value in evidence.observed_value.items():
        if not key.strip():
            raise ValueError("observed_value keys must be non-empty")
        if not _is_allowed_value(value):
            raise ValueError(
                f"{evidence.evidence_type} observed_value '{key}' must be a scalar "
                "or list of scalars"
            )


def _validate_source_observation(evidence: EvidenceContract) -> None:
    if not evidence.observed_value:
        raise ValueError("source_observation observed_value must contain at least one field")
    unknown_keys = set(evidence.observed_value) - SOURCE_OBSERVATION_ALLOWED_KEYS
    if unknown_keys:
        raise ValueError(
            "source_observation observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )


def _validate_spatial_intersection(evidence: EvidenceContract) -> None:
    if not evidence.observed_value:
        raise ValueError("spatial_intersection observed_value must contain spatial result fields")
    unknown_keys = set(evidence.observed_value) - SPATIAL_INTERSECTION_KEYS
    if unknown_keys:
        raise ValueError(
            "spatial_intersection observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )
    if not any(key in evidence.observed_value for key in SPATIAL_RESULT_KEYS):
        raise ValueError("spatial_intersection observed_value must contain a spatial result field")
    for key in ("intersects", "intersects_high_risk_flood_zone"):
        if key in evidence.observed_value and not isinstance(evidence.observed_value[key], bool):
            raise ValueError(f"spatial_intersection observed_value '{key}' must be boolean")
    for key in ("intersection_area_sq_m", "intersection_ratio"):
        if key in evidence.observed_value:
            _require_non_negative_number(evidence.observed_value[key], key)
    ratio = evidence.observed_value.get("intersection_ratio")
    if ratio is not None and cast(int | float, ratio) > 1:
        raise ValueError("intersection_ratio must be less than or equal to 1")


def _validate_derived_metric(evidence: EvidenceContract) -> None:
    unknown_keys = set(evidence.observed_value) - DERIVED_METRIC_KEYS
    if unknown_keys:
        raise ValueError(
            "derived_metric observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )
    metric_code = evidence.observed_value.get("metric_code")
    if not isinstance(metric_code, str) or not metric_code.strip():
        raise ValueError("derived_metric observed_value requires non-empty metric_code")
    value = evidence.observed_value.get("value")
    if not _is_number(value):
        raise ValueError("derived_metric observed_value requires numeric value")
    unit = evidence.observed_value.get("unit")
    if unit is not None and (not isinstance(unit, str) or not unit.strip()):
        raise ValueError("derived_metric observed_value unit must be non-empty when present")


def _validate_document_extract(evidence: EvidenceContract) -> None:
    if not any(key in evidence.observed_value for key in DOCUMENT_EXTRACT_KEYS):
        raise ValueError("document_extract observed_value must contain document/extract fields")
    unknown_keys = set(evidence.observed_value) - DOCUMENT_EXTRACT_KEYS
    if unknown_keys:
        raise ValueError(
            "document_extract observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )
    extract_text = evidence.observed_value.get("extract_text")
    if extract_text is not None and (not isinstance(extract_text, str) or not extract_text.strip()):
        raise ValueError("document_extract observed_value extract_text must be non-empty")


def _validate_source_failure(evidence: EvidenceContract) -> None:
    unknown_keys = set(evidence.observed_value) - SOURCE_FAILURE_ALLOWED_KEYS
    if unknown_keys:
        raise ValueError(
            "source_failure observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )
    for key in ("error_code", "error_message", "failure_reason"):
        value = evidence.observed_value.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"source_failure observed_value '{key}' must be non-empty text")
    status_code = evidence.observed_value.get("status_code")
    if status_code is not None:
        _require_non_negative_number(status_code, "status_code")
    retryable = evidence.observed_value.get("retryable")
    if retryable is not None and not isinstance(retryable, bool):
        raise ValueError("source_failure observed_value 'retryable' must be boolean")


def _validate_human_note(evidence: EvidenceContract) -> None:
    unknown_keys = set(evidence.observed_value) - HUMAN_NOTE_ALLOWED_KEYS
    if unknown_keys:
        raise ValueError(
            "human note observed_value contains unsupported fields: "
            f"{', '.join(sorted(unknown_keys))}"
        )


def _require_non_negative_number(value: object, field_name: str) -> None:
    if not _is_number(value):
        raise ValueError(f"{field_name} must be numeric")
    numeric_value = cast(int | float, value)
    if numeric_value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _is_allowed_value(value: object) -> bool:
    if _is_scalar(value):
        return True
    if isinstance(value, list):
        return all(_is_scalar(item) for item in value)
    return False


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, str | int | float | bool)


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


__all__ = ["validate_observed_value"]
