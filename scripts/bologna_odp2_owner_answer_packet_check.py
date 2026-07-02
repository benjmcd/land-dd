from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_odp2_owner_answer_packet.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_odp2_owner_answer_packet.md"
OWNER_INTAKE_PATH = "config/bologna_owner_answer_intake.yaml"
SCOPE_AUTH_PATH = "config/bol_scope_auth.yaml"
ODP2_GATE_PATH = "config/bologna_odp2_source_rights_response_gate.yaml"
SOURCE_AUTHORITY_PATH = "config/bologna_source_authority_intake.yaml"
SOURCE_RIGHTS_PATH = "config/bologna_source_rights.yaml"
ODP_ID = "ODP-BOL-002"
PREREQUISITE_ODP_ID = "ODP-BOL-001"
ODP1_OWNER_ANSWER_ID = "odp-bol-001-scope-pursuit-2026-06-26"

EXPECTED_APPROVALS = {
    "owner_answer_recorded": False,
    "source_authority_recorded": False,
    "source_rights_approved": False,
    "bsa001_unblocked": False,
    "source_registry_promotion_allowed": False,
    "recorded_corpus_allowed": False,
    "db_report_proof_allowed": False,
    "downstream_authority_updates_allowed": False,
}
EXPECTED_LIMITS = {
    "validate_only_answer_packet": True,
    "records_owner_answer": False,
    "records_source_authority": False,
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
    "claims_cadastral_authority": False,
    "claims_legal_review": False,
    "claims_hosted_production_ready": False,
    "claims_multi_geography_framework": False,
    "claims_level_10": False,
}
EXPECTED_NO_OVERCLAIM_CONTROLS = {
    "no_authority_by_packet",
    "no_source_authority_record_by_packet",
    "no_source_approval_by_packet",
    "no_source_rights_change_by_packet",
    "no_source_registry_promotion_by_packet",
    "no_fixture_capture_by_packet",
    "no_report_runtime_use_by_packet",
    "no_db_seed_by_packet",
    "no_cadastral_owner_title_access_buildability_claim",
    "no_legal_buildability_title_or_value_claim",
    "no_level_10_or_hosted_claim",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    "state/owner-decision-packet.md",
    OWNER_INTAKE_PATH,
    SCOPE_AUTH_PATH,
    ODP2_GATE_PATH,
    SOURCE_AUTHORITY_PATH,
    SOURCE_RIGHTS_PATH,
    "config/bologna_recorded_source_corpus.yaml",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "scripts/run_bologna_odp2_owner_answer_packet_check.ps1",
    "scripts/run_bologna_odp2_owner_answer_packet_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_odp2_owner_answer_packet_v1",
    "validate-only",
    ODP_ID,
    PREREQUISITE_ODP_ID,
    "missing_pilot_scope_authority",
    "current_source_authority_records",
    "current_source_rights_approval_references",
    "downstream_updates_allowed",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return value


def require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list):
        raise SystemExit(message)
    return value


def require_non_empty_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise SystemExit(message)
    return value


def require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(message)
    return value.strip()


def normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def require_existing(path_text: str) -> None:
    normalized = normalize_path(path_text)
    require(
        (ROOT / normalized).exists(),
        f"ODP-BOL-002 owner-answer packet artifact missing: {normalized}",
    )


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must map")


def list_set(value: Any, message: str) -> set[str]:
    return {str(item) for item in require_non_empty_list(value, message)}


def owner_answer_contract() -> dict[str, Any]:
    intake = load_yaml(OWNER_INTAKE_PATH)
    return require_mapping(intake.get("owner_answer_contract"), "owner contract missing")


def owner_answer_fields() -> set[str]:
    return list_set(owner_answer_contract().get("required_record_fields"), "owner fields missing")


def allowed_owner_answer_types() -> set[str]:
    return list_set(owner_answer_contract().get("allowed_answer_types"), "answer types missing")


def source_authority_contract() -> dict[str, Any]:
    payload = load_yaml(SOURCE_AUTHORITY_PATH)
    return require_mapping(
        payload.get("source_authority_record_contract"),
        "source authority contract missing",
    )


def source_authority_record_fields() -> set[str]:
    return list_set(
        source_authority_contract().get("required_record_fields"),
        "source authority fields missing",
    )


def allowed_source_authority_types() -> set[str]:
    return list_set(
        source_authority_contract().get("allowed_authority_types"),
        "source authority types missing",
    )


def source_rights_decisions() -> set[str]:
    rights = load_yaml(SOURCE_RIGHTS_PATH)
    return list_set(rights.get("required_rights_decisions"), "rights decisions missing")


