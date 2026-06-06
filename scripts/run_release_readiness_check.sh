#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required_files=(
  "config/release_readiness.yaml"
  "config/release_package.yaml"
  "config/image_publication.yaml"
  "config/hosted_deployment.yaml"
  "docs/runbooks/release_readiness.md"
  "docs/runbooks/release_package.md"
  "docs/runbooks/image_publication.md"
  "docs/runbooks/hosted_deployment.md"
  ".github/workflows/ci.yml"
  "backend/pyproject.toml"
  "backend/requirements-prod.lock"
  "backend/Dockerfile"
  "docker-compose.yml"
  "docs/sbom/backend-prod-sbom.json"
  "scripts/verify.ps1"
  "scripts/verify.sh"
  "scripts/run_deployment_smoke.ps1"
  "scripts/run_provenance_check.ps1"
  "scripts/run_supply_chain_check.ps1"
  "scripts/run_container_scan_check.ps1"
  "scripts/run_release_package_check.ps1"
  "scripts/run_image_publication_check.ps1"
  "scripts/run_hosted_deployment_check.ps1"
  "scripts/source_readiness.py"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "required release-readiness artifact missing: $file" >&2
    exit 1
  fi
done

python - <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
REQUIRED_CHECKS = {
    "workspace_verify",
    "db_verify",
    "deployment_smoke",
    "dependency_provenance",
    "supply_chain_scan",
    "container_image_scan",
    "backup_restore",
    "incident_rollback",
    "alert_rules",
    "cost_monitoring",
    "access_control",
    "release_package",
    "source_readiness",
}
REQUIRED_CI_JOBS = {
    "verify",
    "db-verify",
    "supply-chain",
    "dependency-attestations",
    "container-image-scan",
    "access-control",
    "release-readiness",
}
REQUIRED_BLOCKERS = {
    "non_ready_must_sources",
}
REQUIRED_DEFERRED = {
    "billing_hosted_billing_reconciliation",
    "hosted_deployment",
    "hosted_deployment_attestation",
    "hosted_alerting",
    "hosted_log_retention",
    "published_registry_image_attestation",
    "registry_push_signing_requirements",
    "automatic_key_rotation_external_secret_manager",
    "full_user_auth_rbac_oidc_user_accounts",
}
REMOTE_ONLY_CHECKS = {"image_publication", "hosted_deployment"}
REMOTE_ONLY_CI_JOBS = {"image-publication", "hosted-deployment"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"referenced release artifact missing: {normalized}")


def step_text(job: dict[str, Any], job_name: str) -> str:
    steps = job.get("steps")
    require(isinstance(steps, list) and steps, f"{job_name} job has no steps")
    return "\n".join(
        str(step.get("uses", "")) + "\n" + str(step.get("run", "")) + "\n" + str(step.get("with", ""))
        for step in steps
        if isinstance(step, dict)
    )


catalog = yaml.safe_load((ROOT / "config" / "release_readiness.yaml").read_text(encoding="utf-8"))
require(isinstance(catalog, dict), "release readiness catalog must be a mapping")
require(catalog.get("schema_version") == "release_readiness_v1", "unexpected release readiness schema")
require(catalog.get("operator_runbook") == "docs/runbooks/release_readiness.md", "operator runbook mismatch")
checks = catalog.get("required_checks")
require(isinstance(checks, list) and checks, "release readiness checks missing")
check_ids = set()
for check in checks:
    require(isinstance(check, dict), "each release readiness check must be a mapping")
    check_id = check.get("id")
    require(isinstance(check_id, str) and check_id, "release readiness check id missing")
    check_ids.add(check_id)
    proof = check.get("proof")
    require(isinstance(proof, str) and proof, f"{check_id} proof missing")
    require_existing(proof)
require(REQUIRED_CHECKS.issubset(check_ids), f"missing release checks: {sorted(REQUIRED_CHECKS - check_ids)}")
require(check_ids.isdisjoint(REMOTE_ONLY_CHECKS), f"remote-only checks must not be required for local-only release: {sorted(check_ids & REMOTE_ONLY_CHECKS)}")

