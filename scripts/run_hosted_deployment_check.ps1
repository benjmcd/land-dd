$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$requiredFiles = @(
    'config\hosted_deployment.yaml',
    'config\image_publication.yaml',
    'config\release_readiness.yaml',
    'docs\runbooks\hosted_deployment.md',
    'backend\Dockerfile',
    'docker-compose.yml',
    'scripts\verify.ps1',
    'scripts\run_deployment_smoke.ps1',
    'scripts\run_release_readiness_check.ps1',
    'scripts\run_image_publication_check.ps1'
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -Path (Join-Path $root $file) -PathType Leaf)) {
        throw "required hosted-deployment artifact missing: $file"
    }
}

$python = @'
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
OPTIONAL_PRE_DEPLOY_GATES = {
    "scripts/verify.ps1",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_release_readiness_check.ps1",
    "scripts/run_image_publication_check.ps1",
}
FUTURE_RUNTIME_INPUTS = {
    "REGISTRY_IMAGE",
    "IMAGE_DIGEST",
    "PUBLIC_BASE_URL",
    "DATABASE_URL",
    "API_KEYS",
    "API_KEY_SPECS",
    "REVIEWER_ACCOUNTS",
    "REVIEWER_ACCOUNT_SCOPES",
}
FUTURE_RUNTIME_EVIDENCE = {
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
DEFERRED_REMOTE_REQUIREMENTS = {
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


def validate_catalog() -> None:
    payload = yaml.safe_load((ROOT / "config" / "hosted_deployment.yaml").read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "hosted deployment catalog must be a mapping")
    require(payload.get("schema_version") == "hosted_deployment_v1", "unexpected hosted deployment schema")
    scope = payload.get("scope")
    require(isinstance(scope, dict), "scope section missing")
    require(scope.get("status") == "out_of_scope_local_only", "hosted deployment must be out_of_scope_local_only")
    require(scope.get("required_for_local_only_release") is False, "hosted deployment must not be required for local-only release")
    deployment = payload.get("deployment")
    require(isinstance(deployment, dict), "deployment section missing")
    require(deployment.get("service_name") == "land-diligence-api", "service name mismatch")
    require(deployment.get("runtime") == "containerized-fastapi", "runtime mismatch")
    require(deployment.get("image_publication_catalog") == "config/image_publication.yaml", "image publication catalog mismatch")
    require(deployment.get("release_readiness_catalog") == "config/release_readiness.yaml", "release readiness catalog mismatch")
    require_existing(str(deployment["image_publication_catalog"]))
    require_existing(str(deployment["release_readiness_catalog"]))
    gates = set(require_str_list(payload, "optional_pre_deploy_gates"))
    require(OPTIONAL_PRE_DEPLOY_GATES.issubset(gates), f"missing optional hosted deployment gates: {sorted(OPTIONAL_PRE_DEPLOY_GATES - gates)}")
    for gate in gates:
        require_existing(gate)
    runtime_inputs = set(require_str_list(payload, "future_runtime_inputs"))
    require(FUTURE_RUNTIME_INPUTS.issubset(runtime_inputs), f"missing future runtime inputs: {sorted(FUTURE_RUNTIME_INPUTS - runtime_inputs)}")
    runtime_evidence = set(require_str_list(payload, "future_runtime_evidence"))
    require(
        FUTURE_RUNTIME_EVIDENCE.issubset(runtime_evidence),
        f"missing future runtime evidence requirements: {sorted(FUTURE_RUNTIME_EVIDENCE - runtime_evidence)}",
    )
    deferred = set(require_str_list(payload, "deferred_remote_requirements"))
    require(
        DEFERRED_REMOTE_REQUIREMENTS.issubset(deferred),
        f"missing deferred hosted deployment requirements: {sorted(DEFERRED_REMOTE_REQUIREMENTS - deferred)}",
    )
    limits = payload.get("limits")
    require(isinstance(limits, dict), "limits section missing")
    require(limits.get("validate_only") is True, "hosted deployment proof must be validate-only")
    require(limits.get("required_for_local_only_release") is False, "hosted deployment proof must not be required for local-only release")
    require(limits.get("creates_hosted_deployment") is False, "hosted deployment proof must not create hosted deployments")
    require(limits.get("mutates_hosted_infrastructure") is False, "hosted deployment proof must not mutate hosted infrastructure")
    require(limits.get("writes_secrets") is False, "hosted deployment proof must not write secrets")
    require(limits.get("opens_public_endpoint") is False, "hosted deployment proof must not open public endpoints")


def validate_no_hosted_mutations() -> None:
    checked_paths = [
        ROOT / ".github" / "workflows" / "ci.yml",
        ROOT / "scripts" / "run_hosted_deployment_check.ps1",
        ROOT / "scripts" / "run_hosted_deployment_check.sh",
    ]
    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        for command in FORBIDDEN_COMMANDS:
            require(command not in text, f"validate-only artifact must not run hosted mutation command: {path}")


def validate_runbook() -> None:
    runbook = (ROOT / "docs" / "runbooks" / "hosted_deployment.md").read_text(encoding="utf-8")
    for phrase in (
        "run_hosted_deployment_check.ps1",
        "validate-only",
        "PUBLIC_BASE_URL",
        "IMAGE_DIGEST",
        "out of scope for local-only",
        "optional future-hosting",
        "local-only release",
        "No hosted deployment",
        "No secrets are written",
        "No registry image is deployed",
    ):
        require(phrase in runbook, f"hosted deployment runbook missing phrase: {phrase}")


def main() -> int:
    validate_catalog()
    validate_no_hosted_mutations()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@

$python | py -3.12 -
if ($LASTEXITCODE -ne 0) {
    throw "hosted deployment validation failed with exit code $LASTEXITCODE"
}

Write-Host 'hosted deployment check: ok'
