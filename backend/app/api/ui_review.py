from __future__ import annotations

import html as _html
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.api.dependencies import ApiServices, get_services
from app.api.reports import (
    raise_report_queue_backpressure_if_needed,
    schedule_report_background,
)
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_CONNECTOR_REVIEW,
    REVIEWER_SCOPE_REPORT_RUN,
)
from app.api.ui_shared import (
    attach_ui_reviewer_session_cookie,
    build_css,
    csrf_form_field,
    error_page,
    page_head,
    require_ui_csrf,
    require_ui_reviewer,
    reviewer_credential_fields,
)
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
    ".decision-context { border: 1px solid #cfd8dc; border-radius: 4px;"
    " padding: 1rem; margin: 1rem 0; background: #f8fbfc; }\n"
    ".decision-context h2 { margin-top: 0; }\n"
    ".decision-context h3 { margin: 1rem 0 0.4rem; font-size: 1rem; }\n"
    ".context-summary { margin: 0.25rem 0; max-width: 72rem; }\n"
    ".context-grid { display: grid; grid-template-columns: repeat(auto-fit,"
    " minmax(160px, 1fr)); gap: 0.5rem; margin: 0.75rem 0; }\n"
    ".context-card { border: 1px solid #e1e7ea; border-radius: 4px; padding: 0.55rem;"
    " background: #fff; overflow-wrap: anywhere; }\n"
    ".context-label { color: #566; font-size: 0.75rem; margin-bottom: 0.15rem; }\n"
    ".context-value { font-weight: 600; font-size: 0.92rem; }\n"
    ".signal-list { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.3rem 0; }\n"
    ".signal-chip { border: 1px solid #bcc7ce; border-radius: 999px; padding: 0.18rem 0.5rem;"
    " background: #fff; font-size: 0.82rem; overflow-wrap: anywhere; }\n"
    ".context-table { width: 100%; table-layout: fixed; border-collapse: collapse;"
    " margin: 0.4rem 0; }\n"
    ".context-table th, .context-table td { border: 1px solid #dee2e6;"
    " padding: 0.4rem; vertical-align: top; overflow-wrap: anywhere; }\n"
    ".context-table th { background: #eef3f5; text-align: left; }\n"
    ".context-table .mono { font-family: ui-monospace, Consolas, monospace;"
    " font-size: 0.82rem; }\n"
    ".evidence-list { display: grid; gap: 0.6rem; margin: 0.4rem 0; }\n"
    ".evidence-card { border: 1px solid #dee2e6; border-radius: 4px;"
    " background: #fff; padding: 0.65rem; }\n"
    ".evidence-card-head { display: flex; flex-wrap: wrap; gap: 0.4rem;"
    " align-items: center; margin-bottom: 0.45rem; }\n"
    ".evidence-pill { border: 1px solid #bcc7ce; border-radius: 999px;"
    " padding: 0.15rem 0.45rem; font-size: 0.8rem; background: #eef3f5; }\n"
    ".evidence-grid { display: grid; grid-template-columns: repeat(auto-fit,"
    " minmax(220px, 1fr)); gap: 0.5rem; margin: 0; }\n"
    ".evidence-field { margin: 0; min-width: 0; }\n"
    ".evidence-field dt { color: #566; font-size: 0.75rem; margin-bottom: 0.1rem; }\n"
    ".evidence-field dd { margin: 0; overflow-wrap: anywhere; }\n"
    ".evidence-field .mono { font-family: ui-monospace, Consolas, monospace;"
    " font-size: 0.82rem; }\n"
    ".muted { color: #666; }\n"
    ".task-list { margin: 0.3rem 0 0.4rem 1.2rem; padding: 0; }\n"
    ".task-list li { margin: 0.2rem 0; }\n"
    ".triage-summary { max-width: 32rem; font-size: 0.86rem; }\n"
    ".triage-line { margin: 0.12rem 0; overflow-wrap: anywhere; }\n"
    ".triage-signals { display: flex; flex-wrap: wrap; gap: 0.25rem;"
    " margin: 0.25rem 0; }\n"
    ".triage-chip { border: 1px solid #bcc7ce; border-radius: 999px;"
    " padding: 0.1rem 0.4rem; background: #fff; font-size: 0.78rem; }\n"
    ".triage-action { white-space: nowrap; }\n"
    ".review-queue-table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }\n"
    ".review-queue-table { min-width: 980px; }\n"
    ".review-queue-table th, .review-queue-table td { vertical-align: top; }\n"
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


