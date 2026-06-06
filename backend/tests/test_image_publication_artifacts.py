from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_GATES = {
    "scripts/verify.ps1",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_container_scan_check.ps1",
    "scripts/run_release_package_check.ps1",
    "scripts/run_release_readiness_check.ps1",
}


def test_image_publication_catalog_records_publish_boundary_and_blockers() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "image_publication.yaml").read_text(encoding="utf-8"),
    )

    assert catalog["schema_version"] == "image_publication_v1"
    assert catalog["image"]["name"] == "land-diligence-backend"
    assert catalog["image"]["dockerfile"] == "backend/Dockerfile"
    assert catalog["image"]["context"] == "."
    assert catalog["image"]["local_tag_template"] == "land-diligence-backend:{git_sha}"
    assert catalog["image"]["registry_image_env"] == "REGISTRY_IMAGE"
    assert (REPO_ROOT / catalog["image"]["dockerfile"]).exists()
    assert REQUIRED_GATES.issubset(set(catalog["required_gates"]))
    for gate in catalog["required_gates"]:
        assert (REPO_ROOT / gate).exists()
    assert {
        "image_digest",
        "registry_image_ref",
        "vulnerability_scan",
        "dependency_sbom",
        "provenance",
    }.issubset(set(catalog["required_attestations"]))
    assert {
        "registry_repository_authority",
        "hosted_deployment_authority",
        "registry_image_attestation_authority",
        "signed_image_sbom_authority",
    }.issubset(set(catalog["blocked_until"]))
    assert catalog["limits"]["validate_only"] is True
    assert catalog["limits"]["pushes_registry_image"] is False
    assert catalog["limits"]["creates_hosted_deployment"] is False
    assert catalog["limits"]["signs_or_publishes_attestations"] is False


def test_image_publication_validate_only_artifacts_do_not_push_or_sign() -> None:
    for relative_path in (
        ".github/workflows/ci.yml",
        "scripts/run_container_scan_check.ps1",
        "scripts/run_container_scan_check.sh",
        "scripts/run_release_readiness_check.ps1",
        "scripts/run_release_readiness_check.sh",
        "scripts/run_image_publication_check.ps1",
        "scripts/run_image_publication_check.sh",
    ):
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "docker push" not in text
        assert "docker/login-action" not in text
        assert "cosign sign" not in text


def test_image_publication_runbook_records_validation_workflow_and_limits() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "image_publication.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "run_image_publication_check.ps1",
        "validate-only",
        "REGISTRY_IMAGE",
        "image digest",
        "registry image ref",
        "No registry image is pushed",
        "No hosted deployment",
        "published registry-image attestation",
    ):
        assert phrase in runbook


def test_image_publication_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "run_image_publication_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_image_publication_check.sh").is_file()
