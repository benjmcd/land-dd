from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_odp3_corpus_response_gate.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_odp3_corpus_response_gate.md"
OWNER_INTAKE_PATH = "config/bologna_owner_answer_intake.yaml"
ODP2_GATE_PATH = "config/bologna_odp2_source_rights_response_gate.yaml"
CORPUS_PATH = "config/bologna_recorded_source_corpus.yaml"
SOURCE_AUTHORITY_PATH = "config/bologna_source_authority_intake.yaml"
SOURCE_RIGHTS_PATH = "config/bologna_source_rights.yaml"
ODP_ID = "ODP-BOL-003"
PREREQUISITE_ODP_IDS = ["ODP-BOL-001", "ODP-BOL-002"]

EXPECTED_APPROVALS = {
    "owner_answer_recorded": False,
    "corpus_authority_recorded": False,
    "recorded_corpus_approved": False,
    "recorded_fixture_capture_allowed": False,
    "source_failure_fixture_capture_allowed": False,
    "runtime_use_allowed": False,
    "report_use_allowed": False,
    "db_seed_allowed": False,
    "db_report_proof_allowed": False,
    "downstream_authority_updates_allowed": False,
}
EXPECTED_LIMITS = {
    "validate_only_response_gate": True,
    "records_owner_answer": False,
    "records_corpus_authority": False,
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
    "no_corpus_authority_record_by_response_gate",
    "no_source_approval_by_response_gate",
    "no_source_rights_change_by_response_gate",
    "no_source_registry_promotion_by_response_gate",
    "no_fixture_capture_by_response_gate",
    "no_source_failure_fixture_capture_by_response_gate",
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
    ODP2_GATE_PATH,
    CORPUS_PATH,
    SOURCE_AUTHORITY_PATH,
    SOURCE_RIGHTS_PATH,
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "scripts/run_bologna_odp3_corpus_response_gate_check.ps1",
    "scripts/run_bologna_odp3_corpus_response_gate_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_odp3_corpus_response_gate_v1",
    "validate-only",
    "does not record corpus authority",
    ODP_ID,
    "ODP-BOL-001",
    "ODP-BOL-002",
    "current_corpus_authority_references",
    "current_recorded_corpus_references",
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
    require((ROOT / normalized).exists(), f"ODP-BOL-003 artifact missing: {normalized}")


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must map")


def list_set(value: Any, message: str) -> set[str]:
    return {str(item) for item in require_non_empty_list(value, message)}


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


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


def allowed_owner_answer_types() -> set[str]:
    return list_set(
        owner_answer_contract().get("allowed_answer_types"),
        "answer types missing",
    )


def corpus_decisions() -> set[str]:
    corpus = load_yaml(CORPUS_PATH)
    return list_set(corpus.get("required_corpus_decisions"), "corpus decisions missing")


def corpus_manifest_fields() -> set[str]:
    corpus = load_yaml(CORPUS_PATH)
    return list_set(corpus.get("required_manifest_fields"), "manifest fields missing")


def corpus_candidate_requirements() -> dict[str, dict[str, Any]]:
    corpus = load_yaml(CORPUS_PATH)
    requirements: dict[str, dict[str, Any]] = {}
    for raw_review in require_non_empty_list(
        corpus.get("candidate_corpus_reviews"),
        "candidate corpus reviews missing",
    ):
        review = require_mapping(raw_review, "candidate corpus review must map")
        candidate_id = require_text(review.get("candidate_id"), "candidate id missing")
        require(candidate_id not in requirements, f"duplicate candidate: {candidate_id}")
        requirements[candidate_id] = review
    cadastral = require_mapping(
        corpus.get("cadastral_corpus_review"),
        "cadastral corpus review missing",
    )
    requirements["cadastral_gap"] = cadastral
    return requirements


def candidate_ids() -> set[str]:
    return set(corpus_candidate_requirements())


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


def validate_owner_threads_still_blocked() -> None:
    threads = _owner_threads()
    for odp_id in (*PREREQUISITE_ODP_IDS, ODP_ID):
        thread = require_mapping(threads.get(odp_id), f"{odp_id} thread missing")
        require(thread.get("status") == "missing_owner_answer", f"{odp_id} changed")
        require(thread.get("owner_answer_references") == [], f"{odp_id} refs changed")
        require(thread.get("downstream_updates_allowed") is False, f"{odp_id} unlocked")
    thread = threads[ODP_ID]
    require(
        thread.get("prerequisite_odp_ids") == PREREQUISITE_ODP_IDS,
        f"{ODP_ID} prerequisites drifted",
    )
    require(
        list_set(thread.get("required_corpus_decisions"), "ODP3 decisions missing")
        == corpus_decisions(),
        "ODP3 owner-thread corpus decisions drifted",
    )
    require(
        list_set(thread.get("required_manifest_fields"), "ODP3 fields missing")
        == corpus_manifest_fields(),
        "ODP3 owner-thread manifest fields drifted",
    )
    require(
        owner_answer_contract().get("current_owner_answers") == [],
        "owner answers must remain empty",
    )


def validate_existing_packets_still_blocked() -> None:
    odp2 = load_yaml(ODP2_GATE_PATH)
    odp2_gate = require_mapping(odp2.get("odp_bol_002_gate"), "ODP2 gate missing")
    require(odp2_gate.get("status") == "blocked_until_odp_bol_001", "ODP2 status")
    require(odp2_gate.get("current_owner_answer_references") == [], "ODP2 refs changed")
    require(
        odp2_gate.get("current_source_authority_record_references") == [],
        "ODP2 source authority refs changed",
    )
    require(
        odp2_gate.get("current_source_rights_approval_references") == [],
        "ODP2 source rights approval refs changed",
    )
    corpus = load_yaml(CORPUS_PATH)
    require(corpus.get("status") == "blocked_no_authority", "corpus status changed")
    for key, value in require_mapping(corpus.get("approvals"), "approvals missing").items():
        require(value is False, f"corpus approval flag enabled: {key}")
    for key, value in require_mapping(corpus.get("limits"), "limits missing").items():
        if key == "validate_only_contract":
            require(value is True, "corpus validate-only flag disabled")
        else:
            require(value is False, f"corpus limit flag enabled: {key}")


def validate_gate(payload: dict[str, Any]) -> None:
    gate = require_mapping(payload.get("odp_bol_003_gate"), "ODP-BOL-003 gate missing")
    require(gate.get("odp_id") == ODP_ID, "ODP-BOL-003 gate id changed")
    require(
        gate.get("status") == "blocked_until_odp_bol_001_and_odp_bol_002",
        "ODP3 status drifted",
    )
    require(gate.get("source_owner_answer_intake") == OWNER_INTAKE_PATH, "intake path")
    require(gate.get("source_odp2_gate") == ODP2_GATE_PATH, "ODP2 path drifted")
    require(
        gate.get("source_recorded_corpus_contract") == CORPUS_PATH,
        "corpus path drifted",
    )
    require(
        gate.get("prerequisite_odp_ids") == PREREQUISITE_ODP_IDS,
        "ODP3 prerequisite list drifted",
    )
    require(gate.get("prerequisite_status") == "missing_owner_answers", "prereq status")
    require(gate.get("current_owner_answer_references") == [], "owner refs changed")
    require(
        gate.get("current_corpus_authority_references") == [],
        "corpus authority refs changed",
    )
    require(
        gate.get("current_recorded_corpus_references") == [],
        "recorded corpus refs changed",
    )
    require(
        list_set(gate.get("required_owner_answer_fields"), "owner fields missing")
        == owner_answer_fields(),
        "gate owner fields drifted from owner-answer intake",
    )
    require(
        list_set(gate.get("required_corpus_decisions"), "corpus decisions missing")
        == corpus_decisions(),
        "gate corpus decisions drifted",
    )
    require(
        list_set(gate.get("required_manifest_fields"), "manifest fields missing")
        == corpus_manifest_fields(),
        "gate manifest fields drifted",
    )
    require(
        list_set(gate.get("candidate_review_ids"), "candidate ids missing")
        == candidate_ids(),
        "gate candidate ids drifted",
    )
    require_non_empty_list(gate.get("response_acceptance"), "response acceptance missing")
    blockers = require_non_empty_list(
        gate.get("still_blocked_after_valid_response"),
        "post-response blockers missing",
    )
    for phrase in ("ODP-BOL-004", "fixture", "DB", "Level 10"):
        require(any(phrase in str(item) for item in blockers), f"missing blocker {phrase}")


def validate_candidate_corpus_requirements(payload: dict[str, Any]) -> None:
    requirements = require_non_empty_list(
        payload.get("candidate_corpus_requirements"),
        "candidate corpus requirements missing",
    )
    expected = corpus_candidate_requirements()
    by_id: dict[str, dict[str, Any]] = {}
    for raw_item in requirements:
        item = require_mapping(raw_item, "candidate requirement must map")
        candidate_id = require_text(item.get("candidate_id"), "candidate id missing")
        require(candidate_id not in by_id, f"duplicate candidate: {candidate_id}")
        by_id[candidate_id] = item
        expected_item = expected[candidate_id]
        require(
            list_set(
                item.get("required_manifest_evidence"),
                f"{candidate_id} manifest evidence missing",
            )
            == list_set(
                expected_item.get("required_manifest_evidence"),
                f"{candidate_id} corpus evidence missing",
            ),
            f"{candidate_id} evidence drifted",
        )
        require(
            item.get("corpus_state") == expected_item.get("corpus_state"),
            f"{candidate_id} corpus state drifted",
        )
        for flag in (
            "fixture_manifest_entry_allowed",
            "source_failure_fixture_allowed",
        ):
            require(item.get(flag) is False, f"{candidate_id} enabled {flag}")
            require(item.get(flag) == expected_item.get(flag), f"{candidate_id} {flag}")
        require(
            item.get("downstream_updates_allowed") is False,
            f"{candidate_id} downstream updates enabled",
        )
    require(set(by_id) == candidate_ids(), "candidate corpus requirements drifted")


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
    require(set(by_id) == corpus_decisions(), "decision requirements drifted")


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
        payload.get("schema_version") == "bologna_odp3_corpus_response_gate_v1",
        "unexpected ODP-BOL-003 gate schema",
    )
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook path drifted")
    require(
        payload.get("status")
        == "blocked_until_odp_bol_001_odp_bol_002_and_missing_odp_bol_003_owner_answer",
        "gate status changed",
    )
    require(
        payload.get("validation")
        == "scripts/run_bologna_odp3_corpus_response_gate_check.ps1",
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
    validate_candidate_corpus_requirements(payload)
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
        require(phrase in runbook, f"ODP-BOL-003 runbook missing phrase: {phrase}")
    for decision_id in corpus_decisions():
        require(f"`{decision_id}`" in runbook, f"runbook missing {decision_id}")
    for candidate_id in candidate_ids():
        require(f"`{candidate_id}`" in runbook, f"runbook missing {candidate_id}")


def main() -> int:
    validate_required_files()
    validate_owner_threads_still_blocked()
    validate_existing_packets_still_blocked()
    validate_catalog()
    validate_runbook()
    print("Bologna ODP-BOL-003 corpus response gate check: ok")
    return 0


if __name__ == "__main__":
    import sys as _qualification_sys
    from pathlib import Path as _QualificationPath

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
