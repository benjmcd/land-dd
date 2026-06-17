from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "config/release_readiness.yaml",
    "config/release_package.yaml",
    "config/image_publication.yaml",
    "config/hosted_deployment.yaml",
    "docs/runbooks/release_readiness.md",
    "docs/runbooks/release_package.md",
    "docs/runbooks/image_publication.md",
    "docs/runbooks/hosted_deployment.md",
    "docs/runbooks/security_scan.md",
    "docs/runbooks/data_retention.md",
    "docs/runbooks/load_testing.md",
    "docs/runbooks/performance.md",
    "docs/checklists/jurisdiction_readiness.md",
    "docs/checklists/rulepack_readiness.md",
    ".github/workflows/ci.yml",
    "backend/pyproject.toml",
    "backend/requirements-prod.lock",
    "backend/Dockerfile",
    "backend/app/api/reports.py",
    "docker-compose.yml",
    "docs/sbom/backend-prod-sbom.json",
    "scripts/verify.ps1",
    "scripts/verify.sh",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_provenance_check.ps1",
    "scripts/run_supply_chain_check.ps1",
    "scripts/run_container_scan_check.ps1",
    "scripts/run_release_package_check.ps1",
    "scripts/run_image_publication_check.ps1",
    "scripts/run_hosted_deployment_check.ps1",
    "scripts/run_security_scan.ps1",
    "scripts/run_data_retention_check.ps1",
    "scripts/run_load_test.ps1",
    "scripts/run_load_test.sh",
    "scripts/load_test_runner.py",
    "scripts/source_readiness.py",
    "scripts/release_readiness_check.py",
)
REQUIRED_CHECKS = {
    "workspace_verify",
    "db_verify",
    "deployment_smoke",
    "dependency_provenance",
    "supply_chain_scan",
    "container_image_scan",
    "backup_restore",
    "incident_rollback",
    "alert_rules",
    "cost_monitoring",
    "access_control",
    "release_package",
    "image_publication",
    "hosted_deployment",
    "source_readiness",
    "security_scan",
    "data_retention",
    "jurisdiction_readiness",
    "rulepack_readiness",
    "load_test",
    "performance",
    "data_lineage",
}
REQUIRED_CI_JOBS = {
    "verify",
    "db-verify",
    "supply-chain",
    "dependency-attestations",
    "container-image-scan",
    "access-control",
    "image-publication",
    "hosted-deployment",
    "release-readiness",
    "security-scan",
}
REQUIRED_BLOCKERS = {
    "hosted_deployment_attestation",
    "published_registry_image_attestation",
    "hosted_billing_reconciliation",
    "non_ready_must_sources",
    "full_user_auth_rbac",
    "hosted_alerting",
}
EXPECTED_DB_SYNC_URL = "postgresql://land:land@localhost:5432/land_diligence"
EXPECTED_DB_APP_URL = "postgresql+psycopg://land:land@localhost:5432/land_diligence"
EXPECTED_CI_PROOFS = {
    "verify": "./scripts/verify.sh",
    "db-verify": "./scripts/verify.sh",
    "supply-chain": "./scripts/run_supply_chain_check.sh",
    "dependency-attestations": "./scripts/run_provenance_check.sh",
    "container-image-scan": "./scripts/run_container_scan_check.sh",
    "access-control": "./scripts/run_access_control_check.sh",
    "image-publication": "./scripts/run_image_publication_check.sh",
    "hosted-deployment": "./scripts/run_hosted_deployment_check.sh",
    "release-readiness": "./scripts/run_release_readiness_check.sh",
    "security-scan": "./scripts/run_security_scan.sh",
}
COMPOSED_VALIDATORS = (
    "scripts/image_publication_check.py",
    "scripts/hosted_deployment_check.py",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return value


def require_non_empty_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise SystemExit(message)
    return value


def require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value:
        raise SystemExit(message)
    return value


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require(
        (ROOT / normalized).exists(),
        f"referenced release artifact missing: {normalized}",
    )


def job_steps(job: dict[str, Any], job_name: str) -> list[dict[str, Any]]:
    steps = job.get("steps")
    raw_steps = require_non_empty_list(steps, f"{job_name} job has no steps")
    typed_steps = [step for step in raw_steps if isinstance(step, dict)]
    require(bool(typed_steps), f"{job_name} job has no mapping steps")
    return typed_steps


def step_text(job: dict[str, Any], job_name: str) -> str:
    return "\n".join(
        str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in job_steps(job, job_name)
    )


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_db_verify_job(job: dict[str, Any]) -> None:
    verify_steps = [
        step
        for step in job_steps(job, "db-verify")
        if step.get("run") == "./scripts/verify.sh"
    ]
    require(len(verify_steps) == 1, "db-verify job must run verify.sh exactly once")
    env = require_mapping(verify_steps[0].get("env"), "db-verify verify step env missing")
    require(env.get("RUN_DB_SMOKE") == "1", "db-verify must enable DB smoke")
    require(
        env.get("DATABASE_URL_SYNC") == EXPECTED_DB_SYNC_URL,
        "db-verify sync DB URL mismatch",
    )
    require(
        env.get("DATABASE_URL") == EXPECTED_DB_APP_URL,
        "db-verify app DB URL mismatch",
    )


def validate_catalog() -> None:
    payload = require_mapping(
        yaml.safe_load(
            (ROOT / "config" / "release_readiness.yaml").read_text(encoding="utf-8"),
        ),
        "release readiness catalog must be a mapping",
    )
    require(
        payload.get("schema_version") == "release_readiness_v1",
        "unexpected release readiness schema",
    )
    require(
        payload.get("operator_runbook") == "docs/runbooks/release_readiness.md",
        "operator runbook mismatch",
    )
    checks = require_non_empty_list(
        payload.get("required_checks"),
        "release readiness checks missing",
    )
    check_ids: set[str] = set()
    for check in checks:
        check = require_mapping(check, "each release readiness check must be a mapping")
        check_id = require_text(check.get("id"), "release readiness check id missing")
        require(check_id not in check_ids, f"duplicate release readiness check id: {check_id}")
        check_ids.add(check_id)
        proof = require_text(check.get("proof"), f"{check_id} proof missing")
        require_existing(proof)
    missing_checks = sorted(REQUIRED_CHECKS - check_ids)
    unexpected_checks = sorted(check_ids - REQUIRED_CHECKS)
    require(not missing_checks, f"missing release checks: {missing_checks}")
    require(not unexpected_checks, f"unexpected release checks: {unexpected_checks}")

    blockers = require_non_empty_list(
        payload.get("release_blockers"),
        "release blockers missing",
    )
    blocker_ids: set[str] = set()
    for blocker in blockers:
        blocker = require_mapping(blocker, "each release blocker must be a mapping")
        blocker_id = require_text(blocker.get("id"), "release blocker id missing")
        blocker_ids.add(blocker_id)
        require(blocker.get("status") == "blocked", f"{blocker_id} must remain blocked")
        authority = require_text(blocker.get("authority"), f"{blocker_id} authority missing")
        require_existing(authority)
    require(
        REQUIRED_BLOCKERS.issubset(blocker_ids),
        f"missing release blockers: {sorted(REQUIRED_BLOCKERS - blocker_ids)}",
    )


def validate_ci() -> None:
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    ci = require_mapping(yaml.safe_load(ci_text), "ci workflow must be a mapping")
    jobs = require_mapping(ci.get("jobs"), "ci workflow jobs missing")
    release_catalog = require_mapping(
        yaml.safe_load(
            (ROOT / "config" / "release_readiness.yaml").read_text(encoding="utf-8"),
        ),
        "release readiness catalog must be a mapping",
    )
    catalog_checks = require_non_empty_list(
        release_catalog.get("required_checks"),
        "release readiness checks missing",
    )
    catalog_ci_jobs = {
        ci_job
        for check in catalog_checks
        if isinstance(check, dict)
        for ci_job in (check.get("ci_job"),)
        if isinstance(ci_job, str) and ci_job
    }
    require(
        REQUIRED_CI_JOBS.issubset(set(jobs)),
        f"missing CI jobs: {sorted(REQUIRED_CI_JOBS - set(jobs))}",
    )
    require(
        catalog_ci_jobs.issubset(set(jobs)),
        f"missing catalog CI jobs: {sorted(catalog_ci_jobs - set(jobs))}",
    )
    require(
        catalog_ci_jobs.issubset(set(EXPECTED_CI_PROOFS)),
        f"missing expected CI proof mapping: {sorted(catalog_ci_jobs - set(EXPECTED_CI_PROOFS))}",
    )
    for job_name in sorted(catalog_ci_jobs):
        job = require_mapping(jobs.get(job_name), f"{job_name} job missing")
        proof = EXPECTED_CI_PROOFS[job_name]
        require(
            proof in step_text(job, job_name),
            f"{job_name} job must run {proof}",
        )
    validate_db_verify_job(require_mapping(jobs.get("db-verify"), "db-verify job missing"))
    job = require_mapping(jobs.get("release-readiness"), "release-readiness job missing")
    permissions = require_mapping(
        job.get("permissions"),
        "release-readiness permissions missing",
    )
    require(
        permissions.get("contents") == "read",
        "release-readiness must use read-only contents permission",
    )
    text = step_text(job, "release-readiness")
    require("actions/checkout@v6" in text, "release-readiness job must checkout repo")
    require(
        "actions/setup-python@v6" in text,
        "release-readiness job must setup Python",
    )
    require("python-version: '3.12'" in ci_text, "release-readiness job must use Python 3.12")
    require(
        "python -m pip install PyYAML" in text,
        "release-readiness job must install PyYAML for static catalog parsing",
    )
    require(
        "./scripts/run_release_readiness_check.sh" in text,
        "release-readiness job must run POSIX release proof",
    )

    image_job = require_mapping(jobs.get("image-publication"), "image-publication job missing")
    image_permissions = require_mapping(
        image_job.get("permissions"),
        "image-publication permissions missing",
    )
    require(
        image_permissions.get("contents") == "read",
        "image-publication must use read-only contents permission",
    )
    image_text = step_text(image_job, "image-publication")
    require("actions/checkout@v6" in image_text, "image-publication job must checkout repo")
    require(
        "actions/setup-python@v6" in image_text,
        "image-publication job must setup Python",
    )
    require(
        "python -m pip install PyYAML" in image_text,
        "image-publication job must install PyYAML",
    )
    require(
        "./scripts/run_image_publication_check.sh" in image_text,
        "image-publication job must run POSIX image publication proof",
    )

    hosted_job = require_mapping(jobs.get("hosted-deployment"), "hosted-deployment job missing")
    hosted_permissions = require_mapping(
        hosted_job.get("permissions"),
        "hosted-deployment permissions missing",
    )
    require(
        hosted_permissions.get("contents") == "read",
        "hosted-deployment must use read-only contents permission",
    )
    hosted_text = step_text(hosted_job, "hosted-deployment")
    require("actions/checkout@v6" in hosted_text, "hosted-deployment job must checkout repo")
    require(
        "actions/setup-python@v6" in hosted_text,
        "hosted-deployment job must setup Python",
    )
    require(
        "python -m pip install PyYAML" in hosted_text,
        "hosted-deployment job must install PyYAML",
    )
    require(
        "./scripts/run_hosted_deployment_check.sh" in hosted_text,
        "hosted-deployment job must run POSIX hosted deployment proof",
    )


def validate_source_readiness() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = require_mapping(
        json.loads(result.stdout),
        "source readiness output must be a mapping",
    )
    require(
        payload.get("source_count") == 8,
        "Must source count changed without release catalog update",
    )
    require(
        payload.get("ready_count") == 7,
        "Must ready count changed without release catalog update",
    )
    require(
        payload.get("blocked_count") == 1,
        "Must blocked count changed without release catalog update",
    )
    sources = require_non_empty_list(payload.get("sources"), "source readiness sources missing")
    blocked: set[str] = set()
    for source in sources:
        source = require_mapping(source, "each source readiness entry must be a mapping")
        if source.get("connector_ready") is False:
            blocked.add(str(source.get("source_registry_id")))
    require(blocked == {"DS-017"}, "expected Must-source blocker set changed")


def validate_composed_contracts() -> None:
    for script_path in COMPOSED_VALIDATORS:
        subprocess.run(
            [sys.executable, script_path],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )


def validate_runbook() -> None:
    runbook = (ROOT / "docs" / "runbooks" / "release_readiness.md").read_text(
        encoding="utf-8",
    )
    for phrase in (
        "run_release_readiness_check.ps1",
        "validate-only",
        "verify",
        "db-verify",
        "supply-chain",
        "dependency-attestations",
        "container-image-scan",
        "access-control",
        "release-package",
        "image-publication",
        "hosted-deployment",
        "security-scan",
        "release-readiness",
        "run_security_scan.ps1",
        "run_data_retention_check.ps1",
        "run_load_test.ps1",
        "load_testing.md",
        "performance.md",
        "jurisdiction_readiness.md",
        "rulepack_readiness.md",
        "data_lineage",
        "DATABASE_URL_SYNC",
        "DATABASE_URL",
        "sources=8 ready=7 blocked=1",
        "build_release_package.ps1",
        "run_image_publication_check.ps1",
        "run_hosted_deployment_check.ps1",
        "executes the image-publication and hosted-deployment validators",
        "No container image is pushed",
        "published registry-image attestation",
    ):
        require(phrase in runbook, f"release readiness runbook missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_ci()
    validate_source_readiness()
    validate_composed_contracts()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
