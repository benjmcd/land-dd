from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "backend" / "requirements-prod.lock"
SBOM = ROOT / "docs" / "sbom" / "backend-prod-sbom.json"
PYPROJECT = ROOT / "backend" / "pyproject.toml"

REQUIRED_FILES = (
    "backend/pyproject.toml",
    "backend/requirements-prod.lock",
    "docs/sbom/backend-prod-sbom.json",
    "docs/runbooks/dependency_provenance.md",
    "docs/runbooks/supply_chain.md",
    ".github/workflows/ci.yml",
    "scripts/provenance_check.py",
    "scripts/run_provenance_check.ps1",
    "scripts/run_provenance_check.sh",
)
REQUIRED_RUNTIME_PACKAGES = ("uvicorn", "psycopg-binary", "httptools", "watchfiles", "websockets")
REQUIRED_DOC_PHRASES = (
    "backend/requirements-prod.lock",
    "docs/sbom/backend-prod-sbom.json",
    "run_provenance_check.ps1",
    "scripts/provenance_check.py",
    "dependency-attestations",
    "actions/attest@v4",
    "SBOM attestation",
)


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require(
            (ROOT / path_text).is_file(),
            f"required dependency provenance artifact missing: {path_text}",
        )


def text_from_steps(job: dict[str, Any]) -> str:
    steps = job.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SystemExit("CI job has no steps")

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


def parse_lock() -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for raw in LOCK.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(
            r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.!+-]+) --hash=sha256:([0-9a-f]{64})",
            line,
        )
        require(match is not None, f"malformed production lock line: {line}")
        assert match is not None
        name, version, sha256 = match.groups()
        key = norm(name)
        require(key not in entries, f"duplicate production lock entry: {name}")
        entries[key] = {"name": name, "version": version, "sha256": sha256}

    require(len(entries) >= 20, "production lock is unexpectedly small")
    return entries


def validate_pyproject_coverage(lock: dict[str, dict[str, str]]) -> None:
    payload = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    require(payload["project"]["requires-python"] == ">=3.12", "unexpected Python version")
    direct = {
        norm(re.split(r"[\[<>=!~ ]", requirement, maxsplit=1)[0])
        for requirement in payload["project"]["dependencies"]
    }
    missing = sorted(direct - set(lock))
    require(not missing, f"production lock missing direct dependencies: {missing}")
    for expected in REQUIRED_RUNTIME_PACKAGES:
        require(expected in lock, f"production lock missing expected runtime package: {expected}")


def validate_sbom(lock: dict[str, dict[str, str]]) -> None:
    payload = json.loads(SBOM.read_text(encoding="utf-8"))
    require(payload.get("bomFormat") == "CycloneDX", "SBOM must be CycloneDX")
    require(payload.get("specVersion") == "1.5", "unexpected SBOM spec version")
    metadata = payload.get("metadata")
    require(isinstance(metadata, dict), "SBOM metadata missing")
    component = metadata.get("component")
    require(isinstance(component, dict), "SBOM metadata component missing")
    require(component.get("name") == "land-diligence-backend", "SBOM app component mismatch")
    require(component.get("version") == "0.1.0", "SBOM app version mismatch")

    components = payload.get("components")
    require(isinstance(components, list) and bool(components), "SBOM components missing")
    sbom_entries: dict[str, dict[str, str]] = {}
    for component in components:
        require(isinstance(component, dict), "SBOM component must be a mapping")
        component = cast(dict[str, Any], component)
        name = str(component.get("name", ""))
        version = str(component.get("version", ""))
        hashes = component.get("hashes")
        if not isinstance(hashes, list) or len(hashes) != 1:
            raise SystemExit(f"SBOM hash missing for {name}")

        digest = hashes[0]
        require(isinstance(digest, dict), f"SBOM hash must be a mapping for {name}")
        digest = cast(dict[str, Any], digest)
        require(digest.get("alg") == "SHA-256", f"SBOM hash algorithm mismatch for {name}")
        sha256 = str(digest.get("content", ""))
        require(re.fullmatch(r"[0-9a-f]{64}", sha256) is not None, f"bad SBOM hash for {name}")
        sbom_entries[norm(name)] = {"name": name, "version": version, "sha256": sha256}
        require(
            str(component.get("purl", "")).startswith("pkg:pypi/"),
            f"SBOM purl missing for {name}",
        )

    require(set(sbom_entries) == set(lock), "SBOM component set does not match lock")
    for key, locked in lock.items():
        require(sbom_entries[key]["version"] == locked["version"], f"SBOM version drift for {key}")
        require(sbom_entries[key]["sha256"] == locked["sha256"], f"SBOM hash drift for {key}")


