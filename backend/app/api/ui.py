from __future__ import annotations

import html as _html
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from app.api.dependencies import ApiServices, get_services
from app.api.reports import _build_comparison_summary, schedule_report_background
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_REPORT_APPROVE,
    REVIEWER_SCOPE_REPORT_RETRY,
    require_reviewer_scope,
)
from app.domain.enums import JobStatus, ReportReviewStatus
from app.reports.dossier import build_rural_land_dossier

_UI_PAGE_SIZE = 30

router = APIRouter(prefix="/ui", tags=["ui"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]

_INTENT_OPTIONS = [
    ("rural_land_purchase", "Rural Land Purchase"),
    ("homestead_feasibility", "Homestead Feasibility"),
]
_GEOJSON_PLACEHOLDER = '{"type":"Polygon","coordinates":[[...]]}'

_INDEX_CSS = """\
body { font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
h1 { color: #2c3e50; }
form { display: flex; flex-direction: column; gap: 1rem; max-width: 600px; }
textarea { font-family: monospace; height: 200px; width: 100%; }
select, input, button { padding: 0.5rem; font-size: 1rem; }
button { background: #2c3e50; color: white; border: none; cursor: pointer; padding: 0.75rem; }
.note { color: #666; font-size: 0.9rem; margin-top: 2rem; border-top: 1px solid #eee; padding-top: 1rem; }"""  # noqa: E501

_REPORT_CSS = (
    "body { font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }\n"  # noqa: E501
    "h1 { color: #2c3e50; } h2 { color: #34495e; border-bottom: 1px solid #eee; }\n"
    "ul { line-height: 1.8; }\n"
    ".meta { background: #f8f9fa; padding: 1rem; border-radius: 4px; font-family: monospace; font-size: 0.9rem; }\n"  # noqa: E501
    ".warning { background: #fff3cd; border: 1px solid #ffc107; padding: 1rem; border-radius: 4px; margin-top: 2rem; }\n"  # noqa: E501
    "pre.dossier { white-space: pre-wrap; font-family: system-ui, sans-serif; line-height: 1.6; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 1.5rem; margin-top: 1rem; font-size: 0.95rem; }"  # noqa: E501
)


@router.get("/", response_class=HTMLResponse)
def ui_index() -> str:
    intent_options = "\n".join(
        f'<option value="{val}">{label}</option>'
        for val, label in _INTENT_OPTIONS
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Land Diligence — Report</title>
<style>
{_INDEX_CSS}
</style>
</head>
<body>
<h1>Land Diligence</h1>
<p>Submit an area of interest to generate a due-diligence report. &nbsp;
<a href="/ui/report-runs">View all report runs &rarr;</a></p>
<h2>Create Report</h2>
<form id="report-form">
  <label>Area GeoJSON (Polygon or MultiPolygon):
    <textarea name="area_geojson" placeholder='{_GEOJSON_PLACEHOLDER}' required></textarea>
  </label>
  <label>Intent:
    <select name="intent">{intent_options}</select>
  </label>
  <button type="button" onclick="submitReport()">Generate Report</button>
</form>
<div id="result"></div>
<script>
function submitReport() {{
  var geojson = document.querySelector('[name=area_geojson]').value;
  var intent = document.querySelector('[name=intent]').value;
  fetch('/intake', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{area_geojson: JSON.parse(geojson), intent_code: intent}})
  }}).then(r => r.json()).then(function(data) {{
    var id = data.report_run_id;
    if (id) {{
      window.location.href = '/ui/report-runs/' + id;
    }} else if (data.status === 'pending_connector_review' && data.connector_ingest_run_id) {{
      var queueUrl = '/ui/connector-review-queue/' + data.connector_ingest_run_id;
      var el = document.getElementById('result');
      var box = document.createElement('div');
      var boxStyle = 'background:#fff3cd;border:1px solid #ffc107;'
        + 'padding:1rem;border-radius:4px;margin-top:1rem';
      box.setAttribute('style', boxStyle);
      var heading = document.createElement('strong');
      heading.appendChild(document.createTextNode('Connector Review Required'));
      box.appendChild(heading);
      var p1 = document.createElement('p');
      p1.appendChild(document.createTextNode(
        'This area requires connector data review before a report can be generated.'));
      box.appendChild(p1);
      var p2 = document.createElement('p');
      p2.appendChild(document.createTextNode('Status: '));
      var statusStrong = document.createElement('strong');
      statusStrong.appendChild(document.createTextNode(data.connector_review_status || 'pending'));
      p2.appendChild(statusStrong);
      box.appendChild(p2);
      var p3 = document.createElement('p');
      var link = document.createElement('a');
      link.href = queueUrl;
      link.appendChild(document.createTextNode('View in Connector Review Queue →'));
      p3.appendChild(link);
      box.appendChild(p3);
      el.innerHTML = '';
      el.appendChild(box);
    }} else {{
      var el = document.getElementById('result');
      el.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    }}
  }}).catch(function(e) {{
    document.getElementById('result').innerHTML = '<p>Error: ' + e + '</p>';
  }});
}}
</script>
<div class="note">
  <strong>Note:</strong> This interface is a screening tool only. All outputs are subject
  to limitations documented in the source appendix.
  Reports do not constitute legal, title, survey, zoning, or appraisal determinations.
  See <a href="/docs">API documentation</a> for full capabilities and caveats.
