from __future__ import annotations


import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/bologna_preflight.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_preflight.md"
EXPECTED_LIMITS = {
    "validate_only_catalog": True,
    "selects_bologna": False,
    "approves_italy_sources": False,
    "approves_eu_italy_rulepack": False,
    "runs_live_connectors": False,
    "creates_runtime_artifacts": False,
    "mutates_database": False,
    "changes_source_readiness": False,
    "unblocks_ds017": False,
    "claims_legal_review": False,
    "claims_hosted_production_ready": False,
    "claims_multi_geography_framework": False,
}
EXPECTED_APPROVALS = {
    "bologna_selected": False,
    "italy_sources_approved": False,
    "eu_italy_rulepack_approved": False,
    "recorded_source_corpus_committed": False,
    "ds017_resolved_or_deferred": False,
    "hosted_production_ready": False,
    "multi_geography_framework_approved": False,
}
ALLOWED_STATUSES = {
    "repo_confirmed",
    "missing_candidate_decision",
    "missing_repo_evidence",
    "blocked_external_authority",
}
EXPECTED_GATE_STATUSES = {
    "lower_layer_runtime_boundary": "repo_confirmed",
    "pilot_candidate_authority": "missing_candidate_decision",
    "jurisdiction_model_authority": "blocked_external_authority",
    "italy_source_inventory": "missing_candidate_decision",
    "italy_source_rights_review": "blocked_external_authority",
    "ds017_treatment": "blocked_external_authority",
    "eu_italy_rulepack_scope": "missing_candidate_decision",
    "recorded_source_fixture_corpus": "missing_repo_evidence",
    "bologna_report_runtime_proof": "missing_repo_evidence",
    "hosted_identity_artifact_boundary": "blocked_external_authority",
    "multi_geography_framework_boundary": "missing_repo_evidence",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    "config/bologna_source_candidates.yaml",
    "config/bologna_pilot_scope_authority.yaml",
    "config/bologna_source_rights.yaml",
    "config/bologna_source_authority_intake.yaml",
    "config/bologna_recorded_source_corpus.yaml",
    "docs/source-reviews/bologna-source-candidates.md",
    "docs/source-reviews/bologna-source-rights.md",
    "docs/runbooks/bologna_recorded_source_corpus.md",
    "scripts/bologna_source_candidates_check.py",
    "scripts/bologna_pilot_scope_authority_check.py",
    "scripts/bologna_source_rights_check.py",
    "scripts/bologna_source_authority_intake_check.py",
    "scripts/bologna_recorded_source_corpus_check.py",
    "scripts/run_bologna_source_candidates_check.ps1",
    "scripts/run_bologna_source_candidates_check.sh",
    "scripts/run_bologna_pilot_scope_authority_check.ps1",
    "scripts/run_bologna_pilot_scope_authority_check.sh",
    "scripts/run_bologna_source_rights_check.ps1",
    "scripts/run_bologna_source_rights_check.sh",
    "scripts/run_bologna_source_authority_intake_check.ps1",
    "scripts/run_bologna_source_authority_intake_check.sh",
    "scripts/run_bologna_recorded_source_corpus_check.ps1",
    "scripts/run_bologna_recorded_source_corpus_check.sh",
    "scripts/run_bologna_preflight_check.ps1",
    "scripts/run_bologna_preflight_check.sh",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "docs/checklists/jurisdiction_readiness.md",
    "docs/checklists/rulepack_readiness.md",
    "config/source_entitlements.yaml",
)
RUNBOOK_PHRASES = (
    "bologna_preflight_v1",
    "validate-only",
    "bologna_pilot_scope_authority_v1",
    "bologna_source_candidates_v1",
    "bologna_source_rights_v1",
    "bologna_source_authority_intake_v1",
    "bologna_recorded_source_corpus_v1",
    "not_started_external_authority_required",
    "does not select Bologna",
    "does not approve Italy sources",
    "does not approve an EU/Italy rulepack",
    "does not unblock DS-017",
    "does not claim hosted production readiness",
    "The current US jurisdiction and rulepack checklists are useful patterns",
)
PRODUCTION_PACKET_PHRASES = (
    "Bologna Recorded-Source Pilot Authority",
    "does not approve or start Bologna",
    "Do not reuse the US homestead rulepack",
    "Do not generalize into a multi-geography framework",
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


def path_exists(path_text: str) -> bool:
    normalized = normalize_path(path_text)
    return any((ROOT / normalized).exists() for normalized in (normalized, normalized.rstrip("/")))


def require_existing(path_text: str) -> None:
    normalized = normalize_path(path_text)
    require(path_exists(normalized), f"referenced Bologna preflight artifact missing: {normalized}")


def read_text(path_text: str) -> str:
    normalized = normalize_path(path_text)
    return (ROOT / normalized).read_text(encoding="utf-8")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_evidence_assertions(raw_assertions: Any, gate_id: str) -> None:
    assertions = require_non_empty_list(raw_assertions, f"{gate_id} evidence assertions missing")
    for raw_assertion in assertions:
        assertion = require_mapping(raw_assertion, f"{gate_id} assertion must be a mapping")
        path_text = require_text(assertion.get("path"), f"{gate_id} assertion path missing")
        require_existing(path_text)
        text = read_text(path_text)
        contains = assertion.get("contains")
        regex = assertion.get("regex")
        require(
            isinstance(contains, str) ^ isinstance(regex, str),
            f"{gate_id} assertion must provide exactly one of contains or regex",
        )
        if isinstance(contains, str):
            require(contains in text, f"{gate_id} assertion missing text: {contains}")
        if isinstance(regex, str):
            require(
                re.search(regex, text, flags=re.MULTILINE) is not None,
                f"{gate_id} assertion regex did not match: {regex}",
            )


def validate_candidate(payload: dict[str, Any]) -> None:
    candidate = require_mapping(payload.get("candidate"), "candidate missing")
    require(candidate.get("id") == "bologna_recorded_source_pilot", "candidate id mismatch")
    require(
        candidate.get("status") == "not_started_external_authority_required",
        "Bologna candidate must remain not started",
    )
    for authority in require_non_empty_list(candidate.get("authority"), "authority paths missing"):
        require(isinstance(authority, str), "authority paths must be strings")
        require_existing(authority)
    require(
        require_mapping(candidate.get("approvals"), "approvals missing") == EXPECTED_APPROVALS,
        "Bologna approval flags changed without validator update",
    )


def validate_gates(payload: dict[str, Any]) -> None:
    gates = require_non_empty_list(payload.get("preflight_gates"), "preflight gates missing")
    seen: set[str] = set()
    for raw_gate in gates:
        gate = require_mapping(raw_gate, "each preflight gate must be a mapping")
        gate_id = require_text(gate.get("id"), "gate id missing")
        require(gate_id not in seen, f"duplicate preflight gate: {gate_id}")
        seen.add(gate_id)
        expected_status = EXPECTED_GATE_STATUSES.get(gate_id)
        require(expected_status is not None, f"unexpected preflight gate: {gate_id}")
        status = require_text(gate.get("status"), f"{gate_id} status missing")
        require(status in ALLOWED_STATUSES, f"{gate_id} unsupported status: {status}")
        require(status == expected_status, f"{gate_id} must remain {expected_status}")
        for evidence_path in require_non_empty_list(
            gate.get("evidence"),
            f"{gate_id} evidence missing",
        ):
            require(isinstance(evidence_path, str), f"{gate_id} evidence must be strings")
            require_existing(evidence_path)
        if status == "repo_confirmed":
            validate_evidence_assertions(gate.get("evidence_assertions"), gate_id)
            require_text(gate.get("interpretation"), f"{gate_id} interpretation missing")
        else:
            require_text(gate.get("next_action"), f"{gate_id} next action missing")
            for authority_path in require_non_empty_list(
                gate.get("blocker_authority"),
                f"{gate_id} blocker authority missing",
            ):
                require(isinstance(authority_path, str), f"{gate_id} authority must be strings")
                require_existing(authority_path)
    require(seen == set(EXPECTED_GATE_STATUSES), f"preflight gate set mismatch: {sorted(seen)}")


def validate_catalog() -> None:
    payload = require_mapping(yaml.safe_load(read_text(CONFIG_PATH)), "catalog must be a mapping")
    require(payload.get("schema_version") == "bologna_preflight_v1", "unexpected schema")
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook mismatch")
    require(payload.get("status") == "repo_local_validate_only", "catalog must be validate-only")
    require(
        payload.get("validation") == "scripts/run_bologna_preflight_check.ps1",
        "validation wrapper mismatch",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "Bologna preflight limits changed without validator update",
    )
    validate_candidate(payload)
    validate_gates(payload)


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"Bologna preflight runbook missing phrase: {phrase}")


