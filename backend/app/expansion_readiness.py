from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

EXPECTED_SCHEMA_VERSION = "checklist_dry_run_v1"
EXPECTED_STATUS = "repo_local_validate_only"
EXPECTED_VALIDATION = "scripts/run_checklist_dry_run_check.ps1"
EXPECTED_OPERATOR_RUNBOOK = "docs/runbooks/checklist_dry_run.md"
EXPECTED_CANDIDATE_STATUS = "hypothetical_not_selected"
EXPECTED_APPROVALS = {
    "new_geography_selected": False,
    "new_rulepack_approved": False,
    "new_source_approved": False,
    "ds017_unblocked": False,
    "hosted_production_ready": False,
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


class ExpansionReadinessError(RuntimeError):
    """Raised when expansion readiness artifacts cannot be displayed safely."""


@dataclass(frozen=True)
class ExpansionCandidate:
    candidate_id: str
    status: str
    description: str
    authority: tuple[str, ...]
    approvals: dict[str, bool]


@dataclass(frozen=True)
class EvidenceAssertion:
    path: str
    contains: str | None
    regex: str | None


@dataclass(frozen=True)
class ChecklistItem:
    item_id: str
    status: str
    evidence: tuple[str, ...]
    blocker_authority: tuple[str, ...]
    next_action: str | None
    evidence_assertions: tuple[EvidenceAssertion, ...]


@dataclass(frozen=True)
class ChecklistSummary:
    checklist_id: str
    source: str
    scope: str
    item_count: int
    status_counts: dict[str, int]
    items: tuple[ChecklistItem, ...]


@dataclass(frozen=True)
class ExpansionReadiness:
    schema_version: str
    status: str
    operator_runbook: str
    validation: str
    candidate: ExpansionCandidate
    limits: dict[str, bool]
    checklists: tuple[ChecklistSummary, ...]
    total_items: int
    status_counts: dict[str, int]


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_expansion_readiness(repo_root: Path | None = None) -> ExpansionReadiness:
    root = repo_root or repo_root_from_app()
    payload = _read_yaml(root / "config" / "checklist_dry_run.yaml")
    return parse_expansion_readiness(payload, root=root)


def parse_expansion_readiness(
    payload: dict[str, Any],
    *,
    root: Path,
) -> ExpansionReadiness:
    schema_version = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_SCHEMA_VERSION,
        "schema_version",
    )
    status = _require_exact_text(payload.get("status"), EXPECTED_STATUS, "status")
    operator_runbook = _require_exact_text(
        payload.get("operator_runbook"),
        EXPECTED_OPERATOR_RUNBOOK,
        "operator_runbook",
    )
    validation = _require_exact_text(
        payload.get("validation"),
        EXPECTED_VALIDATION,
        "validation",
    )
    _require_existing(root, operator_runbook)
    _require_existing(root, validation)

    limits = _require_bool_mapping(payload.get("limits"), "limits missing")
    if limits != EXPECTED_LIMITS:
        raise ExpansionReadinessError("checklist dry-run limits changed")

    candidate = _candidate_from_payload(payload.get("candidate_shape"), root)
    checklists = _checklists_from_payload(payload.get("checklists"), root)
    status_counter: Counter[str] = Counter()
    total_items = 0
    for checklist in checklists:
        total_items += checklist.item_count
        status_counter.update(checklist.status_counts)
    if not REQUIRED_FAIL_CLOSED_STATUSES.issubset(set(status_counter)):
        raise ExpansionReadinessError("dry run must exercise every fail-closed status class")

    return ExpansionReadiness(
        schema_version=schema_version,
        status=status,
        operator_runbook=operator_runbook,
        validation=validation,
        candidate=candidate,
        limits=limits,
        checklists=checklists,
        total_items=total_items,
        status_counts=dict(sorted(status_counter.items())),
    )


def _candidate_from_payload(raw_candidate: Any, root: Path) -> ExpansionCandidate:
    candidate = _require_mapping(raw_candidate, "candidate_shape missing")
    candidate_id = _require_text(candidate.get("id"), "candidate id missing")
    status = _require_exact_text(
        candidate.get("status"),
        EXPECTED_CANDIDATE_STATUS,
        "candidate status",
    )
    description = _require_text(candidate.get("description"), "candidate description missing")
    authority = _require_text_tuple(candidate.get("authority"), "candidate authority missing")
    for path_text in authority:
        _require_existing(root, path_text)
    approvals = _require_bool_mapping(candidate.get("approvals"), "candidate approvals missing")
    if approvals != EXPECTED_APPROVALS:
        raise ExpansionReadinessError("candidate approvals changed")
    return ExpansionCandidate(
        candidate_id=candidate_id,
        status=status,
        description=description,
        authority=authority,
        approvals=approvals,
    )


