from __future__ import annotations

import html as _html
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.api.dependencies import ApiServices, get_services
from app.api.operations import JobQueueHealthResponse, job_queue_health_response
from app.api.reviewer_auth import REVIEWER_SCOPE_OPERATIONS_READ
from app.api.ui_shared import (
    attach_ui_reviewer_session_cookie,
    build_css,
    csrf_form_field,
    error_page,
    page_head,
    require_ui_csrf,
    require_ui_reviewer,
    reviewer_credential_fields,
    ui_reviewer_principal_from_cookie,
)

router = APIRouter(prefix="/ui/operations", tags=["ui"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]

_OPS_CSS = build_css(
    "table { margin-bottom: 1.5rem; }\n"
    ".ops-table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch;"
    " margin-bottom: 1.5rem; }\n"
    ".ops-table-wrap table { min-width: 920px; margin-bottom: 0; }\n"
    ".auth-form { display: flex; flex-direction: column; gap: 0.75rem; max-width: 320px;"
    " margin-top: 1rem; }\n"
    ".auth-form label { font-size: 0.95rem; }\n"
    ".auth-form input { display: block; width: 100%; padding: 0.4rem; font-size: 1rem; }\n"
    ".auth-form button { background: #2c3e50; color: white; border: none; padding: 0.5rem 1rem;"
    " font-size: 1rem; cursor: pointer; border-radius: 4px; }\n",
)


def _credential_form(
    request: Request,
    services: ApiServices,
    csrf_field: str = "",
) -> str:
    reviewer_fields = reviewer_credential_fields(
        request,
        services,
        required_scope=REVIEWER_SCOPE_OPERATIONS_READ,
    )
    return (
        "<form method='post' action='/ui/operations' class='auth-form'>"
        f"{csrf_field}"
        f"{reviewer_fields}"
        "<button type='submit'>View Dashboard</button>"
        "</form>"
    )


def _reviewer_has_operations_scope(request: Request, services: ApiServices) -> str | None:
    principal = ui_reviewer_principal_from_cookie(request, services)
    if principal is None or REVIEWER_SCOPE_OPERATIONS_READ not in principal.scopes:
        return None
    return principal.reviewer_id


def _dashboard_response(
    *,
    reviewer_id: str,
    services: ApiServices,
) -> HTMLResponse:
    report_health = job_queue_health_response(services.async_report_jobs.health())
    connector_health = job_queue_health_response(services.live_connector_jobs.health())

    report_table = _render_health_table("Report Jobs", report_health, "/ui/report-runs")
    connector_table = _render_health_table(
        "Live Connector Jobs",
        connector_health,
        "/ui/live-connector-jobs",
    )

    principal_esc = _html.escape(reviewer_id)
    body = (
        "<!DOCTYPE html><html lang='en'>"
        f"{page_head('Operations Dashboard', css=_OPS_CSS)}"
        "<body>"
        "<a href='/ui/report-runs'>&larr; Report Runs</a>"
        "<h1>Operations Dashboard</h1>"
        f"<p>Authenticated as: <strong>{principal_esc}</strong></p>"
        "<p class='reviewer-session'>Using reviewer session: "
        f"<strong>{principal_esc}</strong> "
        "<a class='reviewer-session-link' href='/ui/auth/reviewer'>"
        "Manage reviewer session</a></p>"
        f"{report_table}"
        f"{connector_table}"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)


def _count_link(href: str, count: int) -> str:
    return f"<a href='{_html.escape(href, quote=True)}'>{count}</a>"


def _status_count_link(base_href: str, status: str, count: int) -> str:
    return _count_link(f"{base_href}?status={status}", count)


def _render_health_table(
    label: str,
    health_resp: JobQueueHealthResponse,
    base_href: str,
) -> str:
    queued_age = _format_age(health_resp.oldest_queued_age_seconds)
    running_age = _format_age(health_resp.oldest_running_age_seconds)
    return (
        f"<h2>{_html.escape(label)}</h2>"
        "<div class='ops-table-wrap'>"
        "<table>"
        "<thead><tr>"
        "<th>Total</th><th>Queued</th><th>Running</th>"
        "<th>Succeeded</th><th>Failed</th><th>Cancelled</th>"
        "<th>Needs Review</th><th>Oldest Queued Age</th>"
        "<th>Oldest Running Age</th><th>Stale Running</th>"
        "</tr></thead>"
        "<tbody><tr>"
        f"<td>{_count_link(base_href, health_resp.total)}</td>"
        f"<td>{_status_count_link(base_href, 'queued', health_resp.queued)}</td>"
        f"<td>{_status_count_link(base_href, 'running', health_resp.running)}</td>"
        f"<td>{_status_count_link(base_href, 'succeeded', health_resp.succeeded)}</td>"
        f"<td>{_status_count_link(base_href, 'failed', health_resp.failed)}</td>"
        f"<td>{_status_count_link(base_href, 'cancelled', health_resp.cancelled)}</td>"
        f"<td>{_status_count_link(base_href, 'needs_review', health_resp.needs_review)}</td>"
        f"<td>{_html.escape(queued_age)}</td>"
        f"<td>{_oldest_running_link(base_href, health_resp, running_age)}</td>"
        f"<td>{_stale_running_link(base_href, health_resp.stale_running)}</td>"
        "</tr></tbody>"
        "</table>"
        "</div>"
    )


def _format_age(age_seconds: float | None) -> str:
    return f"{age_seconds:.1f}s" if age_seconds is not None else "n/a"


def _oldest_running_link(
    base_href: str,
    health_resp: JobQueueHealthResponse,
    running_age: str,
) -> str:
    job_id = health_resp.oldest_running_job_id
    if job_id is None:
        return _html.escape(running_age)
    return (
        f"<a href='{_html.escape(f'{base_href}/{job_id}', quote=True)}'>"
        f"{_html.escape(running_age)}</a>"
    )


def _stale_running_link(base_href: str, stale_count: int) -> str:
    return _count_link(f"{base_href}?status=running&stale=true", stale_count)


@router.get("", response_class=HTMLResponse)
def ui_operations_get(request: Request, services: ServicesDep) -> HTMLResponse:
    reviewer_id = _reviewer_has_operations_scope(request, services)
    if reviewer_id is not None:
        return _dashboard_response(reviewer_id=reviewer_id, services=services)

    csrf_field = csrf_form_field(request)
    body = (
        "<!DOCTYPE html><html lang='en'>"
        f"{page_head('Operations Dashboard', css=_OPS_CSS)}"
        "<body>"
        "<a href='/ui/report-runs'>&larr; Report Runs</a>"
        "<h1>Operations Dashboard</h1>"
        "<p>Use a reviewer session or credentials with <code>operations:read</code>"
        " scope to view queue health.</p>"
        f"{_credential_form(request, services, csrf_field=csrf_field)}"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)


@router.post("", response_class=HTMLResponse)
def ui_operations_post(
    request: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    csrf_error = require_ui_csrf(
        request,
        csrf_token,
        back_url="/ui/operations",
        css=_OPS_CSS,
    )
    if csrf_error is not None:
        return csrf_error
    try:
        auth_result = require_ui_reviewer(
            request,
            services,
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
            required_scope=REVIEWER_SCOPE_OPERATIONS_READ,
        )
    except HTTPException as exc:
        return error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            "/ui/operations",
            exc.status_code,
            css=_OPS_CSS,
        )
    principal = auth_result.principal
    response = _dashboard_response(
        reviewer_id=principal.reviewer_id,
        services=services,
    )
    attach_ui_reviewer_session_cookie(response, request, services, auth_result)
    return response


__all__ = ["router"]
