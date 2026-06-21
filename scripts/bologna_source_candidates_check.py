from __future__ import annotations


from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_source_candidates.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_source_candidates.md"
SOURCE_REVIEW_PATH = "docs/source-reviews/bologna-source-candidates.md"

EXPECTED_APPROVALS = {
    "product_selected_sources": False,
    "source_rights_review_complete": False,
    "source_registry_promoted": False,
    "recorded_source_corpus_committed": False,
    "bologna_aoi_authorized": False,
    "eu_italy_rulepack_approved": False,
    "runtime_use_allowed": False,
}
EXPECTED_LIMITS = {
    "candidate_only": True,
    "approves_sources": False,
    "changes_source_readiness": False,
    "promotes_source_registry": False,
    "runs_live_connectors": False,
    "creates_recorded_fixtures": False,
    "mutates_database": False,
    "creates_runtime_artifacts": False,
    "claims_legal_review": False,
    "claims_report_use_allowed": False,
    "claims_cadastral_authority": False,
    "claims_hosted_production_ready": False,
}
REQUIRED_BEFORE_ANY_USE = {
    "authorized_one_aoi_scope",
    "per_source_license_terms_review",
    "cache_redistribution_export_ai_raw_data_decisions",
    "source_owner_and_version_date",
    "retrieval_metadata_and_attribution_policy",
    "crs_geometry_precision_policy",
    "caveats_and_no_overclaim_language",
    "source_failure_and_no_data_fixture_policy",
    "rulepack_or_evidence_only_scope_decision",
}
REQUIRED_DOMAINS = {
    "municipal_planning",
    "municipal_open_data",
    "regional_topographic",
    "regional_geodata_catalog",
    "coordinate_reference",
    "environmental_context",
}
REQUIRED_GAPS = {
    "authorized_bologna_aoi",
    "per_source_rights_reviews",
    "italian_cadastral_cartography",
    "recorded_fixture_corpus",
    "eu_italy_rulepack_scope",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    SOURCE_REVIEW_PATH,
    "scripts/bologna_source_candidates_check.py",
    "scripts/run_bologna_source_candidates_check.ps1",
    "scripts/run_bologna_source_candidates_check.sh",
    "config/bologna_preflight.yaml",
    "docs/DATA_SOURCE_STRATEGY.md",
    "schemas/source_schema.json",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
)
RUNBOOK_PHRASES = (
    "bologna_source_candidates_v1",
    "candidate-only",
    "does not approve sources",
    "does not fetch official datasets",
    "Italian cadastral cartography remains a direct source-review gap",
    "Do not promote a candidate into `registers/data_source_registry.csv`",
)
SOURCE_REVIEW_PHRASES = (
    "candidate inventory only",
    "Production use allowed: no",
    "Fixture corpus allowed: no",
    "Source registry promotion allowed: no",
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
        f"referenced source-candidate artifact missing: {normalized}",
    )


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_authority(payload: dict[str, Any]) -> None:
    for authority in require_non_empty_list(payload.get("authority"), "authority paths missing"):
        require(isinstance(authority, str), "authority paths must be strings")
        require_existing(authority)


def validate_candidate(candidate: dict[str, Any]) -> str:
    candidate_id = require_text(candidate.get("candidate_id"), "candidate_id missing")
    domain = require_text(candidate.get("domain"), f"{candidate_id} domain missing")
    require(domain in REQUIRED_DOMAINS, f"{candidate_id} unexpected domain: {domain}")
    require_text(candidate.get("source_name"), f"{candidate_id} source_name missing")
    require_text(candidate.get("organization"), f"{candidate_id} organization missing")
    source_url = require_text(candidate.get("source_url"), f"{candidate_id} source_url missing")
    require(source_url.startswith("https://"), f"{candidate_id} source_url must be https")
    evidence_urls = require_non_empty_list(
        candidate.get("evidence_urls"),
        f"{candidate_id} evidence urls missing",
    )
    for evidence_url in evidence_urls:
        require(isinstance(evidence_url, str), f"{candidate_id} evidence urls must be strings")
        require(evidence_url.startswith("https://"), f"{candidate_id} evidence url must be https")
    require_text(candidate.get("authority_level"), f"{candidate_id} authority_level missing")
    require_text(candidate.get("candidate_use"), f"{candidate_id} candidate_use missing")
    require_text(candidate.get("retrieval_model"), f"{candidate_id} retrieval_model missing")
    require_non_empty_list(
        candidate.get("observed_evidence"),
        f"{candidate_id} observed evidence missing",
    )
    require(
        candidate.get("source_version_status") == "pending_review",
        f"{candidate_id} source version promoted",
    )
    require(
        candidate.get("rights_review_status") == "pending_review",
        f"{candidate_id} rights review promoted",
    )
    require(
        candidate.get("approval_status") == "not_approved",
        f"{candidate_id} approval status promoted",
    )
    require(
        candidate.get("source_registry_promoted") is False,
        f"{candidate_id} source registry promoted",
    )
    require(candidate.get("allowed_for_runtime") is False, f"{candidate_id} runtime use allowed")
    require(
        candidate.get("allowed_for_fixture_corpus") is False,
        f"{candidate_id} fixture corpus use allowed",
    )
    require_non_empty_list(
        candidate.get("required_before_use"),
        f"{candidate_id} required_before_use missing",
    )
    require_non_empty_list(candidate.get("caveats"), f"{candidate_id} caveats missing")
    return domain


