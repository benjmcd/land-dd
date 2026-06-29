from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

EXPECTED_AUTHORITY_TITLES = (
    "DS-017 Commercial Parcel Vendor Authority",
    "Hosted Platform Authority",
    "Secrets Authority",
    "Identity And RBAC Authority",
    "Image Publication Authority",
    "Billing And Cost Authority",
    "Alerting Authority",
    "Production Workload And Retention Authority",
    "Bologna Recorded-Source Pilot Authority",
)
AUTHORITY_SECTION_LABEL = "- External decisions required:"
EXPECTED_EXTERNAL_AREAS = {
    "Hosted deployment",
    "Secret management",
    "Identity/RBAC",
    "DS-017 commercial parcel vendor",
    "Registry/image publication",
    "Hosted alerting/on-call",
    "Billing/cost approval",
    "Hosted workload/SLO",
}
REQUIRED_FAIL_CLOSED_PHRASES = (
    "Do not implement a DS-017 connector",
    "hosted deployment",
    "full identity/RBAC",
    "registry image publication",
)


class ProductionAuthorityError(RuntimeError):
    """Raised when authority artifacts cannot be trusted for UI rendering."""


@dataclass(frozen=True)
class AuthorityRequirement:
    title: str
    decisions: tuple[str, ...]
    evidence: tuple[str, ...]
    criteria: tuple[str, ...]
    unlocked_lane: tuple[str, ...]


@dataclass(frozen=True)
class ExternalAuthorityBlocker:
    area: str
    required_authority: str
    current_authority: str


@dataclass(frozen=True)
class RepoLocalCandidate:
    candidate: str
    why_repo_local: str
    boundary: str


@dataclass(frozen=True)
class ProductionAuthorityReadiness:
    packet_path: str
    split_path: str
    fail_closed_rule: str
    requirements: tuple[AuthorityRequirement, ...]
    external_blockers: tuple[ExternalAuthorityBlocker, ...]
    repo_local_candidates: tuple[RepoLocalCandidate, ...]
    open_blockers: tuple[str, ...]


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_production_authority(repo_root: Path | None = None) -> ProductionAuthorityReadiness:
    root = repo_root or repo_root_from_app()
    packet_path = root / "state" / "PRODUCTION_AUTHORITY_PACKET.md"
    split_path = root / "state" / "POST_RC_AUTHORITY_SPLIT.md"
    return parse_production_authority(
        _read_required_text(packet_path),
        _read_required_text(split_path),
    )


def parse_production_authority(
    packet_text: str,
    split_text: str,
) -> ProductionAuthorityReadiness:
    if not packet_text.strip():
        raise ProductionAuthorityError("production authority packet is empty")
    if not split_text.strip():
        raise ProductionAuthorityError("post-RC authority split is empty")
    fail_closed_rule = _fail_closed_rule(packet_text)
    requirements = tuple(
        _parse_requirement(packet_text, title) for title in EXPECTED_AUTHORITY_TITLES
    )
    _require_authority_section_coverage(packet_text)
    external_blockers = _parse_external_blockers(split_text)
    repo_local_candidates = _parse_repo_local_candidates(split_text)
    open_blockers = _top_level_bullets(_required_section(packet_text, "Open Blockers"))
    if not open_blockers:
        raise ProductionAuthorityError("Open Blockers section has no blockers")
    return ProductionAuthorityReadiness(
        packet_path="state/PRODUCTION_AUTHORITY_PACKET.md",
        split_path="state/POST_RC_AUTHORITY_SPLIT.md",
        fail_closed_rule=fail_closed_rule,
        requirements=requirements,
        external_blockers=external_blockers,
        repo_local_candidates=repo_local_candidates,
        open_blockers=open_blockers,
    )


def _parse_requirement(text: str, title: str) -> AuthorityRequirement:
    section = _required_section(text, title)
    decisions = _nested_bullets(section, "External decisions required:")
    evidence = _nested_bullets(section, "Evidence fields required:")
    criteria = _nested_bullets(section, "Acceptable unblock criteria:")
    unlocked_lane = _nested_bullets(section, "Repo lane unlocked only after authority exists:")
    if not decisions:
        raise ProductionAuthorityError(f"{title} External decisions list is empty")
    if not evidence:
        raise ProductionAuthorityError(f"{title} Evidence fields list is empty")
    if not criteria:
        raise ProductionAuthorityError(f"{title} Acceptable unblock criteria list is empty")
    if not unlocked_lane:
        raise ProductionAuthorityError(f"{title} Repo lane unlocked list is empty")
    return AuthorityRequirement(
        title=title,
        decisions=decisions,
        evidence=evidence,
        criteria=criteria,
        unlocked_lane=unlocked_lane,
    )


