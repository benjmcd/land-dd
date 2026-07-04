from __future__ import annotations

import importlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = REPO_ROOT / "backend" / "requirements-prod.lock"
SBOM_PATH = REPO_ROOT / "docs" / "sbom" / "backend-prod-sbom.json"


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _lock_entries() -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    for raw in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(
            r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.!+-]+) --hash=sha256:([0-9a-f]{64})",
            line,
        )
        assert match is not None, line
        name, version, sha256 = match.groups()
        entries[_norm(name)] = (version, sha256)
    return entries


def test_production_lock_covers_declared_runtime_dependencies() -> None:
    pyproject = tomllib.loads(
        (REPO_ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8"),
    )
    direct = {
        _norm(re.split(r"[\[<>=!~ ]", dependency, maxsplit=1)[0])
        for dependency in pyproject["project"]["dependencies"]
    }
    lock = _lock_entries()

    assert direct.issubset(set(lock))
    assert {"uvicorn", "psycopg-binary", "httptools", "watchfiles", "websockets"}.issubset(
        set(lock),
    )
    assert len(lock) == 26


def test_backend_sbom_matches_production_lock() -> None:
    lock = _lock_entries()
    sbom = json.loads(SBOM_PATH.read_text(encoding="utf-8"))

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert sbom["metadata"]["component"]["name"] == "land-diligence-backend"
    assert sbom["metadata"]["component"]["version"] == "0.1.0"

    components = {}
    for component in sbom["components"]:
        digest = component["hashes"][0]
        assert digest["alg"] == "SHA-256"
        assert component["purl"].startswith("pkg:pypi/")
        components[_norm(component["name"])] = (component["version"], digest["content"])

    assert components == lock


def test_dependency_provenance_scripts_and_runbook_exist() -> None:
    for path in (
        REPO_ROOT / "scripts" / "provenance_check.py",
        REPO_ROOT / "scripts" / "run_provenance_check.ps1",
        REPO_ROOT / "scripts" / "run_provenance_check.sh",
        REPO_ROOT / "docs" / "runbooks" / "dependency_provenance.md",
    ):
        assert path.is_file()

    runbook = (REPO_ROOT / "docs" / "runbooks" / "dependency_provenance.md").read_text(
        encoding="utf-8",
    )
    for phrase in (
        "backend/requirements-prod.lock",
        "docs/sbom/backend-prod-sbom.json",
        "run_provenance_check.ps1",
        "scripts/provenance_check.py",
        "dependency-attestations",
        "actions/attest@v4",
        "SBOM attestation",
    ):
        assert phrase in runbook


def test_ci_attests_dependency_provenance_artifacts() -> None:
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
    assert "actions/checkout@v7" in steps_text
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


def test_provenance_wrappers_delegate_to_shared_validator() -> None:
    for script_name in ("run_provenance_check.ps1", "run_provenance_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "provenance_check.py" in script
