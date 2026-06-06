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


def test_incident_rollback_checks_reference_current_proof_scripts() -> None:
    powershell = (REPO_ROOT / "scripts" / "run_incident_rollback_check.ps1").read_text(
        encoding="utf-8",
    )
    posix = (REPO_ROOT / "scripts" / "run_incident_rollback_check.sh").read_text(
        encoding="utf-8",
    )

    for script in (powershell, posix):
        assert "docs" in script
        assert "runbooks" in script
        assert "incident_response.md" in script
        assert "run_deployment_smoke" in script
        assert "run_backup_restore_check" in script
        assert "source_readiness.py" in script
        assert "incident/rollback check: ok" in script