def validate_docs_and_ci() -> None:
    ci = yaml.safe_load(read_text(".github/workflows/ci.yml"))
    require(isinstance(ci, dict), "ci workflow must be a mapping")
    ci = cast(dict[str, Any], ci)
    jobs = ci.get("jobs")
    require(isinstance(jobs, dict), "ci workflow jobs missing")
    jobs = cast(dict[str, Any], jobs)

    supply_job = jobs.get("supply-chain")
    require(isinstance(supply_job, dict), "CI missing supply-chain job")
    supply_steps = text_from_steps(cast(dict[str, Any], supply_job))
    require("python -m pip install PyYAML" in supply_steps, "supply-chain job must install PyYAML")
    require("run_provenance_check.sh" in supply_steps, "CI must run dependency provenance check")
    require("pip-audit --local" in supply_steps, "CI must still run pip-audit")

    attest_job = jobs.get("dependency-attestations")
    require(isinstance(attest_job, dict), "CI missing dependency-attestations job")
    attest_job = cast(dict[str, Any], attest_job)
    permissions = attest_job.get("permissions")
    require(isinstance(permissions, dict), "dependency-attestations permissions missing")
    permissions = cast(dict[str, Any], permissions)
    require(
        permissions.get("contents") == "read",
        "dependency-attestations contents permission must be read",
    )
    require(
        permissions.get("id-token") == "write",
        "dependency-attestations id-token permission must be write",
    )
    require(
        permissions.get("attestations") == "write",
        "dependency-attestations attestations permission must be write",
    )
    require(
        permissions.get("artifact-metadata") == "write",
        "dependency-attestations artifact-metadata permission must be write",
    )

    attest_steps = text_from_steps(attest_job)
    require(
        "./scripts/run_provenance_check.sh" in attest_steps,
        "attestation job must validate provenance first",
    )
    require(
        "Check GitHub attestation entitlement" in attest_steps,
        "attestation job must check entitlement",
    )
    require(
        "Dependency attestations blocked" in attest_steps,
        "attestation job must record blocked entitlement",
    )
    require(
        attest_steps.count("actions/attest@v4") == 2,
        "attestation job must use actions/attest@v4 twice",
    )
    require(
        "steps.attestation-entitlement.outputs.enabled == 'true'" in attest_steps,
        "attestation actions must be entitlement-gated",
    )
    require(
        "create-storage-record" in attest_steps,
        "attestation job must avoid storage-record writes",
    )
    require(
        "backend/requirements-prod.lock" in attest_steps,
        "attestation job missing lock subject",
    )
    require("docs/sbom/backend-prod-sbom.json" in attest_steps, "attestation job missing SBOM path")
    require(
        "'sbom-path': 'docs/sbom/backend-prod-sbom.json'" in attest_steps,
        "attestation job missing SBOM attestation",
    )

    docs = read_text("docs/runbooks/supply_chain.md") + read_text(
        "docs/runbooks/dependency_provenance.md",
    )
    for phrase in REQUIRED_DOC_PHRASES:
        require(phrase in docs, f"dependency provenance docs missing: {phrase}")


def validate_pip_hash_dry_run() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--dry-run",
            "--ignore-installed",
            "--only-binary=:all:",
            "--platform",
            "manylinux2014_x86_64",
            "--python-version",
            "3.12",
            "--implementation",
            "cp",
            "--abi",
            "cp312",
            "--require-hashes",
            "-r",
            str(LOCK),
        ],
        check=True,
    )


def main() -> int:
    validate_required_files()
    lock = parse_lock()
    validate_pyproject_coverage(lock)
    validate_sbom(lock)
    validate_docs_and_ci()
    validate_pip_hash_dry_run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
