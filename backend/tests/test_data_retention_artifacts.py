from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_IDS = {"report_runs", "evidence_observations", "audit_events", "source_ingest_runs"}
REQUIRED_FIELDS = {"id", "description", "retention_period", "deletion_approach", "blocker"}


def test_data_retention_catalog_exists() -> None:
    assert (REPO_ROOT / "config" / "data_retention.yaml").is_file()


def test_data_retention_catalog_schema_version() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"),
    )
    assert catalog["schema_version"] == "data_retention_v1"


def test_data_retention_catalog_has_at_least_six_classes() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"),
    )
    classes = catalog["retention_classes"]
    assert isinstance(classes, list)
    assert len(classes) >= 6


def test_data_retention_classes_have_required_fields() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"),
    )
    for cls in catalog["retention_classes"]:
        missing = REQUIRED_FIELDS - set(cls.keys())
        cls_id = cls.get("id", "?")
        assert not missing, f"retention class {cls_id} missing fields: {sorted(missing)}"


def test_data_retention_catalog_includes_required_ids() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"),
    )
    ids = {cls["id"] for cls in catalog["retention_classes"]}
    missing = REQUIRED_IDS - ids
    assert not missing, f"retention_classes missing required ids: {sorted(missing)}"


def test_data_retention_runbook_exists_and_mentions_90_days() -> None:
    runbook_path = REPO_ROOT / "docs" / "runbooks" / "data_retention.md"
    assert runbook_path.is_file()
    content = runbook_path.read_text(encoding="utf-8")
    assert "90" in content


def test_data_retention_validation_and_purge_scripts_exist() -> None:
    assert (REPO_ROOT / "scripts" / "run_data_retention_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_data_retention_check.sh").is_file()
    assert (REPO_ROOT / "scripts" / "purge_audit_events.py").is_file()
    assert (REPO_ROOT / "scripts" / "run_purge_audit_events.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_purge_audit_events.sh").is_file()


def test_data_retention_checks_validate_purge_tooling() -> None:
    for script_name in ("run_data_retention_check.ps1", "run_data_retention_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
        assert "purge_audit_events.py" in script
        assert "run_purge_audit_events.ps1" in script
        assert "run_purge_audit_events.sh" in script
        assert "audit purge tooling: exists and documented" in script


def test_data_retention_posix_check_honors_python_bin() -> None:
    script = (REPO_ROOT / "scripts" / "run_data_retention_check.sh").read_text(
        encoding="utf-8"
    )
    assert 'PYTHON_BIN="${PYTHON_BIN:-python}"' in script
    assert '"$PYTHON_BIN" -c' in script
    assert '"$PYTHON_BIN" - <<' in script


def test_purge_wrappers_are_dry_run_by_default() -> None:
    powershell = (REPO_ROOT / "scripts" / "run_purge_audit_events.ps1").read_text(
        encoding="utf-8"
    )
    posix = (REPO_ROOT / "scripts" / "run_purge_audit_events.sh").read_text(
        encoding="utf-8"
    )
    assert "running dry-run" in powershell
    assert "running dry-run" in posix
    assert "scripts/purge_audit_events.py" in powershell
    assert "scripts/purge_audit_events.py" in posix
    for script in (powershell, posix):
        invocation_lines = [
            line
            for line in script.splitlines()
            if "scripts/purge_audit_events.py" in line
            and not line.strip().startswith(("Write-Host", "echo"))
        ]
        assert invocation_lines
        assert all("--apply" not in line for line in invocation_lines)
