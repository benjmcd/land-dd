from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ci_has_supply_chain_scan_job() -> None:
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8",
    )
    ci = yaml.safe_load(ci_text)
    job = ci["jobs"]["supply-chain"]
    steps_text = "\n".join(
        str(step.get("uses", "")) + "\n" + str(step.get("run", ""))
        for step in job["steps"]
    )

    assert job["permissions"]["contents"] == "read"
    assert "actions/checkout@v4" in steps_text
    assert "actions/setup-python@v5" in steps_text
    assert "python-version: '3.12'" in ci_text
    assert "./scripts/run_provenance_check.sh" in steps_text
    assert 'python -m pip install -e "backend[dev]"' in steps_text
    assert "python -m pip install pip-audit" in steps_text
    assert "pip-audit --local" in steps_text


def test_ci_has_dependency_attestation_job() -> None:
    ci = yaml.safe_load(
        (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"),
    )
    job = ci["jobs"]["dependency-attestations"]
    steps_text = "\n".join(
        str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in job["steps"]
    )

    assert job["permissions"]["contents"] == "read"
    assert job["permissions"]["id-token"] == "write"
    assert job["permissions"]["attestations"] == "write"
    assert job["permissions"]["artifact-metadata"] == "write"
    assert "./scripts/run_provenance_check.sh" in steps_text
    assert steps_text.count("actions/attest@v4") == 2
    assert "backend/requirements-prod.lock" in steps_text
    assert "docs/sbom/backend-prod-sbom.json" in steps_text
    assert "'sbom-path': 'docs/sbom/backend-prod-sbom.json'" in steps_text


def test_dependabot_covers_actions_and_backend_python_dependencies() -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"),
    )

    assert payload["version"] == 2
    ecosystems = {
        (entry["package-ecosystem"], entry["directory"])
        for entry in payload["updates"]
    }
    assert ("github-actions", "/") in ecosystems
    assert ("pip", "/backend") in ecosystems


def test_supply_chain_runbook_records_validation_and_limits() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "supply_chain.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "pip-audit --local",
        "run_supply_chain_check.ps1",
        ".github/dependabot.yml",
        "backend/requirements-prod.lock",
        "docs/sbom/backend-prod-sbom.json",
        "run_provenance_check.ps1",
        "dependency-attestations",
        "actions/attest@v4",
        "container-image-scan",
        "docs/runbooks/container_image_scan.md",
        "docs/runbooks/incident_response.md",
        "attached attestation",
        "base-image packages",
    ):
        assert phrase in runbook