def validate_production_packet() -> None:
    packet = read_text("state/PRODUCTION_AUTHORITY_PACKET.md")
    for phrase in PRODUCTION_PACKET_PHRASES:
        require(phrase in packet, f"production authority packet missing phrase: {phrase}")


def validate_source_candidates() -> None:
    payload = require_mapping(
        yaml.safe_load(read_text("config/bologna_source_candidates.yaml")),
        "Bologna source-candidates catalog must be a mapping",
    )
    require(
        payload.get("schema_version") == "bologna_source_candidates_v1",
        "Bologna source-candidates schema mismatch",
    )
    require(
        payload.get("status") == "repo_local_candidate_inventory",
        "Bologna source-candidates catalog must remain candidate inventory",
    )
    approvals = require_mapping(
        payload.get("approvals"),
        "Bologna source-candidates approvals missing",
    )
    require(
        all(value is False for value in approvals.values()),
        "Bologna source-candidates approvals must remain false",
    )
    candidates = require_non_empty_list(
        payload.get("candidate_sources"),
        "Bologna source candidates missing",
    )
    for candidate in candidates:
        candidate = require_mapping(candidate, "each Bologna source candidate must be a mapping")
        candidate_id = require_text(candidate.get("candidate_id"), "candidate id missing")
        require(
            candidate.get("approval_status") == "not_approved",
            f"{candidate_id} source approved",
        )
        require(
            candidate.get("allowed_for_runtime") is False,
            f"{candidate_id} runtime use allowed",
        )
        require(
            candidate.get("allowed_for_fixture_corpus") is False,
            f"{candidate_id} fixture corpus use allowed",
        )