def source_rights_candidate_ids() -> set[str]:
    rights = load_yaml(SOURCE_RIGHTS_PATH)
    ids = {
        require_text(item.get("candidate_id"), "candidate id missing")
        for item in require_non_empty_list(
            rights.get("candidate_rights_reviews"),
            "candidate rights reviews missing",
        )
        if isinstance(item, dict)
    }
    require_mapping(rights.get("cadastral_gap"), "cadastral gap missing")
    ids.add("cadastral_gap")
    return ids


def gate_candidate_requirements() -> dict[str, dict[str, Any]]:
    gate = load_yaml(ODP2_GATE_PATH)
    rows: dict[str, dict[str, Any]] = {}
    for raw_item in require_non_empty_list(
        gate.get("candidate_review_requirements"),
        "candidate requirements missing",
    ):
        item = require_mapping(raw_item, "candidate requirement must map")
        candidate_id = require_text(item.get("candidate_id"), "candidate id missing")
        require(candidate_id not in rows, f"duplicate candidate requirement: {candidate_id}")
        rows[candidate_id] = item
    return rows


def gate_decision_requirements() -> dict[str, dict[str, Any]]:
    gate = load_yaml(ODP2_GATE_PATH)
    rows: dict[str, dict[str, Any]] = {}
    for raw_item in require_non_empty_list(
        gate.get("decision_requirements"),
        "decision requirements missing",
    ):
        item = require_mapping(raw_item, "decision requirement must map")
        decision_id = require_text(item.get("decision_id"), "decision id missing")
        require(decision_id not in rows, f"duplicate decision requirement: {decision_id}")
        rows[decision_id] = item
    return rows


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_current_source_state() -> None:
    intake = load_yaml(OWNER_INTAKE_PATH)
    answers = require_list(
        owner_answer_contract().get("current_owner_answers"),
        "owner answers must be a list",
    )
    require(len(answers) == 1, "current owner answers must contain only review-only ODP1")
    answer = require_mapping(answers[0], "owner answer must map")
    require(answer.get("owner_answer_id") == ODP1_OWNER_ANSWER_ID, "ODP1 answer id changed")
    require(answer.get("odp_id") == PREREQUISITE_ODP_ID, "ODP1 answer ODP id changed")
    require(answer.get("answer_type") == "approve_review_only", "ODP1 answer type changed")
    require(answer.get("downstream_unlocks_requested") == [], "ODP1 answer unlocks changed")

    threads = {
        require_text(thread.get("odp_id"), "thread id missing"): thread
        for thread in require_non_empty_list(
            intake.get("bologna_decision_threads"),
            "Bologna decision threads missing",
        )
        if isinstance(thread, dict)
    }
    odp2_thread = require_mapping(threads.get(ODP_ID), f"{ODP_ID} thread missing")
    require(odp2_thread.get("status") == "missing_owner_answer", "ODP2 thread status changed")
    require(odp2_thread.get("owner_answer_references") == [], "ODP2 owner refs changed")
    require(odp2_thread.get("downstream_updates_allowed") is False, "ODP2 unlocked")

    scope = require_mapping(
        load_yaml(SCOPE_AUTH_PATH).get("promotion_readiness"),
        "scope promotion readiness missing",
    )
    require(
        scope.get("current_owner_answer_type") == "approve_review_only",
        "scope answer type changed",
    )
    require(
        scope.get("current_authority_record_references") == [],
        "scope authority refs changed",
    )

    odp2_gate = require_mapping(load_yaml(ODP2_GATE_PATH).get("odp_bol_002_gate"), "gate missing")
    require(
        odp2_gate.get("prerequisite_status") == "missing_pilot_scope_authority",
        "ODP2 prerequisite status changed",
    )
    require(odp2_gate.get("current_owner_answer_references") == [], "gate owner refs changed")
    require(
        odp2_gate.get("current_source_authority_record_references") == [],
        "gate source authority refs changed",
    )
    require(
        odp2_gate.get("current_source_rights_approval_references") == [],
        "gate source-rights refs changed",
    )

    source_contract = source_authority_contract()
    require(
        source_contract.get("current_source_authority_records") == [],
        "source authority records must remain empty",
    )

    rights = load_yaml(SOURCE_RIGHTS_PATH)
    approvals = require_mapping(rights.get("approvals"), "source-rights approvals missing")
    for key, value in approvals.items():
        require(value is False, f"source-rights approval enabled: {key}")
    for raw_review in require_non_empty_list(
        rights.get("candidate_rights_reviews"),
        "candidate rights reviews missing",
    ):
        review = require_mapping(raw_review, "candidate review must map")
        candidate_id = require_text(review.get("candidate_id"), "candidate id missing")
        require(
            review.get("decision_state") == "pending_external_review",
            f"{candidate_id} decision state changed",
        )
        for key, value in require_mapping(review.get("promotion"), "promotion missing").items():
            require(value is False, f"{candidate_id} promotion enabled: {key}")
    cadastral = require_mapping(rights.get("cadastral_gap"), "cadastral gap missing")
    require(
        cadastral.get("status") == "direct_source_review_required",
        "cadastral gap status changed",
    )
    for key, value in require_mapping(cadastral.get("approval"), "approval missing").items():
        require(value is False, f"cadastral approval enabled: {key}")