</div>
</body>
</html>"""


@router.get("/report-runs/{report_run_id}", response_class=HTMLResponse)
def ui_report_run(
    report_run_id: UUID,
    services: ServicesDep,
) -> str:
    job = services.async_report_jobs.get(report_run_id)
    if job is not None and job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
        return (
            "<!DOCTYPE html>\n"
            "<html><head><title>Report Generating</title>"
            "<meta http-equiv='refresh' content='3'></head>\n"
            f"<body><h1>Generating Report</h1>"
            f"<p>Status: <strong>{job.status.value}</strong></p>"
            f"<p>Report ID: {report_run_id}</p>"
            "<p>This page will refresh automatically.</p>"
            "<a href=\"/ui/\">Back to Home</a></body></html>"
        )
    if job is not None and job.status == JobStatus.FAILED:
        error_msg = _html.escape(job.error_msg or "Unknown error")
        job_id_esc = _html.escape(str(report_run_id))
        return (
            "<!DOCTYPE html>\n"
            "<html><head><title>Report Failed</title></head>\n"
            "<body>"
            "<h1>Report Generation Failed</h1>"
            f"<p>{error_msg}</p>"
            f"<p>Report ID: {job_id_esc}</p>"
            "<a href=\"/ui/\">Back to Home</a>"
            " &nbsp; <a href=\"/ui/report-runs\">All Reports</a>"
            "<br><br>"
            "<h2>Retry Report</h2>"
            "<p>Reviewer credentials required to queue a retry.</p>"
            f"<form method=\"POST\""
            f" action=\"/ui/report-runs/{report_run_id}/retry\""
            " style=\"display:flex;flex-direction:column;gap:0.5rem;max-width:320px\">"
            "<label>Reviewer ID:"
            " <input type=\"text\" name=\"reviewer_id\" required"
            " style=\"display:block;width:100%;padding:0.4rem;font-size:1rem\"></label>"
            "<label>Reviewer token:"
            " <input type=\"password\" name=\"reviewer_token\" required"
            " style=\"display:block;width:100%;padding:0.4rem;font-size:1rem\"></label>"
            "<button type=\"submit\""
            " style=\"background:#007bff;color:white;border:none;"
            "padding:0.5rem 1rem;cursor:pointer;"
            "font-size:1rem;border-radius:4px\">Retry Report</button>"
            "</form>"
            "</body></html>"
        )
    report = services.report_service.get_report_run(report_run_id)
    if report is None:
        return (
            "<!DOCTYPE html>\n"
            "<html><head><title>Report Not Found</title></head>\n"
            f"<body><h1>Report Not Found</h1><p>No report found for ID: {report_run_id}</p>\n"
            "<a href=\"/ui/\">Back to Home</a></body></html>"
        )
    if report.review_status != ReportReviewStatus.APPROVED:
        return (
            "<!DOCTYPE html>\n"
            "<html><head><title>Report Pending Review</title></head>\n"
            "<body><h1>Report Pending Approval</h1>"
            "<p>This report has not yet been approved for release. "
            "An operator must review and approve it before the dossier is available.</p>"
            f"<p>Review status: <strong>{_html.escape(report.review_status.value)}</strong></p>"
            f"<p>Report ID: {report_run_id}</p>"
            "<a href=\"/ui/\">Back to Home</a>"
            f" &nbsp; <a href=\"/ui/report-runs\">All Reports</a>"
            f"<br><br>"
            f"<form method=\"POST\""
            f" action=\"/ui/report-runs/{report_run_id}/approve\""
            " style=\"display:flex;flex-direction:column;gap:0.5rem;max-width:320px\">"
            "<label>Reviewer ID:"
            " <input type=\"text\" name=\"reviewer_id\" required"
            " style=\"display:block;width:100%;padding:0.4rem;font-size:1rem\"></label>"
            "<label>Reviewer token:"
            " <input type=\"password\" name=\"reviewer_token\" required"
            " style=\"display:block;width:100%;padding:0.4rem;font-size:1rem\"></label>"
            "<button type=\"submit\""
            " style=\"background:#28a745;color:white;border:none;"
            "padding:0.5rem 1rem;cursor:pointer;"
            "font-size:1rem;border-radius:4px\">Approve Report</button>"
            "</form>"
            "</body></html>"
        )

    dossier_md = build_rural_land_dossier(report)
    dossier_escaped = _html.escape(dossier_md)

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Report {report_run_id}</title>
<style>
{_REPORT_CSS}
</style></head>
<body>
<a href="/ui/">&#8592; Back</a>&nbsp;|&nbsp;
<a href="/ui/report-runs">All Reports</a>&nbsp;|&nbsp;
<a href="/ui/report-runs/{report_run_id}/print">Print / Export PDF</a>&nbsp;|&nbsp;
<a href="/report-runs/{report_run_id}/dossier?download=1">Download dossier (.md)</a>&nbsp;|&nbsp;
<a href="/report-runs/{report_run_id}/artifact">Download report (.json)</a>&nbsp;|&nbsp;
<a href="/ui/report-runs/{report_run_id}/lineage">View evidence lineage</a>
<h1>Report Run</h1>
<div class="meta">
  <div>ID: {report.report_run_id}</div>
  <div>Status: {report.status.value}</div>
  <div>Intent: {report.intent_code.value}</div>
  <div>Review: {report.review_status.value}</div>
</div>
<pre class="dossier">{dossier_escaped}</pre>
<div class="warning">
  <strong>Screening Tool Only.</strong> This report does not constitute legal, title,
  survey, appraisal, or investment advice.
  All claims are subject to source limitations and require professional verification
  where indicated.
</div>
</body></html>"""


