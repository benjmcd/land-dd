from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_odp4_db_report_proof_response_gate.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_odp4_db_report_proof_response_gate.md"
OWNER_INTAKE_PATH = "config/bologna_owner_answer_intake.yaml"
ODP3_GATE_PATH = "config/bologna_odp3_corpus_response_gate.yaml"
CORPUS_PATH = "config/bologna_recorded_source_corpus.yaml"
REPORT_SCHEMA_PATH = "schemas/report_run_schema.json"
EVIDENCE_SCHEMA_PATH = "schemas/evidence_schema.json"
CLAIM_SCHEMA_PATH = "schemas/claim_schema.json"
ODP_ID = "ODP-BOL-004"
PREREQUISITE_ODP_IDS = ["ODP-BOL-001", "ODP-BOL-002", "ODP-BOL-003"]

EXPECTED_APPROVALS = {
    "owner_answer_recorded": False,
    "report_proof_authority_recorded": False,
    "db_report_proof_approved": False,
    "db_seed_allowed": False,
    "db_report_run_allowed": False,
    "runtime_use_allowed": False,
    "report_artifact_allowed": False,
    "api_surface_allowed": False,
    "report_semantics_change_allowed": False,
    "downstream_authority_updates_allowed": False,
}
EXPECTED_LIMITS = {
    "validate_only_response_gate": True,
    "records_owner_answer": False,
    "records_report_proof_authority": False,
    "selects_bologna_aoi": False,
    "approves_sources": False,
    "changes_source_rights": False,
    "promotes_source_registry": False,
    "approves_recorded_corpus": False,
    "creates_recorded_fixtures": False,
    "creates_source_failure_fixtures": False,
    "runs_live_connectors": False,
    "mutates_database": False,
    "creates_db_seed": False,
    "creates_db_report_run": False,
    "creates_runtime_artifacts": False,
    "creates_report_artifacts": False,
    "changes_report_semantics": False,
    "changes_api_surface": False,
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
    "no_report_proof_authority_record_by_response_gate",
    "no_owner_answer_record_by_response_gate",
    "no_corpus_authority_record_by_response_gate",
    "no_db_seed_by_response_gate",
    "no_db_report_run_by_response_gate",
    "no_report_artifact_by_response_gate",
    "no_api_surface_by_response_gate",
    "no_report_semantics_change_by_response_gate",
    "no_runtime_use_by_response_gate",
    "no_legal_buildability_title_or_value_claim",
    "no_level_10_or_hosted_claim",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    "state/owner-decision-packet.md",
    OWNER_INTAKE_PATH,
    ODP3_GATE_PATH,
    CORPUS_PATH,
    REPORT_SCHEMA_PATH,
    EVIDENCE_SCHEMA_PATH,
    CLAIM_SCHEMA_PATH,
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "scripts/run_bologna_odp4_db_report_proof_response_gate_check.ps1",
    "scripts/run_bologna_odp4_db_report_proof_response_gate_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_odp4_db_report_proof_response_gate_v1",
    "validate-only",
    "does not record report-proof authority",
    ODP_ID,
    "ODP-BOL-001",
    "ODP-BOL-002",
    "ODP-BOL-003",
    "current_report_proof_authority_references",
    "current_db_report_run_references",
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
    require((ROOT / normalized).exists(), f"ODP-BOL-004 artifact missing: {normalized}")


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must map")


def load_json(path_text: str) -> dict[str, Any]:
    return require_mapping(json.loads(read_text(path_text)), f"{path_text} must map")


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


def report_proof_fields() -> set[str]:
    threads = _owner_threads()
    thread = require_mapping(threads.get(ODP_ID), f"{ODP_ID} thread missing")
    return list_set(
        thread.get("required_report_proof_fields"),
        "report proof fields missing",
    )


def schema_required_fields(path_text: str) -> set[str]:
    schema = load_json(path_text)
    return list_set(schema.get("required"), f"{path_text} required fields missing")


def report_run_required_fields() -> set[str]:
    return schema_required_fields(REPORT_SCHEMA_PATH)


def evidence_required_fields() -> set[str]:
    return schema_required_fields(EVIDENCE_SCHEMA_PATH)


def claim_required_fields() -> set[str]:
    return schema_required_fields(CLAIM_SCHEMA_PATH)


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
        list_set(thread.get("required_report_proof_fields"), "ODP4 fields missing")
        == {
            "one_local_db_report_run_id",
            "approved_corpus_reference",
            "evidence_ledger_rows",
            "claim_evidence_links",
            "unknowns_list",
            "caveats_list",
            "artifact_manifest",
            "source_lineage",
            "report_use_policy",
            "no_overclaim_review",
            "storage_export_boundaries",
        },
        "ODP4 owner-thread report proof fields drifted",
    )
    require(
        owner_answer_contract().get("current_owner_answers") == [],
        "owner answers must remain empty",
    )


