from __future__ import annotations


import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "config/checklist_dry_run.yaml",
    "docs/runbooks/checklist_dry_run.md",
    "docs/checklists/jurisdiction_readiness.md",
    "docs/checklists/rulepack_readiness.md",
    "scripts/run_checklist_dry_run_check.ps1",
    "scripts/run_checklist_dry_run_check.sh",
    "state/POST_RC_AUTHORITY_SPLIT.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "state/PROJECT_STATE.md",
)
REQUIRED_CHECKLISTS = {
    "jurisdiction_readiness": "docs/checklists/jurisdiction_readiness.md",
    "rulepack_readiness": "docs/checklists/rulepack_readiness.md",
}
ALLOWED_STATUSES = {
    "repo_confirmed",
    "missing_candidate_decision",
    "missing_repo_evidence",
    "blocked_external_authority",
    "not_applicable_existing_scope",
}
REQUIRED_FAIL_CLOSED_STATUSES = {
    "missing_candidate_decision",
    "missing_repo_evidence",
    "blocked_external_authority",
    "not_applicable_existing_scope",
}
EXPECTED_LIMITS = {
    "validate_only_catalog": True,
    "selects_new_geography": False,
    "approves_new_rulepack": False,
    "approves_new_source": False,
    "unblocks_ds017": False,
    "runs_live_connectors": False,
    "creates_runtime_artifacts": False,
    "claims_legal_review": False,
    "claims_hosted_production_ready": False,
}
CHECKBOX_PREFIX_RE = re.compile(r"^(?:[-*+]|\d+[.)]) \[")
CHECKBOX_ITEM_RE = re.compile(r"^(?:[-*+]|\d+[.)]) \[[ xX]\] (?P<item>.+)$")


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


def resolve_repo_path(path_text: str) -> Path:
    normalized = normalize_path(path_text)
    path = Path(normalized)
    require(
        not path.is_absolute(),
        f"referenced checklist dry-run artifact path must be repo-relative: {normalized}",
    )
    root = ROOT.resolve()
    resolved = (root / path).resolve()
    require(
        resolved == root or resolved.is_relative_to(root),
        f"referenced checklist dry-run artifact outside repository root: {normalized}",
    )
    return resolved


def require_existing(path_text: Any) -> None:
    path_value = require_text(
        path_text,
        "referenced checklist dry-run artifact path missing",
    )
    normalized = normalize_path(path_value)
    resolved = resolve_repo_path(normalized)
    require(
        resolved.exists(),
        f"referenced checklist dry-run artifact missing: {normalized}",
    )
    require(
        resolved.is_file(),
        f"referenced checklist dry-run artifact must be a file: {normalized}",
    )


def read_text(path_text: str) -> str:
    return resolve_repo_path(path_text).read_text(encoding="utf-8")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return re.sub(r"_+", "_", slug)


def checklist_item_ids(path_text: str) -> set[str]:
    ids: set[str] = set()
    for line in read_text(path_text).splitlines():
        stripped = line.strip()
        if CHECKBOX_PREFIX_RE.match(stripped) and CHECKBOX_ITEM_RE.match(stripped) is None:
            raise SystemExit(f"unsupported checkbox marker in {path_text}: {stripped}")
        match = CHECKBOX_ITEM_RE.match(stripped)
        if match is None:
            continue
        item = match.group("item").strip()
        item_id = slugify(item)
        require(item_id not in ids, f"duplicate checklist item id in {path_text}: {item_id}")
        ids.add(item_id)
    require(bool(ids), f"no checkbox items found in {path_text}")
    return ids


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_candidate_shape(payload: dict[str, Any]) -> None:
    candidate = require_mapping(payload.get("candidate_shape"), "candidate shape missing")
    require_text(candidate.get("id"), "candidate shape id missing")
    require(
        candidate.get("status") == "hypothetical_not_selected",
        "candidate shape must remain hypothetical_not_selected",
    )
    authorities = require_non_empty_list(
        candidate.get("authority"),
        "candidate authority paths missing",
    )
    for authority in authorities:
        require(isinstance(authority, str), "candidate authority paths must be strings")
        require_existing(authority)

    approvals = require_mapping(candidate.get("approvals"), "candidate approvals missing")
    require(
        approvals
        == {
            "new_geography_selected": False,
            "new_rulepack_approved": False,
            "new_source_approved": False,
            "ds017_unblocked": False,
            "hosted_production_ready": False,
        },
        "candidate approvals changed without validator update",
    )


def validate_evidence_assertions(raw_assertions: Any, item_id: str) -> None:
    assertions = require_non_empty_list(
        raw_assertions,
        f"{item_id} evidence assertions missing",
    )
    for raw_assertion in assertions:
        assertion = require_mapping(
            raw_assertion,
            f"{item_id} evidence assertion must be a mapping",
        )
        path_text = require_text(assertion.get("path"), f"{item_id} assertion path missing")
        require_existing(path_text)
        text = read_text(path_text)
        contains = assertion.get("contains")
        regex = assertion.get("regex")
        require(
            isinstance(contains, str) ^ isinstance(regex, str),
            f"{item_id} assertion must provide exactly one of contains or regex",
        )
        if isinstance(contains, str):
            require(
                bool(contains.strip()),
                f"{item_id} assertion contains must be non-empty",
            )
            require(contains in text, f"{item_id} assertion missing text: {contains}")
        if isinstance(regex, str):
            require(
                bool(regex.strip()),
                f"{item_id} assertion regex must be non-empty",
            )
            require(
                re.search(regex, text, flags=re.MULTILINE) is not None,
                f"{item_id} assertion regex did not match: {regex}",
            )