_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "credential",
    "password",
    "secret",
    "token",
)


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _payload_list(value: object) -> list[object]:
    if isinstance(value, list | tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]


def _payload_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _render_value(value: object, *, max_length: int = 240) -> str:
    if value is None or value == "":
        raw = "None"
    elif isinstance(value, bool):
        raw = "true" if value else "false"
    elif isinstance(value, dict):
        parts = [
            f"{key}: {item}"
            for key, item in value.items()
            if not _is_sensitive_key(key)
        ]
        raw = ", ".join(parts) if parts else "None"
    elif isinstance(value, list | tuple | set):
        raw = ", ".join(str(item) for item in value) or "None"
    else:
        raw = str(value)
    if len(raw) > max_length:
        raw = f"{raw[: max_length - 3]}..."
    return _html.escape(raw)


def _context_card(label: str, value: object) -> str:
    return (
        "<div class='context-card'>"
        f"<div class='context-label'>{_html.escape(label)}</div>"
        f"<div class='context-value'>{_render_value(value)}</div>"
        "</div>"
    )


def _signal_chips(signal_codes: list[object]) -> str:
    if not signal_codes:
        return "<p class='muted'>No review signals recorded.</p>"
    chips = "".join(
        f"<span class='signal-chip'>{_render_value(code, max_length=96)}</span>"
        for code in signal_codes
    )
    return f"<div class='signal-list'>{chips}</div>"


def _task_list(tasks: list[object]) -> str:
    if not tasks:
        return "<p class='muted'>No human-review tasks recorded.</p>"
    rows = "".join(f"<li>{_render_value(task)}</li>" for task in tasks)
    return f"<ul class='task-list'>{rows}</ul>"


def _metrics_table(metrics: dict[str, object]) -> str:
    rows = ""
    for key in sorted(metrics):
        if _is_sensitive_key(key):
            continue
        rows += (
            "<tr>"
            f"<th>{_html.escape(key)}</th>"
            f"<td>{_render_value(metrics[key])}</td>"
            "</tr>"
        )
    if not rows:
        return "<p class='muted'>No safe metrics recorded.</p>"
    return f"<table class='context-table'>{rows}</table>"


def _evidence_table(
    created_evidence: list[object],
    skipped_evidence: list[object],
) -> str:
    cards = ""
    for outcome, records in (
        ("created", created_evidence),
        ("skipped", skipped_evidence),
    ):
        for record_value in records:
            record = _payload_dict(record_value)
            if not record:
                continue
            status = "source failure" if record.get("is_source_failure") else "evidence"
            cards += (
                "<div class='evidence-card'>"
                "<div class='evidence-card-head'>"
                f"<span class='evidence-pill'>{_html.escape(outcome)}</span>"
                f"<span class='evidence-pill'>{_html.escape(status)}</span>"
                "</div>"
                "<dl class='evidence-grid'>"
                "<div class='evidence-field'><dt>Evidence Code</dt>"
                f"<dd>{_render_value(record.get('evidence_code'), max_length=96)}</dd></div>"
                "<div class='evidence-field'><dt>Observation</dt>"
                f"<dd>{_render_value(record.get('observation'))}</dd></div>"
                "<div class='evidence-field'><dt>Caveat</dt>"
                f"<dd>{_render_value(record.get('caveat'))}</dd></div>"
                "<div class='evidence-field'><dt>Evidence ID</dt>"
                f"<dd class='mono'>"
                f"{_render_value(record.get('evidence_id'), max_length=96)}"
                "</dd></div>"
                "</dl>"
                "</div>"
            )
    if not cards:
        return "<p class='muted'>No evidence summaries captured in this queue item.</p>"
    return f"<div class='evidence-list'>{cards}</div>"


