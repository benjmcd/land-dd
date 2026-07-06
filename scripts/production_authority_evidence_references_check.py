from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from authority_check_lib import (  # noqa: E402
    build_summary as _build_summary,
    format_summary as _format_summary,
    list_set,
    load_yaml,
    read_text,
    repo_path,
    require,
    require_list,
    require_mapping,
    require_non_empty_list,
    require_text,
    row_summary,
    run_reporting_cli,
)

CONFIG_PATH = "config/production_authority_evidence_references.yaml"
PRODUCTION_INTAKE_PATH = "config/production_authority_intake.yaml"
FOLLOW_ON_SEQUENCE_PATH = "config/authority_follow_on_sequence.yaml"

EXPECTED_LIMITS = {
    "validate_only_reference_contract": True,
    "records_authority": False,
    "records_owner_answer": False,
    "supplies_authority_evidence": False,
    "approves_sources": False,
    "changes_source_rights": False,
    "changes_source_readiness": False,
    "triggers_follow_on_sequence": False,
    "captures_fixtures": False,
    "seeds_database": False,
    "proves_report": False,
    "provisions_hosted_runtime": False,
    "changes_schema_api_auth_ui_runtime": False,
    "unfreezes_qualification": False,
    "unblocks_p0": False,
    "claims_level_10": False,
}

EXPECTED_REFERENCE_FIELDS = (
    "reference_id",
    "authority_stream_id",
    "evidence_item_id",
    "authority_reference",
    "artifact_type",
    "artifact_location_or_citation",
    "decision_owner",
    "review_owner",
    "decision_date",
    "effective_date",
    "scope_summary",
    "evidence_summary",
    "caveats",
    "downstream_unlocks_requested",
    "supersedes_reference_ids",
)

EXPECTED_ARTIFACT_TYPES = {
    "redacted_contract_reference",
    "terms_url",
    "ticket_or_adr",
    "signed_decision_record",
    "platform_console_reference",
    "registry_or_digest_reference",
    "billing_owner_record",
    "alert_route_reference",
    "source_terms_review",
}

EXPECTED_FORBIDDEN_EFFECTS = {
    "source_approval",
    "source_rights_change",
    "owner_answer_recording",
    "corpus_capture",
    "fixture_capture",
    "db_seed",
    "report_proof",
    "hosted_runtime_provisioning",
    "level_10_claim",
    "qualification_pass",
    "owner_decision_unfreeze",
    "p0_unblock",
}

REQUIRED_FILES = (
    CONFIG_PATH,
    PRODUCTION_INTAKE_PATH,
    FOLLOW_ON_SEQUENCE_PATH,
    "docs/runbooks/production_authority_intake.md",
    "scripts/run_production_authority_evidence_references_check.ps1",
    "scripts/run_production_authority_evidence_references_check.sh",
)


@dataclass(frozen=True)
class EvidenceReferenceEvaluation:
    accepted: bool
    errors: tuple[str, ...]
    still_blocked: tuple[str, ...]


