#!/usr/bin/env python3
r"""Validate empirical-qualification v3 control files.

The validator distinguishes structural validity from qualification readiness:

- A DRAFT configuration may validate structurally.
- P0 or a higher qualification cannot PASS while an applicable target,
  criterion contract, rubric, result, prerequisite, or evidence record is unresolved.

Windows usage:
    python .\scripts\validate_qualification.py --root .\docs\qualification ^
        --targets .\config\qualification_targets.yaml ^
        --status .\state\EMPIRICAL_QUALIFICATION_STATUS.yaml

PowerShell uses backticks rather than carets for line continuation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit(
        "Missing dev dependency. Install PyYAML and jsonschema before running qualification validation."
    ) from exc


GATE_STATUSES = {"NOT_RUN", "RUNNING", "BLOCKED", "FAIL", "PASS", "INVALIDATED", "EXPIRED"}
CRITERION_RESULTS = {"PASS", "FAIL", "BLOCKED", "N/A"}
NONBLOCKING_CLASS = "DIAGNOSTIC"
ADVERTISEMENT_FLAG = "--qualification-criteria-json"
ADVERTISEMENT_SCHEMA_VERSION = "qualification_checker_advertisement_v1"

GATE_TO_STATUS_KEY = {
    "P0": "p0",
    "Q1": "q1",
    "Q2": "q2",
    "Q3A": "q3a",
    "Q3B": "q3b",
    "Q3C": "q3c",
    "DQ": "data_quality",
    "IR": "input_resolution",
    "DB": "database",
    "S": "security_privacy_compliance",
    "A": "accessibility_human_factors",
    "M": "maintainability_modularity",
    "O": "hosted_operations",
    "E": "economics",
    "G": "governance_release",
    "R": "regulatory_professional_scope",
    "F": "field_surveillance",
    "W": "windows_native",
    "CG": "candidate_generation",
    "FIN": "financial_modeling",
    "AI": "ai_llm",
}
STATUS_KEY_TO_GATE = {value: key for key, value in GATE_TO_STATUS_KEY.items()}

CLASSIFICATION_REQUIRED_GATES = {
    "L9-R": set(),
    "L9-P": {"P0"},
    "L9-E1": {"P0", "Q1", "DQ", "IR", "DB", "S", "M", "R", "G"},
    "L9-E2": {"P0", "Q1", "Q2", "DQ", "IR", "DB", "S", "A", "M", "R", "G"},
    "L10-BP-LOCAL": {
        "P0", "Q1", "Q2", "DQ", "IR", "DB", "S", "A", "M", "O", "R", "F", "G"
    },
    "L10-BP-ST": {
        "P0", "Q1", "Q2", "DQ", "IR", "DB", "S", "A", "M", "O", "R", "F", "G"
    },
    "L10-BP-MT": {
        "P0", "Q1", "Q2", "DQ", "IR", "DB", "S", "A", "M", "O", "R", "F", "G"
    },
    "X-US": {
        "P0", "Q1", "Q2", "DQ", "IR", "DB", "S", "A", "M", "R", "G", "Q3A", "Q3B"
    },
    "X-GLOBAL-ARCH": {
        "P0", "Q1", "Q2", "DQ", "IR", "DB", "S", "A", "M", "R", "G",
        "Q3A", "Q3B", "Q3C"
    },
}

REQUIRED_READINESS_CONFIG_GLOBS = {
    "config/*readiness*.yaml",
    "config/*authority*.yaml",
    "config/*entitlement*.yaml",
    "config/bologna_*.yaml",
}
REQUIRED_READINESS_CHECKER_GLOBS = {
    "scripts/*readiness*_check.py",
    "scripts/*authority*_check.py",
    "scripts/*entitlement*_check.py",
    "scripts/bologna_*_check.py",
}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def validate_json_schema(
    instance: Any,
    schema_path: Path,
    label: str,
    errors: list[str],
) -> None:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for issue in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        where = ".".join(str(part) for part in issue.path) or "<root>"
        errors.append(f"{label}: {where}: {issue.message}")


def framework_ids(framework_path: Path) -> set[str]:
    text = framework_path.read_text(encoding="utf-8")
    return set(re.findall(r"`([A-Z][A-Z0-9]*-\d{3})`", text))


def get_path(value: Any, dotted_path: str) -> tuple[bool, Any]:
    current = value
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current


def unresolved(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip().upper() in {"TBD", "TODO", "UNKNOWN"}
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0 or any(unresolved(item) for item in value)
    if isinstance(value, dict):
        return len(value) == 0 or any(unresolved(item) for item in value.values())
    return False


def resolve_local_reference(root: Path, reference: str | None) -> Path | None:
    if not reference:
        return None
    if "://" in reference:
        return None
    path_text = reference.split("#", 1)[0]
    if not path_text:
        return None
    candidate = Path(path_text)
    return candidate if candidate.is_absolute() else (root / candidate).resolve()


def parse_datetime_utc(
    value: Any,
    label: str,
    errors: list[str],
) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append(f"{label}: expires_at must be a date-time string")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label}: invalid date-time {value!r}")
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def validate_unexpired_pass(
    expires_at: str | None,
    label: str,
    now_utc: datetime,
    errors: list[str],
) -> None:
    expires = parse_datetime_utc(expires_at, f"{label}.expires_at", errors)
    if expires is None:
        errors.append(f"{label}: PASS has no expires_at")
        return
    if expires <= now_utc:
        errors.append(f"{label}: expired PASS at {expires_at}")


def validate_evidence_reference(
    root: Path,
    label: str,
    reference: str | None,
    errors: list[str],
) -> None:
    if not isinstance(reference, str) or not reference.strip():
        errors.append(f"{label}: criterion evidence reference is empty")
        return
    if "://" in reference:
        errors.append(f"{label}: criterion evidence must be repo-local: {reference}")
        return
    evidence_path = resolve_local_reference(root, reference)
    if evidence_path is None:
        return
    try:
        evidence_path.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label}: criterion evidence escapes repo: {reference}")
        return
    if not evidence_path.exists():
        errors.append(f"{label}: criterion evidence does not exist: {reference}")


def inherited_profile(
    profiles: dict[str, Any],
    name: str,
    errors: list[str],
    stack: tuple[str, ...] = (),
) -> dict[str, Any]:
    if name in stack:
        errors.append(f"profiles: inheritance cycle: {' -> '.join((*stack, name))}")
        return {}
    item = profiles.get("profiles", {}).get(name)
    if item is None:
        errors.append(f"profiles: unknown profile {name!r}")
        return {}

    merged: dict[str, Any] = {
        "required_gates": set(),
        "conditional_gates": {},
        "mandatory_criteria": set(),
    }
    parent = item.get("inherits")
    if parent:
        parent_item = inherited_profile(profiles, parent, errors, (*stack, name))
        merged["required_gates"] |= set(parent_item.get("required_gates", set()))
        merged["conditional_gates"].update(parent_item.get("conditional_gates", {}))
        merged["mandatory_criteria"] |= set(parent_item.get("mandatory_criteria", set()))

    merged["required_gates"] |= set(item.get("required_gates", []))
    merged["conditional_gates"].update(item.get("conditional_gates", {}))
    merged["mandatory_criteria"] |= set(item.get("mandatory_criteria", []))
    merged["deployment_profile"] = item.get("deployment_profile", merged.get("deployment_profile"))
    return merged


def conditional_gate_enabled(gate: str, targets: dict[str, Any]) -> bool:
    scope = targets.get("scope", {})
    mapping = {
        "W": bool(scope.get("windows_native_required")),
        "E": bool(scope.get("commercial_profile_enabled")),
        "CG": bool(scope.get("candidate_generation_enabled")),
        "FIN": bool(scope.get("financial_modeling_enabled")),
        "AI": bool(scope.get("ai_llm_enabled_for_decision_relevant_output")),
        "Q2": bool(scope.get("user_utility_claim_enabled")),
        "A": bool(scope.get("user_facing_workflow_enabled")),
    }
    return mapping.get(gate, True)


def selected_profile_gates(
    profiles: dict[str, Any],
    targets: dict[str, Any],
    errors: list[str],
) -> set[str]:
    name = targets.get("scope", {}).get("product_scope_profile")
    merged = inherited_profile(profiles, name, errors)
    required = set(merged.get("required_gates", set()))
    for gate in merged.get("conditional_gates", {}):
        if conditional_gate_enabled(gate, targets):
            required.add(gate)
    return required


def criterion_is_applicable(
    contract: dict[str, Any],
    targets: dict[str, Any],
    result_gate: str | None = None,
) -> bool:
    gate = contract.get("gate_id")
    scope = targets.get("scope", {})

    if gate == "W":
        return bool(scope.get("windows_native_required"))
    if gate == "CG":
        return bool(scope.get("candidate_generation_enabled"))
    if gate == "FIN":
        return bool(scope.get("financial_modeling_enabled"))
    if gate == "AI":
        return bool(scope.get("ai_llm_enabled_for_decision_relevant_output"))
    if gate == "E":
        return bool(scope.get("commercial_profile_enabled"))
    if gate == "Q2":
        return bool(scope.get("user_utility_claim_enabled"))
    if gate == "A":
        return bool(scope.get("user_facing_workflow_enabled"))

    cid = contract.get("criterion_id")
    if cid in {"DQ-021", "DQ-022"}:
        return bool(targets.get("document_extraction", {}).get("enabled"))
    if cid == "DQ-023":
        # Conservative: map/tile use may exist in any land-intelligence product.
        return True
    if cid in {"S-004", "DB-011"}:
        return scope.get("deployment_profile") == "PUBLIC_MULTI_TENANT_SAAS"
    if cid in {"S-025", "R-006"}:
        return bool(scope.get("international_operation_enabled"))
    if cid == "A-011":
        return "exported_report" in set(scope.get("output_channels", []))
    if cid == "CG-016":
        return bool(scope.get("candidate_generation_enabled"))
    if gate == "Q3" and result_gate:
        return result_gate in set(contract.get("applicable_subgates", []))
    return True


def validate_profiles(
    profiles: dict[str, Any],
    known_criteria: set[str],
    errors: list[str],
) -> None:
    profile_names = set(profiles.get("profiles", {}))
    deployment_names = set(profiles.get("deployment_profiles", {}))
    for name, item in profiles.get("profiles", {}).items():
        parent = item.get("inherits")
        if parent and parent not in profile_names:
            errors.append(f"profiles: {name} inherits unknown profile {parent}")
        deployment = item.get("deployment_profile")
        if deployment and deployment not in deployment_names:
            errors.append(f"profiles: {name} references unknown deployment profile {deployment}")
        unknown_criteria = sorted(set(item.get("mandatory_criteria", [])) - known_criteria)
        if unknown_criteria:
            errors.append(f"profiles: {name} references unknown criteria {unknown_criteria}")

    for name in profile_names:
        inherited_profile(profiles, name, errors)


def repo_relative_file_paths(root: Path, patterns: Iterable[str]) -> set[str]:
    root = root.resolve()
    paths: set[str] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            paths.add(path.resolve().relative_to(root).as_posix())
    return paths


def validate_repo_local_paths(
    root: Path,
    label: str,
    references: Iterable[str],
    errors: list[str],
) -> set[str]:
    root = root.resolve()
    resolved: set[str] = set()
    for reference in references:
        path = Path(reference)
        if path.is_absolute():
            errors.append(f"{label}: path must be repo-local: {reference}")
            continue
        absolute = (root / path).resolve()
        try:
            relative = absolute.relative_to(root)
        except ValueError:
            errors.append(f"{label}: path escapes repo: {reference}")
            continue
        if not absolute.exists():
            errors.append(f"{label}: path does not exist: {reference}")
            continue
        if not absolute.is_file():
            errors.append(f"{label}: path is not a file: {reference}")
            continue
        resolved.add(relative.as_posix())
    return resolved


def validate_criterion_references(
    label: str,
    criterion_ids: Iterable[str],
    known_criteria: set[str],
    errors: list[str],
) -> None:
    unknown = sorted(set(criterion_ids) - known_criteria)
    if unknown:
        errors.append(f"{label}: unknown criterion IDs: {unknown}")


def validate_change_impact_matrix(
    change_matrix: dict[str, Any],
    known_criteria: set[str],
    errors: list[str],
) -> None:
    for change_class, entry in sorted((change_matrix.get("change_classes") or {}).items()):
        validate_criterion_references(
            f"change_impact_matrix.{change_class}.invalidate_by_default",
            entry.get("invalidate_by_default") or [],
            known_criteria,
            errors,
        )


def validate_readiness_crosswalk(
    root: Path,
    crosswalk: dict[str, Any],
    schema_path: Path,
    known_criteria: set[str],
    errors: list[str],
) -> None:
    validate_json_schema(crosswalk, schema_path, "readiness_crosswalk", errors)

    entries = crosswalk.get("entries") or []
    surface_ids = [entry.get("surface_id") for entry in entries]
    duplicates = sorted(
        {
            surface_id
            for surface_id in surface_ids
            if surface_ids.count(surface_id) > 1
        }
    )
    if duplicates:
        errors.append(f"readiness_crosswalk: duplicate surface IDs: {duplicates}")

    inventory = crosswalk.get("inventory") or {}
    missing_config_globs = sorted(
        REQUIRED_READINESS_CONFIG_GLOBS - set(inventory.get("config_globs") or [])
    )
    if missing_config_globs:
        errors.append(
            f"readiness_crosswalk: missing required config globs: {missing_config_globs}"
        )
    missing_checker_globs = sorted(
        REQUIRED_READINESS_CHECKER_GLOBS - set(inventory.get("checker_globs") or [])
    )
    if missing_checker_globs:
        errors.append(
            f"readiness_crosswalk: missing required checker globs: {missing_checker_globs}"
        )

    expected_configs = repo_relative_file_paths(
        root, inventory.get("config_globs") or []
    )
    expected_checkers = repo_relative_file_paths(
        root, inventory.get("checker_globs") or []
    )
    excluded = set(inventory.get("intentional_exclusions") or [])
    declared_configs: set[str] = set()
    declared_checkers: set[str] = set()

    for entry in entries:
        label = f"readiness_crosswalk.{entry.get('surface_id')}"
        criterion_ids = entry.get("criterion_ids") or []
        validate_criterion_references(label, criterion_ids, known_criteria, errors)
        declared_configs |= validate_repo_local_paths(
            root,
            f"{label}.config_paths",
            entry.get("config_paths") or [],
            errors,
        )
        declared_checkers |= validate_repo_local_paths(
            root,
            f"{label}.checker_paths",
            entry.get("checker_paths") or [],
            errors,
        )

    for gap in crosswalk.get("gap_groups") or []:
        validate_criterion_references(
            f"readiness_crosswalk.gap_groups.{gap.get('gap_id')}",
            gap.get("criterion_ids") or [],
            known_criteria,
            errors,
        )

    missing_configs = sorted(expected_configs - declared_configs - excluded)
    if missing_configs:
        errors.append(
            f"readiness_crosswalk: missing config inventory paths: {missing_configs}"
        )
    missing_checkers = sorted(expected_checkers - declared_checkers - excluded)
    if missing_checkers:
        errors.append(
            f"readiness_crosswalk: missing checker inventory paths: {missing_checkers}"
        )

    unused_exclusions = sorted(excluded - expected_configs - expected_checkers)
    if unused_exclusions:
        errors.append(
            f"readiness_crosswalk: intentional exclusions are not in inventory: {unused_exclusions}"
        )


def expected_checker_criteria(crosswalk: dict[str, Any]) -> dict[str, set[str]]:
    expected: dict[str, set[str]] = {}
    for entry in crosswalk.get("entries") or []:
        for checker_path in entry.get("checker_paths") or []:
            expected.setdefault(checker_path, set()).update(
                str(criterion_id) for criterion_id in (entry.get("criterion_ids") or [])
            )
    return expected


def validate_checker_advertisements(
    root: Path,
    crosswalk: dict[str, Any],
    errors: list[str],
) -> None:
    def timeout_text(value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    for checker_path, expected_ids in sorted(expected_checker_criteria(crosswalk).items()):
        try:
            completed = subprocess.run(
                [sys.executable, checker_path, ADVERTISEMENT_FLAG],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            errors.append(
                f"checker advertisement timed out: {checker_path}: "
                f"{timeout_text(exc.stdout)} {timeout_text(exc.stderr)}"
            )
            continue

        if completed.returncode != 0:
            errors.append(
                f"checker advertisement failed: {checker_path}: "
                f"{completed.stdout} {completed.stderr}"
            )
            continue
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            errors.append(f"checker advertisement invalid JSON: {checker_path}: {exc}")
            continue

        advertised_ids = payload.get("criterion_ids")
        if (
            payload.get("schema_version") != ADVERTISEMENT_SCHEMA_VERSION
            or payload.get("checker_path") != checker_path
            or not isinstance(advertised_ids, list)
            or not all(isinstance(item, str) for item in advertised_ids)
        ):
            errors.append(f"checker advertisement schema mismatch: {checker_path}")
            continue

        advertised_set = set(advertised_ids)
        if advertised_set != expected_ids:
            errors.append(
                f"checker advertisement mismatch: {checker_path}: "
                f"expected {sorted(expected_ids)} got {sorted(advertised_set)}"
            )


def validate_catalog(
    root: Path,
    catalog: dict[str, Any],
    framework_path: Path,
    catalog_schema_path: Path,
    criterion_schema_path: Path,
    vocabulary: dict[str, Any],
    targets: dict[str, Any],
    rubrics: dict[str, Any],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    validate_json_schema(catalog, catalog_schema_path, "criterion_catalog", errors)
    criteria = catalog.get("criteria") or []
    ids = [item.get("criterion_id") for item in criteria]
    duplicates = sorted({cid for cid in ids if ids.count(cid) > 1})
    if duplicates:
        errors.append(f"criterion_catalog: duplicate criterion IDs: {duplicates}")

    if catalog.get("criterion_count") != len(criteria):
        errors.append(
            f"criterion_catalog: criterion_count={catalog.get('criterion_count')} but contains {len(criteria)}"
        )

    catalog_map = {
        item["criterion_id"]: item
        for item in criteria
        if isinstance(item, dict) and item.get("criterion_id")
    }
    doc_ids = framework_ids(framework_path)
    catalog_ids = set(catalog_map)
    if doc_ids - catalog_ids:
        errors.append(f"criterion_catalog: missing framework IDs: {sorted(doc_ids - catalog_ids)}")
    if catalog_ids - doc_ids:
        errors.append(f"criterion_catalog: IDs absent from framework: {sorted(catalog_ids - doc_ids)}")
    if catalog.get("framework_sha256") != sha256_file(framework_path):
        errors.append("criterion_catalog: framework digest mismatch")

    criterion_schema = load_json(criterion_schema_path)
    criterion_validator = Draft202012Validator(
        criterion_schema, format_checker=FormatChecker()
    )
    vocabulary_terms = set((vocabulary.get("terms") or {}).keys())
    target_bindings = targets.get("criterion_bindings", {})
    rubric_entries = rubrics.get("criteria", {})

    for cid, contract in catalog_map.items():
        for issue in sorted(
            criterion_validator.iter_errors(contract), key=lambda item: list(item.path)
        ):
            where = ".".join(str(part) for part in issue.path) or "<root>"
            errors.append(f"criterion_catalog: {cid}.{where}: {issue.message}")

        if contract.get("gate_id") != cid.split("-", 1)[0]:
            errors.append(f"criterion_catalog: {cid} gate_id mismatch")
        controlled = set(contract.get("controlled_terms") or [])
        undefined = sorted(controlled - vocabulary_terms)
        if undefined:
            errors.append(f"criterion_catalog: {cid} undefined controlled terms: {undefined}")
        if len(contract.get("definition_references") or []) != len(controlled):
            errors.append(f"criterion_catalog: {cid} term/reference count mismatch")

        if contract.get("target_reference"):
            binding = target_bindings.get(cid)
            if binding is None:
                errors.append(f"criterion_catalog: {cid} has target_reference but no target binding")
            else:
                for reference in binding.get("references", []):
                    exists, _ = get_path(targets, reference)
                    if not exists:
                        errors.append(f"targets: binding {cid} references missing path {reference}")

        if contract.get("human_judgment_required") or contract.get("requirement_class") == "JUDGMENT_RUBRIC":
            if cid not in rubric_entries:
                errors.append(f"criterion_catalog: {cid} requires missing judgment rubric")

    return catalog_map


def expected_criteria_for_gate(
    gate: str,
    catalog_map: dict[str, dict[str, Any]],
    targets: dict[str, Any],
) -> set[str]:
    if gate in {"Q3A", "Q3B", "Q3C"}:
        return {
            cid for cid, contract in catalog_map.items()
            if contract.get("gate_id") == "Q3"
            and gate in set(contract.get("applicable_subgates", []))
            and contract.get("requirement_class") != NONBLOCKING_CLASS
            and criterion_is_applicable(contract, targets, result_gate=gate)
        }
    return {
        cid for cid, contract in catalog_map.items()
        if contract.get("gate_id") == gate
        and contract.get("requirement_class") != NONBLOCKING_CLASS
        and criterion_is_applicable(contract, targets, result_gate=gate)
    }


def validate_result(
    root: Path,
    result_path: Path,
    result_schema_path: Path,
    catalog_map: dict[str, dict[str, Any]],
    targets: dict[str, Any],
    status: dict[str, Any],
    expected_gate: str,
    now_utc: datetime,
    errors: list[str],
) -> dict[str, Any] | None:
    if not result_path.exists():
        errors.append(f"result file does not exist: {result_path}")
        return None
    result = (
        load_yaml(result_path)
        if result_path.suffix.lower() in {".yaml", ".yml"}
        else load_json(result_path)
    )
    validate_json_schema(result, result_schema_path, str(result_path), errors)

    rows = result.get("criterion_results") or []
    ids = [row.get("criterion_id") for row in rows]
    if len(ids) != len(set(ids)):
        errors.append(f"{result_path}: duplicate criterion IDs")

    gate = result.get("gate_id")
    if gate != expected_gate:
        errors.append(
            f"{result_path}: gate_id {gate} does not match status gate {expected_gate}"
        )
    expected = expected_criteria_for_gate(gate, catalog_map, targets)
    present = set(ids)

    if result.get("status") == "PASS":
        validate_unexpired_pass(
            result.get("expires_at"),
            f"{result_path}: result",
            now_utc,
            errors,
        )
        missing = sorted(expected - present)
        if missing:
            errors.append(f"{result_path}: PASS omits applicable criteria: {missing}")
        illegal = [
            row.get("criterion_id")
            for row in rows
            if row.get("result") in {"FAIL", "BLOCKED"}
        ]
        if illegal:
            errors.append(f"{result_path}: PASS contains failed/blocked criteria: {illegal}")

    for row in rows:
        cid = row.get("criterion_id")
        contract = catalog_map.get(cid)
        if contract is None:
            errors.append(f"{result_path}: unknown criterion ID {cid}")
            continue
        if row.get("requirement_class") != contract.get("requirement_class"):
            errors.append(f"{result_path}: {cid} requirement_class differs from catalog")
        applicable = criterion_is_applicable(contract, targets, result_gate=gate)
        if row.get("result") == "N/A":
            if applicable:
                errors.append(f"{result_path}: applicable criterion {cid} cannot be N/A")
        elif not applicable:
            errors.append(f"{result_path}: inapplicable criterion {cid} must be omitted or N/A")
        if row.get("result") not in CRITERION_RESULTS:
            errors.append(f"{result_path}: invalid criterion result for {cid}")
        if result.get("status") == "PASS" and row.get("result") == "PASS":
            for evidence_ref in row.get("evidence") or []:
                validate_evidence_reference(
                    root,
                    f"{result_path}: {cid}",
                    evidence_ref,
                    errors,
                )

    candidate = status.get("candidate", {})
    if result.get("selected_product_scope_profile") != status.get(
        "selected_product_scope_profile"
    ):
        errors.append(f"{result_path}: selected product-scope profile differs from status")
    if result.get("selected_deployment_profile") != status.get(
        "selected_deployment_profile"
    ):
        errors.append(f"{result_path}: selected deployment profile differs from status")
    if candidate.get("commit") and result.get("candidate_commit") != candidate.get("commit"):
        errors.append(f"{result_path}: candidate commit differs from status")
    if candidate.get("tag") and result.get("candidate_tag") != candidate.get("tag"):
        errors.append(f"{result_path}: candidate tag differs from status")
    if candidate.get("artifact_digest") and result.get("artifact_digest") != candidate.get(
        "artifact_digest"
    ):
        errors.append(f"{result_path}: artifact digest differs from status")
    if candidate.get("protocol_version") and result.get("protocol_version") != candidate.get(
        "protocol_version"
    ):
        errors.append(f"{result_path}: protocol version differs from status")
    if candidate.get("targets_version") and result.get("targets_version") != candidate.get(
        "targets_version"
    ):
        errors.append(f"{result_path}: targets version differs from status")
    if candidate.get("vocabulary_version") and result.get(
        "vocabulary_version"
    ) != candidate.get("vocabulary_version"):
        errors.append(f"{result_path}: vocabulary version differs from status")
    if candidate.get("criteria_catalog_digest"):
        if result.get("criteria_catalog_digest") != candidate.get("criteria_catalog_digest"):
            errors.append(f"{result_path}: criterion catalog digest differs from status")

    evidence_ref = result.get("evidence_path")
    if result.get("status") == "PASS" and evidence_ref:
        validate_evidence_reference(
            root,
            f"{result_path}: evidence_path",
            evidence_ref,
            errors,
        )

    return result


def gate_record(status: dict[str, Any], gate: str) -> dict[str, Any] | None:
    key = GATE_TO_STATUS_KEY.get(gate, gate.lower())
    for section in ("qualifications", "overlays", "conditional_overlays"):
        record = status.get(section, {}).get(key)
        if record is not None:
            return record
    return None


def validate_prerequisites(status: dict[str, Any], errors: list[str]) -> None:
    for name, record in status.get("qualifications", {}).items():
        if record.get("status") != "PASS":
            continue
        for prerequisite in record.get("prerequisites", []):
            found = None
            for section in ("qualifications", "overlays", "conditional_overlays"):
                if prerequisite in status.get(section, {}):
                    found = status[section][prerequisite]
                    break
            if not found or found.get("status") != "PASS":
                errors.append(
                    f"status: {name} PASS while prerequisite {prerequisite} is not PASS"
                )


def validate_conditional_status(
    status: dict[str, Any],
    targets: dict[str, Any],
    errors: list[str],
) -> None:
    expected = {
        "ai_llm": bool(targets.get("scope", {}).get("ai_llm_enabled_for_decision_relevant_output")),
        "candidate_generation": bool(targets.get("scope", {}).get("candidate_generation_enabled")),
        "financial_modeling": bool(targets.get("scope", {}).get("financial_modeling_enabled")),
    }
    for name, applicable in expected.items():
        record = status.get("conditional_overlays", {}).get(name)
        if not record:
            errors.append(f"status: missing conditional overlay {name}")
            continue
        if bool(record.get("applicable")) != applicable:
            errors.append(
                f"status: conditional overlay {name}.applicable does not match qualification targets"
            )
        if not applicable and record.get("status") == "PASS":
            errors.append(f"status: inapplicable conditional overlay {name} cannot be PASS")


def validate_classification(
    status: dict[str, Any],
    targets: dict[str, Any],
    errors: list[str],
) -> None:
    classification = status.get("highest_valid_classification", "")
    required = set(CLASSIFICATION_REQUIRED_GATES.get(classification, set()))
    if classification.startswith("J-QUALIFIED-"):
        required = {"P0", "Q1", "DQ", "IR", "DB", "S", "M", "O", "R", "F", "G"}
        if targets.get("scope", {}).get("user_utility_claim_enabled"):
            required |= {"Q2", "A"}
    elif classification not in CLASSIFICATION_REQUIRED_GATES:
        errors.append(f"status: unknown classification {classification!r}")
        return

    if classification not in {"L9-R", "L9-P"}:
        for conditional in ("W", "E", "CG", "FIN", "AI"):
            if conditional_gate_enabled(conditional, targets):
                required.add(conditional)

    if classification == "L9-P":
        required = {"P0"}

    for gate in sorted(required):
        record = gate_record(status, gate)
        if not record or record.get("status") != "PASS":
            errors.append(
                f"status: classification {classification} requires {gate}=PASS"
            )

    selected_profile = targets.get("scope", {}).get("product_scope_profile")
    compatible_profiles = {
        "L9-R": set(),
        "L9-P": {
            "BOUNDED_SCREENING_VALIDATED", "BOUNDED_USER_VALIDATED",
            "BOUNDED_PRODUCTION_LOCAL", "BOUNDED_PRODUCTION_SINGLE_TENANT",
            "BOUNDED_PRODUCTION_MULTI_TENANT", "US_EXPANSION_READY",
            "GLOBAL_ARCHITECTURE_PROBED", "JURISDICTION_OPERATIONALLY_QUALIFIED",
        },
        "L9-E1": {
            "BOUNDED_SCREENING_VALIDATED", "BOUNDED_USER_VALIDATED",
            "BOUNDED_PRODUCTION_LOCAL", "BOUNDED_PRODUCTION_SINGLE_TENANT",
            "BOUNDED_PRODUCTION_MULTI_TENANT", "US_EXPANSION_READY",
            "GLOBAL_ARCHITECTURE_PROBED", "JURISDICTION_OPERATIONALLY_QUALIFIED",
        },
        "L9-E2": {
            "BOUNDED_USER_VALIDATED", "BOUNDED_PRODUCTION_LOCAL",
            "BOUNDED_PRODUCTION_SINGLE_TENANT", "BOUNDED_PRODUCTION_MULTI_TENANT",
            "US_EXPANSION_READY", "GLOBAL_ARCHITECTURE_PROBED",
            "JURISDICTION_OPERATIONALLY_QUALIFIED",
        },
        "L10-BP-LOCAL": {"BOUNDED_PRODUCTION_LOCAL"},
        "L10-BP-ST": {"BOUNDED_PRODUCTION_SINGLE_TENANT"},
        "L10-BP-MT": {"BOUNDED_PRODUCTION_MULTI_TENANT"},
        "X-US": {"US_EXPANSION_READY", "GLOBAL_ARCHITECTURE_PROBED"},
        "X-GLOBAL-ARCH": {"GLOBAL_ARCHITECTURE_PROBED"},
    }
    if classification.startswith("J-QUALIFIED-"):
        allowed = {"JURISDICTION_OPERATIONALLY_QUALIFIED"}
    else:
        allowed = compatible_profiles.get(classification, set())
    if allowed and selected_profile not in allowed:
        errors.append(
            f"status: classification {classification} is incompatible with selected "
            f"product-scope profile {selected_profile}"
        )

    deployment = targets.get("scope", {}).get("deployment_profile")
    if classification == "L10-BP-MT" and deployment != "PUBLIC_MULTI_TENANT_SAAS":
        errors.append("status: L10-BP-MT requires PUBLIC_MULTI_TENANT_SAAS deployment profile")
    if classification == "L10-BP-ST" and deployment != "PRIVATE_SINGLE_TENANT_HOSTED":
        errors.append("status: L10-BP-ST requires PRIVATE_SINGLE_TENANT_HOSTED deployment profile")
    if classification == "L10-BP-LOCAL" and deployment != "LOCAL_SINGLE_USER":
        errors.append("status: L10-BP-LOCAL requires LOCAL_SINGLE_USER deployment profile")


def validate_active_parameterization(
    targets: dict[str, Any],
    status: dict[str, Any],
    profiles: dict[str, Any],
    catalog_map: dict[str, dict[str, Any]],
    rubrics: dict[str, Any],
    errors: list[str],
) -> None:
    p0_status = status.get("qualifications", {}).get("p0", {}).get("status")
    p0_pass = p0_status == "PASS"
    targets_frozen = targets.get("status") == "FROZEN"
    if not p0_pass and not targets_frozen:
        return

    if p0_pass and not targets_frozen:
        errors.append("status: P0 cannot PASS while qualification targets are not FROZEN")
    active_gates = selected_profile_gates(profiles, targets, errors)
    # P0 itself is always active before empirical execution.
    active_gates.add("P0")
    bindings = targets.get("criterion_bindings", {})
    rubric_entries = rubrics.get("criteria", {})
    active_human_criteria = [
        cid for cid, contract in catalog_map.items()
        if (contract.get("human_judgment_required")
            and (contract.get("gate_id") in active_gates
                 or bool(set(contract.get("applicable_subgates", [])) & active_gates))
            and criterion_is_applicable(contract, targets))
    ]
    if active_human_criteria and rubrics.get("status") != "FROZEN":
        errors.append(
            "status: P0 cannot PASS while the judgment-rubric registry is not FROZEN"
        )

    for cid, contract in catalog_map.items():
        gate = contract.get("gate_id")
        q3_gate_names = set(contract.get("applicable_subgates", []))
        active = gate in active_gates or bool(q3_gate_names & active_gates)
        if not active or not criterion_is_applicable(contract, targets):
            continue
        if contract.get("requirement_class") == NONBLOCKING_CLASS:
            continue
        if p0_pass and contract.get("parameterization_status") != "FROZEN":
            errors.append(f"status: P0 PASS while applicable criterion contract {cid} is DRAFT")

        if contract.get("target_reference"):
            binding = bindings.get(cid)
            if not binding or binding.get("status") != "FROZEN":
                errors.append(
                    f"targets: frozen/P0 scope requires target binding {cid}=FROZEN"
                )
            else:
                for reference in binding.get("references", []):
                    exists, value = get_path(targets, reference)
                    if not exists or unresolved(value):
                        errors.append(
                            f"targets: frozen/P0 scope has unresolved {cid} reference {reference}"
                        )

        if p0_pass and contract.get("human_judgment_required"):
            rubric = rubric_entries.get(cid)
            if not rubric or rubric.get("status") != "FROZEN":
                errors.append(f"status: P0 PASS while judgment rubric {cid} is not FROZEN")


def validate_result_records(
    root: Path,
    status: dict[str, Any],
    targets: dict[str, Any],
    catalog_map: dict[str, dict[str, Any]],
    result_schema_path: Path,
    now_utc: datetime,
    errors: list[str],
) -> None:
    root = root.resolve()
    for section in ("qualifications", "overlays", "conditional_overlays"):
        for name, record in status.get(section, {}).items():
            current_status = record.get("status")
            if current_status not in {"PASS", "FAIL", "BLOCKED"}:
                continue
            expected_gate = STATUS_KEY_TO_GATE.get(name, name.upper())
            if current_status == "PASS":
                validate_unexpired_pass(
                    record.get("expires_at"),
                    f"status: {section}.{name}",
                    now_utc,
                    errors,
                )
            if (
                current_status == "BLOCKED"
                and section == "qualifications"
                and name == "p0"
            ):
                validate_blocked_record(root, section, name, record, errors)
            result_ref = record.get("result_path")
            if not result_ref:
                if (
                    current_status == "BLOCKED"
                    and section == "qualifications"
                    and name == "p0"
                ):
                    continue
                errors.append(
                    f"status: {section}.{name} is {current_status} but has no result_path"
                )
                continue
            result_path = Path(result_ref)
            if not result_path.is_absolute():
                result_path = (root / result_path).resolve()
            result = validate_result(
                root, result_path, result_schema_path,
                catalog_map, targets, status, expected_gate, now_utc, errors
            )
            if result and result.get("status") != current_status:
                errors.append(
                    f"status: {section}.{name}={current_status} "
                    f"but result file says {result.get('status')}"
                )


def validate_blocked_record(
    root: Path,
    section: str,
    name: str,
    record: dict[str, Any],
    errors: list[str],
) -> None:
    label = f"{section}.{name}"
    blocked_reason = record.get("blocked_reason")
    if not isinstance(blocked_reason, str) or not blocked_reason.strip():
        errors.append(f"status: {label} is BLOCKED but has no blocked_reason")

    blocker_references = record.get("blocker_references")
    if not isinstance(blocker_references, list) or not blocker_references:
        errors.append(f"status: {label} is BLOCKED but has no blocker_references")
        return

    for reference in blocker_references:
        if not isinstance(reference, str) or not reference.strip():
            errors.append(f"status: {label} has invalid blocker reference {reference!r}")
            continue
        reference_path = Path(reference)
        if reference_path.is_absolute():
            errors.append(
                f"status: {label} blocker reference must be repo-local: {reference}"
            )
            continue
        resolved = (root / reference_path).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            errors.append(f"status: {label} blocker reference escapes repo: {reference}")
            continue
        if not resolved.exists():
            errors.append(f"status: {label} blocker reference does not exist: {reference}")


def load_profile_directory(
    directory: Path,
    schema_path: Path,
    id_field: str,
    label: str,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    if not directory.exists() or not directory.is_dir():
        errors.append(f"missing required profile directory ({label}): {directory}")
        return {}
    profiles: dict[str, dict[str, Any]] = {}
    for path in sorted([*directory.glob("*.yaml"), *directory.glob("*.yml")]):
        value = load_yaml(path)
        validate_json_schema(value, schema_path, str(path), errors)
        profile_id = value.get(id_field) if isinstance(value, dict) else None
        if not profile_id:
            errors.append(f"{path}: missing {id_field}")
            continue
        if profile_id in profiles:
            errors.append(f"{label}: duplicate {id_field} {profile_id!r}")
            continue
        profiles[profile_id] = value
    return profiles


def coverage_covers(required: set[str], coverage: set[str]) -> bool:
    if not required:
        return True
    if not coverage:
        return False
    if "*" in coverage or "GLOBAL" in coverage:
        return True
    for item in required:
        if item in coverage:
            continue
        if any(item.startswith(f"{covered}-") for covered in coverage):
            continue
        return False
    return True


def coverage_overlaps(required: set[str], coverage: set[str]) -> bool:
    if not required:
        return True
    if not coverage:
        return False
    if "*" in coverage or "GLOBAL" in coverage:
        return True
    for item in required:
        if item in coverage:
            return True
        if any(item.startswith(f"{covered}-") for covered in coverage):
            return True
    return False


def validate_conditional_right(
    source_id: str,
    right_name: str,
    rights_conditions: dict[str, Any],
    conditions_enforced_by: list[str],
    errors: list[str],
) -> None:
    if not conditions_enforced_by or unresolved(conditions_enforced_by):
        errors.append(
            f"source profile {source_id}: conditional {right_name} right "
            "lacks enforcement controls"
        )
    if not rights_conditions or unresolved(rights_conditions):
        errors.append(
            f"source profile {source_id}: conditional {right_name} right "
            "lacks recorded rights conditions"
        )


def validate_domain_and_source_profiles(
    targets: dict[str, Any],
    status: dict[str, Any],
    domain_profiles: dict[str, dict[str, Any]],
    source_profiles: dict[str, dict[str, Any]],
    errors: list[str],
    warnings: list[str],
) -> None:
    scope = targets.get("scope", {})
    required_domains = set(scope.get("qualified_domains", []))
    required_sources = set(scope.get("source_profile_ids", []))
    p0_pass = status.get("qualifications", {}).get("p0", {}).get("status") == "PASS"

    missing_domains = sorted(required_domains - set(domain_profiles))
    missing_sources = sorted(required_sources - set(source_profiles))
    if missing_domains:
        if p0_pass:
            errors.append(
                f"domain profiles missing for qualified domains: {missing_domains}"
            )
        elif "domain_profile_template" in domain_profiles:
            warnings.append(
                f"{len(missing_domains)} qualified-domain profiles "
                "are represented by template only"
            )
        else:
            warnings.append(
                f"{len(missing_domains)} qualified-domain profiles are missing before P0"
            )
    if missing_sources:
        if p0_pass:
            errors.append(
                f"source profiles missing for selected sources: {missing_sources}"
            )
        else:
            warnings.append(
                f"{len(missing_sources)} selected source profiles are missing before P0"
            )

    if not p0_pass:
        draft_domains = sorted(
            key for key in required_domains
            if domain_profiles.get(key, {}).get("status") != "FROZEN"
        )
        if draft_domains and not missing_domains:
            warnings.append(f"{len(draft_domains)} qualified-domain profiles remain DRAFT")
        if not required_sources:
            warnings.append("no source_profile_ids are frozen in the target scope")
        else:
            draft_sources = sorted(
                key for key in required_sources
                if source_profiles.get(key, {}).get("status") != "APPROVED"
            )
            if draft_sources:
                warnings.append(
                    f"{len(draft_sources)} selected source profiles are not APPROVED"
                )
        return

    if not required_sources:
        errors.append("status: P0 cannot PASS with an empty source_profile_ids set")

    for domain_id in sorted(required_domains):
        profile = domain_profiles.get(domain_id)
        if not profile:
            continue
        if profile.get("status") != "FROZEN":
            errors.append(f"status: P0 PASS while domain profile {domain_id} is not FROZEN")
        profile_scope = profile.get("scope", {})
        if profile_scope.get("geographies") != scope.get("geographies"):
            errors.append(
                f"domain profile {domain_id}: geographies do not exactly match frozen target scope"
            )
        if profile_scope.get("intents") != scope.get("intents"):
            errors.append(
                f"domain profile {domain_id}: intents do not exactly match frozen target scope"
            )
        if profile_scope.get("input_modalities") != scope.get("input_modalities"):
            errors.append(
                f"domain profile {domain_id}: input_modalities do not exactly match frozen target scope"
            )
        if profile_scope.get("output_channels") != scope.get("output_channels"):
            errors.append(
                f"domain profile {domain_id}: output_channels do not exactly match frozen target scope"
            )
        unresolved_profile_fields = [
            field
            for field in [
                "reference_hierarchy",
                "issue_taxonomy",
                "severity_rubric",
                "confidence_rubric",
                "source_requirements",
                "spatial_temporal_tolerances",
                "unknown_states",
                "metrics",
                "owner",
                "reviewers",
                "expires_at",
                "frozen_at",
                "approved_by",
                "invalidation_triggers",
                "field_surveillance_plan",
            ]
            if unresolved(profile.get(field))
        ]
        if unresolved_profile_fields:
            errors.append(
                f"domain profile {domain_id}: unresolved frozen profile fields "
                f"{unresolved_profile_fields}"
            )
        source_requirements = profile.get("source_requirements") or []
        if unresolved(source_requirements):
            errors.append(f"domain profile {domain_id}: source requirements unresolved")

    selected_product_profile = scope.get("product_scope_profile")
    commercial = bool(scope.get("commercial_profile_enabled"))
    ai_enabled = bool(scope.get("ai_llm_enabled_for_decision_relevant_output"))
    source_domain_coverage: set[str] = set()
    source_domain_wildcard = False

    for source_id in sorted(required_sources):
        profile = source_profiles.get(source_id)
        if not profile:
            continue
        if profile.get("status") != "APPROVED":
            errors.append(f"status: P0 PASS while source profile {source_id} is not APPROVED")
            continue
        if selected_product_profile not in set(profile.get("approved_use_profiles", [])):
            errors.append(
                f"source profile {source_id}: selected product profile is not approved"
            )
        coverage = profile.get("coverage") or {}
        coverage_geographies = set(coverage.get("geographies") or [])
        coverage_domains = set(coverage.get("domains") or [])
        if "*" in coverage_domains or "GLOBAL" in coverage_domains:
            source_domain_wildcard = True
            source_domain_coverage.update(required_domains)
        else:
            for domain_id in required_domains:
                if coverage_covers({domain_id}, coverage_domains):
                    source_domain_coverage.add(domain_id)
        if not coverage_covers(set(scope.get("geographies") or []), coverage_geographies):
            errors.append(
                f"source profile {source_id}: coverage.geographies does not cover target scope"
            )
        if not coverage_overlaps(required_domains, coverage_domains):
            errors.append(
                f"source profile {source_id}: coverage.domains does not overlap target domains"
            )
        rights = profile.get("rights", {})
        operations = set(profile.get("enabled_operations", []))
        rights_conditions = profile.get("rights_conditions") or {}
        conditions_enforced_by = profile.get("conditions_enforced_by") or []
        if commercial and rights.get("commercial_use") in {"UNKNOWN", "PROHIBITED"}:
            errors.append(f"source profile {source_id}: commercial use is not permitted")
        if commercial and rights.get("commercial_use") == "CONDITIONAL":
            validate_conditional_right(
                source_id,
                "commercial_use",
                rights_conditions,
                conditions_enforced_by,
                errors,
            )
        right_by_operation = {
            "CACHE": ("cache",),
            "RETAIN_HISTORY": ("retain",),
            "RAW_EXPORT": ("raw_data", "export"),
            "DERIVED_EXPORT": ("export",),
            "DISPLAY": ("redistribute",),
            "AI_PROCESS": ("ai_use",),
        }
        for operation, right_names in right_by_operation.items():
            if operation not in operations:
                continue
            for right_name in right_names:
                right_value = rights.get(right_name)
                if right_value in {"UNKNOWN", "PROHIBITED"}:
                    errors.append(
                        f"source profile {source_id}: operation {operation} conflicts with {right_name} right"
                    )
                if right_value == "CONDITIONAL":
                    validate_conditional_right(
                        source_id,
                        right_name,
                        rights_conditions,
                        conditions_enforced_by,
                        errors,
                    )
        if (
            ai_enabled
            and "AI_PROCESS" in operations
            and rights.get("ai_use") in {"UNKNOWN", "PROHIBITED"}
        ):
            errors.append(f"source profile {source_id}: AI processing is not permitted")

    if not source_domain_wildcard and not coverage_covers(required_domains, source_domain_coverage):
        missing_domains = sorted(required_domains - source_domain_coverage)
        errors.append(
            "selected source profiles do not cover target domains: "
            f"{missing_domains}"
        )


def validate_scope_versioning(
    targets: dict[str, Any],
    status: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    scope = targets.get("scope", {})
    required_version_fields = [
        "report_contract_version",
        "api_contract_version",
        "normalization_schema_version",
        "geometry_pipeline_version",
        "source_snapshot_policy",
        "data_as_of_policy",
    ]
    p0_pass = status.get("qualifications", {}).get("p0", {}).get("status") == "PASS"
    unresolved_fields = [
        field for field in required_version_fields if unresolved(scope.get(field))
    ]
    if p0_pass and unresolved_fields:
        errors.append(
            f"status: P0 PASS while scope/version fields are unresolved: {unresolved_fields}"
        )
    elif unresolved_fields:
        warnings.append(
            f"{len(unresolved_fields)} scope/version fields remain unresolved"
        )
    if p0_pass and unresolved(scope.get("ruleset_versions")):
        errors.append("status: P0 PASS while ruleset_versions is unresolved")
    elif unresolved(scope.get("ruleset_versions")):
        warnings.append("ruleset_versions remain unresolved")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--layout", choices=["auto", "bundle", "repo"], default="auto")
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--status", type=Path)
    parser.add_argument("--rubrics", type=Path)
    parser.add_argument("--domain-profiles-dir", type=Path)
    parser.add_argument("--source-profiles-dir", type=Path)
    parser.add_argument(
        "--now",
        help="ISO-8601 UTC timestamp used for deterministic PASS expiry checks.",
    )
    args = parser.parse_args(argv)
    clock_errors: list[str] = []
    now_utc = (
        parse_datetime_utc(args.now, "--now", clock_errors)
        if args.now
        else datetime.now(timezone.utc)
    )
    if clock_errors or now_utc is None:
        for error in clock_errors:
            print(f"FAIL: {error}")
        return 1

    root = args.root.resolve()
    if args.layout == "auto":
        layout = (
            "repo"
            if (root / "docs" / "qualification" / "EMPIRICAL_QUALIFICATION_FRAMEWORK.md").exists()
            else "bundle"
        )
    else:
        layout = args.layout

    if layout == "repo":
        docs_root = root / "docs" / "qualification"
        config_root = root / "config" / "qualification"
        schema_root = root / "schemas" / "qualification"
        state_root = root / "state"
        targets_path = (args.targets or config_root / "qualification_targets.yaml").resolve()
        status_path = (
            args.status or state_root / "EMPIRICAL_QUALIFICATION_STATUS.yaml"
        ).resolve()
        rubrics_path = (args.rubrics or config_root / "judgment_rubrics.yaml").resolve()
        domain_profiles_dir = (
            args.domain_profiles_dir or config_root / "domain_profiles"
        ).resolve()
        source_profiles_dir = (
            args.source_profiles_dir or config_root / "source_profiles"
        ).resolve()
        required_files = {
            "framework": docs_root / "EMPIRICAL_QUALIFICATION_FRAMEWORK.md",
            "catalog": config_root / "criterion_catalog.yaml",
            "profiles": config_root / "qualification_profiles.yaml",
            "vocabulary": config_root / "qualification_vocabulary.yaml",
            "change_matrix": config_root / "change_impact_matrix.yaml",
            "readiness_crosswalk": config_root / "readiness_crosswalk.yaml",
            "result_schema": schema_root / "qualification_result.schema.json",
            "criterion_schema": schema_root / "criterion_contract.schema.json",
            "catalog_schema": schema_root / "criterion_catalog.schema.json",
            "profiles_schema": schema_root / "qualification_profiles.schema.json",
            "vocabulary_schema": schema_root / "qualification_vocabulary.schema.json",
            "change_schema": schema_root / "change_impact_matrix.schema.json",
            "readiness_crosswalk_schema": schema_root / "readiness_crosswalk.schema.json",
            "targets_schema": schema_root / "qualification_targets.schema.json",
            "status_schema": schema_root / "empirical_qualification_status.schema.json",
            "rubrics_schema": schema_root / "judgment_rubrics.schema.json",
            "domain_profile_schema": schema_root / "domain_qualification_profile.schema.json",
            "source_profile_schema": schema_root / "source_quality_profile.schema.json",
        }
    else:
        targets_path = (
            args.targets or root / "qualification_targets.example.yaml"
        ).resolve()
        status_path = (
            args.status or root / "empirical_qualification_status.example.yaml"
        ).resolve()
        rubrics_path = (
            args.rubrics or root / "judgment_rubrics.example.yaml"
        ).resolve()
        domain_profiles_dir = (
            args.domain_profiles_dir or root / "domain_profiles"
        ).resolve()
        source_profiles_dir = (
            args.source_profiles_dir or root / "source_profiles"
        ).resolve()
        required_files = {
            "framework": root / "EMPIRICAL_QUALIFICATION_FRAMEWORK.md",
            "catalog": root / "criterion_catalog.yaml",
            "profiles": root / "qualification_profiles.yaml",
            "vocabulary": root / "qualification_vocabulary.yaml",
            "change_matrix": root / "change_impact_matrix.yaml",
            "result_schema": root / "qualification_result.schema.json",
            "criterion_schema": root / "criterion_contract.schema.json",
            "catalog_schema": root / "criterion_catalog.schema.json",
            "profiles_schema": root / "qualification_profiles.schema.json",
            "vocabulary_schema": root / "qualification_vocabulary.schema.json",
            "change_schema": root / "change_impact_matrix.schema.json",
            "targets_schema": root / "qualification_targets.schema.json",
            "status_schema": root / "empirical_qualification_status.schema.json",
            "rubrics_schema": root / "judgment_rubrics.schema.json",
            "domain_profile_schema": root / "domain_qualification_profile.schema.json",
            "source_profile_schema": root / "source_quality_profile.schema.json",
        }

    errors: list[str] = []
    warnings: list[str] = []

    for label, path in {
        **required_files,
        "targets": targets_path,
        "status": status_path,
        "rubrics": rubrics_path,
    }.items():
        if not path.exists():
            errors.append(f"missing required file ({label}): {path}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    targets = load_yaml(targets_path)
    status = load_yaml(status_path)
    rubrics = load_yaml(rubrics_path)
    profiles = load_yaml(required_files["profiles"])
    vocabulary = load_yaml(required_files["vocabulary"])
    change_matrix = load_yaml(required_files["change_matrix"])
    readiness_crosswalk = (
        load_yaml(required_files["readiness_crosswalk"])
        if "readiness_crosswalk" in required_files
        else None
    )
    catalog = load_yaml(required_files["catalog"])

    validate_json_schema(targets, required_files["targets_schema"], str(targets_path), errors)
    validate_json_schema(status, required_files["status_schema"], str(status_path), errors)
    validate_json_schema(rubrics, required_files["rubrics_schema"], str(rubrics_path), errors)
    validate_json_schema(profiles, required_files["profiles_schema"], "qualification_profiles", errors)
    validate_json_schema(vocabulary, required_files["vocabulary_schema"], "qualification_vocabulary", errors)
    validate_json_schema(change_matrix, required_files["change_schema"], "change_impact_matrix", errors)

    catalog_map = validate_catalog(
        root=root,
        catalog=catalog,
        framework_path=required_files["framework"],
        catalog_schema_path=required_files["catalog_schema"],
        criterion_schema_path=required_files["criterion_schema"],
        vocabulary=vocabulary,
        targets=targets,
        rubrics=rubrics,
        errors=errors,
    )
    validate_profiles(profiles, set(catalog_map), errors)
    validate_change_impact_matrix(change_matrix, set(catalog_map), errors)
    if readiness_crosswalk is not None:
        validate_readiness_crosswalk(
            root,
            readiness_crosswalk,
            required_files["readiness_crosswalk_schema"],
            set(catalog_map),
            errors,
        )
        validate_checker_advertisements(root, readiness_crosswalk, errors)

    domain_profiles = load_profile_directory(
        domain_profiles_dir,
        required_files["domain_profile_schema"],
        "domain_id",
        "domain_profiles",
        errors,
    )
    source_profiles = load_profile_directory(
        source_profiles_dir,
        required_files["source_profile_schema"],
        "source_id",
        "source_profiles",
        errors,
    )

    if status.get("selected_product_scope_profile") != targets.get("scope", {}).get("product_scope_profile"):
        errors.append("status/targets: selected product-scope profile mismatch")
    if status.get("selected_deployment_profile") != targets.get("scope", {}).get("deployment_profile"):
        errors.append("status/targets: selected deployment profile mismatch")

    selected_profile = profiles.get("profiles", {}).get(
        status.get("selected_product_scope_profile"), {}
    )
    profile_deployment = selected_profile.get("deployment_profile")
    if profile_deployment and profile_deployment != status.get("selected_deployment_profile"):
        errors.append(
            "status/profiles: selected deployment profile conflicts with product-scope profile"
        )

    validate_prerequisites(status, errors)
    validate_conditional_status(status, targets, errors)
    validate_classification(status, targets, errors)
    validate_active_parameterization(
        targets, status, profiles, catalog_map, rubrics, errors
    )
    validate_result_records(
        root,
        status,
        targets,
        catalog_map,
        required_files["result_schema"],
        now_utc,
        errors,
    )
    validate_domain_and_source_profiles(
        targets, status, domain_profiles, source_profiles, errors, warnings
    )
    validate_scope_versioning(targets, status, errors, warnings)

    # Keep duplicated enabled/applicable flags coherent.
    flag_pairs = [
        ("candidate_generation", "candidate_generation_enabled"),
        ("financial_modeling", "financial_modeling_enabled"),
        ("ai_llm", "ai_llm_enabled_for_decision_relevant_output"),
    ]
    for section_name, scope_flag in flag_pairs:
        section_enabled = bool(targets.get(section_name, {}).get("enabled"))
        scope_enabled = bool(targets.get("scope", {}).get(scope_flag))
        if section_enabled != scope_enabled:
            errors.append(
                f"targets: {section_name}.enabled does not match scope.{scope_flag}"
            )

    # Structural DRAFT files are allowed but never imply qualification readiness.
    if targets.get("status") != "FROZEN":
        warnings.append("qualification targets are DRAFT")
    draft_contracts = [
        cid for cid, item in catalog_map.items()
        if item.get("parameterization_status") != "FROZEN"
        and item.get("requirement_class") != NONBLOCKING_CLASS
    ]
    if draft_contracts:
        warnings.append(f"{len(draft_contracts)} criterion contracts remain DRAFT")
    draft_rubrics = [
        cid for cid, item in (rubrics.get("criteria") or {}).items()
        if item.get("status") != "FROZEN"
    ]
    if draft_rubrics:
        warnings.append(f"{len(draft_rubrics)} judgment rubrics remain DRAFT")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"qualification validation: FAIL ({len(errors)} issue(s))")
        return 1

    print("qualification structural validation: PASS")
    print(f"layout: {layout}")
    print(f"framework criteria: {len(catalog_map)}")
    print(f"target status: {targets.get('status')}")
    print(f"highest valid classification: {status.get('highest_valid_classification')}")
    for warning in warnings:
        print(f"BLOCKED-READINESS: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
