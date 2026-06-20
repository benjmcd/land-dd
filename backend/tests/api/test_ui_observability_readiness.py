from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from fastapi.testclient import TestClient

from app.api import ui as ui_module
from app.main import create_app
from app.observability_readiness import (
    ObservabilityReadinessError,
    load_observability_readiness,
    parse_observability_readiness,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_SIGNAL_IDS = {
    "runtime_metrics",
    "queue_health",
    "recovery_preview",
    "connector_observability",
    "source_failure_evidence",
    "deployment_smoke",
    "alert_rule_catalog",
}
REQUIRED_BLOCKERS = {
    "hosted_dashboard",
    "hosted_alert_routing",
    "pager_on_call",
    "hosted_log_retention",
    "production_traffic_observability",
}


def _catalog() -> dict[str, Any]:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "observability_readiness.yaml").read_text(
            encoding="utf-8",
        )
    )
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def test_observability_readiness_parser_composes_local_contract() -> None:
    readiness = load_observability_readiness(REPO_ROOT)

    assert readiness.schema_version == "observability_readiness_v1"
    assert readiness.scope == "local_release_candidate_observability"
    assert readiness.status == "local_only"
    assert set(readiness.signal_ids) == REQUIRED_SIGNAL_IDS
    assert "runtime_metrics_v1" in readiness.schema_refs
    assert "operations_queue_health_v1" in readiness.schema_refs
    assert "operations_recovery_preview_v1" in readiness.schema_refs
    assert "metrics_endpoint_down" in readiness.alert_rule_ids
    assert "report_queue_backlog_high" in readiness.alert_rule_ids
    assert set(readiness.hosted_blocker_ids) == REQUIRED_BLOCKERS
    assert readiness.limits["validate_only"] is True
    assert readiness.limits["creates_hosted_dashboard"] is False
    assert readiness.limits["dispatches_alerts"] is False
    assert readiness.limits["provisions_pager"] is False
    assert readiness.limits["provisions_hosted_log_retention"] is False
    assert readiness.limits["opens_public_endpoint"] is False
    assert "scripts/run_observability_readiness_check.ps1" in readiness.validation_commands


def test_observability_readiness_parser_fails_closed_on_schema_drift() -> None:
    catalog = deepcopy(_catalog())
    catalog["schema_version"] = "observability_readiness_v2"

    with pytest.raises(ObservabilityReadinessError, match="schema"):
        parse_observability_readiness(catalog, root=REPO_ROOT)


def test_observability_readiness_parser_fails_closed_on_missing_hosted_blocker() -> None:
    catalog = deepcopy(_catalog())
    catalog["hosted_blockers"] = [
        blocker
        for blocker in cast(list[dict[str, Any]], catalog["hosted_blockers"])
        if blocker["id"] != "hosted_alert_routing"
    ]

    with pytest.raises(ObservabilityReadinessError, match="hosted blocker"):
        parse_observability_readiness(catalog, root=REPO_ROOT)


def test_observability_readiness_parser_fails_closed_on_schema_ref_drift() -> None:
    catalog = deepcopy(_catalog())
    first_signal = cast(list[dict[str, Any]], catalog["signals"])[0]
    first_signal["schema_ref"] = "runtime_metrics_v2"

    with pytest.raises(ObservabilityReadinessError, match="schema refs"):
        parse_observability_readiness(catalog, root=REPO_ROOT)


def test_observability_readiness_parser_fails_closed_on_hosted_dashboard_claim() -> None:
    catalog = deepcopy(_catalog())
    catalog["limits"]["creates_hosted_dashboard"] = True

    with pytest.raises(ObservabilityReadinessError, match="hosted dashboard"):
        parse_observability_readiness(catalog, root=REPO_ROOT)


def test_observability_readiness_loader_uses_repo_relative_error_paths(
    tmp_path: Path,
) -> None:
    with pytest.raises(ObservabilityReadinessError) as exc_info:
        load_observability_readiness(tmp_path)

    message = str(exc_info.value)
    assert "config/observability_readiness.yaml" in message
    assert str(tmp_path) not in message


def test_ui_observability_readiness_route_returns_503_when_loader_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_loader() -> None:
        raise ObservabilityReadinessError("test observability readiness failure")

    monkeypatch.setattr(ui_module, "load_observability_readiness", _raise_loader)
    client = TestClient(create_app())

    response = client.get("/ui/observability-readiness")

    assert response.status_code == 503
    assert "Observability readiness unavailable from repo-owned artifacts" in response.text
    assert "test observability readiness failure" in response.text
    assert "Traceback" not in response.text


def test_ui_observability_readiness_route_renders_catalogs_and_boundaries() -> None:
    client = TestClient(create_app())

    response = client.get("/ui/observability-readiness")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "Observability Readiness" in response.text
    for text in (
        "observability_readiness_v1",
        "local_release_candidate_observability",
        "local_only",
        "runtime_metrics",
        "runtime_metrics_v1",
        "/metrics",
        "queue_health",
        "operations_queue_health_v1",
        "/operations/queue-health",
        "recovery_preview",
        "operations_recovery_preview_v1",
        "/operations/recovery-preview",
        "connector_observability",
        "source_failure_evidence",
        "deployment_smoke",
        "alert_rule_catalog",
        "metrics_endpoint_down",
        "report_queue_backlog_high",
        "hosted_dashboard",
        "hosted_alert_routing",
        "pager_on_call",
        "hosted_log_retention",
        "production_traffic_observability",
        "creates_hosted_dashboard",
        "dispatches_alerts",
        "provisions_pager",
        "provisions_hosted_log_retention",
        "opens_public_endpoint",
        "scripts/run_observability_readiness_check.ps1",
        "does not create hosted dashboards",
        "does not dispatch alerts",
        "does not provision pager",
        "does not provision hosted log retention",
        "does not open public endpoints",
        "does not claim Level 10",
    ):
        assert text in response.text


def test_current_ui_navigation_links_to_observability_readiness() -> None:
    client = TestClient(create_app())

    for path in (
        "/ui/",
        "/ui/raw-data",
        "/ui/source-provenance",
        "/ui/deployment-readiness",
        "/ui/security-guardrails",
        "/ui/operations-guardrails",
        "/ui/performance-guardrails",
    ):
        response = client.get(path)

        assert response.status_code == 200
        assert 'href="/ui/observability-readiness"' in response.text