@router.get("/report-runs", response_class=HTMLResponse)
def ui_report_run_list(
    services: ServicesDep,
    status: Annotated[str | None, Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> str:
    # Validate and resolve the status filter
    status_filter: JobStatus | None = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            status_filter = None

    jobs = services.async_report_jobs.list_recent(
        limit=_UI_PAGE_SIZE,
        offset=offset,
        status=status_filter,
    )
    rows = ""
    for job in jobs:
        review_badge = ""
        if job.status == JobStatus.SUCCEEDED:
            report = services.report_service.get_report_run(job.report_run_id)
            if report is not None:
                rv = report.review_status.value
                color = "#28a745" if rv == "approved" else "#ffc107"
                review_badge = (
                    f' &nbsp; <span style="color:{color};font-weight:bold">'
                    f'{_html.escape(rv)}</span>'
                )
        status_color = {
            "queued": "#6c757d",
            "running": "#007bff",
            "succeeded": "#28a745",
            "failed": "#dc3545",
        }.get(job.status.value, "#333")
        rid_esc = _html.escape(str(job.report_run_id))
        rows += (
            f'<tr>'
            f'<td style="text-align:center">'
            f'<input type="checkbox" class="cmp-check" value="{rid_esc}"'
            f' aria-label="Select {rid_esc[:8]}"></td>'
            f'<td><a href="/ui/report-runs/{job.report_run_id}">'
            f'{_html.escape(str(job.report_run_id)[:8])}&#8230;</a></td>'
            f'<td>{_html.escape(job.intent_code.value)}</td>'
            f'<td style="color:{status_color}">'
            f'{_html.escape(job.status.value)}{review_badge}</td>'
            f'<td>{_html.escape(str(job.created_at)[:19])}</td>'
            f'</tr>\n'
        )
    if not rows:
        rows = '<tr><td colspan="5" style="color:#666">No report runs yet.</td></tr>'

    # Build status filter dropdown
    status_options = '<option value="">All</option>\n'
    for js in JobStatus:
        selected = ' selected' if status_filter == js else ''
        status_options += (
            f'<option value="{_html.escape(js.value)}"{selected}>'
            f'{_html.escape(js.value)}</option>\n'
        )

    # Build query string helpers for pagination links
    def _page_qs(new_offset: int) -> str:
        parts = []
        if status_filter is not None:
            parts.append(f"status={_html.escape(status_filter.value)}")
        parts.append(f"offset={new_offset}")
        return "?" + "&amp;".join(parts)

    prev_link = ""
    if offset > 0:
        prev_offset = max(0, offset - _UI_PAGE_SIZE)
        prev_link = (
            f'<a href="/ui/report-runs{_page_qs(prev_offset)}">&larr; Previous</a>'
        )
    next_link = ""
    if len(jobs) == _UI_PAGE_SIZE:
        next_offset = offset + _UI_PAGE_SIZE
        next_link = (
            f'<a href="/ui/report-runs{_page_qs(next_offset)}">Next &rarr;</a>'
        )
    pagination = ""
    if prev_link or next_link:
        sep = " &nbsp; " if (prev_link and next_link) else ""
        pagination = (
            f'<div style="margin-top:1rem">{prev_link}{sep}{next_link}</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Report Runs</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }}
h1 {{ color: #2c3e50; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ text-align: left; padding: 0.5rem 1rem; border-bottom: 1px solid #dee2e6; }}
th {{ background: #f8f9fa; }}
a {{ color: #2c3e50; }}
form.filter {{ display:inline-flex; gap:0.5rem; align-items:center; margin-bottom:1rem; }}
.cmp-bar {{ margin-bottom:0.75rem; display:flex; gap:0.5rem; align-items:center; }}
</style>
</head>
<body>
<a href="/ui/">&#8592; Home</a>
&nbsp;|&nbsp; <a href="/ui/operations">Operations Dashboard</a>
<h1>Report Runs</h1>
<form class="filter" method="GET" action="/ui/report-runs">
  <label for="status-filter">Filter by status:</label>
  <select id="status-filter" name="status" onchange="this.form.submit()">
    {status_options}
  </select>
  <noscript><button type="submit">Apply</button></noscript>
</form>
<div class="cmp-bar">
  <button id="cmp-btn" type="button" onclick="goCompare()"
    style="background:#2c3e50;color:white;border:none;padding:0.4rem 1rem;
           cursor:pointer;font-size:0.9rem;border-radius:4px">
    Compare Selected (2&#8211;4)
  </button>
  <span id="cmp-msg" style="color:#666;font-size:0.9rem"></span>
</div>
<table>
<thead><tr>
  <th style="width:2rem;text-align:center">
    <abbr title="Select 2&#8211;4 rows then click Compare">&#9745;</abbr>
  </th>
  <th>ID</th><th>Intent</th><th>Status</th><th>Created</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
{pagination}
<script>
function goCompare() {{
  var checked = Array.from(document.querySelectorAll('.cmp-check:checked'));
  var msg = document.getElementById('cmp-msg');
  if (checked.length < 2) {{
    msg.textContent = 'Select at least 2 reports.';
    return;
  }}
  if (checked.length > 4) {{
    msg.textContent = 'Select at most 4 reports.';
    return;
  }}
  msg.textContent = '';
  var ids = checked.map(function(c) {{ return c.value; }}).join(',');
  window.location.href = '/ui/compare?ids=' + ids;
}}
</script>
</body></html>"""


_COMPARE_CSS = (
    "body { font-family: system-ui, sans-serif; max-width: 1100px; margin: 2rem auto; padding: 0 1rem; }\n"  # noqa: E501
    "h1 { color: #2c3e50; }\n"
    "table { border-collapse: collapse; width: 100%; }\n"
    "th, td { text-align: left; padding: 0.5rem 0.75rem; border: 1px solid #dee2e6; }\n"
    "th { background: #f8f9fa; }\n"
    "th.run-header a { color: #2c3e50; font-size: 0.85rem; word-break: break-all; }\n"
    "td.metric { background: #f8f9fa; font-weight: bold; width: 180px; }\n"
    ".warning { background: #fff3cd; border: 1px solid #ffc107; padding: 1rem;"
    " border-radius: 4px; margin-top: 2rem; font-size: 0.9rem; }\n"
    ".error { background: #f8d7da; border: 1px solid #dc3545; padding: 1rem;"
    " border-radius: 4px; margin-top: 1rem; }\n"
)


@router.get("/compare", response_class=HTMLResponse)
def ui_compare_report_runs(
    ids: Annotated[str | None, Query()] = None,
    *,
    services: ServicesDep,
) -> HTMLResponse:
    """Side-by-side comparison table for 2..4 report run IDs."""
    nav = (
        '<a href="/ui/">&#8592; Home</a>'
        ' &nbsp;|&nbsp; <a href="/ui/report-runs">All Reports</a>'
    )

    def _error_page(message: str, http_status: int) -> HTMLResponse:
        body = (
            f"<!DOCTYPE html><html lang=\"en\">"
            f"<head><meta charset=\"UTF-8\"><title>Compare Error</title>"
            f"<style>{_COMPARE_CSS}</style></head>"
            f"<body>{nav}<h1>Compare Report Runs</h1>"
            f'<div class="error"><strong>Error:</strong> {_html.escape(message)}</div>'
            f"</body></html>"
        )
        return HTMLResponse(content=body, status_code=http_status)

    if not ids:
        return _error_page(
            "at least 2 report run IDs are required for comparison", 400
        )

    raw_ids = [part.strip() for part in ids.split(",") if part.strip()]
    if len(raw_ids) < 2:
        return _error_page(
            "at least 2 report run IDs are required for comparison", 400
        )
    if len(raw_ids) > 4:
        return _error_page(
            "at most 4 report run IDs are allowed for comparison", 400
        )

    try:
        run_ids = [UUID(rid) for rid in raw_ids]
    except ValueError as exc:
        return _error_page(f"malformed UUID in ids: {exc}", 422)

    summaries = []
    for run_id in run_ids:
        report = services.report_service.get_report_run(run_id)
        if report is None:
            return _error_page(f"report run '{run_id}' not found", 404)
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
    rows += _metric_row("Claims", [str(s.claims_count) for s in summaries])
    rows += _metric_row("Unknowns", [str(s.unknowns_count) for s in summaries])
    rows += _metric_row("Red Flags", [str(s.red_flags_count) for s in summaries])
    rows += _metric_row(
        "Verification Tasks", [str(s.verification_tasks_count) for s in summaries]
    )
    rows += _metric_row(
        "High-Severity Claims", [str(len(s.high_severity_claims)) for s in summaries]
    )

    body = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Compare Report Runs</title>
<style>
{_COMPARE_CSS}
</style></head>
<body>
{nav}
<h1>Compare Report Runs</h1>
<table>
<thead>
<tr><th>Metric</th>{col_headers}</tr>
</thead>
<tbody>
{rows}</tbody>
</table>
<div class="warning">
  <strong>Screening Tool Only.</strong> Counts reflect unapproved and approved reports.
  Report content is available only for approved reports.
</div>
</body></html>"""
    return HTMLResponse(content=body, status_code=200)


@router.post("/report-runs/{report_run_id}/approve", response_class=HTMLResponse)
def ui_approve_report_run(
    report_run_id: UUID,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    try:
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
        require_reviewer_scope(principal, REVIEWER_SCOPE_REPORT_APPROVE)
    except HTTPException as exc:
        error_body = (
            "<!DOCTYPE html><html><head><title>Authentication Error</title></head>"
            "<body><h1>Authentication Error</h1>"
            "<p>Reviewer credentials are missing, invalid, or lack the required scope.</p>"
            f"<a href='/ui/report-runs/{report_run_id}'>Back</a></body></html>"
        )
        return HTMLResponse(content=error_body, status_code=exc.status_code)
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
    services.report_service.approve_report_run(
        report_run_id,
        reviewer_id=principal.reviewer_id,
    )
    return HTMLResponse(
        content=(
            "<!DOCTYPE html>"
            "<html><head><title>Approved</title>"
            f"<meta http-equiv='refresh' content='1;url=/ui/report-runs/{report_run_id}'>"
            "</head>"
            f"<body><h1>Report Approved</h1>"
            f"<p>Approved by: {_html.escape(principal.reviewer_id)}</p>"
            f"<p><a href='/ui/report-runs/{report_run_id}'>View Report</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )


@router.post("/report-runs/{report_run_id}/retry", response_class=HTMLResponse)
def ui_retry_report_run(
    report_run_id: UUID,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Form()] = None,
    reviewer_token: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    failed_url = f"/ui/report-runs/{report_run_id}"
    try:
        principal = services.reviewer_auth(
            reviewer_id=reviewer_id,
            reviewer_token=reviewer_token,
        )
        require_reviewer_scope(principal, REVIEWER_SCOPE_REPORT_RETRY)
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
    return HTMLResponse(
        content=(
            "<!DOCTYPE html>"
            "<html><head><title>Retry Queued</title>"
            f"<meta http-equiv='refresh' content='1;url={_html.escape(new_url)}'>"
            "</head>"
            "<body><h1>Retry Queued</h1>"
            f"<p>New report run ID: {_html.escape(str(retry_job.report_run_id))}</p>"
            f"<p><a href='{_html.escape(new_url)}'>View New Report Run</a></p>"
            "</body></html>"
        ),
        status_code=200,
    )


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
        return (
            "<!DOCTYPE html><html><head><title>Not Found</title></head>"
            f"<body><h1>Report Not Found</h1><p>ID: {report_run_id}</p>"
            "<a href='/ui/report-runs'>Back to List</a></body></html>"
        )
    if report.review_status != ReportReviewStatus.APPROVED:
        return (
            "<!DOCTYPE html><html><head><title>Not Approved</title></head>"
            "<body><h1>Report Not Yet Approved</h1>"
            "<p>This report must be approved before it can be exported.</p>"
            f"<a href='/ui/report-runs/{report_run_id}'>Back</a></body></html>"
        )
    dossier_md = build_rural_land_dossier(report)
    dossier_escaped = _html.escape(dossier_md)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Dossier — {report_run_id}</title>
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
