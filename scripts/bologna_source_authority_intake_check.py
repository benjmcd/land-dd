from __future__ import annotations

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
        f"referenced authority-intake artifact missing: {normalized}",
    )


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must be a mapping")


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
    raise SystemExit(main())
