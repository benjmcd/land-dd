from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path
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
    "release_package",
    "source_readiness",
}
REQUIRED_BLOCKERS = {
    "non_ready_must_sources",
}
REQUIRED_DEFERRED = {
    "billing_hosted_billing_reconciliation",
    "hosted_deployment",
    "hosted_deployment_attestation",
    "hosted_alerting",
    "hosted_log_retention",
    "published_registry_image_attestation",
    "registry_push_signing_requirements",
    "automatic_key_rotation_external_secret_manager",
    "full_user_auth_rbac_oidc_user_accounts",
}
REMOTE_ONLY_CHECKS = {"image_publication", "hosted_deployment"}


def test_release_readiness_catalog_covers_required_checks_and_blockers() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "release_readiness.yaml").read_text(encoding="utf-8"),
    )

    assert catalog["schema_version"] == "release_readiness_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/release_readiness.md"
    check_ids = {check["id"] for check in catalog["required_checks"]}
    assert REQUIRED_CHECKS.issubset(check_ids)
    assert check_ids.isdisjoint(REMOTE_ONLY_CHECKS)
    for check in catalog["required_checks"]:
        assert (REPO_ROOT / check["proof"]).exists()

    blockers = {blocker["id"]: blocker for blocker in catalog["release_blockers"]}
    assert REQUIRED_BLOCKERS.issubset(set(blockers))
    for blocker in blockers.values():
        assert blocker["status"] == "blocked"
        assert (REPO_ROOT / blocker["authority"]).exists()

    deferred = {item["id"]: item for item in catalog["local_only_deferred"]}
    assert REQUIRED_DEFERRED.issubset(set(deferred))
    for item in deferred.values():
        assert item["status"] == "out_of_scope_local_only"
        assert item["reason"]
        assert (REPO_ROOT / item["authority"]).exists()


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
    assert "actions/checkout@v4" in steps_text
    assert "actions/setup-python@v5" in steps_text
    assert "python-version: '3.12'" in ci_text
    assert "python -m pip install PyYAML" in steps_text
    assert "./scripts/run_release_readiness_check.sh" in steps_text


def test_ci_excludes_remote_only_publication_and_hosting_jobs() -> None:
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8",
    )
    ci = yaml.safe_load(ci_text)
    assert "image-publication" not in ci["jobs"]
    assert "hosted-deployment" not in ci["jobs"]


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
        "release-package",
        "release-readiness",
        "sources=8 ready=4 blocked=4",
        "build_release_package.ps1",
        "run_image_publication_check.ps1",
        "run_hosted_deployment_check.ps1",
        "out of scope for local-only",
        "not local-only release blockers",
    ):
        assert phrase in runbook


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
    assert payload["ready_count"] == 4
    assert payload["blocked_count"] == 4
    blocked = {
        source["source_registry_id"]
        for source in payload["sources"]
        if source["connector_ready"] is False
    }
    assert {"DS-010", "DS-011", "DS-017", "DS-023"}.issubset(blocked)


def test_release_readiness_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "run_release_readiness_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_release_readiness_check.sh").is_file()
