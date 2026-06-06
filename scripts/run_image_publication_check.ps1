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
OPTIONAL_GATES = {
    "scripts/verify.ps1",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_container_scan_check.ps1",
    "scripts/run_release_package_check.ps1",
    "scripts/run_release_readiness_check.ps1",
}
LOCAL_ONLY_EVIDENCE = {
    "local_image_build",
    "vulnerability_scan",
    "dependency_sbom",
    "release_package_manifest",
}
DEFERRED_REMOTE_REQUIREMENTS = {
    "registry_repository_authority",
    "registry_push_authority",
    "registry_image_ref",
    "immutable_image_digest",
    "registry_image_attestation_authority",
    "signed_image_sbom_authority",
    "provenance_attestation",
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
    scope = payload.get("scope")
    require(isinstance(scope, dict), "scope section missing")
    require(scope.get("status") == "out_of_scope_local_only", "image publication must be out_of_scope_local_only")
    require(scope.get("required_for_local_only_release") is False, "image publication must not be required for local-only release")
    image = payload.get("image")
    require(isinstance(image, dict), "image section missing")
    require(image.get("name") == "land-diligence-backend", "image name mismatch")
    require(image.get("dockerfile") == "backend/Dockerfile", "image Dockerfile mismatch")
    require(image.get("context") == ".", "image build context must be repo root")
    require(image.get("local_tag_template") == "land-diligence-backend:{git_sha}", "local tag template mismatch")
    require(image.get("registry_image_env") == "REGISTRY_IMAGE", "registry image env mismatch")
    require_existing(str(image["dockerfile"]))
    gates = set(require_str_list(payload, "optional_pre_publish_gates"))
    require(OPTIONAL_GATES.issubset(gates), f"missing optional image publication gates: {sorted(OPTIONAL_GATES - gates)}")
    for gate in gates:
        require_existing(gate)
    local_evidence = set(require_str_list(payload, "local_only_evidence"))
    require(
        LOCAL_ONLY_EVIDENCE.issubset(local_evidence),
        f"missing local-only image evidence: {sorted(LOCAL_ONLY_EVIDENCE - local_evidence)}",
    )
    deferred = set(require_str_list(payload, "deferred_remote_requirements"))
    require(
        DEFERRED_REMOTE_REQUIREMENTS.issubset(deferred),
        f"missing deferred remote image requirements: {sorted(DEFERRED_REMOTE_REQUIREMENTS - deferred)}",
    )
    limits = payload.get("limits")
    require(isinstance(limits, dict), "limits section missing")
    require(limits.get("validate_only") is True, "image publication proof must be validate-only")
    require(limits.get("required_for_local_only_release") is False, "image publication proof must not be required for local-only release")
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
        "out of scope for local-only",
        "optional remote distribution",
        "local-only release",
        "No registry image is pushed",
        "No hosted deployment",
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
