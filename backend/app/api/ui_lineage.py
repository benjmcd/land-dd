from __future__ import annotations

import html as _html
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.api.dependencies import ApiServices, get_services
from app.api.reports import build_lineage_response
from app.api.ui_shared import build_css, error_page, page_head
from app.domain.enums import ReportReviewStatus

router = APIRouter(prefix="/ui/report-runs", tags=["ui"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]

_LINEAGE_CSS = build_css(
    "table { margin-bottom: 1.5rem; }\n"
    ".meta { margin-bottom: 1.5rem; }\n"
    ".meta div { margin-bottom: 0.25rem; }\n"
    ".tag { display: inline-block; background: #e9ecef; border-radius: 3px;"
    " padding: 0.15rem 0.4rem; font-size: 0.8rem; font-family: monospace;"
    " margin: 0.1rem; }\n"
    ".tag.unknown { background: #fff3cd; }\n"
    ".tag.source-failure { background: #f8d7da; }\n"
    ".section-note { color: #666; font-size: 0.9rem; margin-bottom: 0.75rem; }\n",
    ".meta { overflow-wrap: anywhere; }\n"
    ".table-scroll { max-width: 100%; overflow-x: auto; margin-bottom: 1.5rem; }\n"
    ".table-scroll table { min-width: 680px; margin-bottom: 0; }\n",
)


def _short(uid: object) -> str:
    """Return first 8 chars of a UUID string for display."""
    return str(uid)[:8] + "…"


@router.get("/{report_run_id}/lineage", response_class=HTMLResponse)
def ui_report_run_lineage(
    report_run_id: UUID,
    services: ServicesDep,
) -> HTMLResponse:
    report = services.report_service.get_report_run(report_run_id)
    if report is None:
        return error_page(
            "Not Found",
            f"No report found for ID: {_html.escape(str(report_run_id))}",
            "/ui/report-runs",
            200,
            css=_LINEAGE_CSS,
        )
    if report.review_status != ReportReviewStatus.APPROVED:
        review_status = _html.escape(report.review_status.value)
        return error_page(
            "Approval Required",
            (
                "Evidence lineage is available in the operator UI only after report "
                f"approval. Current review_status={review_status}."
            ),
            f"/ui/report-runs/{report_run_id}",
            409,
            css=_LINEAGE_CSS,
        )

    lineage = build_lineage_response(report)
    run_id_esc = _html.escape(str(report_run_id))
    back_url = _html.escape(f"/ui/report-runs/{report_run_id}")

    # Sources section
    source_rows = ""
    for src in lineage.sources:
        src_id_esc = _html.escape(str(src.source_id))
        src_name_esc = _html.escape(src.source_name)
        ingest_tags = "".join(
            f"<span class='tag'>{_html.escape(_short(iid))}</span>"
            for iid in src.ingest_run_ids
        ) or "<span style='color:#999'>none</span>"
        source_rows += (
            "<tr>"
            f"<td><span class='tag'>{_short(src.source_id)}</span>"
            f"<br><small style='color:#666'>{src_id_esc}</small></td>"
            f"<td>{src_name_esc}</td>"
            f"<td>{ingest_tags}</td>"
            "</tr>\n"
        )
    if not source_rows:
        source_rows = '<tr><td colspan="3" style="color:#666">No source entries.</td></tr>'

    # Claims section
    claim_rows = ""
    for cl in lineage.claim_lineage:
        claim_id_esc = _html.escape(str(cl.claim_id))
        claim_code_esc = _html.escape(cl.claim_code)
        domain_esc = _html.escape(cl.domain)
        ev_tags = "".join(
            f"<span class='tag'>{_html.escape(_short(eid))}</span>"
            for eid in cl.evidence_ids
        ) or "<span style='color:#999'>none</span>"
        claim_rows += (
            "<tr>"
            f"<td><code>{claim_code_esc}</code></td>"
            f"<td>{domain_esc}</td>"
            f"<td>{ev_tags}</td>"
            f"<td><small style='color:#999'>{claim_id_esc}</small></td>"
            "</tr>\n"
        )
    if not claim_rows:
        claim_rows = '<tr><td colspan="4" style="color:#666">No claims.</td></tr>'

    # Evidence section — split into normal and unknowns/source-failure
    ev_rows = ""
    for ev in lineage.evidence_lineage:
        ev_id_esc = _html.escape(str(ev.evidence_id))
        ev_code_esc = _html.escape(ev.evidence_code)
        domain_esc = _html.escape(ev.domain)
        src_short = _html.escape(_short(ev.source_id))
        # Tag style based on code prefix
        tag_class = ""
        if ev.evidence_code.startswith("UNKNOWN"):
            tag_class = " unknown"
        elif (
            ev.evidence_code.startswith("SOURCE_FAILURE")
            or "source_failure" in ev.evidence_code.lower()
        ):
            tag_class = " source-failure"
        claim_tags = "".join(
            f"<span class='tag'>{_html.escape(_short(cid))}</span>"
            for cid in ev.claim_ids
        ) or "<span style='color:#999'>uncited</span>"
        ev_rows += (
            "<tr>"
            f"<td><span class='tag{tag_class}'>{ev_code_esc}</span></td>"
            f"<td>{domain_esc}</td>"
            f"<td><span class='tag'>{src_short}</span></td>"
            f"<td>{claim_tags}</td>"
            f"<td><small style='color:#999'>{ev_id_esc}</small></td>"
            "</tr>\n"
        )
    if not ev_rows:
        ev_rows = '<tr><td colspan="5" style="color:#666">No evidence records.</td></tr>'

    intent_esc = _html.escape(lineage.intent_code)
    area_id_esc = _html.escape(str(lineage.area_id))

    body = (
        "<!DOCTYPE html><html lang='en'>"
        f"{page_head(f'Evidence Lineage - {run_id_esc}', css=_LINEAGE_CSS)}"
        "<body>"
        f"<a href='{back_url}'>&larr; Back to Report</a>"
        "&nbsp;|&nbsp;"
        "<a href='/ui/report-runs'>All Reports</a>"
        "<h1>Evidence Lineage</h1>"
        "<div class='meta'>"
        f"<div>Report Run ID: {run_id_esc}</div>"
        f"<div>Area ID: {area_id_esc}</div>"
        f"<div>Intent: {intent_esc}</div>"
        f"<div>Sources: {len(lineage.sources)}</div>"
        f"<div>Evidence records: {len(lineage.evidence_lineage)}</div>"
        f"<div>Claims: {len(lineage.claim_lineage)}</div>"
        "</div>"
        "<h2>Sources &rarr; Ingest Runs</h2>"
        "<p class='section-note'>Each source and its associated ingest run chain.</p>"
        "<div class='table-scroll'>"
        "<table>"
        "<thead><tr>"
        "<th>Source ID</th><th>Source Name</th><th>Ingest Run IDs</th>"
        "</tr></thead>"
        f"<tbody>{source_rows}</tbody>"
        "</table>"
        "</div>"
        "<h2>Claims &rarr; Evidence</h2>"
        "<p class='section-note'>Each claim and the evidence records that support it.</p>"
        "<div class='table-scroll'>"
        "<table>"
        "<thead><tr>"
        "<th>Claim Code</th><th>Domain</th><th>Evidence IDs</th><th>Claim ID</th>"
        "</tr></thead>"
        f"<tbody>{claim_rows}</tbody>"
        "</table>"
        "</div>"
        "<h2>Evidence &rarr; Claims</h2>"
        "<p class='section-note'>"
        "Each evidence record, its source, and the claims that cite it."
        " Highlighted rows: <span class='tag unknown'>UNKNOWN</span>"
        " = unknown/no-data evidence;"
        " <span class='tag source-failure'>SOURCE_FAILURE</span>"
        " = source retrieval failure."
        "</p>"
        "<div class='table-scroll'>"
        "<table>"
        "<thead><tr>"
        "<th>Evidence Code</th><th>Domain</th><th>Source</th>"
        "<th>Cited by Claims</th><th>Evidence ID</th>"
        "</tr></thead>"
        f"<tbody>{ev_rows}</tbody>"
        "</table>"
        "</div>"
        "</body></html>"
    )
    return HTMLResponse(content=body, status_code=200)
