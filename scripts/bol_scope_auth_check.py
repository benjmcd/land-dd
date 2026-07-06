#!/usr/bin/env python3
"""Validate the Bologna ODP-BOL-001 scope-authority readiness gate."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from authority_check_lib import (  # noqa: E402
    build_summary as _build_summary,
    format_summary as _format_summary,
    list_set,
    load_yaml,
    read_text,
    require,
    require_existing as _require_existing,
    require_list,
    require_mapping,
    require_non_empty_list,
    require_text,
    row_summary,
    run_reporting_cli,
)
from bologna_owner_answer_evaluator import (  # noqa: E402
    OwnerAnswerEvaluation,
    evaluate_owner_answer,
)

CONFIG_PATH = "config/bol_scope_auth.yaml"
RUNBOOK_PATH = "docs/runbooks/bol_scope_auth.md"
OWNER_INTAKE_PATH = "config/bologna_owner_answer_intake.yaml"
ODP1_GATE_PATH = "config/bologna_odp1_owner_response_gate.yaml"
ODP1_PACKET_PATH = "config/bologna_odp1_owner_answer_packet.yaml"
PILOT_SCOPE_PATH = "config/bologna_pilot_scope_authority.yaml"
ODP_ID = "ODP-BOL-001"
ODP1_OWNER_ANSWER_ID = "odp-bol-001-scope-pursuit-2026-06-26"

EXPECTED_APPROVALS = {
    "owner_answer_is_cited_authority": False,
    "pilot_scope_authority_record_ready": False,
    "product_aoi_scope_authorized": False,
    "source_authority_updates_allowed": False,
    "source_rights_updates_allowed": False,
    "recorded_corpus_allowed": False,
    "db_report_proof_allowed": False,
}
EXPECTED_LIMITS = {
    "validate_only_promotion_readiness": True,
    "records_owner_answer": False,
    "records_pilot_scope_authority": False,
    "selects_bologna_aoi": False,
    "approves_sources": False,
    "changes_source_rights": False,
    "promotes_source_registry": False,
    "creates_recorded_fixtures": False,
    "creates_source_failure_fixtures": False,
    "runs_live_connectors": False,
    "mutates_database": False,
    "creates_runtime_artifacts": False,
    "creates_report_artifacts": False,
    "changes_report_semantics": False,
    "changes_source_readiness": False,
    "approves_ds017": False,
    "claims_legal_review": False,
    "claims_hosted_production_ready": False,
    "claims_level_10": False,
}
EXPECTED_NO_OVERCLAIM_CONTROLS = {
    "no_authority_by_readiness_gate",
    "no_aoi_selection_by_readiness_gate",
    "no_source_approval_by_readiness_gate",
    "no_source_rights_change_by_readiness_gate",
    "no_fixture_capture_by_readiness_gate",
    "no_report_runtime_use_by_readiness_gate",
    "no_db_seed_by_readiness_gate",
    "no_legal_buildability_title_or_value_claim",
    "no_level_10_or_hosted_claim",
}
EXPECTED_FUTURE_REQUIREMENTS = {
    "coverage_policy": "all_required_scope_decisions",
    "downstream_unlocks_requested_must_be_empty": True,
    "cited_artifacts_required": True,
    "caveats_required": True,
    "stop_conditions_required": True,
    "supersedes_ids_may_be_empty": True,
}
EXPECTED_ALLOWED_TARGETS = {
    OWNER_INTAKE_PATH,
    PILOT_SCOPE_PATH,
    CONFIG_PATH,
}
EXPECTED_FORBIDDEN_TARGETS = {
    "config/bologna_source_authority_intake.yaml",
    "config/bologna_source_rights.yaml",
    "config/bologna_recorded_source_corpus.yaml",
    "db/migrations",
    "db/seeds",
    "backend/app/api",
    "backend/app/reports",
    "backend/app/connectors",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    "state/owner-decision-packet.md",
    OWNER_INTAKE_PATH,
    ODP1_GATE_PATH,
    ODP1_PACKET_PATH,
    PILOT_SCOPE_PATH,
    "config/bologna_source_authority_intake.yaml",
    "config/bologna_source_rights.yaml",
    "config/bologna_recorded_source_corpus.yaml",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "scripts/run_bol_scope_auth_check.ps1",
    "scripts/run_bol_scope_auth_check.sh",
)
RUNBOOK_PHRASES = (
    "bol_scope_auth_v1",
    "validate-only",
    "approve_review_only",
    "approve_with_cited_authority",
    ODP_ID,
    ODP1_OWNER_ANSWER_ID,
    "current_authority_records",
    "request no downstream unlocks",
)


def require_existing(path_text: str) -> None:
    _require_existing(path_text, "scope-authority artifact missing")


def owner_answer_contract() -> dict[str, Any]:
    intake = load_yaml(OWNER_INTAKE_PATH)
    return require_mapping(
        intake.get("owner_answer_contract"),
        "owner answer contract missing",
    )


def owner_answer_fields() -> set[str]:
    return list_set(
        owner_answer_contract().get("required_record_fields"),
        "owner answer fields missing",
    )


def pilot_contract() -> dict[str, Any]:
    pilot = load_yaml(PILOT_SCOPE_PATH)
    return require_mapping(
        pilot.get("authority_record_contract"),
        "pilot authority record contract missing",
    )


def pilot_authority_record_fields() -> set[str]:
    return list_set(
        pilot_contract().get("required_record_fields"),
        "authority fields missing",
    )


def pilot_scope_decisions() -> set[str]:
    pilot = load_yaml(PILOT_SCOPE_PATH)
    return list_set(pilot.get("required_scope_decisions"), "pilot scope decisions missing")


def current_odp1_owner_answer() -> dict[str, Any]:
    answers = require_list(
        owner_answer_contract().get("current_owner_answers"),
        "owner answers must be a list",
    )
    require(len(answers) == 1, "exactly one ODP-BOL-001 owner answer must be recorded")
    answer = require_mapping(answers[0], "owner answer must be a mapping")
    require(
        answer.get("owner_answer_id") == ODP1_OWNER_ANSWER_ID,
        "ODP-BOL-001 owner answer id changed",
    )
    return answer


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_current_source_state() -> None:
    answer = current_odp1_owner_answer()
    require(
        answer.get("answer_type") == "approve_review_only",
        "current owner answer is not review-only",
    )
    require(
        answer.get("downstream_unlocks_requested") == [],
        "current owner answer must not request downstream unlocks",
    )

    contract = pilot_contract()
    require(
        contract.get("current_authority_records") == [],
        "pilot authority records must remain empty",
    )

    gate = require_mapping(
        load_yaml(ODP1_GATE_PATH).get("odp_bol_001_gate"),
        "ODP1 gate missing",
    )
    require(
        gate.get("current_owner_answer_references") == [ODP1_OWNER_ANSWER_ID],
        "ODP1 gate owner refs changed",
    )
    require(gate.get("current_authority_record_references") == [], "ODP1 gate authority refs")

    packet = require_mapping(load_yaml(ODP1_PACKET_PATH).get("packet"), "ODP1 packet missing")
    require(
        packet.get("current_owner_answer_references") == [ODP1_OWNER_ANSWER_ID],
        "ODP1 packet owner refs changed",
    )
    require(packet.get("current_authority_record_references") == [], "ODP1 packet authority refs")


def validate_promotion_readiness(payload: dict[str, Any]) -> None:
    readiness = require_mapping(
        payload.get("promotion_readiness"),
        "promotion readiness missing",
    )
    require(readiness.get("odp_id") == ODP_ID, "ODP id changed")
    require(readiness.get("sequence") == 1, "sequence changed")
    require(
        readiness.get("readiness_state") == "blocked_current_answer_review_only",
        "readiness state changed",
    )
    require(
        readiness.get("current_owner_answer_references") == [ODP1_OWNER_ANSWER_ID],
        "current owner refs changed",
    )
    require(
        readiness.get("current_authority_record_references") == [],
        "authority refs must remain empty",
    )
    answer = current_odp1_owner_answer()
    require(
        readiness.get("current_owner_answer_type") == answer.get("answer_type"),
        "current owner answer type drifted",
    )
    require(
        readiness.get("current_owner_answer_type") == "approve_review_only",
        "readiness must reflect review-only current answer",
    )
    require(
        readiness.get("required_next_owner_answer_type") == "approve_with_cited_authority",
        "required next answer type changed",
    )
    require(
        readiness.get("current_owner_answer_type")
        != readiness.get("required_next_owner_answer_type"),
        "review-only answer cannot satisfy cited-authority promotion",
    )
    require(
        readiness.get("owner_answer_submission_target") == OWNER_INTAKE_PATH,
        "owner answer target drifted",
    )
    require(
        readiness.get("authority_record_submission_target") == PILOT_SCOPE_PATH,
        "authority record target drifted",
    )
    require(
        list_set(readiness.get("required_owner_answer_fields"), "owner fields missing")
        == owner_answer_fields(),
        "owner answer fields drifted",
    )
    require(
        list_set(readiness.get("required_authority_record_fields"), "authority fields missing")
        == pilot_authority_record_fields(),
        "authority record fields drifted",
    )
    require(
        list_set(readiness.get("required_scope_decisions"), "scope decisions missing")
        == pilot_scope_decisions(),
        "scope decisions drifted",
    )
    require(
        require_mapping(
            readiness.get("future_authority_record_requirements"),
            "future requirements missing",
        )
        == EXPECTED_FUTURE_REQUIREMENTS,
        "future authority requirements changed",
    )


def evaluate_synthetic_owner_answer(
    payload: dict[str, Any],
    owner_answer: Mapping[str, Any],
    authority_record: Mapping[str, Any],
    *,
    satisfied_prerequisites: Iterable[str] = (),
) -> OwnerAnswerEvaluation:
    readiness = require_mapping(
        payload.get("promotion_readiness"),
        "promotion readiness missing",
    )
    decision_coverage = (
        authority_record.get("scope_decision_ids", [])
        if isinstance(authority_record, Mapping)
        else []
    )
    downstream = [
        f"{row.get('id')}: {row.get('status')}"
        for row in require_non_empty_list(
            payload.get("downstream_after_valid_scope_authority"),
            "downstream status missing",
        )
        if isinstance(row, dict)
    ]
    return evaluate_owner_answer(
        owner_answer,
        odp_id=ODP_ID,
        required_fields=require_non_empty_list(
            readiness.get("required_owner_answer_fields"),
            "owner fields missing",
        ),
        allowed_answer_types={"approve_with_cited_authority"},
        required_answer_type=require_text(
            readiness.get("required_next_owner_answer_type"),
            "required next answer type missing",
        ),
        required_prerequisites=(),
        satisfied_prerequisites=satisfied_prerequisites,
        required_decisions=require_non_empty_list(
            readiness.get("required_scope_decisions"),
            "scope decisions missing",
        ),
        decision_coverage=decision_coverage,
        companion_records=[authority_record],
        companion_required_fields=require_non_empty_list(
            readiness.get("required_authority_record_fields"),
            "authority fields missing",
        ),
        companion_label="pilot_scope_authority_record",
        companion_decision_field="scope_decision_ids",
        companion_required_decisions=require_non_empty_list(
            readiness.get("required_scope_decisions"),
            "scope decisions missing",
        ),
        still_blocked_after_acceptance=downstream,
    )


def validate_catalog(payload: dict[str, Any]) -> None:
    require(payload.get("schema_version") == "bol_scope_auth_v1", "unexpected schema")
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook path drifted")
    require(
        payload.get("status") == "blocked_review_only_owner_answer",
        "status changed",
    )
    require(
        payload.get("validation") == "scripts/run_bol_scope_auth_check.ps1",
        "validation wrapper drifted",
    )
    for path_text in require_non_empty_list(payload.get("authority"), "authority paths missing"):
        require(isinstance(path_text, str), "authority paths must be strings")
        require_existing(path_text)
    require(
        require_mapping(payload.get("approvals"), "approvals missing") == EXPECTED_APPROVALS,
        "approvals changed",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "limits changed",
    )
    validate_promotion_readiness(payload)
    require_non_empty_list(payload.get("eligible_when"), "eligibility list missing")
    require(
        list_set(payload.get("allowed_future_authority_targets"), "allowed targets missing")
        == EXPECTED_ALLOWED_TARGETS,
        "allowed future authority targets changed",
    )
    require(
        list_set(payload.get("forbidden_bundled_targets"), "forbidden targets missing")
        == EXPECTED_FORBIDDEN_TARGETS,
        "forbidden bundled targets changed",
    )
    downstream = require_non_empty_list(
        payload.get("downstream_after_valid_scope_authority"),
        "downstream status missing",
    )
    downstream_ids = {
        require_text(
            require_mapping(item, "each downstream row must be a mapping").get("id"),
            "downstream id missing",
        )
        for item in downstream
    }
    require(downstream_ids == {"ODP-BOL-002", "ODP-BOL-003", "ODP-BOL-004"}, "downstream ids")
    for raw_item in downstream:
        item = require_mapping(raw_item, "each downstream row must be a mapping")
        require(
            item.get("update_allowed_by_this_gate") is False,
            f"{item.get('id')} unexpectedly allowed",
        )
    controls = require_mapping(payload.get("no_overclaim_controls"), "no-overclaim missing")
    require(set(controls) == EXPECTED_NO_OVERCLAIM_CONTROLS, "no-overclaim controls drifted")
    for control_id, enabled in controls.items():
        require(enabled is True, f"{control_id} no-overclaim control disabled")


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"runbook missing phrase: {phrase}")


def validate_for_output() -> dict[str, Any]:
    validate_required_files()
    payload = load_yaml(CONFIG_PATH)
    validate_catalog(payload)
    validate_current_source_state()
    validate_runbook()
    return payload


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    readiness = require_mapping(
        payload.get("promotion_readiness"),
        "promotion readiness missing",
    )
    downstream_rows = []
    for raw_item in require_non_empty_list(
        payload.get("downstream_after_valid_scope_authority"),
        "downstream status missing",
    ):
        item = require_mapping(raw_item, "each downstream row must be a mapping")
        downstream_rows.append(
            {
                "id": require_text(item.get("id"), "downstream id missing"),
                "status": item.get("status"),
                "update_allowed_by_this_gate": item.get("update_allowed_by_this_gate"),
            }
        )
    owner_fields = require_non_empty_list(
        readiness.get("required_owner_answer_fields"),
        "owner fields missing",
    )
    authority_fields = require_non_empty_list(
        readiness.get("required_authority_record_fields"),
        "authority fields missing",
    )
    scope_decisions = require_non_empty_list(
        readiness.get("required_scope_decisions"),
        "scope decisions missing",
    )
    current_authority_refs = require_list(
        readiness.get("current_authority_record_references"),
        "authority refs must be a list",
    )
    no_overclaim_controls = require_mapping(
        payload.get("no_overclaim_controls"),
        "no-overclaim missing",
    )
    return _build_summary(
        "bol_scope_auth_summary_v1",
        {
            "gate_status": payload.get("status"),
            "operator_runbook": payload.get("operator_runbook"),
            "validation": payload.get("validation"),
            "odp_id": readiness.get("odp_id"),
            "sequence": readiness.get("sequence"),
            "readiness_state": readiness.get("readiness_state"),
            "current_owner_answer_references": require_list(
                readiness.get("current_owner_answer_references"),
                "current owner refs must be a list",
            ),
            "current_authority_record_reference_count": len(current_authority_refs),
            "current_owner_answer_type": readiness.get("current_owner_answer_type"),
            "required_next_owner_answer_type": readiness.get("required_next_owner_answer_type"),
            "owner_answer_submission_target": readiness.get("owner_answer_submission_target"),
            "authority_record_submission_target": readiness.get(
                "authority_record_submission_target",
            ),
            "required_owner_answer_fields": owner_fields,
            "required_owner_answer_field_count": len(owner_fields),
            "required_authority_record_fields": authority_fields,
            "required_authority_record_field_count": len(authority_fields),
            "required_scope_decisions": scope_decisions,
            "required_scope_decision_count": len(scope_decisions),
            "future_authority_record_requirements": require_mapping(
                readiness.get("future_authority_record_requirements"),
                "future requirements missing",
            ),
            "allowed_future_authority_targets": require_non_empty_list(
                payload.get("allowed_future_authority_targets"),
                "allowed targets missing",
            ),
            "forbidden_bundled_targets": require_non_empty_list(
                payload.get("forbidden_bundled_targets"),
                "forbidden targets missing",
            ),
            "downstream_after_valid_scope_authority": downstream_rows,
            "downstream_gate_count": len(downstream_rows),
            "no_overclaim_controls": no_overclaim_controls,
            "no_overclaim_control_count": len(no_overclaim_controls),
        },
    )


def format_summary(summary: dict[str, Any]) -> str:
    require_non_empty_list(
        summary.get("downstream_after_valid_scope_authority"),
        "downstream status missing",
    )
    return _format_summary(
        "Bologna scope authority readiness summary: blocked",
        summary,
        (
            ("schema_version", "schema_version"),
            ("gate_status", "gate_status"),
            ("odp_id", "odp_id"),
            ("readiness_state", "readiness_state"),
            ("current_owner_answer_type", "current_owner_answer_type"),
            ("required_next_owner_answer_type", "required_next_owner_answer_type"),
            ("current_authority_records", "current_authority_record_reference_count"),
            ("required_owner_answer_fields", "required_owner_answer_field_count"),
            (
                "required_authority_record_fields",
                "required_authority_record_field_count",
            ),
            ("required_scope_decisions", "required_scope_decision_count"),
            ("downstream_gates", "downstream_gate_count"),
        ),
        row_groups=(
            (
                "downstream_after_valid_scope_authority",
                "downstream_after_valid_scope_authority",
                row_summary(
                    "id",
                    (
                        ("status", "status"),
                        ("update_allowed_by_this_gate", "update_allowed_by_this_gate"),
                    ),
                ),
            ),
        ),
        fields_after_rows=(("no_overclaim_controls", "no_overclaim_control_count"),),
        footer="Bologna scope authority readiness check: ok",
    )


def main(argv: list[str] | None = None) -> int:
    return run_reporting_cli(
        description="Validate the Bologna ODP-BOL-001 scope-authority readiness gate.",
        ok_message="Bologna scope authority readiness check: ok",
        validate=validate_for_output,
        summary_builder=build_summary,
        summary_formatter=format_summary,
        argv=argv,
    )


if __name__ == "__main__":
    import sys as _qualification_sys
    from pathlib import Path as _QualificationPath

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main(_qualification_sys.argv[1:]))
