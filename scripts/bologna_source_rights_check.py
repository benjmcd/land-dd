from __future__ import annotations


from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_source_rights.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_source_rights.md"
SOURCE_REVIEW_PATH = "docs/source-reviews/bologna-source-rights.md"
CANDIDATE_PATH = "config/bologna_source_candidates.yaml"
SOURCE_SCHEMA_PATH = "schemas/source_schema.json"

EXPECTED_APPROVALS = {
    "source_rights_review_complete": False,
    "any_source_approved": False,
    "source_registry_promoted": False,
    "recorded_source_corpus_allowed": False,
    "runtime_use_allowed": False,
    "report_use_allowed": False,
    "raw_data_export_allowed": False,
    "cadastral_use_approved": False,
}
EXPECTED_LIMITS = {
    "validate_only_matrix": True,
    "approves_sources": False,
    "changes_source_readiness": False,
    "promotes_source_registry": False,
    "creates_recorded_fixtures": False,
    "runs_live_connectors": False,
    "mutates_database": False,
    "creates_runtime_artifacts": False,
    "claims_legal_review": False,
    "claims_cadastral_authority": False,
    "claims_report_use_allowed": False,
    "claims_hosted_production_ready": False,
}
EXPECTED_RIGHTS_DECISIONS = {
    "terms_reference",
    "terms_effective_date",
    "source_version_or_publication_date",
    "update_cadence",
    "license_status",
    "commercial_use_status",
    "redistribution_status",
    "cache_allowed",
    "export_allowed",
    "raw_data_allowed",
    "ai_use_allowed",
    "attribution_required",
    "retrieval_metadata_policy",
    "source_failure_policy",
    "no_data_policy",
    "caveat_policy",
    "crs_precision_policy",
    "field_allowlist",
    "field_denylist",
    "fixture_capture_policy",
    "report_use_policy",
}
EXPECTED_PROMOTION = {
    "source_registry_row_allowed": False,
    "fixture_capture_allowed": False,
    "runtime_use_allowed": False,
    "report_use_allowed": False,
    "raw_export_allowed": False,
}
EXPECTED_BLOCKERS = {
    "authorized_one_aoi_scope",
    "exact_source_selection",
    "completed_per_source_rights_review",
    "source_contract_fields_complete",
    "source_registry_row_review",
    "recorded_fixture_scope",
    "crs_precision_policy",
    "rulepack_or_evidence_only_scope",
    "no_overclaim_review",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    SOURCE_REVIEW_PATH,
    CANDIDATE_PATH,
    SOURCE_SCHEMA_PATH,
    "config/bologna_preflight.yaml",
    "docs/DATA_SOURCE_STRATEGY.md",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "scripts/run_bologna_source_rights_check.ps1",
    "scripts/run_bologna_source_rights_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_source_rights_v1",
    "validate-only",
    "does not approve sources",
    "source registry rows",
    "schemas/source_schema.json",
    "Cadastral cartography remains a direct official-source review gap",
)
SOURCE_REVIEW_PHRASES = (
    "source-rights matrix only",
    "Source approval allowed: no",
    "Source registry promotion allowed: no",
    "Fixture corpus allowed: no",
    "Runtime/report use allowed: no",
    "Not approved",
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


def normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def require_existing(path_text: str) -> None:
    normalized = normalize_path(path_text)
    require(
        (ROOT / normalized).exists(),
        f"referenced source-rights artifact missing: {normalized}",
    )


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must be a mapping")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def source_schema_required_fields() -> set[str]:
    schema = load_yaml(SOURCE_SCHEMA_PATH)
    return {
        str(item)
        for item in require_non_empty_list(
            schema.get("required"),
            "source schema required fields missing",
        )
    }


def candidate_ids() -> set[str]:
    payload = load_yaml(CANDIDATE_PATH)
    candidates = require_non_empty_list(
        payload.get("candidate_sources"),
        "candidate sources missing",
    )
    ids: set[str] = set()
    for raw_candidate in candidates:
        candidate = require_mapping(raw_candidate, "each candidate must be a mapping")
        candidate_id = str(candidate.get("candidate_id", "")).strip()
        require(candidate_id != "", "candidate id missing")
        ids.add(candidate_id)
        require(candidate.get("approval_status") == "not_approved", f"{candidate_id} approved")
        require(candidate.get("allowed_for_runtime") is False, f"{candidate_id} runtime allowed")
        require(
            candidate.get("allowed_for_fixture_corpus") is False,
            f"{candidate_id} fixture allowed",
        )
    return ids


def validate_authority(payload: dict[str, Any]) -> None:
    for authority in require_non_empty_list(payload.get("authority"), "authority paths missing"):
        require(isinstance(authority, str), "authority paths must be strings")
        require_existing(authority)


def validate_rights_review(raw_review: Any) -> str:
    review = require_mapping(raw_review, "each rights review must be a mapping")
    candidate_id = str(review.get("candidate_id", "")).strip()
    require(candidate_id != "", "rights review candidate_id missing")
    require(
        review.get("decision_state") == "pending_external_review",
        f"{candidate_id} decision state must remain pending",
    )
    rights = require_mapping(review.get("rights_decisions"), f"{candidate_id} rights missing")
    require(set(rights) == EXPECTED_RIGHTS_DECISIONS, f"{candidate_id} rights set mismatch")
    for key, value in rights.items():
        require(value == "pending_review", f"{candidate_id} {key} must remain pending_review")
    promotion = require_mapping(review.get("promotion"), f"{candidate_id} promotion missing")
    require(promotion == EXPECTED_PROMOTION, f"{candidate_id} promotion changed")
    require_non_empty_list(review.get("required_evidence"), f"{candidate_id} evidence missing")
    return candidate_id


def validate_cadastral_gap(payload: dict[str, Any]) -> None:
    gap = require_mapping(payload.get("cadastral_gap"), "cadastral gap missing")
    require(
        gap.get("status") == "direct_source_review_required",
        "cadastral gap status must remain direct_source_review_required",
    )
    approval = require_mapping(gap.get("approval"), "cadastral approval missing")
    require(all(value is False for value in approval.values()), "cadastral approval changed")
    require_non_empty_list(gap.get("required_evidence"), "cadastral required evidence missing")


def validate_catalog() -> None:
    payload = load_yaml(CONFIG_PATH)
    require(payload.get("schema_version") == "bologna_source_rights_v1", "unexpected schema")
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook mismatch")
    require(payload.get("source_review") == SOURCE_REVIEW_PATH, "source review mismatch")
    require(payload.get("candidate_catalog") == CANDIDATE_PATH, "candidate catalog mismatch")
    require(payload.get("status") == "repo_local_validate_only", "status must remain validate-only")
    require(
        payload.get("validation") == "scripts/run_bologna_source_rights_check.ps1",
        "validation wrapper mismatch",
    )
    approvals = require_mapping(payload.get("approvals"), "approvals missing")
    require(approvals == EXPECTED_APPROVALS, "approvals changed")
    limits = require_mapping(payload.get("limits"), "limits missing")
    require(limits == EXPECTED_LIMITS, "limits changed")
    require(
        set(
            require_non_empty_list(
                payload.get("source_contract_required_fields"),
                "source fields missing",
            ),
        )
        == source_schema_required_fields(),
        "source contract fields do not match source schema",
    )
    require(
        set(
            require_non_empty_list(
                payload.get("required_rights_decisions"),
                "rights fields missing",
            ),
        )
        == EXPECTED_RIGHTS_DECISIONS,
        "required rights decision set mismatch",
    )
    validate_authority(payload)
    reviews = require_non_empty_list(
        payload.get("candidate_rights_reviews"),
        "rights reviews missing",
    )
    reviewed_ids = {validate_rights_review(review) for review in reviews}
    require(
        reviewed_ids == candidate_ids(),
        f"rights review candidate mismatch: {sorted(reviewed_ids)}",
    )
    validate_cadastral_gap(payload)
    blockers = set(
        require_non_empty_list(payload.get("promotion_blockers"), "promotion blockers missing"),
    )
    require(blockers == EXPECTED_BLOCKERS, f"promotion blocker set mismatch: {sorted(blockers)}")


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"Bologna source-rights runbook missing phrase: {phrase}")


def validate_source_review() -> None:
    review = read_text(SOURCE_REVIEW_PATH)
    for phrase in SOURCE_REVIEW_PHRASES:
        require(phrase in review, f"Bologna source-rights review missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_runbook()
    validate_source_review()
    print("Bologna source rights check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
