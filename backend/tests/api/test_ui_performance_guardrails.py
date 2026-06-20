from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from fastapi.testclient import TestClient

from app.api import ui as ui_module
from app.main import create_app
from app.performance_guardrails import (
    PerformanceGuardrailsError,
    load_performance_guardrails,
    parse_performance_guardrails,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_SCENARIOS = {"sequential", "concurrent"}
REQUIRED_SPATIAL_REVIEWS = {
    "area_parcel_intersections",
    "area_reference_feature_intersections",
    "area_observation_intersections",
}
REQUIRED_SPATIAL_INDEXES = {
    "areas_geom_gix",
    "area_versions_geom_gix",
    "parcels_geom_gix",
    "reference_features_geom_gix",
    "observations_geom_gix",
}
REQUIRED_BACKPRESSURE_SETTINGS = {
    "ENABLE_QUEUE_BACKPRESSURE",
    "MAX_REPORT_QUEUE_DEPTH",
    "MAX_LIVE_CONNECTOR_QUEUE_DEPTH",
    "MAX_QUEUE_OLDEST_QUEUED_SECONDS",
    "MAX_QUEUE_STALE_RUNNING",
}


def _catalog(path: str) -> dict[str, Any]:
    payload = yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _catalogs() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        _catalog("config/performance_baseline.yaml"),
        _catalog("config/spatial_query_plan.yaml"),
    )


def test_performance_guardrails_parser_composes_performance_contract() -> None:
    readiness = load_performance_guardrails(REPO_ROOT)

    assert readiness.baseline_schema_version == "performance_baseline_v1"
    assert readiness.baseline_scope == "selected_county_private_mvp_local"
    assert readiness.baseline_status == "release_candidate_local_only"
    assert readiness.result_schema_version == "load_test_result_v1"
    assert {
        "schema_version",
        "scenario",
        "base_url",
        "thresholds",
        "total_requests",
        "ok",
        "failures",
        "requests",
        "summary",
    }.issubset(set(readiness.result_required_fields))
    assert set(readiness.performance_scenario_ids) == REQUIRED_SCENARIOS

    scenarios = {scenario.scenario_id: scenario for scenario in readiness.performance_scenarios}
    assert scenarios["sequential"].request_count == 20
    assert scenarios["sequential"].workers is None
    assert scenarios["sequential"].thresholds["max_request_seconds"] == 5.0
    assert {"/health", "/version", "/metrics", "/areas", "/report-runs"}.issubset(
        set(scenarios["sequential"].endpoints)
    )
    assert scenarios["concurrent"].request_count == 40
    assert scenarios["concurrent"].workers == 8
    assert scenarios["concurrent"].thresholds["p95_seconds"] == 3.0
    assert scenarios["concurrent"].thresholds["max_error_rate"] == 0.1

    assert readiness.baseline_limits["hosted_production_claim"] is False
    assert readiness.baseline_limits["ci_live_load_gate"] is False
    assert readiness.baseline_limits["committed_measured_results"] is False

    assert readiness.spatial_schema_version == "spatial_query_plan_v1"
    assert readiness.spatial_scope == "selected_county_private_mvp_spatial_queries"
    assert readiness.spatial_default_mode == "validate_only_static"
    assert set(readiness.spatial_query_review_ids) == REQUIRED_SPATIAL_REVIEWS
    assert REQUIRED_SPATIAL_INDEXES.issubset(set(readiness.spatial_required_index_names))
    assert readiness.spatial_runtime_checker == "scripts/spatial_query_plan_runtime_check.py"
    assert (
        readiness.spatial_runtime_output_schema_version
        == "spatial_query_plan_runtime_result_v1"
    )
    assert readiness.spatial_limits["opens_database_connection_by_default"] is False
    assert readiness.spatial_limits["generates_artifacts"] is False
    assert readiness.spatial_limits["hosted_performance_claim"] is False
    assert readiness.spatial_limits["level_10_completion_claim"] is False

    assert REQUIRED_BACKPRESSURE_SETTINGS.issubset(set(readiness.backpressure_setting_ids))
    assert readiness.queue_health_path == "/operations/queue-health"
    assert "scripts/run_performance_baseline_check.ps1" in readiness.validation_commands
    assert "scripts/run_spatial_query_plan_check.ps1" in readiness.validation_commands
    assert "scripts/run_load_test.ps1 -ValidateOnly" in readiness.validation_commands


