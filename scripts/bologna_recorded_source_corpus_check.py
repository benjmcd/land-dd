from __future__ import annotations


from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_recorded_source_corpus.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_recorded_source_corpus.md"
PREFLIGHT_PATH = "config/bologna_preflight.yaml"
INTAKE_PATH = "config/bologna_source_authority_intake.yaml"
RIGHTS_PATH = "config/bologna_source_rights.yaml"

EXPECTED_APPROVALS = {
    "corpus_contract_complete": False,
    "one_aoi_scope_authorized": False,
    "exact_sources_authorized": False,
    "source_rights_review_complete": False,
    "source_registry_promotion_allowed": False,
    "recorded_fixture_capture_allowed": False,
    "source_failure_fixture_capture_allowed": False,
    "runtime_use_allowed": False,
    "report_use_allowed": False,
    "db_seed_allowed": False,
}
EXPECTED_LIMITS = {
    "validate_only_contract": True,
    "selects_bologna_aoi": False,
    "approves_sources": False,
    "changes_source_rights": False,
    "promotes_source_registry": False,
    "creates_recorded_fixtures": False,
    "creates_source_failure_fixtures": False,
    "runs_live_connectors": False,
    "mutates_database": False,
    "creates_runtime_artifacts": False,
    "changes_source_readiness": False,
    "claims_legal_review": False,
    "claims_hosted_production_ready": False,
    "claims_multi_geography_framework": False,
}
EXPECTED_REQUIRED_DECISIONS = {
    "one_aoi_scope",
    "exact_source_selection",
    "completed_per_source_rights_review",
    "source_contract_fields_complete",
    "source_registry_row_review",
    "recorded_fixture_scope",
    "retrieval_metadata_policy",
    "source_version_policy",
    "attribution_policy",
    "crs_precision_policy",
    "field_allowlist",
    "field_denylist",
    "no_data_policy",
    "source_failure_policy",
    "caveat_policy",
    "report_use_policy",
    "raw_data_export_policy",
    "review_owner",
    "no_overclaim_review",
}
EXPECTED_MANIFEST_FIELDS = {
    "manifest_schema_version",
    "corpus_id",
    "one_aoi_authority_reference",
    "source_authority_references",
    "source_contract_references",
    "source_versions",
    "retrieval_metadata",
    "fixture_file_manifest",
    "source_failure_fixture_manifest",
    "attribution_text",
    "crs_and_precision",
    "field_allowlist",
    "field_denylist",
    "no_data_policy",
    "caveat_policy",
    "report_use_policy",
    "review_owner",
    "no_overclaim_review",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    PREFLIGHT_PATH,
    INTAKE_PATH,
    RIGHTS_PATH,
    "schemas/source_schema.json",
    "schemas/evidence_schema.json",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "scripts/run_bologna_recorded_source_corpus_check.ps1",
    "scripts/run_bologna_recorded_source_corpus_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_recorded_source_corpus_v1",
    "validate-only",
    "does not select a Bologna AOI",
    "source-failure fixture",
    "corpus_state",
    "fixture manifest entry remains disallowed",
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
    require((ROOT / normalized).exists(), f"referenced corpus artifact missing: {normalized}")


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must be a mapping")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_authority_paths(payload: dict[str, Any]) -> None:
    for path_text in require_non_empty_list(payload.get("authority"), "authority paths missing"):
        require(isinstance(path_text, str), "authority paths must be strings")
        require_existing(path_text)


def intake_reviews_by_candidate() -> dict[str, dict[str, Any]]:
    intake = load_yaml(INTAKE_PATH)
    reviews: dict[str, dict[str, Any]] = {}
    for raw_review in require_non_empty_list(
        intake.get("candidate_authority_reviews"),
        "intake candidate reviews missing",
    ):
        review = require_mapping(raw_review, "each intake review must be a mapping")
        candidate_id = require_text(review.get("candidate_id"), "intake candidate id missing")
        require(candidate_id not in reviews, f"duplicate intake candidate {candidate_id}")
        require(
            review.get("authority_state") == "missing_authority",
            f"{candidate_id} authority unexpectedly present",
        )
        reviews[candidate_id] = review
    return reviews


def rights_reviews_by_candidate() -> dict[str, dict[str, Any]]:
    rights = load_yaml(RIGHTS_PATH)
    reviews: dict[str, dict[str, Any]] = {}
    for raw_review in require_non_empty_list(
        rights.get("candidate_rights_reviews"),
        "rights candidate reviews missing",
    ):
        review = require_mapping(raw_review, "each rights review must be a mapping")
        candidate_id = require_text(review.get("candidate_id"), "rights candidate id missing")
        require(candidate_id not in reviews, f"duplicate rights candidate {candidate_id}")
        require(
            review.get("decision_state") == "pending_external_review",
            f"{candidate_id} rights unexpectedly reviewed",
        )
        reviews[candidate_id] = review
    return reviews


def intake_cadastral_review() -> dict[str, Any]:
    intake = load_yaml(INTAKE_PATH)
    return require_mapping(
        intake.get("cadastral_authority_review"),
        "cadastral intake review missing",
    )


def rights_cadastral_gap() -> dict[str, Any]:
    rights = load_yaml(RIGHTS_PATH)
    return require_mapping(rights.get("cadastral_gap"), "cadastral rights gap missing")


def rights_promotion_blockers() -> set[str]:
    rights = load_yaml(RIGHTS_PATH)
    return {
        str(item)
        for item in require_non_empty_list(
            rights.get("promotion_blockers"),
            "rights promotion blockers missing",
        )
    }


def validate_candidate_review(
    raw_review: Any,
    intake_reviews: dict[str, dict[str, Any]],
    rights_reviews: dict[str, dict[str, Any]],
) -> str:
    review = require_mapping(raw_review, "each corpus review must be a mapping")
    candidate_id = require_text(review.get("candidate_id"), "corpus candidate id missing")
    require(candidate_id in intake_reviews, f"{candidate_id} missing from authority intake")
    require(candidate_id in rights_reviews, f"{candidate_id} missing from source rights")
    require(
        review.get("corpus_state") == "blocked_no_authority",
        f"{candidate_id} corpus state must remain blocked",
    )
    require(
        review.get("fixture_manifest_entry_allowed") is False,
        f"{candidate_id} fixture manifest unexpectedly allowed",
    )
    require(
        review.get("source_failure_fixture_allowed") is False,
        f"{candidate_id} source-failure fixture unexpectedly allowed",
    )
    evidence = set(
        require_non_empty_list(
            review.get("required_manifest_evidence"),
            f"{candidate_id} manifest evidence missing",
        ),
    )
    intake_evidence = set(
        require_non_empty_list(
            intake_reviews[candidate_id].get("evidence_slots"),
            f"{candidate_id} intake evidence missing",
        ),
    )
    rights_evidence = set(
        require_non_empty_list(
            rights_reviews[candidate_id].get("required_evidence"),
            f"{candidate_id} rights evidence missing",
        ),
    )
    require(evidence == intake_evidence == rights_evidence, f"{candidate_id} evidence drifted")
    return candidate_id


def validate_cadastral_review(payload: dict[str, Any]) -> None:
    review = require_mapping(
        payload.get("cadastral_corpus_review"),
        "cadastral corpus review missing",
    )
    intake = intake_cadastral_review()
    rights = rights_cadastral_gap()
    require(
        review.get("corpus_state") == "blocked_direct_source_review_required",
        "cadastral corpus state changed",
    )
    require(
        review.get("fixture_manifest_entry_allowed") is False,
        "cadastral fixture manifest unexpectedly allowed",
    )
    require(
        review.get("source_failure_fixture_allowed") is False,
        "cadastral source-failure fixture unexpectedly allowed",
    )
    evidence = set(
        require_non_empty_list(
            review.get("required_manifest_evidence"),
            "cadastral manifest evidence missing",
        ),
    )
    require(
        evidence
        == set(require_non_empty_list(intake.get("evidence_slots"), "cadastral intake slots missing"))
        == set(
            require_non_empty_list(
                rights.get("required_evidence"),
                "cadastral rights evidence missing",
            ),
        ),
        "cadastral manifest evidence drifted",
    )


def validate_preflight_references() -> None:
    preflight = load_yaml(PREFLIGHT_PATH)
    for raw_gate in require_non_empty_list(preflight.get("preflight_gates"), "gates missing"):
        gate = require_mapping(raw_gate, "each preflight gate must be a mapping")
        if gate.get("id") == "recorded_source_fixture_corpus":
            evidence = set(require_non_empty_list(gate.get("evidence"), "corpus evidence missing"))
            authority = set(
                require_non_empty_list(
                    gate.get("blocker_authority"),
                    "corpus blocker authority missing",
                ),
            )
            require(CONFIG_PATH in evidence, "preflight must cite corpus contract evidence")
            require(CONFIG_PATH in authority, "preflight must block on corpus contract")
            return
    raise SystemExit("recorded_source_fixture_corpus gate missing")


def validate_catalog() -> None:
    payload = load_yaml(CONFIG_PATH)
    require(payload.get("schema_version") == "bologna_recorded_source_corpus_v1", "schema")
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook mismatch")
    require(payload.get("preflight_catalog") == PREFLIGHT_PATH, "preflight mismatch")
    require(payload.get("source_authority_intake") == INTAKE_PATH, "intake mismatch")
    require(payload.get("source_rights_matrix") == RIGHTS_PATH, "rights mismatch")
    require(payload.get("status") == "blocked_no_authority", "corpus must remain blocked")
    require(
        payload.get("validation") == "scripts/run_bologna_recorded_source_corpus_check.ps1",
        "validation wrapper mismatch",
    )
    require(
        require_mapping(payload.get("approvals"), "approvals missing") == EXPECTED_APPROVALS,
        "approvals changed",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "limits changed",
    )
    require(
        set(require_non_empty_list(payload.get("required_corpus_decisions"), "decisions missing"))
        == EXPECTED_REQUIRED_DECISIONS,
        "required corpus decisions changed",
    )
    require(
        set(require_non_empty_list(payload.get("required_manifest_fields"), "fields missing"))
        == EXPECTED_MANIFEST_FIELDS,
        "required manifest fields changed",
    )
    validate_authority_paths(payload)
    intake_reviews = intake_reviews_by_candidate()
    rights_reviews = rights_reviews_by_candidate()
    corpus_ids = {
        validate_candidate_review(review, intake_reviews, rights_reviews)
        for review in require_non_empty_list(
            payload.get("candidate_corpus_reviews"),
            "candidate corpus reviews missing",
        )
    }
    require(corpus_ids == set(intake_reviews) == set(rights_reviews), "candidate set mismatch")
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
        require(phrase in runbook, f"corpus runbook missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_preflight_references()
    validate_runbook()
    print("Bologna recorded-source corpus check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
