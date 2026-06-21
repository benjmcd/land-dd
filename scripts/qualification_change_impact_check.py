#!/usr/bin/env python3
"""Report qualification change-impact implications for a changed path set."""

import argparse
import json
import subprocess
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:
    raise SystemExit("Missing dev dependency. Install PyYAML before running change-impact checks.") from exc


DOCS_NONSEMANTIC_CLASS = "DOCS_NONSEMANTIC"


class QualificationChangeImpactError(RuntimeError):
    """Raised when change-impact inputs cannot be analyzed safely."""


@dataclass(frozen=True)
class ImpactReport:
    changed_paths: list[str]
    change_classes: list[str]
    review_groups: list[str]
    invalidate_criterion_ids: list[str]
    surface_ids: list[str]
    surface_criterion_ids: list[str]
    unmatched_paths: list[str]
    path_impacts: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "changed_paths": self.changed_paths,
            "change_classes": self.change_classes,
            "review_groups": self.review_groups,
            "invalidate_criterion_ids": self.invalidate_criterion_ids,
            "surface_ids": self.surface_ids,
            "surface_criterion_ids": self.surface_criterion_ids,
            "unmatched_paths": self.unmatched_paths,
            "path_impacts": self.path_impacts,
            "warnings": self.warnings,
        }


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QualificationChangeImpactError(f"YAML object required: {path}")
    return payload


def add_unique(values: list[str], new_values: Iterable[str]) -> None:
    for value in new_values:
        if value not in values:
            values.append(value)


