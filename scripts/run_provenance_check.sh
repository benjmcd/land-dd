#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required_files=(
  "backend/pyproject.toml"
  "backend/requirements-prod.lock"
  "docs/sbom/backend-prod-sbom.json"
  "docs/runbooks/dependency_provenance.md"
  "docs/runbooks/supply_chain.md"
  ".github/workflows/ci.yml"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "required dependency provenance artifact missing: $file" >&2
    exit 1
  fi
done

python - <<'PY'
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
LOCK = ROOT / "backend" / "requirements-prod.lock"
SBOM = ROOT / "docs" / "sbom" / "backend-prod-sbom.json"
PYPROJECT = ROOT / "backend" / "pyproject.toml"


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def text_from_steps(job: dict[str, Any]) -> str:
    steps = job.get("steps")
    require(isinstance(steps, list) and steps, "CI job has no steps")
    return "\n".join(
        str(step.get("uses", "")) + "\n" + str(step.get("run", "")) + "\n" + str(step.get("with", ""))
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
    for expected in ("uvicorn", "psycopg-binary", "httptools", "watchfiles", "websockets"):
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
    require(isinstance(components, list) and components, "SBOM components missing")
    sbom_entries: dict[str, dict[str, str]] = {}
    for component in components:
        require(isinstance(component, dict), "SBOM component must be a mapping")
        name = str(component.get("name", ""))
        version = str(component.get("version", ""))
        hashes = component.get("hashes")
        require(isinstance(hashes, list) and len(hashes) == 1, f"SBOM hash missing for {name}")
        digest = hashes[0]
        require(isinstance(digest, dict), f"SBOM hash must be a mapping for {name}")
        require(digest.get("alg") == "SHA-256", f"SBOM hash algorithm mismatch for {name}")
        sha256 = str(digest.get("content", ""))
        require(re.fullmatch(r"[0-9a-f]{64}", sha256) is not None, f"bad SBOM hash for {name}")
        sbom_entries[norm(name)] = {"name": name, "version": version, "sha256": sha256}
        require(str(component.get("purl", "")).startswith("pkg:pypi/"), f"SBOM purl missing for {name}")
    require(set(sbom_entries) == set(lock), "SBOM component set does not match lock")
    for key, locked in lock.items():
        require(sbom_entries[key]["version"] == locked["version"], f"SBOM version drift for {key}")
        require(sbom_entries[key]["sha256"] == locked["sha256"], f"SBOM hash drift for {key}")


def validate_docs_and_ci() -> None:
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    ci = yaml.safe_load(ci_text)
    require(isinstance(ci, dict), "ci workflow must be a mapping")
    jobs = ci.get("jobs")
    require(isinstance(jobs, dict), "ci workflow jobs missing")
    supply_job = jobs.get("supply-chain")
    require(isinstance(supply_job, dict), "CI missing supply-chain job")
    require("run_provenance_check.sh" in text_from_steps(supply_job), "CI must run dependency provenance check")
    require("pip-audit --local" in text_from_steps(supply_job), "CI must still run pip-audit")
    attest_job = jobs.get("dependency-attestations")
    require(isinstance(attest_job, dict), "CI missing dependency-attestations job")
    permissions = attest_job.get("permissions")
    require(isinstance(permissions, dict), "dependency-attestations permissions missing")
    require(permissions.get("contents") == "read", "dependency-attestations contents permission must be read")
    require(permissions.get("id-token") == "write", "dependency-attestations id-token permission must be write")
    require(permissions.get("attestations") == "write", "dependency-attestations attestations permission must be write")
    require(
        permissions.get("artifact-metadata") == "write",
        "dependency-attestations artifact-metadata permission must be write",
    )
    attest_steps = text_from_steps(attest_job)
    require("./scripts/run_provenance_check.sh" in attest_steps, "attestation job must validate provenance first")
    require(attest_steps.count("actions/attest@v4") == 2, "attestation job must use actions/attest@v4 twice")
    require("backend/requirements-prod.lock" in attest_steps, "attestation job missing lock subject")
    require("docs/sbom/backend-prod-sbom.json" in attest_steps, "attestation job missing SBOM path")
    require("'sbom-path': 'docs/sbom/backend-prod-sbom.json'" in attest_steps, "attestation job missing SBOM attestation")
    supply = (ROOT / "docs" / "runbooks" / "supply_chain.md").read_text(encoding="utf-8")
    provenance = (ROOT / "docs" / "runbooks" / "dependency_provenance.md").read_text(
        encoding="utf-8",
    )
    for phrase in (
        "backend/requirements-prod.lock",
        "docs/sbom/backend-prod-sbom.json",
        "run_provenance_check.ps1",
        "dependency-attestations",
        "actions/attest@v4",
        "SBOM attestation",
    ):
        require(phrase in supply + provenance, f"dependency provenance docs missing: {phrase}")


lock = parse_lock()
validate_pyproject_coverage(lock)
validate_sbom(lock)
validate_docs_and_ci()
PY

python -m pip install \
  --dry-run \
  --ignore-installed \
  --only-binary=:all: \
  --platform manylinux2014_x86_64 \
  --python-version 3.12 \
  --implementation cp \
  --abi cp312 \
  --require-hashes \
  -r ./backend/requirements-prod.lock

echo "dependency provenance check: ok"
