"""Tests that verify the security scan artifacts (scripts, runbook) exist and are correct."""

from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


def test_run_security_scan_ps1_exists() -> None:
    script = REPO_ROOT / "scripts" / "run_security_scan.ps1"
    assert script.exists(), f"Expected {script} to exist"
    assert script.is_file(), f"Expected {script} to be a file"


def test_run_security_scan_sh_exists() -> None:
    script = REPO_ROOT / "scripts" / "run_security_scan.sh"
    assert script.exists(), f"Expected {script} to exist"
    assert script.is_file(), f"Expected {script} to be a file"


def test_security_scan_runbook_exists_and_mentions_bandit() -> None:
    runbook = REPO_ROOT / "docs" / "runbooks" / "security_scan.md"
    assert runbook.exists(), f"Expected {runbook} to exist"
    content = runbook.read_text(encoding="utf-8")
    assert "bandit" in content.lower(), "security_scan.md must mention 'bandit'"


def test_security_scan_runbook_mentions_high_or_critical() -> None:
    runbook = REPO_ROOT / "docs" / "runbooks" / "security_scan.md"
    assert runbook.exists(), f"Expected {runbook} to exist"
    content = runbook.read_text(encoding="utf-8")
    assert "HIGH" in content or "CRITICAL" in content, (
        "security_scan.md must mention 'HIGH' or 'CRITICAL' severity threshold"
    )


def test_security_scan_runbook_mentions_validate_only() -> None:
    runbook = REPO_ROOT / "docs" / "runbooks" / "security_scan.md"
    assert runbook.exists(), f"Expected {runbook} to exist"
    content = runbook.read_text(encoding="utf-8")
    assert "--validate-only" in content or "validate-only" in content, (
        "security_scan.md must document the --validate-only / validate-only flag"
    )


def test_security_scan_ci_uses_repo_wrapper() -> None:
    workflow = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    content = workflow.read_text(encoding="utf-8")
    assert "security-scan:" in content
    assert "run: ./scripts/run_security_scan.sh" in content
