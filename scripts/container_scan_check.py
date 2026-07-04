from __future__ import annotations


from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    ".github/workflows/ci.yml",
    "backend/Dockerfile",
    ".dockerignore",
    "docs/runbooks/container_image_scan.md",
    "scripts/container_scan_check.py",
    "scripts/run_container_scan_check.ps1",
    "scripts/run_container_scan_check.sh",
)
PINNED_BASE = (
    "FROM python:3.12-slim@"
    "sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203 AS runtime"
)
DOCKERIGNORE_REQUIRED = (
    ".git",
    ".omc",
    "archive",
    "local_artifacts",
    "worktrees",
    "backend/tests",
    "docs/planning_pack",
)
RUNBOOK_REQUIRED_PHRASES = (
    "container-image-scan",
    "Docker Scout",
    "DOCKERHUB_USERNAME",
    "DOCKERHUB_TOKEN",
    "backend/Dockerfile",
    "scripts/container_scan_check.py",
    "local://land-diligence-backend:${{ github.sha }}",
    "critical and high severity CVEs",
    "exit-code: true",
    "python:3.12-slim",
    "sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203",
    "pinned base image digest",
    "signed image SBOM",
    "SLSA provenance attestation",
    "docs/runbooks/incident_response.md",
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
            f"required container-scan artifact missing: {path_text}",
        )


def text_from_steps(job: dict[str, Any]) -> str:
    steps = job.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SystemExit("container-image-scan job has no steps")

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
        for step in steps
        if isinstance(step, dict)
    )


def validate_ci() -> None:
    ci = yaml.safe_load(read_text(".github/workflows/ci.yml"))
    require(isinstance(ci, dict), "ci workflow must be a mapping")
    ci = cast(dict[str, Any], ci)
    jobs = ci.get("jobs")
    require(isinstance(jobs, dict), "ci workflow jobs missing")
    jobs = cast(dict[str, Any], jobs)
    job = jobs.get("container-image-scan")
    require(isinstance(job, dict), "ci workflow missing container-image-scan job")
    job = cast(dict[str, Any], job)
    permissions = job.get("permissions")
    require(isinstance(permissions, dict), "container-image-scan permissions missing")
    permissions = cast(dict[str, Any], permissions)
    require(
        permissions.get("contents") == "read",
        "container-image-scan must use read-only contents permission",
    )

    steps_text = text_from_steps(job)
    for phrase, message in (
        ("actions/checkout@v7", "container-image-scan job must checkout repo"),
        ("Check Docker Scout entitlement", "container-image-scan job must check entitlement"),
        (
            "Docker Scout entitlement is not configured for this repository.",
            "container-image-scan job must record blocked entitlement",
        ),
        (
            "docker build -f backend/Dockerfile -t land-diligence-backend:${{ github.sha }} .",
            "container-image-scan job must build backend image from backend/Dockerfile",
        ),
        ("docker/scout-action@v1", "container-image-scan job must use Docker Scout action"),
        (
            "'dockerhub-user': '${{ secrets.DOCKERHUB_USERNAME }}'",
            "Docker Scout must use configured Docker Hub username secret",
        ),
        (
            "'dockerhub-password': '${{ secrets.DOCKERHUB_TOKEN }}'",
            "Docker Scout must use configured Docker Hub token secret",
        ),
        (
            "local://land-diligence-backend:${{ github.sha }}",
            "Docker Scout must scan the locally built backend image",
        ),
    ):
        require(phrase in steps_text, message)

    require(
        "'command': 'cves'" in steps_text or '"command": "cves"' in steps_text,
        "Docker Scout command must be cves",
    )
    require(
        "'only-severities': 'critical,high'" in steps_text
        or '"only-severities": "critical,high"' in steps_text,
        "Docker Scout must be scoped to critical/high severities",
    )
    require(
        "'exit-code': True" in steps_text or '"exit-code": true' in steps_text,
        "Docker Scout must fail closed",
    )


def validate_docker_context() -> None:
    dockerfile = read_text("backend/Dockerfile")
    require(PINNED_BASE in dockerfile, "Dockerfile must pin python:3.12-slim by OCI index digest")
    require(
        dockerfile.count("\nFROM ") == 0,
        "Dockerfile must have one runtime stage for this scan proof",
    )

    dockerignore = read_text(".dockerignore").splitlines()
    ignored = {line.strip() for line in dockerignore if line.strip() and not line.startswith("#")}
    for entry in DOCKERIGNORE_REQUIRED:
        require(entry in ignored, f".dockerignore missing build-context exclusion: {entry}")


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/container_image_scan.md")
    for phrase in RUNBOOK_REQUIRED_PHRASES:
        require(phrase in runbook, f"container image scan runbook missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_ci()
    validate_docker_context()
    validate_runbook()
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
