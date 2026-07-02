from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return value


def require_non_empty_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise SystemExit(message)
    return value


def require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list):
        raise SystemExit(message)
    return value


def require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(message)
    return value.strip()


def normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def repo_path(path_text: str) -> Path:
    return ROOT / normalize_path(path_text)


def read_text(path_text: str) -> str:
    return repo_path(path_text).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must be a mapping")


def list_set(value: Any, message: str) -> set[str]:
    return {str(item) for item in require_non_empty_list(value, message)}


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
    return {
        "schema_version": "production_authority_evidence_references_summary_v1",
        "ok": True,
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
    }


def format_summary(summary: dict[str, Any]) -> str:
    templates = require_non_empty_list(
        summary.get("stream_reference_templates"),
        "stream templates missing",
    )
    lines = [
        "production authority evidence references summary: blocked",
        f"schema_version: {summary.get('schema_version')}",
        f"contract_status: {summary.get('contract_status')}",
        f"source_intake: {summary.get('source_intake')}",
        f"follow_on_sequence: {summary.get('follow_on_sequence')}",
        f"current_evidence_references: {summary.get('current_evidence_reference_count')}",
        f"downstream_unlock_requests: {summary.get('downstream_unlock_request_count')}",
        f"required_reference_fields: {summary.get('required_reference_field_count')}",
        f"stream_reference_templates: {summary.get('stream_reference_template_count')}",
    ]
    for raw_template in templates:
        template = require_mapping(raw_template, "stream template summary must be a mapping")
        lines.append(
            "stream_reference_template "
            f"{template.get('authority_stream_id')}: "
            f"status={template.get('status')} "
            f"evidence_status={template.get('evidence_status')} "
            f"required_evidence={template.get('required_evidence_count')} "
            "current_authority_references="
            f"{template.get('current_authority_reference_count')} "
            f"decision_updates_allowed={template.get('decision_updates_allowed')} "
            f"downstream_unlocks={template.get('downstream_unlock_request_count')}"
        )
    lines.append(
        "forbidden_reference_effects: "
        + ", ".join(str(effect) for effect in summary.get("forbidden_reference_effects", []))
    )
    lines.append("production authority evidence references check: ok")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the production authority evidence reference contract.",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", dest="json_output")
    output_group.add_argument("--summary", action="store_true", dest="summary_output")
    args = parser.parse_args([] if argv is None else argv)
    validate_required_files()
    payload = validate_catalog(load_yaml(CONFIG_PATH))
    validate_repo_wiring()
    if args.json_output:
        print(json.dumps(build_summary(payload), indent=2, sort_keys=True))
    elif args.summary_output:
        print(format_summary(build_summary(payload)))
    else:
        print("production authority evidence references check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main(_qualification_sys.argv[1:]))