def _decision_context_html(payload: dict[str, Any]) -> str:
    quality = _payload_dict(payload.get("quality"))
    signal_codes = _payload_list(payload.get("signal_codes"))
    tasks = _payload_list(payload.get("tasks"))
    metrics = _payload_dict(payload.get("metrics"))
    created_evidence = _payload_list(payload.get("created_evidence"))
    skipped_evidence = _payload_list(payload.get("skipped_evidence"))
    cards = "".join(
        [
            _context_card("Connector", payload.get("connector_name")),
            _context_card("Retrieval Status", payload.get("retrieval_status")),
            _context_card("Disposition", payload.get("disposition")),
            _context_card("Review Required", payload.get("review_required")),
            _context_card("Rows", payload.get("row_count")),
            _context_card("Errors", payload.get("error_count")),
            _context_card("Warnings", payload.get("warning_count")),
            _context_card("Log URI", payload.get("log_uri")),
            _context_card("Evidence Created", payload.get("evidence_created_count")),
            _context_card("Evidence Skipped", payload.get("evidence_skipped_count")),
            _context_card(
                "Source Failures",
                (
                    f"{payload.get('source_failure_created_count', 0)} created, "
                    f"{payload.get('source_failure_skipped_count', 0)} skipped"
                ),
            ),
            _context_card("Quality Blocking", quality.get("blocking_issue_count")),
        ]
    )
    return (
        "<section class='decision-context'>"
        "<h2>Decision Context</h2>"
        f"<p class='context-summary'><strong>{_render_value(payload.get('title'))}</strong></p>"
        f"<p class='context-summary'>{_render_value(payload.get('summary'))}</p>"
        f"<div class='context-grid'>{cards}</div>"
        "<h3>Signals</h3>"
        f"{_signal_chips(signal_codes)}"
        "<h3>Human Review Tasks</h3>"
        f"{_task_list(tasks)}"
        "<h3>Evidence Summary</h3>"
        f"{_evidence_table(created_evidence, skipped_evidence)}"
        "<h3>Retrieval Metrics</h3>"
        f"{_metrics_table(metrics)}"
        "</section>"
    )


def _payload_count(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int | float):
        return int(value)
    return 0


def _triage_chip_list(values: list[object], *, limit: int = 3) -> str:
    if not values:
        return "<span class='muted'>No signals</span>"
    rendered = "".join(
        f"<span class='triage-chip'>{_render_value(value, max_length=64)}</span>"
        for value in values[:limit]
    )
    remaining = len(values) - limit
    if remaining > 0:
        rendered += f"<span class='triage-chip'>+{remaining}</span>"
    return rendered


def _triage_task_line(tasks: list[object]) -> str:
    if not tasks:
        return "Tasks: None"
    first_task = _render_value(tasks[0], max_length=120)
    remaining = len(tasks) - 1
    suffix = f" (+{remaining})" if remaining > 0 else ""
    return f"Task: {first_task}{suffix}"


def _triage_summary_html(payload: dict[str, Any]) -> str:
    quality = _payload_dict(payload.get("quality"))
    signal_codes = _payload_list(payload.get("signal_codes"))
    tasks = _payload_list(payload.get("tasks"))
    evidence_created = _payload_count(payload, "evidence_created_count")
    evidence_skipped = _payload_count(payload, "evidence_skipped_count")
    source_failure_created = _payload_count(payload, "source_failure_created_count")
    source_failure_skipped = _payload_count(payload, "source_failure_skipped_count")
    blocking_count = _render_value(quality.get("blocking_issue_count"), max_length=24)
    return (
        "<div class='triage-summary'>"
        "<div class='triage-line'>"
        f"Disposition: {_render_value(payload.get('disposition'), max_length=80)}"
        "</div>"
        f"<div class='triage-signals'>{_triage_chip_list(signal_codes)}</div>"
        f"<div class='triage-line'>{_triage_task_line(tasks)}</div>"
        f"<div class='triage-line'>Blocking: {blocking_count}</div>"
        "<div class='triage-line'>"
        f"Evidence: {evidence_created} created / {evidence_skipped} skipped"
        "</div>"
        "<div class='triage-line'>"
        "Source failures: "
        f"{source_failure_created} created / {source_failure_skipped} skipped"
        "</div>"
        "</div>"
    )


