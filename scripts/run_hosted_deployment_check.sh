#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required_files=(
  "config/hosted_deployment.yaml"
  "config/image_publication.yaml"
  "config/release_readiness.yaml"
  "docs/runbooks/hosted_deployment.md"
  "backend/Dockerfile"
  "docker-compose.yml"
  "scripts/verify.ps1"
  "scripts/run_deployment_smoke.ps1"
  "scripts/run_release_readiness_check.ps1"
  "scripts/run_image_publication_check.ps1"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "required hosted-deployment artifact missing: $file" >&2
    exit 1
  fi
done

python - <<'PY'
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
REQUIRED_PRE_DEPLOY_GATES = {
    "scripts/verify.ps1",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_release_readiness_check.ps1",
    "scripts/run_image_publication_check.ps1",
}
REQUIRED_RUNTIME_INPUTS = {
    "REGISTRY_IMAGE",
    "IMAGE_DIGEST",
    "PUBLIC_BASE_URL",
    "DATABASE_URL",
    "API_KEYS",
    "API_KEY_SPECS",
    "REVIEWER_ACCOUNTS",
    "REVIEWER_ACCOUNT_SCOPES",
}
REQUIRED_RUNTIME_EVIDENCE = {
    "immutable_image_digest",
    "deployed_image_ref",
    "platform_environment_name",
    "database_instance_name",
    "public_https_url",
    "tls_certificate_status",
    "health_endpoint_ok",
    "version_endpoint_ok",
    "metrics_endpoint_ok",
    "queue_health_endpoint_ok",
    "report_workflow_smoke_ok",
    "rollback_target",
    "backup_restore_proof",
}
REQUIRED_BLOCKERS = {
    "hosted_platform_selected",
    "domain_tls_authority",
    "secrets_manager_authority",
    "database_instance_authority",
    "registry_image_digest_available",
    "hosted_billing_reconciliation",
    "hosted_alerting_route",
}
FORBIDDEN_COMMANDS = (
    "kubectl " + "apply",
    "helm " + "upgrade",
    "flyctl " + "deploy",
    "fly " + "deploy",
    "railway " + "up",
    "render " + "deploy",
    "vercel " + "--prod",
    "netlify " + "deploy",
    "az " + "containerapp",
    "gcloud " + "run deploy",
    "aws " + "ecs update-service",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"referenced hosted-deployment artifact missing: {normalized}")


def require_str_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    require(isinstance(value, list), f"{key} must be a list")
    result: list[str] = []
    for item in value:
        require(isinstance(item, str) and item, f"{key} entries must be non-empty strings")
        result.append(item)
    return result


catalog = yaml.safe_load((ROOT / "config" / "hosted_deployment.yaml").read_text(encoding="utf-8"))
require(isinstance(catalog, dict), "hosted deployment catalog must be a mapping")
require(catalog.get("schema_version") == "hosted_deployment_v1", "unexpected hosted deployment schema")
deployment = catalog.get("deployment")
require(isinstance(deployment, dict), "deployment section missing")
require(deployment.get("service_name") == "land-diligence-api", "service name mismatch")
require(deployment.get("runtime") == "containerized-fastapi", "runtime mismatch")
require(deployment.get("image_publication_catalog") == "config/image_publication.yaml", "image publication catalog mismatch")
require(deployment.get("release_readiness_catalog") == "config/release_readiness.yaml", "release readiness catalog mismatch")
require_existing(str(deployment["image_publication_catalog"]))
require_existing(str(deployment["release_readiness_catalog"]))
gates = set(require_str_list(catalog, "required_pre_deploy_gates"))
require(REQUIRED_PRE_DEPLOY_GATES.issubset(gates), f"missing hosted deployment gates: {sorted(REQUIRED_PRE_DEPLOY_GATES - gates)}")
for gate in gates:
    require_existing(gate)
runtime_inputs = set(require_str_list(catalog, "required_runtime_inputs"))
require(REQUIRED_RUNTIME_INPUTS.issubset(runtime_inputs), f"missing runtime inputs: {sorted(REQUIRED_RUNTIME_INPUTS - runtime_inputs)}")
runtime_evidence = set(require_str_list(catalog, "required_runtime_evidence"))
require(
    REQUIRED_RUNTIME_EVIDENCE.issubset(runtime_evidence),
    f"missing runtime evidence requirements: {sorted(REQUIRED_RUNTIME_EVIDENCE - runtime_evidence)}",
)
blockers = set(require_str_list(catalog, "blocked_until"))
require(REQUIRED_BLOCKERS.issubset(blockers), f"missing hosted deployment blockers: {sorted(REQUIRED_BLOCKERS - blockers)}")
limits = catalog.get("limits")
require(isinstance(limits, dict), "limits section missing")
require(limits.get("validate_only") is True, "hosted deployment proof must be validate-only")
require(limits.get("creates_hosted_deployment") is False, "hosted deployment proof must not create hosted deployments")
require(limits.get("mutates_hosted_infrastructure") is False, "hosted deployment proof must not mutate hosted infrastructure")
require(limits.get("writes_secrets") is False, "hosted deployment proof must not write secrets")
require(limits.get("opens_public_endpoint") is False, "hosted deployment proof must not open public endpoints")

for relative_path in (
    ".github/workflows/ci.yml",
    "scripts/run_hosted_deployment_check.ps1",
    "scripts/run_hosted_deployment_check.sh",
):
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    for command in FORBIDDEN_COMMANDS:
        require(command not in text, f"validate-only artifact must not run hosted mutation command: {relative_path}")

runbook = (ROOT / "docs" / "runbooks" / "hosted_deployment.md").read_text(encoding="utf-8")
for phrase in (
    "run_hosted_deployment_check.ps1",
    "validate-only",
    "PUBLIC_BASE_URL",
    "IMAGE_DIGEST",
    "public HTTPS URL",
    "TLS status",
    "No hosted deployment",
    "No secrets are written",
    "No registry image is deployed",
):
    require(phrase in runbook, f"hosted deployment runbook missing phrase: {phrase}")
PY

echo "hosted deployment check: ok"
