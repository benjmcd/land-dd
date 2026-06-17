from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.main import create_app
from app.reports.artifacts import serialize_report_artifact

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def _valid_geojson() -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_http_approved_path_with_shipped_fixture_credential() -> None:
    app = create_app()
    client = TestClient(app)

    area_resp = client.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]

    run_resp = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert run_resp.status_code == 202
    report_run_id = run_resp.json()["report_run_id"]

    artifact_before = client.get(f"/report-runs/{report_run_id}/artifact")
    assert artifact_before.status_code == 409

    approve_resp = client.post(
        f"/report-runs/{report_run_id}/approve",
        headers={
            "X-Reviewer-Id": "fixture-reviewer",
            "X-Reviewer-Token": "fixture-token-123",
        },
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["review_status"] == "approved"

    artifact_resp = client.get(f"/report-runs/{report_run_id}/artifact")
    assert artifact_resp.status_code == 200
    assert "application/json" in artifact_resp.headers["content-type"]

    services = cast(ApiServices, app.state.services)
    contract = services.report_service.get_report_run(UUID(report_run_id))
    assert contract is not None
    expected = serialize_report_artifact(contract)
    assert artifact_resp.text == expected


def test_http_approve_requires_credential() -> None:
    app = create_app()
    client = TestClient(app)

    area_resp = client.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]

    run_resp = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert run_resp.status_code == 202
    report_run_id = run_resp.json()["report_run_id"]

    approve_resp = client.post(f"/report-runs/{report_run_id}/approve")
    assert approve_resp.status_code == 401
