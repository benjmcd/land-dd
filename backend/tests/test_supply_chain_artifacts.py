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
        str(step.get("name", ""))
        + "\n"
        + str(step.get("uses", ""))
        + "\n"
        + str(step.get("if", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in job["steps"]
    )

    assert job["permissions"]["contents"] == "read"
    assert "actions/checkout@v7" in steps_text
    assert "actions/setup-python@v6" in steps_text
    assert "python-version: '3.12'" in ci_text
    assert "python -m pip install PyYAML" in steps_text
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
        str(step.get("name", ""))
        + "\n"
        + str(step.get("uses", ""))
        + "\n"
        + str(step.get("if", ""))
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
    assert "actions/setup-python@v6" in steps_text
    assert "python -m pip install PyYAML" in steps_text
    assert "./scripts/run_provenance_check.sh" in steps_text
    assert "Check GitHub attestation entitlement" in steps_text
    assert "Dependency attestations blocked" in steps_text
    assert "steps.attestation-entitlement.outputs.enabled == 'true'" in steps_text
    assert steps_text.count("actions/attest@v4") == 2
    assert "create-storage-record" in steps_text
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
        "scripts/supply_chain_check.py",
        ".github/dependabot.yml",
        "backend/requirements-prod.lock",
        "docs/sbom/backend-prod-sbom.json",
        "run_provenance_check.ps1",
        "dependency-attestations",
        "actions/attest@v4",
        "Dependency attestations blocked",
        "container-image-scan",
        "docs/runbooks/container_image_scan.md",
        "docs/runbooks/incident_response.md",
        "attached attestation",
        "base-image packages",
    ):
        assert phrase in runbook


def test_supply_chain_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "supply_chain_check.py").is_file()
    assert (REPO_ROOT / "scripts" / "run_supply_chain_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_supply_chain_check.sh").is_file()


def test_supply_chain_wrappers_delegate_to_shared_validator() -> None:
    for script_name in ("run_supply_chain_check.ps1", "run_supply_chain_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "supply_chain_check.py" in script
