from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "config/image_publication.yaml",
    "docs/runbooks/image_publication.md",
    "backend/Dockerfile",
    "docker-compose.yml",
    "scripts/verify.ps1",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_container_scan_check.ps1",
    "scripts/run_release_package_check.ps1",
    "scripts/run_release_readiness_check.ps1",
    "scripts/image_publication_check.py",
    "scripts/run_image_publication_check.ps1",
    "scripts/run_image_publication_check.sh",
)
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
ATTESTATION_EVIDENCE_AUTHORITY = "docs/runbooks/image_publication.md"
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require(
        (ROOT / normalized).exists(),
        f"referenced image-publication artifact missing: {normalized}",
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
            f"required image-publication artifact missing: {path_text}",
        )


def validate_catalog() -> None:
    payload = yaml.safe_load(read_text("config/image_publication.yaml"))
    require(isinstance(payload, dict), "image publication catalog must be a mapping")
    require(
        payload.get("schema_version") == "image_publication_v1",
        "unexpected image publication schema",
    )

    image = payload.get("image")
    require(isinstance(image, dict), "image section missing")
    require(image.get("name") == "land-diligence-backend", "image name mismatch")
    require(image.get("dockerfile") == "backend/Dockerfile", "image Dockerfile mismatch")
    require(image.get("context") == ".", "image build context must be repo root")
    require(
        image.get("local_tag_template") == "land-diligence-backend:{git_sha}",
        "local tag template mismatch",
    )
    require(image.get("registry_image_env") == "REGISTRY_IMAGE", "registry image env mismatch")
    dockerfile = image.get("dockerfile")
    require(isinstance(dockerfile, str), "image Dockerfile path missing")
    require_existing(dockerfile)

    gates = set(require_str_list(payload, "required_gates"))
    missing_gates = sorted(REQUIRED_GATES - gates)
    require(not missing_gates, f"missing image publication gates: {missing_gates}")
    for gate in gates:
        require_existing(gate)

    attestations = set(require_str_list(payload, "required_attestations"))
    missing_attestations = sorted(REQUIRED_ATTESTATIONS - attestations)
    require(
        not missing_attestations,
        f"missing image publication attestation requirements: {missing_attestations}",
    )

    blockers = set(require_str_list(payload, "blocked_until"))
    missing_blockers = sorted(REQUIRED_BLOCKERS - blockers)
    require(not missing_blockers, f"missing image publication blockers: {missing_blockers}")

    evidence = payload.get("attestation_evidence")
    require(isinstance(evidence, dict), "attestation_evidence section missing")
    status = evidence.get("status")
    require(
        isinstance(status, str) and status in ALLOWED_ATTESTATION_STATUSES,
        "attestation_evidence status must be not_available or an available proof status",
    )
    authority = evidence.get("authority")
    require(
        authority == ATTESTATION_EVIDENCE_AUTHORITY,
        "attestation_evidence authority must point to the image publication runbook",
    )
    require_existing(ATTESTATION_EVIDENCE_AUTHORITY)

    evidence_fields = set(require_str_list(evidence, "required_fields"))
    require(
        evidence_fields == REQUIRED_ATTESTATIONS,
        "attestation_evidence required_fields must exactly match required_attestations",
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
        template_keys == REQUIRED_ATTESTATIONS,
        "attestation_evidence evidence_template keys must exactly match required_attestations",
    )
    if status in AVAILABLE_ATTESTATION_STATUSES:
        empty_fields = sorted(
            field
            for field in REQUIRED_ATTESTATIONS
            if is_empty_evidence_value(template.get(field))
        )
        require(
            not empty_fields,
            f"attestation_evidence status {status} requires values for: {empty_fields}",
        )

    limits = payload.get("limits")
    require(isinstance(limits, dict), "limits section missing")
    require(limits.get("validate_only") is True, "image publication proof must be validate-only")
    require(
        limits.get("pushes_registry_image") is False,
        "image publication proof must not push registry images",
    )
    require(
        limits.get("creates_hosted_deployment") is False,
        "image publication proof must not create hosted deployments",
    )
    require(
        limits.get("signs_or_publishes_attestations") is False,
        "image publication proof must not sign or publish attestations",
    )


def validate_no_validate_only_pushes() -> None:
    for relative_path in (
        ".github/workflows/ci.yml",
        "scripts/run_container_scan_check.ps1",
        "scripts/run_container_scan_check.sh",
        "scripts/run_release_readiness_check.ps1",
        "scripts/run_release_readiness_check.sh",
        "scripts/run_image_publication_check.ps1",
        "scripts/run_image_publication_check.sh",
    ):
        text = read_text(relative_path)
        require(
            "docker " + "push" not in text,
            f"validate-only artifact must not run a registry push command: {relative_path}",
        )
        require(
            "docker/" + "login-action" not in text,
            f"validate-only artifact must not login to a registry: {relative_path}",
        )
        require(
            "cosign " + "sign" not in text,
            f"validate-only artifact must not sign images: {relative_path}",
        )


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/image_publication.md")
    for phrase in (
        "run_image_publication_check.ps1",
        "scripts/image_publication_check.py",
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
    validate_required_files()
    validate_catalog()
    validate_no_validate_only_pushes()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