def validate_pilot_scope_authority() -> None:
    payload = require_mapping(
        yaml.safe_load(read_text("config/bologna_pilot_scope_authority.yaml")),
        "Bologna pilot-scope authority catalog must be a mapping",
    )
    require(
        payload.get("schema_version") == "bologna_pilot_scope_authority_v1",
        "Bologna pilot-scope authority schema mismatch",
    )
    require(
        payload.get("status") == "blocked_no_pilot_scope_authority",
        "Bologna pilot-scope authority must remain blocked",
    )
    approvals = require_mapping(
        payload.get("approvals"),
        "Bologna pilot-scope approvals missing",
    )
    require(
        all(value is False for value in approvals.values()),
        "Bologna pilot-scope approvals must remain false",
    )
    review = require_mapping(
        payload.get("scope_authority_review"),
        "Bologna pilot-scope review missing",
    )
    require(
        review.get("authority_state") == "missing_authority",
        "Bologna pilot-scope authority state promoted",
    )
    require(
        review.get("authority_references") == [],
        "Bologna pilot-scope authority references must remain empty",
    )
    require(
        review.get("decision_updates_allowed") is False,
        "Bologna pilot-scope updates unexpectedly allowed",
    )


def validate_source_rights() -> None:
    payload = require_mapping(
        yaml.safe_load(read_text("config/bologna_source_rights.yaml")),
        "Bologna source-rights catalog must be a mapping",
    )
    require(
        payload.get("schema_version") == "bologna_source_rights_v1",
        "Bologna source-rights schema mismatch",
    )
    require(
        payload.get("status") == "repo_local_validate_only",
        "Bologna source-rights catalog must remain validate-only",
    )
    approvals = require_mapping(payload.get("approvals"), "Bologna source-rights approvals missing")
    require(
        all(value is False for value in approvals.values()),
        "Bologna source-rights approvals must remain false",
    )
    reviews = require_non_empty_list(
        payload.get("candidate_rights_reviews"),
        "Bologna source-rights reviews missing",
    )
    for review in reviews:
        review = require_mapping(review, "each Bologna source-rights review must be a mapping")
        candidate_id = require_text(
            review.get("candidate_id"),
            "source-rights candidate id missing",
        )
        require(
            review.get("decision_state") == "pending_external_review",
            f"{candidate_id} source-rights decision state promoted",
        )
        rights = require_mapping(review.get("rights_decisions"), f"{candidate_id} rights missing")
        require(
            all(value == "pending_review" for value in rights.values()),
            f"{candidate_id} source-rights decisions must remain pending",
        )
        promotion = require_mapping(review.get("promotion"), f"{candidate_id} promotion missing")
        require(
            all(value is False for value in promotion.values()),
            f"{candidate_id} source-rights promotion changed",
        )


