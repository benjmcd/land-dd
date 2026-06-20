from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from fastapi.testclient import TestClient

from app.api import ui as ui_module
from app.main import create_app
from app.operations_guardrails import (
    OperationsGuardrailsError,
    load_operations_guardrails,
    parse_operations_guardrails,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_ALERT_RULE_IDS = {
    "safety_contract_check_failed",
    "api_health_down",
    "deployment_smoke_failed",
    "db_smoke_failed",
    "backup_restore_failed",
    "metrics_endpoint_down",
    "report_queue_backlog_high",
    "report_running_stale",
    "report_failures_high",
    "live_connector_queue_backlog_high",
    "live_connector_running_stale",
    "live_connector_failures_high",
    "source_readiness_ready_drop",
    "source_registry_last_checked_stale",
    "cost_monitoring_check_failed",
}
REQUIRED_RETENTION_CLASSES = {
    "report_runs",
    "evidence_observations",
    "audit_events",
    "api_key_audit_events",
    "connector_review_queue",
    "job_queue_report_jobs",
    "source_ingest_runs",
}
REQUIRED_COST_CATEGORIES = {
    "compute",
    "storage",
    "llm",
    "maps",
    "geocoding",
    "data_vendors",
}


def _catalog(path: str) -> dict[str, Any]:
    payload = yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _catalogs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        _catalog("config/ops_alert_rules.yaml"),
        _catalog("config/data_retention.yaml"),
        _catalog("config/ops_cost_monitoring.yaml"),
    )


def test_operations_guardrails_parser_composes_operations_contract() -> None:
    readiness = load_operations_guardrails(REPO_ROOT)

    assert readiness.alert_schema_version == "ops_alert_rules_v1"
    assert REQUIRED_ALERT_RULE_IDS.issubset(set(readiness.alert_rule_ids))
    assert readiness.alert_severity_counts["SEV0"] >= 1
    assert readiness.alert_severity_counts["SEV1"] >= 4
    assert readiness.alert_severity_counts["SEV2"] >= 1
    assert "/operations/queue-health" in readiness.queue_signal_targets
    assert readiness.recovery_preview_path == "/operations/recovery-preview"
    assert readiness.incident_runbook == "docs/runbooks/incident_response.md"
    assert readiness.backup_restore_runbook == "docs/runbooks/backup_restore.md"
    assert "scripts/run_backup_restore_check.ps1" in readiness.validation_commands
    assert "scripts/run_incident_rollback_check.ps1" in readiness.validation_commands

    assert readiness.retention_schema_version == "data_retention_v1"
    assert REQUIRED_RETENTION_CLASSES.issubset(set(readiness.retention_class_ids))
    assert readiness.retention_automation_status == "repo_local_schedule_contract"
    assert readiness.retention_automation_mode == "dry_run_by_default"
    assert readiness.hosted_scheduler_status == "blocked"
    assert readiness.retention_limits["deletes_by_default"] is False
    assert readiness.retention_limits["requires_explicit_apply"] is True

    assert readiness.cost_schema_version == "ops_cost_monitoring_v1"
    assert REQUIRED_COST_CATEGORIES.issubset(set(readiness.cost_category_ids))
    assert {"llm", "maps", "geocoding", "data_vendors"}.issubset(
        set(readiness.cost_blocked_or_disabled_ids)
    )
    assert readiness.report_cost_metrics_authority == "schemas/report_run_schema.json"
    assert readiness.planning_cost_inputs == (
        "docs/planning_pack/registers/cost_model_inputs.csv"
    )


def test_operations_guardrails_parser_fails_closed_on_alert_schema_drift() -> None:
    alert_catalog, retention_catalog, cost_catalog = _catalogs()
    alert_catalog = deepcopy(alert_catalog)
    alert_catalog["schema_version"] = "ops_alert_rules_v2"

    with pytest.raises(OperationsGuardrailsError, match="alert schema"):
        parse_operations_guardrails(
            alert_catalog,
            retention_catalog,
            cost_catalog,
            root=REPO_ROOT,
        )


def test_operations_guardrails_parser_fails_closed_on_missing_queue_alert() -> None:
    alert_catalog, retention_catalog, cost_catalog = _catalogs()
    alert_catalog = deepcopy(alert_catalog)
    alert_catalog["rules"] = [
        rule
        for rule in cast(list[dict[str, Any]], alert_catalog["rules"])
        if rule["id"] != "report_queue_backlog_high"
    ]

    with pytest.raises(OperationsGuardrailsError, match="required alert"):
        parse_operations_guardrails(
            alert_catalog,
            retention_catalog,
            cost_catalog,
            root=REPO_ROOT,
        )


def test_operations_guardrails_parser_fails_closed_on_hosted_scheduler_claim() -> None:
    alert_catalog, retention_catalog, cost_catalog = _catalogs()
    retention_catalog = deepcopy(retention_catalog)
    retention_catalog["automation_plan"]["hosted_scheduler_status"] = "provisioned"

    with pytest.raises(OperationsGuardrailsError, match="hosted scheduler"):
        parse_operations_guardrails(
            alert_catalog,
            retention_catalog,
            cost_catalog,
            root=REPO_ROOT,
        )


def test_operations_guardrails_loader_uses_repo_relative_error_paths(
    tmp_path: Path,
) -> None:
    with pytest.raises(OperationsGuardrailsError) as exc_info:
        load_operations_guardrails(tmp_path)

    message = str(exc_info.value)
    assert "config/ops_alert_rules.yaml" in message
    assert str(tmp_path) not in message


def test_ui_operations_guardrails_route_returns_503_when_loader_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_loader() -> None:
        raise OperationsGuardrailsError("test operations guardrails failure")

    monkeypatch.setattr(ui_module, "load_operations_guardrails", _raise_loader)
    client = TestClient(create_app())

    response = client.get("/ui/operations-guardrails")

    assert response.status_code == 503
    assert "Operations guardrails unavailable from repo-owned artifacts" in response.text
    assert "test operations guardrails failure" in response.text
    assert "Traceback" not in response.text


def test_ui_operations_guardrails_route_renders_catalogs_and_boundaries() -> None:
    client = TestClient(create_app())

    response = client.get("/ui/operations-guardrails")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "Operations Guardrails" in response.text
    for text in (
        "ops_alert_rules_v1",
        "safety_contract_check_failed",
        "report_queue_backlog_high",
        "live_connector_running_stale",
        "source_registry_last_checked_stale",
        "cost_monitoring_check_failed",
        "SEV0",
        "SEV1",
        "SEV2",
        "/operations/queue-health",
        "/operations/recovery-preview",
        "data_retention_v1",
        "audit_events",
        "api_key_audit_events",
        "repo_local_schedule_contract",
        "dry_run_by_default",
        "hosted scheduler: blocked",
        "ops_cost_monitoring_v1",
        "compute",
        "data_vendors",
        "disabled_until_metered",
        "blocked_until_reviewed",
        "does not execute recovery",
        "does not dispatch alerts",
        "does not run backup/restore",
        "does not purge audit events",
        "does not claim hosted alerting",
        "does not claim Level 10",
    ):
        assert text in response.text


def test_current_ui_navigation_links_to_operations_guardrails() -> None:
    client = TestClient(create_app())

    for path in (
        "/ui/",
        "/ui/raw-data",
        "/ui/source-provenance",
        "/ui/deployment-readiness",
        "/ui/security-guardrails",
    ):
        response = client.get(path)

        assert response.status_code == 200
        assert 'href="/ui/operations-guardrails"' in response.text
