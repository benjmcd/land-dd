from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_IDS = {"report_runs", "evidence_observations", "audit_events", "source_ingest_runs"}
REQUIRED_FIELDS = {"id", "description", "retention_period", "deletion_approach", "blocker"}
REQUIRED_AUTOMATION_TARGET_CLASSES = {"audit_events", "api_key_audit_events"}
REQUIRED_AUTOMATION_EVENT_TYPES = {"api_key_auth", "created", "superseded"}
REQUIRED_AUTOMATION_APPLY_GATES = {
    "--apply",
    "backup_or_export",
    "security_reviewer_approval",
    "state_worklog_entry",
}


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


def test_data_retention_catalog_records_repo_local_schedule_contract() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"),
    )
    plan = catalog["automation_plan"]

    assert plan["status"] == "repo_local_schedule_contract"
    assert plan["runner"] == "scripts/purge_audit_events.py"
    assert plan["windows_dry_run_wrapper"] == "scripts/run_purge_audit_events.ps1"
    assert plan["posix_dry_run_wrapper"] == "scripts/run_purge_audit_events.sh"
    assert plan["cadence"] == "weekly"
    assert plan["mode"] == "dry_run_by_default"
    assert set(plan["target_retention_classes"]) == REQUIRED_AUTOMATION_TARGET_CLASSES
    assert set(plan["target_event_types"]) == REQUIRED_AUTOMATION_EVENT_TYPES
    assert REQUIRED_AUTOMATION_APPLY_GATES.issubset(set(plan["apply_requires"]))
    assert plan["hosted_scheduler_status"] == "blocked"
    assert plan["limits"]["validate_only_catalog"] is True
    assert plan["limits"]["deletes_by_default"] is False
    assert plan["limits"]["requires_explicit_apply"] is True
    assert plan["limits"]["writes_secrets"] is False


def test_data_retention_runbook_exists_and_mentions_90_days() -> None:
    runbook_path = REPO_ROOT / "docs" / "runbooks" / "data_retention.md"
    assert runbook_path.is_file()
    content = runbook_path.read_text(encoding="utf-8")
    assert "90" in content
    assert "repo-local audit retention schedule contract" in content
    assert "hosted scheduler is not provisioned" in content


def test_data_retention_runbook_documents_fail_closed_catalog_default() -> None:
    content = (REPO_ROOT / "docs" / "runbooks" / "data_retention.md").read_text(
        encoding="utf-8"
    )

    assert "The default retention window is" in content
    assert "read from that catalog" in content
    assert "fails closed" in content
    assert "unreadable or invalid" in content
    assert "`--retention-days`" in content
    assert "operator override" in content
    assert "Every purge validates `config/data_retention.yaml`" in content
    assert "after the catalog has validated" in content
    assert "falls back to 90 days if the YAML is unreadable" not in content
    assert "fallback if YAML is absent or unparseable" not in content


def test_data_retention_validation_and_purge_scripts_exist() -> None:
    assert (REPO_ROOT / "scripts" / "data_retention_check.py").is_file()
    assert (REPO_ROOT / "scripts" / "run_data_retention_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_data_retention_check.sh").is_file()
    assert (REPO_ROOT / "scripts" / "purge_audit_events.py").is_file()
    assert (REPO_ROOT / "scripts" / "run_purge_audit_events.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_purge_audit_events.sh").is_file()


def test_data_retention_validator_validates_purge_tooling() -> None:
    script = (REPO_ROOT / "scripts" / "data_retention_check.py").read_text(
        encoding="utf-8"
    )
    assert "purge_audit_events.py" in script
    assert "run_purge_audit_events.ps1" in script
    assert "run_purge_audit_events.sh" in script
    assert "audit purge tooling: exists and documented" in script
    assert "validate_automation_plan" in script
    assert "dry_run_by_default" in script
    assert "automation must not delete by default" in script


def test_data_retention_validator_guards_fail_closed_catalog_default() -> None:
    script = (REPO_ROOT / "scripts" / "data_retention_check.py").read_text(
        encoding="utf-8"
    )

    assert "validate_purge_default_retention_semantics" in script
    assert "validate_purge_runtime_contract" in script
    assert "expected_audit_retention_days" in script
    assert "retention_classes missing audit purge targets" in script
    assert "purge script event allowlist must match automation target event types" in script
    assert "explicit --retention-days must not bypass retention catalog validation" in script
    assert "explicit --retention-days with missing catalog must exit 1" in script
    assert "REQUIRED_PURGE_SCRIPT_FAIL_CLOSED_SNIPPETS" in script
    assert "DISALLOWED_PURGE_SCRIPT_FALLBACK_SNIPPETS" in script
    assert "_resolve_default_retention_days" in script
    assert "RetentionCatalogError" in script
    assert "default=None" in script
    assert "fails closed if invalid" in script
    assert "_DEFAULT_RETENTION_DAYS = 90  # fallback" in script
    assert "pass  # keep the hard-coded default" in script
    assert "purge script must fail closed when catalog retention cannot be read" in script
    assert "explicit --retention-days override" in script
    assert "validate_purge_default_retention_semantics()" in script


def test_data_retention_wrappers_delegate_to_shared_validator() -> None:
    for script_name in ("run_data_retention_check.ps1", "run_data_retention_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "data_retention_check.py" in script


def test_data_retention_posix_check_honors_python_bin() -> None:
    script = (REPO_ROOT / "scripts" / "run_data_retention_check.sh").read_text(
        encoding="utf-8"
    )
    assert 'PYTHON_BIN="${PYTHON_BIN:-python}"' in script
    assert '"$PYTHON_BIN" ./scripts/data_retention_check.py' in script


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