def validate_source_authority_intake() -> None:
    payload = require_mapping(
        yaml.safe_load(read_text("config/bologna_source_authority_intake.yaml")),
        "Bologna source-authority intake catalog must be a mapping",
    )
    require(
        payload.get("schema_version") == "bologna_source_authority_intake_v1",
        "Bologna source-authority intake schema mismatch",
    )
    require(
        payload.get("status") == "blocked_no_authority",
        "Bologna source-authority intake must remain blocked",
    )
    approvals = require_mapping(
        payload.get("approvals"),
        "Bologna source-authority approvals missing",
    )
    require(
        all(value is False for value in approvals.values()),
        "Bologna source-authority approvals must remain false",
    )
    reviews = require_non_empty_list(
        payload.get("candidate_authority_reviews"),
        "Bologna source-authority reviews missing",
    )
    for review in reviews:
        review = require_mapping(review, "each source-authority review must be a mapping")
        candidate_id = require_text(
            review.get("candidate_id"),
            "source-authority candidate id missing",
        )
        require(
            review.get("authority_state") == "missing_authority",
            f"{candidate_id} source-authority state promoted",
        )
        require(
            review.get("authority_references") == [],
            f"{candidate_id} source-authority references must remain empty",
        )
        require(
            review.get("decision_updates_allowed") is False,
            f"{candidate_id} source-authority updates unexpectedly allowed",
        )


def validate_recorded_source_corpus() -> None:
    payload = require_mapping(
        yaml.safe_load(read_text("config/bologna_recorded_source_corpus.yaml")),
        "Bologna recorded-source corpus catalog must be a mapping",
    )
    require(
        payload.get("schema_version") == "bologna_recorded_source_corpus_v1",
        "Bologna recorded-source corpus schema mismatch",
    )
    require(
        payload.get("status") == "blocked_no_authority",
        "Bologna recorded-source corpus must remain blocked",
    )
    approvals = require_mapping(
        payload.get("approvals"),
        "Bologna recorded-source corpus approvals missing",
    )
    require(
        all(value is False for value in approvals.values()),
        "Bologna recorded-source corpus approvals must remain false",
    )
    reviews = require_non_empty_list(
        payload.get("candidate_corpus_reviews"),
        "Bologna recorded-source corpus reviews missing",
    )
    for review in reviews:
        review = require_mapping(review, "each corpus review must be a mapping")
        candidate_id = require_text(review.get("candidate_id"), "corpus candidate id missing")
        require(
            review.get("corpus_state") == "blocked_no_authority",
            f"{candidate_id} corpus state promoted",
        )
        require(
            review.get("fixture_manifest_entry_allowed") is False,
            f"{candidate_id} fixture manifest unexpectedly allowed",
        )
        require(
            review.get("source_failure_fixture_allowed") is False,
            f"{candidate_id} source-failure fixture unexpectedly allowed",
        )


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_pilot_scope_authority()
    validate_source_candidates()
    validate_source_rights()
    validate_source_authority_intake()
    validate_recorded_source_corpus()
    validate_runbook()
    validate_production_packet()
    print("Bologna preflight check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
