from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

EXPECTED_PACKAGE_SCHEMA = "release_package_v1"
EXPECTED_IMAGE_SCHEMA = "image_publication_v1"
EXPECTED_HOSTED_SCHEMA = "hosted_deployment_v1"
EXPECTED_PACKAGE_NAME = "land-diligence"
EXPECTED_IMAGE_NAME = "land-diligence-backend"
EXPECTED_SERVICE_NAME = "land-diligence-api"
EXPECTED_IMAGE_CATALOG = "config/image_publication.yaml"
EXPECTED_RELEASE_CATALOG = "config/release_readiness.yaml"

EXPECTED_PACKAGE_REQUIRED_GATES = {
    "scripts/run_release_package_check.ps1",
    "scripts/run_release_readiness_check.ps1",
    "scripts/verify.ps1",
}
EXPECTED_IMAGE_BLOCKERS = {
    "registry_repository_authority",
    "hosted_deployment_authority",
    "registry_image_attestation_authority",
    "signed_image_sbom_authority",
}
EXPECTED_HOSTED_BLOCKERS = {
    "hosted_platform_selected",
    "domain_tls_authority",
    "secrets_manager_authority",
    "database_instance_authority",
    "registry_image_digest_available",
    "hosted_billing_reconciliation",
    "hosted_alerting_route",
}
EXPECTED_HOSTED_RUNTIME_INPUTS = {
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
EXPECTED_HOSTED_RUNTIME_EVIDENCE = {
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
EXPECTED_IMAGE_LIMITS = {
    "validate_only": True,
    "pushes_registry_image": False,
    "creates_hosted_deployment": False,
    "signs_or_publishes_attestations": False,
}
EXPECTED_HOSTED_LIMITS = {
    "validate_only": True,
    "creates_hosted_deployment": False,
    "mutates_hosted_infrastructure": False,
    "writes_secrets": False,
    "opens_public_endpoint": False,
}


class DeploymentReadinessError(RuntimeError):
    """Raised when deployment-path catalogs cannot be trusted for UI rendering."""


@dataclass(frozen=True)
class PackageReadiness:
    schema_version: str
    package_name: str
    output_dir: str
    manifest_filename: str
    include_count: int
    exclude_part_count: int
    exclude_suffix_count: int
    required_gates: tuple[str, ...]


@dataclass(frozen=True)
class ImageReadiness:
    schema_version: str
    image_name: str
    dockerfile: str
    context: str
    local_tag_template: str
    registry_image_env: str
    required_gates: tuple[str, ...]
    required_attestations: tuple[str, ...]
    blockers: tuple[str, ...]
    limits: dict[str, bool]


@dataclass(frozen=True)
class HostedReadiness:
    schema_version: str
    service_name: str
    runtime: str
    image_publication_catalog: str
    release_readiness_catalog: str
    required_pre_deploy_gates: tuple[str, ...]
    required_runtime_inputs: tuple[str, ...]
    required_runtime_evidence: tuple[str, ...]
    attestation_required_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    limits: dict[str, bool]


@dataclass(frozen=True)
class DeploymentReadiness:
    package: PackageReadiness
    image: ImageReadiness
    hosted: HostedReadiness


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_deployment_readiness(repo_root: Path | None = None) -> DeploymentReadiness:
    root = repo_root or repo_root_from_app()
    package_payload = _read_yaml(root / "config" / "release_package.yaml")
    image_payload = _read_yaml(root / "config" / "image_publication.yaml")
    hosted_payload = _read_yaml(root / "config" / "hosted_deployment.yaml")
    return parse_deployment_readiness(
        package_payload,
        image_payload,
        hosted_payload,
        root=root,
    )


def parse_deployment_readiness(
    package_payload: dict[str, Any],
    image_payload: dict[str, Any],
    hosted_payload: dict[str, Any],
    *,
    root: Path,
) -> DeploymentReadiness:
    return DeploymentReadiness(
        package=_parse_package(package_payload, root),
        image=_parse_image(image_payload, root),
        hosted=_parse_hosted(hosted_payload, root),
    )


def _parse_package(payload: dict[str, Any], root: Path) -> PackageReadiness:
    schema_version = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_PACKAGE_SCHEMA,
        "release package schema_version",
    )
    package_name = _require_exact_text(
        payload.get("package_name"),
        EXPECTED_PACKAGE_NAME,
        "package_name",
    )
    output_dir = _require_text(payload.get("output_dir"), "package output_dir missing")
    manifest_filename = _require_text(
        payload.get("manifest_filename"),
        "package manifest filename missing",
    )
    include_paths = _require_text_tuple(payload.get("include_paths"), "include_paths missing")
    for path_text in include_paths:
        _require_existing(root, path_text)
    exclude_parts = _require_text_tuple(
        payload.get("exclude_path_parts"),
        "exclude_path_parts missing",
    )
    exclude_suffixes = _require_text_tuple(
        payload.get("exclude_suffixes"),
        "exclude_suffixes missing",
    )
    required_gates = _require_text_tuple(
        payload.get("required_release_gates"),
        "required_release_gates missing",
    )
    if set(required_gates) != EXPECTED_PACKAGE_REQUIRED_GATES:
        raise DeploymentReadinessError("release package required gate set mismatch")
    for path_text in required_gates:
        _require_existing(root, path_text)
    return PackageReadiness(
        schema_version=schema_version,
        package_name=package_name,
        output_dir=output_dir,
        manifest_filename=manifest_filename,
        include_count=len(include_paths),
        exclude_part_count=len(exclude_parts),
        exclude_suffix_count=len(exclude_suffixes),
        required_gates=tuple(sorted(required_gates)),
    )


def _parse_image(payload: dict[str, Any], root: Path) -> ImageReadiness:
    schema_version = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_IMAGE_SCHEMA,
        "image publication schema_version",
    )
    image = _require_mapping(payload.get("image"), "image section missing")
    image_name = _require_exact_text(image.get("name"), EXPECTED_IMAGE_NAME, "image.name")
    dockerfile = _require_text(image.get("dockerfile"), "image dockerfile missing")
    _require_existing(root, dockerfile)
    context = _require_exact_text(image.get("context"), ".", "image context")
    local_tag_template = _require_text(
        image.get("local_tag_template"),
        "local tag template missing",
    )
    registry_image_env = _require_exact_text(
        image.get("registry_image_env"),
        "REGISTRY_IMAGE",
        "registry image env",
    )
    required_gates = _require_text_tuple(payload.get("required_gates"), "image gates missing")
    for path_text in required_gates:
        _require_existing(root, path_text)
    required_attestations = _require_text_tuple(
        payload.get("required_attestations"),
        "image attestations missing",
    )
    blockers = _blockers(payload, EXPECTED_IMAGE_BLOCKERS, "image publication")
    limits = _bool_mapping(payload.get("limits"), "image limits missing")
    if limits != EXPECTED_IMAGE_LIMITS:
        raise DeploymentReadinessError("image publication limits changed")
    evidence = _require_mapping(
        payload.get("attestation_evidence"),
        "image attestation evidence missing",
    )
    _require_exact_text(evidence.get("status"), "not_available", "image evidence status")
    _require_existing(
        root,
        _require_text(evidence.get("authority"), "image evidence authority missing"),
    )
    evidence_blockers = _blockers(evidence, EXPECTED_IMAGE_BLOCKERS, "image evidence")
    if evidence_blockers != blockers:
        raise DeploymentReadinessError("image evidence blocker set mismatch")
    return ImageReadiness(
        schema_version=schema_version,
        image_name=image_name,
        dockerfile=dockerfile,
        context=context,
        local_tag_template=local_tag_template,
        registry_image_env=registry_image_env,
        required_gates=tuple(sorted(required_gates)),
        required_attestations=tuple(sorted(required_attestations)),
        blockers=blockers,
        limits=limits,
    )


