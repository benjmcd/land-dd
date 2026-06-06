#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required_files=(
  "config/release_package.yaml"
  "docs/runbooks/release_package.md"
  "scripts/build_release_package.ps1"
  "scripts/build_release_package.sh"
  "scripts/run_release_package_check.ps1"
  "scripts/run_release_package_check.sh"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "required release-package artifact missing: $file" >&2
    exit 1
  fi
done

python - <<'PY'
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
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


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"release package referenced path missing: {normalized}")


def require_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    require(isinstance(value, list), f"{key} must be a list")
    result: list[str] = []
    for item in value:
        require(isinstance(item, str) and item, f"{key} entries must be strings")
        result.append(item)
    return result


payload = yaml.safe_load((ROOT / "config" / "release_package.yaml").read_text(encoding="utf-8"))
require(isinstance(payload, dict), "release package catalog must be a mapping")
require(payload.get("schema_version") == "release_package_v1", "unexpected release package schema")
require(payload.get("package_name") == "land-diligence", "package name mismatch")
require(payload.get("output_dir") == "local_artifacts/releases", "release output dir must stay local")
require(payload.get("manifest_filename") == "release-manifest.json", "release manifest filename mismatch")
includes = set(require_list(payload, "include_paths"))
require(REQUIRED_INCLUDES.issubset(includes), f"missing release includes: {sorted(REQUIRED_INCLUDES - includes)}")
for include in includes:
    require_existing(include)
    require(include != ".git" and not include.startswith(".git/"), "release package must not include .git")
    require(not include.startswith("local_artifacts"), "release package must not include local_artifacts")
    require(not include.startswith("worktrees"), "release package must not include worktrees")
exclude_parts = set(require_list(payload, "exclude_path_parts"))
require(
    REQUIRED_EXCLUDE_PARTS.issubset(exclude_parts),
    f"missing release excludes: {sorted(REQUIRED_EXCLUDE_PARTS - exclude_parts)}",
)
suffixes = set(require_list(payload, "exclude_suffixes"))
require({".pyc", ".pyo", ".tmp", ".bak"}.issubset(suffixes), "missing generated-file suffix excludes")
gates = set(require_list(payload, "required_release_gates"))
for gate in gates:
    require_existing(gate)
require("scripts/verify.ps1" in gates, "release package must require verify gate")
require("scripts/run_release_readiness_check.ps1" in gates, "release package must require release readiness gate")

for script_name in ("build_release_package.ps1", "build_release_package.sh"):
    text = (ROOT / "scripts" / script_name).read_text(encoding="utf-8")
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

runbook = (ROOT / "docs" / "runbooks" / "release_package.md").read_text(encoding="utf-8")
for phrase in (
    "run_release_package_check.ps1",
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
PY

echo "release package check: ok"
