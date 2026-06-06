$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$requiredFiles = @(
    'config\release_readiness.yaml',
    'config\release_package.yaml',
    'config\image_publication.yaml',
    'config\hosted_deployment.yaml',
    'docs\runbooks\release_readiness.md',
    'docs\runbooks\release_package.md',
    'docs\runbooks\image_publication.md',
    'docs\runbooks\hosted_deployment.md',
    '.github\workflows\ci.yml',
    'backend\pyproject.toml',
    'backend\requirements-prod.lock',
    'backend\Dockerfile',
    'docker-compose.yml',
    'docs\sbom\backend-prod-sbom.json',
    'scripts\verify.ps1',
    'scripts\verify.sh',
    'scripts\run_deployment_smoke.ps1',
    'scripts\run_provenance_check.ps1',
    'scripts\run_supply_chain_check.ps1',
    'scripts\run_container_scan_check.ps1',
    'scripts\run_release_package_check.ps1',
    'scripts\run_image_publication_check.ps1',
    'scripts\run_hosted_deployment_check.ps1',
    'scripts\source_readiness.py'
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -Path (Join-Path $root $file) -PathType Leaf)) {
        throw "required release-readiness artifact missing: $file"
    }
}

$python = @'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
REQUIRED_CHECKS = {
    "workspace_verify",
    "db_verify",
    "deployment_smoke",
    "dependency_provenance",
    "supply_chain_scan",
    "container_image_scan",
    "backup_restore",
    "incident_rollback",
    "alert_rules",
    "cost_monitoring",
    "access_control",
    "release_package",
    "image_publication",
    "hosted_deployment",
    "source_readiness",
}
REQUIRED_CI_JOBS = {
    "verify",
    "db-verify",
    "supply-chain",
    "dependency-attestations",
    "container-image-scan",
    "access-control",
    "image-publication",
    "hosted-deployment",
    "release-readiness",
}
REQUIRED_BLOCKERS = {
    "hosted_deployment_attestation",
    "published_registry_image_attestation",
    "hosted_billing_reconciliation",
    "non_ready_must_sources",
    "full_user_auth_rbac",
    "hosted_alerting",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"referenced release artifact missing: {normalized}")


def step_text(job: dict[str, Any], job_name: str) -> str:
    steps = job.get("steps")
    require(isinstance(steps, list) and steps, f"{job_name} job has no steps")
    return "\n".join(
        str(step.get("uses", "")) + "\n" + str(step.get("run", "")) + "\n" + str(step.get("with", ""))
        for step in steps
        if isinstance(step, dict)
    )


def validate_catalog() -> None:
    payload = yaml.safe_load((ROOT / "config" / "release_readiness.yaml").read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "release readiness catalog must be a mapping")
    require(payload.get("schema_version") == "release_readiness_v1", "unexpected release readiness schema")
    require(payload.get("operator_runbook") == "docs/runbooks/release_readiness.md", "operator runbook mismatch")
    checks = payload.get("required_checks")
    require(isinstance(checks, list) and checks, "release readiness checks missing")
    check_ids = set()
    for check in checks:
        require(isinstance(check, dict), "each release readiness check must be a mapping")
        check_id = check.get("id")
        require(isinstance(check_id, str) and check_id, "release readiness check id missing")
        require(check_id not in check_ids, f"duplicate release readiness check id: {check_id}")
        check_ids.add(check_id)
        proof = check.get("proof")
        require(isinstance(proof, str) and proof, f"{check_id} proof missing")
        require_existing(proof)
    require(REQUIRED_CHECKS.issubset(check_ids), f"missing release checks: {sorted(REQUIRED_CHECKS - check_ids)}")
    blockers = payload.get("release_blockers")
    require(isinstance(blockers, list) and blockers, "release blockers missing")
    blocker_ids = set()
    for blocker in blockers:
        require(isinstance(blocker, dict), "each release blocker must be a mapping")
        blocker_id = blocker.get("id")
        require(isinstance(blocker_id, str) and blocker_id, "release blocker id missing")
        blocker_ids.add(blocker_id)
        require(blocker.get("status") == "blocked", f"{blocker_id} must remain blocked")
        authority = blocker.get("authority")
        require(isinstance(authority, str) and authority, f"{blocker_id} authority missing")
        require_existing(authority)
    require(REQUIRED_BLOCKERS.issubset(blocker_ids), f"missing release blockers: {sorted(REQUIRED_BLOCKERS - blocker_ids)}")


