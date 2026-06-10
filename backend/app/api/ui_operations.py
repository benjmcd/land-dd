from __future__ import annotations

import html as _html
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse

from app.api.dependencies import ApiServices, get_services
from app.api.operations import _job_queue_health_response
from app.api.reviewer_auth import REVIEWER_SCOPE_OPERATIONS_READ, require_reviewer_scope

router = APIRouter(prefix="/ui/operations", tags=["ui"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]

_OPS_CSS = (
    "body { font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto;"
    " padding: 0 1rem; }\n"
    "h1 { color: #2c3e50; } h2 { color: #34495e; border-bottom: 1px solid #eee; }\n"
    "table { border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; }\n"
    "th, td { text-align: left; padding: 0.5rem 1rem; border-bottom: 1px solid #dee2e6; }\n"
    "th { background: #f8f9fa; }\n"
    "a { color: #2c3e50; }\n"
    ".auth-form { display: flex; flex-direction: column; gap: 0.75rem; max-width: 320px;"
    " margin-top: 1rem; }\n"
    ".auth-form label { font-size: 0.95rem; }\n"
    ".auth-form input { display: block; width: 100%; padding: 0.4rem; font-size: 1rem; }\n"
    ".auth-form button { background: #2c3e50; color: white; border: none; padding: 0.5rem 1rem;"
    " font-size: 1rem; cursor: pointer; border-radius: 4px; }\n"
    ".error-page { background: #f8d7da; border: 1px solid #f5c6cb; padding: 1rem;"
    " border-radius: 4px; }\n"
)


def _error_page(title: str, message: str, status_code: int) -> HTMLResponse:
    body = (
        "<!DOCTYPE html><html lang='en'>"
        "<head><meta charset='UTF-8'>"
        f"<title>{_html.escape(title)}</title>"
        f"<style>{_OPS_CSS}</style>"
        "</head><body>"
        f"<div class='error-page'><h1>{_html.escape(title)}</h1>"
        f"<p>{_html.escape(message)}</p>"
        "<a href='/ui/operations'>Back</a>"
        "</div></body></html>"
    )
    return HTMLResponse(content=body, status_code=status_code)


def _credential_form() -> str:
    return (
        "<form method='post' action='/ui/operations' class='auth-form'>"
        "<label>Reviewer ID:"
        " <input type='text' name='reviewer_id' required></label>"
        "<label>Reviewer token:"
        " <input type='password' name='reviewer_token' required></label>"
        "<button type='submit'>View Dashboard</button>"
        "</form>"
    )


def _render_health_table(label: str, health_resp: object) -> str:
    from app.api.operations import JobQueueHealthResponse

    if not isinstance(health_resp, JobQueueHealthResponse):
        return ""
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
