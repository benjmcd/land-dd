from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from authority_check_lib import (  # noqa: E402
    build_summary as _build_summary,
    format_summary as _format_summary,
    list_set,
    load_yaml as _load_yaml,
    read_text as _read_text,
    require,
    require_existing as _require_existing,
    require_iso_date,
    require_list,
    require_mapping,
    require_non_empty_list,
    require_text,
    row_summary,
    run_reporting_cli,
)

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
    "complete-record-only",
    "ready_for_external_authority_evidence",
    "authority_state",
    "decision_updates_allowed",
    "config/bologna_source_authority_intake.yaml",
    "config/bologna_recorded_source_corpus.yaml",
)


def require_existing(path_text: str) -> None:
    _require_existing(path_text, "pilot-scope artifact missing")


def read_text(path_text: str) -> str:
    return _read_text(path_text)


def load_yaml(path_text: str) -> dict[str, Any]:
    return _load_yaml(path_text, reader=read_text)


def require_text_list(value: Any, message: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, message)
    if not allow_empty and not items:
        raise SystemExit(message)
    return [require_text(item, message) for item in items]


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


def validate_authority_record(record: dict[str, Any]) -> tuple[str, set[str]]:
    require(
        set(record) == EXPECTED_AUTHORITY_RECORD_FIELDS,
        "authority record fields drifted",
    )
    record_id = require_text(
        record.get("authority_record_id"),
        "authority record id missing",
    )
    authority_type = require_text(
        record.get("authority_type"),
        f"{record_id} authority type missing",
    )
    require(
        authority_type in EXPECTED_AUTHORITY_TYPES,
        f"{record_id} authority type is not allowed",
    )
    require_text(record.get("authority_reference"), f"{record_id} authority reference missing")
    require_text(record.get("decision_owner"), f"{record_id} decision owner missing")
    require_iso_date(record.get("decision_date"), f"{record_id} decision date must be ISO")
    require_iso_date(record.get("effective_date"), f"{record_id} effective date must be ISO")
    scope_decision_ids = list_set(
        record.get("scope_decision_ids"),
        f"{record_id} scope decision ids missing",
    )
    unknown_decisions = scope_decision_ids - EXPECTED_SCOPE_DECISIONS
    require(
        not unknown_decisions,
        f"{record_id} unknown scope decisions: {sorted(unknown_decisions)}",
    )
    require_text(record.get("decision_summary"), f"{record_id} decision summary missing")
    require_text(record.get("evidence_summary"), f"{record_id} evidence summary missing")
    require_text_list(record.get("cited_artifacts"), f"{record_id} cited artifacts missing")
    require(
        require_list(
            record.get("downstream_unlocks_requested"),
            f"{record_id} downstream unlock requests missing",
        )
        == [],
        f"{record_id} must not request downstream unlocks",
    )
    require_text_list(record.get("caveats"), f"{record_id} caveats missing")
    require_text_list(record.get("stop_conditions"), f"{record_id} stop conditions missing")
    require_text_list(
        record.get("supersedes_authority_record_ids"),
        f"{record_id} superseded authority record ids must be text",
        allow_empty=True,
    )
    return record_id, scope_decision_ids


