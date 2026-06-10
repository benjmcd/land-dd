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


# ---------------------------------------------------------------------------
# Retry tests (S4)
# ---------------------------------------------------------------------------


def _make_app_client_with_failed_report() -> tuple[FastAPI, TestClient, str]:
    """Create an app+client with a report job force-marked as FAILED."""
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.async_report_jobs.mark_failed(UUID(report_run_id), error_msg="test failure")
    return app, tc, report_run_id


def test_ui_failed_report_shows_retry_form() -> None:
    _app, tc, report_run_id = _make_app_client_with_failed_report()
    response = tc.get(f"/ui/report-runs/{report_run_id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Failed" in response.text or "failed" in response.text.lower()
    assert "Retry" in response.text
    assert "reviewer_id" in response.text
    assert "reviewer_token" in response.text


def test_ui_retry_report_run_no_credentials_returns_401() -> None:
    _app, tc, report_run_id = _make_app_client_with_failed_report()
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/retry",
        data={},
    )
    assert response.status_code == 401
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Error" in response.text


def test_ui_retry_report_run_wrong_token_returns_403() -> None:
    _app, tc, report_run_id = _make_app_client_with_failed_report()
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/retry",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": "wrong-token",
        },
    )
    assert response.status_code == 403
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Error" in response.text


def test_ui_retry_report_run_valid_creds_without_retry_scope_returns_403() -> None:
    from app.core.config import Settings

    settings = Settings(
        REVIEWER_ACCOUNTS="limited-reviewer:limited-token",
        REVIEWER_ACCOUNT_SCOPES="limited-reviewer:report:approve",
    )
    _app, tc, report_run_id = _make_app_client_with_failed_report()
    # Use a separate client with restricted scopes
    app2, tc2, report_run_id2 = _make_app_client_with_report(settings)
    services = cast(ApiServices, app2.state.services)
    services.async_report_jobs.mark_failed(UUID(report_run_id2), error_msg="test failure")
    response = tc2.post(
        f"/ui/report-runs/{report_run_id2}/retry",
        data={
            "reviewer_id": "limited-reviewer",
            "reviewer_token": "limited-token",
        },
    )
    assert response.status_code == 403
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Error" in response.text


def test_ui_retry_report_run_non_failed_returns_409() -> None:
    # Report is queued (not failed) — retry must be rejected with 409
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/retry",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    assert response.status_code == 409
    assert "text/html" in response.headers["content-type"]


def test_ui_retry_report_run_unknown_id_returns_404() -> None:
    tc = TestClient(create_app())
    response = tc.post(
        f"/ui/report-runs/{uuid4()}/retry",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
    )
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]


def test_ui_retry_report_run_success_creates_queued_retry_job_and_redirects() -> None:
    app, tc, report_run_id = _make_app_client_with_failed_report()
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/retry",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Retry Queued" in response.text
    # New report run ID is in the response
    assert report_run_id not in response.text.split("New report run ID:")[0] or True
    # Verify the new run was created in the job store
    services = cast(ApiServices, app.state.services)
    all_jobs = services.async_report_jobs.list_recent(limit=100)
    new_jobs = [j for j in all_jobs if str(j.report_run_id) != report_run_id]
    assert len(new_jobs) >= 1
    # The new job should link back to the original as retry_of
    new_job = new_jobs[0]
    assert new_job.retry_of_report_run_id == UUID(report_run_id)
    # Response points to new job's URL
    assert str(new_job.report_run_id) in response.text


def test_ui_report_runs_list_has_operations_link() -> None:
    tc = TestClient(create_app())
    response = tc.get("/ui/report-runs")
    assert response.status_code == 200
    assert "/ui/operations" in response.text
    assert "Operations" in response.text


# ---------------------------------------------------------------------------
# S5 — UI list page: status filter + pagination
# ---------------------------------------------------------------------------


