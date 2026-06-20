from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_INCLUDES = {
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
    ".dockerignore",
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
REQUIRED_HANDOFF_SURFACES = {
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
    ".dockerignore",
}


def _catalog() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        yaml.safe_load(
            (REPO_ROOT / "config" / "release_package.yaml").read_text(encoding="utf-8"),
        ),
    )


def _load_builder() -> Any:
    spec = importlib.util.spec_from_file_location(
        "build_release_package",
        REPO_ROOT / "scripts" / "build_release_package.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _boundary_includes(path_text: str, catalog: dict[str, Any]) -> bool:
    path = Path(path_text)
    if path.parts and any(part in set(catalog["exclude_path_parts"]) for part in path.parts):
        return False
    if path.suffix in set(catalog["exclude_suffixes"]):
        return False
    for include_text in catalog["include_paths"]:
        include = Path(include_text)
        if path == include or include in path.parents:
            return True
    return False


def test_release_package_catalog_covers_local_package_boundary() -> None:
    catalog = _catalog()

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
    assert REQUIRED_EXCLUDE_PARTS.issubset(set(catalog["exclude_path_parts"]))
    assert {"scripts/verify.ps1", "scripts/run_release_readiness_check.ps1"}.issubset(
        set(catalog["required_release_gates"]),
    )
    assert ".log" in set(catalog["exclude_suffixes"])


def test_release_package_builder_file_list_excludes_local_state() -> None:
    catalog = _catalog()
    builder = _load_builder()
    release_files = builder.iter_release_files(
        catalog["include_paths"],
        set(catalog["exclude_path_parts"]),
        set(catalog["exclude_suffixes"]),
    )

    for path in release_files:
        relative = path.relative_to(REPO_ROOT)
        assert not (set(relative.parts) & REQUIRED_EXCLUDE_PARTS), relative.as_posix()
        assert relative.suffix not in set(catalog["exclude_suffixes"]), relative.as_posix()


def test_release_package_builder_filters_ignored_state_under_included_dirs(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    builder = _load_builder()
    source_file = tmp_path / "backend" / "app" / "connectors" / "live.py"
    local_state_file = (
        tmp_path
        / "backend"
        / "app"
        / "connectors"
        / ".omc"
        / "state"
        / "session.json"
    )
    source_file.parent.mkdir(parents=True)
    local_state_file.parent.mkdir(parents=True)
    source_file.write_text("VALUE = 1\n", encoding="utf-8")
    local_state_file.write_text('{"local": true}\n', encoding="utf-8")

    monkeypatch.setattr(builder, "ROOT", tmp_path)
    release_files = builder.iter_release_files(["backend/app"], {".omc"}, set())
    relative_paths = {path.relative_to(tmp_path).as_posix() for path in release_files}

    assert "backend/app/connectors/live.py" in relative_paths
    assert "backend/app/connectors/.omc/state/session.json" not in relative_paths


def test_release_package_boundary_carries_handoff_authority_and_fixture_root() -> None:
    catalog = _catalog()
    operator_manifest = json.loads(
        (REPO_ROOT / "backend" / "app" / "operator_cases" / "manifest.json").read_text(
            encoding="utf-8",
        ),
    )

    for path_text in REQUIRED_HANDOFF_SURFACES:
        assert (REPO_ROOT / path_text).exists()
        assert _boundary_includes(path_text, catalog), path_text
    assert _boundary_includes(operator_manifest["source_fixture_root"], catalog)
    if "scripts/verify.ps1" in catalog["required_release_gates"]:
        assert _boundary_includes(
            "backend/tests",
            catalog,
        )


def test_release_package_boundary_excludes_volatile_inbox_and_keeps_verify_inputs() -> None:
    catalog = _catalog()

    assert not _boundary_includes("state/agent-inbox", catalog)
    assert not _boundary_includes("state/agent-inbox/for-codex.md", catalog)
    assert _boundary_includes("docs/planning_pack", catalog)
    assert _boundary_includes("docs/planning_pack/README.md", catalog)


def test_release_package_validator_guards_handoff_boundary_and_fixture_root() -> None:
    script = (REPO_ROOT / "scripts" / "release_package_check.py").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "validate_handoff_boundary",
        "source_fixture_root",
        "scripts/verify.ps1",
        "backend/tests",
        "state/agent-inbox",
        ".omc",
        "docs/planning_pack",
    ):
        assert phrase in script


def test_release_package_builder_creates_local_zip_manifest_without_delete_or_push() -> None:
    script = (REPO_ROOT / "scripts" / "build_release_package.py").read_text(
        encoding="utf-8",
    )
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


def test_release_package_builder_wrappers_delegate_to_shared_builder() -> None:
    for script_name in ("build_release_package.ps1", "build_release_package.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "build_release_package.py" in script


def test_release_package_manifest_checker_guards_built_artifacts() -> None:
    script = (REPO_ROOT / "scripts" / "package_manifest_check.py").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "release_package_manifest_v1",
        "zip_sha256",
        "embedded manifest",
        "undeclared entries",
        "pushes_registry_image",
        "creates_hosted_deployment",
        "includes_secrets",
        "boundary_includes_path",
    ):
        assert phrase in script
    assert "rmtree" not in script
    assert "unlink(" not in script
    assert "remove(" not in script


def test_release_package_manifest_checker_wrappers_delegate_to_shared_checker() -> None:
    for script_name in ("run_package_manifest_check.ps1", "run_package_manifest_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "package_manifest_check.py" in script


def test_release_package_runbook_records_validation_workflow_and_limits() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "release_package.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "run_release_package_check.ps1",
        "scripts/release_package_check.py",
        "scripts/build_release_package.py",
        "scripts/package_manifest_check.py",
        "validate-only",
        "build_release_package.ps1",
        "run_package_manifest_check.ps1",
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
        "post-build manifest verification",
    ):
        assert phrase in runbook


def test_release_package_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "build_release_package.py").is_file()
    assert (REPO_ROOT / "scripts" / "build_release_package.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "build_release_package.sh").is_file()
    assert (REPO_ROOT / "scripts" / "package_manifest_check.py").is_file()
    assert (REPO_ROOT / "scripts" / "release_package_check.py").is_file()
    assert (REPO_ROOT / "scripts" / "run_package_manifest_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_package_manifest_check.sh").is_file()
    assert (REPO_ROOT / "scripts" / "run_release_package_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_release_package_check.sh").is_file()


def test_release_package_wrappers_delegate_to_shared_validator() -> None:
    for script_name in ("run_release_package_check.ps1", "run_release_package_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "release_package_check.py" in script
