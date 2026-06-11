from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "docs/runbooks/incident_response.md",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_deployment_smoke.sh",
    "scripts/run_backup_restore_check.ps1",
    "scripts/run_backup_restore_check.sh",
    "scripts/verify.ps1",
    "scripts/verify.sh",
    "scripts/source_readiness.py",
    "scripts/incident_rollback_check.py",
    "scripts/run_incident_rollback_check.ps1",
    "scripts/run_incident_rollback_check.sh",
)
REQUIRED_PHRASES = (
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
    "run_deployment_smoke.ps1",
    "run_backup_restore_check.ps1",
    "source_readiness.py",
    "ENABLE_LIVE_CONNECTORS=false",
    "scripts/incident_rollback_check.py",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require(
            (ROOT / path_text).is_file(),
            f"required incident/rollback artifact missing: {path_text}",
        )


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/incident_response.md")
    for phrase in REQUIRED_PHRASES:
        require(
            phrase in runbook,
            f"incident response runbook missing required phrase: {phrase}",
        )


def validate_docker_compose_config() -> None:
    if shutil.which("docker") is None:
        print("incident/rollback check: docker unavailable; compose config skipped")
        return

    subprocess.run(
        ["docker", "compose", "config", "--quiet"],
        cwd=ROOT,
        check=True,
    )


def validate_source_readiness() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    require(isinstance(payload, dict), "source readiness JSON must be a mapping")
    payload = cast(dict[str, Any], payload)
    require(
        payload.get("schema_version") == "source_readiness_v1",
        "source readiness JSON did not return source_readiness_v1",
    )
    source_count = payload.get("source_count", 0)
    require(
        isinstance(source_count, int),
        "source readiness source_count must be an integer",
    )
    require(source_count >= 1, "source readiness JSON returned no sources")


def main() -> int:
    validate_required_files()
    validate_runbook()
    validate_docker_compose_config()
    validate_source_readiness()
    print("incident/rollback check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
