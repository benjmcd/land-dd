$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$requiredFiles = @(
    '.github\workflows\ci.yml',
    'backend\Dockerfile',
    '.dockerignore',
    'docs\runbooks\container_image_scan.md'
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -Path (Join-Path $root $file) -PathType Leaf)) {
        throw "required container-scan artifact missing: $file"
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


def text_from_steps(job: dict[str, Any]) -> str:
    steps = job.get("steps")
    require(isinstance(steps, list) and steps, "container-image-scan job has no steps")
    return "\n".join(
        str(step.get("uses", "")) + "\n" + str(step.get("run", "")) + "\n" + str(step.get("with", ""))
        for step in steps
        if isinstance(step, dict)
    )


def validate_ci() -> None:
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    ci = yaml.safe_load(ci_text)
    require(isinstance(ci, dict), "ci workflow must be a mapping")
    jobs = ci.get("jobs")
    require(isinstance(jobs, dict), "ci workflow jobs missing")
    job = jobs.get("container-image-scan")
    require(isinstance(job, dict), "ci workflow missing container-image-scan job")
    permissions = job.get("permissions")
    require(isinstance(permissions, dict), "container-image-scan permissions missing")
    require(permissions.get("contents") == "read", "container-image-scan must use read-only contents permission")
    steps_text = text_from_steps(job)
    require("actions/checkout@v4" in steps_text, "container-image-scan job must checkout repo")
    require(
        "docker build -f backend/Dockerfile -t land-diligence-backend:${{ github.sha }} ." in steps_text,
        "container-image-scan job must build backend image from backend/Dockerfile",
    )
    require("docker/scout-action@v1" in steps_text, "container-image-scan job must use Docker Scout action")
    require("'command': 'cves'" in steps_text or '"command": "cves"' in steps_text, "Docker Scout command must be cves")
    require(
        "local://land-diligence-backend:${{ github.sha }}" in steps_text,
        "Docker Scout must scan the locally built backend image",
    )
    require(
        "'only-severities': 'critical,high'" in steps_text or '"only-severities": "critical,high"' in steps_text,
        "Docker Scout must be scoped to critical/high severities",
    )
    require("'exit-code': True" in steps_text or '"exit-code": true' in steps_text, "Docker Scout must fail closed")


def validate_docker_context() -> None:
    dockerfile = (ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
    pinned_base = (
        "FROM python:3.12-slim@"
        "sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203 AS runtime"
    )
    require(pinned_base in dockerfile, "Dockerfile must pin python:3.12-slim by OCI index digest")
    require(dockerfile.count("\nFROM ") == 0, "Dockerfile must have one runtime stage for this scan proof")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    ignored = {line.strip() for line in dockerignore if line.strip() and not line.startswith("#")}
    for entry in (".git", ".omc", "archive", "local_artifacts", "worktrees", "backend/tests", "docs/planning_pack"):
        require(entry in ignored, f".dockerignore missing build-context exclusion: {entry}")


def validate_runbook() -> None:
    runbook = (ROOT / "docs" / "runbooks" / "container_image_scan.md").read_text(encoding="utf-8")
    for phrase in (
        "container-image-scan",
        "Docker Scout",
        "backend/Dockerfile",
        "local://land-diligence-backend:${{ github.sha }}",
        "critical and high severity CVEs",
        "exit-code: true",
        "python:3.12-slim",
        "sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203",
        "pinned base image digest",
        "signed image SBOM",
        "SLSA provenance attestation",
        "out of scope for local-only operation",
        "docs/runbooks/incident_response.md",
    ):
        require(phrase in runbook, f"container image scan runbook missing phrase: {phrase}")


def main() -> int:
    validate_ci()
    validate_docker_context()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@

$python | py -3.12 -
if ($LASTEXITCODE -ne 0) {
    throw "container image scan configuration validation failed with exit code $LASTEXITCODE"
}

Write-Host 'container image scan check: ok'
