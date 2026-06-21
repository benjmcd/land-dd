from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

EXPECTED_SCHEMA_VERSION = "release_readiness_v1"
EXPECTED_OPERATOR_RUNBOOK = "docs/runbooks/release_readiness.md"


class ReleaseReadinessError(RuntimeError):
    """Raised when release-readiness artifacts cannot be trusted for rendering."""


@dataclass(frozen=True)
class ReleaseCheck:
    check_id: str
    proof: str
    ci_job: str | None


@dataclass(frozen=True)
class ReleaseBlocker:
    blocker_id: str
    status: str
    authority: str


@dataclass(frozen=True)
class ReleaseReadiness:
    schema_version: str
    operator_runbook: str
    checks: tuple[ReleaseCheck, ...]
    blockers: tuple[ReleaseBlocker, ...]

    @property
    def check_ids(self) -> tuple[str, ...]:
        return tuple(check.check_id for check in self.checks)

    @property
    def blocker_ids(self) -> tuple[str, ...]:
        return tuple(blocker.blocker_id for blocker in self.blockers)

    @property
    def ci_backed_check_count(self) -> int:
        return sum(1 for check in self.checks if check.ci_job is not None)

    @property
    def local_only_check_count(self) -> int:
        return len(self.checks) - self.ci_backed_check_count


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_release_readiness(repo_root: Path | None = None) -> ReleaseReadiness:
    root = repo_root or repo_root_from_app()
    payload = _read_yaml(root / "config" / "release_readiness.yaml")
    return parse_release_readiness(payload, root=root)


def parse_release_readiness(payload: dict[str, Any], *, root: Path) -> ReleaseReadiness:
    schema_version = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_SCHEMA_VERSION,
        "schema_version",
    )
    operator_runbook = _require_exact_text(
        payload.get("operator_runbook"),
        EXPECTED_OPERATOR_RUNBOOK,
        "operator_runbook",
    )
    _require_existing(root, operator_runbook)
    checks = _parse_checks(payload.get("required_checks"), root)
    blockers = _parse_blockers(payload.get("release_blockers"), root)
    return ReleaseReadiness(
        schema_version=schema_version,
        operator_runbook=operator_runbook,
        checks=checks,
        blockers=blockers,
    )


def _parse_checks(value: Any, root: Path) -> tuple[ReleaseCheck, ...]:
    checks: list[ReleaseCheck] = []
    seen: set[str] = set()
    for raw_check in _require_list(value, "release required_checks missing"):
        check = _require_mapping(raw_check, "each release check must be a mapping")
        check_id = _require_text(check.get("id"), "release check id missing")
        if check_id in seen:
            raise ReleaseReadinessError(f"duplicate release check: {check_id}")
        seen.add(check_id)
        proof = _require_text(check.get("proof"), f"{check_id} proof missing")
        _require_existing(root, proof)
        ci_job = check.get("ci_job")
        if ci_job is not None and not isinstance(ci_job, str):
            raise ReleaseReadinessError(f"{check_id} ci_job must be text or null")
        if isinstance(ci_job, str) and not ci_job.strip():
            raise ReleaseReadinessError(f"{check_id} ci_job cannot be blank")
        checks.append(
            ReleaseCheck(
                check_id=check_id,
                proof=proof,
                ci_job=ci_job.strip() if isinstance(ci_job, str) else None,
            )
        )
    return tuple(sorted(checks, key=lambda check: check.check_id))


def _parse_blockers(value: Any, root: Path) -> tuple[ReleaseBlocker, ...]:
    blockers: list[ReleaseBlocker] = []
    seen: set[str] = set()
    for raw_blocker in _require_list(value, "release blockers missing"):
        blocker = _require_mapping(raw_blocker, "each release blocker must be a mapping")
        blocker_id = _require_text(blocker.get("id"), "release blocker id missing")
        if blocker_id in seen:
            raise ReleaseReadinessError(f"duplicate release blocker: {blocker_id}")
        seen.add(blocker_id)
        status = _require_exact_text(
            blocker.get("status"),
            "blocked",
            f"{blocker_id} status",
        )
        authority = _require_text(blocker.get("authority"), f"{blocker_id} authority missing")
        _require_existing(root, authority)
        blockers.append(
            ReleaseBlocker(
                blocker_id=blocker_id,
                status=status,
                authority=authority,
            )
        )
    return tuple(sorted(blockers, key=lambda blocker: blocker.blocker_id))


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ReleaseReadinessError(f"cannot read {path}") from exc
    return _require_mapping(payload, f"{path} must be a mapping")


def _require_existing(root: Path, path_text: str) -> None:
    path = _resolved_repo_path(root, path_text)
    if not path.exists():
        raise ReleaseReadinessError(f"referenced release artifact missing: {path_text}")


def _resolved_repo_path(root: Path, path_text: str) -> Path:
    candidate = Path(path_text.replace("\\", "/"))
    if candidate.is_absolute():
        raise ReleaseReadinessError(f"path must be repo-relative: {path_text}")
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ReleaseReadinessError(f"path escapes repo root: {path_text}") from exc
    return resolved


def _require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReleaseReadinessError(message)
    return value


def _require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ReleaseReadinessError(message)
    return value


def _require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReleaseReadinessError(message)
    return value.strip()


def _require_exact_text(value: Any, expected: str, label: str) -> str:
    text = _require_text(value, f"{label} missing")
    if text != expected:
        raise ReleaseReadinessError(f"{label} must be {expected}")
    return text
