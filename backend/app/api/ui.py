from __future__ import annotations

import html as _html
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.api.dependencies import ApiServices, get_services
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
<p>Submit an area of interest to generate a due-diligence report.</p>
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
            "<a href=\"/ui/\">Back to Home</a></body></html>"
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
<a href="/ui/">&#8592; Back</a>
<h1>Report Run</h1>
<div class="meta">
  <div>ID: {report.report_run_id}</div>
  <div>Status: {report.status.value}</div>
  <div>Intent: {report.intent_code.value}</div>
</div>
<pre class="dossier">{dossier_escaped}</pre>
<div class="warning">
  <strong>Screening Tool Only.</strong> This report does not constitute legal, title,
  survey, appraisal, or investment advice.
  All claims are subject to source limitations and require professional verification
  where indicated.
</div>
</body></html>"""
