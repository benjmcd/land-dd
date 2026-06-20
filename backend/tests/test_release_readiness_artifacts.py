from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
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
    "threat_proxy_audit",
    "release_package",
    "image_publication",
    "hosted_deployment",
    "source_readiness",
    "source_entitlement",
    "security_scan",
    "data_retention",
    "jurisdiction_readiness",
    "rulepack_readiness",
    "checklist_dry_run",
    "load_test",
    "performance",
    "data_lineage",
    "observability_readiness",
    "production_authority_intake",
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
    "release-package-manifest": "./scripts/run_release_package_check.sh",
    "image-publication": "./scripts/run_image_publication_check.sh",
    "hosted-deployment": "./scripts/run_hosted_deployment_check.sh",
    "release-readiness": "./scripts/run_release_readiness_check.sh",
    "security-scan": "./scripts/run_security_scan.sh",
}
COMPOSED_VALIDATORS = (
    "scripts/image_publication_check.py",
    "scripts/hosted_deployment_check.py",
    "scripts/performance_baseline_check.py",
    "scripts/spatial_query_plan_check.py",
    "scripts/observability_readiness_check.py",
    "scripts/threat_proxy_audit_check.py",
    "scripts/checklist_dry_run_check.py",
    "scripts/source_entitlement_check.py",
    "scripts/production_authority_intake_check.py",
)


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "release_readiness_check.py"
    spec = importlib.util.spec_from_file_location("release_readiness_check", script_path)
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def steps_text(job: dict[str, Any]) -> str:
    return "\n".join(
        str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in job["steps"]
    )


def test_release_readiness_catalog_covers_required_checks_and_blockers() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "release_readiness.yaml").read_text(encoding="utf-8"),
    )

    assert catalog["schema_version"] == "release_readiness_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/release_readiness.md"
    check_ids = {check["id"] for check in catalog["required_checks"]}
    assert check_ids == REQUIRED_CHECKS
    checks = {check["id"]: check for check in catalog["required_checks"]}
    assert checks["release_package"]["ci_job"] == "release-package-manifest"
    for check in catalog["required_checks"]:
        assert (REPO_ROOT / check["proof"]).exists()

    blockers = {blocker["id"]: blocker for blocker in catalog["release_blockers"]}
    assert REQUIRED_BLOCKERS.issubset(set(blockers))
    for blocker in blockers.values():
        assert blocker["status"] == "blocked"
        assert (REPO_ROOT / blocker["authority"]).exists()


def test_ci_has_release_readiness_job() -> None:
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8",
    )
    ci = yaml.safe_load(ci_text)
    job = ci["jobs"]["release-readiness"]
    steps_text = "\n".join(
        str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in job["steps"]
    )

    assert job["permissions"]["contents"] == "read"
    assert "actions/checkout@v6" in steps_text
    assert "actions/setup-python@v6" in steps_text
    assert "python-version: '3.12'" in ci_text
    assert "python -m pip install PyYAML" in steps_text
    assert 'python -m pip install -e "backend[dev]"' in steps_text
    assert "./scripts/run_release_readiness_check.sh" in steps_text


def test_ci_has_release_package_manifest_job() -> None:
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8",
    )
    ci = yaml.safe_load(ci_text)
    job = ci["jobs"]["release-package-manifest"]
    job_steps_text = steps_text(job)

    assert job["permissions"]["contents"] == "read"
    assert "actions/checkout@v6" in job_steps_text
    assert "actions/setup-python@v6" in job_steps_text
    assert "python-version: '3.12'" in ci_text
    assert "python -m pip install PyYAML" in job_steps_text
    assert "./scripts/run_release_package_check.sh" in job_steps_text
    assert "./scripts/build_release_package.sh" in job_steps_text
    assert "./scripts/run_package_manifest_check.sh" in job_steps_text


def test_catalog_ci_jobs_exist_in_workflow() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "release_readiness.yaml").read_text(encoding="utf-8"),
    )
    ci = yaml.safe_load(
        (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8",
        ),
    )
    catalog_jobs = {
        check["ci_job"]
        for check in catalog["required_checks"]
        if isinstance(check.get("ci_job"), str) and check["ci_job"]
    }

    assert catalog_jobs.issubset(set(ci["jobs"]))
    assert catalog_jobs.issubset(set(EXPECTED_CI_PROOFS))
    for job_name in catalog_jobs:
        assert EXPECTED_CI_PROOFS[job_name] in steps_text(ci["jobs"][job_name])


def test_ci_db_verify_sets_explicit_db_smoke_urls() -> None:
    ci = yaml.safe_load(
        (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8",
        ),
    )
    job = ci["jobs"]["db-verify"]
    verify_steps = [
        step for step in job["steps"] if step.get("run") == "./scripts/verify.sh"
    ]

    assert len(verify_steps) == 1
    env = verify_steps[0]["env"]
    assert env["RUN_DB_SMOKE"] == "1"
    assert env["DATABASE_URL_SYNC"] == EXPECTED_DB_SYNC_URL
    assert env["DATABASE_URL"] == EXPECTED_DB_APP_URL


def test_ci_has_image_publication_job() -> None:
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8",
    )
    ci = yaml.safe_load(ci_text)
    job = ci["jobs"]["image-publication"]
    steps_text = "\n".join(
        str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in job["steps"]
    )

    assert job["permissions"]["contents"] == "read"
    assert "actions/checkout@v6" in steps_text
    assert "actions/setup-python@v6" in steps_text
    assert "python-version: '3.12'" in ci_text
    assert "python -m pip install PyYAML" in steps_text
    assert "./scripts/run_image_publication_check.sh" in steps_text