def _next_action_label(item: Any) -> str:
    if item.status in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.NEEDS_REVIEW}:
        return "Review item"
    if item.status == JobStatus.FAILED:
        if item.attempts < item.max_attempts:
            return "Requeue or cancel"
        return "Inspect failed item"
    if item.status == JobStatus.SUCCEEDED:
        return "Resume report"
    return "No actions"


@router.get("", response_class=HTMLResponse, response_model=None)
def ui_connector_review_queue_list(
    services: ServicesDep,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> str | HTMLResponse:
    # Validate status to prevent a DB CAST error on invalid enum values
    status_filter: str | None = None
    if status:
        try:
            status_filter = JobStatus(status).value
        except ValueError:
            return error_page(
                "Invalid Status Filter",
                (
                    f"Unknown connector review status '{status}'. Choose one of: "
                    f"{', '.join(_STATUS_OPTIONS)}."
                ),
                "/ui/connector-review-queue",
                422,
                css=_REVIEW_CSS,
            )

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
        detail_url = f"/ui/connector-review-queue/{item.ingest_run_id}"
        rows += (
            "<tr>"
            f"<td><a href='{detail_url}'>"
            f"{str(item.ingest_run_id)[:8]}…</a></td>"
            f"<td>{connector_name}</td>"
            f"<td style='color:{status_color}'>{_html.escape(item.status.value)}</td>"
            f"<td>{item.attempts}</td>"
            f"<td>{_triage_summary_html(item.payload)}</td>"
            "<td class='triage-action'>"
            f"<a href='{detail_url}'>{_html.escape(_next_action_label(item))}</a>"
            "</td>"
            f"<td>{created_str}</td>"
            "</tr>\n"
        )
    if not rows:
        rows = '<tr><td colspan="7" style="color:#666">No connector review items.</td></tr>'

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
        f"{page_head('Connector Review Queue', css=_REVIEW_CSS)}"
        "<body>"
        "<a href='/ui/'>&larr; Home</a>"
        "<h1>Connector Review Queue</h1>"
        "<form method='get' class='filter-bar'>"
        "<label>Status: <select name='status'>"
        f"{status_option_tags}"
        "</select></label>"
        f"<input type='hidden' name='limit' value='{limit}'>"
        "<button type='submit'>Filter</button>"
        "</form>"
        "<div class='review-queue-table-wrap'>"
        "<table class='review-queue-table'>"
        "<thead><tr>"
        "<th>Ingest Run ID</th><th>Connector</th><th>Status</th>"
        "<th>Attempts</th><th>Triage</th><th>Next Action</th><th>Created</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
        "</div>"
        f"{pagination}"
        "</body></html>"
    )


