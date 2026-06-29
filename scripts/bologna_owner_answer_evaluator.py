from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class OwnerAnswerEvaluation:
    accepted: bool
    errors: tuple[str, ...]
    still_blocked: tuple[str, ...]


def _text(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _string_set(values: Iterable[Any]) -> set[str]:
    return {str(value) for value in values}


def _list_values(
    value: Any,
    *,
    allow_empty: bool,
    field_name: str,
    errors: list[str],
) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list")
        return []
    if not allow_empty and not value:
        errors.append(f"{field_name} must not be empty")
    return value


def _check_text_list(
    record: Mapping[str, Any],
    field_name: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> list[str]:
    items = _list_values(
        record.get(field_name),
        allow_empty=allow_empty,
        field_name=field_name,
        errors=errors,
    )
    text_items: list[str] = []
    for index, item in enumerate(items):
        text = _text(item)
        if text is None:
            errors.append(f"{field_name}[{index}] must be non-empty text")
        else:
            text_items.append(text)
    return text_items


def _check_complete_record_shape(
    record: Mapping[str, Any],
    required_fields: Iterable[str],
    errors: list[str],
    *,
    label: str,
    reject_extra_fields: bool,
    allow_empty_fields: Iterable[str] = (),
) -> None:
    required = set(required_fields)
    allowed_empty = set(allow_empty_fields)
    actual = set(record)
    missing = sorted(required - actual)
    extra = sorted(actual - required)
    if missing:
        errors.append(f"{label} missing required fields: {', '.join(missing)}")
    if reject_extra_fields and extra:
        errors.append(f"{label} has unexpected fields: {', '.join(extra)}")
    for field_name in required:
        if field_name not in record:
            continue
        value = record[field_name]
        if value is None:
            errors.append(f"{label}.{field_name} must not be null")
        elif isinstance(value, str) and not value.strip():
            errors.append(f"{label}.{field_name} must not be empty")
        elif isinstance(value, list) and not value and field_name not in allowed_empty:
            errors.append(f"{label}.{field_name} must not be an empty list")
        elif isinstance(value, dict) and not value:
            errors.append(f"{label}.{field_name} must not be an empty mapping")


def _check_owner_answer(
    owner_answer: Mapping[str, Any],
    *,
    odp_id: str,
    required_fields: Iterable[str],
    allowed_answer_types: Iterable[str],
    required_answer_type: str,
    errors: list[str],
) -> None:
    _check_complete_record_shape(
        owner_answer,
        required_fields,
        errors,
        label="owner_answer",
        reject_extra_fields=True,
        allow_empty_fields={
            "downstream_unlocks_requested",
            "supersedes_owner_answer_ids",
        },
    )
    if owner_answer.get("odp_id") != odp_id:
        errors.append(f"owner_answer.odp_id must be {odp_id}")
    answer_type = owner_answer.get("answer_type")
    if answer_type not in set(allowed_answer_types):
        errors.append("owner_answer.answer_type is not allowed")
    if answer_type != required_answer_type:
        errors.append(f"owner_answer.answer_type must be {required_answer_type}")
    for field_name in (
        "owner_answer_id",
        "decision_owner",
        "authority_reference",
        "answer_summary",
    ):
        if _text(owner_answer.get(field_name)) is None:
            errors.append(f"owner_answer.{field_name} must be non-empty text")
    try:
        date.fromisoformat(str(owner_answer.get("decision_date")))
    except ValueError:
        errors.append("owner_answer.decision_date must be an ISO date")
    _check_text_list(owner_answer, "cited_artifacts", errors)
    _check_text_list(owner_answer, "caveats", errors)
    downstream = _list_values(
        owner_answer.get("downstream_unlocks_requested"),
        allow_empty=True,
        field_name="owner_answer.downstream_unlocks_requested",
        errors=errors,
    )
    if downstream:
        errors.append("owner_answer must not request downstream unlocks")
    _check_text_list(owner_answer, "supersedes_owner_answer_ids", errors, allow_empty=True)


def evaluate_owner_answer(
    owner_answer: Mapping[str, Any],
    *,
    odp_id: str,
    required_fields: Iterable[str],
    allowed_answer_types: Iterable[str],
    required_answer_type: str = "approve_with_cited_authority",
    required_prerequisites: Iterable[str] = (),
    satisfied_prerequisites: Iterable[str] = (),
    required_decisions: Iterable[str] = (),
    decision_coverage: Iterable[str] = (),
    companion_records: Sequence[Mapping[str, Any]] = (),
    companion_required_fields: Iterable[str] = (),
    companion_label: str = "companion_record",
    companion_decision_field: str | None = None,
    companion_required_decisions: Iterable[str] = (),
    companion_id_field: str | None = None,
    required_companion_ids: Iterable[str] = (),
    still_blocked_after_acceptance: Iterable[str] = (),
) -> OwnerAnswerEvaluation:
    """Evaluate a hypothetical Bologna owner answer without mutating repo state."""
    errors: list[str] = []
    if not isinstance(owner_answer, Mapping):
        return OwnerAnswerEvaluation(
            accepted=False,
            errors=("owner_answer must be a mapping",),
            still_blocked=tuple(str(item) for item in still_blocked_after_acceptance),
        )

    _check_owner_answer(
        owner_answer,
        odp_id=odp_id,
        required_fields=required_fields,
        allowed_answer_types=allowed_answer_types,
        required_answer_type=required_answer_type,
        errors=errors,
    )

    missing_prerequisites = sorted(
        set(required_prerequisites) - set(satisfied_prerequisites),
    )
    if missing_prerequisites:
        errors.append(f"missing satisfied prerequisites: {', '.join(missing_prerequisites)}")

    required_decision_set = set(required_decisions)
    if required_decision_set:
        missing_decisions = sorted(required_decision_set - set(decision_coverage))
        if missing_decisions:
            errors.append(f"missing required decisions: {', '.join(missing_decisions)}")

    companion_fields = set(companion_required_fields)
    if companion_fields and not companion_records:
        errors.append(f"{companion_label} records are required")

    companion_ids: set[str] = set()
    for index, companion in enumerate(companion_records):
        label = f"{companion_label}[{index}]"
        if not isinstance(companion, Mapping):
            errors.append(f"{label} must be a mapping")
            continue
        _check_complete_record_shape(
            companion,
            companion_fields,
            errors,
            label=label,
            reject_extra_fields=False,
            allow_empty_fields={
                "downstream_unlocks_requested",
                "supersedes_authority_record_ids",
                "supersedes_source_authority_record_ids",
            },
        )
        downstream = companion.get("downstream_unlocks_requested")
        if isinstance(downstream, list) and downstream:
            errors.append(f"{label} must not request downstream unlocks")
        if companion_decision_field and companion_required_decisions:
            missing = sorted(
                set(companion_required_decisions)
                - set(companion.get(companion_decision_field, [])),
            )
            if missing:
                errors.append(f"{label} missing decisions: {', '.join(missing)}")
        if companion_id_field:
            companion_id = _text(companion.get(companion_id_field))
            if companion_id is None:
                errors.append(f"{label}.{companion_id_field} must be non-empty text")
            else:
                companion_ids.add(companion_id)

    required_ids = _string_set(required_companion_ids)
    if required_ids:
        missing_ids = sorted(required_ids - companion_ids)
        if missing_ids:
            errors.append(f"missing required {companion_label} ids: {', '.join(missing_ids)}")

    return OwnerAnswerEvaluation(
        accepted=not errors,
        errors=tuple(errors),
        still_blocked=tuple(str(item) for item in still_blocked_after_acceptance),
    )
