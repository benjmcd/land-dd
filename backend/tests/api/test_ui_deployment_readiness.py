from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from fastapi.testclient import TestClient

from app.api import ui as ui_module
from app.deployment_readiness import (
    DeploymentReadinessError,
    load_deployment_readiness,
    parse_deployment_readiness,
)
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED_SCHEMAS = {
    "release_package_v1",
    "image_publication_v1",
    "hosted_deployment_v1",
}
EXPECTED_RUNTIME_INPUTS = {
    "REGISTRY_IMAGE",
    "IMAGE_DIGEST",
    "PUBLIC_BASE_URL",
    "DATABASE_URL",
    "API_KEY_SPECS",
    "REVIEWER_ACCOUNTS",
    "REVIEWER_ACCOUNT_SCOPES",
    "UI_AUTH_COOKIE_SECRET",
    "REPORT_IDENTITY_TOKEN_SECRET",
}
EXPECTED_BLOCKERS = {
    "registry_repository_authority",
    "hosted_deployment_authority",
    "registry_image_attestation_authority",
    "signed_image_sbom_authority",
    "hosted_platform_selected",
    "domain_tls_authority",
    "secrets_manager_authority",
    "database_instance_authority",
    "registry_image_digest_available",
    "hosted_billing_reconciliation",
    "hosted_alerting_route",
}
EXPECTED_LIMITS = {
    "validate_only": True,
    "creates_hosted_deployment": False,
    "pushes_registry_image": False,
    "mutates_hosted_infrastructure": False,
    "writes_secrets": False,
    "opens_public_endpoint": False,
}


def _catalog(path: str) -> dict[str, Any]:
    payload = yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _catalogs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        _catalog("config/release_package.yaml"),
        _catalog("config/image_publication.yaml"),
        _catalog("config/hosted_deployment.yaml"),
    )


def test_deployment_readiness_parser_composes_catalog_contract() -> None:
    readiness = load_deployment_readiness(REPO_ROOT)

    assert {
        readiness.package.schema_version,
        readiness.image.schema_version,
        readiness.hosted.schema_version,
    } == EXPECTED_SCHEMAS
    assert readiness.package.package_name == "land-diligence"
    assert readiness.image.image_name == "land-diligence-backend"
    assert readiness.hosted.service_name == "land-diligence-api"
    assert set(readiness.hosted.required_runtime_inputs) == EXPECTED_RUNTIME_INPUTS
    blockers = set(readiness.image.blockers) | set(readiness.hosted.blockers)
    assert EXPECTED_BLOCKERS.issubset(blockers)
    limits = {**readiness.image.limits, **readiness.hosted.limits}
    for key, expected in EXPECTED_LIMITS.items():
        assert limits[key] is expected


def test_deployment_readiness_parser_fails_closed_on_schema_drift() -> None:
    release_package, image_publication, hosted_deployment = _catalogs()
    release_package = deepcopy(release_package)
    release_package["schema_version"] = "release_package_v2"

    with pytest.raises(DeploymentReadinessError, match="schema"):
        parse_deployment_readiness(
            release_package,
            image_publication,
            hosted_deployment,
            root=REPO_ROOT,
        )


def test_deployment_readiness_loader_uses_repo_relative_error_paths(
    tmp_path: Path,
) -> None:
    with pytest.raises(DeploymentReadinessError) as exc_info:
        load_deployment_readiness(tmp_path)

    message = str(exc_info.value)
    assert "config/release_package.yaml" in message
    assert str(tmp_path) not in message


def test_deployment_readiness_parser_fails_closed_on_runtime_input_drift() -> None:
    release_package, image_publication, hosted_deployment = _catalogs()
    hosted_deployment = deepcopy(hosted_deployment)
    inputs = cast(list[str], hosted_deployment["required_runtime_inputs"])
    hosted_deployment["required_runtime_inputs"] = [
        value for value in inputs if value != "API_KEY_SPECS"
    ]

    with pytest.raises(DeploymentReadinessError, match="runtime input"):
        parse_deployment_readiness(
            release_package,
            image_publication,
            hosted_deployment,
            root=REPO_ROOT,
        )


def test_deployment_readiness_parser_fails_closed_on_blocker_drift() -> None:
    release_package, image_publication, hosted_deployment = _catalogs()
    image_publication = deepcopy(image_publication)
    image_publication["blocked_until"] = [
        blocker
        for blocker in cast(list[str], image_publication["blocked_until"])
        if blocker != "registry_repository_authority"
    ]

    with pytest.raises(DeploymentReadinessError, match="blocker"):
        parse_deployment_readiness(
            release_package,
            image_publication,
            hosted_deployment,
            root=REPO_ROOT,
        )


def test_deployment_readiness_parser_fails_closed_on_limit_drift() -> None:
    release_package, image_publication, hosted_deployment = _catalogs()
    hosted_deployment = deepcopy(hosted_deployment)
    limits = cast(dict[str, bool], hosted_deployment["limits"])
    limits["opens_public_endpoint"] = True

    with pytest.raises(DeploymentReadinessError, match="limit"):
        parse_deployment_readiness(
            release_package,
            image_publication,
            hosted_deployment,
            root=REPO_ROOT,
        )


def test_ui_deployment_readiness_route_returns_503_when_loader_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_loader() -> None:
        raise DeploymentReadinessError("test deployment readiness failure")

    monkeypatch.setattr(ui_module, "load_deployment_readiness", _raise_loader)
    client = TestClient(create_app())

    response = client.get("/ui/deployment-readiness")

    assert response.status_code == 503
    assert (
        "Deployment readiness unavailable from repo-owned deployment-path artifacts"
        in response.text
    )
    assert "test deployment readiness failure" in response.text
    assert "Traceback" not in response.text


def test_ui_deployment_readiness_route_renders_catalogs_and_boundaries() -> None:
    client = TestClient(create_app())

    response = client.get("/ui/deployment-readiness")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "Deployment Readiness" in response.text
    for text in (
        "release_package_v1",
        "image_publication_v1",
        "hosted_deployment_v1",
        "land-diligence",
        "land-diligence-backend",
        "land-diligence-api",
        *EXPECTED_RUNTIME_INPUTS,
        *EXPECTED_BLOCKERS,
        "validate_only",
        "creates_hosted_deployment",
        "pushes_registry_image",
        "mutates_hosted_infrastructure",
        "writes_secrets",
        "opens_public_endpoint",
        "false",
        "local validate-only",
        "does not build or publish a release package",
        "does not push a registry image",
        "does not create hosted deployment",
        "does not write secrets",
        "does not open public endpoints",
        "does not approve DS-017",
        "does not add OAuth/OIDC",
        "full identity/RBAC",
    ):
        assert text in response.text


def test_current_ui_navigation_links_to_deployment_readiness() -> None:
    client = TestClient(create_app())

    for path in ("/ui/", "/ui/raw-data"):
        response = client.get(path)

        assert response.status_code == 200
        assert 'href="/ui/deployment-readiness"' in response.text
