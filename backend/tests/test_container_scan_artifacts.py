from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]


def _steps_text(job: dict[str, Any]) -> str:
    return "\n".join(
        str(step.get("name", ""))
        + "\n"
        + str(step.get("if", ""))
        + "\n"
        + str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in job["steps"]
    )


def test_ci_has_container_image_scan_job() -> None:
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8",
    )
    ci = yaml.safe_load(ci_text)
    job = ci["jobs"]["container-image-scan"]
    steps_text = _steps_text(job)

    assert job["permissions"]["contents"] == "read"
    assert "actions/checkout@v7" in steps_text
    assert (
        "docker build -f backend/Dockerfile -t land-diligence-backend:${{ github.sha }} ."
        in steps_text
    )
    assert "Check Docker Scout entitlement" in steps_text
    assert "Docker Scout entitlement is not configured for this repository." in steps_text
    assert "docker/scout-action@v1" in steps_text
    assert "'dockerhub-user': '${{ secrets.DOCKERHUB_USERNAME }}'" in steps_text
    assert "'dockerhub-password': '${{ secrets.DOCKERHUB_TOKEN }}'" in steps_text
    assert "'command': 'cves'" in steps_text or '"command": "cves"' in steps_text
    assert "local://land-diligence-backend:${{ github.sha }}" in steps_text
    assert (
        "'only-severities': 'critical,high'" in steps_text
        or '"only-severities": "critical,high"' in steps_text
    )
    assert "'exit-code': True" in steps_text or '"exit-code": true' in steps_text


def test_dockerfile_and_dockerignore_are_scan_ready() -> None:
    dockerfile = (REPO_ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    ignored = {line.strip() for line in dockerignore if line.strip() and not line.startswith("#")}
    pinned_base = (
        "FROM python:3.12-slim@"
        "sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203 AS runtime"
    )

    assert pinned_base in dockerfile
    assert dockerfile.count("\nFROM ") == 0
    for entry in (
        ".git",
        ".omc",
        "archive",
        "local_artifacts",
        "worktrees",
        "backend/tests",
        "docs/planning_pack",
    ):
        assert entry in ignored


def test_container_image_scan_runbook_records_validation_and_limits() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "container_image_scan.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "container-image-scan",
        "Docker Scout",
        "DOCKERHUB_USERNAME",
        "DOCKERHUB_TOKEN",
        "backend/Dockerfile",
        "scripts/container_scan_check.py",
        "local://land-diligence-backend:${{ github.sha }}",
        "critical and high severity CVEs",
        "exit-code: true",
        "blocked",
        "python:3.12-slim",
        "sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203",
        "pinned base image digest",
        "signed image SBOM",
        "SLSA provenance attestation",
        "docs/runbooks/incident_response.md",
    ):
        assert phrase in runbook


def test_container_image_scan_scripts_exist() -> None:
    for path in (
        REPO_ROOT / "scripts" / "container_scan_check.py",
        REPO_ROOT / "scripts" / "run_container_scan_check.ps1",
        REPO_ROOT / "scripts" / "run_container_scan_check.sh",
    ):
        assert path.is_file()


def test_container_image_scan_wrappers_delegate_to_shared_validator() -> None:
    for script_name in ("run_container_scan_check.ps1", "run_container_scan_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "container_scan_check.py" in script