def _parse_hosted(payload: dict[str, Any], root: Path) -> HostedReadiness:
    schema_version = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_HOSTED_SCHEMA,
        "hosted deployment schema_version",
    )
    deployment = _require_mapping(payload.get("deployment"), "deployment section missing")
    service_name = _require_exact_text(
        deployment.get("service_name"),
        EXPECTED_SERVICE_NAME,
        "service_name",
    )
    runtime = _require_exact_text(
        deployment.get("runtime"),
        "containerized-fastapi",
        "deployment runtime",
    )
    image_catalog = _require_exact_text(
        deployment.get("image_publication_catalog"),
        EXPECTED_IMAGE_CATALOG,
        "image publication catalog",
    )
    release_catalog = _require_exact_text(
        deployment.get("release_readiness_catalog"),
        EXPECTED_RELEASE_CATALOG,
        "release readiness catalog",
    )
    _require_existing(root, image_catalog)
    _require_existing(root, release_catalog)
    gates = _require_text_tuple(
        payload.get("required_pre_deploy_gates"),
        "pre-deploy gates missing",
    )
    for path_text in gates:
        _require_existing(root, path_text)
    runtime_inputs = _require_text_tuple(
        payload.get("required_runtime_inputs"),
        "runtime inputs missing",
    )
    if set(runtime_inputs) != EXPECTED_HOSTED_RUNTIME_INPUTS:
        raise DeploymentReadinessError("hosted runtime input set mismatch")
    runtime_evidence = _require_text_tuple(
        payload.get("required_runtime_evidence"),
        "runtime evidence missing",
    )
    if set(runtime_evidence) != EXPECTED_HOSTED_RUNTIME_EVIDENCE:
        raise DeploymentReadinessError("hosted runtime evidence set mismatch")
    blockers = _blockers(payload, EXPECTED_HOSTED_BLOCKERS, "hosted deployment")
    limits = _bool_mapping(payload.get("limits"), "hosted limits missing")
    if limits != EXPECTED_HOSTED_LIMITS:
        raise DeploymentReadinessError("hosted deployment limits changed")
    evidence = _require_mapping(
        payload.get("attestation_evidence"),
        "hosted attestation evidence missing",
    )
    _require_exact_text(evidence.get("status"), "not_available", "hosted evidence status")
    _require_existing(
        root,
        _require_text(evidence.get("authority"), "hosted evidence authority missing"),
    )
    attestation_fields = _require_text_tuple(
        evidence.get("required_fields"),
        "hosted attestation fields missing",
    )
    if set(attestation_fields) != EXPECTED_HOSTED_RUNTIME_EVIDENCE:
        raise DeploymentReadinessError("hosted attestation field set mismatch")
    evidence_blockers = _blockers(evidence, EXPECTED_HOSTED_BLOCKERS, "hosted evidence")
    if evidence_blockers != blockers:
        raise DeploymentReadinessError("hosted evidence blocker set mismatch")
    return HostedReadiness(
        schema_version=schema_version,
        service_name=service_name,
        runtime=runtime,
        image_publication_catalog=image_catalog,
        release_readiness_catalog=release_catalog,
        required_pre_deploy_gates=tuple(sorted(gates)),
        required_runtime_inputs=tuple(sorted(runtime_inputs)),
        required_runtime_evidence=tuple(sorted(runtime_evidence)),
        attestation_required_fields=tuple(sorted(attestation_fields)),
        blockers=blockers,
        limits=limits,
    )


