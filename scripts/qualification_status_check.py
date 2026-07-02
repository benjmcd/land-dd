#!/usr/bin/env python3
"""Derive and verify the committed empirical qualification status."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

try:
    import yaml
except ImportError as exc:
    raise SystemExit("Missing dev dependency. Install PyYAML before running status checks.") from exc

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_qualification import (  # noqa: E402
    GATE_TO_STATUS_KEY,
    NONBLOCKING_CLASS,
    get_path,
    unresolved,
)
from qualification_checker_advertisement import (  # noqa: E402
    ADVERTISEMENT_FLAG,
    SCHEMA_VERSION as ADVERTISEMENT_SCHEMA_VERSION,
)

ALLOWED_DERIVED_STATUSES = {"BLOCKED", "NOT_RUN"}
KNOWN_MISSING_RUNTIME = {
    "scripts/package_manifest_check.py": (
        "usage: package_manifest_check.py",
        "manifest",
    ),
    "scripts/spatial_query_plan_runtime_check.py": (
        "missing required --db-url",
        "database_url_sync",
    ),
}
RUNTIME_ENV_KEYS = {
    "scripts/spatial_query_plan_runtime_check.py": ("DATABASE_URL", "DATABASE_URL_SYNC"),
}


class QualificationStatusError(RuntimeError):
    """Raised when status cannot be derived safely."""


class CheckerResult(NamedTuple):
    path: str
    returncode: int
    stdout: str
    stderr: str
    advertised_criterion_ids: tuple[str, ...] = ()


StatusKey = tuple[str, str]
REQUIRED_CANDIDATE_FIELDS = (
    "commit",
    "artifact_digest",
    "protocol_version",
    "targets_version",
    "vocabulary_version",
    "criteria_catalog_digest",
)
REQUIRED_SCOPE_VERSION_FIELDS = (
    "report_contract_version",
    "api_contract_version",
    "normalization_schema_version",
    "geometry_pipeline_version",
    "source_snapshot_policy",
    "data_as_of_policy",
)


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QualificationStatusError(f"YAML object required: {path}")
    return payload


def load_profile_map(directory: Path, id_field: str) -> dict[str, dict[str, Any]]:
    if not directory.exists() or not directory.is_dir():
        raise QualificationStatusError(f"profile directory does not exist: {directory}")
    profiles: dict[str, dict[str, Any]] = {}
    for path in sorted([*directory.glob("*.yaml"), *directory.glob("*.yml")]):
        profile = load_yaml(path)
        profile_id = profile.get(id_field)
        if not isinstance(profile_id, str) or not profile_id.strip():
            raise QualificationStatusError(f"profile missing {id_field}: {path}")
        if profile_id in profiles:
            raise QualificationStatusError(f"duplicate profile {id_field}: {profile_id}")
        profiles[profile_id] = profile
    return profiles


def unique_checker_paths(crosswalk: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for entry in crosswalk.get("entries") or []:
        for path in entry.get("checker_paths") or []:
            if path not in paths:
                paths.append(path)
    return paths


def status_records(status: dict[str, Any]) -> dict[StatusKey, dict[str, Any]]:
    records: dict[StatusKey, dict[str, Any]] = {}
    for section in ("qualifications", "overlays", "conditional_overlays"):
        section_records = status.get(section) or {}
        if not isinstance(section_records, dict):
            raise QualificationStatusError(f"status section must be a mapping: {section}")
        for name, record in section_records.items():
            if not isinstance(record, dict):
                raise QualificationStatusError(f"status record must be a mapping: {section}.{name}")
            records[(section, name)] = record
    return records


def catalog_by_id(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    criteria: dict[str, dict[str, Any]] = {}
    for item in catalog.get("criteria") or []:
        if not isinstance(item, dict) or not item.get("criterion_id"):
            continue
        criteria[str(item["criterion_id"])] = item
    return criteria


def section_for_status_key(status: dict[str, Any], key: str) -> str:
    for section in ("qualifications", "overlays", "conditional_overlays"):
        if key in (status.get(section) or {}):
            return section
    raise QualificationStatusError(f"catalog gate maps to missing status key: {key}")


def criterion_status_keys(
    status: dict[str, Any],
    catalog_map: dict[str, dict[str, Any]],
    criterion_id: str,
) -> set[StatusKey]:
    contract = catalog_map.get(criterion_id)
    if contract is None:
        raise QualificationStatusError(f"crosswalk references unknown criterion: {criterion_id}")

    gate_id = contract.get("gate_id") or criterion_id.split("-", 1)[0]
    gates = list(contract.get("applicable_subgates") or []) if gate_id == "Q3" else [gate_id]
    if gate_id == "Q3" and not gates:
        gates = ["Q3A", "Q3B", "Q3C"]

    status_keys: set[StatusKey] = set()
    for gate in gates:
        key = GATE_TO_STATUS_KEY.get(str(gate), str(gate).lower())
        section = section_for_status_key(status, key)
        status_keys.add((section, key))
    return status_keys


def checker_entries_by_path(crosswalk: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    entries_by_path: dict[str, list[dict[str, Any]]] = {}
    for entry in crosswalk.get("entries") or []:
        for path in entry.get("checker_paths") or []:
            entries_by_path.setdefault(path, []).append(entry)
    return entries_by_path


def advertised_criterion_ids_for_checker(
    crosswalk: dict[str, Any],
    path_text: str,
) -> tuple[str, ...]:
    entries = checker_entries_by_path(crosswalk).get(path_text) or []
    return tuple(
        sorted(
            {
                str(criterion_id)
                for entry in entries
                for criterion_id in (entry.get("criterion_ids") or [])
            },
        ),
    )


def repo_relative_path(root: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        raise QualificationStatusError(f"checker path must be repo-local: {path_text}")
    absolute = (root / path).resolve()
    try:
        absolute.relative_to(root.resolve())
    except ValueError as exc:
        raise QualificationStatusError(f"checker path escapes repo: {path_text}") from exc
    if not absolute.is_file():
        raise QualificationStatusError(f"checker path does not exist: {path_text}")
    return absolute


def timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_checker(
    root: Path,
    path_text: str,
    python_command: str,
    timeout_seconds: int,
    allow_runtime_checkers: bool = False,
) -> CheckerResult:
    repo_relative_path(root, path_text)
    advertised_criterion_ids = run_checker_advertisement(
        root=root,
        path_text=path_text,
        python_command=python_command,
        timeout_seconds=timeout_seconds,
    )
    env = os.environ.copy()
    if not allow_runtime_checkers:
        for key in RUNTIME_ENV_KEYS.get(path_text, ()):
            env.pop(key, None)
    try:
        completed = subprocess.run(
            [python_command, path_text],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        return CheckerResult(
            path=path_text,
            returncode=124,
            stdout=timeout_output(exc.stdout),
            stderr=(
                timeout_output(exc.stderr)
                + f"\nchecker timed out after {timeout_seconds}s"
            ),
            advertised_criterion_ids=advertised_criterion_ids,
        )
    return CheckerResult(
        path=path_text,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        advertised_criterion_ids=advertised_criterion_ids,
    )


def run_checker_advertisement(
    root: Path,
    path_text: str,
    python_command: str,
    timeout_seconds: int,
) -> tuple[str, ...]:
    repo_relative_path(root, path_text)
    try:
        completed = subprocess.run(
            [python_command, path_text, ADVERTISEMENT_FLAG],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise QualificationStatusError(
            f"checker criterion advertisement timed out: {path_text}: "
            f"{timeout_output(exc.stdout)} {timeout_output(exc.stderr)}",
        ) from exc
    if completed.returncode != 0:
        raise QualificationStatusError(
            f"checker criterion advertisement failed: {path_text}: "
            f"{completed.stdout} {completed.stderr}",
        )
    try:
        payload = yaml.safe_load(completed.stdout)
    except yaml.YAMLError as exc:
        raise QualificationStatusError(
            f"checker criterion advertisement is not valid JSON/YAML: {path_text}",
        ) from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != ADVERTISEMENT_SCHEMA_VERSION:
        raise QualificationStatusError(f"checker criterion advertisement schema mismatch: {path_text}")
    if payload.get("checker_path") != path_text:
        raise QualificationStatusError(f"checker criterion advertisement path mismatch: {path_text}")
    criterion_ids = payload.get("criterion_ids")
    if not isinstance(criterion_ids, list) or not all(isinstance(item, str) for item in criterion_ids):
        raise QualificationStatusError(f"checker criterion advertisement IDs invalid: {path_text}")
    if not criterion_ids:
        raise QualificationStatusError(f"checker criterion advertisement is empty: {path_text}")
    return tuple(sorted(set(criterion_ids)))


def run_checker_inventory(
    root: Path,
    crosswalk: dict[str, Any],
    python_command: str,
    timeout_seconds: int,
    allow_runtime_checkers: bool = False,
) -> dict[str, CheckerResult]:
    results: dict[str, CheckerResult] = {}
    for path in unique_checker_paths(crosswalk):
        results[path] = run_checker(
            root,
            path,
            python_command,
            timeout_seconds,
            allow_runtime_checkers=allow_runtime_checkers,
        )
    return results


def checker_is_known_not_run(result: CheckerResult) -> bool:
    expected = KNOWN_MISSING_RUNTIME.get(result.path)
    if expected is None or result.returncode == 0:
        return False
    output = f"{result.stdout}\n{result.stderr}".lower()
    return all(fragment.lower() in output for fragment in expected)


def target_or_candidate_unresolved(status: dict[str, Any], targets: dict[str, Any]) -> bool:
    if targets.get("status") != "FROZEN":
        return True
    candidate = status.get("candidate") or {}
    return any(not candidate.get(field) for field in REQUIRED_CANDIDATE_FIELDS)


def domain_or_source_profile_unresolved(
    targets: dict[str, Any],
    domain_profiles: dict[str, dict[str, Any]] | None,
    source_profiles: dict[str, dict[str, Any]] | None,
) -> bool:
    scope = targets.get("scope") or {}
    required_domains = set(scope.get("qualified_domains") or [])
    required_sources = set(scope.get("source_profile_ids") or [])

    if required_domains and domain_profiles is not None:
        missing_domains = required_domains - set(domain_profiles)
        if missing_domains and "domain_profile_template" in domain_profiles:
            return True
        for domain_id in required_domains:
            if domain_profiles.get(domain_id, {}).get("status") != "FROZEN":
                return True

    if not required_sources:
        return True
    if source_profiles is not None:
        for source_id in required_sources:
            if source_profiles.get(source_id, {}).get("status") != "APPROVED":
                return True
    return False


def scope_versioning_unresolved(targets: dict[str, Any]) -> bool:
    scope = targets.get("scope") or {}
    if any(unresolved(scope.get(field)) for field in REQUIRED_SCOPE_VERSION_FIELDS):
        return True
    return bool(unresolved(scope.get("ruleset_versions")))


def target_bindings_unresolved(targets: dict[str, Any]) -> bool:
    bindings = targets.get("criterion_bindings") or {}
    if not isinstance(bindings, dict):
        return True
    for criterion_id, binding in bindings.items():
        if not isinstance(binding, dict):
            raise QualificationStatusError(f"target binding must be a mapping: {criterion_id}")
        if binding.get("status") != "FROZEN":
            return True
        for reference in binding.get("references") or []:
            exists, value = get_path(targets, str(reference))
            if not exists or unresolved(value):
                return True
    return False


def catalog_parameterization_unresolved(catalog: dict[str, Any]) -> bool:
    for contract in catalog.get("criteria") or []:
        if not isinstance(contract, dict):
            continue
        if contract.get("requirement_class") == NONBLOCKING_CLASS:
            continue
        if contract.get("parameterization_status") != "FROZEN":
            return True
    return False


def rubrics_unresolved(rubrics: dict[str, Any] | None) -> bool:
    if rubrics is None:
        return False
    if rubrics.get("status") != "FROZEN":
        return True
    for criterion_id, rubric in (rubrics.get("criteria") or {}).items():
        if not isinstance(rubric, dict):
            raise QualificationStatusError(f"rubric must be a mapping: {criterion_id}")
        if rubric.get("status") != "FROZEN":
            return True
    return False


def p0_parameterization_unresolved(
    status: dict[str, Any],
    targets: dict[str, Any],
    catalog: dict[str, Any],
    rubrics: dict[str, Any] | None,
    domain_profiles: dict[str, dict[str, Any]] | None,
    source_profiles: dict[str, dict[str, Any]] | None,
) -> bool:
    return any(
        (
            target_or_candidate_unresolved(status, targets),
            domain_or_source_profile_unresolved(targets, domain_profiles, source_profiles),
            scope_versioning_unresolved(targets),
            target_bindings_unresolved(targets),
            catalog_parameterization_unresolved(catalog),
            rubrics_unresolved(rubrics),
        )
    )


def derive_statuses(
    root: Path,
    status: dict[str, Any],
    targets: dict[str, Any],
    catalog: dict[str, Any],
    crosswalk: dict[str, Any],
    checker_results: dict[str, CheckerResult],
    rubrics: dict[str, Any] | None = None,
    domain_profiles: dict[str, dict[str, Any]] | None = None,
    source_profiles: dict[str, dict[str, Any]] | None = None,
) -> dict[StatusKey, str]:
    root = root.resolve()
    records = status_records(status)
    derived = {key: "NOT_RUN" for key in records}
    if ("qualifications", "p0") not in derived:
        raise QualificationStatusError("status is missing qualifications.p0")
    if p0_parameterization_unresolved(
        status,
        targets,
        catalog,
        rubrics,
        domain_profiles,
        source_profiles,
    ):
        derived[("qualifications", "p0")] = "BLOCKED"

    catalog_map = catalog_by_id(catalog)
    for path in unique_checker_paths(crosswalk):
        result = checker_results.get(path)
        if result is None:
            raise QualificationStatusError(f"missing checker result: {path}")
        repo_relative_path(root, path)
        if not result.advertised_criterion_ids:
            raise QualificationStatusError(f"missing checker criterion advertisement: {path}")
        if result.returncode == 0 or checker_is_known_not_run(result):
            continue
        for criterion_id in result.advertised_criterion_ids:
            for status_key in criterion_status_keys(status, catalog_map, criterion_id):
                derived[status_key] = "BLOCKED"
    return derived


def compare_committed_statuses(
    status: dict[str, Any],
    derived: dict[StatusKey, str],
) -> list[str]:
    errors: list[str] = []
    records = status_records(status)
    missing = sorted(set(records) - set(derived))
    if missing:
        for section, name in missing:
            errors.append(f"{section}.{name} missing from derived status view")

    for key, expected in sorted(derived.items()):
        if expected not in ALLOWED_DERIVED_STATUSES:
            errors.append(f"{key[0]}.{key[1]} derived illegal status {expected}")
            continue
        record = records.get(key)
        if record is None:
            errors.append(f"{key[0]}.{key[1]} missing from committed status")
            continue
        actual = record.get("status")
        if actual not in ALLOWED_DERIVED_STATUSES:
            errors.append(f"{key[0]}.{key[1]} has unsupported committed status {actual}")
            continue
        if actual != expected:
            errors.append(f"{key[0]}.{key[1]} expected {expected} but found {actual}")
    return errors


def checker_summary(results: dict[str, CheckerResult]) -> tuple[int, int, int]:
    passed = sum(1 for result in results.values() if result.returncode == 0)
    not_run = sum(1 for result in results.values() if checker_is_known_not_run(result))
    unexpected_failed = len(results) - passed - not_run
    return passed, not_run, unexpected_failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify committed qualification status against derived checker state.",
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--status", type=Path)
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--crosswalk", type=Path)
    parser.add_argument("--rubrics", type=Path)
    parser.add_argument("--domain-profiles-dir", type=Path)
    parser.add_argument("--source-profiles-dir", type=Path)
    parser.add_argument(
        "--python-command",
        default=os.environ.get("LAND_DD_PYTHON_EXECUTABLE") or sys.executable,
    )
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument(
        "--allow-runtime-checkers",
        action="store_true",
        help=(
            "Allow mapped checkers to see ambient runtime env such as DB URLs. "
            "Default keeps runtime-required checks in NOT_RUN mode."
        ),
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    status_path = args.status or root / "state" / "EMPIRICAL_QUALIFICATION_STATUS.yaml"
    targets_path = args.targets or root / "config" / "qualification" / "qualification_targets.yaml"
    catalog_path = args.catalog or root / "config" / "qualification" / "criterion_catalog.yaml"
    crosswalk_path = args.crosswalk or root / "config" / "qualification" / "readiness_crosswalk.yaml"
    rubrics_path = args.rubrics or root / "config" / "qualification" / "judgment_rubrics.yaml"
    domain_profiles_dir = (
        args.domain_profiles_dir or root / "config" / "qualification" / "domain_profiles"
    )
    source_profiles_dir = (
        args.source_profiles_dir or root / "config" / "qualification" / "source_profiles"
    )

    try:
        status = load_yaml(status_path.resolve())
        targets = load_yaml(targets_path.resolve())
        catalog = load_yaml(catalog_path.resolve())
        crosswalk = load_yaml(crosswalk_path.resolve())
        rubrics = load_yaml(rubrics_path.resolve())
        domain_profiles = load_profile_map(domain_profiles_dir.resolve(), "domain_id")
        source_profiles = load_profile_map(source_profiles_dir.resolve(), "source_id")
        checker_results = run_checker_inventory(
            root=root,
            crosswalk=crosswalk,
            python_command=args.python_command,
            timeout_seconds=args.timeout_seconds,
            allow_runtime_checkers=args.allow_runtime_checkers,
        )
        derived = derive_statuses(
            root=root,
            status=status,
            targets=targets,
            catalog=catalog,
            crosswalk=crosswalk,
            checker_results=checker_results,
            rubrics=rubrics,
            domain_profiles=domain_profiles,
            source_profiles=source_profiles,
        )
        errors = compare_committed_statuses(status, derived)
    except QualificationStatusError as exc:
        print(f"FAIL: {exc}")
        print("qualification status check: FAIL")
        return 1

    passed, not_run, unexpected_failed = checker_summary(checker_results)
    print(
        "qualification status checker results: "
        f"passed={passed} not_run={not_run} unexpected_failed={unexpected_failed}"
    )
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("qualification status check: FAIL")
        return 1

    blocked = sum(1 for value in derived.values() if value == "BLOCKED")
    not_run_statuses = sum(1 for value in derived.values() if value == "NOT_RUN")
    print(
        "derived qualification statuses: "
        f"BLOCKED={blocked} NOT_RUN={not_run_statuses}"
    )
    print("qualification status check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
