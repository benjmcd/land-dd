from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
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


def test_release_package_catalog_covers_local_package_boundary() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "release_package.yaml").read_text(encoding="utf-8"),
    )

    assert catalog["schema_version"] == "release_package_v1"
    assert catalog["package_name"] == "land-diligence"
    assert catalog["output_dir"] == "local_artifacts/releases"
    assert catalog["manifest_filename"] == "release-manifest.json"
    assert REQUIRED_INCLUDES.issubset(set(catalog["include_paths"]))
    for include in catalog["include_paths"]:
        assert (REPO_ROOT / include).exists()
        assert include != ".git"
        assert not include.startswith(".git/")
        assert not include.startswith("local_artifacts")
        assert not include.startswith("worktrees")
    assert {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        "__pycache__",
        "local_artifacts",
        "worktrees",
    }.issubset(set(catalog["exclude_path_parts"]))
    assert {"scripts/verify.ps1", "scripts/run_release_readiness_check.ps1"}.issubset(
        set(catalog["required_release_gates"]),
    )


def test_release_package_builders_create_local_zip_manifest_without_delete_or_push() -> None:
    for script_name in ("build_release_package.ps1", "build_release_package.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
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
            assert phrase in script
        assert "rmtree" not in script
        assert "unlink(" not in script
        assert "remove(" not in script


def test_release_package_runbook_records_validation_workflow_and_limits() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "release_package.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "run_release_package_check.ps1",
        "validate-only",
        "build_release_package.ps1",
        "local_artifacts/releases",
        "fails if either output already exists",
        "does not delete, overwrite, push, deploy, or publish",
        "No registry image is pushed",
        "No hosted deployment",
        "out of scope for local-only release",
        "current worktree",
    ):
        assert phrase in runbook


def test_release_package_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "build_release_package.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "build_release_package.sh").is_file()
    assert (REPO_ROOT / "scripts" / "run_release_package_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_release_package_check.sh").is_file()