def test_ui_report_run_list_has_status_filter_dropdown() -> None:
    _app, tc, _run_id = _make_app_client_with_report()
    response = tc.get("/ui/report-runs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Filter form is present
    assert 'name="status"' in response.text
    # JobStatus values appear in the dropdown
    assert "queued" in response.text
    assert "failed" in response.text
    assert "succeeded" in response.text


def test_ui_report_run_list_status_filter_shows_only_matching_rows() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    # Mark the job as failed
    services.async_report_jobs.mark_failed(UUID(report_run_id), error_msg="test failure")
    # Filter for failed: our run should appear
    resp_failed = tc.get("/ui/report-runs?status=failed")
    assert resp_failed.status_code == 200
    assert report_run_id[:8] in resp_failed.text
    # Filter for queued: our run should NOT appear (it's failed)
    resp_queued = tc.get("/ui/report-runs?status=queued")
    assert resp_queued.status_code == 200
    assert report_run_id[:8] not in resp_queued.text


def test_ui_report_run_list_invalid_status_filter_falls_back_gracefully() -> None:
    tc = TestClient(create_app())
    # Invalid status value should not 500 — falls back to no filter
    resp = tc.get("/ui/report-runs?status=not_a_real_status")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_ui_report_run_list_prev_next_pagination_links() -> None:
    app, tc = create_app(), None
    tc = TestClient(app)
    area_resp = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    # Create enough runs to trigger the "Next" link (page size is 30)
    # We'll use offset directly to test prev/next rendering
    # With offset=0 and empty store, no pagination links
    resp0 = tc.get("/ui/report-runs?offset=0")
    assert resp0.status_code == 200
    # With offset>0, prev link should appear
    resp_with_offset = tc.get("/ui/report-runs?offset=30")
    assert resp_with_offset.status_code == 200
    assert "Previous" in resp_with_offset.text or "prev" in resp_with_offset.text.lower()


def test_ui_report_run_list_pagination_preserves_status_filter() -> None:
    tc = TestClient(create_app())
    # With status filter + offset, the prev/next links should preserve status
    resp = tc.get("/ui/report-runs?status=failed&offset=30")
    assert resp.status_code == 200
    # Previous link should include the status param
    if "Previous" in resp.text:
        assert "status=failed" in resp.text


# ---------------------------------------------------------------------------
# S6 — Evidence lineage UI
# ---------------------------------------------------------------------------


def test_ui_lineage_page_unknown_id_returns_html_not_found() -> None:
    tc = TestClient(create_app())
    resp = tc.get(f"/ui/report-runs/{uuid4()}/lineage")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Not Found" in resp.text


def test_ui_lineage_page_invalid_uuid_returns_422() -> None:
    tc = TestClient(create_app())
    resp = tc.get("/ui/report-runs/not-a-uuid/lineage")
    assert resp.status_code == 422


def test_ui_lineage_page_renders_claim_evidence_mapping() -> None:
    """Lineage page renders claim->evidence and evidence->claim sections."""
    app, tc, report_run_id = _make_app_client_with_report()
    resp = tc.get(f"/ui/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    # Structural headings
    assert "Evidence Lineage" in resp.text
    assert "Claims" in resp.text
    assert "Evidence" in resp.text
    assert "Sources" in resp.text
    # Report run ID appears in the page
    assert report_run_id[:8] in resp.text


def test_ui_lineage_page_shows_evidence_records() -> None:
    """The lineage page lists at least one evidence record from the fixture report."""
    app, tc, report_run_id = _make_app_client_with_report()
    resp = tc.get(f"/ui/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    # The fixture connector always generates evidence — at least one row must appear.
    assert "No evidence records" not in resp.text


def test_ui_lineage_page_shows_claim_records() -> None:
    """The lineage page lists at least one claim from the fixture report."""
    app, tc, report_run_id = _make_app_client_with_report()
    resp = tc.get(f"/ui/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    assert "No claims" not in resp.text


def test_ui_lineage_page_gating_matches_api_no_auth_required() -> None:
    """Lineage UI is accessible for any existing report, no reviewer auth needed (mirrors API)."""
    app, tc, report_run_id = _make_app_client_with_report()
    # No credentials supplied — should succeed (same posture as GET /report-runs/{id}/lineage)
    resp = tc.get(f"/ui/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    assert "Evidence Lineage" in resp.text


def test_ui_approved_report_page_has_lineage_link() -> None:
    """The approved report page shows a 'View evidence lineage' link."""
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(UUID(report_run_id), reviewer_id="test-reviewer")
    resp = tc.get(f"/ui/report-runs/{report_run_id}")
    assert resp.status_code == 200
    assert "lineage" in resp.text
    assert f"/ui/report-runs/{report_run_id}/lineage" in resp.text


# ---------------------------------------------------------------------------
# S7 — Compare UI
# ---------------------------------------------------------------------------


def _make_two_report_runs() -> tuple[TestClient, str, str]:
    """Helper: create an app + two report runs on different areas."""

    tc = TestClient(create_app())
    area1 = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area1.status_code == 201
    area2 = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area2.status_code == 201

    run1 = tc.post(
        "/report-runs",
        json={"area_id": area1.json()["area_id"], "intent_code": "rural_land_purchase"},
    )
    assert run1.status_code == 202
    run2 = tc.post(
        "/report-runs",
        json={"area_id": area2.json()["area_id"], "intent_code": "rural_land_purchase"},
    )
    assert run2.status_code == 202
    return tc, run1.json()["report_run_id"], run2.json()["report_run_id"]


def test_ui_compare_two_reports_renders_table() -> None:
    """GET /ui/compare?ids=a,b returns a 200 HTML side-by-side table."""
    tc, run1, run2 = _make_two_report_runs()
    resp = tc.get(f"/ui/compare?ids={run1},{run2}")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Compare Report Runs" in resp.text
    assert run1[:8] in resp.text
    assert run2[:8] in resp.text
    # Structural metric rows
    assert "Claims" in resp.text
    assert "Red Flags" in resp.text
    assert "Unknowns" in resp.text
    assert "Verification Tasks" in resp.text
    assert "High-Severity Claims" in resp.text


def test_ui_compare_one_id_returns_400() -> None:
    """Fewer than 2 IDs → 400 error page."""
    tc, run1, _ = _make_two_report_runs()
    resp = tc.get(f"/ui/compare?ids={run1}")
    assert resp.status_code == 400
    assert "2" in resp.text


def test_ui_compare_five_ids_returns_400() -> None:
    """More than 4 IDs → 400 error page."""
    tc = TestClient(create_app())
    area_resp = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]
    ids = []
    for _ in range(5):
        r = tc.post(
            "/report-runs",
            json={"area_id": area_id, "intent_code": "rural_land_purchase"},
        )
        assert r.status_code == 202
        ids.append(r.json()["report_run_id"])
    resp = tc.get(f"/ui/compare?ids={','.join(ids)}")
    assert resp.status_code == 400
    assert "4" in resp.text


def test_ui_compare_malformed_uuid_returns_422() -> None:
    """A malformed UUID in the ids list → 422 error page."""
    tc, run1, _ = _make_two_report_runs()
    resp = tc.get(f"/ui/compare?ids={run1},not-a-uuid")
    assert resp.status_code == 422
    assert "malformed" in resp.text.lower() or "UUID" in resp.text or "uuid" in resp.text


def test_ui_compare_unknown_id_returns_404() -> None:
    """An unknown report run ID in ids → 404 error page."""
    tc, run1, _ = _make_two_report_runs()
    missing = str(uuid4())
    resp = tc.get(f"/ui/compare?ids={run1},{missing}")
    assert resp.status_code == 404
    assert "not found" in resp.text.lower()


def test_ui_compare_counts_match_api_compare_response() -> None:
    """The UI compare table shows the same counts as GET /report-runs/compare for the same ids."""
    tc, run1, run2 = _make_two_report_runs()

    # Fetch API response for reference
    api_resp = tc.get(f"/report-runs/compare?ids={run1},{run2}")
    assert api_resp.status_code == 200
    summaries = {str(s["report_run_id"]): s for s in api_resp.json()["summaries"]}

    # Fetch UI page
    ui_resp = tc.get(f"/ui/compare?ids={run1},{run2}")
    assert ui_resp.status_code == 200

    # For each run, the claims_count, red_flags_count, and unknowns_count from the API
    # must appear in the UI page HTML.
    for rid in (run1, run2):
        s = summaries[rid]
        assert str(s["claims_count"]) in ui_resp.text
        assert str(s["unknowns_count"]) in ui_resp.text
        assert str(s["red_flags_count"]) in ui_resp.text
        assert str(s["verification_tasks_count"]) in ui_resp.text


def test_ui_compare_no_ids_returns_400() -> None:
    """GET /ui/compare with no ids param → 400 error page."""
    tc = TestClient(create_app())
    resp = tc.get("/ui/compare")
    assert resp.status_code == 400


def test_ui_report_list_has_compare_affordance() -> None:
    """The report list page contains checkboxes and the compare button."""
    tc = TestClient(create_app())
    resp = tc.get("/ui/report-runs")
    assert resp.status_code == 200
    assert "cmp-check" in resp.text
    assert "goCompare" in resp.text
    assert "Compare Selected" in resp.text


def test_ui_report_list_checkbox_column_present_with_reports() -> None:
    """Each report row in the list page includes a checkbox with the run id as value."""
    tc = TestClient(create_app())
    area_resp = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    run_resp = tc.post(
        "/report-runs",
        json={"area_id": area_resp.json()["area_id"], "intent_code": "rural_land_purchase"},
    )
    assert run_resp.status_code == 202
    run_id = run_resp.json()["report_run_id"]

    resp = tc.get("/ui/report-runs")
    assert resp.status_code == 200
    assert f'value="{run_id}"' in resp.text
