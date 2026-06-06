$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$requiredFiles = @(
    '.github\workflows\ci.yml',
    '.github\dependabot.yml',
    'backend\pyproject.toml',
    'backend\requirements-prod.lock',
    'docs\sbom\backend-prod-sbom.json',
    'docs\runbooks\supply_chain.md',
    'docs\runbooks\dependency_provenance.md',
    'docs\runbooks\container_image_scan.md'
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -Path (Join-Path $root $file) -PathType Leaf)) {
        throw "required supply-chain artifact missing: $file"
    }
}

$python = @'
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def text_from_steps(job: dict[str, Any], job_name: str) -> str:
    steps = job.get("steps")
    require(isinstance(steps, list) and steps, f"{job_name} job has no steps")
    return "\n".join(
        str(step.get("uses", "")) + "\n" + str(step.get("run", "")) + "\n" + str(step.get("with", ""))
        for step in steps
        if isinstance(step, dict)
    )


def validate_ci() -> None:
    ci = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    require(isinstance(ci, dict), "ci workflow must be a mapping")
    jobs = ci.get("jobs")
    require(isinstance(jobs, dict), "ci workflow jobs missing")
    job = jobs.get("supply-chain")
    require(isinstance(job, dict), "ci workflow missing supply-chain job")
    permissions = job.get("permissions")
    require(isinstance(permissions, dict), "supply-chain permissions missing")
    require(permissions.get("contents") == "read", "supply-chain job must use read-only contents permission")
    steps_text = text_from_steps(job, "supply-chain")
    require("actions/checkout@v6" in steps_text, "supply-chain job must checkout repo")
    require("actions/setup-python@v6" in steps_text, "supply-chain job must setup Python")
    require("python-version: '3.12'" in (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"), "supply-chain job must use Python 3.12")
    require("./scripts/run_provenance_check.sh" in steps_text, "supply-chain job must validate dependency provenance")
    require('python -m pip install -e "backend[dev]"' in steps_text, "supply-chain job must install backend dev dependencies")
    require("python -m pip install pip-audit" in steps_text, "supply-chain job must install pip-audit")
    require("pip-audit --local" in steps_text, "supply-chain job must run pip-audit --local")
    attest_job = jobs.get("dependency-attestations")
    require(isinstance(attest_job, dict), "ci workflow missing dependency-attestations job")
    attest_permissions = attest_job.get("permissions")
    require(isinstance(attest_permissions, dict), "dependency-attestations permissions missing")
    require(attest_permissions.get("contents") == "read", "dependency-attestations contents permission must be read")
    require(attest_permissions.get("id-token") == "write", "dependency-attestations id-token permission must be write")
    require(attest_permissions.get("attestations") == "write", "dependency-attestations attestations permission must be write")
    require(
        attest_permissions.get("artifact-metadata") == "write",
        "dependency-attestations artifact-metadata permission must be write",
    )
    attest_steps = text_from_steps(attest_job, "dependency-attestations")
    require("./scripts/run_provenance_check.sh" in attest_steps, "dependency-attestations must validate provenance")
    require(attest_steps.count("actions/attest@v4") == 2, "dependency-attestations must use actions/attest@v4 twice")
    require("backend/requirements-prod.lock" in attest_steps, "dependency-attestations missing lock subject")
    require("docs/sbom/backend-prod-sbom.json" in attest_steps, "dependency-attestations missing SBOM path")
    require(
        "'sbom-path': 'docs/sbom/backend-prod-sbom.json'" in attest_steps,
        "dependency-attestations missing SBOM attestation",
    )


def validate_dependabot() -> None:
    payload = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "dependabot config must be a mapping")
    require(payload.get("version") == 2, "dependabot config must use version 2")
    updates = payload.get("updates")
    require(isinstance(updates, list) and updates, "dependabot updates missing")
    ecosystems = {
        (entry.get("package-ecosystem"), entry.get("directory"))
        for entry in updates
        if isinstance(entry, dict)
    }
    require(("github-actions", "/") in ecosystems, "dependabot must cover GitHub Actions")
    require(("pip", "/backend") in ecosystems, "dependabot must cover backend Python dependencies")


def validate_runbook() -> None:
    runbook = (ROOT / "docs" / "runbooks" / "supply_chain.md").read_text(encoding="utf-8")
    for phrase in (
        "supply-chain",
        "pip-audit --local",
        ".github/dependabot.yml",
        "backend/requirements-prod.lock",
        "docs/sbom/backend-prod-sbom.json",
        "run_provenance_check.ps1",
        "dependency-attestations",
        "actions/attest@v4",
        "container-image-scan",
        "docs/runbooks/container_image_scan.md",
        "docs/runbooks/incident_response.md",
        "Known Limits",
        "attached attestation",
        "base-image packages",
    ):
        require(phrase in runbook, f"supply-chain runbook missing phrase: {phrase}")


def main() -> int:
    validate_ci()
    validate_dependabot()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@

$python | py -3.12 -
if ($LASTEXITCODE -ne 0) {
    throw "supply-chain configuration validation failed with exit code $LASTEXITCODE"
}

Write-Host 'supply-chain check: ok'