def _blockers(
    payload: dict[str, Any],
    expected: set[str],
    label: str,
) -> tuple[str, ...]:
    blockers = _require_text_tuple(payload.get("blocked_until"), f"{label} blockers missing")
    if set(blockers) != expected:
        raise DeploymentReadinessError(f"{label} blocker set mismatch")
    return tuple(sorted(blockers))


def _read_yaml(path: Path) -> dict[str, Any]:
    label = _catalog_label(path)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise DeploymentReadinessError(f"cannot read {label}") from exc
    return _require_mapping(payload, f"{label} must be a mapping")


def _require_existing(root: Path, path_text: str) -> None:
    path = _resolved_repo_path(root, path_text)
    if not path.exists():
        raise DeploymentReadinessError(f"referenced deployment artifact missing: {path_text}")


def _resolved_repo_path(root: Path, path_text: str) -> Path:
    if not path_text:
        raise DeploymentReadinessError("empty path reference")
    candidate = Path(_normalize_path(path_text))
    if candidate.is_absolute():
        raise DeploymentReadinessError(f"path must be repo-relative: {path_text}")
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise DeploymentReadinessError(f"path escapes repo root: {path_text}") from exc
    return resolved


def _require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DeploymentReadinessError(message)
    return value


def _require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise DeploymentReadinessError(message)
    return value


def _require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DeploymentReadinessError(message)
    return value.strip()


def _require_exact_text(value: Any, expected: str, label: str) -> str:
    text = _require_text(value, f"{label} missing")
    if text != expected:
        raise DeploymentReadinessError(f"{label} must be {expected}")
    return text


def _require_text_tuple(value: Any, message: str) -> tuple[str, ...]:
    values = _require_list(value, message)
    text_values = tuple(_require_text(item, message) for item in values)
    if not text_values:
        raise DeploymentReadinessError(message)
    return text_values


def _bool_mapping(value: Any, message: str) -> dict[str, bool]:
    raw = _require_mapping(value, message)
    if not all(isinstance(key, str) and isinstance(val, bool) for key, val in raw.items()):
        raise DeploymentReadinessError(message)
    return {str(key): bool(val) for key, val in raw.items()}


def _normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def _catalog_label(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return path.name
