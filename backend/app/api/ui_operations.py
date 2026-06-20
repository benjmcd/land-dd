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
    ui_auth_routes_enabled,
    ui_reviewer_principal_from_cookie,
)
from app.operations.recovery_preview import (
    JobRecoveryPreviewItem,
    build_recovery_preview,
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
    ".ops-nav { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; }\n"
    ".empty-state { color: #495057; margin-bottom: 1.25rem; }\n",
)


def _credential_form(
    request: Request,
    services: ApiServices,
    csrf_field: str = "",
    *,
    action: str = "/ui/operations",
    button_label: str = "View Dashboard",
) -> str:
    reviewer_fields = reviewer_credential_fields(
        request,
        services,
        required_scope=REVIEWER_SCOPE_OPERATIONS_READ,
    )
    return (
        f"<form method='post' action='{_html.escape(action, quote=True)}' class='auth-form'>"
        f"{csrf_field}"
        f"{reviewer_fields}"
        f"<button type='submit'>{_html.escape(button_label)}</button>"
        "</form>"
    )


def _reviewer_has_operations_scope(request: Request, services: ApiServices) -> str | None:
    principal = ui_reviewer_principal_from_cookie(request, services)
    if principal is None or REVIEWER_SCOPE_OPERATIONS_READ not in principal.scopes:
        return None
    return principal.reviewer_id


