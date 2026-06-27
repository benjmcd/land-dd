from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_odp1_owner_response_gate.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_odp1_owner_response_gate.md"
OWNER_INTAKE_PATH = "config/bologna_owner_answer_intake.yaml"
PILOT_SCOPE_PATH = "config/bologna_pilot_scope_authority.yaml"
ODP_ID = "ODP-BOL-001"
ODP1_OWNER_ANSWER_ID = "odp-bol-001-scope-pursuit-2026-06-26"
ODP1_STATUS = "review_only_scope_pursuit_answered"

EXPECTED_APPROVALS = {
    "owner_answer_recorded": True,
    "product_aoi_scope_authorized": False,
    "pilot_scope_authority_recorded": False,
    "bsa001_unblocked": False,
    "source_authority_updates_allowed": False,
    "source_rights_updates_allowed": False,
    "recorded_corpus_allowed": False,
    "db_report_proof_allowed": False,
}
EXPECTED_LIMITS = {
    "validate_only_response_gate": True,
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
    "claims_multi_geography_framework": False,
    "claims_level_10": False,
}
EXPECTED_ANSWER_TYPES = {
    "approve_with_cited_authority",
    "keep_blocked",
    "approve_review_only",
    "exclude_or_defer",
}
EXPECTED_NO_OVERCLAIM_CONTROLS = {
    "no_authority_by_response_gate",
    "no_aoi_selection_by_response_gate",
    "no_source_approval_by_response_gate",
    "no_source_rights_change_by_response_gate",
    "no_fixture_capture_by_response_gate",
    "no_report_runtime_use_by_response_gate",
    "no_db_seed_by_response_gate",
    "no_legal_buildability_title_or_value_claim",
    "no_level_10_or_hosted_claim",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    "state/owner-decision-packet.md",
    OWNER_INTAKE_PATH,
    PILOT_SCOPE_PATH,
    "config/bologna_source_authority_intake.yaml",
    "config/bologna_source_rights.yaml",
    "config/bologna_recorded_source_corpus.yaml",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "scripts/run_bologna_odp1_owner_response_gate_check.ps1",
    "scripts/run_bologna_odp1_owner_response_gate_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_odp1_owner_response_gate_v1",
    "validate-only",
    "review-only scope pursuit",
    ODP_ID,
    ODP1_OWNER_ANSWER_ID,
    "current_owner_answer_references",
    "current_authority_record_references",
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
    require((ROOT / normalized).exists(), f"ODP-BOL-001 gate artifact missing: {normalized}")


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must be a mapping")


def list_set(value: Any, message: str) -> set[str]:
    return {str(item) for item in require_non_empty_list(value, message)}


def owner_answer_fields() -> set[str]:
    intake = load_yaml(OWNER_INTAKE_PATH)
    contract = require_mapping(
        intake.get("owner_answer_contract"),
        "owner answer contract missing",
    )
    return list_set(contract.get("required_record_fields"), "owner answer fields missing")


def allowed_owner_answer_types() -> set[str]:
    intake = load_yaml(OWNER_INTAKE_PATH)
    contract = require_mapping(
        intake.get("owner_answer_contract"),
        "owner answer contract missing",
    )
    return list_set(contract.get("allowed_answer_types"), "owner answer types missing")


def pilot_scope_decisions() -> set[str]:
    pilot = load_yaml(PILOT_SCOPE_PATH)
    return list_set(pilot.get("required_scope_decisions"), "pilot scope decisions missing")


def pilot_authority_record_fields() -> set[str]:
    pilot = load_yaml(PILOT_SCOPE_PATH)
    contract = require_mapping(
        pilot.get("authority_record_contract"),
        "pilot authority record contract missing",
    )
    return list_set(
        contract.get("required_record_fields"),
        "pilot authority record fields missing",
    )


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_source_packets_still_blocked() -> None:
    intake = load_yaml(OWNER_INTAKE_PATH)
    threads = {
        require_text(thread.get("odp_id"), "ODP thread id missing"): thread
        for thread in require_non_empty_list(
            intake.get("bologna_decision_threads"),
            "Bologna decision threads missing",
        )
        if isinstance(thread, dict)
    }
    thread = require_mapping(threads.get(ODP_ID), f"{ODP_ID} thread missing")
    require(thread.get("status") == ODP1_STATUS, f"{ODP_ID} status changed")
    require(
        thread.get("owner_answer_references") == [ODP1_OWNER_ANSWER_ID],
        f"{ODP_ID} owner refs changed",
    )
    require(thread.get("downstream_updates_allowed") is False, f"{ODP_ID} updates allowed")

    contract = require_mapping(
        intake.get("owner_answer_contract"),
        "owner answer contract missing",
    )
    owner_answers = require_list(
        contract.get("current_owner_answers"),
        "owner answers must be a list",
    )
    require(len(owner_answers) == 1, "exactly one ODP-BOL-001 owner answer must be recorded")
    answer = require_mapping(owner_answers[0], "owner answer must be a mapping")
    require(
        answer.get("owner_answer_id") == ODP1_OWNER_ANSWER_ID,
        "ODP-BOL-001 owner answer id changed",
    )
    require(answer.get("answer_type") == "approve_review_only", "ODP-BOL-001 answer type")
    require(
        answer.get("downstream_unlocks_requested") == [],
        "ODP-BOL-001 owner answer must not request downstream unlocks",
    )

    pilot = load_yaml(PILOT_SCOPE_PATH)
    authority_contract = require_mapping(
        pilot.get("authority_record_contract"),
        "pilot authority record contract missing",
    )
    require(
        authority_contract.get("current_authority_records") == [],
        "pilot authority records must remain empty",
    )


def validate_gate(payload: dict[str, Any]) -> None:
    gate = require_mapping(payload.get("odp_bol_001_gate"), "ODP-BOL-001 gate missing")
    require(gate.get("odp_id") == ODP_ID, "ODP-BOL-001 gate id changed")
    require(gate.get("status") == ODP1_STATUS, "ODP-BOL-001 status changed")
    require(gate.get("source_owner_answer_intake") == OWNER_INTAKE_PATH, "intake path drifted")
    require(gate.get("source_pilot_scope_packet") == PILOT_SCOPE_PATH, "pilot path drifted")
    require(
        gate.get("current_owner_answer_references") == [ODP1_OWNER_ANSWER_ID],
        "owner refs changed",
    )
    require(gate.get("current_authority_record_references") == [], "authority refs must be empty")
    require(
        list_set(gate.get("required_owner_answer_fields"), "gate owner fields missing")
        == owner_answer_fields(),
        "gate owner fields drifted from owner-answer intake",
    )
    require(
        list_set(gate.get("required_authority_record_fields"), "gate authority fields missing")
        == pilot_authority_record_fields(),
        "gate authority fields drifted from pilot-scope packet",
    )
    require(
        list_set(gate.get("required_scope_decisions"), "gate scope decisions missing")
        == pilot_scope_decisions(),
        "gate scope decisions drifted from pilot-scope packet",
    )
    require_non_empty_list(gate.get("response_acceptance"), "response acceptance missing")
    blockers = require_non_empty_list(
        gate.get("still_blocked_after_valid_response"),
        "post-response blockers missing",
    )
    for phrase in ("ODP-BOL-002", "ODP-BOL-003", "ODP-BOL-004"):
        require(any(phrase in str(item) for item in blockers), f"missing blocker: {phrase}")


def validate_decision_requirements(payload: dict[str, Any]) -> None:
    requirements = require_non_empty_list(
        payload.get("decision_requirements"),
        "decision requirements missing",
    )
    by_id: dict[str, dict[str, Any]] = {}
    for raw_item in requirements:
        item = require_mapping(raw_item, "each decision requirement must be a mapping")
        decision_id = require_text(item.get("decision_id"), "decision id missing")
        require(decision_id not in by_id, f"duplicate decision requirement: {decision_id}")
        by_id[decision_id] = item
        require_text(item.get("owner_question"), f"{decision_id} owner question missing")
        require_text(item.get("consequence_if_missing"), f"{decision_id} consequence missing")
        for citation_need in require_non_empty_list(
            item.get("must_cite"),
            f"{decision_id} citation requirements missing",
        ):
            require_text(citation_need, f"{decision_id} citation item missing")
    require(set(by_id) == pilot_scope_decisions(), "decision requirements drifted")


def validate_outcome_matrix(payload: dict[str, Any]) -> None:
    outcomes = require_non_empty_list(payload.get("outcome_matrix"), "outcome matrix missing")
    by_type: dict[str, dict[str, Any]] = {}
    for raw_item in outcomes:
        item = require_mapping(raw_item, "each outcome row must be a mapping")
        answer_type = require_text(item.get("answer_type"), "answer type missing")
        require(answer_type not in by_type, f"duplicate answer type: {answer_type}")
        by_type[answer_type] = item
        require_text(item.get("expected_effect"), f"{answer_type} effect missing")
        require(
            item.get("downstream_updates_allowed") is False,
            f"{answer_type} unexpectedly allows downstream updates",
        )
        require_non_empty_list(item.get("still_disallowed"), f"{answer_type} disallowed missing")
    require(set(by_type) == EXPECTED_ANSWER_TYPES, "outcome answer types drifted")
    require(set(by_type) == allowed_owner_answer_types(), "outcomes drifted from intake types")


def validate_catalog() -> dict[str, Any]:
    payload = load_yaml(CONFIG_PATH)
    require(
        payload.get("schema_version") == "bologna_odp1_owner_response_gate_v1",
        "unexpected ODP-BOL-001 gate schema",
    )
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook path drifted")
    require(
        payload.get("status") == "blocked_review_only_scope_pursuit_answered",
        "gate status changed",
    )
    require(
        payload.get("validation") == "scripts/run_bologna_odp1_owner_response_gate_check.ps1",
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
    validate_gate(payload)
    validate_decision_requirements(payload)
    validate_outcome_matrix(payload)
    controls = require_mapping(payload.get("no_overclaim_controls"), "no-overclaim missing")
    require(set(controls) == EXPECTED_NO_OVERCLAIM_CONTROLS, "no-overclaim controls drifted")
    for control_id, enabled in controls.items():
        require(enabled is True, f"{control_id} no-overclaim control disabled")
    return payload


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"ODP-BOL-001 runbook missing phrase: {phrase}")
    for decision_id in pilot_scope_decisions():
        require(f"`{decision_id}`" in runbook, f"ODP-BOL-001 runbook missing {decision_id}")


def main() -> int:
    validate_required_files()
    validate_source_packets_still_blocked()
    validate_catalog()
    validate_runbook()
    print("Bologna ODP-BOL-001 owner response gate check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