def test_ci_has_hosted_deployment_job() -> None:
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8",
    )
    ci = yaml.safe_load(ci_text)
    job = ci["jobs"]["hosted-deployment"]
    steps_text = "\n".join(
        str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in job["steps"]
    )

    assert job["permissions"]["contents"] == "read"
    assert "actions/checkout@v6" in steps_text
    assert "actions/setup-python@v6" in steps_text
    assert "python-version: '3.12'" in ci_text
    assert "python -m pip install PyYAML" in steps_text
    assert "./scripts/run_hosted_deployment_check.sh" in steps_text


def test_release_readiness_runbook_records_limits_and_validation() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "release_readiness.md").read_text(
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
        "release-package-manifest",
        "threat-proxy-audit",
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
        "performance_baseline.yaml",
        "run_performance_baseline_check.ps1",
        "threat_proxy_audit.yaml",
        "run_threat_proxy_audit_check.ps1",
        "checklist_dry_run.yaml",
        "run_checklist_dry_run_check.ps1",
        "source_entitlements.yaml",
        "run_source_entitlement_check.ps1",
        "production_authority_intake.yaml",
        "run_production_authority_intake_check.ps1",
        "spatial_query_plan.yaml",
        "run_spatial_query_plan_check.ps1",
        "spatial_query_plan_check.py",
        "validate-only static proof",
        "load_test_result_v1",
        "jurisdiction_readiness.md",
        "rulepack_readiness.md",
        "data_lineage",
        "DATABASE_URL_SYNC",
        "DATABASE_URL",
        "sources=8 ready=7 blocked=1",
        "build_release_package.ps1",
        "run_package_manifest_check.ps1",
        "run_image_publication_check.ps1",
        "run_hosted_deployment_check.ps1",
        "executes the image-publication and hosted-deployment validators",
        "No container image is pushed",
        "does not run `EXPLAIN ANALYZE` against a live or hosted database by default",
        "published registry-image attestation",
        "source-entitlement check",
        "production-authority intake check",
    ):
        assert phrase in runbook


def test_release_readiness_composes_image_and_hosted_validators(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr(validator.subprocess, "run", fake_run)

    validator.validate_composed_contracts()

    assert [args[1] for args, _ in calls] == list(COMPOSED_VALIDATORS)
    for args, kwargs in calls:
        assert args[0] == sys.executable
        assert kwargs["cwd"] == REPO_ROOT
        assert kwargs["check"] is True
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True


def test_release_readiness_source_blockers_remain_explicit() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["source_count"] == 8
    assert payload["ready_count"] == 7
    assert payload["blocked_count"] == 1
    blocked = {
        source["source_registry_id"]
        for source in payload["sources"]
        if source["connector_ready"] is False
    }
    assert blocked == {"DS-017"}
    assert "DS-011" not in blocked
    ds010 = next(
        source
        for source in payload["sources"]
        if source["source_registry_id"] == "DS-010"
    )
    assert ds010["connector_ready"] is True
    assert ds010["connector_surfaces"] == [
        "immediate_operator_api",
        "request_time_orchestration",
    ]
    assert "durable_live_job" not in ds010["connector_surfaces"]


def test_release_readiness_scripts_expect_current_source_counts() -> None:
    script = (REPO_ROOT / "scripts" / "release_readiness_check.py").read_text(
        encoding="utf-8",
    )

    assert 'ready_count") == 7' in script
    assert 'blocked_count") == 1' in script
    assert "DATABASE_URL_SYNC" in script
    assert "DATABASE_URL" in script
    assert '"security_scan"' in script
    assert '"data_retention"' in script
    assert '"load_test"' in script
    assert '"performance"' in script
    assert '"data_lineage"' in script
    assert '"threat_proxy_audit"' in script
    assert '"checklist_dry_run"' in script
    assert '"source_entitlement"' in script
    assert '"production_authority_intake"' in script
    assert '"config/performance_baseline.yaml"' in script
    assert '"config/threat_proxy_audit.yaml"' in script
    assert '"config/checklist_dry_run.yaml"' in script
    assert '"config/source_entitlements.yaml"' in script
    assert '"config/production_authority_intake.yaml"' in script
    assert '"scripts/performance_baseline_check.py"' in script
    assert '"scripts/threat_proxy_audit_check.py"' in script
    assert '"scripts/checklist_dry_run_check.py"' in script
    assert '"scripts/source_entitlement_check.py"' in script
    assert '"scripts/production_authority_intake_check.py"' in script
    assert '"config/spatial_query_plan.yaml"' in script
    assert '"scripts/spatial_query_plan_check.py"' in script
    assert '{"DS-017"}' in script
    assert '{"DS-011", "DS-017"}' not in script
    assert '{"DS-011", "DS-017", "DS-023"}' not in script


def test_release_readiness_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "run_release_readiness_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_release_readiness_check.sh").is_file()
    assert (REPO_ROOT / "scripts" / "release_readiness_check.py").is_file()


def test_release_readiness_wrappers_delegate_to_shared_validator() -> None:
    for script_path in (
        REPO_ROOT / "scripts" / "run_release_readiness_check.ps1",
        REPO_ROOT / "scripts" / "run_release_readiness_check.sh",
    ):
        script = script_path.read_text(encoding="utf-8")

        assert "release_readiness_check.py" in script
        assert "release readiness check: ok" in script
