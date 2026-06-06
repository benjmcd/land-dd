from __future__ import annotations

import html as _html
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.api.dependencies import ApiServices, get_services
from app.core.config import Settings
from app.domain.enums import JobStatus, ReportReviewStatus
from app.reports.dossier import build_rural_land_dossier

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
        return (
            "<!DOCTYPE html>\n"
            "<html><head><title>Report Failed</title></head>\n"
            f"<body><h1>Report Generation Failed</h1>"
            f"<p>{job.error_msg or 'Unknown error'}</p>"
            "<a href=\"/ui/\">Back to Home</a></body></html>"
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
            " style=\"display:inline\">"
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
<a href="/ui/report-runs/{report_run_id}/print">Print / Export PDF</a>
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
def ui_report_run_list(services: ServicesDep) -> str:
    jobs = services.async_report_jobs.list_recent(limit=30)
    rows = ""
    for job in jobs:
        review_badge = ""
        if job.status == JobStatus.SUCCEEDED:
            report = services.report_service.get_report_run(job.report_run_id)
            if report is not None:
                rv = report.review_status.value
                color = "#28a745" if rv == "approved" else "#ffc107"
                review_badge = f' &nbsp; <span style="color:{color};font-weight:bold">{rv}</span>'
        status_color = {
            "queued": "#6c757d",
            "running": "#007bff",
            "succeeded": "#28a745",
            "failed": "#dc3545",
        }.get(job.status.value, "#333")
        rows += (
            f'<tr>'
            f'<td><a href="/ui/report-runs/{job.report_run_id}">'
            f'{str(job.report_run_id)[:8]}…</a></td>'
            f'<td>{_html.escape(job.intent_code.value)}</td>'
            f'<td style="color:{status_color}">{job.status.value}{review_badge}</td>'
            f'<td>{_html.escape(str(job.created_at)[:19])}</td>'
            f'</tr>\n'
        )
    if not rows:
        rows = '<tr><td colspan="4" style="color:#666">No report runs yet.</td></tr>'
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
</style>
</head>
<body>
<a href="/ui/">&#8592; Home</a>
<h1>Report Runs</h1>
<table>
<thead><tr><th>ID</th><th>Intent</th><th>Status</th><th>Created</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</body></html>"""


@router.post("/report-runs/{report_run_id}/approve", response_class=HTMLResponse)
def ui_approve_report_run(
    report_run_id: UUID,
    services: ServicesDep,
) -> str:
    settings = Settings()
    accounts = settings.parsed_reviewer_accounts()
    if not accounts:
        return (
            "<!DOCTYPE html><html><head><title>Error</title></head>"
            "<body><h1>No reviewer accounts configured</h1>"
            f"<a href='/ui/report-runs/{report_run_id}'>Back</a></body></html>"
        )
    reviewer_id = next(iter(accounts))
    report = services.report_service.get_report_run(report_run_id)
    if report is None:
        return (
            "<!DOCTYPE html><html><head><title>Not Found</title></head>"
            f"<body><h1>Report Not Found</h1><p>ID: {report_run_id}</p>"
            "<a href='/ui/report-runs'>Back to List</a></body></html>"
        )
    services.report_service.approve_report_run(report_run_id, reviewer_id=reviewer_id)
    return (
        "<!DOCTYPE html>"
        "<html><head><title>Approved</title>"
        f"<meta http-equiv='refresh' content='1;url=/ui/report-runs/{report_run_id}'>"
        "</head>"
        f"<body><h1>Report Approved</h1>"
        f"<p>Approved by: {_html.escape(reviewer_id)}</p>"
        f"<p><a href='/ui/report-runs/{report_run_id}'>View Report</a></p>"
        "</body></html>"
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