@router.get("/{ingest_run_id}", response_class=HTMLResponse)
def ui_connector_review_detail(
    ingest_run_id: UUID,
    request: Request,
    services: ServicesDep,
) -> HTMLResponse:
    csrf_field = csrf_form_field(request)
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return error_page(
            "Not Found",
            f"Connector review queue item not found: {ingest_run_id}",
            "/ui/connector-review-queue",
            404,
            css=_REVIEW_CSS,
        )

    # Payload summary
    payload = item.payload
    decision_context_html = _decision_context_html(payload)
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
    review_fields = reviewer_credential_fields(
        request,
        services,
        required_scope=REVIEWER_SCOPE_CONNECTOR_REVIEW,
    )
    report_run_fields = reviewer_credential_fields(
        request,
        services,
        required_scope=REVIEWER_SCOPE_REPORT_RUN,
    )

    approve_form = (
        "<div class='action-form'>"
        "<h3>Approve for QA</h3>"
        f"<form method='post' action='{base_action_url}/approve'>"
        f"{csrf_field}"
        f"{review_fields}"
        "<label>Reason (optional):"
        " <textarea name='reason'></textarea></label>"
        "<button type='submit' class='btn-approve'>Approve</button>"
        "</form></div>"
    )

    reject_form = (
        "<div class='action-form'>"
        "<h3>Request Fixture Fix (Reject)</h3>"
        f"<form method='post' action='{base_action_url}/reject'>"
        f"{csrf_field}"
        f"{review_fields}"
        "<label>Reason (required):"
        " <textarea name='reason' required></textarea></label>"
        "<button type='submit' class='btn-reject'>Request Fix</button>"
        "</form></div>"
    )

    requeue_form = (
        "<div class='action-form'>"
        "<h3>Requeue After Fix</h3>"
        f"<form method='post' action='{base_action_url}/requeue'>"
        f"{csrf_field}"
        f"{review_fields}"
        "<label>Reason (required):"
        " <textarea name='reason' required></textarea></label>"
        "<button type='submit' class='btn-requeue'>Requeue</button>"
        "</form></div>"
    )

    cancel_form = (
        "<div class='action-form'>"
        "<h3>Cancel Review</h3>"
        f"<form method='post' action='{base_action_url}/cancel'>"
        f"{csrf_field}"
        f"{review_fields}"
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
            f"{csrf_field}"
            f"{report_run_fields}"
            "<label>Intent:"
            f" <select name='intent_code'>{intent_options}</select></label>"
            "<button type='submit' class='btn-resume'>Resume Report</button>"
            "</form></div>"
        )

    open_review_statuses = {JobStatus.NEEDS_REVIEW, JobStatus.QUEUED, JobStatus.RUNNING}
    actions_html = ""
    if item.status in open_review_statuses:
        actions_html += approve_form
        actions_html += reject_form
    if item.status == JobStatus.FAILED and item.attempts < item.max_attempts:
        actions_html += requeue_form
    if item.status not in {JobStatus.SUCCEEDED, JobStatus.CANCELLED}:
        actions_html += cancel_form
    if resume_form:
        actions_html += resume_form
    if not actions_html:
        actions_html = (
            "<p style='color:#666'>"
            "No connector review actions are available for this status."
            "</p>"
        )

    body = (
        "<!DOCTYPE html><html lang='en'>"
        f"{page_head(f'Connector Review: {ingest_run_id}', css=_REVIEW_CSS)}"
        "<body>"
        "<a href='/ui/connector-review-queue'>&larr; Queue List</a>"
        f"<h1>Connector Review Item</h1>"
        f"{decision_context_html}"
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
        f"{actions_html}"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)


