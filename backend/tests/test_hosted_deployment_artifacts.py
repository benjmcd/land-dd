from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_PRE_DEPLOY_GATES = {
    "scripts/verify.ps1",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_release_readiness_check.ps1",
    "scripts/run_image_publication_check.ps1",
}


def test_hosted_deployment_catalog_records_boundary_and_blockers() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "hosted_deployment.yaml").read_text(encoding="utf-8"),
    )

    assert catalog["schema_version"] == "hosted_deployment_v1"
    assert catalog["deployment"]["service_name"] == "land-diligence-api"
    assert catalog["deployment"]["runtime"] == "containerized-fastapi"
    assert catalog["deployment"]["image_publication_catalog"] == "config/image_publication.yaml"
    assert catalog["deployment"]["release_readiness_catalog"] == "config/release_readiness.yaml"
    assert REQUIRED_PRE_DEPLOY_GATES.issubset(set(catalog["required_pre_deploy_gates"]))
    for gate in catalog["required_pre_deploy_gates"]:
        assert (REPO_ROOT / gate).exists()
    assert {
        "REGISTRY_IMAGE",
        "IMAGE_DIGEST",
        "PUBLIC_BASE_URL",
        "DATABASE_URL",
        "API_KEYS",
        "API_KEY_SPECS",
        "REVIEWER_ACCOUNTS",
        "REVIEWER_ACCOUNT_SCOPES",
    }.issubset(set(catalog["required_runtime_inputs"]))
    assert {
        "immutable_image_digest",
        "deployed_image_ref",
        "public_https_url",
        "tls_certificate_status",
        "health_endpoint_ok",
        "version_endpoint_ok",
        "metrics_endpoint_ok",
        "queue_health_endpoint_ok",
        "report_workflow_smoke_ok",
        "rollback_target",
        "backup_restore_proof",
    }.issubset(set(catalog["required_runtime_evidence"]))
    assert {
        "hosted_platform_selected",
        "domain_tls_authority",
        "secrets_manager_authority",
        "database_instance_authority",
        "registry_image_digest_available",
        "hosted_billing_reconciliation",
        "hosted_alerting_route",
    }.issubset(set(catalog["blocked_until"]))
    assert catalog["limits"]["validate_only"] is True
    assert catalog["limits"]["creates_hosted_deployment"] is False
    assert catalog["limits"]["mutates_hosted_infrastructure"] is False
    assert catalog["limits"]["writes_secrets"] is False
    assert catalog["limits"]["opens_public_endpoint"] is False


def test_hosted_deployment_validate_only_artifacts_do_not_mutate_cloud() -> None:
    forbidden_commands = (
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
    for relative_path in (
        ".github/workflows/ci.yml",
        "scripts/run_hosted_deployment_check.ps1",
        "scripts/run_hosted_deployment_check.sh",
    ):
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for command in forbidden_commands:
            assert command not in text


def test_hosted_deployment_runbook_records_validation_workflow_and_limits() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "hosted_deployment.md").read_text(
        encoding="utf-8",
    )

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
        assert phrase in runbook


def test_hosted_deployment_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "run_hosted_deployment_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_hosted_deployment_check.sh").is_file()