blockers = catalog.get("release_blockers")
require(isinstance(blockers, list) and blockers, "release blockers missing")
blocker_ids = set()
for blocker in blockers:
    require(isinstance(blocker, dict), "each release blocker must be a mapping")
    blocker_id = blocker.get("id")
    require(isinstance(blocker_id, str) and blocker_id, "release blocker id missing")
    blocker_ids.add(blocker_id)
    require(blocker.get("status") == "blocked", f"{blocker_id} must remain blocked")
    authority = blocker.get("authority")
    require(isinstance(authority, str) and authority, f"{blocker_id} authority missing")
    require_existing(authority)
require(REQUIRED_BLOCKERS.issubset(blocker_ids), f"missing release blockers: {sorted(REQUIRED_BLOCKERS - blocker_ids)}")
deferred = catalog.get("local_only_deferred")
require(isinstance(deferred, list) and deferred, "local-only deferred list missing")
deferred_ids = set()
for item in deferred:
    require(isinstance(item, dict), "each local-only deferred item must be a mapping")
    item_id = item.get("id")
    require(isinstance(item_id, str) and item_id, "local-only deferred id missing")
    deferred_ids.add(item_id)
    require(item.get("status") == "out_of_scope_local_only", f"{item_id} must be out_of_scope_local_only")
    authority = item.get("authority")
    require(isinstance(authority, str) and authority, f"{item_id} authority missing")
    require_existing(authority)
    reason = item.get("reason")
    require(isinstance(reason, str) and reason, f"{item_id} reason missing")
require(REQUIRED_DEFERRED.issubset(deferred_ids), f"missing local-only deferred items: {sorted(REQUIRED_DEFERRED - deferred_ids)}")

ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
ci = yaml.safe_load(ci_text)
require(isinstance(ci, dict), "ci workflow must be a mapping")
jobs = ci.get("jobs")
require(isinstance(jobs, dict), "ci workflow jobs missing")
require(REQUIRED_CI_JOBS.issubset(set(jobs)), f"missing CI jobs: {sorted(REQUIRED_CI_JOBS - set(jobs))}")
require(REMOTE_ONLY_CI_JOBS.isdisjoint(set(jobs)), f"remote-only CI jobs must not run for local-only release: {sorted(REMOTE_ONLY_CI_JOBS & set(jobs))}")
job = jobs["release-readiness"]
permissions = job.get("permissions")
require(isinstance(permissions, dict), "release-readiness permissions missing")
require(permissions.get("contents") == "read", "release-readiness must use read-only contents permission")
text = step_text(job, "release-readiness")
require("actions/checkout@v4" in text, "release-readiness job must checkout repo")
require("actions/setup-python@v5" in text, "release-readiness job must setup Python")
require("python-version: '3.12'" in ci_text, "release-readiness job must use Python 3.12")
require("python -m pip install PyYAML" in text, "release-readiness job must install PyYAML")
require("./scripts/run_release_readiness_check.sh" in text, "release-readiness job must run POSIX proof")
result = subprocess.run(
    [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
    check=True,
    capture_output=True,
    text=True,
)
source_readiness = json.loads(result.stdout)
require(source_readiness.get("source_count") == 8, "Must source count changed")
require(source_readiness.get("ready_count") == 4, "Must ready count changed")
require(source_readiness.get("blocked_count") == 4, "Must blocked count changed")
blocked = {
    str(source.get("source_registry_id"))
    for source in source_readiness.get("sources", [])
    if source.get("connector_ready") is False
}
require({"DS-010", "DS-011", "DS-017", "DS-023"}.issubset(blocked), "expected source blockers missing")

runbook = (ROOT / "docs" / "runbooks" / "release_readiness.md").read_text(encoding="utf-8")
for phrase in (
    "run_release_readiness_check.ps1",
    "validate-only",
    "verify",
    "db-verify",
    "supply-chain",
    "dependency-attestations",
    "container-image-scan",
    "access-control",
    "release-package",
    "release-readiness",
    "sources=8 ready=4 blocked=4",
    "build_release_package.ps1",
    "run_image_publication_check.ps1",
    "run_hosted_deployment_check.ps1",
    "out of scope for local-only",
    "not local-only release blockers",
):
    require(phrase in runbook, f"release readiness runbook missing phrase: {phrase}")
PY

echo "release readiness check: ok"