def validate_ci() -> None:
    ci = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    require(isinstance(ci, dict), "ci workflow must be a mapping")
    jobs = ci.get("jobs")
    require(isinstance(jobs, dict), "ci workflow jobs missing")
    require(REQUIRED_CI_JOBS.issubset(set(jobs)), f"missing CI jobs: {sorted(REQUIRED_CI_JOBS - set(jobs))}")
    job = jobs["release-readiness"]
    permissions = job.get("permissions")
    require(isinstance(permissions, dict), "release-readiness permissions missing")
    require(permissions.get("contents") == "read", "release-readiness must use read-only contents permission")
    text = step_text(job, "release-readiness")
    require("actions/checkout@v6" in text, "release-readiness job must checkout repo")
    require("actions/setup-python@v6" in text, "release-readiness job must setup Python")
    require("python-version: '3.12'" in (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"), "release-readiness job must use Python 3.12")
    require("python -m pip install PyYAML" in text, "release-readiness job must install PyYAML for static catalog parsing")
    require("./scripts/run_release_readiness_check.sh" in text, "release-readiness job must run POSIX release proof")
    image_job = jobs["image-publication"]
    image_permissions = image_job.get("permissions")
    require(isinstance(image_permissions, dict), "image-publication permissions missing")
    require(image_permissions.get("contents") == "read", "image-publication must use read-only contents permission")
    image_text = step_text(image_job, "image-publication")
    require("actions/checkout@v6" in image_text, "image-publication job must checkout repo")
    require("actions/setup-python@v6" in image_text, "image-publication job must setup Python")
    require("python -m pip install PyYAML" in image_text, "image-publication job must install PyYAML")
    require("./scripts/run_image_publication_check.sh" in image_text, "image-publication job must run POSIX image publication proof")
    hosted_job = jobs["hosted-deployment"]
    hosted_permissions = hosted_job.get("permissions")
    require(isinstance(hosted_permissions, dict), "hosted-deployment permissions missing")
    require(hosted_permissions.get("contents") == "read", "hosted-deployment must use read-only contents permission")
    hosted_text = step_text(hosted_job, "hosted-deployment")
    require("actions/checkout@v6" in hosted_text, "hosted-deployment job must checkout repo")
    require("actions/setup-python@v6" in hosted_text, "hosted-deployment job must setup Python")
    require("python -m pip install PyYAML" in hosted_text, "hosted-deployment job must install PyYAML")
    require("./scripts/run_hosted_deployment_check.sh" in hosted_text, "hosted-deployment job must run POSIX hosted deployment proof")


def validate_source_readiness() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    require(payload.get("source_count") == 8, "Must source count changed without release catalog update")
    require(payload.get("ready_count") == 4, "Must ready count changed without release catalog update")
    require(payload.get("blocked_count") == 4, "Must blocked count changed without release catalog update")
    blocked = {
        str(source.get("source_registry_id"))
        for source in payload.get("sources", [])
        if source.get("connector_ready") is False
    }
    require({"DS-010", "DS-011", "DS-017", "DS-023"}.issubset(blocked), "expected Must-source blockers missing")


def validate_runbook() -> None:
    runbook = (ROOT / "docs" / "runbooks" / "release_readiness.md").read_text(encoding="utf-8")
    for phrase in (
        "run_release_readiness_check.ps1",
        "validate-only",
        "verify",
        "db-verify",
        "supply-chain",
        "dependency-attestations",
        "container-image-scan",
        "access-control",
        "release-package",
        "image-publication",
        "hosted-deployment",
        "release-readiness",
        "sources=8 ready=4 blocked=4",
        "build_release_package.ps1",
        "run_image_publication_check.ps1",
        "run_hosted_deployment_check.ps1",
        "No container image is pushed",
        "published registry-image attestation",
    ):
        require(phrase in runbook, f"release readiness runbook missing phrase: {phrase}")


def main() -> int:
    validate_catalog()
    validate_ci()
    validate_source_readiness()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@

$python | py -3.12 -
if ($LASTEXITCODE -ne 0) {
    throw "release readiness validation failed with exit code $LASTEXITCODE"
}

Write-Host 'release readiness check: ok'
