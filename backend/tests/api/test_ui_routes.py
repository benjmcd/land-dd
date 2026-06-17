from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.operator_cases as operator_cases_api
import app.api.ui as ui_api
from app.api.dependencies import ApiServices, create_api_services, get_services
from app.api.intake import IntakeResponse
from app.api.reports import (
    ReportRunComparisonSummary,
)
from app.api.reports import (
    _build_comparison_summary as _reports_build_comparison_summary,
)
from app.core.config import Settings
from app.domain.enums import IntentCode
from app.domain.job_health import STALE_RUNNING_THRESHOLD_SECONDS
from app.main import create_app

client = TestClient(create_app())

_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"
_MANIFEST_PATH = (
    Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "golden_aois" / "manifest.yaml"
)


def _valid_geojson() -> dict[str, object]:
    data = json.loads((_FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


# Default fixture credentials (from Settings defaults)
_FIXTURE_REVIEWER_ID = "fixture-reviewer"
_FIXTURE_REVIEWER_TOKEN = "fixture-token-123"
_API_KEY = "production-key"
_CSRF_FIELD = "csrf_token"


def _csrf_token_from(html: str) -> str:
    match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


def _selected_county_cases() -> list[dict[str, object]]:
    import yaml

    manifest = cast(
        dict[str, object],
        yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8")),
    )
    cases = cast(list[dict[str, object]], manifest["cases"])
    return [
        {
            "case_id": case["case_id"],
            "county": case["county"],
            "state": case["state"],
            "intent": case["intent"],
            "description": case["description"],
            "fixture_scope": case.get("fixture_scope", "private_mvp_fixture"),
            "fixture_language": case.get(
                "fixture_language",
                "Packaged fixture-only selected-county private MVP case; not live coverage.",
            ),
            "connector_domains": cast(
                list[str],
                case["expected_connector_workflow_domains"],
            ),
            "not_evaluated_domains": cast(
                list[str],
                case["expected_not_evaluated_domains"],
            ),
            "expected_unknowns": cast(list[str], case["expected_unknowns"]),
            "fixture_only": True,
        }
        for case in cases
    ]


class _FakeOperatorCasesContract:
    def __init__(self) -> None:
        self._cases = {case["case_id"]: case for case in _selected_county_cases()}

    def list_selected_county_cases(self) -> list[dict[str, object]]:
        return list(self._cases.values())

    def get_selected_county_case(self, case_id: str) -> dict[str, object] | None:
        return self._cases.get(case_id)

    def create_selected_county_report(
        self,
        services: ApiServices,
        case_id: str,
        reviewer_id: str = "fixture-reviewer",
        reason: str = "private_mvp_fixture_only",
        workspace_id: UUID | None = None,
        requested_by: UUID | None = None,
    ) -> dict[str, object]:
        from uuid import NAMESPACE_URL, uuid5

        from app.domain.area_contracts import AreaContract
        from app.domain.enums import IntentCode

        case = self._cases[case_id]
        area_seed = (
            f"selected-county:{workspace_id}:{case_id}"
            if workspace_id
            else f"selected-county:{case_id}"
        )
        area_id = uuid5(NAMESPACE_URL, area_seed)
        if services.area_service.get(area_id) is None:
            services.area_service.create(
                AreaContract(
                    area_id=area_id,
                    workspace_id=workspace_id,
                    created_by=requested_by,
                    label=f"selected-county-{case_id.lower()}",
                    geom_geojson=_valid_geojson(),
                    geom_source="selected-county-fixture",
                )
            )
        report = services.report_service.create_report_run(
            area_id=area_id,
            intent_code=IntentCode(cast(str, case["intent"])),
            workspace_id=workspace_id,
            requested_by=requested_by,
        )
        approved = services.report_service.approve_report_run(
            report.report_run_id,
            reviewer_id=reviewer_id,
            reason=reason,
        )
        assert approved is not None
        return {
            "case_id": case_id,
            "report_run_id": str(approved.report_run_id),
            "review_status": approved.review_status.value,
            "status": approved.status.value,
            "fixture_only": True,
            "links": {
                "ui": f"/ui/report-runs/{approved.report_run_id}",
            },
        }


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


def _make_api_key_app_client_with_report() -> tuple[FastAPI, TestClient, str]:
    app = create_app(
        Settings(
            REQUIRE_API_KEY=True,
            API_KEYS=_API_KEY,
            UI_AUTH_COOKIE_SECRET="stable-ui-cookie-secret",
        )
    )
    tc = TestClient(app)
    headers = {"X-API-Key": _API_KEY}
    area_resp = tc.post(
        "/areas",
        headers=headers,
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    run_resp = tc.post(
        "/report-runs",
        headers=headers,
        json={
            "area_id": area_resp.json()["area_id"],
            "intent_code": "rural_land_purchase",
        },
    )
    assert run_resp.status_code == 202
    return app, tc, run_resp.json()["report_run_id"]


def _make_app_client_with_queued_report(
    *,
    running: bool = False,
) -> tuple[FastAPI, TestClient, str]:
    app = create_app()
    tc = TestClient(app)
    area_resp = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    services = cast(ApiServices, app.state.services)
    job = services.async_report_jobs.create(
        area_id=UUID(area_resp.json()["area_id"]),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    if running:
        services.async_report_jobs.mark_running(job.report_run_id)
    return app, tc, str(job.report_run_id)


def _assert_report_page_chrome(html: str) -> None:
    assert 'name="viewport"' in html
    assert 'content="width=device-width, initial-scale=1"' in html
    assert "report-page" in html
    assert 'class="report-shell"' in html
    assert 'class="status-panel' in html
    assert 'class="action-panel"' in html


def _assert_no_auto_refresh_controls(html: str) -> None:
    assert '<meta http-equiv="refresh"' not in html
    assert "Pause auto-refresh" not in html
    assert "Refresh now" not in html
    assert "Resume auto-refresh" not in html


def _report_list_row_html(html: str, report_run_id: str) -> str:
    value_pos = html.index(f'value="{report_run_id}"')
    row_start = html.rfind("<tr", 0, value_pos)
    row_end = html.index("</tr>", value_pos)
    return html[row_start : row_end + len("</tr>")]


def test_ui_index_returns_200_html() -> None:
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Land Diligence" in response.text
    assert 'name="viewport"' in response.text
    assert 'content="width=device-width, initial-scale=1"' in response.text


def test_ui_index_has_intent_form() -> None:
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "rural_land_purchase" in response.text
    assert "homestead_feasibility" in response.text


def test_ui_index_renders_selected_county_fixture_form(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        operator_cases_api,
        "resolve_operator_cases_contract",
        lambda: _FakeOperatorCasesContract(),
    )
    tc = TestClient(create_app())

    response = tc.get("/ui/")

    assert response.status_code == 200
    assert 'name="selected_county_case_id"' in response.text
    assert "Selected-County Private MVP Fixture Cases" in response.text
    assert "BUN-slope" in response.text


def test_ui_index_renders_operator_console_case_table(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        operator_cases_api,
        "resolve_operator_cases_contract",
        lambda: _FakeOperatorCasesContract(),
    )
    tc = TestClient(create_app())

    response = tc.get("/ui/")

    assert response.status_code == 200
    assert 'aria-label="Operator console navigation"' in response.text
    assert '<main class="console-grid">' in response.text
    assert '<table class="case-table">' in response.text
    assert "<caption>Selected-county fixture cases</caption>" in response.text
    assert response.text.count('action="/ui/operator-cases/report"') >= 2
    assert "reviewer_id" in response.text
    assert "reviewer_token" in response.text
    assert 'data-required-scope="report:run"' in response.text
    assert 'data-label="Case"' in response.text
    assert 'data-label="Boundary"' in response.text
    assert 'data-label="Action"' in response.text
    assert 'value="BUN-slope"' in response.text
    assert "Connector domains" in response.text
    assert "Expected unknowns" in response.text
    assert "assessor_not_evaluated" in response.text
    assert "not live coverage" in response.text
    assert "Create approved report" in response.text
    assert "overflow-wrap: anywhere" in response.text
    assert "display: block" in response.text
    assert "margin-bottom: 0.2rem" in response.text


def test_ui_index_has_primary_connector_review_queue_nav_link() -> None:
    response = client.get("/ui/")

    assert response.status_code == 200
    nav_start = response.text.index(
        '<nav class="console-nav" aria-label="Operator console navigation">'
    )
    nav_end = response.text.index("</nav>", nav_start)
    nav_html = response.text[nav_start:nav_end]
    assert 'href="/ui/connector-review-queue"' in nav_html
    assert "Connector review queue" in nav_html


def test_ui_index_keeps_accessible_custom_geojson_intake() -> None:
    response = client.get("/ui/")

    assert response.status_code == 200
    assert 'id="custom-report-panel"' in response.text
    assert 'for="area_geojson"' in response.text
    assert 'id="area_geojson"' in response.text
    assert 'aria-describedby="custom-intake-help"' in response.text
    assert 'for="intent"' in response.text
    assert 'id="intent"' in response.text


def test_ui_custom_geojson_intake_form_posts_without_javascript() -> None:
    response = client.get("/ui/")

    assert response.status_code == 200
    assert 'id="report-form"' in response.text
    assert 'method="POST"' in response.text
    assert 'action="/ui/intake"' in response.text
    assert 'type="submit"' in response.text
    assert "submitReport()" in response.text


def test_ui_custom_geojson_intake_valid_submission_redirects_to_report_page() -> None:
    tc = TestClient(create_app())

    response = tc.post(
        "/ui/intake",
        data={
            "area_geojson": json.dumps(_valid_geojson()),
            "intent": "rural_land_purchase",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/ui/report-runs/")

    report_response = tc.get(location)
    assert report_response.status_code == 200
    assert "text/html" in report_response.headers["content-type"]
    assert location.rsplit("/", 1)[-1] in report_response.text


def test_ui_custom_geojson_intake_invalid_json_returns_safe_html_error() -> None:
    response = client.post(
        "/ui/intake",
        data={
            "area_geojson": "<script>alert(1)</script>",
            "intent": "rural_land_purchase",
        },
    )

    assert response.status_code == 422
    assert "text/html" in response.headers["content-type"]
    assert "Invalid GeoJSON" in response.text
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" not in response.text
    assert 'href="/ui/"' in response.text


def test_ui_custom_geojson_intake_unknown_intent_returns_html_error() -> None:
    response = client.post(
        "/ui/intake",
        data={
            "area_geojson": json.dumps(_valid_geojson()),
            "intent": "not_a_real_intent",
        },
    )

    assert response.status_code == 422
    assert "text/html" in response.headers["content-type"]
    assert "Invalid report intent" in response.text
    assert "not_a_real_intent" not in response.text
    assert 'href="/ui/"' in response.text


def test_ui_custom_geojson_intake_js_handles_invalid_geojson() -> None:
    response = client.get("/ui/")

    assert response.status_code == 200
    assert "Invalid GeoJSON. Enter a valid GeoJSON object." in response.text
    assert "JSON.parse(geojson)" in response.text
    assert "return;" in response.text


def test_ui_custom_geojson_intake_pending_connector_review_redirects(
    monkeypatch: Any,
) -> None:
    ingest_run_id = uuid4()

    def _pending_intake_report(**_kwargs: object) -> IntakeResponse:
        return IntakeResponse(
            area_id=uuid4(),
            status="pending_connector_review",
            connector_ingest_run_id=ingest_run_id,
            connector_review_status="queued",
        )

    monkeypatch.setattr(ui_api, "intake_report", _pending_intake_report)
    tc = TestClient(create_app())

    response = tc.post(
        "/ui/intake",
        data={
            "area_geojson": json.dumps(_valid_geojson()),
            "intent": "rural_land_purchase",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (f"/ui/connector-review-queue/{ingest_run_id}")


def test_ui_selected_county_fixture_post_redirects_to_report_run(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        operator_cases_api,
        "resolve_operator_cases_contract",
        lambda: _FakeOperatorCasesContract(),
    )
    tc = TestClient(create_app())

    response = tc.post(
        "/ui/operator-cases/report",
        data={
            "selected_county_case_id": "BUN-slope",
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "land_dd_ui_reviewer" in response.headers.get("set-cookie", "")
    location = response.headers["location"]
    assert location.startswith("/ui/report-runs/")

    report_response = tc.get(location)

    assert report_response.status_code == 200
    assert "Executive Summary" in report_response.text


def test_ui_selected_county_fixture_post_requires_report_run_reviewer(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        operator_cases_api,
        "resolve_operator_cases_contract",
        lambda: _FakeOperatorCasesContract(),
    )
    tc = TestClient(create_app())

    response = tc.post(
        "/ui/operator-cases/report",
        data={"selected_county_case_id": "BUN-slope"},
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert "Authentication Error" in response.text


def test_ui_selected_county_fixture_post_fails_closed_outside_local_env(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        operator_cases_api,
        "resolve_operator_cases_contract",
        lambda: _FakeOperatorCasesContract(),
    )
    settings = Settings(
        APP_ENV="production",
        USE_DB_SERVICES=True,
        REVIEWER_ACCOUNTS=(
            f"reviewer:sha256:{hashlib.sha256(b'token').hexdigest()}"
        ),
        REVIEWER_ACCOUNT_SCOPES="reviewer:report:run",
        UI_AUTH_COOKIE_SECRET="stable-ui-cookie-secret-for-prod-test",
    )
    app = create_app(settings=settings)
    app.dependency_overrides[get_services] = lambda: create_api_services(settings)
    tc = TestClient(app)

    response = tc.post(
        "/ui/operator-cases/report",
        data={
            "selected_county_case_id": "BUN-slope",
            "reviewer_id": "reviewer",
            "reviewer_token": "token",
        },
        follow_redirects=False,
    )

    assert response.status_code == 403
    assert "UI workspace identity is not configured" in response.text


def test_ui_report_run_returns_404_page_for_unknown_id() -> None:
    response = client.get(f"/ui/report-runs/{uuid4()}")
    assert response.status_code == 200  # We return 200 HTML with "not found" message
    assert "text/html" in response.headers["content-type"]
    assert "Not Found" in response.text
    _assert_report_page_chrome(response.text)
    assert 'href="/ui/report-runs"' in response.text
    assert "All Reports" in response.text


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
    _assert_report_page_chrome(response.text)
    assert "Operator Action" in response.text
    assert f'action="/ui/report-runs/{report_run_id}/approve"' in response.text
    assert 'method="POST"' in response.text
    assert "reviewer_id" in response.text
    assert "reviewer_token" in response.text
    assert '<textarea name="reason"' in response.text
    reason_field = response.text.split('<textarea name="reason"', 1)[1].split(
        "</textarea>",
        1,
    )[0]
    assert "required" not in reason_field
    _assert_no_auto_refresh_controls(response.text)


def test_ui_report_run_queued_page_has_safe_action_surface() -> None:
    _app, tc, report_run_id = _make_app_client_with_queued_report()
    response = tc.get(f"/ui/report-runs/{report_run_id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "queued" in response.text
    _assert_report_page_chrome(response.text)
    assert '<meta http-equiv="refresh" content="3">' in response.text
    assert "This page refreshes every 3 seconds." in response.text
    assert "<form class='refresh-interval-form'" in response.text
    assert "Refresh interval" in response.text
    assert "<option value='3' selected>3 seconds</option>" in response.text
    assert "<option value='30'>30 seconds</option>" in response.text
    assert f'href="/ui/report-runs/{report_run_id}?auto_refresh=false"' in response.text
    assert "Pause auto-refresh" in response.text
    assert 'href="/ui/report-runs"' in response.text
    assert "All Reports" in response.text


def test_ui_report_run_queued_page_can_change_auto_refresh_interval() -> None:
    _app, tc, report_run_id = _make_app_client_with_queued_report()
    response = tc.get(f"/ui/report-runs/{report_run_id}?refresh_seconds=30")
    assert response.status_code == 200
    assert "queued" in response.text
    _assert_report_page_chrome(response.text)
    assert '<meta http-equiv="refresh" content="30">' in response.text
    assert "This page refreshes every 30 seconds." in response.text
    assert "<option value='30' selected>30 seconds</option>" in response.text
    assert (
        f'href="/ui/report-runs/{report_run_id}?auto_refresh=false&refresh_seconds=30"'
        in response.text
    )


def test_ui_report_run_queued_page_can_pause_auto_refresh() -> None:
    _app, tc, report_run_id = _make_app_client_with_queued_report()
    response = tc.get(f"/ui/report-runs/{report_run_id}?auto_refresh=false")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "queued" in response.text
    _assert_report_page_chrome(response.text)
    assert '<meta http-equiv="refresh"' not in response.text
    assert "Auto-refresh is paused." in response.text
    assert f'href="/ui/report-runs/{report_run_id}?auto_refresh=false"' in response.text
    assert f'href="/ui/report-runs/{report_run_id}"' in response.text
    assert "Refresh now" in response.text
    assert "Resume auto-refresh" in response.text


def test_ui_report_run_paused_page_preserves_changed_refresh_interval() -> None:
    _app, tc, report_run_id = _make_app_client_with_queued_report()
    response = tc.get(f"/ui/report-runs/{report_run_id}?auto_refresh=false&refresh_seconds=30")
    assert response.status_code == 200
    assert '<meta http-equiv="refresh"' not in response.text
    assert "Auto-refresh is paused." in response.text
    assert "name='auto_refresh' value='false'" in response.text
    assert "<option value='30' selected>30 seconds</option>" in response.text
    assert (
        f'href="/ui/report-runs/{report_run_id}?auto_refresh=false&refresh_seconds=30"'
        in response.text
    )
    assert f'href="/ui/report-runs/{report_run_id}?refresh_seconds=30"' in response.text


def test_ui_report_run_running_page_has_same_auto_refresh_controls() -> None:
    _app, tc, report_run_id = _make_app_client_with_queued_report(running=True)
    response = tc.get(f"/ui/report-runs/{report_run_id}")
    assert response.status_code == 200
    assert "running" in response.text
    assert '<meta http-equiv="refresh" content="3">' in response.text
    assert f'href="/ui/report-runs/{report_run_id}?auto_refresh=false"' in response.text
    assert "Pause auto-refresh" in response.text


def test_ui_report_run_shows_dossier_after_approval() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(UUID(report_run_id), reviewer_id="test-reviewer")
    response = tc.get(f"/ui/report-runs/{report_run_id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Executive Summary" in response.text
    _assert_no_auto_refresh_controls(response.text)


def test_ui_report_run_list_returns_html_table() -> None:
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.get("/ui/report-runs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert report_run_id[:8] in response.text


def test_ui_report_run_list_pending_approval_action_links_to_detail() -> None:
    _app, tc, report_run_id = _make_app_client_with_report()
    response = tc.get("/ui/report-runs")

    assert response.status_code == 200
    assert "<th>Action</th>" in response.text
    row = _report_list_row_html(response.text, report_run_id)
    assert f'href="/ui/report-runs/{report_run_id}"' in row
    assert "Approve from detail" in row
    assert f'action="/ui/report-runs/{report_run_id}/approve"' not in row
    assert f'href="/report-runs/{report_run_id}/dossier?download=1"' not in row
    assert f'href="/report-runs/{report_run_id}/artifact"' not in row


def test_ui_report_run_list_table_has_responsive_scroll_wrapper() -> None:
    _app, tc, _report_run_id = _make_app_client_with_report()
    response = tc.get("/ui/report-runs")

    assert response.status_code == 200
    assert '<div class="report-table-wrap">' in response.text
    assert '<table class="report-runs-table">' in response.text
    assert "overflow-x:auto" in response.text
    assert "@media (max-width:640px)" in response.text
    assert ".report-table-wrap { overflow-x:visible; }" in response.text
    assert ".report-runs-table { min-width:0; }" in response.text
    assert ".report-runs-table thead {" in response.text
    assert "clip-path:inset(50%);" in response.text
    assert "position:absolute;" in response.text
    assert ".report-runs-table thead { display:none; }" not in response.text
    assert "content:attr(data-label)" in response.text
    for label in ("Select", "ID", "Intent", "Status", "Created", "Action"):
        assert f'data-label="{label}"' in response.text


def test_ui_report_run_list_approved_action_links_to_delivery_surfaces() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(UUID(report_run_id), reviewer_id="test-reviewer")
    response = tc.get("/ui/report-runs")

    assert response.status_code == 200
    row = _report_list_row_html(response.text, report_run_id)
    assert f'href="/ui/report-runs/{report_run_id}"' in row
    assert "View dossier" in row
    assert f'href="/report-runs/{report_run_id}/dossier?download=1"' in row
    assert "Download dossier" in row
    assert f'href="/report-runs/{report_run_id}/artifact"' in row
    assert "Download JSON" in row
    assert f'href="/ui/report-runs/{report_run_id}/lineage"' in row
    assert "Lineage" in row
    assert "Approve from detail" not in row


def test_ui_report_run_list_failed_action_links_to_retry_detail() -> None:
    _app, tc, report_run_id = _make_app_client_with_failed_report()
    response = tc.get("/ui/report-runs")

    assert response.status_code == 200
    row = _report_list_row_html(response.text, report_run_id)
    assert f'href="/ui/report-runs/{report_run_id}"' in row
    assert "Retry from detail" in row
    assert f'action="/ui/report-runs/{report_run_id}/retry"' not in row


def test_ui_report_run_list_queued_action_links_to_status_detail() -> None:
    _app, tc, report_run_id = _make_app_client_with_queued_report()
    response = tc.get("/ui/report-runs")

    assert response.status_code == 200
    row = _report_list_row_html(response.text, report_run_id)
    assert f'href="/ui/report-runs/{report_run_id}"' in row
    assert "Open status" in row


def test_ui_report_run_list_running_action_links_to_status_detail() -> None:
    _app, tc, report_run_id = _make_app_client_with_queued_report(running=True)
    response = tc.get("/ui/report-runs")

    assert response.status_code == 200
    row = _report_list_row_html(response.text, report_run_id)
    assert f'href="/ui/report-runs/{report_run_id}"' in row
    assert "Open status" in row


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
    assert response.status_code == 303
    assert response.headers["location"] == f"/ui/report-runs/{report_run_id}"

    services = cast(ApiServices, app.state.services)
    report = services.report_service.get_report_run(UUID(report_run_id))
    assert report is not None
    assert report.review_status.value == "approved"

    dossier_resp = tc.get(f"/ui/report-runs/{report_run_id}")
    assert "Executive Summary" in dossier_resp.text


def test_ui_approve_report_run_accepts_reviewer_session_without_form_credentials() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    reviewer_login = tc.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
        },
        follow_redirects=False,
    )
    assert reviewer_login.status_code == 303

    page = tc.get(f"/ui/report-runs/{report_run_id}")
    assert "Using reviewer session" in page.text
    assert "reviewer_token" not in page.text

    response = tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={},
        follow_redirects=False,
    )

    assert response.status_code == 303
    services = cast(ApiServices, app.state.services)
    report = services.report_service.get_report_run(UUID(report_run_id))
    assert report is not None
    assert report.review_status.value == "approved"
    assert report.reviewed_by == _FIXTURE_REVIEWER_ID


def test_ui_approve_report_run_reviewer_session_requires_csrf_with_ui_cookie_auth() -> None:
    app, tc, report_run_id = _make_api_key_app_client_with_report()
    api_login = tc.post(
        "/ui/auth",
        data={"api_key": _API_KEY},
        follow_redirects=False,
    )
    assert api_login.status_code == 303
    reviewer_form = tc.get("/ui/auth/reviewer")
    reviewer_login = tc.post(
        "/ui/auth/reviewer",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
            _CSRF_FIELD: _csrf_token_from(reviewer_form.text),
        },
        follow_redirects=False,
    )
    assert reviewer_login.status_code == 303

    report_page = tc.get(f"/ui/report-runs/{report_run_id}")
    assert report_page.status_code == 200
    assert "Using reviewer session" in report_page.text
    assert "reviewer_token" not in report_page.text
    missing_csrf = tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={},
        follow_redirects=False,
    )
    valid = tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={_CSRF_FIELD: _csrf_token_from(report_page.text)},
        follow_redirects=False,
    )

    assert missing_csrf.status_code == 403
    assert valid.status_code == 303
    services = cast(ApiServices, app.state.services)
    report = services.report_service.get_report_run(UUID(report_run_id))
    assert report is not None
    assert report.review_status.value == "approved"


def test_ui_approve_report_run_records_authenticated_reviewer_id() -> None:
    """Audit integrity: reviewed_by must be the authenticated reviewer, not a fallback.

    Two accounts are configured so the test detects a regression to the
    first-configured-account fallback: we authenticate as the SECOND account
    and assert that the stored reviewed_by matches the second account.
    """
    _SECOND_REVIEWER_ID = "second-reviewer"
    _SECOND_REVIEWER_TOKEN = "second-token-456"
    settings = Settings(
        REVIEWER_ACCOUNTS=(
            f"{_FIXTURE_REVIEWER_ID}:{_FIXTURE_REVIEWER_TOKEN}"
            f",{_SECOND_REVIEWER_ID}:{_SECOND_REVIEWER_TOKEN}"
        ),
        REVIEWER_ACCOUNT_SCOPES=(
            f"{_FIXTURE_REVIEWER_ID}:connector:run|connector:review|operations:read"
            f"|report:approve|report:retry|report:run"
            f",{_SECOND_REVIEWER_ID}:connector:run|connector:review|operations:read"
            f"|report:approve|report:retry|report:run"
        ),
    )
    app, tc, report_run_id = _make_app_client_with_report(settings)
    tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={
            "reviewer_id": _SECOND_REVIEWER_ID,
            "reviewer_token": _SECOND_REVIEWER_TOKEN,
        },
    )
    services = cast(ApiServices, app.state.services)
    report = services.report_service.get_report_run(UUID(report_run_id))
    assert report is not None
    assert report.reviewed_by == _SECOND_REVIEWER_ID


def test_ui_approve_report_run_records_optional_reason() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
            "reason": "  checked source packet  ",
        },
    )
    assert response.status_code == 200

    services = cast(ApiServices, app.state.services)
    report = services.report_service.get_report_run(UUID(report_run_id))
    assert report is not None
    assert report.review_actions[-1].reason == "checked source packet"


def test_ui_approve_report_run_blank_reason_stores_none() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    response = tc.post(
        f"/ui/report-runs/{report_run_id}/approve",
        data={
            "reviewer_id": _FIXTURE_REVIEWER_ID,
            "reviewer_token": _FIXTURE_REVIEWER_TOKEN,
            "reason": "   ",
        },
    )
    assert response.status_code == 200

    services = cast(ApiServices, app.state.services)
    report = services.report_service.get_report_run(UUID(report_run_id))
    assert report is not None
    assert report.review_actions[-1].reason is None


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
    _assert_report_page_chrome(response.text)
    assert "Operator Action" in response.text
    assert f'href="/ui/report-runs/{report_run_id}"' in response.text
    assert 'href="/ui/report-runs"' in response.text
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
    _assert_report_page_chrome(response.text)
    assert "Operator Action" in response.text
    assert 'href="/ui/report-runs"' in response.text
    assert 'href="/ui/"' in response.text
    assert "Executive Summary" not in response.text


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
    _assert_report_page_chrome(response.text)
    assert f'action="/ui/report-runs/{report_run_id}/retry"' in response.text
    assert 'method="POST"' in response.text
    assert 'href="/ui/report-runs"' in response.text


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
    assert response.status_code == 303
    # Verify the new run was created in the job store
    services = cast(ApiServices, app.state.services)
    all_jobs = services.async_report_jobs.list_recent(limit=100)
    new_jobs = [j for j in all_jobs if str(j.report_run_id) != report_run_id]
    assert len(new_jobs) >= 1
    # The new job should link back to the original as retry_of
    new_job = new_jobs[0]
    assert new_job.retry_of_report_run_id == UUID(report_run_id)
    assert response.headers["location"] == f"/ui/report-runs/{new_job.report_run_id}"


def test_ui_report_runs_list_has_operations_link() -> None:
    tc = TestClient(create_app())
    response = tc.get("/ui/report-runs")
    assert response.status_code == 200
    assert "/ui/operations" in response.text
    assert "Operations" in response.text


def test_ui_report_runs_list_has_connector_review_queue_nav_link() -> None:
    tc = TestClient(create_app())
    response = tc.get("/ui/report-runs")

    assert response.status_code == 200
    home_pos = response.text.index('href="/ui/"')
    operations_pos = response.text.index('href="/ui/operations"')
    queue_pos = response.text.index('href="/ui/connector-review-queue"')
    heading_pos = response.text.index("<h1>Report Runs</h1>")
    assert home_pos < operations_pos < queue_pos < heading_pos
    assert "Connector review queue" in response.text[:heading_pos]
    assert '<nav class="report-list-nav" aria-label="Report list navigation">' in response.text
    assert ".report-list-nav {" in response.text
    assert "display:flex; flex-wrap:wrap;" in response.text
    assert ".report-list-nav a { min-width:0; overflow-wrap:anywhere; }" in response.text
    assert ".report-list-nav .sep { display:none; }" in response.text


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


def test_ui_report_run_list_and_detail_show_stale_running_metadata() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    report_uuid = UUID(report_run_id)
    services.async_report_jobs.mark_running(report_uuid)
    job = services.async_report_jobs.get(report_uuid)
    assert job is not None
    job.started_at = datetime.now(UTC) - timedelta(
        seconds=STALE_RUNNING_THRESHOLD_SECONDS + 1,
    )

    list_resp = tc.get("/ui/report-runs?status=running")
    detail_resp = tc.get(f"/ui/report-runs/{report_run_id}")

    assert list_resp.status_code == 200
    assert "Running Age" in list_resp.text
    assert "stale" in list_resp.text
    assert report_run_id[:8] in list_resp.text
    assert detail_resp.status_code == 200
    assert "Running age:" in detail_resp.text
    assert "stale" in detail_resp.text


def test_ui_report_run_list_stale_filter_requires_running_status() -> None:
    tc = TestClient(create_app())

    missing_status = tc.get("/ui/report-runs?stale=true")
    failed_status = tc.get("/ui/report-runs?status=failed&stale=true")

    assert missing_status.status_code == 422
    assert failed_status.status_code == 422
    assert "Invalid Stale Filter" in missing_status.text
    assert "status=running" in missing_status.text
    assert "Invalid Stale Filter" in failed_status.text
    assert "status=running" in failed_status.text


def test_ui_report_run_list_stale_filter_shows_only_stale_running_rows() -> None:
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    report_uuid = UUID(report_run_id)
    fresh = services.async_report_jobs.create(
        area_id=uuid4(),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    failed = services.async_report_jobs.create(
        area_id=uuid4(),
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    services.async_report_jobs.mark_running(report_uuid)
    services.async_report_jobs.mark_running(fresh.report_run_id)
    services.async_report_jobs.mark_failed(failed.report_run_id, error_msg="boom")
    stale_job = services.async_report_jobs.get(report_uuid)
    assert stale_job is not None
    stale_job.started_at = datetime.now(UTC) - timedelta(
        seconds=STALE_RUNNING_THRESHOLD_SECONDS + 1,
    )

    resp = tc.get("/ui/report-runs?status=running&stale=true")

    assert resp.status_code == 200
    assert "Stale running" in resp.text
    assert report_run_id[:8] in resp.text
    assert str(fresh.report_run_id)[:8] not in resp.text
    assert str(failed.report_run_id)[:8] not in resp.text


def test_ui_report_run_list_invalid_status_filter_fails_closed() -> None:
    tc = TestClient(create_app())
    resp = tc.get("/ui/report-runs?status=not_a_real_status")
    assert resp.status_code == 422
    assert "text/html" in resp.headers["content-type"]
    assert "Invalid Status Filter" in resp.text
    assert "not_a_real_status" in resp.text
    assert "queued" in resp.text


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


def test_ui_report_run_list_pagination_preserves_stale_filter() -> None:
    tc = TestClient(create_app())
    resp = tc.get("/ui/report-runs?status=running&stale=true&offset=30")
    assert resp.status_code == 200
    if "Previous" in resp.text:
        assert "status=running" in resp.text
        assert "stale=true" in resp.text


# ---------------------------------------------------------------------------
# S6 — Evidence lineage UI
# ---------------------------------------------------------------------------


def test_ui_lineage_page_unknown_id_returns_html_not_found() -> None:
    tc = TestClient(create_app())
    resp = tc.get(f"/ui/report-runs/{uuid4()}/lineage")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert 'name="viewport"' in resp.text
    assert "href='/ui/report-runs'" in resp.text
    assert "Not Found" in resp.text


def test_ui_lineage_page_invalid_uuid_returns_422() -> None:
    tc = TestClient(create_app())
    resp = tc.get("/ui/report-runs/not-a-uuid/lineage")
    assert resp.status_code == 422


def test_ui_lineage_page_renders_claim_evidence_mapping() -> None:
    """Lineage page renders claim->evidence and evidence->claim sections."""
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(
        UUID(report_run_id),
        reviewer_id="test-reviewer",
    )
    resp = tc.get(f"/ui/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert 'name="viewport"' in resp.text
    assert f"href='/ui/report-runs/{report_run_id}'" in resp.text
    assert "href='/ui/report-runs'" in resp.text
    # Structural headings
    assert "Evidence Lineage" in resp.text
    assert "Claims" in resp.text
    assert "Evidence" in resp.text
    assert "Sources" in resp.text
    assert "table-scroll" in resp.text
    # Report run ID appears in the page
    assert report_run_id[:8] in resp.text


def test_ui_lineage_page_shows_evidence_records() -> None:
    """The lineage page lists at least one evidence record from the fixture report."""
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(
        UUID(report_run_id),
        reviewer_id="test-reviewer",
    )
    resp = tc.get(f"/ui/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    # The fixture connector always generates evidence — at least one row must appear.
    assert "No evidence records" not in resp.text


def test_ui_lineage_page_shows_claim_records() -> None:
    """The lineage page lists at least one claim from the fixture report."""
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(
        UUID(report_run_id),
        reviewer_id="test-reviewer",
    )
    resp = tc.get(f"/ui/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    assert "No claims" not in resp.text


def test_ui_lineage_page_requires_approved_report() -> None:
    """Pending report lineage is not exposed through the operator UI."""
    app, tc, report_run_id = _make_app_client_with_report()
    resp = tc.get(f"/ui/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 409
    assert "text/html" in resp.headers["content-type"]
    assert "Approval Required" in resp.text
    assert "review_status=needs_review" in resp.text
    assert f"href='/ui/report-runs/{report_run_id}'" in resp.text
    assert "Evidence Lineage" not in resp.text


def test_ui_lineage_page_approved_report_needs_no_reviewer_credentials() -> None:
    """Approved report lineage remains viewable without passing reviewer credentials."""
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(
        UUID(report_run_id),
        reviewer_id="test-reviewer",
    )
    resp = tc.get(f"/ui/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    assert "Evidence Lineage" in resp.text
    assert "reviewer_token" not in resp.text


def test_ui_approved_report_page_has_lineage_link() -> None:
    """The approved report page shows a 'View evidence lineage' link."""
    app, tc, report_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(
        UUID(report_run_id),
        reviewer_id="test-reviewer",
    )
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


def _make_two_same_area_report_runs() -> tuple[FastAPI, TestClient, str, str]:
    app = create_app()
    tc = TestClient(app)
    area_resp = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    services = cast(ApiServices, app.state.services)
    first = services.report_service.create_report_run(
        area_id=UUID(area_resp.json()["area_id"]),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    second = services.report_service.create_report_run(
        area_id=UUID(area_resp.json()["area_id"]),
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    return app, tc, str(first.report_run_id), str(second.report_run_id)


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


def test_ui_compare_accepts_repeated_ids_query_params() -> None:
    """GET /ui/compare?ids=a&ids=b returns the same comparison page."""
    tc, run1, run2 = _make_two_report_runs()
    resp = tc.get(f"/ui/compare?ids={run1}&ids={run2}")
    assert resp.status_code == 200
    assert "Compare Report Runs" in resp.text
    assert run1[:8] in resp.text
    assert run2[:8] in resp.text


def test_ui_compare_shows_review_delivery_status_and_actions() -> None:
    app, tc, pending_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    area_resp = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    approved_report = services.report_service.create_report_run(
        area_id=UUID(area_resp.json()["area_id"]),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    services.report_service.approve_report_run(
        approved_report.report_run_id,
        reviewer_id="compare-reviewer",
    )

    resp = tc.get(f"/ui/compare?ids={pending_run_id},{approved_report.report_run_id}")

    assert resp.status_code == 200
    assert "Review Status" in resp.text
    assert "Delivery Status" in resp.text
    assert "Next Action" in resp.text
    assert "needs_review" in resp.text
    assert "approved" in resp.text
    assert "Approval required" in resp.text
    assert "Delivery available" in resp.text
    assert "Approve from detail" in resp.text
    assert "View dossier" in resp.text
    assert "Download dossier" in resp.text
    assert "Download JSON" in resp.text
    assert "Lineage" in resp.text


def test_ui_compare_does_not_expose_pending_delivery_links() -> None:
    app, tc, pending_run_id = _make_app_client_with_report()
    services = cast(ApiServices, app.state.services)
    area_resp = tc.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    approved_report = services.report_service.create_report_run(
        area_id=UUID(area_resp.json()["area_id"]),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    services.report_service.approve_report_run(
        approved_report.report_run_id,
        reviewer_id="compare-reviewer",
    )

    resp = tc.get(f"/ui/compare?ids={pending_run_id},{approved_report.report_run_id}")

    assert resp.status_code == 200
    assert f'href="/report-runs/{pending_run_id}/dossier?download=1"' not in resp.text
    assert f'href="/report-runs/{pending_run_id}/artifact"' not in resp.text
    assert f'href="/ui/report-runs/{pending_run_id}/print"' not in resp.text
    assert f'href="/ui/report-runs/{pending_run_id}/lineage"' not in resp.text
    assert f'href="/ui/report-runs/{pending_run_id}"' in resp.text
    assert f'href="/report-runs/{approved_report.report_run_id}/dossier?download=1"' in resp.text
    assert f'href="/report-runs/{approved_report.report_run_id}/artifact"' in resp.text
    assert f'href="/ui/report-runs/{approved_report.report_run_id}/lineage"' in resp.text


def test_ui_compare_renders_high_severity_code_domain_details(
    monkeypatch: Any,
) -> None:
    tc, run1, run2 = _make_two_report_runs()
    original_summary = _reports_build_comparison_summary

    def _summary_with_high_severity(report: object) -> ReportRunComparisonSummary:
        base = original_summary(report)  # type: ignore[arg-type]
        if str(base.report_run_id) == run1:
            base.high_severity_claims = [
                {"claim_code": "FLOOD_HIGH_RISK", "domain": "flood"},
                {"claim_code": "ACCESS_NO_PUBLIC_ROAD", "domain": "access"},
            ]
        return base

    monkeypatch.setattr(
        ui_api,
        "_build_comparison_summary",
        _summary_with_high_severity,
    )

    resp = tc.get(f"/ui/compare?ids={run1},{run2}")

    assert resp.status_code == 200
    assert "High-Severity Details" in resp.text
    assert "FLOOD_HIGH_RISK" in resp.text
    assert "flood" in resp.text
    assert "ACCESS_NO_PUBLIC_ROAD" in resp.text
    assert "access" in resp.text


def test_ui_compare_table_has_responsive_scroll_and_wrapping() -> None:
    tc, run1, run2 = _make_two_report_runs()

    resp = tc.get(f"/ui/compare?ids={run1},{run2}")

    assert resp.status_code == 200
    assert '<div class="compare-table-wrap">' in resp.text
    assert '<table class="compare-table">' in resp.text
    assert "overflow-x: auto" in resp.text
    assert "overflow-wrap: anywhere" in resp.text


def test_ui_compare_same_area_renders_change_review() -> None:
    _app, tc, run1, run2 = _make_two_same_area_report_runs()

    resp = tc.get(f"/ui/compare?ids={run1},{run2}")

    assert resp.status_code == 200
    assert "Change Review" in resp.text
    assert "Same Area" in resp.text
    assert "Added Claim Codes" in resp.text
    assert "Removed Claim Codes" in resp.text
    assert "Added Sources" in resp.text
    assert "Removed Sources" in resp.text
    assert "Evidence Count Delta" in resp.text
    assert "Ruleset Changed" in resp.text


def test_ui_compare_change_review_values_match_api_diff() -> None:
    _app, tc, run1, run2 = _make_two_same_area_report_runs()
    api_resp = tc.get(f"/report-runs/{run2}/diff?base_id={run1}")
    assert api_resp.status_code == 200
    diff = api_resp.json()

    ui_resp = tc.get(f"/ui/compare?ids={run1},{run2}")

    assert ui_resp.status_code == 200
    assert ("Yes" if diff["ruleset_changed"] else "No") in ui_resp.text
    assert str(diff["evidence_count_delta"]) in ui_resp.text
    for key in (
        "added_claim_codes",
        "removed_claim_codes",
        "added_sources",
        "removed_sources",
    ):
        for value in diff[key]:
            assert value in ui_resp.text


def test_ui_compare_different_areas_renders_change_review_note() -> None:
    tc, run1, run2 = _make_two_report_runs()

    resp = tc.get(f"/ui/compare?ids={run1},{run2}")

    assert resp.status_code == 200
    assert "Change Review" in resp.text
    assert "requires the same area" in resp.text
    assert "Claims" in resp.text
    assert "Red Flags" in resp.text


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
    """The report list page contains a native GET form compare affordance."""
    _app, tc, _report_run_id = _make_app_client_with_report()
    resp = tc.get("/ui/report-runs")
    assert resp.status_code == 200
    form_start = resp.text.index('<form method="GET" action="/ui/compare"')
    form_end = resp.text.index("</form>", form_start)
    checkbox_pos = resp.text.index('type="checkbox" class="cmp-check" name="ids"')
    assert form_start < checkbox_pos < form_end
    assert "cmp-check" in resp.text
    assert 'type="checkbox" class="cmp-check" name="ids"' in resp.text
    form_html = resp.text[form_start:form_end]
    assert "onsubmit" not in form_html
    assert "goCompare" not in resp.text
    assert "cmp-msg" not in resp.text
    assert "<script>" not in resp.text
    assert "Select 2&#8211;4 report rows." in form_html
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
