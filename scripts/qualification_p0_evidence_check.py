#!/usr/bin/env python3
"""Validate blocked repo-local P0 auto-evidence records."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit("Missing dev dependency. Install PyYAML before running P0 evidence checks.") from exc


AUTO_EVIDENCE_IDS = ("P0-004", "P0-005", "P0-021", "P0-023")
ARTIFACT_RELATIVE_PATH = "docs/qualification/P0_AUTO_EVIDENCE.yaml"
BACKLOG_RELATIVE_PATH = "state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md"
BACKLOG_STATUS_PHRASE = "auto-evidenced; still target-blocked"
EXPECTED_SCHEMA_VERSION = "qualification_p0_auto_evidence_v1"
SUPPRESSION_TOKENS = ("pytest.mark.xfail", "@pytest.mark.xfail", "xfail(")


class QualificationP0EvidenceError(RuntimeError):
    """Raised when P0 auto-evidence inputs cannot be read safely."""


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise QualificationP0EvidenceError(f"required YAML file missing: {path}") from exc
    if not isinstance(payload, dict):
        raise QualificationP0EvidenceError(f"YAML object required: {path}")
    return payload


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise QualificationP0EvidenceError(f"required text file missing: {path}") from exc


def catalog_by_id(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for item in catalog.get("criteria") or []:
        if isinstance(item, dict) and item.get("criterion_id"):
            entries[str(item["criterion_id"])] = item
    return entries


def repo_relative_path(root: Path, path_text: str) -> Path:
    normalized = path_text.replace("\\", "/")
    path = PurePosixPath(normalized)
    if normalized.startswith(("/", "\\")) or ":" in normalized or ".." in path.parts:
        raise QualificationP0EvidenceError(f"path must be repo-relative: {path_text}")
    absolute = (root / Path(*path.parts)).resolve()
    try:
        absolute.relative_to(root.resolve())
    except ValueError as exc:
        raise QualificationP0EvidenceError(f"path escapes repo: {path_text}") from exc
    return absolute


def require_file(root: Path, path_text: str, errors: list[str]) -> Path | None:
    try:
        path = repo_relative_path(root, path_text)
    except QualificationP0EvidenceError as exc:
        errors.append(str(exc))
        return None
    if not path.exists():
        errors.append(f"referenced evidence path missing: {path_text}")
        return None
    return path


def validate_catalog_rows(catalog: dict[str, Any], errors: list[str]) -> None:
    catalog_entries = catalog_by_id(catalog)
    for criterion_id in AUTO_EVIDENCE_IDS:
        row = catalog_entries.get(criterion_id)
        if row is None:
            errors.append(f"criterion catalog missing {criterion_id}")
            continue
        if row.get("gate_id") != "P0":
            errors.append(f"{criterion_id} must remain a P0 criterion")
        if row.get("requirement_class") != "INVARIANT":
            errors.append(f"{criterion_id} must remain an INVARIANT criterion")


def validate_artifact(
    root: Path,
    artifact: dict[str, Any],
    catalog: dict[str, Any],
    errors: list[str],
) -> None:
    if artifact.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        errors.append(f"artifact schema_version must be {EXPECTED_SCHEMA_VERSION}")
    if artifact.get("effective_gate_status") != "BLOCKED":
        errors.append("artifact effective_gate_status must remain BLOCKED")
    if artifact.get("result_claimed") is not False:
        errors.append("artifact must not claim a qualification result")
    if artifact.get("status_reference") != "state/EMPIRICAL_QUALIFICATION_STATUS.yaml":
        errors.append("artifact status_reference must point to the committed status file")

    rows = artifact.get("criteria")
    if not isinstance(rows, list):
        errors.append("artifact criteria must be a list")
        return
    ids = [row.get("criterion_id") for row in rows if isinstance(row, dict)]
    if ids != list(AUTO_EVIDENCE_IDS):
        errors.append(f"artifact criteria must be exactly {list(AUTO_EVIDENCE_IDS)}")

    catalog_entries = catalog_by_id(catalog)
    for row in rows:
        if not isinstance(row, dict):
            errors.append("artifact criteria rows must be mappings")
            continue
        criterion_id = str(row.get("criterion_id"))
        catalog_row = catalog_entries.get(criterion_id)
        if catalog_row is None:
            errors.append(f"artifact references unknown criterion {criterion_id}")
            continue
        if row.get("catalog_gate_id") != "P0":
            errors.append(f"{criterion_id} catalog_gate_id must be P0")
        if row.get("catalog_requirement_class") != "INVARIANT":
            errors.append(f"{criterion_id} catalog_requirement_class must be INVARIANT")
        if row.get("catalog_statement") != catalog_row.get("statement"):
            errors.append(f"{criterion_id} catalog_statement drifted from catalog")
        if row.get("evidence_status") != "auto_evidenced_still_target_blocked":
            errors.append(f"{criterion_id} evidence_status must be blocked auto-evidence")
        if row.get("effective_status") != "BLOCKED":
            errors.append(f"{criterion_id} effective_status must remain BLOCKED")
        if row.get("pass_claimed") is not False:
            errors.append(f"{criterion_id} must not claim PASS")

        caveats = row.get("caveats")
        if not isinstance(caveats, list) or not caveats:
            errors.append(f"{criterion_id} caveats must be a non-empty list")
        elif "still target-blocked" not in " ".join(str(value) for value in caveats):
            errors.append(f"{criterion_id} caveats must state it is still target-blocked")

        evidence = row.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{criterion_id} evidence must be a non-empty list")
            continue
        for record in evidence:
            if not isinstance(record, dict):
                errors.append(f"{criterion_id} evidence records must be mappings")
                continue
            path_text = str(record.get("path") or "")
            signal = str(record.get("signal") or "").strip()
            if not path_text:
                errors.append(f"{criterion_id} evidence record missing path")
            else:
                require_file(root, path_text, errors)
            if not signal:
                errors.append(f"{criterion_id} evidence record missing signal")


def validate_status_link(root: Path, status: dict[str, Any], errors: list[str]) -> None:
    p0 = (status.get("qualifications") or {}).get("p0")
    if not isinstance(p0, dict):
        errors.append("status missing qualifications.p0")
        return
    if p0.get("status") != "BLOCKED":
        errors.append("qualifications.p0.status must remain BLOCKED")
    if p0.get("result_path") is not None:
        errors.append("qualifications.p0.result_path must remain null")
    references = p0.get("blocker_references")
    if not isinstance(references, list):
        errors.append("qualifications.p0.blocker_references must be a list")
        return
    if ARTIFACT_RELATIVE_PATH not in references:
        errors.append(f"qualifications.p0.blocker_references must include {ARTIFACT_RELATIVE_PATH}")
    require_file(root, ARTIFACT_RELATIVE_PATH, errors)


def validate_no_pass_status(status: dict[str, Any], errors: list[str]) -> None:
    for section in ("qualifications", "overlays", "conditional_overlays"):
        records = status.get(section) or {}
        if not isinstance(records, dict):
            errors.append(f"status section must be a mapping: {section}")
            continue
        for name, record in records.items():
            if isinstance(record, dict) and record.get("status") == "PASS":
                errors.append(f"{section}.{name} must not be PASS")


def validate_backlog(backlog_text: str, errors: list[str]) -> None:
    if "Status: `P0 = BLOCKED`" not in backlog_text:
        errors.append("backlog must keep P0 = BLOCKED")
    if "No AOI selection, source approval, fixture capture" not in backlog_text:
        errors.append("backlog must preserve no-AOI/no-fixture authorization boundary")
    for criterion_id in AUTO_EVIDENCE_IDS:
        expected = f"`{criterion_id}` | {BACKLOG_STATUS_PHRASE}"
        if expected not in backlog_text:
            errors.append(f"backlog missing {criterion_id} {BACKLOG_STATUS_PHRASE} row")


def require_text_fragments(
    root: Path,
    path_text: str,
    fragments: tuple[str, ...],
    errors: list[str],
) -> None:
    path = require_file(root, path_text, errors)
    if path is None:
        return
    text = read_text(path)
    for fragment in fragments:
        if fragment not in text:
            errors.append(f"{path_text} missing expected fragment: {fragment}")


def iter_python_tests(root: Path) -> list[Path]:
    paths: list[Path] = []
    for base_text in ("backend/tests", "tests"):
        base = root / base_text
        if base.exists():
            paths.extend(sorted(base.rglob("*.py")))
    return paths


def validate_repo_controls(root: Path, errors: list[str]) -> None:
    ci_text = read_text(root / ".github" / "workflows" / "ci.yml")
    if "continue-on-error" in ci_text:
        errors.append("CI workflow must not suppress qualification failures with continue-on-error")

    for path in iter_python_tests(root):
        text = path.read_text(encoding="utf-8")
        matched = [token for token in SUPPRESSION_TOKENS if token in text]
        if matched:
            relative = path.relative_to(root).as_posix()
            errors.append(f"pytest xfail suppression found in {relative}: {matched[0]}")

    for path_text in (
        "scripts/validate_qualification.py",
        "scripts/selftest_qualification_validator.py",
        "scripts/qualification_status_check.py",
        "scripts/qualification_change_impact_check.py",
        "scripts/verify.ps1",
        "scripts/verify.sh",
    ):
        require_file(root, path_text, errors)

    require_text_fragments(
        root,
        "docs/connectors/connector_runbook.md",
        ("fixture-only utility coverage", "does not imply live county coverage"),
        errors,
    )
    require_text_fragments(
        root,
        "tests/fixtures/golden_aois/manifest.yaml",
        ("Fixture-only", "forbidden_claims"),
        errors,
    )
    require_text_fragments(
        root,
        "config/qualification/qualification_targets.yaml",
        ("status: DRAFT", "acceptance_case_storage: external_restricted_vault"),
        errors,
    )
    require_text_fragments(
        root,
        "config/qualification/change_impact_matrix.yaml",
        ("config/qualification/qualification_targets.yaml", "scripts/qualification_*.py"),
        errors,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate repo-local evidence records for blocked P0 invariants.",
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--status", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--backlog", type=Path)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    artifact_path = args.artifact or root / ARTIFACT_RELATIVE_PATH
    status_path = args.status or root / "state" / "EMPIRICAL_QUALIFICATION_STATUS.yaml"
    catalog_path = args.catalog or root / "config" / "qualification" / "criterion_catalog.yaml"
    backlog_path = args.backlog or root / BACKLOG_RELATIVE_PATH

    try:
        artifact = load_yaml(artifact_path.resolve())
        status = load_yaml(status_path.resolve())
        catalog = load_yaml(catalog_path.resolve())
        backlog_text = read_text(backlog_path.resolve())
        errors: list[str] = []
        validate_catalog_rows(catalog, errors)
        validate_artifact(root, artifact, catalog, errors)
        validate_status_link(root, status, errors)
        validate_no_pass_status(status, errors)
        validate_backlog(backlog_text, errors)
        validate_repo_controls(root, errors)
    except QualificationP0EvidenceError as exc:
        print(f"FAIL: {exc}")
        print("qualification P0 auto evidence check: FAIL")
        return 1

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("qualification P0 auto evidence check: FAIL")
        return 1

    print(f"P0 auto evidence criteria: {', '.join(AUTO_EVIDENCE_IDS)}")
    print("evidence status: auto_evidenced_still_target_blocked")
    print("effective P0 status: BLOCKED")
    print("qualification P0 auto evidence check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
