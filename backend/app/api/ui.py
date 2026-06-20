from __future__ import annotations

import html as _html
import json
from collections.abc import Callable, Sequence, Sized
from datetime import UTC, datetime
from json import JSONDecodeError
from typing import Annotated, cast
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

import app.api.operator_cases as operator_cases_api
from app.api.dependencies import ApiServices, get_services
from app.api.intake import IntakeRequest, intake_report
from app.api.reports import (
    ReportRunDiffResponse,
    _build_comparison_summary,
    _parse_compare_ids,
    raise_report_queue_backpressure_if_needed,
    schedule_report_background,
)
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_REPORT_APPROVE,
    REVIEWER_SCOPE_REPORT_RETRY,
    REVIEWER_SCOPE_REPORT_RUN,
)
from app.api.ui_shared import (
    attach_ui_report_identity_session_cookie,
    attach_ui_reviewer_session_cookie,
    csrf_form_field,
    error_page,
    report_identity_fields,
    require_ui_csrf,
    require_ui_report_identity,
    require_ui_reviewer,
    reviewer_credential_fields,
)
from app.core.config import Settings
from app.core.error_safety import safe_error_message
from app.domain.enums import IntentCode, JobStatus, ReportReviewStatus
from app.domain.job_health import STALE_RUNNING_THRESHOLD_SECONDS
from app.domain.report_contracts import ReportRunContract
from app.reports.dossier import build_rural_land_dossier
from app.reports.job_store import ReportJobRecord

_UI_PAGE_SIZE = 30
_RAW_INVENTORY_LIMIT = 50
_REPORT_REFRESH_SECONDS_DEFAULT = 3
_REPORT_REFRESH_SECONDS_OPTIONS = (3, 10, 30, 60)