def validate_existing_packets_still_blocked() -> None:
    odp3 = load_yaml(ODP3_GATE_PATH)
    odp3_gate = require_mapping(odp3.get("odp_bol_003_gate"), "ODP3 gate missing")
    require(
        odp3_gate.get("status") == "blocked_until_odp_bol_001_and_odp_bol_002",
        "ODP3 status changed",
    )
    require(odp3_gate.get("current_owner_answer_references") == [], "ODP3 refs changed")
    require(
        odp3_gate.get("current_corpus_authority_references") == [],
        "ODP3 corpus authority refs changed",
    )
    require(
        odp3_gate.get("current_recorded_corpus_references") == [],
        "ODP3 recorded corpus refs changed",
    )
    corpus = load_yaml(CORPUS_PATH)
    require(corpus.get("status") == "blocked_no_authority", "corpus status changed")
    for key, value in require_mapping(corpus.get("approvals"), "approvals missing").items():
        require(value is False, f"corpus approval flag enabled: {key}")


def validate_gate(payload: dict[str, Any]) -> None:
    gate = require_mapping(payload.get("odp_bol_004_gate"), "ODP-BOL-004 gate missing")
    require(gate.get("odp_id") == ODP_ID, "ODP-BOL-004 gate id changed")
    require(
        gate.get("status") == "blocked_until_odp_bol_001_odp_bol_002_and_odp_bol_003",
        "ODP4 status drifted",
    )
    require(gate.get("source_owner_answer_intake") == OWNER_INTAKE_PATH, "intake path")
    require(gate.get("source_odp3_gate") == ODP3_GATE_PATH, "ODP3 path drifted")
    require(gate.get("source_report_run_schema") == REPORT_SCHEMA_PATH, "report path")
    require(gate.get("source_evidence_schema") == EVIDENCE_SCHEMA_PATH, "evidence path")
    require(gate.get("source_claim_schema") == CLAIM_SCHEMA_PATH, "claim path")
    require(
        gate.get("prerequisite_odp_ids") == PREREQUISITE_ODP_IDS,
        "ODP4 prerequisite list drifted",
    )
    require(gate.get("prerequisite_status") == "missing_owner_answers", "prereq status")
    require(gate.get("current_owner_answer_references") == [], "owner refs changed")
    require(
        gate.get("current_report_proof_authority_references") == [],
        "report proof authority refs changed",
    )
    require(
        gate.get("current_db_report_run_references") == [],
        "DB report run refs changed",
    )
    require(
        gate.get("current_report_artifact_references") == [],
        "report artifact refs changed",
    )
    require(
        list_set(gate.get("required_owner_answer_fields"), "owner fields missing")
        == owner_answer_fields(),
        "gate owner fields drifted from owner-answer intake",
    )
    require(
        list_set(gate.get("required_report_proof_fields"), "report proof fields missing")
        == report_proof_fields(),
        "gate report proof fields drifted",
    )
    require(
        list_set(gate.get("required_report_run_contract_fields"), "report fields missing")
        == report_run_required_fields(),
        "gate report-run fields drifted",
    )
    require(
        list_set(gate.get("required_evidence_contract_fields"), "evidence fields missing")
        == evidence_required_fields(),
        "gate evidence fields drifted",
    )
    require(
        list_set(gate.get("required_claim_contract_fields"), "claim fields missing")
        == claim_required_fields(),
        "gate claim fields drifted",
    )
    require_non_empty_list(gate.get("response_acceptance"), "response acceptance missing")
    blockers = require_non_empty_list(
        gate.get("still_blocked_after_valid_response"),
        "post-response blockers missing",
    )
    for phrase in ("recording", "DB", "report", "Level 10"):
        require(any(phrase in str(item) for item in blockers), f"missing blocker {phrase}")