def validate_known_gaps(payload: dict[str, Any]) -> None:
    gaps = require_non_empty_list(payload.get("known_gaps"), "known gaps missing")
    seen: set[str] = set()
    for raw_gap in gaps:
        gap = require_mapping(raw_gap, "each known gap must be a mapping")
        gap_id = require_text(gap.get("gap_id"), "gap_id missing")
        require(gap_id not in seen, f"duplicate known gap: {gap_id}")
        seen.add(gap_id)
        status = require_text(gap.get("status"), f"{gap_id} status missing")
        require(
            status
            in {
                "missing_external_decision",
                "direct_source_review_required",
                "missing_repo_evidence",
            },
            f"{gap_id} unsupported status: {status}",
        )
        require_text(gap.get("next_action"), f"{gap_id} next_action missing")
        if gap_id == "italian_cadastral_cartography":
            reference = require_mapping(
                gap.get("candidate_reference"),
                "cadastral reference missing",
            )
            urls = require_non_empty_list(reference.get("urls"), "cadastral reference urls missing")
            require(
                all(isinstance(url, str) and url.startswith("https://") for url in urls),
                "cadastral urls invalid",
            )
    require(seen == REQUIRED_GAPS, f"known gap set mismatch: {sorted(seen)}")


def validate_catalog() -> None:
    payload = require_mapping(yaml.safe_load(read_text(CONFIG_PATH)), "catalog must be a mapping")
    require(payload.get("schema_version") == "bologna_source_candidates_v1", "unexpected schema")
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook mismatch")
    require(payload.get("source_review") == SOURCE_REVIEW_PATH, "source review mismatch")
    require(
        payload.get("status") == "repo_local_candidate_inventory",
        "status must remain candidate inventory",
    )
    require(
        payload.get("validation") == "scripts/run_bologna_source_candidates_check.ps1",
        "validation wrapper mismatch",
    )
    approvals = require_mapping(payload.get("approvals"), "approvals missing")
    require(approvals == EXPECTED_APPROVALS, "approvals changed")
    limits = require_mapping(payload.get("limits"), "limits missing")
    require(limits == EXPECTED_LIMITS, "limits changed")
    required_before = set(
        require_non_empty_list(
            payload.get("required_before_any_use"),
            "required use gates missing",
        ),
    )
    require(
        required_before == REQUIRED_BEFORE_ANY_USE,
        f"required use gate mismatch: {sorted(required_before)}",
    )
    validate_authority(payload)

    candidates = require_non_empty_list(
        payload.get("candidate_sources"),
        "candidate sources missing",
    )
    domains = {
        validate_candidate(require_mapping(candidate, "each candidate must be a mapping"))
        for candidate in candidates
    }
    require(domains == REQUIRED_DOMAINS, f"candidate domain set mismatch: {sorted(domains)}")
    validate_known_gaps(payload)


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"Bologna source-candidates runbook missing phrase: {phrase}")


def validate_source_review() -> None:
    review = read_text(SOURCE_REVIEW_PATH)
    for phrase in SOURCE_REVIEW_PHRASES:
        require(phrase in review, f"Bologna source-candidates review missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_runbook()
    validate_source_review()
    print("Bologna source candidates check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
