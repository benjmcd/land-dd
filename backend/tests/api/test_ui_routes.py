from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.core.config import Settings
from app.main import create_app

client = TestClient(create_app())

_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def _valid_geojson() -> dict[str, object]:
    data = json.loads((_FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


# Default fixture credentials (from Settings defaults)
_FIXTURE_REVIEWER_ID = "fixture-reviewer"
_FIXTURE_REVIEWER_TOKEN = "fixture-token-123"


def _make_app_client_with_report(
    settings: Settings | None = None,
) -> tuple[FastAPI, TestClient, str]:
    app = create_app(settings)
    tc = TestClient(app)
    area_resp = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]
    run_resp = tc.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert run_resp.status_code == 202
    return app, tc, run_resp.json()["report_run_id"]


def test_ui_index_returns_200_html() -> None:
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Land Diligence" in response.text


def test_ui_index_has_intent_form() -> None:
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "rural_land_purchase" in response.text
    assert "homestead_feasibility" in response.text


def test_ui_report_run_returns_404_page_for_unknown_id() -> None:
    response = client.get(f"/ui/report-runs/{uuid4()}")
    assert response.status_code == 200  # We return 200 HTML with "not found" message
    assert "text/html" in response.headers["content-type"]
    assert "Not Found" in response.text


def test_ui_report_run_invalid_uuid_returns_422() -> None:
    response = client.get("/ui/report-runs/not-a-uuid")
    assert response.status_code == 422


def test_ui_report_run_shows_pending_approval_for_unapproved_report() -> None:
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.get(f"/ui/report-runs/{report_run_id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Pending" in response.text or "pending" in response.text
    assert "Executive Summary" not in response.text


def test_ui_report_run_shows_dossier_after_approval() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(UUID(report_run_id), reviewer_id="test-reviewer")
    response = tc.get(f"/ui/report-runs/{report_run_id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Executive Summary" in response.text


def test_ui_report_run_list_returns_html_table() -> None:
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.get("/ui/report-runs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert report_run_id[:8] in response.text


def test_ui_report_run_list_empty_state() -> None:
    tc = TestClient(create_app())
    response = tc.get("/ui/report-runs")
    assert response.status_code == 200
    assert "No report runs yet" in response.text


def test_ui_approve_report_run_redirects_on_success() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Approved" in response.text
    # Dossier now accessible
    dossier_resp = tc.get(f"/ui/report-runs/{report_run_id}")
    assert "Executive Summary" in dossier_resp.text


def test_ui_approve_report_run_records_authenticated_reviewer_id() -> None:
    """Audit integrity: reviewed_by must be the authenticated reviewer, not a fallback."""
    app, tc, report_run_id = _make_app_client_with_report()
    tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    services = cast(ApiServices, app.state.services)
    report = services.report_service.get_report_run(UUID(report_run_id))
    assert report is not None
    assert report.reviewed_by == _FIXTURE_REVIEWER_ID


def test_ui_approve_report_run_unknown_id() -> None:
    tc = TestClient(create_app())
    response = tc.post(
        f"/ui/report-runs/{uuid4()}/approve",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    assert response.status_code == 200
    assert "Not Found" in response.text


def test_ui_approve_report_run_no_credentials_returns_401() -> None:
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={},
    )
    assert response.status_code == 401
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Error" in response.text


def test_ui_approve_report_run_wrong_token_returns_403() -> None:
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": "wrong-token",
        },
    )
    assert response.status_code == 403
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Error" in response.text


def test_ui_approve_report_run_valid_creds_without_approve_scope_returns_403() -> None:
    settings = Settings(
        REVIEWER_ACCOUNTS="scoped-reviewer:scoped-token",
        REVIEWER_ACCOUNT_SCOPES="scoped-reviewer:connector:run",
    )
    _app, tc, report_run_id = _make_app_client_with_report(settings)
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={
            "reviewer_id": "scoped-reviewer",
            "reviewer_token": "scoped-token",
        },
    )
    assert response.status_code == 403
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Error" in response.text


def test_ui_approve_report_run_unconfigured_accounts_returns_503() -> None:
    """When reviewer auth is not configured, 503 semantics are preserved."""
    # LocalServiceAccountReviewerAuth raises 503 when no accounts configured.
    # create_app uses default settings which always have fixture-reviewer,
    # so we patch reviewer_auth post-construction.
    from unittest.mock import patch

    from fastapi import HTTPException, status

    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)

    def _unconfigured(**kwargs: object) -> None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="connector reviewer auth is not configured",
        )

    with patch.object(services, "reviewer_auth", side_effect=_unconfigured):
        response = tc.post(
            f"/ui/report-runs/{report_run_id}/approve",
            data={
                "reviewer_id": "any",
                "reviewer_token": "any",
            },
        )
    assert response.status_code == 503
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Error" in response.text


def test_ui_print_report_run_unapproved_returns_not_approved_page() -> None:
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.get(f"/ui/report-runs/{report_run_id}/print")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Not Yet Approved" in response.text or "not yet approved" in response.text.lower()
    assert "Executive Summary" not in response.text


def test_ui_print_report_run_approved_returns_printable_dossier() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(UUID(report_run_id), reviewer_id="test-reviewer")
    response = tc.get(f"/ui/report-runs/{report_run_id}/print")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Executive Summary" in response.text
    assert "window.print()" in response.text
    assert "@media print" in response.text


def test_ui_print_report_run_unknown_id_returns_not_found() -> None:
    tc = TestClient(create_app())
    response = tc.get(f"/ui/report-runs/{uuid4()}/print")
    assert response.status_code == 200
    assert "Not Found" in response.text
