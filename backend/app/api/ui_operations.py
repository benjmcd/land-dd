from __future__ import annotations

import html as _html
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse

from app.api.dependencies import ApiServices, get_services
from app.api.operations import JobQueueHealthResponse, _job_queue_health_response
from app.api.reviewer_auth import REVIEWER_SCOPE_OPERATIONS_READ, require_reviewer_scope
from app.api.ui_shared import build_css, reviewer_credential_fields
from app.api.ui_shared import error_page as _shared_error_page

router = APIRouter(prefix="/ui/operations", tags=["ui"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]

_OPS_CSS = build_css(
    "table { margin-bottom: 1.5rem; }\n"
    ".auth-form { display: flex; flex-direction: column; gap: 0.75rem; max-width: 320px;"
    " margin-top: 1rem; }\n"
    ".auth-form label { font-size: 0.95rem; }\n"
    ".auth-form input { display: block; width: 100%; padding: 0.4rem; font-size: 1rem; }\n"
    ".auth-form button { background: #2c3e50; color: white; border: none; padding: 0.5rem 1rem;"
    " font-size: 1rem; cursor: pointer; border-radius: 4px; }\n",
)


def _error_page(title: str, message: str, status_code: int) -> HTMLResponse:
    return _shared_error_page(title, message, "/ui/operations", status_code, css=_OPS_CSS)


def _credential_form() -> str:
    return (
        "<form method='post' action='/ui/operations' class='auth-form'>"
        f"{reviewer_credential_fields()}"
        "<button type='submit'>View Dashboard</button>"
        "</form>"
    )


def _render_health_table(label: str, health_resp: JobQueueHealthResponse) -> str:
    age = (
        f"{health_resp.oldest_queued_age_seconds:.1f}s"
        if health_resp.oldest_queued_age_seconds is not None
        else "—"
    )
    return (
        f"<h2>{_html.escape(label)}</h2>"
        "<table>"
        "<thead><tr>"
        "<th>Total</th><th>Queued</th><th>Running</th>"
        "<th>Succeeded</th><th>Failed</th><th>Cancelled</th>"
        "<th>Needs Review</th><th>Oldest Queued Age</th>"
        "</tr></thead>"
        "<tbody><tr>"
        f"<td>{health_resp.total}</td>"
        f"<td>{health_resp.queued}</td>"
        f"<td>{health_resp.running}</td>"
        f"<td>{health_resp.succeeded}</td>"
        f"<td>{health_resp.failed}</td>"
        f"<td>{health_resp.cancelled}</td>"
        f"<td>{health_resp.needs_review}</td>"
        f"<td>{_html.escape(age)}</td>"
        "</tr></tbody>"
        "</table>"
    )


@router.get("", response_class=HTMLResponse)
def ui_operations_get() -> HTMLResponse:
    body = (
        "<!DOCTYPE html><html lang='en'>"
        "<head><meta charset='UTF-8'>"
        "<title>Operations Dashboard</title>"
        f"<style>{_OPS_CSS}</style>"
        "</head><body>"
        "<a href='/ui/report-runs'>&larr; Report Runs</a>"
        "<h1>Operations Dashboard</h1>"
        "<p>Enter reviewer credentials with <code>operations:read</code> scope to view"
        " queue health.</p>"
        f"{_credential_form()}"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)


@router.post("", response_class=HTMLResponse)
def ui_operations_post(
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    try:
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
        require_reviewer_scope(principal, REVIEWER_SCOPE_OPERATIONS_READ)
    except HTTPException as exc:
        return _error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            exc.status_code,
        )

    report_health = _job_queue_health_response(services.async_report_jobs.health())
    connector_health = _job_queue_health_response(services.live_connector_jobs.health())

    report_table = _render_health_table("Report Jobs", report_health)
    connector_table = _render_health_table("Live Connector Jobs", connector_health)

    principal_esc = _html.escape(principal.reviewer_id)
    body = (
        "<!DOCTYPE html><html lang='en'>"
        "<head><meta charset='UTF-8'>"
        "<title>Operations Dashboard</title>"
        f"<style>{_OPS_CSS}</style>"
        "</head><body>"
        "<a href='/ui/report-runs'>&larr; Report Runs</a>"
        "<h1>Operations Dashboard</h1>"
        f"<p>Authenticated as: <strong>{principal_esc}</strong></p>"
        f"{report_table}"
        f"{connector_table}"
        f"{_credential_form()}"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)


__all__ = ["router"]