def _checklists_from_payload(raw_checklists: Any, root: Path) -> tuple[ChecklistSummary, ...]:
    checklists = _require_list(raw_checklists, "checklists missing")
    summaries: list[ChecklistSummary] = []
    seen: set[str] = set()
    for raw_checklist in checklists:
        checklist = _require_mapping(raw_checklist, "each checklist must be a mapping")
        checklist_id = _require_text(checklist.get("id"), "checklist id missing")
        if checklist_id in seen:
            raise ExpansionReadinessError(f"duplicate checklist: {checklist_id}")
        seen.add(checklist_id)
        expected_source = REQUIRED_CHECKLISTS.get(checklist_id)
        if expected_source is None:
            raise ExpansionReadinessError(f"unexpected checklist id: {checklist_id}")
        source = _require_exact_text(checklist.get("source"), expected_source, checklist_id)
        _require_existing(root, source)
        scope = _require_exact_text(
            checklist.get("scope"),
            "intentionally_scoped_pre_expansion_gate",
            f"{checklist_id}.scope",
        )
        source_item_ids = _checklist_item_ids(root, source)
        items = _items_from_payload(
            checklist.get("dry_run"),
            checklist_id=checklist_id,
            source=source,
            expected_item_ids=source_item_ids,
            root=root,
        )
        status_counts = dict(sorted(Counter(item.status for item in items).items()))
        summaries.append(
            ChecklistSummary(
                checklist_id=checklist_id,
                source=source,
                scope=scope,
                item_count=len(items),
                status_counts=status_counts,
                items=items,
            )
        )
    if seen != set(REQUIRED_CHECKLISTS):
        raise ExpansionReadinessError("checklist set mismatch")
    return tuple(sorted(summaries, key=lambda item: item.checklist_id))


def _items_from_payload(
    raw_items: Any,
    *,
    checklist_id: str,
    source: str,
    expected_item_ids: set[str],
    root: Path,
) -> tuple[ChecklistItem, ...]:
    raw_items_list = _require_list(raw_items, f"{checklist_id} dry-run items missing")
    items: list[ChecklistItem] = []
    seen: set[str] = set()
    for raw_item in raw_items_list:
        item = _require_mapping(raw_item, f"{checklist_id} item must be a mapping")
        item_id = _require_text(item.get("item_id"), f"{checklist_id} item id missing")
        if item_id in seen:
            raise ExpansionReadinessError(f"duplicate dry-run item: {item_id}")
        seen.add(item_id)
        status = _require_text(item.get("status"), f"{item_id} status missing")
        if status not in ALLOWED_STATUSES or status == "approved":
            raise ExpansionReadinessError(f"{item_id} unexpected status: {status}")
        evidence = _require_text_tuple(item.get("evidence"), f"{item_id} evidence missing")
        for path_text in evidence:
            _require_existing(root, path_text)
        blocker_authority: tuple[str, ...] = ()
        next_action = None
        evidence_assertions: tuple[EvidenceAssertion, ...] = ()
        if status == "repo_confirmed":
            evidence_assertions = _assertions_from_payload(
                item.get("evidence_assertions"),
                item_id=item_id,
                root=root,
            )
        else:
            next_action = _require_text(item.get("next_action"), f"{item_id} next action missing")
            blocker_authority = _require_text_tuple(
                item.get("blocker_authority"),
                f"{item_id} blocker authority missing",
            )
            for path_text in blocker_authority:
                _require_existing(root, path_text)
            if status == "blocked_external_authority":
                external_authority = {
                    _normalize_path(path_text)
                    for path_text in blocker_authority
                } - {_normalize_path(source)}
                if not external_authority:
                    raise ExpansionReadinessError(
                        f"{item_id} blocked authority cannot point only at checklist"
                    )
        items.append(
            ChecklistItem(
                item_id=item_id,
                status=status,
                evidence=evidence,
                blocker_authority=blocker_authority,
                next_action=next_action,
                evidence_assertions=evidence_assertions,
            )
        )
    if seen != expected_item_ids:
        raise ExpansionReadinessError(
            f"{checklist_id} dry-run coverage mismatch: "
            f"missing={sorted(expected_item_ids - seen)} "
            f"unexpected={sorted(seen - expected_item_ids)}"
        )
    return tuple(items)


