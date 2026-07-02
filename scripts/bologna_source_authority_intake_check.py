from __future__ import annotations


from datetime import date
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_source_authority_intake.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_source_authority_intake.md"
RIGHTS_PATH = "config/bologna_source_rights.yaml"
PREFLIGHT_PATH = "config/bologna_preflight.yaml"

EXPECTED_APPROVALS = {
    "authority_intake_complete": False,
    "authorized_one_aoi_scope": False,
    "exact_source_selection_complete": False,
    "per_source_rights_review_complete": False,
    "source_registry_promotion_allowed": False,
    "fixture_capture_allowed": False,
    "runtime_use_allowed": False,
    "report_use_allowed": False,
    "rulepack_or_evidence_scope_approved": False,
}
EXPECTED_LIMITS = {
    "validate_only_intake": True,
    "approves_sources": False,
    "selects_bologna_aoi": False,
    "changes_source_rights": False,
    "promotes_source_registry": False,
    "creates_recorded_fixtures": False,
    "runs_live_connectors": False,
    "mutates_database": False,
    "creates_runtime_artifacts": False,
    "changes_source_readiness": False,
    "claims_legal_review": False,
    "claims_hosted_production_ready": False,
    "claims_multi_geography_framework": False,
}
EXPECTED_REQUIRED_DECISIONS = {
    "product_authorizes_bologna_pilot",
    "one_aoi_scope",
    "exact_candidate_source_selection",
    "per_source_terms_reference",
    "per_source_terms_effective_date",
    "per_source_version_or_publication_date",
    "per_source_cache_export_ai_raw_data_decisions",
    "per_source_attribution_text",
    "per_source_retrieval_metadata_policy",
    "per_source_source_failure_policy",
    "per_source_caveat_policy",
    "per_source_crs_precision_policy",
    "per_source_field_allowlist",
    "per_source_field_denylist",
    "fixture_capture_policy",
    "report_use_policy",
    "rulepack_or_evidence_only_scope",
    "no_overclaim_review",
    "review_owner",
}
EXPECTED_SOURCE_AUTHORITY_RECORD_FIELDS = {
    "source_authority_record_id",
    "authority_type",
    "candidate_id",
    "scope_authority_record_ids",
    "authority_reference",
    "decision_owner",
    "decision_date",
    "effective_date",
    "rights_decision_ids",
    "evidence_slot_values",
    "source_terms_summary",
    "source_version_or_publication_date",
    "retrieval_metadata_policy",
    "cache_export_ai_raw_data_decisions",
    "crs_precision_policy",
    "attribution_text",
    "caveats",
    "storage_export_boundaries",
    "source_failure_policy",
    "downstream_unlocks_requested",
    "supersedes_source_authority_record_ids",
}
EXPECTED_AUTHORITY_TYPES = {
    "candidate_source_terms_review",
    "cadastral_source_terms_review",
}
EXPECTED_CACHE_EXPORT_AI_RAW_DATA_DECISIONS = {
    "cache_allowed",
    "export_allowed",
    "raw_data_allowed",
    "ai_use_allowed",
}
EXPECTED_STORAGE_EXPORT_BOUNDARIES = {
    "cache_boundary",
    "export_boundary",
    "raw_data_boundary",
    "report_boundary",
}
EXPECTED_NO_OVERCLAIM_CONTROLS = {
    "no_source_approval_by_source_authority_record",
    "no_source_rights_change_by_source_authority_record",
    "no_source_registry_promotion_by_source_authority_record",
    "no_fixture_capture_by_source_authority_record",
    "no_runtime_report_use_by_source_authority_record",
    "no_db_seed_by_source_authority_record",
    "no_legal_buildability_title_or_value_claim",
    "no_level_10_or_hosted_claim",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    RIGHTS_PATH,
    PREFLIGHT_PATH,
    "plans/2026-06-20-post-bsr-roadmap.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "scripts/run_bologna_source_authority_intake_check.ps1",
    "scripts/run_bologna_source_authority_intake_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_source_authority_intake_v1",
    "validate-only",
    "does not approve sources",
    "source-rights matrix",
    "source_authority_record_contract",
    "ready_for_external_source_authority_evidence",
    "authority_state",
    "decision_updates_allowed",
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


def require_iso_date(value: Any, message: str) -> str:
    text = require_text(value, message)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise SystemExit(message) from exc
    return text


def normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def require_existing(path_text: str) -> None:
    normalized = normalize_path(path_text)
    require(
        (ROOT / normalized).exists(),
        f"referenced authority-intake artifact missing: {normalized}",
    )


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must be a mapping")


def list_set(value: Any, message: str) -> set[str]:
    return {str(item) for item in require_non_empty_list(value, message)}


def require_text_list(value: Any, message: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, message)
    if not allow_empty and not items:
        raise SystemExit(message)
    return [require_text(item, message) for item in items]


def require_text_mapping_keys(value: Any, expected_keys: set[str], message: str) -> dict[str, Any]:
    mapping = require_mapping(value, message)
    require(set(mapping) == expected_keys, message)
    for raw_value in mapping.values():
        require_text(raw_value, message)
    return mapping


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def rights_reviews_by_candidate() -> dict[str, dict[str, Any]]:
    rights = load_yaml(RIGHTS_PATH)
    reviews: dict[str, dict[str, Any]] = {}
    for raw_review in require_non_empty_list(
        rights.get("candidate_rights_reviews"),
        "source-rights candidate reviews missing",
    ):
        review = require_mapping(raw_review, "each source-rights review must be a mapping")
        candidate_id = require_text(
            review.get("candidate_id"),
            "source-rights candidate id missing",
        )
        require(candidate_id not in reviews, f"duplicate source-rights candidate {candidate_id}")
        require(
            review.get("decision_state") == "pending_external_review",
            f"{candidate_id} source-rights state changed",
        )
        reviews[candidate_id] = review
    return reviews


def rights_cadastral_gap() -> dict[str, Any]:
    rights = load_yaml(RIGHTS_PATH)
    gap = require_mapping(rights.get("cadastral_gap"), "source-rights cadastral gap missing")
    require(
        gap.get("status") == "direct_source_review_required",
        "cadastral gap state changed",
    )
    return gap


def rights_required_decisions() -> set[str]:
    rights = load_yaml(RIGHTS_PATH)
    return list_set(
        rights.get("required_rights_decisions"),
        "source-rights required decisions missing",
    )


def rights_promotion_blockers() -> set[str]:
    rights = load_yaml(RIGHTS_PATH)
    return {
        str(item)
        for item in require_non_empty_list(
            rights.get("promotion_blockers"),
            "blockers missing",
        )
    }


def validate_authority_paths(payload: dict[str, Any]) -> None:
    for path_text in require_non_empty_list(payload.get("authority"), "authority paths missing"):
        require(isinstance(path_text, str), "authority paths must be strings")
        require_existing(path_text)


def validate_candidate_review(
    raw_review: Any,
    source_rights_reviews: dict[str, dict[str, Any]],
) -> str:
    review = require_mapping(raw_review, "each authority review must be a mapping")
    candidate_id = require_text(review.get("candidate_id"), "authority review candidate id missing")
    require(
        candidate_id in source_rights_reviews,
        f"{candidate_id} missing from source-rights matrix",
    )
    rights_review = source_rights_reviews[candidate_id]
    require(
        review.get("authority_state") == "missing_authority",
        f"{candidate_id} authority state must remain missing",
    )
    require(
        review.get("rights_matrix_state") == "pending_external_review",
        f"{candidate_id} rights matrix state mismatch",
    )
    require(
        review.get("evidence_status") == "missing",
        f"{candidate_id} evidence status must remain missing",
    )
    require(
        set(require_non_empty_list(review.get("evidence_slots"), f"{candidate_id} slots missing"))
        == set(
            require_non_empty_list(
                rights_review.get("required_evidence"),
                f"{candidate_id} rights evidence missing",
            ),
        ),
        f"{candidate_id} evidence slots drifted from source-rights matrix",
    )
    require(
        review.get("authority_references") == [],
        f"{candidate_id} authority references changed",
    )
    require(
        review.get("decision_updates_allowed") is False,
        f"{candidate_id} decision updates unexpectedly allowed",
    )
    return candidate_id


def validate_cadastral_review(payload: dict[str, Any]) -> None:
    review = require_mapping(
        payload.get("cadastral_authority_review"),
        "cadastral authority review missing",
    )
    gap = rights_cadastral_gap()
    require(
        review.get("authority_state") == "missing_authority",
        "cadastral authority state must remain missing",
    )
    require(
        review.get("rights_matrix_state") == "direct_source_review_required",
        "cadastral rights matrix state mismatch",
    )
    require(
        review.get("evidence_status") == "missing",
        "cadastral evidence status must remain missing",
    )
    require(
        set(require_non_empty_list(review.get("evidence_slots"), "cadastral slots missing"))
        == set(
            require_non_empty_list(
                gap.get("required_evidence"),
                "cadastral rights evidence missing",
            ),
        ),
        "cadastral evidence slots drifted from source-rights matrix",
    )
    require(review.get("authority_references") == [], "cadastral authority references changed")
    require(
        review.get("decision_updates_allowed") is False,
        "cadastral decision updates unexpectedly allowed",
    )


def required_evidence_slots_for_record(
    record_id: str,
    authority_type: str,
    candidate_id: str,
    source_rights_reviews: dict[str, dict[str, Any]],
) -> set[str]:
    if authority_type == "candidate_source_terms_review":
        require(
            candidate_id in source_rights_reviews,
            f"{record_id} candidate missing from source-rights matrix",
        )
        return list_set(
            source_rights_reviews[candidate_id].get("required_evidence"),
            f"{record_id} required evidence missing",
        )
    require(
        candidate_id == "cadastral_gap",
        f"{record_id} cadastral record must target cadastral_gap",
    )
    return list_set(
        rights_cadastral_gap().get("required_evidence"),
        f"{record_id} cadastral required evidence missing",
    )


def validate_source_authority_record(
    record: dict[str, Any],
    source_rights_reviews: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    require(
        set(record) == EXPECTED_SOURCE_AUTHORITY_RECORD_FIELDS,
        "source authority record fields drifted",
    )
    record_id = require_text(
        record.get("source_authority_record_id"),
        "source authority record id missing",
    )
    authority_type = require_text(record.get("authority_type"), f"{record_id} type missing")
    require(authority_type in EXPECTED_AUTHORITY_TYPES, f"{record_id} type is not allowed")
    candidate_id = require_text(record.get("candidate_id"), f"{record_id} candidate id missing")
    require_text_list(
        record.get("scope_authority_record_ids"),
        f"{record_id} scope authority links missing",
    )
    require_text(record.get("authority_reference"), f"{record_id} authority reference missing")
    require_text(record.get("decision_owner"), f"{record_id} decision owner missing")
    require_iso_date(record.get("decision_date"), f"{record_id} decision date must be ISO")
    require_iso_date(record.get("effective_date"), f"{record_id} effective date must be ISO")
    require(
        list_set(record.get("rights_decision_ids"), f"{record_id} rights decisions missing")
        == rights_required_decisions(),
        f"{record_id} rights decision coverage drifted",
    )
    required_slots = required_evidence_slots_for_record(
        record_id,
        authority_type,
        candidate_id,
        source_rights_reviews,
    )
    slot_values = require_mapping(
        record.get("evidence_slot_values"),
        f"{record_id} evidence slot values missing",
    )
    require(set(slot_values) == required_slots, f"{record_id} evidence slot values drifted")
    for slot_value in slot_values.values():
        require_text(slot_value, f"{record_id} evidence slot value missing")
    require_text(record.get("source_terms_summary"), f"{record_id} source terms missing")
    require_text(
        record.get("source_version_or_publication_date"),
        f"{record_id} source version or publication date missing",
    )
    require_text(
        record.get("retrieval_metadata_policy"),
        f"{record_id} retrieval metadata policy missing",
    )
    require_text_mapping_keys(
        record.get("cache_export_ai_raw_data_decisions"),
        EXPECTED_CACHE_EXPORT_AI_RAW_DATA_DECISIONS,
        f"{record_id} cache/export/AI/raw-data decisions drifted",
    )
    require_text(record.get("crs_precision_policy"), f"{record_id} CRS policy missing")
    require_text(record.get("attribution_text"), f"{record_id} attribution missing")
    require_text_list(record.get("caveats"), f"{record_id} caveats missing")
    require_text_mapping_keys(
        record.get("storage_export_boundaries"),
        EXPECTED_STORAGE_EXPORT_BOUNDARIES,
        f"{record_id} storage/export boundaries drifted",
    )
    require_text(record.get("source_failure_policy"), f"{record_id} failure policy missing")
    require(
        require_list(
            record.get("downstream_unlocks_requested"),
            f"{record_id} downstream unlock requests missing",
        )
        == [],
        f"{record_id} must not request downstream unlocks",
    )
    require_text_list(
        record.get("supersedes_source_authority_record_ids"),
        f"{record_id} superseded source authority record ids must be text",
        allow_empty=True,
    )
    return record_id, candidate_id


def validate_source_authority_records(contract: dict[str, Any]) -> None:
    records = require_list(
        contract.get("current_source_authority_records"),
        "source authority records must be a list",
    )
    if not records:
        return

    source_rights_reviews = rights_reviews_by_candidate()
    record_ids: set[str] = set()
    record_targets: set[str] = set()
    for raw_record in records:
        record = require_mapping(raw_record, "each source authority record must be a mapping")
        record_id, candidate_id = validate_source_authority_record(record, source_rights_reviews)
        require(record_id not in record_ids, f"duplicate source authority record id: {record_id}")
        record_ids.add(record_id)
        record_targets.add(candidate_id)
    require(
        len(record_targets) == len(records),
        "source authority record candidate targets must be unique",
    )


def validate_source_authority_record_contract(payload: dict[str, Any]) -> None:
    contract = require_mapping(
        payload.get("source_authority_record_contract"),
        "source authority record contract missing",
    )
    require(
        contract.get("contract_state") == "ready_for_external_source_authority_evidence",
        "source authority record contract state changed",
    )
    require(
        list_set(
            contract.get("required_record_fields"),
            "source authority record fields missing",
        )
        == EXPECTED_SOURCE_AUTHORITY_RECORD_FIELDS,
        "source authority record fields drifted",
    )
    require(
        list_set(contract.get("allowed_authority_types"), "source authority types missing")
        == EXPECTED_AUTHORITY_TYPES,
        "source authority types drifted",
    )
    require(
        list_set(
            contract.get("required_rights_decision_coverage"),
            "source authority rights coverage missing",
        )
        == rights_required_decisions(),
        "source authority rights decision coverage drifted",
    )
    require(
        contract.get("coverage_policy") == "per_record_all_required_rights_decisions",
        "source authority coverage policy changed",
    )
    require(
        contract.get("evidence_slot_policy") == "per_candidate_required_evidence",
        "source authority evidence-slot policy changed",
    )
    require(
        contract.get("decision_update_policy")
        == "disabled_until_complete_cited_source_authority",
        "source authority decision update policy changed",
    )
    controls = require_mapping(
        contract.get("no_overclaim_controls"),
        "source authority no-overclaim controls missing",
    )
    require(
        set(controls) == EXPECTED_NO_OVERCLAIM_CONTROLS,
        "source authority no-overclaim controls drifted",
    )
    for control_id, enabled in controls.items():
        require(enabled is True, f"{control_id} no-overclaim control disabled")
    validate_source_authority_records(contract)


def validate_preflight_references() -> None:
    preflight = load_yaml(PREFLIGHT_PATH)
    gates = require_non_empty_list(preflight.get("preflight_gates"), "preflight gates missing")
    for raw_gate in gates:
        gate = require_mapping(raw_gate, "each preflight gate must be a mapping")
        if gate.get("id") == "italy_source_rights_review":
            evidence = set(
                require_non_empty_list(
                    gate.get("evidence"),
                    "source-rights evidence missing",
                ),
            )
            authority = set(
                require_non_empty_list(
                    gate.get("blocker_authority"),
                    "source-rights blocker authority missing",
                ),
            )
            require(CONFIG_PATH in evidence, "preflight must cite source-authority intake evidence")
            require(CONFIG_PATH in authority, "preflight must block on source-authority intake")
            return
    raise SystemExit("italy_source_rights_review gate missing")


def validate_catalog() -> None:
    payload = load_yaml(CONFIG_PATH)
    require(
        payload.get("schema_version") == "bologna_source_authority_intake_v1",
        "unexpected schema",
    )
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook mismatch")
    require(payload.get("source_rights_matrix") == RIGHTS_PATH, "source-rights matrix mismatch")
    require(payload.get("preflight_catalog") == PREFLIGHT_PATH, "preflight catalog mismatch")
    require(payload.get("status") == "blocked_no_authority", "authority intake must remain blocked")
    require(
        payload.get("validation") == "scripts/run_bologna_source_authority_intake_check.ps1",
        "validation wrapper mismatch",
    )
    require(
        require_mapping(payload.get("approvals"), "approvals missing") == EXPECTED_APPROVALS,
        "authority approvals changed",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "authority limits changed",
    )
    require(
        {
            str(item)
            for item in require_non_empty_list(
                payload.get("required_authority_decisions"),
                "authority decisions missing",
            )
        }
        == EXPECTED_REQUIRED_DECISIONS,
        "required authority decisions changed",
    )
    validate_authority_paths(payload)
    source_rights_reviews = rights_reviews_by_candidate()
    intake_reviews = require_non_empty_list(
        payload.get("candidate_authority_reviews"),
        "candidate authority reviews missing",
    )
    intake_ids = {
        validate_candidate_review(review, source_rights_reviews) for review in intake_reviews
    }
    require(intake_ids == set(source_rights_reviews), "authority review candidate set mismatch")
    validate_cadastral_review(payload)
    validate_source_authority_record_contract(payload)
    require(
        {
            str(item)
            for item in require_non_empty_list(
                payload.get("promotion_blockers"),
                "promotion blockers missing",
            )
        }
        == rights_promotion_blockers(),
        "promotion blockers drifted from source-rights matrix",
    )
    require_non_empty_list(payload.get("unlock_conditions"), "unlock conditions missing")


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"authority-intake runbook missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_preflight_references()
    validate_runbook()
    print("Bologna source authority intake check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