def validate_report_proof_requirements(payload: dict[str, Any]) -> None:
    requirements = require_non_empty_list(
        payload.get("report_proof_requirements"),
        "report proof requirements missing",
    )
    by_id: dict[str, dict[str, Any]] = {}
    for raw_item in requirements:
        item = require_mapping(raw_item, "report proof requirement must map")
        field_id = require_text(item.get("field_id"), "field id missing")
        require(field_id not in by_id, f"duplicate field: {field_id}")
        by_id[field_id] = item
        require_text(item.get("owner_question"), f"{field_id} question missing")
        require_text(item.get("consequence_if_missing"), f"{field_id} consequence")
        for citation_need in require_non_empty_list(
            item.get("must_cite"),
            f"{field_id} citation requirements missing",
        ):
            require_text(citation_need, f"{field_id} citation item missing")
    require(set(by_id) == report_proof_fields(), "report proof requirements drifted")


def validate_schema_contract_requirements(payload: dict[str, Any]) -> None:
    contracts = require_mapping(
        payload.get("schema_contract_requirements"),
        "schema contract requirements missing",
    )
    expected = {
        "report_run_contract": (REPORT_SCHEMA_PATH, report_run_required_fields()),
        "evidence_contract": (EVIDENCE_SCHEMA_PATH, evidence_required_fields()),
        "claim_contract": (CLAIM_SCHEMA_PATH, claim_required_fields()),
    }
    require(set(contracts) == set(expected), "schema contract set drifted")
    for contract_id, (path_text, required_fields) in expected.items():
        contract = require_mapping(contracts.get(contract_id), f"{contract_id} missing")
        require(contract.get("schema_path") == path_text, f"{contract_id} path drifted")
        require(
            contract.get("required_fields_source") == "required",
            f"{contract_id} source drifted",
        )
        require(
            list_set(contract.get("required_fields"), f"{contract_id} fields missing")
            == required_fields,
            f"{contract_id} required fields drifted",
        )


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
        payload.get("schema_version") == "bologna_odp4_db_report_proof_response_gate_v1",
        "unexpected ODP-BOL-004 gate schema",
    )
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook path drifted")
    require(
        payload.get("status")
        == "blocked_until_odp_bol_001_odp_bol_002_odp_bol_003_and_missing_odp_bol_004_owner_answer",
        "gate status changed",
    )
    require(
        payload.get("validation")
        == "scripts/run_bologna_odp4_db_report_proof_response_gate_check.ps1",
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
    validate_report_proof_requirements(payload)
    validate_schema_contract_requirements(payload)
    validate_outcome_matrix(payload)
    controls = require_mapping(payload.get("no_overclaim_controls"), "controls missing")
    require(set(controls) == EXPECTED_NO_OVERCLAIM_CONTROLS, "controls drifted")
    for control_id, enabled in controls.items():
        require(enabled is True, f"{control_id} disabled")
    return payload


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"ODP-BOL-004 runbook missing phrase: {phrase}")
    for field_id in report_proof_fields():
        require(f"`{field_id}`" in runbook, f"runbook missing {field_id}")
    for field_id in report_run_required_fields():
        require(f"`{field_id}`" in runbook, f"runbook missing report field {field_id}")
    for field_id in evidence_required_fields():
        require(f"`{field_id}`" in runbook, f"runbook missing evidence field {field_id}")
    for field_id in claim_required_fields():
        require(f"`{field_id}`" in runbook, f"runbook missing claim field {field_id}")


def main() -> int:
    validate_required_files()
    validate_owner_threads_still_blocked()
    validate_existing_packets_still_blocked()
    validate_catalog()
    validate_runbook()
    print("Bologna ODP-BOL-004 DB report proof response gate check: ok")
    return 0


if __name__ == "__main__":
    import sys as _qualification_sys
    from pathlib import Path as _QualificationPath

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
