from __future__ import annotations


from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    ".github/workflows/ci.yml",
    ".github/dependabot.yml",
    "backend/pyproject.toml",
    "backend/requirements-prod.lock",
    "docs/sbom/backend-prod-sbom.json",
    "docs/runbooks/supply_chain.md",
    "docs/runbooks/dependency_provenance.md",
    "docs/runbooks/container_image_scan.md",
    "scripts/supply_chain_check.py",
    "scripts/run_supply_chain_check.ps1",
    "scripts/run_supply_chain_check.sh",
)
REQUIRED_RUNBOOK_PHRASES = (
    "supply-chain",
    "pip-audit --local",
    ".github/dependabot.yml",
    "backend/requirements-prod.lock",
    "docs/sbom/backend-prod-sbom.json",
    "run_supply_chain_check.ps1",
    "scripts/supply_chain_check.py",
    "run_provenance_check.ps1",
    "dependency-attestations",
    "actions/attest@v4",
    "container-image-scan",
    "docs/runbooks/container_image_scan.md",
    "docs/runbooks/incident_response.md",
    "Known Limits",
    "attached attestation",
    "base-image packages",
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
            f"required supply-chain artifact missing: {path_text}",
        )


def text_from_steps(job: dict[str, Any], job_name: str) -> str:
    steps = job.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SystemExit(f"{job_name} job has no steps")

    return "\n".join(
        str(step.get("name", ""))
        + "\n"
        + str(step.get("uses", ""))
        + "\n"
        + str(step.get("if", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in steps
        if isinstance(step, dict)
    )


def validate_supply_chain_job(ci_text: str, jobs: dict[str, Any]) -> None:
    job = jobs.get("supply-chain")
    require(isinstance(job, dict), "ci workflow missing supply-chain job")
    job = cast(dict[str, Any], job)
    permissions = job.get("permissions")
    require(isinstance(permissions, dict), "supply-chain permissions missing")
    permissions = cast(dict[str, Any], permissions)
    require(
        permissions.get("contents") == "read",
        "supply-chain job must use read-only contents permission",
    )

    steps_text = text_from_steps(job, "supply-chain")
    for phrase, message in (
        ("actions/checkout@v7", "supply-chain job must checkout repo"),
        ("actions/setup-python@v6", "supply-chain job must setup Python"),
        ("python -m pip install PyYAML", "supply-chain job must install PyYAML"),
        (
            "./scripts/run_provenance_check.sh",
            "supply-chain job must validate dependency provenance",
        ),
        (
            'python -m pip install -e "backend[dev]"',
            "supply-chain job must install backend dev dependencies",
        ),
        ("python -m pip install pip-audit", "supply-chain job must install pip-audit"),
        ("pip-audit --local", "supply-chain job must run pip-audit --local"),
    ):
        require(phrase in steps_text, message)
    require("python-version: '3.12'" in ci_text, "supply-chain job must use Python 3.12")


def validate_dependency_attestation_job(jobs: dict[str, Any]) -> None:
    attest_job = jobs.get("dependency-attestations")
    require(isinstance(attest_job, dict), "ci workflow missing dependency-attestations job")
    attest_job = cast(dict[str, Any], attest_job)
    attest_permissions = attest_job.get("permissions")
    require(isinstance(attest_permissions, dict), "dependency-attestations permissions missing")
    attest_permissions = cast(dict[str, Any], attest_permissions)
    require(
        attest_permissions.get("contents") == "read",
        "dependency-attestations contents permission must be read",
    )
    require(
        attest_permissions.get("id-token") == "write",
        "dependency-attestations id-token permission must be write",
    )
    require(
        attest_permissions.get("attestations") == "write",
        "dependency-attestations attestations permission must be write",
    )
    require(
        attest_permissions.get("artifact-metadata") == "write",
        "dependency-attestations artifact-metadata permission must be write",
    )

    attest_steps = text_from_steps(attest_job, "dependency-attestations")
    require(
        "./scripts/run_provenance_check.sh" in attest_steps,
        "dependency-attestations must validate provenance",
    )
    require(
        attest_steps.count("actions/attest@v4") == 2,
        "dependency-attestations must use actions/attest@v4 twice",
    )
    require(
        "backend/requirements-prod.lock" in attest_steps,
        "dependency-attestations missing lock subject",
    )
    require(
        "docs/sbom/backend-prod-sbom.json" in attest_steps,
        "dependency-attestations missing SBOM path",
    )
    require(
        "'sbom-path': 'docs/sbom/backend-prod-sbom.json'" in attest_steps,
        "dependency-attestations missing SBOM attestation",
    )


def validate_ci() -> None:
    ci_text = read_text(".github/workflows/ci.yml")
    ci = yaml.safe_load(ci_text)
    require(isinstance(ci, dict), "ci workflow must be a mapping")
    ci = cast(dict[str, Any], ci)
    jobs = ci.get("jobs")
    require(isinstance(jobs, dict), "ci workflow jobs missing")
    jobs = cast(dict[str, Any], jobs)
    validate_supply_chain_job(ci_text, jobs)
    validate_dependency_attestation_job(jobs)


def validate_dependabot() -> None:
    payload = yaml.safe_load(read_text(".github/dependabot.yml"))
    require(isinstance(payload, dict), "dependabot config must be a mapping")
    payload = cast(dict[str, Any], payload)
    require(payload.get("version") == 2, "dependabot config must use version 2")
    updates = payload.get("updates")
    if not isinstance(updates, list) or not updates:
        raise SystemExit("dependabot updates missing")

    ecosystems = {
        (entry.get("package-ecosystem"), entry.get("directory"))
        for entry in updates
        if isinstance(entry, dict)
    }
    require(("github-actions", "/") in ecosystems, "dependabot must cover GitHub Actions")
    require(("pip", "/backend") in ecosystems, "dependabot must cover backend Python dependencies")


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/supply_chain.md")
    for phrase in REQUIRED_RUNBOOK_PHRASES:
        require(phrase in runbook, f"supply-chain runbook missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_ci()
    validate_dependabot()
    validate_runbook()
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