def catalog_ids(catalog: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for item in catalog.get("criteria") or []:
        if isinstance(item, dict) and item.get("criterion_id"):
            ids.add(str(item["criterion_id"]))
    return ids


def normalize_changed_path(root: Path, path_text: str) -> str:
    root = root.resolve()
    raw = path_text.strip()
    if not raw:
        raise QualificationChangeImpactError("changed path must not be empty")
    path = Path(raw)
    if path.is_absolute():
        raise QualificationChangeImpactError(f"changed path must be repo-relative: {path_text}")
    absolute = (root / path).resolve()
    try:
        absolute.relative_to(root)
    except ValueError as exc:
        raise QualificationChangeImpactError(f"changed path escapes repo: {path_text}") from exc

    normalized = PurePosixPath(*path.parts).as_posix()
    if normalized in {"", "."}:
        raise QualificationChangeImpactError(f"changed path must name a repo file: {path_text}")
    if normalized.startswith("../") or normalized == "..":
        raise QualificationChangeImpactError(f"changed path escapes repo: {path_text}")
    return normalized


def normalize_changed_paths(root: Path, changed_paths: Iterable[str]) -> list[str]:
    paths: list[str] = []
    for path_text in changed_paths:
        if not path_text.strip():
            continue
        normalized = normalize_changed_path(root, path_text)
        if normalized not in paths:
            paths.append(normalized)
    return paths


def validate_path_glob(change_class: str, pattern: str) -> None:
    normalized = pattern.replace("\\", "/")
    path = PurePosixPath(normalized)
    if normalized.startswith("/") or ".." in path.parts:
        raise QualificationChangeImpactError(
            f"change_impact_matrix.{change_class}.path_globs contains unsafe pattern: {pattern}"
        )


def validate_inputs(
    change_matrix: dict[str, Any],
    crosswalk: dict[str, Any],
    catalog: dict[str, Any],
) -> None:
    ids = catalog_ids(catalog)
    if not ids:
        raise QualificationChangeImpactError("criterion catalog has no criteria")

    for change_class, entry in (change_matrix.get("change_classes") or {}).items():
        invalidates = [str(value) for value in entry.get("invalidate_by_default") or []]
        unknown = sorted(set(invalidates) - ids)
        if unknown:
            raise QualificationChangeImpactError(
                f"change_impact_matrix.{change_class}.invalidate_by_default: "
                f"unknown criterion IDs {unknown}"
            )
        path_globs = [str(value) for value in entry.get("path_globs") or []]
        if change_class != DOCS_NONSEMANTIC_CLASS and not path_globs:
            raise QualificationChangeImpactError(
                f"change_impact_matrix.{change_class}.path_globs must not be empty"
            )
        for pattern in path_globs:
            validate_path_glob(str(change_class), pattern)

    for entry in crosswalk.get("entries") or []:
        surface_id = entry.get("surface_id")
        criterion_ids = [str(value) for value in entry.get("criterion_ids") or []]
        unknown = sorted(set(criterion_ids) - ids)
        if unknown:
            raise QualificationChangeImpactError(
                f"readiness_crosswalk.{surface_id}: unknown criterion IDs {unknown}"
            )


def surface_entries_by_path(crosswalk: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    entries_by_path: dict[str, list[dict[str, Any]]] = {}
    for entry in crosswalk.get("entries") or []:
        for path in list(entry.get("config_paths") or []) + list(entry.get("checker_paths") or []):
            entries_by_path.setdefault(str(path), []).append(entry)
    return entries_by_path


def path_matches(patterns: Iterable[str], path: str) -> bool:
    return any(fnmatchcase(path, pattern.replace("\\", "/")) for pattern in patterns)


def analyze_changed_paths(
    root: Path,
    changed_paths: Iterable[str],
    change_matrix: dict[str, Any],
    crosswalk: dict[str, Any],
    catalog: dict[str, Any],
    warnings: Iterable[str] = (),
) -> ImpactReport:
    validate_inputs(change_matrix, crosswalk, catalog)
    normalized_paths = normalize_changed_paths(root, changed_paths)
    matrix_entries = change_matrix.get("change_classes") or {}
    surfaces_by_path = surface_entries_by_path(crosswalk)

    change_classes: list[str] = []
    review_groups: list[str] = []
    invalidate_ids: list[str] = []
    surface_ids: list[str] = []
    surface_criterion_ids: list[str] = []
    unmatched_paths: list[str] = []
    path_impacts: dict[str, dict[str, list[str]]] = {}

    for path in normalized_paths:
        matched_classes: list[str] = []
        matched_surfaces: list[str] = []
        matched_surface_criteria: list[str] = []

        for change_class, entry in matrix_entries.items():
            if path_matches(entry.get("path_globs") or [], path):
                matched_classes.append(str(change_class))
                add_unique(change_classes, [str(change_class)])
                add_unique(review_groups, [str(value) for value in entry.get("review") or []])
                add_unique(invalidate_ids, [str(value) for value in entry.get("invalidate_by_default") or []])

        for surface in surfaces_by_path.get(path, []):
            surface_id = str(surface.get("surface_id"))
            criteria = [str(value) for value in surface.get("criterion_ids") or []]
            matched_surfaces.append(surface_id)
            add_unique(matched_surface_criteria, criteria)
            add_unique(surface_ids, [surface_id])
            add_unique(surface_criterion_ids, criteria)

        if not matched_classes and not matched_surfaces:
            unmatched_paths.append(path)

        path_impacts[path] = {
            "change_classes": matched_classes,
            "surface_ids": matched_surfaces,
            "surface_criterion_ids": matched_surface_criteria,
        }

    return ImpactReport(
        changed_paths=normalized_paths,
        change_classes=change_classes,
        review_groups=review_groups,
        invalidate_criterion_ids=invalidate_ids,
        surface_ids=surface_ids,
        surface_criterion_ids=surface_criterion_ids,
        unmatched_paths=unmatched_paths,
        path_impacts=path_impacts,
        warnings=list(warnings),
    )


def read_changed_paths_file(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def git_changed_paths(root: Path, base_ref: str) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    candidates = [
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        ["git", "diff", "--name-only", "HEAD~1..HEAD"],
    ]
    for command in candidates:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return [line for line in result.stdout.splitlines() if line.strip()], warnings
        warnings.append(
            f"could not read changed paths with {' '.join(command)}: {result.stderr.strip()}"
        )
    warnings.append("no git diff base was available; treating changed path set as empty")
    return [], warnings


def changed_paths_from_args(args: argparse.Namespace, root: Path) -> tuple[list[str], list[str]]:
    paths: list[str] = []
    warnings: list[str] = []
    for path in args.changed_path or []:
        paths.append(path)
    if args.changed_paths_file:
        paths.extend(read_changed_paths_file(args.changed_paths_file))
    if paths:
        return paths, warnings
    return git_changed_paths(root, args.base_ref)


def format_list(label: str, values: list[str]) -> str:
    if values:
        return f"{label}: {', '.join(values)}"
    return f"{label}: none"


def print_report(report: ImpactReport) -> None:
    print("qualification change impact: advisory")
    print(f"changed paths: {len(report.changed_paths)}")
    for warning in report.warnings:
        print(f"warning: {warning}")
    print(format_list("change classes", report.change_classes))
    print(format_list("review groups", report.review_groups))
    print(format_list("invalidate_by_default criteria", report.invalidate_criterion_ids))
    print(format_list("crosswalk surfaces", report.surface_ids))
    print(format_list("crosswalk criteria", report.surface_criterion_ids))
    print(format_list("unmatched paths", report.unmatched_paths))
    for path, impact in report.path_impacts.items():
        print(
            f"path {path}: "
            f"classes={impact['change_classes'] or ['none']} "
            f"surfaces={impact['surface_ids'] or ['none']}"
        )
    print("qualification change impact check: ok")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report advisory qualification impact for changed repo paths.",
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--change-matrix", type=Path)
    parser.add_argument("--crosswalk", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--changed-path", action="append")
    parser.add_argument("--changed-paths-file", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    change_matrix_path = args.change_matrix or root / "config" / "qualification" / "change_impact_matrix.yaml"
    crosswalk_path = args.crosswalk or root / "config" / "qualification" / "readiness_crosswalk.yaml"
    catalog_path = args.catalog or root / "config" / "qualification" / "criterion_catalog.yaml"

    try:
        changed_paths, warnings = changed_paths_from_args(args, root)
        report = analyze_changed_paths(
            root=root,
            changed_paths=changed_paths,
            change_matrix=load_yaml(change_matrix_path.resolve()),
            crosswalk=load_yaml(crosswalk_path.resolve()),
            catalog=load_yaml(catalog_path.resolve()),
            warnings=warnings,
        )
    except QualificationChangeImpactError as exc:
        print(f"FAIL: {exc}")
        print("qualification change impact check: FAIL")
        return 1

    if args.json_output:
        print(json.dumps(report.to_jsonable(), indent=2, sort_keys=True))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
