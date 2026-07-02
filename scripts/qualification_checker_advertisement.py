#!/usr/bin/env python3
"""Emit qualification criterion advertisements for mapped checker scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Sequence

try:
    import yaml
except ImportError as exc:
    raise SystemExit("Missing dev dependency. Install PyYAML before running qualification checks.") from exc

ADVERTISEMENT_FLAG = "--qualification-criteria-json"
SCHEMA_VERSION = "qualification_checker_advertisement_v1"


class QualificationAdvertisementError(RuntimeError):
    """Raised when a checker advertisement cannot be built safely."""


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QualificationAdvertisementError(f"YAML object required: {path}")
    return payload


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "config" / "qualification" / "readiness_crosswalk.yaml").is_file():
            return candidate
    raise QualificationAdvertisementError(f"could not find repo root from {start}")


def repo_relative_checker_path(root: Path, checker_file: str | Path) -> str:
    checker_path = Path(checker_file).resolve()
    try:
        relative = checker_path.relative_to(root.resolve())
    except ValueError as exc:
        raise QualificationAdvertisementError(
            f"checker path is outside repo root: {checker_file}",
        ) from exc
    return relative.as_posix()


def expected_entries_for_checker(
    crosswalk: dict[str, Any],
    checker_path: str,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for entry in crosswalk.get("entries") or []:
        if checker_path not in (entry.get("checker_paths") or []):
            continue
        criterion_ids = entry.get("criterion_ids") or []
        entries.append(
            {
                "surface_id": entry.get("surface_id"),
                "evidence_role": entry.get("evidence_role"),
                "criterion_ids": sorted(str(item) for item in criterion_ids),
            },
        )
    return entries


def advertisement_for_checker(
    root: Path,
    checker_path: str,
    crosswalk: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo_root = root.resolve()
    relative = Path(checker_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise QualificationAdvertisementError(f"checker path must be repo-local: {checker_path}")
    absolute = repo_root / relative
    if not absolute.is_file():
        raise QualificationAdvertisementError(f"checker path does not exist: {checker_path}")
    payload = crosswalk or load_yaml(repo_root / "config" / "qualification" / "readiness_crosswalk.yaml")
    entries = expected_entries_for_checker(payload, relative.as_posix())
    if not entries:
        raise QualificationAdvertisementError(f"checker is not mapped in crosswalk: {checker_path}")
    criterion_ids = sorted(
        {
            criterion_id
            for entry in entries
            for criterion_id in entry["criterion_ids"]
        },
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "checker_path": relative.as_posix(),
        "criterion_ids": criterion_ids,
        "entries": entries,
    }


def advertisement_for_current_checker(checker_file: str | Path) -> dict[str, Any]:
    root = find_repo_root(Path(checker_file))
    checker_path = repo_relative_checker_path(root, checker_file)
    return advertisement_for_checker(root, checker_path)


def maybe_emit_qualification_criteria(
    checker_file: str | Path,
    argv: Sequence[str] | None = None,
) -> bool:
    args = list(sys.argv[1:] if argv is None else argv)
    if ADVERTISEMENT_FLAG not in args:
        return False
    try:
        advertisement = advertisement_for_current_checker(checker_file)
    except QualificationAdvertisementError as exc:
        print(f"qualification checker advertisement failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(advertisement, sort_keys=True))
    raise SystemExit(0)


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] != "--checker":
        print("usage: qualification_checker_advertisement.py --checker scripts/<checker>.py", file=sys.stderr)
        return 2
    root = find_repo_root(Path.cwd())
    try:
        advertisement = advertisement_for_checker(root, args[1])
    except QualificationAdvertisementError as exc:
        print(f"qualification checker advertisement failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(advertisement, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