def test_performance_guardrails_parser_fails_closed_on_baseline_schema_drift() -> None:
    performance_catalog, spatial_catalog = _catalogs()
    performance_catalog = deepcopy(performance_catalog)
    performance_catalog["schema_version"] = "performance_baseline_v2"

    with pytest.raises(PerformanceGuardrailsError, match="performance baseline schema"):
        parse_performance_guardrails(
            performance_catalog,
            spatial_catalog,
            root=REPO_ROOT,
        )


def test_performance_guardrails_parser_fails_closed_on_hosted_claim() -> None:
    performance_catalog, spatial_catalog = _catalogs()
    performance_catalog = deepcopy(performance_catalog)
    performance_catalog["limits"]["hosted_production_claim"] = True

    with pytest.raises(PerformanceGuardrailsError, match="hosted production"):
        parse_performance_guardrails(
            performance_catalog,
            spatial_catalog,
            root=REPO_ROOT,
        )


def test_performance_guardrails_parser_fails_closed_on_missing_spatial_review() -> None:
    performance_catalog, spatial_catalog = _catalogs()
    spatial_catalog = deepcopy(spatial_catalog)
    spatial_catalog["query_plan_reviews"] = [
        review
        for review in cast(list[dict[str, Any]], spatial_catalog["query_plan_reviews"])
        if review["id"] != "area_observation_intersections"
    ]

    with pytest.raises(PerformanceGuardrailsError, match="spatial query review"):
        parse_performance_guardrails(
            performance_catalog,
            spatial_catalog,
            root=REPO_ROOT,
        )


def test_performance_guardrails_loader_uses_repo_relative_error_paths(
    tmp_path: Path,
) -> None:
    with pytest.raises(PerformanceGuardrailsError) as exc_info:
        load_performance_guardrails(tmp_path)

    message = str(exc_info.value)
    assert "config/performance_baseline.yaml" in message
    assert str(tmp_path) not in message


def test_ui_performance_guardrails_route_returns_503_when_loader_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_loader() -> None:
        raise PerformanceGuardrailsError("test performance guardrails failure")

    monkeypatch.setattr(ui_module, "load_performance_guardrails", _raise_loader)
    client = TestClient(create_app())

    response = client.get("/ui/performance-guardrails")

    assert response.status_code == 503
    assert "Performance guardrails unavailable from repo-owned artifacts" in response.text
    assert "test performance guardrails failure" in response.text
    assert "Traceback" not in response.text


def test_ui_performance_guardrails_route_renders_catalogs_and_boundaries() -> None:
    client = TestClient(create_app())

    response = client.get("/ui/performance-guardrails")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "Performance Guardrails" in response.text
    for text in (
        "performance_baseline_v1",
        "selected_county_private_mvp_local",
        "release_candidate_local_only",
        "load_test_result_v1",
        "sequential",
        "concurrent",
        "/health",
        "/areas",
        "/report-runs",
        "max_request_seconds",
        "p95_seconds",
        "hosted_production_claim",
        "ci_live_load_gate",
        "committed_measured_results",
        "spatial_query_plan_v1",
        "validate_only_static",
        "area_parcel_intersections",
        "area_observation_intersections",
        "parcels_geom_gix",
        "observations_geom_gix",
        "spatial_query_plan_runtime_result_v1",
        "ENABLE_QUEUE_BACKPRESSURE",
        "MAX_REPORT_QUEUE_DEPTH",
        "MAX_QUEUE_STALE_RUNNING",
        "/operations/queue-health",
        "scripts/run_load_test.ps1 -ValidateOnly",
        "does not run live load tests",
        "does not run runtime EXPLAIN",
        "does not write performance artifacts",
        "does not claim hosted SLO",
        "does not claim hosted performance",
        "does not claim Level 10",
    ):
        assert text in response.text


def test_current_ui_navigation_links_to_performance_guardrails() -> None:
    client = TestClient(create_app())

    for path in (
        "/ui/",
        "/ui/raw-data",
        "/ui/source-provenance",
        "/ui/deployment-readiness",
        "/ui/security-guardrails",
        "/ui/operations-guardrails",
    ):
        response = client.get(path)

        assert response.status_code == 200
        assert 'href="/ui/performance-guardrails"' in response.text
