from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import build_release_package
import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "config/release_package.yaml",
    "docs/runbooks/release_package.md",
    "scripts/build_release_package.py",
    "scripts/build_release_package.ps1",
    "scripts/build_release_package.sh",
    "scripts/release_package_check.py",
    "scripts/run_release_package_check.ps1",
    "scripts/run_release_package_check.sh",
)
REQUIRED_INCLUDES = {
    ".dockerignore",
    ".env.example",
    ".github/workflows/ci.yml",
    "AGENTS.md",
    "CLAUDE.md",
    "DESIGN.md",
    "LANE_OWNERSHIP.md",
    "MANIFEST.md",
    "MILESTONE_MAP.md",
    "README.md",
    "START_HERE.md",
    "backend/app",
    "backend/Dockerfile",
    "backend/pyproject.toml",
    "backend/requirements-prod.lock",
    "backend/tests",
    "config",
    "db",
    "docker-compose.yml",
    "docs",
    "lanes",
    "plans",
    "registers",
    "schemas",
    "scripts",
    "state/connector-state.md",
    "state/DECISION_LEDGER.md",
    "state/lane-a-state.md",
    "state/lane-b-state.md",
    "state/lane-c-state.md",
    "state/lane-d-state.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "state/OPEN_QUESTIONS.md",
    "state/POST_RC_AUTHORITY_SPLIT.md",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "state/PROJECT_STATE.md",
    "state/VALIDATION_LOG.md",
    "state/WORKLOG.md",
    "tasks",
    "tests/fixtures",
}
REQUIRED_EXCLUDE_PARTS = {
    ".git",
    ".codesight",
    ".codex",
    ".coverage",
    ".claude",
    ".gstack",
    ".mypy_cache",
    ".omc",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "agent-inbox",
    "htmlcov",
    "local_artifacts",
    "venv",
    "worktrees",
}
REQUIRED_HANDOFF_PATHS = {
    ".dockerignore",
    "START_HERE.md",
    "CLAUDE.md",
    "MILESTONE_MAP.md",
    "LANE_OWNERSHIP.md",
    "DESIGN.md",
    "plans",
    "state/PROJECT_STATE.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "state/POST_RC_AUTHORITY_SPLIT.md",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "state/VALIDATION_LOG.md",
    "state/WORKLOG.md",
    "tasks",
    "lanes",
    "backend/tests",
    "tests/fixtures",
    "docs/planning_pack",
}
REQUIRED_EXCLUDED_BOUNDARY_PATHS = {
    "state/agent-inbox",
    "state/agent-inbox/for-codex.md",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require(
        (ROOT / normalized).exists(),
        f"release package referenced path missing: {normalized}",
    )


def require_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise SystemExit(f"{key} must be a list")

    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise SystemExit(f"{key} entries must be strings")
        result.append(item)
    return result


def boundary_includes_path(
    path_text: str,
    includes: set[str],
    exclude_parts: set[str],
    exclude_suffixes: set[str],
) -> bool:
    relative = Path(path_text.replace("\\", "/"))
    if any(part in exclude_parts for part in relative.parts):
        return False
    if relative.suffix in exclude_suffixes:
        return False
    for include_text in includes:
        include = Path(include_text.replace("\\", "/"))
        if relative == include or include in relative.parents:
            return True
    return False


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require(
            (ROOT / path_text).is_file(),
            f"required release-package artifact missing: {path_text}",
        )


def validate_handoff_boundary(
    includes: set[str],
    exclude_parts: set[str],
    exclude_suffixes: set[str],
    gates: set[str],
) -> None:
    for path in REQUIRED_HANDOFF_PATHS:
        require((ROOT / path).exists(), f"required handoff path missing: {path}")

    missing_handoff_paths = sorted(
        path
        for path in REQUIRED_HANDOFF_PATHS
        if not boundary_includes_path(path, includes, exclude_parts, exclude_suffixes)
    )
    require(not missing_handoff_paths, f"missing handoff package paths: {missing_handoff_paths}")

    unexpectedly_included = sorted(
        path
        for path in REQUIRED_EXCLUDED_BOUNDARY_PATHS
        if boundary_includes_path(path, includes, exclude_parts, exclude_suffixes)
    )
    require(
        not unexpectedly_included,
        f"release package must exclude volatile/planning paths: {unexpectedly_included}",
    )

    manifest = json.loads(read_text("backend/app/operator_cases/manifest.json"))
    fixture_root = manifest.get("source_fixture_root")
    require(
        isinstance(fixture_root, str) and bool(fixture_root),
        "source_fixture_root is required",
    )
    require(
        boundary_includes_path(fixture_root, includes, exclude_parts, exclude_suffixes),
        f"operator_cases source_fixture_root is outside package boundary: {fixture_root}",
    )

    if "scripts/verify.ps1" in gates:
        require(
            boundary_includes_path("backend/tests", includes, exclude_parts, exclude_suffixes),
            "scripts/verify.ps1 package gate requires backend/tests in the package",
        )


def validate_catalog() -> None:
    payload = yaml.safe_load(read_text("config/release_package.yaml"))
    require(isinstance(payload, dict), "release package catalog must be a mapping")
    require(
        payload.get("schema_version") == "release_package_v1",
        "unexpected release package schema",
    )
    require(payload.get("package_name") == "land-diligence", "package name mismatch")
    require(
        payload.get("output_dir") == "local_artifacts/releases",
        "release output dir must stay local",
    )
    require(
        payload.get("manifest_filename") == "release-manifest.json",
        "release manifest filename mismatch",
    )

    includes = set(require_list(payload, "include_paths"))
    missing_includes = sorted(REQUIRED_INCLUDES - includes)
    require(not missing_includes, f"missing release includes: {missing_includes}")
    for include in includes:
        require_existing(include)
        require(
            include != ".git" and not include.startswith(".git/"),
            "release package must not include .git",
        )
        require(
            not include.startswith("local_artifacts"),
            "release package must not include local_artifacts",
        )
        require(not include.startswith("worktrees"), "release package must not include worktrees")

    exclude_parts = set(require_list(payload, "exclude_path_parts"))
    missing_excludes = sorted(REQUIRED_EXCLUDE_PARTS - exclude_parts)
    require(not missing_excludes, f"missing release excludes: {missing_excludes}")

    suffixes = set(require_list(payload, "exclude_suffixes"))
    require(
        {".log", ".pyc", ".pyo", ".tmp", ".bak"}.issubset(suffixes),
        "missing generated-file suffix excludes",
    )

    gates = set(require_list(payload, "required_release_gates"))
    for gate in gates:
        require_existing(gate)
    require("scripts/verify.ps1" in gates, "release package must require verify gate")
    require(
        "scripts/run_release_readiness_check.ps1" in gates,
        "release package must require release readiness gate",
    )
    validate_handoff_boundary(includes, exclude_parts, suffixes, gates)
    validate_builder_file_list(includes, exclude_parts, suffixes)


def validate_builder_file_list(
    includes: set[str],
    exclude_parts: set[str],
    exclude_suffixes: set[str],
) -> None:
    files = build_release_package.iter_release_files(
        sorted(includes),
        exclude_parts,
        exclude_suffixes,
    )
    forbidden_paths: list[str] = []
    forbidden_suffixes: list[str] = []
    for path in files:
        relative = path.relative_to(ROOT)
        if set(relative.parts) & exclude_parts:
            forbidden_paths.append(relative.as_posix())
        if relative.suffix in exclude_suffixes:
            forbidden_suffixes.append(relative.as_posix())

    require(not forbidden_paths, f"release package includes excluded paths: {forbidden_paths}")
    require(
        not forbidden_suffixes,
        f"release package includes excluded suffixes: {forbidden_suffixes}",
    )


def validate_builders() -> None:
    builder = read_text("scripts/build_release_package.py")
    for phrase in (
        "release_package.yaml",
        "zipfile.ZipFile",
        '"x"',
        "release_package_manifest_v1",
        "pushes_registry_image",
        "creates_hosted_deployment",
        "includes_secrets",
        "sha256_file",
    ):
        require(phrase in builder, f"build_release_package.py missing phrase: {phrase}")
    require("rmtree" not in builder, "build_release_package.py must not delete staging trees")
    require("unlink(" not in builder, "build_release_package.py must not delete files")
    require("remove(" not in builder, "build_release_package.py must not remove files")

    for script_name in ("build_release_package.ps1", "build_release_package.sh"):
        text = read_text(f"scripts/{script_name}")
        require(
            "build_release_package.py" in text,
            f"{script_name} must delegate to build_release_package.py",
        )


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/release_package.md")
    for phrase in (
        "run_release_package_check.ps1",
        "scripts/release_package_check.py",
        "scripts/build_release_package.py",
        "validate-only",
        "build_release_package.ps1",
        "local_artifacts/releases",
        "fails if either output already exists",
        "does not delete, overwrite, push, deploy, or publish",
        "No registry image is pushed",
        "No hosted deployment",
        "blocked sources",
        "DS-017",
        "current worktree",
        "startup/routing/state/plan/task authority",
        "backend tests",
        "selected-county fixtures",
        "excludes state/agent-inbox",
        "local agent state",
        "includes docs/planning_pack",
    ):
        require(phrase in runbook, f"release package runbook missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_builders()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
