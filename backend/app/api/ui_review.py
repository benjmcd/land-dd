from __future__ import annotations

import html as _html
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from app.api.dependencies import ApiServices, get_services
from app.api.reports import schedule_report_background
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_CONNECTOR_REVIEW,
    REVIEWER_SCOPE_REPORT_RUN,
    require_reviewer_scope,
)
from app.api.ui_shared import build_css, reviewer_credential_fields
from app.api.ui_shared import error_page as _shared_error_page
from app.domain.enums import IntentCode, JobStatus

router = APIRouter(prefix="/ui/connector-review-queue", tags=["ui"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]

_REVIEW_CSS = build_css(
    ".action-form { border: 1px solid #dee2e6; border-radius: 4px; padding: 1rem;"
    " margin: 0.5rem 0; }\n"
    ".action-form h3 { margin: 0 0 0.5rem 0; font-size: 1rem; }\n"
    ".action-form label { display: block; margin-bottom: 0.4rem; font-size: 0.9rem; }\n"
    ".action-form input { display: block; width: 100%; padding: 0.3rem;"
    " font-size: 0.9rem; margin-bottom: 0.4rem; box-sizing: border-box; }\n"
    ".action-form textarea { display: block; width: 100%; padding: 0.3rem;"
    " font-size: 0.9rem; height: 60px; box-sizing: border-box; }\n"
    ".action-form button { padding: 0.4rem 1rem; font-size: 0.9rem; cursor: pointer;"
    " border: none; border-radius: 3px; }\n"
    ".btn-approve { background: #28a745; color: white; }\n"
    ".btn-reject { background: #dc3545; color: white; }\n"
    ".btn-requeue { background: #007bff; color: white; }\n"
    ".btn-cancel { background: #6c757d; color: white; }\n"
    ".btn-resume { background: #17a2b8; color: white; }\n"
    ".issue { border-left: 3px solid #ffc107; padding: 0.3rem 0.5rem;"
    " margin: 0.3rem 0; background: #fff3cd; font-size: 0.9rem; }\n"
    ".issue.blocking { border-color: #dc3545; background: #f8d7da; }\n"
    ".filter-bar { display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem; }\n"
    ".filter-bar select, .filter-bar input { padding: 0.3rem; font-size: 0.9rem; }\n"
    ".filter-bar button { padding: 0.3rem 0.75rem; font-size: 0.9rem; cursor: pointer; }\n"
    ".pagination { margin-top: 1rem; display: flex; gap: 1rem; }\n",
)

_STATUS_OPTIONS = [s.value for s in JobStatus]
_INTENT_OPTIONS = [
    ("rural_land_purchase", "Rural Land Purchase"),
    ("homestead_feasibility", "Homestead Feasibility"),
]

_CONNECTOR_STATUS_COLORS: dict[str, str] = {
    "queued": "#6c757d",
    "running": "#007bff",
    "succeeded": "#28a745",
    "failed": "#dc3545",
    "cancelled": "#6c757d",
    "needs_review": "#ffc107",
}


def _error_page(title: str, message: str, back_url: str, status_code: int) -> HTMLResponse:
    return _shared_error_page(title, message, back_url, status_code, css=_REVIEW_CSS)


@router.get("", response_class=HTMLResponse)
def ui_connector_review_queue_list(
    services: ServicesDep,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> str:
    # Validate status to prevent a DB CAST error on invalid enum values
    status_filter: str | None = None
    if status:
        try:
            status_filter = JobStatus(status).value
        except ValueError:
            status_filter = None

    items = services.connector_review_queue.list_connector_runs(
        workspace_id=None,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    status_option_tags = "<option value=''>All statuses</option>\n"
    for s in _STATUS_OPTIONS:
        selected = " selected" if s == status else ""
        s_esc = _html.escape(s)
        status_option_tags += f"<option value='{s_esc}'{selected}>{s_esc}</option>\n"

    rows = ""
    for item in items:
        status_color = _CONNECTOR_STATUS_COLORS.get(item.status.value, "#333")
        connector_name = _html.escape(str(item.payload.get("connector_name", "")))
        created_str = _html.escape(str(item.created_at)[:19])
        rows += (
            "<tr>"
            f"<td><a href='/ui/connector-review-queue/{item.ingest_run_id}'>"
            f"{str(item.ingest_run_id)[:8]}…</a></td>"
            f"<td>{connector_name}</td>"
            f"<td style='color:{status_color}'>{_html.escape(item.status.value)}</td>"
            f"<td>{item.attempts}</td>"
            f"<td>{created_str}</td>"
            "</tr>\n"
        )
    if not rows:
        rows = '<tr><td colspan="5" style="color:#666">No connector review items.</td></tr>'

    # Pagination controls
    prev_offset = max(0, offset - limit)
    next_offset = offset + limit
    has_prev = offset > 0
    has_next = len(items) == limit

    status_param = f"&status={_html.escape(status_filter)}" if status_filter else ""
    prev_link = f"?limit={limit}&offset={prev_offset}{status_param}"
    next_link = f"?limit={limit}&offset={next_offset}{status_param}"

    pagination = "<div class='pagination'>"
    if has_prev:
        pagination += f"<a href='{prev_link}'>&larr; Previous</a>"
    if has_next:
        pagination += f"<a href='{next_link}'>Next &rarr;</a>"
    pagination += "</div>"

    return (
        "<!DOCTYPE html><html lang='en'>"
        "<head><meta charset='UTF-8'>"
        "<title>Connector Review Queue</title>"
        f"<style>{_REVIEW_CSS}</style>"
        "</head><body>"
        "<a href='/ui/'>&larr; Home</a>"
        "<h1>Connector Review Queue</h1>"
        "<form method='get' class='filter-bar'>"
        "<label>Status: <select name='status'>"
        f"{status_option_tags}"
        "</select></label>"
        f"<input type='hidden' name='limit' value='{limit}'>"
        "<button type='submit'>Filter</button>"
        "</form>"
        "<table>"
        "<thead><tr>"
        "<th>Ingest Run ID</th><th>Connector</th><th>Status</th>"
        "<th>Attempts</th><th>Created</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
        f"{pagination}"
        "</body></html>"
    )


@router.get("/{ingest_run_id}", response_class=HTMLResponse)
def ui_connector_review_detail(
    ingest_run_id: UUID,
    services: ServicesDep,
) -> HTMLResponse:
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return _error_page(
            "Not Found",
            f"Connector review queue item not found: {ingest_run_id}",
            "/ui/connector-review-queue",
            404,
        )

    # Payload summary
    payload = item.payload
    connector_name = _html.escape(str(payload.get("connector_name", "")))
    area_id = _html.escape(str(payload.get("area_id", "")))
    retrieval_status = _html.escape(str(payload.get("retrieval_status", "")))
    review_required = _html.escape(str(payload.get("review_required", "")))
    disposition = _html.escape(str(payload.get("disposition", "")))
    signal_codes = payload.get("signal_codes") or []
    quality = payload.get("quality") or {}

    # Quality issues
    issues_html = ""
    issues_list = quality.get("issues") or [] if isinstance(quality, dict) else []
    for issue in issues_list:
        if not isinstance(issue, dict):
            continue
        blocking_class = " blocking" if issue.get("blocking") else ""
        code = _html.escape(str(issue.get("code", "")))
        message = _html.escape(str(issue.get("message", "")))
        blocking_label = " [BLOCKING]" if issue.get("blocking") else ""
        issues_html += (
            f"<div class='issue{blocking_class}'>{code}: {message}{blocking_label}</div>\n"
        )
    if not issues_html:
        issues_html = "<p style='color:#666'>No quality issues recorded.</p>"

    # Metadata
    status_color = _CONNECTOR_STATUS_COLORS.get(item.status.value, "#333")

    locked_by = _html.escape(str(item.locked_by or ""))
    locked_at = _html.escape(str(item.locked_at or ""))
    started_at = _html.escape(str(item.started_at or ""))
    finished_at = _html.escape(str(item.finished_at or ""))
    last_error = _html.escape(str(item.last_error or ""))

    signals_str = _html.escape(", ".join(str(s) for s in signal_codes))

    # Action forms
    base_action_url = f"/ui/connector-review-queue/{ingest_run_id}"

    approve_form = (
        "<div class='action-form'>"
        "<h3>Approve for QA</h3>"
        f"<form method='post' action='{base_action_url}/approve'>"
        f"{reviewer_credential_fields()}"
        "<label>Reason (optional):"
        " <textarea name='reason'></textarea></label>"
        "<button type='submit' class='btn-approve'>Approve</button>"
        "</form></div>"
    )

    reject_form = (
        "<div class='action-form'>"
        "<h3>Request Fixture Fix (Reject)</h3>"
        f"<form method='post' action='{base_action_url}/reject'>"
        f"{reviewer_credential_fields()}"
        "<label>Reason (required):"
        " <textarea name='reason' required></textarea></label>"
        "<button type='submit' class='btn-reject'>Request Fix</button>"
        "</form></div>"
    )

    requeue_form = (
        "<div class='action-form'>"
        "<h3>Requeue After Fix</h3>"
        f"<form method='post' action='{base_action_url}/requeue'>"
        f"{reviewer_credential_fields()}"
        "<label>Reason (required):"
        " <textarea name='reason' required></textarea></label>"
        "<button type='submit' class='btn-requeue'>Requeue</button>"
        "</form></div>"
    )

    cancel_form = (
        "<div class='action-form'>"
        "<h3>Cancel Review</h3>"
        f"<form method='post' action='{base_action_url}/cancel'>"
        f"{reviewer_credential_fields()}"
        "<label>Reason (required):"
        " <textarea name='reason' required></textarea></label>"
        "<button type='submit' class='btn-cancel'>Cancel</button>"
        "</form></div>"
    )

    # Resume report run form — shown for approved/succeeded items
    resume_form = ""
    if item.status == JobStatus.SUCCEEDED:
        intent_options = "\n".join(
            f"<option value='{val}'>{label}</option>"
            for val, label in _INTENT_OPTIONS
        )
        resume_form = (
            "<h2>Resume Report Run</h2>"
            "<p>This connector run has been approved. You can now create a report run.</p>"
            "<div class='action-form'>"
            "<h3>Create Report Run</h3>"
            f"<form method='post' action='{base_action_url}/resume-report'>"
            f"{reviewer_credential_fields()}"
            "<label>Intent:"
            f" <select name='intent_code'>{intent_options}</select></label>"
            "<button type='submit' class='btn-resume'>Resume Report</button>"
            "</form></div>"
        )

    body = (
        "<!DOCTYPE html><html lang='en'>"
        "<head><meta charset='UTF-8'>"
        f"<title>Connector Review: {ingest_run_id}</title>"
        f"<style>{_REVIEW_CSS}</style>"
        "</head><body>"
        "<a href='/ui/connector-review-queue'>&larr; Queue List</a>"
        f"<h1>Connector Review Item</h1>"
        "<div class='meta'>"
        f"<div>Ingest Run ID: {_html.escape(str(ingest_run_id))}</div>"
        f"<div>Connector: {connector_name}</div>"
        f"<div>Status: <span style='color:{status_color}'>"
        f"{_html.escape(item.status.value)}</span></div>"
        f"<div>Attempts: {item.attempts} / {item.max_attempts}</div>"
        f"<div>Area ID: {area_id}</div>"
        f"<div>Retrieval Status: {retrieval_status}</div>"
        f"<div>Review Required: {review_required}</div>"
        f"<div>Disposition: {disposition}</div>"
        f"<div>Signal Codes: {signals_str}</div>"
        f"<div>Locked By: {locked_by}</div>"
        f"<div>Locked At: {locked_at}</div>"
        f"<div>Started At: {started_at}</div>"
        f"<div>Finished At: {finished_at}</div>"
        f"<div>Last Error: {last_error}</div>"
        "</div>"
        "<h2>Quality Issues</h2>"
        f"{issues_html}"
        "<h2>Actions</h2>"
        f"{approve_form}"
        f"{reject_form}"
        f"{requeue_form}"
        f"{cancel_form}"
        f"{resume_form}"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)


@router.post("/{ingest_run_id}/approve", response_class=HTMLResponse)
def ui_connector_approve(
    ingest_run_id: UUID,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    reason: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    detail_url = f"/ui/connector-review-queue/{ingest_run_id}"
    try:
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
        require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_REVIEW)
    except HTTPException as exc:
        return _error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            detail_url,
            exc.status_code,
        )
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return _error_page("Not Found", f"Queue item not found: {ingest_run_id}", detail_url, 404)
    try:
        services.connector_review_queue.approve_for_connector_qa(
            item.job_id,
            reviewer_id=principal.reviewer_id,
            reason=reason or None,
        )
    except ValueError as exc:
        return _error_page("Action Failed", str(exc), detail_url, 409)
    return HTMLResponse(
        content=(
            "<!DOCTYPE html><html><head><title>Approved</title>"
            f"<meta http-equiv='refresh' content='1;url={detail_url}'>"
            "</head><body><h1>Approved</h1>"
            f"<p><a href='{detail_url}'>View item</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )


@router.post("/{ingest_run_id}/reject", response_class=HTMLResponse)
def ui_connector_reject(
    ingest_run_id: UUID,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    reason: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    detail_url = f"/ui/connector-review-queue/{ingest_run_id}"
    try:
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
        require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_REVIEW)
    except HTTPException as exc:
        return _error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            detail_url,
            exc.status_code,
        )
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return _error_page("Not Found", f"Queue item not found: {ingest_run_id}", detail_url, 404)
    if not reason or not reason.strip():
        return _error_page("Validation Error", "Reason is required for reject.", detail_url, 422)
    try:
        services.connector_review_queue.request_fixture_fix(
            item.job_id,
            reviewer_id=principal.reviewer_id,
            reason=reason.strip(),
        )
    except ValueError as exc:
        return _error_page("Action Failed", str(exc), detail_url, 409)
    return HTMLResponse(
        content=(
            "<!DOCTYPE html><html><head><title>Fix Requested</title>"
            f"<meta http-equiv='refresh' content='1;url={detail_url}'>"
            "</head><body><h1>Fix Requested</h1>"
            f"<p><a href='{detail_url}'>View item</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )


@router.post("/{ingest_run_id}/requeue", response_class=HTMLResponse)
def ui_connector_requeue(
    ingest_run_id: UUID,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    reason: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    detail_url = f"/ui/connector-review-queue/{ingest_run_id}"
    try:
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
        require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_REVIEW)
    except HTTPException as exc:
        return _error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            detail_url,
            exc.status_code,
        )
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return _error_page("Not Found", f"Queue item not found: {ingest_run_id}", detail_url, 404)
    if not reason or not reason.strip():
        return _error_page("Validation Error", "Reason is required for requeue.", detail_url, 422)
    try:
        services.connector_review_queue.requeue_failed(
            item.job_id,
            reason=reason.strip(),
            reviewer_id=principal.reviewer_id,
        )
    except ValueError as exc:
        return _error_page("Action Failed", str(exc), detail_url, 409)
    return HTMLResponse(
        content=(
            "<!DOCTYPE html><html><head><title>Requeued</title>"
            f"<meta http-equiv='refresh' content='1;url={detail_url}'>"
            "</head><body><h1>Requeued</h1>"
            f"<p><a href='{detail_url}'>View item</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )


@router.post("/{ingest_run_id}/cancel", response_class=HTMLResponse)
def ui_connector_cancel(
    ingest_run_id: UUID,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    reason: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    detail_url = f"/ui/connector-review-queue/{ingest_run_id}"
    try:
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
        require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_REVIEW)
    except HTTPException as exc:
        return _error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            detail_url,
            exc.status_code,
        )
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return _error_page("Not Found", f"Queue item not found: {ingest_run_id}", detail_url, 404)
    if not reason or not reason.strip():
        return _error_page("Validation Error", "Reason is required for cancel.", detail_url, 422)
    try:
        services.connector_review_queue.cancel(
            item.job_id,
            reason=reason.strip(),
            reviewer_id=principal.reviewer_id,
        )
    except ValueError as exc:
        return _error_page("Action Failed", str(exc), detail_url, 409)
    return HTMLResponse(
        content=(
            "<!DOCTYPE html><html><head><title>Cancelled</title>"
            f"<meta http-equiv='refresh' content='1;url={detail_url}'>"
            "</head><body><h1>Cancelled</h1>"
            f"<p><a href='{detail_url}'>View item</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )


@router.post("/{ingest_run_id}/resume-report", response_class=HTMLResponse)
def ui_connector_resume_report(
    ingest_run_id: UUID,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    intent_code: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    detail_url = f"/ui/connector-review-queue/{ingest_run_id}"
    try:
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
        require_reviewer_scope(principal, REVIEWER_SCOPE_REPORT_RUN)
    except HTTPException as exc:
        return _error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            detail_url,
            exc.status_code,
        )
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return _error_page("Not Found", f"Queue item not found: {ingest_run_id}", detail_url, 404)
    if item.status != JobStatus.SUCCEEDED:
        return _error_page(
            "Not Approved",
            "Connector review item must be approved (succeeded) before resuming a report run.",
            detail_url,
            409,
        )
    try:
        resolved_intent = (
            IntentCode(intent_code) if intent_code else IntentCode.RURAL_LAND_PURCHASE
        )
    except ValueError:
        return _error_page(
            "Validation Error", f"Unknown intent code: {intent_code}", detail_url, 422
        )
    area_id_raw = item.payload.get("area_id")
    if not isinstance(area_id_raw, str) or not area_id_raw.strip():
        return _error_page(
            "Configuration Error", "Queue item missing area_id.", detail_url, 409
        )
    try:
        area_id = UUID(area_id_raw)
    except ValueError:
        return _error_page(
            "Configuration Error", "Queue item has invalid area_id.", detail_url, 409
        )
    area = services.area_service.get(area_id)
    if area is None:
        return _error_page("Not Found", f"Area {area_id} is not registered.", detail_url, 409)
    job = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=resolved_intent,
    )
    schedule_report_background(
        background_tasks=background_tasks,
        request_context=request_context,
        services=services,
        report_run_id=job.report_run_id,
        area_id=area_id,
        intent_code=resolved_intent,
    )
    report_url = f"/ui/report-runs/{job.report_run_id}"
    return HTMLResponse(
        content=(
            "<!DOCTYPE html><html><head><title>Report Queued</title>"
            f"<meta http-equiv='refresh' content='1;url={report_url}'>"
            "</head><body><h1>Report Run Queued</h1>"
            f"<p>Report run ID: {_html.escape(str(job.report_run_id))}</p>"
            f"<p><a href='{report_url}'>View Report Run</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )
