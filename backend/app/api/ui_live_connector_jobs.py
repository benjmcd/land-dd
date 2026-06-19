from __future__ import annotations

import html as _html
import json
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from app.api.dependencies import ApiServices, get_services
from app.api.reviewer_auth import REVIEWER_SCOPE_OPERATIONS_READ
from app.api.ui_shared import (
    build_css,
    error_page,
    page_head,
    ui_reviewer_principal_from_cookie,
)
from app.connectors.live_jobs import LiveConnectorJobRecord
from app.core.error_safety import safe_error_message, safe_payload_summary, safe_url_summary
from app.domain.enums import JobStatus
from app.domain.job_health import STALE_RUNNING_THRESHOLD_SECONDS

router = APIRouter(prefix="/ui/live-connector-jobs", tags=["ui"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]

_UI_PAGE_SIZE = 50
_CSS = build_css(
    "table { margin-bottom: 1rem; }\n"
    ".jobs-table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }\n"
    ".jobs-table { min-width: 1040px; }\n"
    ".nav { align-items:center; display:flex; flex-wrap:wrap; gap:0.35rem 0.5rem;"
    " margin-bottom:1rem; }\n"
    ".nav a { min-width:0; overflow-wrap:anywhere; }\n"
    ".filters { display:flex; flex-wrap:wrap; gap:0.5rem; align-items:center;"
    " margin-bottom:1rem; }\n"
    ".meta { display:grid; grid-template-columns: max-content 1fr; gap:0.35rem 1rem;"
    " margin:1rem 0; }\n"
    ".meta dt { font-weight:700; }\n"
    ".payload { background:#f8f9fa; border:1px solid #dee2e6; border-radius:4px;"
    " overflow:auto; padding:0.75rem; }\n"
    ".badge-stale { color:#b42318; font-weight:700; }\n"
    "@media (max-width:640px) { .nav { align-items:flex-start; flex-direction:column; }"
    " .jobs-table-wrap { overflow-x:visible; } .jobs-table { min-width:0; }"
    " .jobs-table thead { border:0; clip:rect(0 0 0 0); clip-path:inset(50%);"
    " height:1px; margin:-1px; overflow:hidden; padding:0; position:absolute;"
    " white-space:nowrap; width:1px; }"
    " .jobs-table, .jobs-table tbody, .jobs-table tr, .jobs-table td { display:block;"
    " width:100%; } .jobs-table tr { border-bottom:1px solid #dee2e6;"
    " padding:0.65rem 0; } .jobs-table td { border-bottom:0; min-width:0;"
    " overflow-wrap:anywhere; padding:0.35rem 0.5rem; }"
    " .jobs-table td::before { color:#666; content:attr(data-label); display:block;"
    " font-size:0.72rem; font-weight:700; margin-bottom:0.18rem;"
    " text-transform:uppercase; } .meta { grid-template-columns:1fr; } }\n",
)


@router.get("", response_class=HTMLResponse)
def ui_live_connector_job_list(
    request: Request,
    services: ServicesDep,
    status: Annotated[str | None, Query()] = None,
    stale: Annotated[bool, Query()] = False,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> HTMLResponse:
    reviewer_id = _operations_reviewer_id(request, services)
    if reviewer_id is None:
        return _operations_auth_required()
    status_filter = _parse_status_filter(status)
    if isinstance(status_filter, HTMLResponse):
        return status_filter
    if stale and status_filter not in (None, JobStatus.RUNNING):
        return error_page(
            "Invalid Stale Filter",
            "Stale live connector job filtering requires status=running.",
            "/ui/live-connector-jobs",
            422,
            css=_CSS,
        )
    jobs = services.live_connector_jobs.list_recent(
        limit=_UI_PAGE_SIZE,
        offset=offset,
        status=status_filter,
        stale=stale,
    )
    body = (
        "<!DOCTYPE html><html lang='en'>"
        f"{page_head('Live Connector Jobs', css=_CSS)}"
        "<body>"
        f"{_nav()}"
        "<h1>Live Connector Jobs</h1>"
        f"<p>Authenticated as: <strong>{_html.escape(reviewer_id)}</strong></p>"
        f"{_filter_form(status_filter, stale)}"
        f"{_job_table(jobs)}"
        f"{_pagination(status_filter, stale, offset, len(jobs))}"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)


@router.get("/{job_id}", response_class=HTMLResponse)
def ui_live_connector_job_detail(
    job_id: UUID,
    request: Request,
    services: ServicesDep,
) -> HTMLResponse:
    reviewer_id = _operations_reviewer_id(request, services)
    if reviewer_id is None:
        return _operations_auth_required()
    job = services.live_connector_jobs.get(job_id)
    if job is None:
        return error_page(
            "Live Connector Job Not Found",
            "No live connector job was found for this ID.",
            "/ui/live-connector-jobs",
            404,
            css=_CSS,
        )
    body = (
        "<!DOCTYPE html><html lang='en'>"
        f"{page_head('Live Connector Job', css=_CSS)}"
        "<body>"
        f"{_nav()}"
        f"<h1>Live Connector Job {_html.escape(str(job.job_id)[:8])}</h1>"
        f"<p>Authenticated as: <strong>{_html.escape(reviewer_id)}</strong></p>"
        f"{_detail_meta(job)}"
        "<h2>Payload</h2>"
        f"<pre class='payload'>{_payload_json(job)}</pre>"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)


def _operations_reviewer_id(request: Request, services: ApiServices) -> str | None:
    principal = ui_reviewer_principal_from_cookie(request, services)
    if principal is None or REVIEWER_SCOPE_OPERATIONS_READ not in principal.scopes:
        return None
    return principal.reviewer_id


def _operations_auth_required() -> HTMLResponse:
    return error_page(
        "Authentication Required",
        "Use an operations reviewer session before viewing live connector jobs.",
        "/ui/operations",
        401,
        css=_CSS,
    )


def _parse_status_filter(status: str | None) -> JobStatus | HTMLResponse | None:
    if not status:
        return None
    try:
        return JobStatus(status)
    except ValueError:
        return error_page(
            "Invalid Status Filter",
            (
                f"Unknown live connector job status '{_html.escape(status)}'. "
                f"Choose one of: {', '.join(s.value for s in JobStatus)}."
            ),
            "/ui/live-connector-jobs",
            422,
            css=_CSS,
        )


def _nav() -> str:
    return (
        "<nav class='nav' aria-label='Live connector job navigation'>"
        "<a href='/ui/operations'>&larr; Operations Dashboard</a>"
        "<a href='/ui/report-runs'>Report Runs</a>"
        "<a href='/ui/connector-review-queue'>Connector review queue</a>"
        "</nav>"
    )


def _filter_form(status_filter: JobStatus | None, stale: bool) -> str:
    options = "<option value=''>All</option>"
    for job_status in JobStatus:
        selected = " selected" if status_filter == job_status else ""
        options += (
            f"<option value='{_html.escape(job_status.value, quote=True)}'{selected}>"
            f"{_html.escape(job_status.value)}</option>"
        )
    checked = " checked" if stale else ""
    return (
        "<form class='filters' method='GET' action='/ui/live-connector-jobs'>"
        "<label for='status-filter'>Status</label>"
        f"<select id='status-filter' name='status'>{options}</select>"
        "<label><input type='checkbox' name='stale' value='true'"
        f"{checked}> Stale running</label>"
        "<button type='submit'>Apply</button>"
        "</form>"
    )


def _job_table(jobs: list[LiveConnectorJobRecord]) -> str:
    rows = "".join(_job_row(job) for job in jobs)
    if not rows:
        rows = "<tr><td colspan='9' style='color:#666'>No live connector jobs.</td></tr>"
    return (
        "<div class='jobs-table-wrap'>"
        "<table class='jobs-table'>"
        "<thead><tr>"
        "<th>ID</th><th>Connector</th><th>Status</th><th>Running Age</th>"
        "<th>Started</th><th>Attempts</th><th>Locked By</th>"
        "<th>Result</th><th>Action</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
        "</div>"
    )


def _job_row(job: LiveConnectorJobRecord) -> str:
    job_href = f"/ui/live-connector-jobs/{job.job_id}"
    result_html = _result_link(job)
    age_html = _running_age_html(job)
    return (
        "<tr>"
        f"<td data-label='ID'><a href='{job_href}'>{_html.escape(str(job.job_id)[:8])}"
        "...</a></td>"
        f"<td data-label='Connector'>{_html.escape(job.connector_name)}</td>"
        f"<td data-label='Status' style='color:{_status_color(job.status)}'>"
        f"{_html.escape(job.status.value)}</td>"
        f"<td data-label='Running Age'>{age_html}</td>"
        f"<td data-label='Started'>{_html.escape(_format_dt(job.started_at))}</td>"
        f"<td data-label='Attempts'>{job.attempts}/{job.max_attempts}</td>"
        f"<td data-label='Locked By'>{_html.escape(job.locked_by or 'n/a')}</td>"
        f"<td data-label='Result'>{result_html}</td>"
        f"<td data-label='Action'><a href='{job_href}'>Open status</a></td>"
        "</tr>"
    )


def _detail_meta(job: LiveConnectorJobRecord) -> str:
    values = [
        ("Job ID", str(job.job_id)),
        ("Area ID", str(job.area_id)),
        ("Source", job.source_registry_id),
        ("Connector", job.connector_name),
        ("Status", job.status.value),
        ("Created", _format_dt(job.created_at)),
        ("Not Before", _format_dt(job.not_before)),
        ("Started", _format_dt(job.started_at)),
        ("Finished", _format_dt(job.finished_at)),
        ("Running Age", _running_age_text(job)),
        ("Attempts", f"{job.attempts}/{job.max_attempts}"),
        ("Locked By", job.locked_by or "n/a"),
        ("Locked At", _format_dt(job.locked_at)),
        ("Last Error", safe_error_message(job.last_error) or "n/a"),
        ("Ingest Run", str(job.connector_ingest_run_id or "n/a")),
        ("Review Status", job.connector_review_status or "n/a"),
        ("Request URL", safe_url_summary(job.request_url) or "n/a"),
    ]
    rows = "".join(
        f"<dt>{_html.escape(label)}</dt><dd>{_html.escape(value)}</dd>" for label, value in values
    )
    result = _result_link(job)
    return f"<dl class='meta'>{rows}<dt>Result Link</dt><dd>{result}</dd></dl>"


def _result_link(job: LiveConnectorJobRecord) -> str:
    if job.connector_ingest_run_id is None:
        return "<span style='color:#666'>n/a</span>"
    href = f"/ui/connector-review-queue/{job.connector_ingest_run_id}"
    return f"<a href='{href}'>Review queue item</a>"


def _pagination(
    status_filter: JobStatus | None,
    stale: bool,
    offset: int,
    count: int,
) -> str:
    def _query(new_offset: int) -> str:
        parts: list[str] = []
        if status_filter is not None:
            parts.append(f"status={_html.escape(status_filter.value, quote=True)}")
        if stale:
            parts.append("stale=true")
        parts.append(f"offset={new_offset}")
        return "?" + "&amp;".join(parts)

    links: list[str] = []
    if offset > 0:
        links.append(
            f"<a href='/ui/live-connector-jobs{_query(max(0, offset - _UI_PAGE_SIZE))}'>"
            "&larr; Previous</a>"
        )
    if count == _UI_PAGE_SIZE:
        links.append(
            f"<a href='/ui/live-connector-jobs{_query(offset + _UI_PAGE_SIZE)}'>Next &rarr;</a>"
        )
    return "" if not links else "<div style='margin-top:1rem'>" + " ".join(links) + "</div>"


def _running_age_seconds(job: LiveConnectorJobRecord) -> float | None:
    if job.status != JobStatus.RUNNING:
        return None
    started_at = job.started_at or job.created_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=UTC)
    return max(0.0, (datetime.now(UTC) - started_at).total_seconds())


def _running_age_text(job: LiveConnectorJobRecord) -> str:
    age = _running_age_seconds(job)
    return "n/a" if age is None else f"{age:.1f}s"


def _running_age_html(job: LiveConnectorJobRecord) -> str:
    text = _html.escape(_running_age_text(job))
    age = _running_age_seconds(job)
    if age is None or age < STALE_RUNNING_THRESHOLD_SECONDS:
        return text
    return f"<span class='badge-stale'>{text} stale</span>"


def _status_color(status: JobStatus) -> str:
    return {
        JobStatus.QUEUED: "#6c757d",
        JobStatus.RUNNING: "#007bff",
        JobStatus.SUCCEEDED: "#1f7a3f",
        JobStatus.FAILED: "#b42318",
        JobStatus.CANCELLED: "#6c757d",
        JobStatus.NEEDS_REVIEW: "#8a6116",
    }.get(status, "#333")


def _format_dt(value: datetime | None) -> str:
    return "n/a" if value is None else value.isoformat()


def _payload_json(job: LiveConnectorJobRecord) -> str:
    payload = safe_payload_summary(
        job.payload,
        allowed_keys=(
            "kind",
            "source_registry_id",
            "connector_name",
            "area_id",
            "workspace_id",
            "requested_by",
            "max_features",
            "max_rows",
            "max_sample_points",
            "connector_ingest_run_id",
            "connector_review_status",
        ),
    )
    safe_request_url = safe_url_summary(job.request_url)
    if safe_request_url is not None:
        payload["request_url"] = safe_request_url
    return _html.escape(json.dumps(payload, indent=2, sort_keys=True))


__all__ = ["router"]
