from __future__ import annotations


from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_pilot_scope_authority.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_pilot_scope_authority.md"

EXPECTED_APPROVALS = {
    "product_authorizes_bologna_pilot": False,
    "one_aoi_scope_authorized": False,
    "intended_operator_named": False,
    "pilot_non_goals_reviewed": False,
    "stop_conditions_defined": False,
    "jurisdiction_boundary_reviewed": False,
    "evidence_only_or_rulepack_scope_approved": False,
    "ds017_treatment_decided": False,
    "candidate_source_selection_allowed": False,
    "source_authority_updates_allowed": False,
    "recorded_corpus_allowed": False,
    "runtime_report_proof_allowed": False,
}
EXPECTED_LIMITS = {
    "validate_only_scope_packet": True,
    "selects_bologna_aoi": False,
    "approves_sources": False,
    "changes_source_rights": False,
    "promotes_source_registry": False,
    "creates_recorded_fixtures": False,
    "runs_live_connectors": False,
    "mutates_database": False,
    "creates_runtime_artifacts": False,
    "changes_source_readiness": False,
    "approves_ds017": False,
    "claims_legal_review": False,
    "claims_hosted_production_ready": False,
    "claims_multi_geography_framework": False,
}
EXPECTED_SCOPE_DECISIONS = {
    "product_authorizes_bologna_pilot_reference",
    "one_aoi_geometry_or_named_boundary",
    "intended_operator_and_use_case",
    "pilot_non_goals_and_exclusions",
    "stop_conditions_and_reversion_plan",
    "jurisdiction_boundary_review",
    "evidence_only_or_rulepack_scope",
    "ds017_treatment_for_pilot",
    "candidate_source_selection_policy",
    "fixture_capture_boundary",
    "report_runtime_boundary",
    "no_overclaim_review_owner",
}
EXPECTED_DOWNSTREAM = {
    "bologna_source_authority_intake": "config/bologna_source_authority_intake.yaml",
    "bologna_source_rights_matrix": "config/bologna_source_rights.yaml",
    "bologna_recorded_source_corpus": "config/bologna_recorded_source_corpus.yaml",
}
EXPECTED_AUTHORITY_RECORD_FIELDS = {
    "authority_record_id",
    "authority_type",
    "authority_reference",
    "decision_owner",
    "decision_date",
    "effective_date",
    "scope_decision_ids",
    "decision_summary",
    "evidence_summary",
    "cited_artifacts",
    "downstream_unlocks_requested",
    "caveats",
    "stop_conditions",
    "supersedes_authority_record_ids",
}
EXPECTED_AUTHORITY_TYPES = {
    "product_decision",
    "aoi_boundary_decision",
    "operator_use_case_decision",
    "non_goal_review",
    "jurisdiction_review",
    "scope_mode_decision",
    "ds017_treatment_decision",
    "source_selection_policy",
    "fixture_boundary_decision",
    "runtime_boundary_decision",
    "no_overclaim_review",
}
EXPECTED_NO_OVERCLAIM_CONTROLS = {
    "no_source_approval_by_pilot_scope_record",
    "no_source_rights_change_by_pilot_scope_record",
    "no_fixture_capture_by_pilot_scope_record",
    "no_runtime_report_use_by_pilot_scope_record",
    "no_db_seed_by_pilot_scope_record",
    "no_legal_buildability_title_or_value_claim",
    "no_level_10_or_hosted_claim",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "config/bologna_preflight.yaml",
    "config/bologna_source_candidates.yaml",
    "config/bologna_source_authority_intake.yaml",
    "config/bologna_source_rights.yaml",
    "config/bologna_recorded_source_corpus.yaml",
    "docs/checklists/jurisdiction_readiness.md",
    "docs/checklists/rulepack_readiness.md",
    "scripts/run_bologna_pilot_scope_authority_check.ps1",
    "scripts/run_bologna_pilot_scope_authority_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_pilot_scope_authority_v1",
    "validate-only",
    "does not select a Bologna AOI",
    "does not approve Italy/EU/local sources",
    "scope_decision_requests",
    "authority_record_contract",
    "ready_for_external_authority_evidence",
    "authority_state",
    "decision_updates_allowed",
    "config/bologna_source_authority_intake.yaml",
    "config/bologna_recorded_source_corpus.yaml",
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
    require((ROOT / normalized).exists(), f"pilot-scope artifact missing: {normalized}")


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(
        yaml.safe_load(read_text(path_text)),
        f"{path_text} must be a mapping",
    )


def list_set(value: Any, message: str) -> set[str]:
    return {str(item) for item in require_non_empty_list(value, message)}


def validate_scope_decision_requests(payload: dict[str, Any]) -> None:
    raw_requests = require_non_empty_list(
        payload.get("scope_decision_requests"),
        "scope decision requests missing",
    )
    requests_by_id: dict[str, dict[str, Any]] = {}
    for raw_request in raw_requests:
        request = require_mapping(
            raw_request,
            "each scope decision request must be a mapping",
        )
        request_id = require_text(request.get("id"), "scope decision request id missing")
        require(
            request_id not in requests_by_id,
            f"duplicate scope decision request: {request_id}",
        )
        requests_by_id[request_id] = request
        require(
            request.get("status") == "missing_authority",
            f"{request_id} scope request status changed",
        )
        require_text(
            request.get("expected_reference"),
            f"{request_id} expected reference missing",
        )
        for evidence_item in require_non_empty_list(
            request.get("minimum_evidence"),
            f"{request_id} minimum evidence missing",
        ):
            require_text(evidence_item, f"{request_id} minimum evidence item missing")
        require_text(request.get("downstream_use"), f"{request_id} downstream use missing")
        require(
            request.get("authority_references") == [],
            f"{request_id} authority references changed",
        )
        require(
            request.get("decision_updates_allowed") is False,
            f"{request_id} updates unexpectedly allowed",
        )
    require(
        set(requests_by_id) == EXPECTED_SCOPE_DECISIONS,
        "scope decision requests drifted from required decisions",
    )


def validate_authority_record_contract(payload: dict[str, Any]) -> None:
    contract = require_mapping(
        payload.get("authority_record_contract"),
        "authority record contract missing",
    )
    require(
        contract.get("contract_state") == "ready_for_external_authority_evidence",
        "authority record contract state changed",
    )
    require(
        contract.get("current_authority_records") == [],
        "authority records must remain empty until cited authority exists",
    )
    require(
        list_set(contract.get("required_record_fields"), "authority record fields missing")
        == EXPECTED_AUTHORITY_RECORD_FIELDS,
        "authority record fields drifted",
    )
    require(
        list_set(contract.get("allowed_authority_types"), "authority types missing")
        == EXPECTED_AUTHORITY_TYPES,
        "authority types drifted",
    )
    require(
        list_set(
            contract.get("required_scope_decision_coverage"),
            "authority record coverage missing",
        )
        == EXPECTED_SCOPE_DECISIONS,
        "authority record coverage drifted",
    )
    require(
        contract.get("coverage_policy") == "all_required_scope_decisions",
        "authority record coverage policy changed",
    )
    require(
        contract.get("decision_update_policy") == "disabled_until_complete_cited_record",
        "authority record decision update policy changed",
    )
    controls = require_mapping(
        contract.get("no_overclaim_controls"),
        "authority record no-overclaim controls missing",
    )
    require(
        set(controls) == EXPECTED_NO_OVERCLAIM_CONTROLS,
        "authority record no-overclaim controls drifted",
    )
    for control_id, enabled in controls.items():
        require(enabled is True, f"{control_id} no-overclaim control disabled")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_catalog() -> dict[str, Any]:
    payload = load_yaml(CONFIG_PATH)
    require(
        payload.get("schema_version") == "bologna_pilot_scope_authority_v1",
        "unexpected schema",
    )
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook mismatch")
    require(
        payload.get("status") == "blocked_no_pilot_scope_authority",
        "pilot-scope authority must remain blocked",
    )
    require(
        payload.get("validation") == "scripts/run_bologna_pilot_scope_authority_check.ps1",
        "validation wrapper mismatch",
    )
    for path_text in require_non_empty_list(payload.get("authority"), "authority paths missing"):
        require(isinstance(path_text, str), "authority paths must be strings")
        require_existing(path_text)
    require(
        require_mapping(payload.get("approvals"), "approvals missing") == EXPECTED_APPROVALS,
        "pilot-scope approvals changed",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "pilot-scope limits changed",
    )
    require(
        list_set(payload.get("required_scope_decisions"), "scope decisions missing")
        == EXPECTED_SCOPE_DECISIONS,
        "required scope decisions changed",
    )
    validate_scope_decision_requests(payload)
    validate_authority_record_contract(payload)
    review = require_mapping(
        payload.get("scope_authority_review"),
        "scope authority review missing",
    )
    require(
        review.get("authority_state") == "missing_authority",
        "scope authority state must remain missing",
    )
    require(review.get("evidence_status") == "missing", "scope evidence status changed")
    require(
        list_set(review.get("evidence_slots"), "scope evidence slots missing")
        == EXPECTED_SCOPE_DECISIONS,
        "scope evidence slots drifted",
    )
    require(review.get("authority_references") == [], "scope authority references changed")
    require(
        review.get("decision_updates_allowed") is False,
        "scope decision updates unexpectedly allowed",
    )

    downstream = require_non_empty_list(payload.get("downstream_unlocks"), "downstream missing")
    downstream_by_id: dict[str, dict[str, Any]] = {}
    for raw_item in downstream:
        item = require_mapping(raw_item, "each downstream unlock must be a mapping")
        item_id = require_text(item.get("id"), "downstream id missing")
        require(item_id not in downstream_by_id, f"duplicate downstream unlock: {item_id}")
        downstream_by_id[item_id] = item
    require(set(downstream_by_id) == set(EXPECTED_DOWNSTREAM), "downstream set changed")
    for item_id, target_catalog in EXPECTED_DOWNSTREAM.items():
        item = downstream_by_id[item_id]
        require(item.get("target_catalog") == target_catalog, f"{item_id} target mismatch")
        require_existing(target_catalog)
        require_text(item.get("status"), f"{item_id} status missing")
        require(item.get("update_allowed") is False, f"{item_id} updates unexpectedly allowed")
    require_non_empty_list(payload.get("unlock_conditions"), "unlock conditions missing")
    return payload


def validate_runbook(payload: dict[str, Any]) -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"pilot-scope runbook missing phrase: {phrase}")
    for item in require_non_empty_list(
        payload.get("required_scope_decisions"),
        "scope decisions missing",
    ):
        decision = require_text(item, "scope decision missing")
        require(f"`{decision}`" in runbook, f"pilot-scope runbook missing {decision}")


def main() -> int:
    validate_required_files()
    payload = validate_catalog()
    validate_runbook(payload)
    print("Bologna pilot scope authority check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
