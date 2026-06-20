from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_SIGNAL_IDS = {
    "runtime_metrics",
    "queue_health",
    "recovery_preview",
    "connector_observability",
    "source_failure_evidence",
    "deployment_smoke",
    "alert_rule_catalog",
}
REQUIRED_ALERT_RULE_IDS = {
    "metrics_endpoint_down",
    "report_queue_backlog_high",
    "report_running_stale",
    "live_connector_queue_backlog_high",
    "live_connector_running_stale",
}
REQUIRED_BLOCKERS = {
    "hosted_dashboard",
    "hosted_alert_routing",
    "pager_on_call",
    "hosted_log_retention",
    "production_traffic_observability",
}
REQUIRED_FALSE_LIMITS = {
    "creates_hosted_dashboard",
    "dispatches_alerts",
    "provisions_pager",
    "provisions_hosted_log_retention",
    "mutates_hosted_infrastructure",
    "writes_secrets",
    "opens_public_endpoint",
    "runs_deployment_smoke",
}


def _load_checker() -> ModuleType:
    module_path = REPO_ROOT / "scripts" / "observability_readiness_check.py"
    spec = importlib.util.spec_from_file_location(
        "observability_readiness_check",
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _catalog() -> dict[str, Any]:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "observability_readiness.yaml").read_text(
            encoding="utf-8",
        )
    )
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def test_observability_readiness_catalog_composes_local_authority() -> None:
    catalog = _catalog()

    assert catalog["schema_version"] == "observability_readiness_v1"
    assert catalog["scope"] == "local_release_candidate_observability"
    assert catalog["status"] == "local_only"
    assert {signal["id"] for signal in catalog["signals"]} == REQUIRED_SIGNAL_IDS
    assert REQUIRED_ALERT_RULE_IDS.issubset(set(catalog["alert_rule_ids"]))
    assert {blocker["id"] for blocker in catalog["hosted_blockers"]} == REQUIRED_BLOCKERS
    for blocker in catalog["hosted_blockers"]:
        assert blocker["status"] == "blocked"
        assert (REPO_ROOT / blocker["authority"]).exists()
    for key in REQUIRED_FALSE_LIMITS:
        assert catalog["limits"][key] is False
    assert catalog["limits"]["validate_only"] is True


def test_observability_readiness_catalog_references_existing_artifacts() -> None:
    catalog = _catalog()

    for signal in catalog["signals"]:
        for path_text in signal["source_files"]:
            assert (REPO_ROOT / path_text).exists()
        for path_text in signal["validation"]:
            assert (REPO_ROOT / path_text).exists()
    for path_text in catalog["validation_commands"]:
        command_path = path_text.split()[0]
        assert (REPO_ROOT / command_path).exists()


def test_observability_readiness_checker_passes_current_catalog() -> None:
    checker = _load_checker()

    assert checker.main() == 0


def test_observability_readiness_wrappers_delegate_to_checker() -> None:
    for script_name in (
        "run_observability_readiness_check.ps1",
        "run_observability_readiness_check.sh",
    ):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "observability_readiness_check.py" in script


def test_release_readiness_composes_observability_readiness_check() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "release_readiness.yaml").read_text(encoding="utf-8"),
    )
    checks = {check["id"]: check for check in catalog["required_checks"]}

    assert checks["observability_readiness"]["proof"] == (
        "scripts/run_observability_readiness_check.ps1"
    )
    assert checks["observability_readiness"]["ci_job"] is None

    checker = (REPO_ROOT / "scripts" / "release_readiness_check.py").read_text(
        encoding="utf-8",
    )
    assert "scripts/run_observability_readiness_check.ps1" in checker
    assert "scripts/observability_readiness_check.py" in checker
