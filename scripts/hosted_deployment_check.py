from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "config/hosted_deployment.yaml",
    "config/image_publication.yaml",
    "config/release_readiness.yaml",
    "docs/runbooks/hosted_deployment.md",
    "backend/Dockerfile",
    "docker-compose.yml",
    "scripts/verify.ps1",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_release_readiness_check.ps1",
    "scripts/run_image_publication_check.ps1",
    "scripts/hosted_deployment_check.py",
    "scripts/run_hosted_deployment_check.ps1",
    "scripts/run_hosted_deployment_check.sh",
)
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
ATTESTATION_EVIDENCE_AUTHORITY = "docs/runbooks/hosted_deployment.md"
UNAVAILABLE_ATTESTATION_STATUS = "not_available"
AVAILABLE_ATTESTATION_STATUSES = {
    "available",
    "deployed",
    "production_ready",
    "published",
    "ready",
}
ALLOWED_ATTESTATION_STATUSES = {
    UNAVAILABLE_ATTESTATION_STATUS,
    *AVAILABLE_ATTESTATION_STATUSES,
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


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require(
        (ROOT / normalized).exists(),
        f"referenced hosted-deployment artifact missing: {normalized}",
    )


def require_str_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise SystemExit(f"{key} must be a list")

    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise SystemExit(f"{key} entries must be non-empty strings")
        result.append(item)
    return result


def is_empty_evidence_value(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, dict | list | tuple | set):
        return len(value) == 0
    return False


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require(
            (ROOT / path_text).is_file(),
            f"required hosted-deployment artifact missing: {path_text}",
        )


def validate_catalog() -> None:
    catalog = yaml.safe_load(read_text("config/hosted_deployment.yaml"))
    require(isinstance(catalog, dict), "hosted deployment catalog must be a mapping")
    require(
        catalog.get("schema_version") == "hosted_deployment_v1",
        "unexpected hosted deployment schema",
    )
    deployment = catalog.get("deployment")
    require(isinstance(deployment, dict), "deployment section missing")
    require(deployment.get("service_name") == "land-diligence-api", "service name mismatch")
    require(deployment.get("runtime") == "containerized-fastapi", "runtime mismatch")
    require(
        deployment.get("image_publication_catalog") == "config/image_publication.yaml",
        "image publication catalog mismatch",
    )
    require(
        deployment.get("release_readiness_catalog") == "config/release_readiness.yaml",
        "release readiness catalog mismatch",
    )
    image_catalog = deployment.get("image_publication_catalog")
    release_catalog = deployment.get("release_readiness_catalog")
    require(isinstance(image_catalog, str), "image publication catalog path missing")
    require(isinstance(release_catalog, str), "release readiness catalog path missing")
    require_existing(image_catalog)
    require_existing(release_catalog)

    gates = set(require_str_list(catalog, "required_pre_deploy_gates"))
    missing_gates = sorted(REQUIRED_PRE_DEPLOY_GATES - gates)
    require(not missing_gates, f"missing hosted deployment gates: {missing_gates}")
    for gate in gates:
        require_existing(gate)

    runtime_inputs = set(require_str_list(catalog, "required_runtime_inputs"))
    missing_inputs = sorted(REQUIRED_RUNTIME_INPUTS - runtime_inputs)
    require(not missing_inputs, f"missing runtime inputs: {missing_inputs}")

    runtime_evidence = set(require_str_list(catalog, "required_runtime_evidence"))
    missing_evidence = sorted(REQUIRED_RUNTIME_EVIDENCE - runtime_evidence)
    require(
        not missing_evidence,
        f"missing runtime evidence requirements: {missing_evidence}",
    )

    blockers = set(require_str_list(catalog, "blocked_until"))
    missing_blockers = sorted(REQUIRED_BLOCKERS - blockers)
    require(not missing_blockers, f"missing hosted deployment blockers: {missing_blockers}")

    evidence = catalog.get("attestation_evidence")
    require(isinstance(evidence, dict), "attestation_evidence section missing")
    status = evidence.get("status")
    require(
        isinstance(status, str) and status in ALLOWED_ATTESTATION_STATUSES,
        "attestation_evidence status must be not_available or an available proof status",
    )
    authority = evidence.get("authority")
    require(
        authority == ATTESTATION_EVIDENCE_AUTHORITY,
        "attestation_evidence authority must point to the hosted deployment runbook",
    )
    require_existing(ATTESTATION_EVIDENCE_AUTHORITY)

    evidence_fields = set(require_str_list(evidence, "required_fields"))
    require(
        evidence_fields == REQUIRED_RUNTIME_EVIDENCE,
        "attestation_evidence required_fields must exactly match required_runtime_evidence",
    )
    evidence_blockers = set(require_str_list(evidence, "blocked_until"))
    missing_evidence_blockers = sorted(REQUIRED_BLOCKERS - evidence_blockers)
    require(
        not missing_evidence_blockers,
        f"attestation_evidence missing blockers: {missing_evidence_blockers}",
    )
    template = evidence.get("evidence_template")
    require(isinstance(template, dict), "attestation_evidence evidence_template missing")
    template_keys = {str(key) for key in template}
    require(
        template_keys == REQUIRED_RUNTIME_EVIDENCE,
        "attestation_evidence evidence_template keys must exactly match required_runtime_evidence",
    )
    if status in AVAILABLE_ATTESTATION_STATUSES:
        empty_fields = sorted(
            field
            for field in REQUIRED_RUNTIME_EVIDENCE
            if is_empty_evidence_value(template.get(field))
        )
        require(
            not empty_fields,
            f"attestation_evidence status {status} requires values for: {empty_fields}",
        )

    limits = catalog.get("limits")
    require(isinstance(limits, dict), "limits section missing")
    require(limits.get("validate_only") is True, "hosted deployment proof must be validate-only")
    require(
        limits.get("creates_hosted_deployment") is False,
        "hosted deployment proof must not create hosted deployments",
    )
    require(
        limits.get("mutates_hosted_infrastructure") is False,
        "hosted deployment proof must not mutate hosted infrastructure",
    )
    require(limits.get("writes_secrets") is False, "hosted deployment proof must not write secrets")
    require(
        limits.get("opens_public_endpoint") is False,
        "hosted deployment proof must not open public endpoints",
    )


def validate_no_hosted_mutations() -> None:
    for relative_path in (
        ".github/workflows/ci.yml",
        "scripts/run_hosted_deployment_check.ps1",
        "scripts/run_hosted_deployment_check.sh",
    ):
        text = read_text(relative_path)
        for command in FORBIDDEN_COMMANDS:
            require(
                command not in text,
                f"validate-only artifact must not run hosted mutation command: {relative_path}",
            )


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/hosted_deployment.md")
    for phrase in (
        "run_hosted_deployment_check.ps1",
        "scripts/hosted_deployment_check.py",
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


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_no_hosted_mutations()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