def validate_packet(payload: dict[str, Any]) -> None:
    require(
        payload.get("schema_version") == "bologna_odp2_owner_answer_packet_v1",
        "unexpected ODP-BOL-002 owner-answer packet schema",
    )
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook path drifted")
    require(
        payload.get("status")
        == "blocked_until_odp_bol_001_authority_and_missing_odp_bol_002_owner_answer",
        "packet status drifted",
    )
    require(
        payload.get("validation") == "scripts/run_bologna_odp2_owner_answer_packet_check.ps1",
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

    packet = require_mapping(payload.get("packet"), "packet body missing")
    require(packet.get("odp_id") == ODP_ID, "packet ODP id changed")
    require(packet.get("sequence") == 2, "packet sequence changed")
    require(packet.get("source_owner_answer_intake") == OWNER_INTAKE_PATH, "intake path")
    require(packet.get("source_scope_authority_gate") == SCOPE_AUTH_PATH, "scope path")
    require(packet.get("source_response_gate") == ODP2_GATE_PATH, "gate path")
    require(packet.get("source_authority_intake") == SOURCE_AUTHORITY_PATH, "authority path")
    require(packet.get("source_rights_matrix") == SOURCE_RIGHTS_PATH, "rights path")
    require(packet.get("prerequisite_odp_ids") == [PREREQUISITE_ODP_ID], "prereqs")
    require(packet.get("prerequisite_status") == "missing_pilot_scope_authority", "prereq")
    require(packet.get("current_owner_answer_references") == [], "owner refs changed")
    require(
        packet.get("current_source_authority_record_references") == [],
        "source authority refs changed",
    )
    require(
        packet.get("current_source_rights_approval_references") == [],
        "source rights refs changed",
    )

    owner_template = require_mapping(
        packet.get("owner_answer_template"),
        "owner answer template missing",
    )
    require(set(owner_template) == owner_answer_fields(), "owner template fields drifted")
    require(owner_template.get("odp_id") == ODP_ID, "owner template ODP id changed")
    require(owner_template.get("downstream_unlocks_requested") == [], "owner template unlocks")
    require(
        list_set(packet.get("allowed_answer_types"), "allowed answer types missing")
        == allowed_owner_answer_types(),
        "allowed answer types drifted",
    )

    authority_template = require_mapping(
        packet.get("source_authority_record_template"),
        "source authority record template missing",
    )
    require(
        set(authority_template) == source_authority_record_fields(),
        "source authority template fields drifted",
    )
    require(
        set(
            require_non_empty_list(
                authority_template.get("rights_decision_ids"),
                "rights ids missing",
            ),
        )
        == source_rights_decisions(),
        "source authority template rights decisions drifted",
    )
    require(
        authority_template.get("downstream_unlocks_requested") == [],
        "source authority template unlocks",
    )
    require(
        list_set(packet.get("allowed_source_authority_types"), "source types missing")
        == allowed_source_authority_types(),
        "source authority types drifted",
    )

    validate_candidate_checklist(payload)
    validate_rights_decision_checklist(payload)
    validate_outcome_policy(payload)
    validate_submission_policy(payload)
    controls = require_mapping(payload.get("no_overclaim_controls"), "controls missing")
    require(set(controls) == EXPECTED_NO_OVERCLAIM_CONTROLS, "controls drifted")
    for control_id, enabled in controls.items():
        require(enabled is True, f"{control_id} disabled")


def validate_candidate_checklist(payload: dict[str, Any]) -> None:
    checklist = require_non_empty_list(
        payload.get("candidate_review_checklist"),
        "candidate checklist missing",
    )
    requirements = gate_candidate_requirements()
    by_id: dict[str, dict[str, Any]] = {}
    for raw_item in checklist:
        item = require_mapping(raw_item, "candidate checklist item must map")
        candidate_id = require_text(item.get("candidate_id"), "candidate id missing")
        require(candidate_id not in by_id, f"duplicate candidate checklist id: {candidate_id}")
        by_id[candidate_id] = item
        source = require_mapping(
            requirements.get(candidate_id),
            f"unknown candidate checklist id: {candidate_id}",
        )
        require(item.get("status") == "awaiting_owner_response", f"{candidate_id} status")
        require(
            item.get("source_authority_record_required") is True,
            f"{candidate_id} authority flag",
        )
        for field in ("decision_state", "required_evidence"):
            require(item.get(field) == source.get(field), f"{candidate_id} {field} drifted")
    require(set(by_id) == source_rights_candidate_ids(), "candidate checklist coverage drifted")


def validate_rights_decision_checklist(payload: dict[str, Any]) -> None:
    checklist = require_non_empty_list(
        payload.get("rights_decision_checklist"),
        "rights decision checklist missing",
    )
    requirements = gate_decision_requirements()
    by_id: dict[str, dict[str, Any]] = {}
    for raw_item in checklist:
        item = require_mapping(raw_item, "rights checklist item must map")
        decision_id = require_text(item.get("decision_id"), "decision id missing")
        require(decision_id not in by_id, f"duplicate rights checklist id: {decision_id}")
        by_id[decision_id] = item
        source = require_mapping(
            requirements.get(decision_id),
            f"unknown rights checklist id: {decision_id}",
        )
        require(item.get("status") == "awaiting_owner_response", f"{decision_id} status")
        for field in ("owner_question", "must_cite", "consequence_if_missing"):
            require(item.get(field) == source.get(field), f"{decision_id} {field} drifted")
    require(set(by_id) == source_rights_decisions(), "rights checklist coverage drifted")


def validate_outcome_policy(payload: dict[str, Any]) -> None:
    rows = require_non_empty_list(payload.get("outcome_policy"), "outcome policy missing")
    by_type: dict[str, dict[str, Any]] = {}
    for raw_item in rows:
        item = require_mapping(raw_item, "outcome row must map")
        answer_type = require_text(item.get("answer_type"), "answer type missing")
        require(answer_type not in by_type, f"duplicate answer type: {answer_type}")
        by_type[answer_type] = item
        require_text(item.get("packet_effect"), f"{answer_type} packet effect missing")
        require(
            item.get("downstream_updates_allowed") is False,
            f"{answer_type} unexpectedly allows downstream updates",
        )
    require(set(by_type) == allowed_owner_answer_types(), "outcome answer types drifted")


def validate_submission_policy(payload: dict[str, Any]) -> None:
    policy = require_mapping(payload.get("submission_policy"), "submission policy missing")
    expected_paths = {
        "owner_answer_submission_target": OWNER_INTAKE_PATH,
        "source_authority_record_submission_target": SOURCE_AUTHORITY_PATH,
        "source_rights_submission_target": SOURCE_RIGHTS_PATH,
    }
    for key, expected in expected_paths.items():
        require(policy.get(key) == expected, f"{key} drifted")
    for key in (
        "current_owner_answer_references_must_remain_empty",
        "current_source_authority_records_must_remain_empty",
        "current_source_rights_approval_references_must_remain_empty",
        "requires_odp_bol_001_cited_authority_first",
        "requires_later_recording_slice",
    ):
        require(policy.get(key) is True, f"{key} must remain true")
    require(
        policy.get("downstream_updates_allowed_by_packet") is False,
        "packet unexpectedly allows downstream updates",
    )
    blocked = set(
        require_non_empty_list(
            payload.get("downstream_blocked_targets"),
            "downstream blocked targets missing",
        )
    )
    for path_text in (
        "config/bologna_source_rights.yaml",
        "config/bologna_recorded_source_corpus.yaml",
        "db/migrations",
        "db/seeds",
        "backend/app/reports",
        "backend/app/api",
    ):
        require(path_text in blocked, f"missing downstream blocker: {path_text}")


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"runbook missing phrase: {phrase}")
    for decision_id in source_rights_decisions():
        require(f"`{decision_id}`" in runbook, f"runbook missing {decision_id}")
    for candidate_id in source_rights_candidate_ids():
        require(f"`{candidate_id}`" in runbook, f"runbook missing {candidate_id}")


def main() -> int:
    validate_required_files()
    validate_packet(load_yaml(CONFIG_PATH))
    validate_current_source_state()
    validate_runbook()
    print("Bologna ODP-BOL-002 owner answer packet check: ok")
    return 0


if __name__ == "__main__":
    import sys as _qualification_sys
    from pathlib import Path as _QualificationPath

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