@router.post("/{ingest_run_id}/approve", response_class=HTMLResponse)
def ui_connector_approve(
    ingest_run_id: UUID,
    request: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    reason: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    detail_url = f"/ui/connector-review-queue/{ingest_run_id}"
    csrf_error = require_ui_csrf(request, csrf_token, back_url=detail_url, css=_REVIEW_CSS)
    if csrf_error is not None:
        return csrf_error
    try:
        auth_result = require_ui_reviewer(
            request,
            services,
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
            required_scope=REVIEWER_SCOPE_CONNECTOR_REVIEW,
        )
    except HTTPException as exc:
        return error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            detail_url,
            exc.status_code,
            css=_REVIEW_CSS,
        )
    principal = auth_result.principal
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return error_page(
            "Not Found",
            f"Queue item not found: {ingest_run_id}",
            detail_url,
            404,
            css=_REVIEW_CSS,
        )
    try:
        services.connector_review_queue.approve_for_connector_qa(
            item.job_id,
            reviewer_id=principal.reviewer_id,
            reason=reason or None,
        )
    except ValueError as exc:
        return error_page("Action Failed", str(exc), detail_url, 409, css=_REVIEW_CSS)
    response = HTMLResponse(
        content=(
            "<!DOCTYPE html><html>"
            f"{page_head('Approved', css=None, refresh_url=detail_url)}"
            "<body><h1>Approved</h1>"
            f"<p><a href='{detail_url}'>View item</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )
    attach_ui_reviewer_session_cookie(response, request, services, auth_result)
    return response


@router.post("/{ingest_run_id}/reject", response_class=HTMLResponse)
def ui_connector_reject(
    ingest_run_id: UUID,
    request: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    reason: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    detail_url = f"/ui/connector-review-queue/{ingest_run_id}"
    csrf_error = require_ui_csrf(request, csrf_token, back_url=detail_url, css=_REVIEW_CSS)
    if csrf_error is not None:
        return csrf_error
    try:
        auth_result = require_ui_reviewer(
            request,
            services,
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
            required_scope=REVIEWER_SCOPE_CONNECTOR_REVIEW,
        )
    except HTTPException as exc:
        return error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            detail_url,
            exc.status_code,
            css=_REVIEW_CSS,
        )
    principal = auth_result.principal
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return error_page(
            "Not Found",
            f"Queue item not found: {ingest_run_id}",
            detail_url,
            404,
            css=_REVIEW_CSS,
        )
    if not reason or not reason.strip():
        return error_page(
            "Validation Error",
            "Reason is required for reject.",
            detail_url,
            422,
            css=_REVIEW_CSS,
        )
    try:
        services.connector_review_queue.request_fixture_fix(
            item.job_id,
            reviewer_id=principal.reviewer_id,
            reason=reason.strip(),
        )
    except ValueError as exc:
        return error_page("Action Failed", str(exc), detail_url, 409, css=_REVIEW_CSS)
    response = HTMLResponse(
        content=(
            "<!DOCTYPE html><html>"
            f"{page_head('Fix Requested', css=None, refresh_url=detail_url)}"
            "<body><h1>Fix Requested</h1>"
            f"<p><a href='{detail_url}'>View item</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )
    attach_ui_reviewer_session_cookie(response, request, services, auth_result)
    return response


@router.post("/{ingest_run_id}/requeue", response_class=HTMLResponse)
def ui_connector_requeue(
    ingest_run_id: UUID,
    request: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    reason: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    detail_url = f"/ui/connector-review-queue/{ingest_run_id}"
    csrf_error = require_ui_csrf(request, csrf_token, back_url=detail_url, css=_REVIEW_CSS)
    if csrf_error is not None:
        return csrf_error
    try:
        auth_result = require_ui_reviewer(
            request,
            services,
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
            required_scope=REVIEWER_SCOPE_CONNECTOR_REVIEW,
        )
    except HTTPException as exc:
        return error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            detail_url,
            exc.status_code,
            css=_REVIEW_CSS,
        )
    principal = auth_result.principal
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return error_page(
            "Not Found",
            f"Queue item not found: {ingest_run_id}",
            detail_url,
            404,
            css=_REVIEW_CSS,
        )
    if not reason or not reason.strip():
        return error_page(
            "Validation Error",
            "Reason is required for requeue.",
            detail_url,
            422,
            css=_REVIEW_CSS,
        )
    try:
        services.connector_review_queue.requeue_failed(
            item.job_id,
            reason=reason.strip(),
            reviewer_id=principal.reviewer_id,
        )
    except ValueError as exc:
        return error_page("Action Failed", str(exc), detail_url, 409, css=_REVIEW_CSS)
    response = HTMLResponse(
        content=(
            "<!DOCTYPE html><html>"
            f"{page_head('Requeued', css=None, refresh_url=detail_url)}"
            "<body><h1>Requeued</h1>"
            f"<p><a href='{detail_url}'>View item</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )
    attach_ui_reviewer_session_cookie(response, request, services, auth_result)
    return response


@router.post("/{ingest_run_id}/cancel", response_class=HTMLResponse)
def ui_connector_cancel(
    ingest_run_id: UUID,
    request: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    reason: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    detail_url = f"/ui/connector-review-queue/{ingest_run_id}"
    csrf_error = require_ui_csrf(request, csrf_token, back_url=detail_url, css=_REVIEW_CSS)
    if csrf_error is not None:
        return csrf_error
    try:
        auth_result = require_ui_reviewer(
            request,
            services,
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
            required_scope=REVIEWER_SCOPE_CONNECTOR_REVIEW,
        )
    except HTTPException as exc:
        return error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            detail_url,
            exc.status_code,
            css=_REVIEW_CSS,
        )
    principal = auth_result.principal
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return error_page(
            "Not Found",
            f"Queue item not found: {ingest_run_id}",
            detail_url,
            404,
            css=_REVIEW_CSS,
        )
    if not reason or not reason.strip():
        return error_page(
            "Validation Error",
            "Reason is required for cancel.",
            detail_url,
            422,
            css=_REVIEW_CSS,
        )
    try:
        services.connector_review_queue.cancel(
            item.job_id,
            reason=reason.strip(),
            reviewer_id=principal.reviewer_id,
        )
    except ValueError as exc:
        return error_page("Action Failed", str(exc), detail_url, 409, css=_REVIEW_CSS)
    response = HTMLResponse(
        content=(
            "<!DOCTYPE html><html>"
            f"{page_head('Cancelled', css=None, refresh_url=detail_url)}"
            "<body><h1>Cancelled</h1>"
            f"<p><a href='{detail_url}'>View item</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )
    attach_ui_reviewer_session_cookie(response, request, services, auth_result)
    return response


@router.post("/{ingest_run_id}/resume-report", response_class=HTMLResponse)
def ui_connector_resume_report(
    ingest_run_id: UUID,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    intent_code: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> Response:
    detail_url = f"/ui/connector-review-queue/{ingest_run_id}"
    csrf_error = require_ui_csrf(
        request_context,
        csrf_token,
        back_url=detail_url,
        css=_REVIEW_CSS,
    )
    if csrf_error is not None:
        return csrf_error
    try:
        auth_result = require_ui_reviewer(
            request_context,
            services,
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
            required_scope=REVIEWER_SCOPE_REPORT_RUN,
        )
    except HTTPException as exc:
        return error_page(
            "Authentication Error",
            "Reviewer credentials are missing, invalid, or lack the required scope.",
            detail_url,
            exc.status_code,
            css=_REVIEW_CSS,
        )
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        return error_page(
            "Not Found",
            f"Queue item not found: {ingest_run_id}",
            detail_url,
            404,
            css=_REVIEW_CSS,
        )
    if item.status != JobStatus.SUCCEEDED:
        return error_page(
            "Not Approved",
            "Connector review item must be approved (succeeded) before resuming a report run.",
            detail_url,
            409,
            css=_REVIEW_CSS,
        )
    try:
        resolved_intent = (
            IntentCode(intent_code) if intent_code else IntentCode.RURAL_LAND_PURCHASE
        )
    except ValueError:
        return error_page(
            "Validation Error",
            f"Unknown intent code: {intent_code}",
            detail_url,
            422,
            css=_REVIEW_CSS,
        )
    area_id_raw = item.payload.get("area_id")
    if not isinstance(area_id_raw, str) or not area_id_raw.strip():
        return error_page(
            "Configuration Error",
            "Queue item missing area_id.",
            detail_url,
            409,
            css=_REVIEW_CSS,
        )
    try:
        area_id = UUID(area_id_raw)
    except ValueError:
        return error_page(
            "Configuration Error",
            "Queue item has invalid area_id.",
            detail_url,
            409,
            css=_REVIEW_CSS,
        )
    area = services.area_service.get(area_id)
    if area is None:
        return error_page(
            "Not Found",
            f"Area {area_id} is not registered.",
            detail_url,
            409,
            css=_REVIEW_CSS,
        )
    try:
        raise_report_queue_backpressure_if_needed(
            request_context=request_context,
            services=services,
        )
    except HTTPException as exc:
        return error_page(
            "Queue Backpressure",
            str(exc.detail),
            detail_url,
            exc.status_code,
            css=_REVIEW_CSS,
        )
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
    response = RedirectResponse(report_url, status_code=303)
    attach_ui_reviewer_session_cookie(response, request_context, services, auth_result)
    return response
