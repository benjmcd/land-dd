$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$requiredFiles = @(
    'config\image_publication.yaml',
    'docs\runbooks\image_publication.md',
    'backend\Dockerfile',
    'docker-compose.yml',
    'scripts\verify.ps1',
    'scripts\run_deployment_smoke.ps1',
    'scripts\run_container_scan_check.ps1',
    'scripts\run_release_package_check.ps1',
    'scripts\run_release_readiness_check.ps1'
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -Path (Join-Path $root $file) -PathType Leaf)) {
        throw "required image-publication artifact missing: $file"
    }
}

$python = @'
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
REQUIRED_GATES = {
    "scripts/verify.ps1",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_container_scan_check.ps1",
    "scripts/run_release_package_check.ps1",
    "scripts/run_release_readiness_check.ps1",
}
REQUIRED_ATTESTATIONS = {
    "image_digest",
    "registry_image_ref",
    "vulnerability_scan",
    "dependency_sbom",
    "provenance",
}
REQUIRED_BLOCKERS = {
    "registry_repository_authority",
    "hosted_deployment_authority",
    "registry_image_attestation_authority",
    "signed_image_sbom_authority",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"referenced image-publication artifact missing: {normalized}")


def require_str_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    require(isinstance(value, list), f"{key} must be a list")
    result: list[str] = []
    for item in value:
        require(isinstance(item, str) and item, f"{key} entries must be non-empty strings")
        result.append(item)
    return result


def validate_catalog() -> None:
    payload = yaml.safe_load((ROOT / "config" / "image_publication.yaml").read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "image publication catalog must be a mapping")
    require(payload.get("schema_version") == "image_publication_v1", "unexpected image publication schema")
    image = payload.get("image")
    require(isinstance(image, dict), "image section missing")
    require(image.get("name") == "land-diligence-backend", "image name mismatch")
    require(image.get("dockerfile") == "backend/Dockerfile", "image Dockerfile mismatch")
    require(image.get("context") == ".", "image build context must be repo root")
    require(image.get("local_tag_template") == "land-diligence-backend:{git_sha}", "local tag template mismatch")
    require(image.get("registry_image_env") == "REGISTRY_IMAGE", "registry image env mismatch")
    require_existing(str(image["dockerfile"]))
    gates = set(require_str_list(payload, "required_gates"))
    require(REQUIRED_GATES.issubset(gates), f"missing image publication gates: {sorted(REQUIRED_GATES - gates)}")
    for gate in gates:
        require_existing(gate)
    attestations = set(require_str_list(payload, "required_attestations"))
    require(
        REQUIRED_ATTESTATIONS.issubset(attestations),
        f"missing image publication attestation requirements: {sorted(REQUIRED_ATTESTATIONS - attestations)}",
    )
    blockers = set(require_str_list(payload, "blocked_until"))
    require(REQUIRED_BLOCKERS.issubset(blockers), f"missing image publication blockers: {sorted(REQUIRED_BLOCKERS - blockers)}")
    limits = payload.get("limits")
    require(isinstance(limits, dict), "limits section missing")
    require(limits.get("validate_only") is True, "image publication proof must be validate-only")
    require(limits.get("pushes_registry_image") is False, "image publication proof must not push registry images")
    require(limits.get("creates_hosted_deployment") is False, "image publication proof must not create hosted deployments")
    require(limits.get("signs_or_publishes_attestations") is False, "image publication proof must not sign or publish attestations")


def validate_no_validate_only_pushes() -> None:
    checked_paths = [
        ROOT / ".github" / "workflows" / "ci.yml",
        ROOT / "scripts" / "run_container_scan_check.ps1",
        ROOT / "scripts" / "run_container_scan_check.sh",
        ROOT / "scripts" / "run_release_readiness_check.ps1",
        ROOT / "scripts" / "run_release_readiness_check.sh",
        ROOT / "scripts" / "run_image_publication_check.ps1",
        ROOT / "scripts" / "run_image_publication_check.sh",
    ]
    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        require("docker " + "push" not in text, f"validate-only artifact must not run a registry push command: {path}")
        require("docker/" + "login-action" not in text, f"validate-only artifact must not login to a registry: {path}")
        require("cosign " + "sign" not in text, f"validate-only artifact must not sign images: {path}")


def validate_runbook() -> None:
    runbook = (ROOT / "docs" / "runbooks" / "image_publication.md").read_text(encoding="utf-8")
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
        require(phrase in runbook, f"image publication runbook missing phrase: {phrase}")


def main() -> int:
    validate_catalog()
    validate_no_validate_only_pushes()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@

$python | py -3.12 -
if ($LASTEXITCODE -ne 0) {
    throw "image publication validation failed with exit code $LASTEXITCODE"
}

Write-Host 'image publication check: ok'