def text_value(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def text_list_values(
    record: Mapping[str, Any],
    field_name: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> list[str]:
    value = record.get(field_name)
    if not isinstance(value, list):
        errors.append(f"evidence_reference.{field_name} must be a list")
        return []
    if not value and not allow_empty:
        errors.append(f"evidence_reference.{field_name} must not be empty")
    items: list[str] = []
    for index, item in enumerate(value):
        text = text_value(item)
        if text is None:
            errors.append(f"evidence_reference.{field_name}[{index}] must be non-empty text")
        else:
            items.append(text)
    return items


def require_reference_date(record: Mapping[str, Any], field_name: str, errors: list[str]) -> None:
    text = text_value(record.get(field_name))
    if text is None:
        errors.append(f"evidence_reference.{field_name} must be non-empty text")
        return
    try:
        date.fromisoformat(text)
    except ValueError:
        errors.append(f"evidence_reference.{field_name} must be an ISO date")


def blocked_reference_effects(payload: Mapping[str, Any]) -> tuple[str, ...]:
    contract = payload.get("reference_contract")
    if isinstance(contract, Mapping):
        effects = contract.get("forbidden_reference_effects")
        if isinstance(effects, list):
            return tuple(str(effect) for effect in effects)
    return tuple(sorted(EXPECTED_FORBIDDEN_EFFECTS))


def reference_templates(payload: Mapping[str, Any], errors: list[str]) -> dict[str, Mapping[str, Any]]:
    raw_templates = payload.get("stream_reference_templates")
    if not isinstance(raw_templates, list) or not raw_templates:
        errors.append("stream_reference_templates must be a non-empty list")
        return {}
    templates: dict[str, Mapping[str, Any]] = {}
    for index, raw_template in enumerate(raw_templates):
        if not isinstance(raw_template, Mapping):
            errors.append(f"stream_reference_templates[{index}] must be a mapping")
            continue
        stream_id = text_value(raw_template.get("authority_stream_id"))
        if stream_id is None:
            errors.append(f"stream_reference_templates[{index}].authority_stream_id missing")
            continue
        templates[stream_id] = raw_template
    return templates


def evaluate_submitted_evidence_reference(
    payload: Mapping[str, Any],
    evidence_reference: Mapping[str, Any],
) -> EvidenceReferenceEvaluation:
    """Evaluate a hypothetical authority evidence reference without recording it."""
    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return EvidenceReferenceEvaluation(
            accepted=False,
            errors=("payload must be a mapping",),
            still_blocked=tuple(sorted(EXPECTED_FORBIDDEN_EFFECTS)),
        )
    if not isinstance(evidence_reference, Mapping):
        return EvidenceReferenceEvaluation(
            accepted=False,
            errors=("evidence_reference must be a mapping",),
            still_blocked=blocked_reference_effects(payload),
        )

    required_fields = set(EXPECTED_REFERENCE_FIELDS)
    actual_fields = set(evidence_reference)
    missing_fields = sorted(required_fields - actual_fields)
    extra_fields = sorted(actual_fields - required_fields)
    if missing_fields:
        errors.append(f"evidence_reference missing required fields: {', '.join(missing_fields)}")
    if extra_fields:
        errors.append(f"evidence_reference has unexpected fields: {', '.join(extra_fields)}")

    for field_name in (
        "reference_id",
        "authority_stream_id",
        "evidence_item_id",
        "authority_reference",
        "artifact_location_or_citation",
        "decision_owner",
        "review_owner",
        "scope_summary",
        "evidence_summary",
    ):
        if text_value(evidence_reference.get(field_name)) is None:
            errors.append(f"evidence_reference.{field_name} must be non-empty text")

    require_reference_date(evidence_reference, "decision_date", errors)
    require_reference_date(evidence_reference, "effective_date", errors)
    text_list_values(evidence_reference, "caveats", errors)
    text_list_values(evidence_reference, "supersedes_reference_ids", errors, allow_empty=True)
    downstream_unlocks = text_list_values(
        evidence_reference,
        "downstream_unlocks_requested",
        errors,
        allow_empty=True,
    )
    if downstream_unlocks:
        errors.append("evidence_reference must not request downstream unlocks")

    artifact_type = evidence_reference.get("artifact_type")
    if artifact_type not in EXPECTED_ARTIFACT_TYPES:
        errors.append("evidence_reference.artifact_type is not allowed")

    templates = reference_templates(payload, errors)
    authority_stream_id = text_value(evidence_reference.get("authority_stream_id"))
    evidence_item_id = text_value(evidence_reference.get("evidence_item_id"))
    if authority_stream_id is not None:
        template = templates.get(authority_stream_id)
        if template is None:
            errors.append(f"unknown authority_stream_id: {authority_stream_id}")
        elif evidence_item_id is not None:
            required_evidence = template.get("required_evidence")
            if not isinstance(required_evidence, list):
                errors.append(f"{authority_stream_id} required_evidence must be a list")
            elif evidence_item_id not in {str(item) for item in required_evidence}:
                errors.append(
                    "evidence_reference.evidence_item_id is not required for "
                    f"{authority_stream_id}"
                )

    return EvidenceReferenceEvaluation(
        accepted=not errors,
        errors=tuple(errors),
        still_blocked=blocked_reference_effects(payload),
    )


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require(repo_path(path_text).exists(), f"authority reference artifact missing: {path_text}")


def production_streams() -> dict[str, dict[str, Any]]:
    intake = load_yaml(PRODUCTION_INTAKE_PATH)
    streams = {
        require_text(stream.get("id"), "production stream id missing"): require_mapping(
            stream,
            "production stream must be a mapping",
        )
        for stream in require_non_empty_list(
            intake.get("authority_streams"),
            "production authority streams missing",
        )
    }
    for stream_id, stream in streams.items():
        require(stream.get("status") == "blocked", f"{stream_id} must remain blocked")
        require(stream.get("evidence_status") == "missing", f"{stream_id} evidence changed")
        require(stream.get("authority_references") == [], f"{stream_id} references changed")
        require(
            stream.get("decision_updates_allowed") is False,
            f"{stream_id} decision updates unexpectedly allowed",
        )
    return streams


def validate_reference_contract(contract: dict[str, Any]) -> None:
    require(
        contract.get("current_evidence_references") == [],
        "current evidence references must remain empty",
    )
    require(
        contract.get("downstream_unlocks_requested") == [],
        "reference contract must not request downstream unlocks",
    )
    fields = tuple(require_non_empty_list(contract.get("required_reference_fields"), "fields missing"))
    require(fields == EXPECTED_REFERENCE_FIELDS, "required reference fields drifted")
    require(
        list_set(contract.get("allowed_artifact_types"), "artifact types missing")
        == EXPECTED_ARTIFACT_TYPES,
        "allowed artifact types drifted",
    )
    require(
        list_set(contract.get("forbidden_reference_effects"), "forbidden effects missing")
        == EXPECTED_FORBIDDEN_EFFECTS,
        "forbidden reference effects drifted",
    )


def validate_template(template: dict[str, Any], stream: dict[str, Any]) -> None:
    stream_id = require_text(template.get("authority_stream_id"), "template stream id missing")
    require(template.get("source_catalog") == stream.get("source_catalog"), f"{stream_id} catalog drifted")
    require(
        template.get("status") == "missing_authority_reference",
        f"{stream_id} template must stay missing",
    )
    require(template.get("evidence_status") == "missing", f"{stream_id} evidence status drifted")
    require(
        list_set(template.get("required_evidence"), f"{stream_id} template evidence missing")
        == list_set(stream.get("required_evidence"), f"{stream_id} production evidence missing"),
        f"{stream_id} required evidence drifted",
    )
    require(
        template.get("current_authority_references") == [],
        f"{stream_id} template references must remain empty",
    )
    require(
        template.get("decision_updates_allowed") is False,
        f"{stream_id} template decision updates unexpectedly allowed",
    )
    require(
        template.get("downstream_unlocks_requested") == [],
        f"{stream_id} template requested downstream unlocks",
    )


def validate_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    require(
        payload.get("schema_version") == "production_authority_evidence_references_v1",
        "unexpected schema",
    )
    require(
        payload.get("status") == "blocked_no_submitted_references",
        "reference contract must stay blocked",
    )
    require(payload.get("source_intake") == PRODUCTION_INTAKE_PATH, "source intake mismatch")
    require(payload.get("follow_on_sequence") == FOLLOW_ON_SEQUENCE_PATH, "follow-on mismatch")
    require(
        payload.get("operator_runbook") == "docs/runbooks/production_authority_intake.md",
        "operator runbook mismatch",
    )
    require(
        payload.get("validation") == "scripts/run_production_authority_evidence_references_check.ps1",
        "validation wrapper mismatch",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "authority reference limits changed",
    )
    validate_reference_contract(
        require_mapping(payload.get("reference_contract"), "reference contract missing"),
    )

    streams = production_streams()
    templates = {
        require_text(template.get("authority_stream_id"), "template stream id missing"): require_mapping(
            template,
            "stream reference template must be a mapping",
        )
        for template in require_non_empty_list(
            payload.get("stream_reference_templates"),
            "stream reference templates missing",
        )
    }
    require(set(templates) == set(streams), "stream reference template set drifted")
    for stream_id, template in templates.items():
        validate_template(template, streams[stream_id])
    return payload


def validate_repo_wiring() -> None:
    expected_fragments = (
        ("MANIFEST.md", "config/production_authority_evidence_references.yaml"),
        ("MANIFEST.md", "scripts/production_authority_evidence_references_check.py"),
        ("scripts/verify.ps1", "production_authority_evidence_references_check.py"),
        ("scripts/verify.sh", "production_authority_evidence_references_check.py"),
        (
            "scripts/authority_evidence_intake_check.py",
            "production_authority_evidence_references_check.py",
        ),
        (
            "plans/2026-07-02-authority-evidence-intake.md",
            "production_authority_evidence_references_check.py",
        ),
        ("tasks/task_queue.yaml", "production_authority_evidence_references_check.py"),
        ("state/PROJECT_STATE.md", "production_authority_evidence_references_check.py"),
    )
    for path_text, fragment in expected_fragments:
        require(fragment in read_text(path_text), f"{path_text} missing expected fragment: {fragment}")


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    contract = require_mapping(payload.get("reference_contract"), "reference contract missing")
    current_references = require_list(
        contract.get("current_evidence_references"),
        "current evidence references must be a list",
    )
    downstream_unlocks = require_list(
        contract.get("downstream_unlocks_requested"),
        "downstream unlock requests must be a list",
    )
    required_fields = require_non_empty_list(
        contract.get("required_reference_fields"),
        "required reference fields missing",
    )
    templates = []
    for raw_template in require_non_empty_list(
        payload.get("stream_reference_templates"),
        "stream reference templates missing",
    ):
        template = require_mapping(raw_template, "stream reference template must be a mapping")
        required_evidence = require_non_empty_list(
            template.get("required_evidence"),
            "template required evidence missing",
        )
        current_authority_references = require_list(
            template.get("current_authority_references"),
            "template current authority references must be a list",
        )
        template_unlocks = require_list(
            template.get("downstream_unlocks_requested"),
            "template downstream unlocks must be a list",
        )
        templates.append(
            {
                "authority_stream_id": require_text(
                    template.get("authority_stream_id"),
                    "template stream id missing",
                ),
                "source_catalog": template.get("source_catalog"),
                "status": template.get("status"),
                "evidence_status": template.get("evidence_status"),
                "required_evidence": required_evidence,
                "required_evidence_count": len(required_evidence),
                "current_authority_reference_count": len(current_authority_references),
                "decision_updates_allowed": template.get("decision_updates_allowed"),
                "downstream_unlock_request_count": len(template_unlocks),
            }
        )
    return _build_summary(
        "production_authority_evidence_references_summary_v1",
        {
            "contract_status": payload.get("status"),
            "source_intake": payload.get("source_intake"),
            "follow_on_sequence": payload.get("follow_on_sequence"),
            "operator_runbook": payload.get("operator_runbook"),
            "validation": payload.get("validation"),
            "current_evidence_reference_count": len(current_references),
            "downstream_unlock_request_count": len(downstream_unlocks),
            "required_reference_fields": required_fields,
            "required_reference_field_count": len(required_fields),
            "allowed_artifact_types": require_non_empty_list(
                contract.get("allowed_artifact_types"),
                "allowed artifact types missing",
            ),
            "forbidden_reference_effects": require_non_empty_list(
                contract.get("forbidden_reference_effects"),
                "forbidden effects missing",
            ),
            "stream_reference_templates": templates,
            "stream_reference_template_count": len(templates),
        },
    )


def format_summary(summary: dict[str, Any]) -> str:
    require_non_empty_list(summary.get("stream_reference_templates"), "stream templates missing")
    return _format_summary(
        "production authority evidence references summary: blocked",
        summary,
        (
            ("schema_version", "schema_version"),
            ("contract_status", "contract_status"),
            ("source_intake", "source_intake"),
            ("follow_on_sequence", "follow_on_sequence"),
            ("current_evidence_references", "current_evidence_reference_count"),
            ("downstream_unlock_requests", "downstream_unlock_request_count"),
            ("required_reference_fields", "required_reference_field_count"),
            ("stream_reference_templates", "stream_reference_template_count"),
        ),
        row_groups=(
            (
                "stream_reference_templates",
                "stream_reference_template",
                row_summary(
                    "authority_stream_id",
                    (
                        ("status", "status"),
                        ("evidence_status", "evidence_status"),
                        ("required_evidence", "required_evidence_count"),
                        ("current_authority_references", "current_authority_reference_count"),
                        ("decision_updates_allowed", "decision_updates_allowed"),
                        ("downstream_unlocks", "downstream_unlock_request_count"),
                    ),
                ),
            ),
        ),
        list_fields=(("forbidden_reference_effects", "forbidden_reference_effects"),),
        footer="production authority evidence references check: ok",
    )


def validate_for_output() -> dict[str, Any]:
    validate_required_files()
    payload = validate_catalog(load_yaml(CONFIG_PATH))
    validate_repo_wiring()
    return payload


def main(argv: list[str] | None = None) -> int:
    return run_reporting_cli(
        description="Validate the production authority evidence reference contract.",
        ok_message="production authority evidence references check: ok",
        validate=validate_for_output,
        summary_builder=build_summary,
        summary_formatter=format_summary,
        argv=argv,
    )


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main(_qualification_sys.argv[1:]))
