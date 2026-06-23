from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_odp1_owner_answer_packet.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_odp1_owner_answer_packet.md"
OWNER_INTAKE_PATH = "config/bologna_owner_answer_intake.yaml"
ODP1_GATE_PATH = "config/bologna_odp1_owner_response_gate.yaml"
PILOT_SCOPE_PATH = "config/bologna_pilot_scope_authority.yaml"
ODP_ID = "ODP-BOL-001"

EXPECTED_APPROVALS = {
    "owner_answer_recorded": False,
    "pilot_scope_authority_recorded": False,
    "product_aoi_scope_authorized": False,
    "downstream_authority_updates_allowed": False,
}
EXPECTED_LIMITS = {
    "validate_only_answer_packet": True,
    "records_owner_answer": False,
    "records_pilot_scope_authority": False,
    "selects_bologna_aoi": False,
    "approves_sources": False,
    "changes_source_rights": False,
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
    "no_authority_by_packet",
    "no_aoi_selection_by_packet",
    "no_source_approval_by_packet",
    "no_source_rights_change_by_packet",
    "no_fixture_capture_by_packet",
    "no_report_runtime_use_by_packet",
    "no_db_seed_by_packet",
    "no_legal_buildability_title_or_value_claim",
    "no_level_10_or_hosted_claim",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    "state/owner-decision-packet.md",
    OWNER_INTAKE_PATH,
    ODP1_GATE_PATH,
    PILOT_SCOPE_PATH,
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "scripts/run_bologna_odp1_owner_answer_packet_check.ps1",
    "scripts/run_bologna_odp1_owner_answer_packet_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_odp1_owner_answer_packet_v1",
    "validate-only",
    "does not record owner authority",
    ODP_ID,
    "current_owner_answers",
    "current_authority_records",
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
    require((ROOT / normalized).exists(), f"ODP-BOL-001 answer packet artifact missing: {normalized}")


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


def pilot_authority_record_fields() -> set[str]:
    pilot = load_yaml(PILOT_SCOPE_PATH)
    contract = require_mapping(
        pilot.get("authority_record_contract"),
        "pilot authority record contract missing",
    )
    return list_set(contract.get("required_record_fields"), "authority fields missing")


def pilot_scope_decisions() -> set[str]:
    pilot = load_yaml(PILOT_SCOPE_PATH)
    return list_set(pilot.get("required_scope_decisions"), "pilot scope decisions missing")


def odp1_gate_decision_requirements() -> dict[str, dict[str, Any]]:
    gate = load_yaml(ODP1_GATE_PATH)
    requirements: dict[str, dict[str, Any]] = {}
    for raw_item in require_non_empty_list(
        gate.get("decision_requirements"),
        "ODP1 decision requirements missing",
    ):
        item = require_mapping(raw_item, "each ODP1 decision requirement must be a mapping")
        decision_id = require_text(item.get("decision_id"), "ODP1 decision id missing")
        require(decision_id not in requirements, f"duplicate ODP1 decision id: {decision_id}")
        requirements[decision_id] = item
    return requirements


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_current_source_state() -> None:
    intake = load_yaml(OWNER_INTAKE_PATH)
    contract = require_mapping(
        intake.get("owner_answer_contract"),
        "owner answer contract missing",
    )
    require(contract.get("current_owner_answers") == [], "owner answers must remain empty")
    threads = {
        require_text(thread.get("odp_id"), "thread id missing"): thread
        for thread in require_non_empty_list(
            intake.get("bologna_decision_threads"),
            "Bologna decision threads missing",
        )
        if isinstance(thread, dict)
    }
    odp1 = require_mapping(threads.get(ODP_ID), f"{ODP_ID} thread missing")
    require(odp1.get("status") == "missing_owner_answer", f"{ODP_ID} status changed")
    require(odp1.get("owner_answer_references") == [], f"{ODP_ID} owner refs changed")
    require(odp1.get("downstream_updates_allowed") is False, f"{ODP_ID} updates allowed")

    pilot = load_yaml(PILOT_SCOPE_PATH)
    authority_contract = require_mapping(
        pilot.get("authority_record_contract"),
        "pilot authority record contract missing",
    )
    require(
        authority_contract.get("current_authority_records") == [],
        "pilot authority records must remain empty",
    )

    gate = require_mapping(
        load_yaml(ODP1_GATE_PATH).get("odp_bol_001_gate"),
        "ODP1 gate missing",
    )
    require(gate.get("current_owner_answer_references") == [], "gate owner refs changed")
    require(gate.get("current_authority_record_references") == [], "gate authority refs changed")


def validate_packet(payload: dict[str, Any]) -> None:
    require(
        payload.get("schema_version") == "bologna_odp1_owner_answer_packet_v1",
        "unexpected ODP-BOL-001 answer packet schema",
    )
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook path drifted")
    require(payload.get("status") == "ready_for_external_owner_response", "packet status drifted")
    require(
        payload.get("validation") == "scripts/run_bologna_odp1_owner_answer_packet_check.ps1",
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
    require(packet.get("sequence") == 1, "packet sequence changed")
    require(packet.get("source_owner_answer_intake") == OWNER_INTAKE_PATH, "intake path drifted")
    require(packet.get("source_response_gate") == ODP1_GATE_PATH, "gate path drifted")
    require(packet.get("source_pilot_scope_authority") == PILOT_SCOPE_PATH, "pilot path drifted")
    require(packet.get("current_owner_answer_references") == [], "packet owner refs must be empty")
    require(
        packet.get("current_authority_record_references") == [],
        "packet authority refs must be empty",
    )

    owner_template = require_mapping(
        packet.get("owner_answer_template"),
        "owner answer template missing",
    )
    require(set(owner_template) == owner_answer_fields(), "owner answer template fields drifted")
    require(owner_template.get("odp_id") == ODP_ID, "owner answer template ODP id changed")
    require(owner_template.get("downstream_unlocks_requested") == [], "owner template unlocks")
    require(
        list_set(packet.get("allowed_answer_types"), "allowed answer types missing")
        == allowed_owner_answer_types(),
        "allowed answer types drifted",
    )

    authority_template = require_mapping(
        packet.get("pilot_scope_authority_record_template"),
        "authority record template missing",
    )
    require(
        set(authority_template) == pilot_authority_record_fields(),
        "authority record template fields drifted",
    )
    require(
        set(require_non_empty_list(authority_template.get("scope_decision_ids"), "scope ids"))
        == pilot_scope_decisions(),
        "authority record scope decisions drifted",
    )
    require(
        authority_template.get("downstream_unlocks_requested") == [],
        "authority template unlocks",
    )

    validate_decision_checklist(payload)
    validate_outcome_policy(payload)
    validate_submission_policy(payload)
    controls = require_mapping(payload.get("no_overclaim_controls"), "no-overclaim missing")
    require(set(controls) == EXPECTED_NO_OVERCLAIM_CONTROLS, "no-overclaim controls drifted")
    for control_id, enabled in controls.items():
        require(enabled is True, f"{control_id} no-overclaim control disabled")


def validate_decision_checklist(payload: dict[str, Any]) -> None:
    checklist = require_non_empty_list(
        payload.get("decision_checklist"),
        "decision checklist missing",
    )
    requirements = odp1_gate_decision_requirements()
    by_id: dict[str, dict[str, Any]] = {}
    for raw_item in checklist:
        item = require_mapping(raw_item, "each decision checklist row must be a mapping")
        decision_id = require_text(item.get("decision_id"), "decision id missing")
        require(decision_id not in by_id, f"duplicate decision checklist id: {decision_id}")
        by_id[decision_id] = item
        source = require_mapping(
            requirements.get(decision_id),
            f"unknown decision checklist id: {decision_id}",
        )
        require(item.get("status") == "awaiting_owner_response", f"{decision_id} status drifted")
        require(item.get("authority_record_required") is True, f"{decision_id} authority flag")
        for field in ("owner_question", "must_cite", "consequence_if_missing"):
            require(item.get(field) == source.get(field), f"{decision_id} {field} drifted")
    require(set(by_id) == pilot_scope_decisions(), "decision checklist coverage drifted")


def validate_outcome_policy(payload: dict[str, Any]) -> None:
    rows = require_non_empty_list(payload.get("outcome_policy"), "outcome policy missing")
    by_type: dict[str, dict[str, Any]] = {}
    for raw_item in rows:
        item = require_mapping(raw_item, "each outcome row must be a mapping")
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
    require(
        policy.get("owner_answer_submission_target") == OWNER_INTAKE_PATH,
        "owner answer submission target drifted",
    )
    require(
        policy.get("authority_record_submission_target") == PILOT_SCOPE_PATH,
        "authority record submission target drifted",
    )
    for key in (
        "current_owner_answers_must_remain_empty",
        "current_authority_records_must_remain_empty",
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
        "config/bologna_source_authority_intake.yaml",
        "config/bologna_source_rights.yaml",
        "config/bologna_recorded_source_corpus.yaml",
    ):
        require(path_text in blocked, f"missing downstream blocker: {path_text}")


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"runbook missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_packet(load_yaml(CONFIG_PATH))
    validate_current_source_state()
    validate_runbook()
    print("Bologna ODP-BOL-001 owner answer packet check: ok")
    return 0


if __name__ == "__main__":
    import sys as _qualification_sys
    from pathlib import Path as _QualificationPath

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