def validate_authority_records(contract: dict[str, Any]) -> None:
    records = require_list(
        contract.get("current_authority_records"),
        "authority records must be a list",
    )
    if not records:
        return

    record_ids: set[str] = set()
    covered_scope_decisions: set[str] = set()
    for raw_record in records:
        record = require_mapping(raw_record, "each authority record must be a mapping")
        record_id, scope_decision_ids = validate_authority_record(record)
        require(record_id not in record_ids, f"duplicate authority record id: {record_id}")
        record_ids.add(record_id)
        covered_scope_decisions.update(scope_decision_ids)
    require(
        covered_scope_decisions == EXPECTED_SCOPE_DECISIONS,
        "authority records must cover all required scope decisions",
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
    validate_authority_records(contract)


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


def validate_for_output() -> dict[str, Any]:
    validate_required_files()
    payload = validate_catalog()
    validate_runbook(payload)
    return payload


def scope_decision_summary_row(raw_request: Any) -> dict[str, Any]:
    request = require_mapping(raw_request, "each scope decision request must be a mapping")
    minimum_evidence = require_non_empty_list(
        request.get("minimum_evidence"),
        "minimum evidence missing",
    )
    authority_references = require_list(
        request.get("authority_references"),
        "authority references must be a list",
    )
    return {
        "id": require_text(request.get("id"), "scope decision request id missing"),
        "status": request.get("status"),
        "expected_reference": request.get("expected_reference"),
        "minimum_evidence": minimum_evidence,
        "minimum_evidence_count": len(minimum_evidence),
        "downstream_use": request.get("downstream_use"),
        "authority_reference_count": len(authority_references),
        "decision_updates_allowed": request.get("decision_updates_allowed"),
    }


def downstream_unlock_summary_row(raw_item: Any) -> dict[str, Any]:
    item = require_mapping(raw_item, "each downstream unlock must be a mapping")
    return {
        "id": require_text(item.get("id"), "downstream id missing"),
        "target_catalog": item.get("target_catalog"),
        "status": item.get("status"),
        "update_allowed": item.get("update_allowed"),
    }


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    contract = require_mapping(payload.get("authority_record_contract"), "authority record contract missing")
    review = require_mapping(payload.get("scope_authority_review"), "scope authority review missing")
    request_rows = [
        scope_decision_summary_row(raw_request)
        for raw_request in require_non_empty_list(
            payload.get("scope_decision_requests"),
            "scope decision requests missing",
        )
    ]
    downstream_rows = [
        downstream_unlock_summary_row(raw_item)
        for raw_item in require_non_empty_list(payload.get("downstream_unlocks"), "downstream missing")
    ]
    current_records = require_list(
        contract.get("current_authority_records"),
        "authority records must be a list",
    )
    required_scope_decisions = require_non_empty_list(
        payload.get("required_scope_decisions"),
        "scope decisions missing",
    )
    required_authority_record_fields = require_non_empty_list(
        contract.get("required_record_fields"),
        "authority record fields missing",
    )
    allowed_authority_types = require_non_empty_list(
        contract.get("allowed_authority_types"),
        "authority types missing",
    )
    no_overclaim_controls = require_mapping(
        contract.get("no_overclaim_controls"),
        "authority record no-overclaim controls missing",
    )
    return _build_summary(
        "bologna_pilot_scope_authority_summary_v1",
        {
            "gate_status": payload.get("status"),
            "operator_runbook": payload.get("operator_runbook"),
            "validation": payload.get("validation"),
            "authority_state": review.get("authority_state"),
            "evidence_status": review.get("evidence_status"),
            "authority_reference_count": len(
                require_list(review.get("authority_references"), "authority references must be a list")
            ),
            "decision_updates_allowed": review.get("decision_updates_allowed"),
            "required_scope_decisions": required_scope_decisions,
            "required_scope_decision_count": len(required_scope_decisions),
            "scope_decision_requests": request_rows,
            "scope_decision_request_count": len(request_rows),
            "authority_record_contract_state": contract.get("contract_state"),
            "current_authority_record_count": len(current_records),
            "required_authority_record_fields": required_authority_record_fields,
            "required_authority_record_field_count": len(required_authority_record_fields),
            "allowed_authority_types": allowed_authority_types,
            "allowed_authority_type_count": len(allowed_authority_types),
            "coverage_policy": contract.get("coverage_policy"),
            "decision_update_policy": contract.get("decision_update_policy"),
            "no_overclaim_controls": no_overclaim_controls,
            "no_overclaim_control_count": len(no_overclaim_controls),
            "downstream_unlocks": downstream_rows,
            "downstream_unlock_count": len(downstream_rows),
        },
    )


def format_summary(summary: dict[str, Any]) -> str:
    require_non_empty_list(summary.get("scope_decision_requests"), "scope decision requests missing")
    require_non_empty_list(summary.get("downstream_unlocks"), "downstream missing")
    return _format_summary(
        "Bologna pilot scope authority summary: blocked",
        summary,
        (
            ("schema_version", "schema_version"),
            ("gate_status", "gate_status"),
            ("authority_state", "authority_state"),
            ("evidence_status", "evidence_status"),
            ("authority_references", "authority_reference_count"),
            ("decision_updates_allowed", "decision_updates_allowed"),
            ("required_scope_decisions", "required_scope_decision_count"),
            ("scope_decision_requests", "scope_decision_request_count"),
            ("current_authority_records", "current_authority_record_count"),
            (
                "required_authority_record_fields",
                "required_authority_record_field_count",
            ),
            ("allowed_authority_types", "allowed_authority_type_count"),
            ("coverage_policy", "coverage_policy"),
            ("decision_update_policy", "decision_update_policy"),
        ),
        row_groups=(
            (
                "scope_decision_requests",
                "scope_decision_request",
                row_summary(
                    "id",
                    (
                        ("status", "status"),
                        ("minimum_evidence", "minimum_evidence_count"),
                        ("authority_references", "authority_reference_count"),
                        ("decision_updates_allowed", "decision_updates_allowed"),
                    ),
                ),
            ),
            (
                "downstream_unlocks",
                "downstream_unlock",
                row_summary("id", (("status", "status"), ("update_allowed", "update_allowed"))),
            ),
        ),
        fields_after_rows=(("no_overclaim_controls", "no_overclaim_control_count"),),
        footer="Bologna pilot scope authority check: ok",
    )


def main(argv: list[str] | None = None) -> int:
    return run_reporting_cli(
        description="Validate the Bologna pilot-scope authority packet.",
        ok_message="Bologna pilot scope authority check: ok",
        validate=validate_for_output,
        summary_builder=build_summary,
        summary_formatter=format_summary,
        argv=argv,
    )


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    _qualification_sys = sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main(_qualification_sys.argv[1:]))