def validate_catalog() -> None:
    payload = require_mapping(
        yaml.safe_load(read_text("config/checklist_dry_run.yaml")),
        "checklist dry-run catalog must be a mapping",
    )
    require(
        payload.get("schema_version") == "checklist_dry_run_v1",
        "unexpected checklist dry-run schema",
    )
    require(
        payload.get("operator_runbook") == "docs/runbooks/checklist_dry_run.md",
        "checklist dry-run runbook mismatch",
    )
    require(
        payload.get("status") == "repo_local_validate_only",
        "checklist dry-run catalog must remain validate-only",
    )
    require(
        payload.get("validation") == "scripts/run_checklist_dry_run_check.ps1",
        "checklist dry-run validation wrapper mismatch",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "checklist dry-run limits changed without validator update",
    )
    validate_candidate_shape(payload)

    checklists = require_non_empty_list(payload.get("checklists"), "checklists missing")
    seen_checklists: set[str] = set()
    seen_statuses: set[str] = set()
    for raw_checklist in checklists:
        checklist = require_mapping(raw_checklist, "each checklist must be a mapping")
        checklist_id = require_text(checklist.get("id"), "checklist id missing")
        require(checklist_id not in seen_checklists, f"duplicate checklist: {checklist_id}")
        seen_checklists.add(checklist_id)
        expected_source = REQUIRED_CHECKLISTS.get(checklist_id)
        if expected_source is None:
            raise SystemExit(f"unexpected checklist id: {checklist_id}")
        require(
            checklist.get("source") == expected_source,
            f"{checklist_id} source mismatch",
        )
        require_existing(expected_source)
        require(
            checklist.get("scope") == "intentionally_scoped_pre_expansion_gate",
            f"{checklist_id} scope must remain intentionally scoped",
        )
        source_item_ids = checklist_item_ids(expected_source)
        dry_run = require_non_empty_list(
            checklist.get("dry_run"),
            f"{checklist_id} dry-run items missing",
        )
        catalog_item_ids: set[str] = set()
        for raw_item in dry_run:
            item = require_mapping(raw_item, f"{checklist_id} item must be a mapping")
            item_id = require_text(item.get("item_id"), f"{checklist_id} item id missing")
            require(item_id not in catalog_item_ids, f"duplicate dry-run item: {item_id}")
            catalog_item_ids.add(item_id)
            status = require_text(item.get("status"), f"{item_id} status missing")
            require(status in ALLOWED_STATUSES, f"{item_id} unexpected status: {status}")
            require(status != "approved", f"{item_id} must not be approved by dry run")
            seen_statuses.add(status)
            evidence = require_non_empty_list(item.get("evidence"), f"{item_id} evidence missing")
            for evidence_path in evidence:
                require(isinstance(evidence_path, str), f"{item_id} evidence must be strings")
                require_existing(evidence_path)
            if status == "repo_confirmed":
                validate_evidence_assertions(item.get("evidence_assertions"), item_id)
            if status != "repo_confirmed":
                require_text(item.get("next_action"), f"{item_id} next action missing")
                blocker_authority = require_non_empty_list(
                    item.get("blocker_authority"),
                    f"{item_id} blocker authority missing",
                )
                for authority_path in blocker_authority:
                    require(
                        isinstance(authority_path, str),
                        f"{item_id} blocker authority must be strings",
                    )
                    require_existing(authority_path)
                if status == "blocked_external_authority":
                    external_authorities = {
                        normalize_path(authority_path)
                        for authority_path in blocker_authority
                        if isinstance(authority_path, str)
                    } - {normalize_path(expected_source)}
                    require(
                        bool(external_authorities),
                        f"{item_id} blocked authority cannot point only at checklist",
                    )
        require(
            catalog_item_ids == source_item_ids,
            f"{checklist_id} dry-run coverage mismatch: "
            f"missing={sorted(source_item_ids - catalog_item_ids)} "
            f"unexpected={sorted(catalog_item_ids - source_item_ids)}",
        )
    require(
        seen_checklists == set(REQUIRED_CHECKLISTS),
        f"checklist set mismatch: {sorted(seen_checklists)}",
    )
    require(
        REQUIRED_FAIL_CLOSED_STATUSES.issubset(seen_statuses),
        "dry run must exercise every fail-closed status class",
    )


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/checklist_dry_run.md")
    for phrase in (
        "run_checklist_dry_run_check.ps1",
        "checklist_dry_run_v1",
        "validate-only",
        "hypothetical_not_selected",
        "missing_candidate_decision",
        "missing_repo_evidence",
        "blocked_external_authority",
        "not_applicable_existing_scope",
        "does not approve a new geography",
        "does not approve a new rulepack",
        "does not unblock DS-017",
        "does not claim hosted production readiness",
    ):
        require(phrase in runbook, f"checklist dry-run runbook missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_runbook()
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