def _assertions_from_payload(
    raw_assertions: Any,
    *,
    item_id: str,
    root: Path,
) -> tuple[EvidenceAssertion, ...]:
    assertions = _require_list(raw_assertions, f"{item_id} evidence assertions missing")
    parsed: list[EvidenceAssertion] = []
    for raw_assertion in assertions:
        assertion = _require_mapping(raw_assertion, f"{item_id} assertion must be a mapping")
        path_text = _require_text(assertion.get("path"), f"{item_id} assertion path missing")
        _require_existing(root, path_text)
        contains = assertion.get("contains")
        regex = assertion.get("regex")
        has_contains = isinstance(contains, str) and regex is None
        has_regex = contains is None and isinstance(regex, str)
        if not (has_contains or has_regex):
            raise ExpansionReadinessError(
                f"{item_id} assertion must provide exactly one of contains or regex"
            )
        if isinstance(contains, str) and not contains.strip():
            raise ExpansionReadinessError(
                f"{item_id} assertion contains must be a non-empty string"
            )
        if isinstance(regex, str) and not regex.strip():
            raise ExpansionReadinessError(
                f"{item_id} assertion regex must be a non-empty string"
            )
        text = _read_text(root, path_text)
        if isinstance(contains, str) and contains not in text:
            raise ExpansionReadinessError(f"{item_id} assertion missing text: {contains}")
        if isinstance(regex, str) and re.search(regex, text, flags=re.MULTILINE) is None:
            raise ExpansionReadinessError(f"{item_id} assertion regex did not match: {regex}")
        parsed.append(EvidenceAssertion(path=path_text, contains=contains, regex=regex))
    if not parsed:
        raise ExpansionReadinessError(f"{item_id} evidence assertions missing")
    return tuple(parsed)


def _checklist_item_ids(root: Path, path_text: str) -> set[str]:
    ids: set[str] = set()
    for line in _read_text(root, path_text).splitlines():
        stripped = line.strip()
        if stripped.startswith("- [") and re.match(r"^- \[[ xX]\] .+$", stripped) is None:
            raise ExpansionReadinessError(f"unsupported checkbox marker in {path_text}: {stripped}")
        match = re.match(r"^- \[[ xX]\] (?P<item>.+)$", stripped)
        if match is None:
            continue
        item_id = _slugify(match.group("item").strip())
        if item_id in ids:
            raise ExpansionReadinessError(f"duplicate checklist item id in {path_text}: {item_id}")
        ids.add(item_id)
    if not ids:
        raise ExpansionReadinessError(f"no checkbox items found in {path_text}")
    return ids


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ExpansionReadinessError(f"cannot read {path}") from exc
    return _require_mapping(payload, f"{path} must be a mapping")


def _read_text(root: Path, path_text: str) -> str:
    path = _resolved_repo_path(root, path_text)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ExpansionReadinessError(f"cannot read {path_text}") from exc


def _require_existing(root: Path, path_text: str) -> None:
    path = _resolved_repo_path(root, path_text)
    if not path.exists():
        raise ExpansionReadinessError(f"referenced expansion artifact missing: {path_text}")


def _resolved_repo_path(root: Path, path_text: str) -> Path:
    if not path_text:
        raise ExpansionReadinessError("empty path reference")
    candidate = Path(_normalize_path(path_text))
    if candidate.is_absolute():
        raise ExpansionReadinessError(f"path must be repo-relative: {path_text}")
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ExpansionReadinessError(f"path escapes repo root: {path_text}") from exc
    return resolved


def _require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExpansionReadinessError(message)
    return value


def _require_bool_mapping(value: Any, message: str) -> dict[str, bool]:
    raw = _require_mapping(value, message)
    if not all(isinstance(key, str) and isinstance(val, bool) for key, val in raw.items()):
        raise ExpansionReadinessError(message)
    return {str(key): bool(val) for key, val in raw.items()}


def _require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ExpansionReadinessError(message)
    return value


def _require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExpansionReadinessError(message)
    return value.strip()


def _require_exact_text(value: Any, expected: str, label: str) -> str:
    text = _require_text(value, f"{label} missing")
    if text != expected:
        raise ExpansionReadinessError(f"{label} must be {expected}")
    return text


def _require_text_tuple(value: Any, message: str) -> tuple[str, ...]:
    values = _require_list(value, message)
    text_values = tuple(_require_text(item, message) for item in values)
    if not text_values:
        raise ExpansionReadinessError(message)
    return text_values


def _normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return re.sub(r"_+", "_", slug)