def _parse_external_blockers(text: str) -> tuple[ExternalAuthorityBlocker, ...]:
    section = _required_section(text, "External-Authority Blockers")
    rows = _parse_table(section, ("Area", "Required authority/evidence", "Current authority"))
    blockers = tuple(
        ExternalAuthorityBlocker(
            area=row[0],
            required_authority=row[1],
            current_authority=row[2],
        )
        for row in rows
    )
    areas = {blocker.area for blocker in blockers}
    if areas != EXPECTED_EXTERNAL_AREAS:
        missing = sorted(EXPECTED_EXTERNAL_AREAS - areas)
        extra = sorted(areas - EXPECTED_EXTERNAL_AREAS)
        raise ProductionAuthorityError(
            "external authority blocker table mismatch: "
            f"missing={', '.join(missing) or 'none'} extra={', '.join(extra) or 'none'}"
        )
    return tuple(sorted(blockers, key=lambda item: item.area))


def _parse_repo_local_candidates(text: str) -> tuple[RepoLocalCandidate, ...]:
    section = _required_section(text, "Repo-Local Implementation Candidates")
    rows = _parse_table(section, ("Candidate", "Why it is repo-local", "Boundary"))
    candidates = tuple(
        RepoLocalCandidate(candidate=row[0], why_repo_local=row[1], boundary=row[2])
        for row in rows
    )
    if not candidates:
        raise ProductionAuthorityError("repo-local candidate table is empty")
    return candidates


def _fail_closed_rule(text: str) -> str:
    section = _required_section(text, "Fail-Closed Rule")
    paragraph = _normalize_text(section)
    missing = [phrase for phrase in REQUIRED_FAIL_CLOSED_PHRASES if phrase not in paragraph]
    if missing:
        raise ProductionAuthorityError(
            f"fail-closed rule missing required phrase: {', '.join(missing)}"
        )
    return paragraph


def _require_authority_section_coverage(text: str) -> None:
    declared = {
        match.group("title").strip()
        for match in re.finditer(r"^## (?P<title>.+?)\s*$", text, flags=re.MULTILINE)
        if AUTHORITY_SECTION_LABEL in _section_body(text, match.end())
    }
    expected = set(EXPECTED_AUTHORITY_TITLES)
    if declared != expected:
        missing = sorted(expected - declared)
        extra = sorted(declared - expected)
        raise ProductionAuthorityError(
            "authority section coverage mismatch: "
            f"missing={', '.join(missing) or 'none'} extra={', '.join(extra) or 'none'}"
        )


def _section_body(text: str, start: int) -> str:
    next_match = re.search(r"^##\s+", text[start:], flags=re.MULTILINE)
    end = len(text) if next_match is None else start + next_match.start()
    return text[start:end]


def _required_section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        raise ProductionAuthorityError(f"required authority section missing: {heading}")
    next_match = re.search(r"^##\s+", text[match.end() :], flags=re.MULTILINE)
    end = len(text) if next_match is None else match.end() + next_match.start()
    section = text[match.end() : end].strip()
    if not section:
        raise ProductionAuthorityError(f"required authority section is empty: {heading}")
    return section


def _nested_bullets(section: str, label: str) -> tuple[str, ...]:
    lines = section.splitlines()
    label_line = f"- {label}"
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == label_line),
        None,
    )
    if start is None:
        raise ProductionAuthorityError(f"{label.removesuffix(':')} label missing")
    items: list[str] = []
    active: str | None = None
    for line in lines[start + 1 :]:
        if line.startswith("- "):
            break
        stripped = line.strip()
        if not stripped:
            continue
        if line.startswith("  - "):
            if active is not None:
                items.append(_normalize_text(active))
            active = line.removeprefix("  - ").strip()
            continue
        if active is None:
            continue
        active = f"{active} {stripped}"
    if active is not None:
        items.append(_normalize_text(active))
    return tuple(items)


def _top_level_bullets(section: str) -> tuple[str, ...]:
    items: list[str] = []
    active: str | None = None
    for line in section.splitlines():
        if line.startswith("- "):
            if active is not None:
                items.append(_normalize_text(active))
            active = line.removeprefix("- ")
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if active is not None:
            # Fold a wrapped continuation line into the current bullet so
            # multi-line blockers are not truncated on the operator view.
            active = f"{active} {stripped}"
    if active is not None:
        items.append(_normalize_text(active))
    return tuple(item for item in items if item)


def _parse_table(section: str, expected_headers: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    header_found = False
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        columns = tuple(_clean_cell(cell) for cell in stripped.strip("|").split("|"))
        if columns == expected_headers:
            header_found = True
            continue
        if all(set(column) <= {"-"} for column in columns):
            continue
        if not header_found:
            continue
        if len(columns) != len(expected_headers):
            raise ProductionAuthorityError("authority table row has wrong column count")
        rows.append(columns)
    if not header_found:
        raise ProductionAuthorityError(f"authority table header missing: {expected_headers[0]}")
    if not rows:
        raise ProductionAuthorityError("authority table has no rows")
    return tuple(rows)


def _read_required_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProductionAuthorityError(f"cannot read {path}") from exc
    if not text.strip():
        raise ProductionAuthorityError(f"{path} is empty")
    return text


def _clean_cell(value: str) -> str:
    return _normalize_text(value.replace("`", ""))


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