def _dashboard_response(
    *,
    request: Request,
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
        "<nav class='ops-nav'>"
        "<a href='/ui/report-runs'>&larr; Report Runs</a>"
        "<a href='/ui/operations/recovery-preview'>Recovery Preview</a>"
        "</nav>"
        "<h1>Operations Dashboard</h1>"
        f"<p>Authenticated as: <strong>{principal_esc}</strong></p>"
        "<p class='reviewer-session'>Using reviewer session: "
        f"<strong>{principal_esc}</strong> "
        f"{_reviewer_session_link(request)}</p>"
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


def _recovery_preview_response(
    *,
    request: Request,
    reviewer_id: str,
    services: ApiServices,
) -> HTMLResponse:
    preview = build_recovery_preview(
        report_jobs=services.async_report_jobs,
        live_connector_jobs=services.live_connector_jobs,
    )
    report_health = job_queue_health_response(services.async_report_jobs.health())
    connector_health = job_queue_health_response(services.live_connector_jobs.health())
    report_section = _render_recovery_section(
        "Report Jobs",
        report_health,
        preview.report_jobs,
        candidate_limit_per_state=preview.candidate_limit_per_state,
    )
    connector_section = _render_recovery_section(
        "Live Connector Jobs",
        connector_health,
        preview.live_connector_jobs,
        candidate_limit_per_state=preview.candidate_limit_per_state,
    )

    principal_esc = _html.escape(reviewer_id)
    body = (
        "<!DOCTYPE html><html lang='en'>"
        f"{page_head('Recovery Preview', css=_OPS_CSS)}"
        "<body>"
        "<nav class='ops-nav'>"
        "<a href='/ui/operations'>&larr; Operations Dashboard</a>"
        "<a href='/ui/report-runs'>Report Runs</a>"
        "<a href='/ui/live-connector-jobs'>Live Connector Jobs</a>"
        "</nav>"
        "<h1>Recovery Preview</h1>"
        f"<p>Authenticated as: <strong>{principal_esc}</strong></p>"
        "<p class='reviewer-session'>Using reviewer session: "
        f"<strong>{principal_esc}</strong> "
        f"{_reviewer_session_link(request)}</p>"
        f"<p>Generated at: <strong>{_html.escape(str(preview.generated_at))}</strong></p>"
        "<p>Stale running threshold: "
        f"<strong>{preview.stale_running_threshold_seconds}s</strong></p>"
        f"{report_section}"
        f"{connector_section}"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)


def _reviewer_session_link(request: Request) -> str:
    if not ui_auth_routes_enabled(request):
        return ""
    return (
        "<a class='reviewer-session-link' href='/ui/auth/reviewer'>"
        "Manage reviewer session</a>"
    )


def _render_recovery_section(
    label: str,
    health_resp: JobQueueHealthResponse,
    candidates: tuple[JobRecoveryPreviewItem, ...],
    *,
    candidate_limit_per_state: int,
) -> str:
    failed_candidate_count = sum(1 for candidate in candidates if not candidate.stale_running)
    stale_candidate_count = sum(1 for candidate in candidates if candidate.stale_running)
    failed_note = _truncation_note(
        "failed",
        health_resp.failed,
        failed_candidate_count,
        candidate_limit_per_state,
    )
    stale_note = _truncation_note(
        "stale-running",
        health_resp.stale_running,
        stale_candidate_count,
        candidate_limit_per_state,
    )
    summary = (
        f"<h2>{_html.escape(label)}</h2>"
        "<p class='empty-state'>Showing up to "
        f"{candidate_limit_per_state} failed and {candidate_limit_per_state} "
        "stale-running candidates per queue.</p>"
        "<div class='ops-table-wrap'>"
        "<table>"
        "<thead><tr>"
        "<th>Failed</th><th>Stale Running</th><th>Queued</th>"
        "<th>Oldest Queued Age</th><th>Candidates</th>"
        "</tr></thead>"
        "<tbody><tr>"
        f"<td>{health_resp.failed}</td>"
        f"<td>{health_resp.stale_running}</td>"
        f"<td>{health_resp.queued}</td>"
        f"<td>{_html.escape(_format_age(health_resp.oldest_queued_age_seconds))}</td>"
        f"<td>{len(candidates)}</td>"
        "</tr></tbody>"
        "</table>"
        "</div>"
        f"{failed_note}"
        f"{stale_note}"
    )
    return summary + _render_candidate_table(candidates)


def _render_candidate_table(candidates: tuple[JobRecoveryPreviewItem, ...]) -> str:
    if not candidates:
        return "<p class='empty-state'>No recovery candidates.</p>"
    rows = "".join(_render_candidate_row(candidate) for candidate in candidates)
    return (
        "<div class='ops-table-wrap'>"
        "<table>"
        "<thead><tr>"
        "<th>Job</th><th>Status</th><th>Reason</th><th>Age</th>"
        "<th>Context</th><th>Recommended Next Step</th><th>Error</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
        "</div>"
    )


def _render_candidate_row(candidate: JobRecoveryPreviewItem) -> str:
    detail_path = _html.escape(candidate.detail_ui_path, quote=True)
    job_id = _html.escape(str(candidate.job_id))
    reason_code = "stale_running" if candidate.stale_running else "failed"
    return (
        "<tr>"
        f"<td><a href='{detail_path}'>{job_id}</a></td>"
        f"<td>{_html.escape(candidate.status.value)}</td>"
        f"<td>{reason_code}</td>"
        f"<td>{_html.escape(_format_age(candidate.age_seconds))}</td>"
        f"<td>{_candidate_context(candidate)}</td>"
        f"<td>{_html.escape(candidate.reason)}</td>"
        f"<td>{_html.escape(candidate.error_message or 'n/a')}</td>"
        "</tr>"
    )


def _candidate_context(candidate: JobRecoveryPreviewItem) -> str:
    if candidate.intent_code is not None:
        return _html.escape(candidate.intent_code)
    connector = candidate.connector_name or "unknown connector"
    source = candidate.source_registry_id or "unknown source"
    attempts = "n/a"
    if candidate.attempts is not None and candidate.max_attempts is not None:
        attempts = f"{candidate.attempts}/{candidate.max_attempts}"
    return _html.escape(f"{connector} ({source}), attempts {attempts}")


def _truncation_note(
    label: str,
    total_count: int,
    candidate_count: int,
    candidate_limit_per_state: int,
) -> str:
    if total_count <= candidate_count:
        return ""
    return (
        "<p class='empty-state'>"
        f"{_html.escape(label)} candidates truncated: showing {candidate_count} "
        f"of {total_count} (limit {candidate_limit_per_state})."
        "</p>"
    )


@router.get("", response_class=HTMLResponse)
def ui_operations_get(request: Request, services: ServicesDep) -> HTMLResponse:
    reviewer_id = _reviewer_has_operations_scope(request, services)
    if reviewer_id is not None:
        return _dashboard_response(
            request=request,
            reviewer_id=reviewer_id,
            services=services,
        )

    csrf_field = csrf_form_field(request)
    body = (
        "<!DOCTYPE html><html lang='en'>"
        f"{page_head('Operations Dashboard', css=_OPS_CSS)}"
        "<body>"
        "<nav class='ops-nav'>"
        "<a href='/ui/report-runs'>&larr; Report Runs</a>"
        "<a href='/ui/operations/recovery-preview'>Recovery Preview</a>"
        "</nav>"
        "<h1>Operations Dashboard</h1>"
        "<p>Use a reviewer session or credentials with <code>operations:read</code>"
        " scope to view queue health.</p>"
        f"{_credential_form(request, services, csrf_field=csrf_field)}"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)


@router.get("/recovery-preview", response_class=HTMLResponse)
def ui_operations_recovery_preview_get(
    request: Request,
    services: ServicesDep,
) -> HTMLResponse:
    reviewer_id = _reviewer_has_operations_scope(request, services)
    if reviewer_id is not None:
        return _recovery_preview_response(
            request=request,
            reviewer_id=reviewer_id,
            services=services,
        )

    csrf_field = csrf_form_field(request)
    credential_form = _credential_form(
        request,
        services,
        csrf_field=csrf_field,
        action="/ui/operations/recovery-preview",
        button_label="View Recovery Preview",
    )
    body = (
        "<!DOCTYPE html><html lang='en'>"
        f"{page_head('Recovery Preview', css=_OPS_CSS)}"
        "<body>"
        "<nav class='ops-nav'>"
        "<a href='/ui/operations'>&larr; Operations Dashboard</a>"
        "<a href='/ui/report-runs'>Report Runs</a>"
        "</nav>"
        "<h1>Recovery Preview</h1>"
        "<p>Use a reviewer session or credentials with <code>operations:read</code>"
        " scope to view recovery candidates.</p>"
        f"{credential_form}"
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
        request=request,
        reviewer_id=principal.reviewer_id,
        services=services,
    )
    attach_ui_reviewer_session_cookie(response, request, services, auth_result)
    return response


@router.post("/recovery-preview", response_class=HTMLResponse)
def ui_operations_recovery_preview_post(
    request: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    csrf_error = require_ui_csrf(
        request,
        csrf_token,
        back_url="/ui/operations/recovery-preview",
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
            "/ui/operations/recovery-preview",
            exc.status_code,
            css=_OPS_CSS,
        )
    principal = auth_result.principal
    response = _recovery_preview_response(
        request=request,
        reviewer_id=principal.reviewer_id,
        services=services,
    )
    attach_ui_reviewer_session_cookie(response, request, services, auth_result)
    return response


__all__ = ["router"]
