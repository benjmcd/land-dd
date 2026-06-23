from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_odp2_source_rights_response_gate.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_odp2_source_rights_response_gate.md"
OWNER_INTAKE_PATH = "config/bologna_owner_answer_intake.yaml"
ODP1_GATE_PATH = "config/bologna_odp1_owner_response_gate.yaml"
SOURCE_AUTHORITY_PATH = "config/bologna_source_authority_intake.yaml"
SOURCE_RIGHTS_PATH = "config/bologna_source_rights.yaml"
ODP_ID = "ODP-BOL-002"
PREREQUISITE_ODP_ID = "ODP-BOL-001"

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
    "validate_only_response_gate": True,
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
EXPECTED_ANSWER_TYPES = {
    "approve_with_cited_authority",
    "keep_blocked",
    "approve_review_only",
    "exclude_or_defer",
}
EXPECTED_NO_OVERCLAIM_CONTROLS = {
    "no_authority_by_response_gate",
    "no_source_authority_record_by_response_gate",
    "no_source_approval_by_response_gate",
    "no_source_rights_change_by_response_gate",
    "no_source_registry_promotion_by_response_gate",
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
    ODP1_GATE_PATH,
    SOURCE_AUTHORITY_PATH,
    SOURCE_RIGHTS_PATH,
    "config/bologna_recorded_source_corpus.yaml",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "scripts/run_bologna_odp2_source_rights_response_gate_check.ps1",
    "scripts/run_bologna_odp2_source_rights_response_gate_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_odp2_source_rights_response_gate_v1",
    "validate-only",
    "does not record source authority",
    ODP_ID,
    PREREQUISITE_ODP_ID,
    "current_source_authority_record_references",
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
    require((ROOT / normalized).exists(), f"ODP-BOL-002 artifact missing: {normalized}")


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must map")


def list_set(value: Any, message: str) -> set[str]:
    return {str(item) for item in require_non_empty_list(value, message)}


def owner_answer_contract() -> dict[str, Any]:
    intake = load_yaml(OWNER_INTAKE_PATH)
    return require_mapping(
        intake.get("owner_answer_contract"),
        "owner answer contract missing",
    )


def owner_answer_fields() -> set[str]:
    contract = owner_answer_contract()
    return list_set(contract.get("required_record_fields"), "owner fields missing")


def allowed_owner_answer_types() -> set[str]:
    contract = owner_answer_contract()
    return list_set(contract.get("allowed_answer_types"), "answer types missing")


def source_authority_contract() -> dict[str, Any]:
    payload = load_yaml(SOURCE_AUTHORITY_PATH)
    return require_mapping(
        payload.get("source_authority_record_contract"),
        "source authority record contract missing",
    )


def source_authority_record_fields() -> set[str]:
    contract = source_authority_contract()
    return list_set(
        contract.get("required_record_fields"),
        "source authority fields missing",
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


def source_authority_evidence_slots() -> dict[str, set[str]]:
    payload = load_yaml(SOURCE_AUTHORITY_PATH)
    slots: dict[str, set[str]] = {}
    for raw_review in require_non_empty_list(
        payload.get("candidate_authority_reviews"),
        "candidate authority reviews missing",
    ):
        review = require_mapping(raw_review, "authority review must map")
        candidate_id = require_text(review.get("candidate_id"), "candidate id missing")
        slots[candidate_id] = list_set(
            review.get("evidence_slots"),
            f"{candidate_id} evidence slots missing",
        )
    cadastral = require_mapping(
        payload.get("cadastral_authority_review"),
        "cadastral authority review missing",
    )
    slots["cadastral_gap"] = list_set(
        cadastral.get("evidence_slots"),
        "cadastral evidence slots missing",
    )
    return slots


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def _owner_threads() -> dict[str, dict[str, Any]]:
    intake = load_yaml(OWNER_INTAKE_PATH)
    return {
        require_text(thread.get("odp_id"), "ODP thread id missing"): thread
        for thread in require_non_empty_list(
            intake.get("bologna_decision_threads"),
            "Bologna decision threads missing",
        )
        if isinstance(thread, dict)
    }


def validate_source_packets_still_blocked() -> None:
    threads = _owner_threads()
    thread = require_mapping(threads.get(ODP_ID), f"{ODP_ID} thread missing")
    require(thread.get("status") == "missing_owner_answer", f"{ODP_ID} changed")
    require(
        thread.get("prerequisite_odp_ids") == [PREREQUISITE_ODP_ID],
        f"{ODP_ID} prerequisite drifted",
    )
    require(thread.get("owner_answer_references") == [], f"{ODP_ID} refs changed")
    require(thread.get("downstream_updates_allowed") is False, f"{ODP_ID} unlocked")

    prerequisite = require_mapping(
        threads.get(PREREQUISITE_ODP_ID),
        f"{PREREQUISITE_ODP_ID} thread missing",
    )
    require(
        prerequisite.get("status") == "missing_owner_answer",
        f"{PREREQUISITE_ODP_ID} answered before ODP2 gate",
    )
    require(
        prerequisite.get("owner_answer_references") == [],
        f"{PREREQUISITE_ODP_ID} refs changed",
    )
    require(
        owner_answer_contract().get("current_owner_answers") == [],
        "owner answers must remain empty",
    )

    odp1 = load_yaml(ODP1_GATE_PATH)
    odp1_gate = require_mapping(odp1.get("odp_bol_001_gate"), "ODP1 gate missing")
    require(odp1_gate.get("status") == "missing_owner_answer", "ODP1 status changed")
    require(odp1_gate.get("current_owner_answer_references") == [], "ODP1 refs changed")
    require(
        odp1_gate.get("current_authority_record_references") == [],
        "ODP1 authority refs changed",
    )

    source_contract = source_authority_contract()
    require(
        source_contract.get("current_source_authority_records") == [],
        "source authority records must remain empty",
    )

    rights = load_yaml(SOURCE_RIGHTS_PATH)
    require(
        rights.get("approvals", {}).get("any_source_approved") is False,
        "source rights now approve a source",
    )
    require(
        rights.get("approvals", {}).get("recorded_source_corpus_allowed") is False,
        "source rights now allow a corpus",
    )
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
        require(
            set(require_mapping(review.get("rights_decisions"), "rights missing"))
            == source_rights_decisions(),
            f"{candidate_id} rights decisions drifted",
        )
        promotion = require_mapping(review.get("promotion"), "promotion missing")
        for key, value in promotion.items():
            require(value is False, f"{candidate_id} promotion flag enabled: {key}")
    cadastral = require_mapping(rights.get("cadastral_gap"), "cadastral gap missing")
    require(
        cadastral.get("status") == "direct_source_review_required",
        "cadastral gap status changed",
    )
    for key, value in require_mapping(cadastral.get("approval"), "approval missing").items():
        require(value is False, f"cadastral approval flag enabled: {key}")


def validate_gate(payload: dict[str, Any]) -> None:
    gate = require_mapping(payload.get("odp_bol_002_gate"), "ODP-BOL-002 gate missing")
    require(gate.get("odp_id") == ODP_ID, "ODP-BOL-002 gate id changed")
    require(gate.get("status") == "blocked_until_odp_bol_001", "ODP2 status drifted")
    require(gate.get("source_owner_answer_intake") == OWNER_INTAKE_PATH, "intake path")
    require(gate.get("source_odp1_gate") == ODP1_GATE_PATH, "ODP1 path drifted")
    require(
        gate.get("source_source_authority_packet") == SOURCE_AUTHORITY_PATH,
        "source authority path drifted",
    )
    require(gate.get("source_rights_packet") == SOURCE_RIGHTS_PATH, "rights path")
    require(
        gate.get("prerequisite_odp_ids") == [PREREQUISITE_ODP_ID],
        "ODP2 prerequisite list drifted",
    )
    require(gate.get("prerequisite_status") == "missing_owner_answer", "prereq status")
    require(gate.get("current_owner_answer_references") == [], "owner refs changed")
    require(
        gate.get("current_source_authority_record_references") == [],
        "source authority refs changed",
    )
    require(
        gate.get("current_source_rights_approval_references") == [],
        "source rights approval refs changed",
    )
    require(
        list_set(gate.get("required_owner_answer_fields"), "owner fields missing")
        == owner_answer_fields(),
        "gate owner fields drifted from owner-answer intake",
    )
    require(
        list_set(
            gate.get("required_source_authority_record_fields"),
            "source authority fields missing",
        )
        == source_authority_record_fields(),
        "gate source authority fields drifted",
    )
    require(
        list_set(gate.get("required_rights_decisions"), "rights decisions missing")
        == source_rights_decisions(),
        "gate rights decisions drifted",
    )
    require(
        list_set(gate.get("candidate_review_ids"), "candidate ids missing")
        == source_rights_candidate_ids(),
        "gate candidate ids drifted",
    )
    require_non_empty_list(gate.get("response_acceptance"), "response acceptance missing")
    blockers = require_non_empty_list(
        gate.get("still_blocked_after_valid_response"),
        "post-response blockers missing",
    )
    for phrase in ("ODP-BOL-003", "ODP-BOL-004", "BSA-001"):
        require(any(phrase in str(item) for item in blockers), f"missing blocker {phrase}")


def validate_candidate_review_requirements(payload: dict[str, Any]) -> None:
    requirements = require_non_empty_list(
        payload.get("candidate_review_requirements"),
        "candidate review requirements missing",
    )
    expected_slots = source_authority_evidence_slots()
    by_id: dict[str, dict[str, Any]] = {}
    for raw_item in requirements:
        item = require_mapping(raw_item, "candidate requirement must map")
        candidate_id = require_text(item.get("candidate_id"), "candidate id missing")
        require(candidate_id not in by_id, f"duplicate candidate: {candidate_id}")
        by_id[candidate_id] = item
        require(
            list_set(item.get("required_evidence"), f"{candidate_id} evidence missing")
            == expected_slots[candidate_id],
            f"{candidate_id} evidence slots drifted",
        )
        expected_state = (
            "direct_source_review_required"
            if candidate_id == "cadastral_gap"
            else "pending_external_review"
        )
        require(item.get("decision_state") == expected_state, f"{candidate_id} state")
        require(
            item.get("downstream_updates_allowed") is False,
            f"{candidate_id} downstream updates enabled",
        )
    require(set(by_id) == source_rights_candidate_ids(), "candidate requirements drifted")


def validate_decision_requirements(payload: dict[str, Any]) -> None:
    requirements = require_non_empty_list(
        payload.get("decision_requirements"),
        "decision requirements missing",
    )
    by_id: dict[str, dict[str, Any]] = {}
    for raw_item in requirements:
        item = require_mapping(raw_item, "decision requirement must map")
        decision_id = require_text(item.get("decision_id"), "decision id missing")
        require(decision_id not in by_id, f"duplicate decision: {decision_id}")
        by_id[decision_id] = item
        require_text(item.get("owner_question"), f"{decision_id} question missing")
        require_text(item.get("consequence_if_missing"), f"{decision_id} consequence")
        for citation_need in require_non_empty_list(
            item.get("must_cite"),
            f"{decision_id} citation requirements missing",
        ):
            require_text(citation_need, f"{decision_id} citation item missing")
    require(set(by_id) == source_rights_decisions(), "decision requirements drifted")


def validate_outcome_matrix(payload: dict[str, Any]) -> None:
    outcomes = require_non_empty_list(payload.get("outcome_matrix"), "outcomes missing")
    by_type: dict[str, dict[str, Any]] = {}
    for raw_item in outcomes:
        item = require_mapping(raw_item, "outcome row must map")
        answer_type = require_text(item.get("answer_type"), "answer type missing")
        require(answer_type not in by_type, f"duplicate answer type: {answer_type}")
        by_type[answer_type] = item
        require_text(item.get("expected_effect"), f"{answer_type} effect missing")
        require(
            item.get("downstream_updates_allowed") is False,
            f"{answer_type} unexpectedly allows downstream updates",
        )
        require_non_empty_list(item.get("still_disallowed"), f"{answer_type} disallowed")
    require(set(by_type) == EXPECTED_ANSWER_TYPES, "outcome answer types drifted")
    require(set(by_type) == allowed_owner_answer_types(), "outcomes drifted from intake")


def validate_catalog() -> dict[str, Any]:
    payload = load_yaml(CONFIG_PATH)
    require(
        payload.get("schema_version")
        == "bologna_odp2_source_rights_response_gate_v1",
        "unexpected ODP-BOL-002 gate schema",
    )
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook path drifted")
    require(
        payload.get("status")
        == "blocked_until_odp_bol_001_and_missing_odp_bol_002_owner_answer",
        "gate status changed",
    )
    require(
        payload.get("validation")
        == "scripts/run_bologna_odp2_source_rights_response_gate_check.ps1",
        "validation wrapper drifted",
    )
    for path_text in require_non_empty_list(payload.get("authority"), "authority missing"):
        require(isinstance(path_text, str), "authority paths must be strings")
        require_existing(path_text)
    require(
        require_mapping(payload.get("approvals"), "approvals missing")
        == EXPECTED_APPROVALS,
        "approvals changed",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "limits changed",
    )
    validate_gate(payload)
    validate_candidate_review_requirements(payload)
    validate_decision_requirements(payload)
    validate_outcome_matrix(payload)
    controls = require_mapping(payload.get("no_overclaim_controls"), "controls missing")
    require(set(controls) == EXPECTED_NO_OVERCLAIM_CONTROLS, "controls drifted")
    for control_id, enabled in controls.items():
        require(enabled is True, f"{control_id} disabled")
    return payload


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"ODP-BOL-002 runbook missing phrase: {phrase}")
    for decision_id in source_rights_decisions():
        require(f"`{decision_id}`" in runbook, f"runbook missing {decision_id}")
    for candidate_id in source_rights_candidate_ids():
        require(f"`{candidate_id}`" in runbook, f"runbook missing {candidate_id}")


def main() -> int:
    validate_required_files()
    validate_source_packets_still_blocked()
    validate_catalog()
    validate_runbook()
    print("Bologna ODP-BOL-002 source-rights response gate check: ok")
    return 0


if __name__ == "__main__":
    import sys as _qualification_sys
    from pathlib import Path as _QualificationPath

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