router = APIRouter(prefix="/ui", tags=["ui"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]

_INTENT_OPTIONS = [
    ("rural_land_purchase", "Rural Land Purchase"),
    ("homestead_feasibility", "Homestead Feasibility"),
]
_GEOJSON_PLACEHOLDER = '{"type":"Polygon","coordinates":[[...]]}'
_LOCAL_UI_WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
_LOCAL_UI_USER_ID = UUID("22222222-2222-4222-8222-222222222222")

_INDEX_CSS = """\
:root { color-scheme: light; --ink:#1f2933; --muted:#5f6c7b; --line:#d8dee7; --panel:#ffffff; --soft:#f4f7fb; --accent:#155e75; --ok:#166534; --warn:#9a3412; }
* { box-sizing: border-box; }
body { font-family: system-ui, sans-serif; margin: 0; background: #eef2f6; color: var(--ink); }
a { color: var(--accent); }
.topbar { background: #ffffff; border-bottom: 1px solid var(--line); position: sticky; top: 0; z-index: 1; }
.topbar-inner { max-width: 1320px; margin: 0 auto; padding: 0.75rem 1rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.brand { display: flex; flex-direction: column; gap: 0.15rem; min-width: 13rem; }
.brand h1 { font-size: 1rem; margin: 0; }
.brand span, .status-strip span { color: var(--muted); font-size: 0.82rem; }
nav.console-nav { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; justify-content: flex-end; }
nav.console-nav a { border: 1px solid var(--line); border-radius: 4px; padding: 0.35rem 0.55rem; text-decoration: none; background: #ffffff; font-size: 0.88rem; }
nav.console-nav a:focus-visible, button:focus-visible, select:focus-visible, textarea:focus-visible { outline: 3px solid #7dd3fc; outline-offset: 2px; }
.shell { max-width: 1360px; margin: 0 auto; padding: 1rem; }
.status-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
.status-item { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; min-width: 0; padding: 0.7rem 0.8rem; }
.status-item strong { display: block; font-size: 0.92rem; margin-bottom: 0.2rem; }
h1 { font-size: 1.45rem; margin: 0 0 0.25rem; }
h2 { font-size: 1rem; margin: 0; }
p { color: var(--muted); line-height: 1.45; }
.console-grid { display: grid; grid-template-columns: minmax(900px, 2fr) minmax(300px, 0.7fr); gap: 1rem; align-items: start; }
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; min-width: 0; padding: 1rem; }
.case-panel { grid-column: 1 / -1; }
.panel-header { display: flex; align-items: start; justify-content: space-between; gap: 1rem; margin-bottom: 0.85rem; }
.panel-header p { margin: 0.25rem 0 0; font-size: 0.9rem; }
.badge { align-items: center; background: var(--soft); border: 1px solid var(--line); border-radius: 999px; color: #3d4b5c; display: inline-flex; font-size: 0.78rem; font-weight: 700; gap: 0.25rem; padding: 0.2rem 0.5rem; white-space: nowrap; }
.table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 6px; min-width: 0; }
.case-table { border-collapse: collapse; min-width: 1020px; width: 100%; }
.case-table caption { height: 1px; overflow: hidden; position: absolute; width: 1px; }
.case-table th, .case-table td { border-bottom: 1px solid var(--line); min-width: 0; overflow-wrap: anywhere; padding: 0.55rem 0.65rem; text-align: left; vertical-align: top; }
.case-table th { background: var(--soft); color: #334155; font-size: 0.78rem; letter-spacing: 0; text-transform: uppercase; }
.case-table tr:last-child td { border-bottom: 0; }
.case-table th:last-child, .case-table td:last-child { width: 8.4rem; }
.case-id { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-weight: 700; }
.description { color: #314153; max-width: 26rem; overflow-wrap: anywhere; }
.domain-list { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.domain { background: #ecfdf5; border: 1px solid #bbf7d0; border-radius: 4px; color: var(--ok); font-size: 0.78rem; padding: 0.12rem 0.35rem; }
.boundary { color: #314153; display: grid; gap: 0.28rem; max-width: 16rem; overflow-wrap: anywhere; }
.boundary strong { color: #334155; font-size: 0.76rem; }
.boundary-note { color: var(--muted); font-size: 0.78rem; }
.boundary-list { display: flex; flex-wrap: wrap; gap: 0.25rem; }
.boundary-chip { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 4px; color: #1d4ed8; font-size: 0.76rem; padding: 0.1rem 0.3rem; word-break: break-word; }
.compact-form { margin: 0; }
.primary-button, .secondary-button { border: 0; border-radius: 4px; cursor: pointer; font-weight: 700; }
.primary-button { background: var(--accent); color: white; min-width: 7.4rem; padding: 0.48rem 0.65rem; }
.secondary-button { background: #334155; color: white; padding: 0.65rem 0.8rem; width: 100%; }
.intake-form { display: flex; flex-direction: column; gap: 0.75rem; }
.field { display: flex; flex-direction: column; gap: 0.35rem; }
label { color: #334155; font-size: 0.88rem; font-weight: 700; }
textarea { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; min-height: 13rem; resize: vertical; width: 100%; }
select, textarea { border: 1px solid #b8c2cf; border-radius: 4px; padding: 0.55rem; font-size: 0.95rem; }
.help { color: var(--muted); font-size: 0.82rem; margin: 0; }
.warning { background: #fff7ed; border: 1px solid #fed7aa; color: var(--warn); padding: 0.85rem; border-radius: 4px; margin: 0.75rem 0 0; }
.note { color: var(--muted); font-size: 0.86rem; margin-top: 1rem; border-top: 1px solid var(--line); padding-top: 0.9rem; }
#result pre { white-space: pre-wrap; }
@media (max-width: 1080px) { .topbar-inner, .panel-header { align-items: stretch; flex-direction: column; } nav.console-nav { justify-content: flex-start; } .status-strip, .console-grid { grid-template-columns: 1fr; } .shell { padding: 0.75rem; } }
@media (max-width: 640px) {
  .table-wrap { overflow-x: visible; }
  .case-table { min-width: 0; }
  .case-table thead { display: none; }
  .case-table, .case-table tbody, .case-table tr, .case-table td {
    display: block;
    width: 100%;
  }
  .case-table tr { border-bottom: 1px solid var(--line); padding: 0.75rem 0; }
  .case-table tr:last-child { border-bottom: 0; }
  .case-table td {
    border-bottom: 0;
    display: block;
    min-width: 0;
    overflow-wrap: anywhere;
    padding: 0.35rem 0.65rem;
  }
  .case-table td::before {
    color: var(--muted);
    content: attr(data-label);
    display: block;
    font-size: 0.72rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
    text-transform: uppercase;
  }
  .case-table td:last-child { width: 100%; }
  .primary-button { width: 100%; }
}
"""  # noqa: E501

_REPORT_CSS = """\
:root { color-scheme: light; --ink:#1f2933; --muted:#5f6c7b; --line:#d8dee7; --panel:#ffffff; --soft:#f4f7fb; --accent:#155e75; --ok:#166534; --warn:#9a3412; --danger:#991b1b; }
* { box-sizing: border-box; }
body.report-page { font-family: system-ui, sans-serif; margin: 0; background: #eef2f6; color: var(--ink); }
a { color: var(--accent); }
.report-shell { max-width: 980px; margin: 0 auto; padding: 1rem; }
.report-nav { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; }
.report-nav a, .action-panel a { background: #ffffff; border: 1px solid var(--line); border-radius: 4px; padding: 0.45rem 0.65rem; text-decoration: none; }
.status-panel, .action-panel, .warning, pre.dossier { background: var(--panel); border: 1px solid var(--line); border-radius: 6px; margin-bottom: 1rem; min-width: 0; padding: 1rem; }
.status-panel { border-left: 0.45rem solid var(--accent); display: grid; gap: 0.75rem; }
.status-pending { border-left-color: var(--warn); }
.status-generating { border-left-color: var(--accent); }
.status-failed, .status-missing { border-left-color: var(--danger); }
.status-approved { border-left-color: var(--ok); }
.status-label { color: var(--muted); font-size: 0.78rem; font-weight: 700; letter-spacing: 0; text-transform: uppercase; }
h1 { color: #2c3e50; font-size: 1.55rem; margin: 0; }
h2 { color: #34495e; font-size: 1rem; margin: 0 0 0.5rem; }
p { color: var(--muted); line-height: 1.45; margin: 0.35rem 0; }
ul { line-height: 1.8; }
.meta { background: var(--soft); border-radius: 4px; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 0.9rem; padding: 0.85rem; overflow-wrap: anywhere; }
.action-panel { display: grid; gap: 0.75rem; }
.action-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.refresh-controls { display: grid; gap: 0.75rem; }
.refresh-interval-form { align-items: end; display: flex; flex-wrap: wrap; gap: 0.5rem; }
.refresh-interval-form label { color: #334155; display: grid; font-size: 0.88rem; font-weight: 700; gap: 0.3rem; }
.refresh-interval-form select { border: 1px solid #b8c2cf; border-radius: 4px; font-size: 0.95rem; padding: 0.48rem; }
.refresh-interval-form button { background: #334155; border: 0; border-radius: 4px; color: #ffffff; cursor: pointer; font-weight: 700; padding: 0.58rem 0.8rem; }
.stacked-form { display: grid; gap: 0.7rem; max-width: 24rem; }
.stacked-form label { color: #334155; display: grid; font-size: 0.88rem; font-weight: 700; gap: 0.35rem; }
.stacked-form input, .stacked-form textarea { border: 1px solid #b8c2cf; border-radius: 4px; font-size: 0.95rem; padding: 0.55rem; width: 100%; }
.stacked-form textarea { font-family: system-ui, sans-serif; min-height: 5.5rem; resize: vertical; }
.primary-action { background: var(--accent); border: 0; border-radius: 4px; color: #ffffff; cursor: pointer; font-size: 1rem; font-weight: 700; padding: 0.65rem 0.9rem; }
.primary-action.approve { background: var(--ok); }
.primary-action.retry { background: #1d4ed8; }
.warning { background: #fff7ed; border-color: #fed7aa; color: var(--warn); margin-top: 1rem; }
pre.dossier { white-space: pre-wrap; font-family: system-ui, sans-serif; line-height: 1.6; font-size: 0.95rem; }
input { border: 1px solid #b8c2cf; border-radius: 4px; font-size: 0.95rem; max-width: 100%; padding: 0.55rem; }
.reviewer-session { color: var(--muted); display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.25rem 0.45rem; line-height: 1.45; margin: 0.35rem 0; }
.reviewer-session.warning { display: block; }
.reviewer-session-link { background: transparent; border: 0; color: var(--accent); display: inline; padding: 0; text-decoration: underline; }
button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible { outline: 3px solid #7dd3fc; outline-offset: 2px; }
@media (max-width: 640px) { .report-shell { padding: 0.75rem; } .report-nav, .action-row, .refresh-interval-form { align-items: stretch; flex-direction: column; } .refresh-interval-form label { width: 100%; } .report-nav a, .action-panel a, .primary-action, .refresh-interval-form button, .refresh-interval-form select { text-align: center; width: 100%; } }
"""  # noqa: E501


def _report_refresh_query(
    *,
    auto_refresh: bool | None = None,
    refresh_seconds: int = _REPORT_REFRESH_SECONDS_DEFAULT,
) -> str:
    params: list[str] = []
    if auto_refresh is False:
        params.append("auto_refresh=false")
    if refresh_seconds != _REPORT_REFRESH_SECONDS_DEFAULT:
        params.append(f"refresh_seconds={refresh_seconds}")
    if not params:
        return ""
    return "?" + "&".join(params)


def _report_refresh_interval_form(
    *,
    report_url: str,
    auto_refresh: bool,
    refresh_seconds: int,
) -> str:
    pause_field = "" if auto_refresh else "<input type='hidden' name='auto_refresh' value='false'>"
    options = "".join(
        (
            f"<option value='{seconds}'"
            f"{' selected' if seconds == refresh_seconds else ''}>"
            f"{seconds} seconds</option>"
        )
        for seconds in _REPORT_REFRESH_SECONDS_OPTIONS
    )
    return (
        f"<form class='refresh-interval-form' method='get' action='{report_url}'>"
        f"{pause_field}"
        "<label>Refresh interval"
        f"<select name='refresh_seconds'>{options}</select>"
        "</label>"
        "<button type='submit'>Apply interval</button>"
        "</form>"
    )


def _report_nav(
    report_run_id: UUID | None = None,
    *,
    include_report_links: bool = False,
) -> str:
    links = [
        '<a href="/ui/">Home</a>',
        '<a href="/ui/report-runs">All Reports</a>',
    ]
    if include_report_links and report_run_id is not None:
        links.extend(
            [
                (f'<a href="/ui/report-runs/{report_run_id}/print">Print / Export PDF</a>'),
                (
                    f'<a href="/report-runs/{report_run_id}/dossier?download=1">'
                    "Download dossier (.md)</a>"
                ),
                (f'<a href="/report-runs/{report_run_id}/artifact">Download report (.json)</a>'),
                (f'<a href="/ui/report-runs/{report_run_id}/lineage">View evidence lineage</a>'),
            ]
        )
    return '<nav class="report-nav" aria-label="Report navigation">' + "".join(links) + "</nav>"


def _report_page(
    *,
    title: str,
    heading: str,
    status_label: str,
    status_class: str,
    details_html: str,
    action_html: str,
    report_run_id: UUID | None = None,
    include_report_links: bool = False,
    refresh_seconds: int | None = None,
    extra_html: str = "",
) -> str:
    refresh_meta = ""
    if refresh_seconds is not None:
        refresh_meta = f'<meta http-equiv="refresh" content="{refresh_seconds}">'
    safe_title = _html.escape(title)
    safe_heading = _html.escape(heading)
    safe_status_label = _html.escape(status_label)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{refresh_meta}
<title>{safe_title}</title>
<style>
{_REPORT_CSS}
</style></head>
<body class="report-page">
<main class="report-shell">
{_report_nav(report_run_id, include_report_links=include_report_links)}
<section class="status-panel status-{status_class}" aria-labelledby="report-status-title">
  <div class="status-label">{safe_status_label}</div>
  <h1 id="report-status-title">{safe_heading}</h1>
  {details_html}
</section>
<section class="action-panel" aria-labelledby="report-action-title">
  <h2 id="report-action-title">Operator Action</h2>
  {action_html}
</section>
{extra_html}
</main>
</body></html>"""


def _report_list_action_links(links: list[tuple[str, str]]) -> str:
    rendered = "".join(
        (f'<a href="{_html.escape(href, quote=True)}">{_html.escape(label)}</a>')
        for href, label in links
    )
    return f'<div class="report-actions">{rendered}</div>'


def _report_list_next_action_html(
    report_run_id: UUID,
    status_value: JobStatus,
    review_status: ReportReviewStatus | None,
    *,
    has_report: bool,
) -> str:
    detail_href = f"/ui/report-runs/{report_run_id}"
    if status_value in {JobStatus.QUEUED, JobStatus.RUNNING}:
        return _report_list_action_links([(detail_href, "Open status")])
    if status_value == JobStatus.FAILED:
        return _report_list_action_links([(detail_href, "Retry from detail")])
    if status_value == JobStatus.SUCCEEDED and has_report:
        if review_status == ReportReviewStatus.APPROVED:
            return _report_list_action_links(
                [
                    (detail_href, "View dossier"),
                    (
                        f"/report-runs/{report_run_id}/dossier?download=1",
                        "Download dossier",
                    ),
                    (f"/report-runs/{report_run_id}/artifact", "Download JSON"),
                    (f"{detail_href}/lineage", "Lineage"),
                ]
            )
        return _report_list_action_links([(detail_href, "Approve from detail")])
    return _report_list_action_links([(detail_href, "Open detail")])


def _report_job_running_age_seconds(job: ReportJobRecord) -> float | None:
    if job.status != JobStatus.RUNNING:
        return None
    started_at = job.started_at or job.created_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=UTC)
    return max(0.0, (datetime.now(UTC) - started_at).total_seconds())


def _report_job_running_age_html(job: ReportJobRecord) -> str:
    running_age = _report_job_running_age_seconds(job)
    if running_age is None:
        return "n/a"
    text = f"{running_age:.1f}s"
    if running_age < STALE_RUNNING_THRESHOLD_SECONDS:
        return _html.escape(text)
    return f"<span style='color:#b42318;font-weight:700'>{_html.escape(text)} stale</span>"


def _format_dt(value: datetime | None) -> str:
    return "n/a" if value is None else value.isoformat()


def _raw_collect(
    collector: Callable[[], Sequence[object]],
) -> tuple[list[object], str | None]:
    try:
        return list(collector()), None
    except Exception as exc:  # noqa: BLE001 - inventory must fail closed per section
        return [], safe_error_message(str(exc)) or "not available from current service"


def _raw_count(collector: Callable[[], Sized]) -> str:
    try:
        return str(len(collector()))
    except Exception:  # noqa: BLE001 - home summary must remain available
        return "n/a"


def _raw_inventory_summary(services: ApiServices) -> str:
    values = (
        ("sources", _raw_count(lambda: services.source_service.list_all())),
        ("areas", _raw_count(lambda: services.area_service.list_all())),
        ("evidence", _raw_count(lambda: services.evidence_service.list_all())),
        ("claims", _raw_count(lambda: services.claim_service.list_all())),
        (
            "report runs",
            _raw_count(
                lambda: services.report_service.list_recent_report_runs(
                    limit=_RAW_INVENTORY_LIMIT
                )
            ),
        ),
        (
            "report jobs",
            _raw_count(
                lambda: services.async_report_jobs.list_recent(
                    limit=_RAW_INVENTORY_LIMIT
                )
            ),
        ),
        (
            "review items",
            _raw_count(
                lambda: services.connector_review_queue.list_connector_runs(
                    limit=_RAW_INVENTORY_LIMIT
                )
            ),
        ),
        (
            "live jobs",
            _raw_count(
                lambda: services.live_connector_jobs.list_recent(
                    limit=_RAW_INVENTORY_LIMIT
                )
            ),
        ),
    )
    return " | ".join(f"{label}: {value}" for label, value in values)


def _raw_inventory_table(headers: tuple[str, ...], rows: str) -> str:
    header_html = "".join(f"<th scope='col'>{_html.escape(header)}</th>" for header in headers)
    return (
        "<table class='case-table raw-table'>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
    )


def _empty_raw_row(colspan: int, message: str) -> str:
    return f'<tr><td colspan="{colspan}">{_html.escape(message)}</td></tr>'


def _unavailable_raw_row(colspan: int, message: str) -> str:
    return (
        f'<tr><td colspan="{colspan}">'
        f"Unavailable: {_html.escape(message)}"
        "</td></tr>"
    )


def _short_id(value: object) -> str:
    raw = str(value)
    return f"{raw[:8]}..." if len(raw) > 8 else raw


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


def _source_rows(records: list[object], unavailable: str | None) -> str:
    headers = ("ID", "Name", "Domain", "Review", "Rights")
    if unavailable is not None:
        return _raw_inventory_table(headers, _unavailable_raw_row(len(headers), unavailable))
    rows = ""
    for source in records:
        source_id = _html.escape(_short_id(getattr(source, "source_id", "n/a")))
        rows += (
            "<tr>"
            f"<td class='case-id'>{source_id}</td>"
            f"<td>{_html.escape(str(getattr(source, 'name', 'n/a')))}</td>"
            f"<td>{_html.escape(str(getattr(source, 'domain', 'n/a')))}</td>"
            f"<td>{_html.escape(str(getattr(source, 'review_status', 'n/a')))}</td>"
            "<td>"
            f"raw={_html.escape(str(getattr(source, 'raw_data_allowed', 'n/a')))}; "
            f"export={_html.escape(str(getattr(source, 'export_allowed', 'n/a')))}"
            "</td>"
            "</tr>"
        )
    return _raw_inventory_table(headers, rows or _empty_raw_row(len(headers), "No sources."))


def _area_rows(records: list[object], unavailable: str | None) -> str:
    headers = ("ID", "Label", "Type", "Geometry Source", "Validated")
    if unavailable is not None:
        return _raw_inventory_table(headers, _unavailable_raw_row(len(headers), unavailable))
    rows = ""
    for area in records:
        rows += (
            "<tr>"
            f"<td class='case-id'>{_html.escape(_short_id(getattr(area, 'area_id', 'n/a')))}</td>"
            f"<td>{_html.escape(str(getattr(area, 'label', None) or 'n/a'))}</td>"
            f"<td>{_html.escape(_enum_value(getattr(area, 'area_type', 'n/a')))}</td>"
            f"<td>{_html.escape(str(getattr(area, 'geom_source', None) or 'n/a'))}</td>"
            f"<td>{_html.escape(str(getattr(area, 'geom_validated', 'n/a')))}</td>"
            "</tr>"
        )
    return _raw_inventory_table(headers, rows or _empty_raw_row(len(headers), "No areas."))


def _evidence_rows(records: list[object], unavailable: str | None) -> str:
    headers = ("ID", "Area", "Source", "Domain", "Type", "Observation")
    if unavailable is not None:
        return _raw_inventory_table(headers, _unavailable_raw_row(len(headers), unavailable))
    rows = ""
    for evidence in records:
        evidence_id = _html.escape(_short_id(getattr(evidence, "evidence_id", "n/a")))
        area_id = _html.escape(_short_id(getattr(evidence, "area_id", "n/a")))
        source_id = _html.escape(_short_id(getattr(evidence, "source_id", "n/a")))
        rows += (
            "<tr>"
            f"<td class='case-id'>{evidence_id}</td>"
            f"<td class='case-id'>{area_id}</td>"
            f"<td class='case-id'>{source_id}</td>"
            f"<td>{_html.escape(str(getattr(evidence, 'domain', 'n/a')))}</td>"
            f"<td>{_html.escape(_enum_value(getattr(evidence, 'evidence_type', 'n/a')))}</td>"
            f"<td>{_html.escape(str(getattr(evidence, 'observation', 'n/a')))}</td>"
            "</tr>"
        )
    return _raw_inventory_table(headers, rows or _empty_raw_row(len(headers), "No evidence."))


def _claim_rows(records: list[object], unavailable: str | None) -> str:
    headers = ("ID", "Area", "Code", "Domain", "Severity", "Evidence IDs", "Verification Task")
    if unavailable is not None:
        return _raw_inventory_table(headers, _unavailable_raw_row(len(headers), unavailable))
    rows = ""
    for claim in records:
        evidence_ids = getattr(claim, "evidence_ids", [])
        evidence_html = "<br>".join(
            f"<span class='case-id'>{_html.escape(_short_id(evidence_id))}</span>"
            for evidence_id in evidence_ids
        )
        rows += (
            "<tr>"
            f"<td class='case-id'>{_html.escape(_short_id(getattr(claim, 'claim_id', 'n/a')))}</td>"
            f"<td class='case-id'>{_html.escape(_short_id(getattr(claim, 'area_id', 'n/a')))}</td>"
            f"<td>{_html.escape(str(getattr(claim, 'claim_code', 'n/a')))}</td>"
            f"<td>{_html.escape(str(getattr(claim, 'domain', 'n/a')))}</td>"
            f"<td>{_html.escape(_enum_value(getattr(claim, 'severity', 'n/a')))}</td>"
            f"<td>{evidence_html or 'none'}</td>"
            f"<td>{_html.escape(str(getattr(claim, 'verification_task', None) or 'n/a'))}</td>"
            "</tr>"
        )
    return _raw_inventory_table(headers, rows or _empty_raw_row(len(headers), "No claims."))


def _report_run_rows(records: list[object], unavailable: str | None) -> str:
    headers = ("ID", "Intent", "Status", "Review", "Evidence", "Claims", "Links")
    if unavailable is not None:
        return _raw_inventory_table(headers, _unavailable_raw_row(len(headers), unavailable))
    rows = ""
    for report in records:
        if not isinstance(report, ReportRunContract):
            continue
        rows += (
            "<tr>"
            f"<td class='case-id'>{_html.escape(str(report.report_run_id))}</td>"
            f"<td>{_html.escape(report.intent_code.value)}</td>"
            f"<td>{_html.escape(report.status.value)}</td>"
            f"<td>{_html.escape(report.review_status.value)}</td>"
            f"<td>{_html.escape(str(len(report.evidence)))}</td>"
            f"<td>{_html.escape(str(_report_claim_total(report)))}</td>"
            f"<td>{_report_contract_links(report)}</td>"
            "</tr>"
        )
    return _raw_inventory_table(
        headers,
        rows or _empty_raw_row(len(headers), "No report run contracts."),
    )


def _report_claim_total(report: ReportRunContract) -> int:
    return (
        len(report.claims)
        + len(report.unknowns)
        + len(report.red_flags)
        + len(report.advisory_claims)
    )


def _report_contract_links(report: ReportRunContract) -> str:
    report_run_id = report.report_run_id
    return _report_list_action_links(
        [
            (f"/ui/report-runs/{report_run_id}", "detail"),
            (f"/report-runs/{report_run_id}/dossier?download=1", "dossier"),
            (f"/report-runs/{report_run_id}/artifact", "json"),
            (f"/ui/report-runs/{report_run_id}/lineage", "lineage"),
        ]
    )


def _report_job_rows(records: list[object], unavailable: str | None) -> str:
    headers = ("ID", "Status", "Intent", "Area", "Created", "Links")
    if unavailable is not None:
        return _raw_inventory_table(headers, _unavailable_raw_row(len(headers), unavailable))
    rows = ""
    for job in records:
        report_run_id = getattr(job, "report_run_id", "n/a")
        job_links = _report_list_action_links([(f"/ui/report-runs/{report_run_id}", "detail")])
        rows += (
            "<tr>"
            f"<td class='case-id'>{_html.escape(str(report_run_id))}</td>"
            f"<td>{_html.escape(_enum_value(getattr(job, 'status', 'n/a')))}</td>"
            f"<td>{_html.escape(_enum_value(getattr(job, 'intent_code', 'n/a')))}</td>"
            f"<td class='case-id'>{_html.escape(_short_id(getattr(job, 'area_id', 'n/a')))}</td>"
            f"<td>{_html.escape(_format_dt(getattr(job, 'created_at', None)))}</td>"
            f"<td>{job_links}</td>"
            "</tr>"
        )
    return _raw_inventory_table(headers, rows or _empty_raw_row(len(headers), "No report jobs."))


def _review_item_rows(records: list[object], unavailable: str | None) -> str:
    headers = ("Ingest Run", "Status", "Connector", "Priority", "Created", "Link")
    if unavailable is not None:
        return _raw_inventory_table(headers, _unavailable_raw_row(len(headers), unavailable))
    rows = ""
    for item in records:
        ingest_run_id = getattr(item, "ingest_run_id", None)
        payload = getattr(item, "payload", {})
        connector = payload.get("connector_name", "n/a") if isinstance(payload, dict) else "n/a"
        link = "n/a"
        if isinstance(ingest_run_id, UUID):
            link = _report_list_action_links(
                [(f"/ui/connector-review-queue/{ingest_run_id}", "review")]
            )
        rows += (
            "<tr>"
            f"<td class='case-id'>{_html.escape(_short_id(ingest_run_id or 'n/a'))}</td>"
            f"<td>{_html.escape(_enum_value(getattr(item, 'status', 'n/a')))}</td>"
            f"<td>{_html.escape(str(connector))}</td>"
            f"<td>{_html.escape(str(getattr(item, 'priority', 'n/a')))}</td>"
            f"<td>{_html.escape(_format_dt(getattr(item, 'created_at', None)))}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )
    return _raw_inventory_table(
        headers,
        rows or _empty_raw_row(len(headers), "No connector review items."),
    )


def _live_job_rows(records: list[object], unavailable: str | None) -> str:
    headers = ("ID", "Status", "Connector", "Source", "Area", "Link")
    if unavailable is not None:
        return _raw_inventory_table(headers, _unavailable_raw_row(len(headers), unavailable))
    rows = ""
    for job in records:
        job_id = getattr(job, "job_id", None)
        link = "n/a"
        if isinstance(job_id, UUID):
            link = _report_list_action_links([(f"/ui/live-connector-jobs/{job_id}", "status")])
        rows += (
            "<tr>"
            f"<td class='case-id'>{_html.escape(_short_id(job_id or 'n/a'))}</td>"
            f"<td>{_html.escape(_enum_value(getattr(job, 'status', 'n/a')))}</td>"
            f"<td>{_html.escape(str(getattr(job, 'connector_name', 'n/a')))}</td>"
            f"<td>{_html.escape(str(getattr(job, 'source_registry_id', 'n/a')))}</td>"
            f"<td class='case-id'>{_html.escape(_short_id(getattr(job, 'area_id', 'n/a')))}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )
    return _raw_inventory_table(
        headers,
        rows or _empty_raw_row(len(headers), "No live connector jobs."),
    )


def _raw_inventory_section(
    title: str,
    description: str,
    records: list[object],
    unavailable: str | None,
    table_html: str,
) -> str:
    count_label = "n/a" if unavailable is not None else f"{len(records)} records"
    section_id = title.lower().replace(" ", "-")
    return (
        f'<section class="panel" aria-labelledby="{_html.escape(section_id)}">'
        '<div class="panel-header"><div>'
        f'<h2 id="{_html.escape(section_id)}">{_html.escape(title)}</h2>'
        f"<p>{_html.escape(description)}</p>"
        "</div>"
        f'<span class="badge">{_html.escape(count_label)}</span>'
        "</div>"
        f'<div class="table-wrap">{table_html}</div>'
        "</section>"
    )


@router.get("/", response_class=HTMLResponse)
def ui_index(request: Request, services: ServicesDep) -> str:
    intent_options = "\n".join(
        f'<option value="{val}">{label}</option>' for val, label in _INTENT_OPTIONS
    )
    csrf_field = csrf_form_field(request)
    selected_county_markup = _selected_county_fixture_markup(
        request,
        services,
        csrf_field,
    )
    raw_inventory_summary = _html.escape(_raw_inventory_summary(services))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Land Diligence — Report</title>
<style>
{_INDEX_CSS}
</style>
</head>
<body>
<header class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <h1>Land Diligence Operator Console</h1>
      <span>Selected-county fixtures and custom AOI intake</span>
    </div>
    <nav class="console-nav" aria-label="Operator console navigation">
      <a href="/ui/raw-data">Raw data inventory</a>
      <a href="/ui/report-runs">Report runs</a>
      <a href="/ui/operations">Operations</a>
      <a href="/ui/connector-review-queue">Connector review queue</a>
      <a href="/docs">API docs</a>
    </nav>
  </div>
</header>
<div class="shell">
  <div class="status-strip" aria-label="Console status">
    <div class="status-item">
      <strong>Coverage mode</strong>
      <span>Private MVP fixture coverage</span>
    </div>
    <div class="status-item">
      <strong>Report release</strong>
      <span>Review-gated dossier and artifact delivery</span>
    </div>
    <div class="status-item">
      <strong>Custom AOI</strong>
      <span>Polygon or MultiPolygon GeoJSON</span>
    </div>
    <div class="status-item">
      <strong><a href="/ui/raw-data">Runtime inventory</a></strong>
      <span>{raw_inventory_summary}</span>
    </div>
  </div>
  <main class="console-grid">
    {selected_county_markup}
    <section class="panel" id="custom-report-panel" aria-labelledby="custom-report-title">
      <div class="panel-header">
        <div>
          <h2 id="custom-report-title">Custom GeoJSON Intake</h2>
          <p id="custom-intake-help">
            Non-fixture screening report creation.
          </p>
        </div>
        <span class="badge">Manual AOI</span>
      </div>
      <form id="report-form" class="intake-form" method="POST" action="/ui/intake">
        {csrf_field}
        <div class="field">
          <label for="area_geojson">Area GeoJSON</label>
          <textarea
            id="area_geojson"
            name="area_geojson"
            placeholder='{_GEOJSON_PLACEHOLDER}'
            aria-describedby="custom-intake-help"
            required></textarea>
        </div>
        <div class="field">
          <label for="intent">Intent</label>
          <select id="intent" name="intent">{intent_options}</select>
        </div>
        <button class="secondary-button" type="submit">
          Generate custom report
        </button>
      </form>
      <div id="result" role="status" aria-live="polite"></div>
    </section>
  </main>
  <div class="note">
    <strong>Screening tool only.</strong> Outputs are subject to the source appendix
    and do not constitute legal, title, survey, zoning, or appraisal determinations.
  </div>
</div>
<script>
function submitReport() {{
  var form = document.getElementById('report-form');
  var geojson = document.getElementById('area_geojson').value;
  var parsedGeojson;
  try {{
    parsedGeojson = JSON.parse(geojson);
  }} catch (e) {{
    document.getElementById('result').innerHTML =
      '<p>Invalid GeoJSON. Enter a valid GeoJSON object.</p>';
    return;
  }}
  fetch(form.action, {{
    method: 'POST',
    body: new FormData(form),
    credentials: 'same-origin'
  }}).then(function(response) {{
    if (response.redirected) {{
      window.location.href = response.url;
      return null;
    }}
    return response.text();
  }}).then(function(html) {{
    if (html !== null) {{
      document.getElementById('result').innerHTML = html;
    }}
  }}).catch(function(e) {{
    document.getElementById('result').innerHTML = '<p>Error: ' + e + '</p>';
  }});
}}
document.getElementById('report-form').addEventListener('submit', function(event) {{
  if (window.fetch && window.JSON) {{
    event.preventDefault();
    submitReport();
  }}
}});
</script>
</body>
</html>"""


@router.get("/raw-data", response_class=HTMLResponse)
def ui_raw_data_inventory(services: ServicesDep) -> str:
    sources, sources_unavailable = _raw_collect(lambda: services.source_service.list_all())
    areas, areas_unavailable = _raw_collect(lambda: services.area_service.list_all())
    evidence, evidence_unavailable = _raw_collect(lambda: services.evidence_service.list_all())
    claims, claims_unavailable = _raw_collect(lambda: services.claim_service.list_all())
    report_runs, report_runs_unavailable = _raw_collect(
        lambda: services.report_service.list_recent_report_runs(limit=_RAW_INVENTORY_LIMIT)
    )
    report_jobs, report_jobs_unavailable = _raw_collect(
        lambda: services.async_report_jobs.list_recent(limit=_RAW_INVENTORY_LIMIT)
    )
    review_items, review_items_unavailable = _raw_collect(
        lambda: services.connector_review_queue.list_connector_runs(
            limit=_RAW_INVENTORY_LIMIT
        )
    )
    live_jobs, live_jobs_unavailable = _raw_collect(
        lambda: services.live_connector_jobs.list_recent(limit=_RAW_INVENTORY_LIMIT)
    )
    summary = _html.escape(_raw_inventory_summary(services))
    sections = "".join(
        [
            _raw_inventory_section(
                "Sources",
                "Source registry records currently loaded in this runtime.",
                sources,
                sources_unavailable,
                _source_rows(sources, sources_unavailable),
            ),
            _raw_inventory_section(
                "Areas",
                "Stored AOI geometry records available to the current services.",
                areas,
                areas_unavailable,
                _area_rows(areas, areas_unavailable),
            ),
            _raw_inventory_section(
                "Evidence",
                "Stored source-failure, source-observation, and manual evidence records.",
                evidence,
                evidence_unavailable,
                _evidence_rows(evidence, evidence_unavailable),
            ),
            _raw_inventory_section(
                "Claims",
                "Interpreted claims currently stored by the claim service.",
                claims,
                claims_unavailable,
                _claim_rows(claims, claims_unavailable),
            ),
            _raw_inventory_section(
                "Report Run Contracts",
                "Bounded recent report-run contracts, independent of job queue state.",
                report_runs,
                report_runs_unavailable,
                _report_run_rows(report_runs, report_runs_unavailable),
            ),
            _raw_inventory_section(
                "Report Jobs",
                "Bounded recent async report job records.",
                report_jobs,
                report_jobs_unavailable,
                _report_job_rows(report_jobs, report_jobs_unavailable),
            ),
            _raw_inventory_section(
                "Connector Review Items",
                "Connector handoff jobs awaiting or recording fixture QA review.",
                review_items,
                review_items_unavailable,
                _review_item_rows(review_items, review_items_unavailable),
            ),
            _raw_inventory_section(
                "Live Connector Jobs",
                "Bounded recent live connector queue records.",
                live_jobs,
                live_jobs_unavailable,
                _live_job_rows(live_jobs, live_jobs_unavailable),
            ),
        ]
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Land Diligence - Raw Data Inventory</title>
<style>
{_INDEX_CSS}
.raw-shell .console-grid {{ grid-template-columns: 1fr; }}
.raw-table {{ min-width: 920px; }}
.raw-boundary {{ margin-top: 1rem; }}
</style>
</head>
<body>
<header class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <h1>Raw Data Inventory</h1>
      <span>Current runtime records only</span>
    </div>
    <nav class="console-nav" aria-label="Operator console navigation">
      <a href="/ui/">Home</a>
      <a href="/ui/report-runs">Report runs</a>
      <a href="/ui/operations">Operations</a>
      <a href="/ui/connector-review-queue">Connector review queue</a>
    </nav>
  </div>
</header>
<div class="shell raw-shell">
  <div class="status-strip" aria-label="Raw inventory summary">
    <div class="status-item">
      <strong>Runtime inventory</strong>
      <span>{summary}</span>
    </div>
    <div class="status-item">
      <strong>Read behavior</strong>
      <span>GET-only inventory display</span>
    </div>
    <div class="status-item">
      <strong>Authority boundary</strong>
      <span>No source-readiness, hosted, legal, or DS-017 claim</span>
    </div>
    <div class="status-item">
      <strong>Record limit</strong>
      <span>Recent {str(_RAW_INVENTORY_LIMIT)} where stores are ordered</span>
    </div>
  </div>
  <main class="console-grid">
    {sections}
  </main>
  <div class="note raw-boundary">
    <strong>Local raw-data inventory view only.</strong> This page reads existing
    runtime service state; it does not seed fixtures, does not create reports,
    does not run connectors, does not create accounts, does not approve DS-017,
    and does not prove hosted deployment or source-readiness authority.
  </div>
</div>
</body>
</html>"""


def _selected_county_fixture_markup(
    request: Request,
    services: ApiServices,
    csrf_field: str = "",
) -> str:
    try:
        cases = operator_cases_api.list_selected_county_case_summaries()
    except HTTPException as exc:
        detail = _html.escape(str(exc.detail))
        return (
            '<section class="panel" aria-labelledby="fixture-cases-title">'
            '<div class="panel-header"><div>'
            '<h2 id="fixture-cases-title">Selected-County Private MVP Fixture Cases</h2>'
            "<p>Fixture-case launcher unavailable.</p>"
            "</div></div>"
            '<div class="warning">'
            "<strong>Unavailable.</strong> "
            f"{detail}"
            "</div>"
            "</section>"
        )

    if not cases:
        return (
            '<section class="panel" aria-labelledby="fixture-cases-title">'
            '<div class="panel-header"><div>'
            '<h2 id="fixture-cases-title">Selected-County Private MVP Fixture Cases</h2>'
            "<p>No selected-county fixture cases are available.</p>"
            "</div></div>"
            '<div class="warning">No selected-county fixture cases are available.</div>'
            "</section>"
        )

    rows = "\n".join(
        _selected_county_case_row(case, request, services, csrf_field)
        for case in cases
    )
    case_count = len(cases)
    return f"""<section class="panel case-panel" aria-labelledby="fixture-cases-title">
  <div class="panel-header">
    <div>
      <h2 id="fixture-cases-title">Selected-County Private MVP Fixture Cases</h2>
      <p>Create approved fixture reports for the selected-county operator path.</p>
    </div>
    <span class="badge">{case_count} cases</span>
  </div>
  <div class="table-wrap">
    <table class="case-table">
      <caption>Selected-county fixture cases</caption>
      <thead>
        <tr>
          <th scope="col">Case</th>
          <th scope="col">County</th>
          <th scope="col">Intent</th>
          <th scope="col">Description</th>
          <th scope="col">Boundary</th>
          <th scope="col">Connector domains</th>
          <th scope="col">Action</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</section>"""


def _selected_county_case_row(
    case: operator_cases_api.OperatorCaseSummary,
    request: Request,
    services: ApiServices,
    csrf_field: str = "",
) -> str:
    case_id = _html.escape(case.case_id)
    county = _html.escape(case.county.title())
    state = _html.escape(case.state.upper())
    intent = _html.escape(case.intent.replace("_", " "))
    description = _html.escape(case.description)
    boundary = _case_boundary_metadata(case)
    domains = _connector_domain_badges(case.connector_domains)
    settings = cast(Settings, request.app.state.settings)
    reviewer_fields = reviewer_credential_fields(
        request,
        services,
        required_scope=REVIEWER_SCOPE_REPORT_RUN,
    )
    identity_fields = report_identity_fields(request, settings)
    return f"""<tr>
  <td data-label="Case"><span class="case-id">{case_id}</span></td>
  <td data-label="County">{county}, {state}</td>
  <td data-label="Intent">{intent}</td>
  <td data-label="Description" class="description">{description}</td>
  <td data-label="Boundary">{boundary}</td>
  <td data-label="Domains"><div class="domain-list">{domains}</div></td>
  <td data-label="Action">
    <form class="compact-form" method="POST" action="/ui/operator-cases/report">
      <input type="hidden" name="selected_county_case_id" value="{case_id}">
      {csrf_field}
      <div data-required-scope="report:run">{reviewer_fields}</div>
      <div>{identity_fields}</div>
      <button class="primary-button" type="submit"
        aria-label="Create approved report for {case_id}">
        Create report
      </button>
    </form>
  </td>
</tr>"""


def _case_boundary_metadata(case: operator_cases_api.OperatorCaseSummary) -> str:
    scope = _html.escape(case.fixture_scope.replace("_", " "))
    language = _html.escape(case.fixture_language)
    not_evaluated = _boundary_chips(case.not_evaluated_domains)
    unknowns = _boundary_chips(case.expected_unknowns)
    return (
        '<div class="boundary">'
        f"<div><strong>Scope</strong> {scope}</div>"
        f'<div class="boundary-note" title="{language}">fixture only; not live coverage</div>'
        "<div><strong>Not evaluated</strong>"
        f'<div class="boundary-list">{not_evaluated}</div></div>'
        "<div><strong>Expected unknowns</strong>"
        f'<div class="boundary-list">{unknowns}</div></div>'
        "</div>"
    )


def _boundary_chips(values: list[str]) -> str:
    if not values:
        return '<span class="boundary-chip">none declared</span>'
    return "".join(f'<span class="boundary-chip">{_html.escape(value)}</span>' for value in values)


def _connector_domain_badges(domains: list[str]) -> str:
    if not domains:
        return '<span class="domain">none declared</span>'
    return "".join(f'<span class="domain">{_html.escape(domain)}</span>' for domain in domains)


def _ui_intake_error_page(message: str, status_code: int = 422) -> HTMLResponse:
    safe_message = _html.escape(message)
    return HTMLResponse(
        content=(
            '<!DOCTYPE html><html lang="en">'
            '<head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            "<title>Custom GeoJSON Intake Error</title></head>"
            "<body><h1>Custom GeoJSON Intake Error</h1>"
            f"<p>{safe_message}</p>"
            '<p><a href="/ui/">Back to Home</a></p>'
            "</body></html>"
        ),
        status_code=status_code,
    )


@router.post("/intake", response_model=None)
def ui_custom_geojson_intake(
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
    area_geojson: Annotated[str, Form()],
    intent: Annotated[str, Form()],
    csrf_token: Annotated[str | None, Form()] = None,
) -> RedirectResponse | HTMLResponse:
    csrf_error = require_ui_csrf(request_context, csrf_token, back_url="/ui/")
    if csrf_error is not None:
        return csrf_error
    try:
        parsed_geojson = json.loads(area_geojson)
    except JSONDecodeError:
        return _ui_intake_error_page("Invalid GeoJSON. Enter a valid GeoJSON object.")
    if not isinstance(parsed_geojson, dict):
        return _ui_intake_error_page(
            "Invalid GeoJSON. The top-level GeoJSON value must be an object."
        )

    try:
        intent_code = IntentCode(intent)
    except ValueError:
        return _ui_intake_error_page(
            "Invalid report intent. Choose one of the available intent options."
        )
    try:
        intake_request = IntakeRequest(
            area_geojson=parsed_geojson,
            intent_code=intent_code,
        )
    except ValidationError:
        return _ui_intake_error_page(
            "Invalid intake payload. Check the GeoJSON object and try again."
        )

    try:
        intake_response = intake_report(
            request=intake_request,
            background_tasks=background_tasks,
            request_context=request_context,
            services=services,
            response=Response(),
        )
    except HTTPException as exc:
        return _ui_intake_error_page(str(exc.detail), status_code=exc.status_code)

    if (
        intake_response.status == "pending_connector_review"
        and intake_response.connector_ingest_run_id is not None
    ):
        return RedirectResponse(
            url=(f"/ui/connector-review-queue/{intake_response.connector_ingest_run_id}"),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    if intake_response.report_run_id is None:
        return _ui_intake_error_page(
            "Custom intake did not return a report run.",
        )
    return RedirectResponse(
        url=f"/ui/report-runs/{intake_response.report_run_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/operator-cases/report", response_model=None)
def ui_create_selected_county_report(
    request: Request,
    services: ServicesDep,
    selected_county_case_id: Annotated[str, Form()],
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    report_identity_token: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> RedirectResponse | HTMLResponse:
    csrf_error = require_ui_csrf(request, csrf_token, back_url="/ui/")
    if csrf_error is not None:
        return csrf_error
    try:
        auth_result = require_ui_reviewer(
            request,
            services,
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
            required_scope=REVIEWER_SCOPE_REPORT_RUN,
        )
    except HTTPException as exc:
        return HTMLResponse(
            content=(
                "<!DOCTYPE html><html><head><title>Authentication Error</title></head>"
                "<body><h1>Authentication Error</h1>"
                "<p>Reviewer credentials are missing, invalid, or lack the required scope.</p>"
                "<a href='/ui/'>Back to Home</a></body></html>"
            ),
            status_code=exc.status_code,
        )
    principal = auth_result.principal
    settings = cast(Settings, request.app.state.settings)
    try:
        identity_result = require_ui_report_identity(
            request,
            settings,
            report_identity_token=report_identity_token,
        )
    except HTTPException as exc:
        return error_page(
            "Workspace Identity Required",
            str(exc.detail),
            "/ui/",
            exc.status_code,
            css=_INDEX_CSS,
        )
    if identity_result is None and not settings.is_local_app_env():
        return error_page(
            "Workspace Identity Required",
            (
                "UI workspace identity is not configured for selected-county report "
                "creation outside local/dev/test environments."
            ),
            "/ui/",
            status.HTTP_403_FORBIDDEN,
            css=_INDEX_CSS,
        )
    workspace_id = (
        identity_result.auth.workspace_id
        if identity_result is not None
        else _LOCAL_UI_WORKSPACE_ID
    )
    requested_by = (
        identity_result.auth.user_id
        if identity_result is not None
        else _LOCAL_UI_USER_ID
    )
    try:
        created = operator_cases_api.create_selected_county_fixture_report_response(
            services=services,
            case_id=selected_county_case_id,
            reviewer_id=principal.reviewer_id,
            workspace_id=workspace_id,
            requested_by=requested_by,
        )
    except HTTPException as exc:
        detail = _html.escape(str(exc.detail))
        return HTMLResponse(
            content=(
                "<!DOCTYPE html><html><head><title>Fixture Report Error</title></head>"
                "<body><h1>Fixture Report Error</h1>"
                f"<p>{detail}</p>"
                "<a href='/ui/'>Back to Home</a></body></html>"
            ),
            status_code=exc.status_code,
        )
    response = RedirectResponse(
        url=created.links.ui,
        status_code=status.HTTP_303_SEE_OTHER,
    )
    attach_ui_reviewer_session_cookie(response, request, services, auth_result)
    attach_ui_report_identity_session_cookie(response, request, identity_result)
    return response


@router.get("/report-runs/{report_run_id}", response_class=HTMLResponse)
def ui_report_run(
    report_run_id: UUID,
    request: Request,
    services: ServicesDep,
    auto_refresh: Annotated[bool, Query()] = True,
    refresh_seconds: Annotated[
        int,
        Query(ge=min(_REPORT_REFRESH_SECONDS_OPTIONS), le=max(_REPORT_REFRESH_SECONDS_OPTIONS)),
    ] = _REPORT_REFRESH_SECONDS_DEFAULT,
) -> str:
    csrf_field = csrf_form_field(request)
    job = services.async_report_jobs.get(report_run_id)
    if job is not None and job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
        job_status = _html.escape(job.status.value)
        report_url = f"/ui/report-runs/{_html.escape(str(report_run_id), quote=True)}"
        refresh_meta_seconds = refresh_seconds if auto_refresh else None
        refresh_interval_form = _report_refresh_interval_form(
            report_url=report_url,
            auto_refresh=auto_refresh,
            refresh_seconds=refresh_seconds,
        )
        if auto_refresh:
            refresh_copy = f"<p>This page refreshes every {refresh_seconds} seconds.</p>"
            refresh_actions = (
                f'<a href="{report_url}'
                f'{_report_refresh_query(auto_refresh=False, refresh_seconds=refresh_seconds)}">'
                "Pause auto-refresh</a>"
            )
        else:
            refresh_copy = "<p>Auto-refresh is paused.</p>"
            refresh_actions = (
                f'<a href="{report_url}'
                f'{_report_refresh_query(auto_refresh=False, refresh_seconds=refresh_seconds)}">'
                "Refresh now</a>"
                f'<a href="{report_url}'
                f'{_report_refresh_query(refresh_seconds=refresh_seconds)}">'
                "Resume auto-refresh</a>"
            )
        return _report_page(
            title="Report Generating",
            heading="Generating Report",
            status_label="Report status",
            status_class="generating",
            report_run_id=report_run_id,
            refresh_seconds=refresh_meta_seconds,
            details_html=(
                '<div class="meta">'
                f"<div>Status: {job_status}</div>"
                f"<div>Report ID: {report_run_id}</div>"
                f"<div>Created: {_html.escape(_format_dt(job.created_at))}</div>"
                f"<div>Started: {_html.escape(_format_dt(job.started_at))}</div>"
                f"<div>Running age: {_report_job_running_age_html(job)}</div>"
                "</div>"
                f"{refresh_copy}"
            ),
            action_html=(
                "<p>Wait for processing to complete, or return to the report queue.</p>"
                '<div class="refresh-controls">'
                f"{refresh_interval_form}"
                '<div class="action-row">'
                f"{refresh_actions}"
                '<a href="/ui/report-runs">All Reports</a>'
                '<a href="/ui/">Home</a>'
                "</div>"
                "</div>"
            ),
        )
    if job is not None and job.status == JobStatus.FAILED:
        error_msg = _html.escape(safe_error_message(job.error_msg) or "Unknown error")
        job_id_esc = _html.escape(str(report_run_id))
        reviewer_fields = reviewer_credential_fields(
            request,
            services,
            required_scope=REVIEWER_SCOPE_REPORT_RETRY,
        )
        return _report_page(
            title="Report Failed",
            heading="Report Generation Failed",
            status_label="Report failed",
            status_class="failed",
            report_run_id=report_run_id,
            details_html=(
                '<div class="meta">'
                f"<div>Status: failed</div><div>Report ID: {job_id_esc}</div>"
                "</div>"
                f"<p>{error_msg}</p>"
            ),
            action_html=(
                "<p>Use a reviewer session or credentials to queue a retry.</p>"
                f'<form class="stacked-form" method="POST"'
                f' action="/ui/report-runs/{report_run_id}/retry">'
                f"{csrf_field}"
                f"{reviewer_fields}"
                '<button class="primary-action retry" type="submit">'
                "Retry Report</button>"
                "</form>"
                '<div class="action-row"><a href="/ui/report-runs">All Reports</a>'
                '<a href="/ui/">Home</a></div>'
            ),
        )
    report = services.report_service.get_report_run(report_run_id)
    if report is None:
        return _report_page(
            title="Report Not Found",
            heading="Report Not Found",
            status_label="Missing report",
            status_class="missing",
            report_run_id=report_run_id,
            details_html=(
                '<div class="meta">'
                f"<div>Report ID: {_html.escape(str(report_run_id))}</div>"
                "</div>"
                "<p>No report was found for this ID.</p>"
            ),
            action_html=(
                "<p>Return to the report list and choose an available run.</p>"
                '<div class="action-row">'
                '<a href="/ui/report-runs">All Reports</a>'
                '<a href="/ui/">Home</a>'
                "</div>"
            ),
        )
    if report.review_status != ReportReviewStatus.APPROVED:
        review_status = _html.escape(report.review_status.value)
        reviewer_fields = reviewer_credential_fields(
            request,
            services,
            required_scope=REVIEWER_SCOPE_REPORT_APPROVE,
        )
        return _report_page(
            title="Report Pending Review",
            heading="Report Pending Approval",
            status_label="Approval required",
            status_class="pending",
            report_run_id=report_run_id,
            details_html=(
                '<div class="meta">'
                f"<div>Review status: {review_status}</div>"
                f"<div>Report ID: {report_run_id}</div>"
                "</div>"
                "<p>This report has not yet been approved for release. "
                "An operator must review and approve it before the dossier "
                "is available.</p>"
            ),
            action_html=(
                "<p>Use a reviewer session or credentials to approve this report.</p>"
                f'<form class="stacked-form" method="POST"'
                f' action="/ui/report-runs/{report_run_id}/approve">'
                f"{csrf_field}"
                f"{reviewer_fields}"
                "<label>Approval reason (optional)"
                '<textarea name="reason" class="approval-reason" rows="4"></textarea></label>'
                '<button class="primary-action approve" type="submit">'
                "Approve Report</button>"
                "</form>"
                '<div class="action-row"><a href="/ui/report-runs">All Reports</a>'
                '<a href="/ui/">Home</a></div>'
            ),
        )

    dossier_md = build_rural_land_dossier(report)
    dossier_escaped = _html.escape(dossier_md)

    return _report_page(
        title=f"Report {report_run_id}",
        heading="Report Run",
        status_label="Approved report",
        status_class="approved",
        report_run_id=report_run_id,
        include_report_links=True,
        details_html=(
            '<div class="meta">'
            f"<div>ID: {report.report_run_id}</div>"
            f"<div>Status: {_html.escape(report.status.value)}</div>"
            f"<div>Intent: {_html.escape(report.intent_code.value)}</div>"
            f"<div>Review: {_html.escape(report.review_status.value)}</div>"
            "</div>"
        ),
        action_html=(
            "<p>Export, download, or inspect the evidence lineage for this report.</p>"
            '<div class="action-row">'
            f'<a href="/ui/report-runs/{report_run_id}/print">Print / Export PDF</a>'
            f'<a href="/report-runs/{report_run_id}/dossier?download=1">'
            "Download dossier (.md)</a>"
            f'<a href="/report-runs/{report_run_id}/artifact">'
            "Download report (.json)</a>"
            f'<a href="/ui/report-runs/{report_run_id}/lineage">'
            "View evidence lineage</a>"
            "</div>"
        ),
        extra_html=(
            f'<pre class="dossier">{dossier_escaped}</pre>'
            '<div class="warning">'
            "<strong>Screening Tool Only.</strong> This report does not "
            "constitute legal, title, survey, appraisal, or investment advice. "
            "All claims are subject to source limitations and require "
            "professional verification where indicated."
            "</div>"
        ),
    )


@router.get("/report-runs", response_class=HTMLResponse, response_model=None)
def ui_report_run_list(
    services: ServicesDep,
    status: Annotated[str | None, Query()] = None,
    stale: Annotated[bool, Query()] = False,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> str | HTMLResponse:
    # Validate and resolve the status filter
    status_filter: JobStatus | None = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            return error_page(
                "Invalid Status Filter",
                (
                    f"Unknown report status '{status}'. Choose one of: "
                    f"{', '.join(s.value for s in JobStatus)}."
                ),
                "/ui/report-runs",
                422,
            )
    if stale and status_filter != JobStatus.RUNNING:
        return error_page(
            "Invalid Stale Filter",
            "Stale report run filtering requires status=running.",
            "/ui/report-runs",
            422,
        )

    jobs = services.async_report_jobs.list_recent(
        limit=_UI_PAGE_SIZE,
        offset=offset,
        status=status_filter,
        stale=stale,
    )
    rows = ""
    for job in jobs:
        review_badge = ""
        report = None
        if job.status == JobStatus.SUCCEEDED:
            report = services.report_service.get_report_run(job.report_run_id)
            if report is not None:
                rv = report.review_status.value
                color = "#28a745" if rv == "approved" else "#ffc107"
                review_badge = (
                    f' &nbsp; <span style="color:{color};font-weight:bold">'
                    f"{_html.escape(rv)}</span>"
                )
        status_color = {
            "queued": "#6c757d",
            "running": "#007bff",
            "succeeded": "#28a745",
            "failed": "#dc3545",
        }.get(job.status.value, "#333")
        rid_esc = _html.escape(str(job.report_run_id))
        action_html = _report_list_next_action_html(
            job.report_run_id,
            job.status,
            report.review_status if report is not None else None,
            has_report=report is not None,
        )
        running_age = _report_job_running_age_html(job)
        rows += (
            f"<tr>"
            f'<td data-label="Select" style="text-align:center">'
            f'<input type="checkbox" class="cmp-check" name="ids" value="{rid_esc}"'
            f' aria-label="Select {rid_esc[:8]}"></td>'
            f'<td data-label="ID"><a href="/ui/report-runs/{job.report_run_id}">'
            f"{_html.escape(str(job.report_run_id)[:8])}&#8230;</a></td>"
            f'<td data-label="Intent">{_html.escape(job.intent_code.value)}</td>'
            f'<td data-label="Status" style="color:{status_color}">'
            f"{_html.escape(job.status.value)}{review_badge}</td>"
            f'<td data-label="Created">{_html.escape(str(job.created_at)[:19])}</td>'
            f'<td data-label="Running Age">{running_age}</td>'
            f'<td data-label="Action">{action_html}</td>'
            f"</tr>\n"
        )
    if not rows:
        empty_text = "No stale running report runs." if stale else "No report runs yet."
        rows = f'<tr><td colspan="7" style="color:#666">{_html.escape(empty_text)}</td></tr>'

    # Build status filter dropdown
    status_options = '<option value="">All</option>\n'
    for js in JobStatus:
        selected = " selected" if status_filter == js else ""
        status_options += (
            f'<option value="{_html.escape(js.value)}"{selected}>'
            f"{_html.escape(js.value)}</option>\n"
        )

    # Build query string helpers for pagination links
    def _page_qs(new_offset: int) -> str:
        parts = []
        if status_filter is not None:
            parts.append(f"status={_html.escape(status_filter.value)}")
        if stale:
            parts.append("stale=true")
        parts.append(f"offset={new_offset}")
        return "?" + "&amp;".join(parts)

    prev_link = ""
    if offset > 0:
        prev_offset = max(0, offset - _UI_PAGE_SIZE)
        prev_link = f'<a href="/ui/report-runs{_page_qs(prev_offset)}">&larr; Previous</a>'
    next_link = ""
    if len(jobs) == _UI_PAGE_SIZE:
        next_offset = offset + _UI_PAGE_SIZE
        next_link = f'<a href="/ui/report-runs{_page_qs(next_offset)}">Next &rarr;</a>'
    pagination = ""
    if prev_link or next_link:
        sep = " &nbsp; " if (prev_link and next_link) else ""
        pagination = f'<div style="margin-top:1rem">{prev_link}{sep}{next_link}</div>'
    stale_checked = " checked" if stale else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report Runs</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }}
h1 {{ color: #2c3e50; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ text-align: left; padding: 0.5rem 1rem; border-bottom: 1px solid #dee2e6; }}
th {{ background: #f8f9fa; }}
a {{ color: #2c3e50; }}
.report-list-nav {{
  align-items:center; display:flex; flex-wrap:wrap; gap:0.35rem 0.5rem;
  margin-bottom:1rem;
}}
.report-list-nav a {{ min-width:0; overflow-wrap:anywhere; }}
.report-list-nav .sep {{ color:#666; }}
form.filter {{ display:inline-flex; gap:0.5rem; align-items:center; margin-bottom:1rem; }}
.cmp-bar {{ margin-bottom:0.75rem; display:flex; flex-wrap:wrap; gap:0.5rem; align-items:center; }}
.cmp-help {{ color:#666; font-size:0.9rem; }}
.report-table-wrap {{ overflow-x:auto; }}
.report-runs-table {{ min-width:920px; }}
.report-actions {{ display:flex; flex-wrap:wrap; gap:0.35rem; min-width:10rem; }}
.report-actions a {{ border:1px solid #dee2e6; border-radius:4px;
  padding:0.2rem 0.35rem; text-decoration:none; white-space:nowrap; }}
@media (max-width:640px) {{
  .report-list-nav {{ align-items:flex-start; flex-direction:column; }}
  .report-list-nav .sep {{ display:none; }}
  .report-table-wrap {{ overflow-x:visible; }}
  .report-runs-table {{ min-width:0; }}
  .report-runs-table thead {{
    border:0;
    clip:rect(0 0 0 0);
    clip-path:inset(50%);
    height:1px;
    margin:-1px;
    overflow:hidden;
    padding:0;
    position:absolute;
    white-space:nowrap;
    width:1px;
  }}
  .report-runs-table, .report-runs-table tbody, .report-runs-table tr,
  .report-runs-table td {{ display:block; width:100%; }}
  .report-runs-table tr {{ border-bottom:1px solid #dee2e6; padding:0.65rem 0; }}
  .report-runs-table tr:last-child {{ border-bottom:0; }}
  .report-runs-table td {{
    border-bottom:0;
    min-width:0;
    overflow-wrap:anywhere;
    padding:0.35rem 0.5rem;
    text-align:left !important;
  }}
  .report-runs-table td::before {{
    color:#666;
    content:attr(data-label);
    display:block;
    font-size:0.72rem;
    font-weight:700;
    margin-bottom:0.18rem;
    text-transform:uppercase;
  }}
  .report-actions {{ min-width:0; }}
  .report-actions a {{ white-space:normal; }}
}}
</style>
</head>
<body>
<nav class="report-list-nav" aria-label="Report list navigation">
  <a href="/ui/">&#8592; Home</a>
  <span class="sep" aria-hidden="true">|</span>
  <a href="/ui/operations">Operations Dashboard</a>
  <span class="sep" aria-hidden="true">|</span>
  <a href="/ui/connector-review-queue">Connector review queue</a>
</nav>
<h1>Report Runs</h1>
<form class="filter" method="GET" action="/ui/report-runs">
  <label for="status-filter">Filter by status:</label>
  <select id="status-filter" name="status">
    {status_options}
  </select>
  <label><input type="checkbox" name="stale" value="true"{stale_checked}> Stale running</label>
  <button type="submit">Apply</button>
</form>
<form method="GET" action="/ui/compare">
<div class="cmp-bar">
  <button id="cmp-btn" type="submit"
    style="background:#2c3e50;color:white;border:none;padding:0.4rem 1rem;
           cursor:pointer;font-size:0.9rem;border-radius:4px">
    Compare Selected (2&#8211;4)
  </button>
  <span class="cmp-help">Select 2&#8211;4 report rows.</span>
</div>
<div class="report-table-wrap">
<table class="report-runs-table">
<thead><tr>
  <th style="width:2rem;text-align:center">
    <abbr title="Select 2&#8211;4 rows then click Compare">&#9745;</abbr>
  </th>
  <th>ID</th><th>Intent</th><th>Status</th><th>Created</th>
  <th>Running Age</th><th>Action</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
</form>
{pagination}
</body></html>"""


_COMPARE_CSS = (
    "body { font-family: system-ui, sans-serif; max-width: 1100px; margin: 2rem auto; padding: 0 1rem; }\n"  # noqa: E501
    "h1 { color: #2c3e50; }\n"
    "h2 { color: #34495e; margin-top: 1.5rem; }\n"
    "table { border-collapse: collapse; width: 100%; }\n"
    "th, td { text-align: left; padding: 0.5rem 0.75rem; border: 1px solid #dee2e6; }\n"
    "th { background: #f8f9fa; }\n"
    "th.run-header a { color: #2c3e50; font-size: 0.85rem; word-break: break-all; }\n"
    "td.metric { background: #f8f9fa; font-weight: bold; width: 180px; }\n"
    ".compare-table-wrap { overflow-x: auto; }\n"
    ".compare-table { min-width: 760px; }\n"
    ".compare-table td, .compare-table th { overflow-wrap: anywhere; }\n"
    ".actions { display: flex; flex-wrap: wrap; gap: 0.35rem; }\n"
    ".actions a { border: 1px solid #dee2e6; border-radius: 4px; padding: 0.2rem 0.35rem; text-decoration: none; }\n"  # noqa: E501
    ".claim-list { margin: 0; padding-left: 1rem; }\n"
    ".claim-list li { margin: 0.15rem 0; overflow-wrap: anywhere; }\n"
    ".muted { color: #666; }\n"
    ".change-review { margin-top: 1.25rem; }\n"
    ".change-review table { margin-top: 0.5rem; }\n"
    ".warning { background: #fff3cd; border: 1px solid #ffc107; padding: 1rem;"
    " border-radius: 4px; margin-top: 2rem; font-size: 0.9rem; }\n"
    ".error { background: #f8d7da; border: 1px solid #dc3545; padding: 1rem;"
    " border-radius: 4px; margin-top: 1rem; }\n"
)


def _compare_action_links(report: ReportRunContract) -> str:
    report_run_id = report.report_run_id
    detail_href = f"/ui/report-runs/{report_run_id}"
    if report.review_status == ReportReviewStatus.APPROVED:
        links = [
            (detail_href, "View dossier"),
            (f"/ui/report-runs/{report_run_id}/print", "Print / Export PDF"),
            (f"/report-runs/{report_run_id}/dossier?download=1", "Download dossier"),
            (f"/report-runs/{report_run_id}/artifact", "Download JSON"),
            (f"/ui/report-runs/{report_run_id}/lineage", "Lineage"),
        ]
    else:
        links = [(detail_href, "Approve from detail")]
    rendered = "".join(
        f'<a href="{_html.escape(href, quote=True)}">{_html.escape(label)}</a>'
        for href, label in links
    )
    return f'<div class="actions">{rendered}</div>'


def _compare_delivery_status(report: ReportRunContract) -> str:
    if report.review_status == ReportReviewStatus.APPROVED:
        return "Delivery available"
    return "Approval required"


def _compare_high_severity_html(claims: list[dict[str, str]]) -> str:
    if not claims:
        return '<span class="muted">None</span>'
    items = ""
    for claim in claims:
        code = _html.escape(claim.get("claim_code", "unknown"))
        domain = _html.escape(claim.get("domain", "unknown"))
        items += f'<li><code>{code}</code> <span class="muted">({domain})</span></li>'
    return f'<ul class="claim-list">{items}</ul>'


def _compare_joined_values(values: list[str]) -> str:
    if not values:
        return '<span class="muted">None</span>'
    return ", ".join(_html.escape(value) for value in values)


def _build_ui_report_diff(
    report: ReportRunContract,
    base: ReportRunContract,
) -> ReportRunDiffResponse:
    all_report_claims = list(report.claims) + list(report.unknowns) + list(report.red_flags)
    all_base_claims = list(base.claims) + list(base.unknowns) + list(base.red_flags)
    report_codes = {claim.claim_code for claim in all_report_claims}
    base_codes = {claim.claim_code for claim in all_base_claims}
    report_sources = set(report.source_manifest.keys())
    base_sources = set(base.source_manifest.keys())
    report_rulesets = {claim.ruleset_id for claim in all_report_claims if claim.ruleset_id}
    base_rulesets = {claim.ruleset_id for claim in all_base_claims if claim.ruleset_id}
    return ReportRunDiffResponse(
        report_run_id=report.report_run_id,
        base_report_run_id=base.report_run_id,
        area_id=report.area_id,
        same_area=True,
        ruleset_changed=report_rulesets != base_rulesets,
        added_claim_codes=sorted(report_codes - base_codes),
        removed_claim_codes=sorted(base_codes - report_codes),
        added_sources=sorted(report_sources - base_sources),
        removed_sources=sorted(base_sources - report_sources),
        evidence_count_delta=len(report.evidence) - len(base.evidence),
    )


def _compare_change_review_html(reports: list[ReportRunContract]) -> str:
    if len(reports) != 2:
        return ""
    base, report = reports
    if base.area_id != report.area_id:
        return (
            '<section class="change-review" aria-labelledby="change-review-title">'
            '<h2 id="change-review-title">Change Review</h2>'
            '<p class="muted">Change review requires the same area. '
            "The side-by-side counts above remain available for cross-area comparison.</p>"
            "</section>"
        )
    diff = _build_ui_report_diff(report, base)

    def _row(label: str, value_html: str) -> str:
        return f'<tr><td class="metric">{_html.escape(label)}</td><td>{value_html}</td></tr>\n'

    rows = ""
    rows += _row("Same Area", "Yes")
    rows += _row("Ruleset Changed", "Yes" if diff.ruleset_changed else "No")
    rows += _row("Added Claim Codes", _compare_joined_values(diff.added_claim_codes))
    rows += _row("Removed Claim Codes", _compare_joined_values(diff.removed_claim_codes))
    rows += _row("Added Sources", _compare_joined_values(diff.added_sources))
    rows += _row("Removed Sources", _compare_joined_values(diff.removed_sources))
    rows += _row("Evidence Count Delta", _html.escape(str(diff.evidence_count_delta)))
    return (
        '<section class="change-review" aria-labelledby="change-review-title">'
        '<h2 id="change-review-title">Change Review</h2>'
        "<table><tbody>"
        f"{rows}"
        "</tbody></table>"
        "</section>"
    )


@router.get("/compare", response_class=HTMLResponse)
def ui_compare_report_runs(
    ids: Annotated[list[str] | None, Query()] = None,
    *,
    services: ServicesDep,
) -> HTMLResponse:
    """Side-by-side comparison table for 2..4 report run IDs."""
    nav = '<a href="/ui/">&#8592; Home</a> &nbsp;|&nbsp; <a href="/ui/report-runs">All Reports</a>'

    def _error_page(message: str, http_status: int) -> HTMLResponse:
        body = (
            f'<!DOCTYPE html><html lang="en">'
            f'<head><meta charset="UTF-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>Compare Error</title>"
            f"<style>{_COMPARE_CSS}</style></head>"
            f"<body>{nav}<h1>Compare Report Runs</h1>"
            f'<div class="error"><strong>Error:</strong> {_html.escape(message)}</div>'
            f"</body></html>"
        )
        return HTMLResponse(content=body, status_code=http_status)

    if not ids:
        return _error_page("at least 2 report run IDs are required for comparison", 400)

    try:
        run_ids = _parse_compare_ids(",".join(ids))
    except HTTPException as exc:
        return _error_page(str(exc.detail), exc.status_code)

    reports: list[ReportRunContract] = []
    summaries = []
    for run_id in run_ids:
        report = services.report_service.get_report_run(run_id)
        if report is None:
            return _error_page(f"report run '{run_id}' not found", 404)
        reports.append(report)
        summaries.append(_build_comparison_summary(report))

    # Build column headers — each links to the individual report page
    col_headers = ""
    for s in summaries:
        rid_str = _html.escape(str(s.report_run_id))
        col_headers += (
            f'<th class="run-header">'
            f'<a href="/ui/report-runs/{rid_str}">{rid_str[:8]}&#8230;</a>'
            f"</th>"
        )

    def _metric_row(label: str, values: list[str]) -> str:
        cells = "".join(f"<td>{_html.escape(v)}</td>" for v in values)
        return f'<tr><td class="metric">{_html.escape(label)}</td>{cells}</tr>\n'

    rows = ""
    rows += _metric_row("Area ID", [str(s.area_id)[:8] + "…" for s in summaries])
    rows += _metric_row("Intent", [s.intent_code for s in summaries])
    rows += _metric_row("Report Status", [r.status.value for r in reports])
    rows += _metric_row("Review Status", [r.review_status.value for r in reports])
    rows += _metric_row("Delivery Status", [_compare_delivery_status(r) for r in reports])
    rows += _metric_row("Claims", [str(s.claims_count) for s in summaries])
    rows += _metric_row("Unknowns", [str(s.unknowns_count) for s in summaries])
    rows += _metric_row("Red Flags", [str(s.red_flags_count) for s in summaries])
    rows += _metric_row("Verification Tasks", [str(s.verification_tasks_count) for s in summaries])
    rows += _metric_row(
        "High-Severity Claims", [str(len(s.high_severity_claims)) for s in summaries]
    )
    rows += (
        '<tr><td class="metric">High-Severity Details</td>'
        + "".join(
            f"<td>{_compare_high_severity_html(s.high_severity_claims)}</td>" for s in summaries
        )
        + "</tr>\n"
    )
    rows += (
        '<tr><td class="metric">Next Action</td>'
        + "".join(f"<td>{_compare_action_links(report)}</td>" for report in reports)
        + "</tr>\n"
    )
    change_review_html = _compare_change_review_html(reports)

    body = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Compare Report Runs</title>
<style>
{_COMPARE_CSS}
</style></head>
<body>
{nav}
<h1>Compare Report Runs</h1>
<div class="compare-table-wrap">
<table class="compare-table">
<thead>
<tr><th>Metric</th>{col_headers}</tr>
</thead>
<tbody>
{rows}</tbody>
</table>
</div>
{change_review_html}
<div class="warning">
  <strong>Screening Tool Only.</strong> Counts reflect unapproved and approved reports.
  Report content is available only for approved reports.
</div>
</body></html>"""
    return HTMLResponse(content=body, status_code=200)


@router.post(
    "/report-runs/{report_run_id}/approve",
    response_class=HTMLResponse,
    response_model=None,
)
def ui_approve_report_run(
    report_run_id: UUID,
    request: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    reason: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> RedirectResponse | HTMLResponse:
    back_url = f"/ui/report-runs/{report_run_id}"
    csrf_error = require_ui_csrf(request, csrf_token, back_url=back_url)
    if csrf_error is not None:
        return csrf_error
    try:
        auth_result = require_ui_reviewer(
            request,
            services,
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
            required_scope=REVIEWER_SCOPE_REPORT_APPROVE,
        )
    except HTTPException as exc:
        error_body = (
            "<!DOCTYPE html><html><head><title>Authentication Error</title></head>"
            "<body><h1>Authentication Error</h1>"
            "<p>Reviewer credentials are missing, invalid, or lack the required scope.</p>"
            f"<a href='/ui/report-runs/{report_run_id}'>Back</a></body></html>"
        )
        return HTMLResponse(content=error_body, status_code=exc.status_code)
    principal = auth_result.principal
    report = services.report_service.get_report_run(report_run_id)
    if report is None:
        return HTMLResponse(
            content=(
                "<!DOCTYPE html><html><head><title>Not Found</title></head>"
                f"<body><h1>Report Not Found</h1><p>ID: {report_run_id}</p>"
                "<a href='/ui/report-runs'>Back to List</a></body></html>"
            ),
            status_code=200,
        )
    approval_reason = reason.strip() if reason is not None else None
    services.report_service.approve_report_run(
        report_run_id,
        reviewer_id=principal.reviewer_id,
        reason=approval_reason or None,
    )
    response = RedirectResponse(
        url=f"/ui/report-runs/{report_run_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    attach_ui_reviewer_session_cookie(response, request, services, auth_result)
    return response


@router.post(
    "/report-runs/{report_run_id}/retry",
    response_class=HTMLResponse,
    response_model=None,
)
def ui_retry_report_run(
    report_run_id: UUID,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
    csrf_token: Annotated[str | None, Form()] = None,
) -> RedirectResponse | HTMLResponse:
    failed_url = f"/ui/report-runs/{report_run_id}"
    csrf_error = require_ui_csrf(request_context, csrf_token, back_url=failed_url)
    if csrf_error is not None:
        return csrf_error
    try:
        auth_result = require_ui_reviewer(
            request_context,
            services,
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
            required_scope=REVIEWER_SCOPE_REPORT_RETRY,
        )
    except HTTPException as exc:
        error_body = (
            "<!DOCTYPE html><html><head><title>Authentication Error</title></head>"
            "<body><h1>Authentication Error</h1>"
            "<p>Reviewer credentials are missing, invalid, or lack the required scope.</p>"
            f"<a href='{_html.escape(failed_url)}'>Back</a></body></html>"
        )
        return HTMLResponse(content=error_body, status_code=exc.status_code)
    failed_job = services.async_report_jobs.get(report_run_id)
    if failed_job is None:
        return HTMLResponse(
            content=(
                "<!DOCTYPE html><html><head><title>Not Found</title></head>"
                f"<body><h1>Report Job Not Found</h1><p>ID: {report_run_id}</p>"
                "<a href='/ui/report-runs'>Back to List</a></body></html>"
            ),
            status_code=404,
        )
    if failed_job.status != JobStatus.FAILED:
        return HTMLResponse(
            content=(
                "<!DOCTYPE html><html><head><title>Conflict</title></head>"
                "<body><h1>Retry Not Available</h1>"
                "<p>Retry requires a failed report job.</p>"
                f"<a href='{_html.escape(failed_url)}'>Back</a></body></html>"
            ),
            status_code=409,
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
            failed_url,
            exc.status_code,
        )
    retry_job = services.async_report_jobs.create(
        area_id=failed_job.area_id,
        intent_code=failed_job.intent_code,
        retry_of_report_run_id=failed_job.report_run_id,
    )
    schedule_report_background(
        background_tasks=background_tasks,
        request_context=request_context,
        services=services,
        report_run_id=retry_job.report_run_id,
        area_id=retry_job.area_id,
        intent_code=retry_job.intent_code,
    )
    new_url = f"/ui/report-runs/{retry_job.report_run_id}"
    response = RedirectResponse(
        url=new_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )
    attach_ui_reviewer_session_cookie(response, request_context, services, auth_result)
    return response


_PRINT_CSS = (
    "body { font-family: Georgia, serif; max-width: 860px; margin: 2rem auto; padding: 0 1.5rem; font-size: 11pt; }\n"  # noqa: E501
    "h1, h2, h3 { color: #1a1a1a; }\n"
    "h2 { border-bottom: 1px solid #ccc; padding-bottom: 0.25rem; page-break-after: avoid; }\n"
    "pre { white-space: pre-wrap; font-family: inherit; line-height: 1.7; }\n"
    ".caveat { background: #fffbe6; border: 1px solid #e6c200; padding: 0.75rem; border-radius: 4px; font-size: 9pt; }\n"  # noqa: E501
    ".no-print { margin-bottom: 1rem; }\n"
    "@media print { .no-print { display: none; } body { margin: 0; padding: 1cm; } }\n"
)


@router.get("/report-runs/{report_run_id}/print", response_class=HTMLResponse)
def ui_print_report_run(
    report_run_id: UUID,
    services: ServicesDep,
) -> str:
    report = services.report_service.get_report_run(report_run_id)
    if report is None:
        return _report_page(
            title="Not Found",
            heading="Report Not Found",
            status_label="Not Found",
            status_class="missing",
            report_run_id=report_run_id,
            details_html=f"<p>ID: {_html.escape(str(report_run_id))}</p>",
            action_html=(
                '<div class="action-row">'
                '<a href="/ui/report-runs">Back to List</a>'
                '<a href="/ui/">Home</a>'
                "</div>"
            ),
        )
    if report.review_status != ReportReviewStatus.APPROVED:
        return _report_page(
            title="Not Approved",
            heading="Report Not Yet Approved",
            status_label="Not Approved",
            status_class="pending",
            report_run_id=report_run_id,
            details_html="<p>This report must be approved before it can be exported.</p>",
            action_html=(
                '<div class="action-row">'
                f'<a href="/ui/report-runs/{report_run_id}">Back</a>'
                '<a href="/ui/report-runs">All Reports</a>'
                "</div>"
            ),
        )
    dossier_md = build_rural_land_dossier(report)
    dossier_escaped = _html.escape(dossier_md)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dossier — {report_run_id}</title>
<style>
{_PRINT_CSS}
</style>
</head>
<body>
<div class="no-print">
  <button onclick="window.print()"
    style="padding:0.5rem 1.5rem;font-size:1rem;cursor:pointer">Print / Save as PDF</button>
  &nbsp; <a href="/ui/report-runs/{report_run_id}">&#8592; Back to Report</a>
</div>
<pre>{dossier_escaped}</pre>
<div class="caveat">
  <strong>Screening Tool Only.</strong> This report does not constitute legal, title,
  survey, appraisal, or investment advice. All claims require professional verification
  where indicated.
</div>
</body></html>"""
