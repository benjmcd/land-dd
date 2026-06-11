from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_incident_response_runbook_names_required_l10_ops_elements() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "incident_response.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "## Severity Levels",
        "## Ownership",
        "## Escalation",
        "## Rollback and Mitigation",
        "## Recovery Criteria",
        "SEV0",
        "SEV1",
        "Incident commander",
        "Deployment Rollback",
        "Database Rollback or Migration Mitigation",
        "Connector or Source Outage",
        "Queue or Report Failure",
    ):
        assert phrase in runbook


def test_incident_rollback_validation_scripts_exist() -> None:
    assert (REPO_ROOT / "scripts" / "incident_rollback_check.py").is_file()
    assert (REPO_ROOT / "scripts" / "run_incident_rollback_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_incident_rollback_check.sh").is_file()


def test_incident_rollback_validator_references_current_proof_scripts() -> None:
    script = (REPO_ROOT / "scripts" / "incident_rollback_check.py").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "docs",
        "runbooks",
        "incident_response.md",
        "run_deployment_smoke",
        "run_backup_restore_check",
        "source_readiness.py",
        "incident/rollback check: ok",
    ):
        assert phrase in script


def test_incident_rollback_wrappers_delegate_to_shared_validator() -> None:
    powershell = (REPO_ROOT / "scripts" / "run_incident_rollback_check.ps1").read_text(
        encoding="utf-8",
    )
    posix = (REPO_ROOT / "scripts" / "run_incident_rollback_check.sh").read_text(
        encoding="utf-8",
    )

    for script in (powershell, posix):
        assert "incident_rollback_check.py" in script
