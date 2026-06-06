from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_metrics_endpoint_reports_structured_http_counts() -> None:
    client = TestClient(create_app())

    assert client.get("/areas").status_code == 200
    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "runtime_metrics_v1"
    assert body["uptime_seconds"] >= 0
    assert body["http"]["requests_total"] >= 1
    area_metrics = _route_metric(body, method="GET", path="/areas")
    assert area_metrics["requests_total"] == 1
    assert area_metrics["status_counts"] == {"200": 1}
    assert area_metrics["duration_ms"]["total"] >= 0


def test_metrics_uses_route_templates_for_parameterized_paths() -> None:
    client = TestClient(create_app())

    response = client.get("/report-runs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

    metrics = client.get("/metrics").json()
    report_run_metrics = _route_metric(
        metrics,
        method="GET",
        path="/report-runs/{report_run_id}",
    )
    assert report_run_metrics["status_counts"] == {"404": 1}


def test_metrics_endpoint_can_be_disabled() -> None:
    client = TestClient(create_app(Settings(ENABLE_METRICS=False)))

    response = client.get("/metrics")

    assert response.status_code == 404
    assert response.json()["detail"] == "runtime metrics are not enabled"


def test_metrics_endpoint_is_protected_by_api_key_auth_when_required() -> None:
    client = TestClient(
        create_app(Settings(REQUIRE_API_KEY=True, API_KEYS="production-key"))
    )

    missing = client.get("/metrics")
    allowed = client.get("/metrics", headers={"X-API-Key": "production-key"})

    assert missing.status_code == 401
    assert allowed.status_code == 200


def test_metrics_endpoint_is_rate_limited_when_rate_limit_enabled() -> None:
    client = TestClient(
        create_app(
            Settings(
                ENABLE_RATE_LIMIT=True,
                RATE_LIMIT_REQUESTS=1,
                RATE_LIMIT_WINDOW_SECONDS=60,
            )
        )
    )

    assert client.get("/metrics").status_code == 200
    response = client.get("/metrics")

    assert response.status_code == 429
    assert response.json()["detail"] == "rate limit exceeded"


def _route_metric(
    snapshot: dict[str, Any],
    *,
    method: str,
    path: str,
) -> dict[str, Any]:
    http_metrics = snapshot["http"]
    assert isinstance(http_metrics, dict)
    routes = http_metrics["routes"]
    assert isinstance(routes, list)
    for route in routes:
        assert isinstance(route, dict)
        if route.get("method") == method and route.get("path") == path:
            return route
    raise AssertionError(f"missing route metric {method} {path}")
