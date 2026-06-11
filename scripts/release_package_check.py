from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "config/release_package.yaml",
    "docs/runbooks/release_package.md",
    "scripts/build_release_package.ps1",
    "scripts/build_release_package.sh",
    "scripts/release_package_check.py",
    "scripts/run_release_package_check.ps1",
    "scripts/run_release_package_check.sh",
)
REQUIRED_INCLUDES = {
    ".env.example",
    ".github/workflows/ci.yml",
    "AGENTS.md",
    "MANIFEST.md",
    "README.md",
    "backend/app",
    "backend/Dockerfile",
    "backend/pyproject.toml",
    "backend/requirements-prod.lock",
    "config",
    "db",
    "docker-compose.yml",
    "docs/runbooks",
    "docs/sbom",
    "registers",
    "schemas",
    "scripts",
}
REQUIRED_EXCLUDE_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "local_artifacts",
    "worktrees",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"release package referenced path missing: {normalized}")


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


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require(
            (ROOT / path_text).is_file(),
            f"required release-package artifact missing: {path_text}",
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
        {".pyc", ".pyo", ".tmp", ".bak"}.issubset(suffixes),
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


def validate_builders() -> None:
    for script_name in ("build_release_package.ps1", "build_release_package.sh"):
        text = read_text(f"scripts/{script_name}")
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
            require(phrase in text, f"{script_name} missing phrase: {phrase}")
        require("rmtree" not in text, f"{script_name} must not delete staging trees")
        require("unlink(" not in text, f"{script_name} must not delete files")
        require("remove(" not in text, f"{script_name} must not remove files")


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/release_package.md")
    for phrase in (
        "run_release_package_check.ps1",
        "scripts/release_package_check.py",
        "validate-only",
        "build_release_package.ps1",
        "local_artifacts/releases",
        "fails if either output already exists",
        "does not delete, overwrite, push, deploy, or publish",
        "No registry image is pushed",
        "No hosted deployment",
        "current worktree",
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
