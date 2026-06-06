from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from app.domain.claim_contracts import ClaimContract
from app.domain.evidence_contracts import EvidenceContract
from app.domain.report_contracts import ReportRunContract

_SCREENING_DISCLAIMER = (
    "Screening output only. This dossier is not legal, title, water-rights, "
    "insurance, lending, appraisal, or investment advice."
)
_ROAD_PROXY_LANGUAGE = (
    "Road proximity is a physical proxy only and does not establish recorded "
    "legal access."
)


def build_rural_land_dossier(report_run: ReportRunContract) -> str:
    lines = [
        "# Rural Land Dossier",
        "",
        f"> {_SCREENING_DISCLAIMER}",
        "",
        "## 1. Executive Summary",
        "",
        f"- Overall suitability band: {_overall_suitability(report_run)}",
        f"- Confidence band: {_confidence_band(report_run)}",
        f"- Critical red flags: {len(report_run.red_flags)}",
        f"- High-priority unknowns: {len(report_run.unknowns)}",
        f"- Recommended next action: {_recommended_next_action(report_run)}",
        "",
        "## 2. Area Identity",
        "",
        "- Parcel ID/APN: unknown",
        "- Jurisdiction: unknown",
        "- Acreage: unknown",
        f"- Geometry source: area_id {report_run.area_id}",
        "- Geometry confidence: unknown",
        f"- Report run ID: {report_run.report_run_id}",
        f"- Review status: {report_run.review_status.value}",
        f"- Reviewed by: {report_run.reviewed_by or 'unknown'}",
        f"- Reviewed at: {_format_datetime(report_run.reviewed_at)}",
        f"- Source manifest version: {_source_manifest_version(report_run)}",
        "",
        "## 3. Top Red Flags",
        "",
        "| Severity | Domain | Claim | Evidence | Verification |",
        "|---|---|---|---|---|",
        *_claim_rows(report_run.red_flags),
        "",
        "## 4. Data Confidence Summary",
        "",
        "| Domain | Confidence | Sources used | Missing/conflicting data |",
        "|---|---|---|---|",
        *_confidence_rows(report_run),
        "",
        "## 5. Access Screen",
        "",
        "- Apparent road adjacency: unknown",
        "- Public/private/unknown road context: unknown",
        "- Legal access conclusion: not determined",
        f"- Required verification: {_domain_verification(report_run, 'access')}",
        "",
        "Required language:",
        f"> {_ROAD_PROXY_LANGUAGE}",
        "",
        "## 6. Buildability Screen",
        "",
        "- Slope metrics: not evaluated unless listed in evidence appendix",
        "- Usable area proxy: unknown",
        "- Terrain constraints: not determined",
        f"- Required verification: {_domain_verification(report_run, 'slope')}",
        "",
        "## 7. Flood and Wetlands Screen",
        "",
        f"- FEMA/NFHL result: {_domain_summary(report_run, 'flood')}",
        f"- USFWS/NWI result: {_domain_summary(report_run, 'wetland')}",
        f"- Caveats: {_domain_caveats(report_run, {'flood', 'wetland'})}",
        f"- Required verification: {_domain_verification(report_run, 'flood')}",
        "",
        "## 8. Soil / Septic Proxy",
        "",
        "- Soil map units: not evaluated",
        "- Drainage/limitation notes: unknown",
        "- Septic proxy confidence: unknown",
        f"- Required verification: {_domain_verification(report_run, 'soil')}",
        "",
        "## 9. Water Context",
        "",
        "- Nearby wells/monitoring: not evaluated",
        "- Groundwater/surface water context: unknown",
        "- Water-rights status: not determined",
        f"- Required verification: {_domain_verification(report_run, 'water')}",
        "",
        "## 10. Zoning / Land Use",
        "",
        f"- Zoning district: {_domain_summary(report_run, 'zoning')}",
        "- Intended-use compatibility: not determined",
        "- Overlays: unknown",
        "- Minimum lot size/setbacks: unknown",
        "- Source excerpts: see source appendix",
        f"- Required verification: {_domain_verification(report_run, 'zoning')}",
        "",
        "## 11. Environmental / Compliance Hazards",
        "",
        "- Nearby regulated facilities: not evaluated",
        "- Known contamination/remediation context: unknown",
        "- Caveats: screening category not complete for beta until sources are approved",
        "- Required verification: review approved environmental/compliance sources",
        "",
        "## 12. Market Context",
        "",
        "- Price/acre: not evaluated",
        "- Nearby comps/listings: not evaluated",
        "- Liquidity context: unknown",
        "- Caveats: no appraisal, valuation, or investment conclusion is provided",
        "",
        "## 13. Unknowns",
        "",
        "| Domain | Unknown | Why unknown | How to resolve |",
        "|---|---|---|---|",
        *_unknown_rows(report_run),
        "",
        "## 14. Verification Plan",
        "",
        "| Priority | Task | Who to contact | Evidence to request |",
        "|---|---|---|---|",
        *_verification_rows(report_run),
        "",
        "## 15. Source Appendix",
        "",
        "| Source | Version/date | Use | Caveat | URL |",
        "|---|---|---|---|---|",
        *_source_rows(report_run),
        "",
    ]
    return "\n".join(lines)


def _overall_suitability(report_run: ReportRunContract) -> str:
    if report_run.red_flags:
        return "needs_review"
    if report_run.unknowns:
        return "unknown"
    return "screening_clear"


def _confidence_band(report_run: ReportRunContract) -> str:
    if report_run.unknowns:
        return "low"
    if report_run.evidence:
        return "medium"
    return "unknown"


def _recommended_next_action(report_run: ReportRunContract) -> str:
    if report_run.verification_tasks:
        return "Complete the verification plan before relying on the screening output."
    return "Review source appendix and caveats before delivery."


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "unknown"
    return value.isoformat()


def _source_manifest_version(report_run: ReportRunContract) -> str:
    manifest = report_run.source_manifest
    ruleset_id = manifest.get("ruleset_id", "unknown")
    ruleset_version = manifest.get("ruleset_version", "unknown")
    return f"{ruleset_id}@{ruleset_version}"


def _claim_rows(claims: list[ClaimContract]) -> list[str]:
    if not claims:
        return ["| none | none | none | none | none |"]
    return [
        "| {severity} | {domain} | {claim} | {evidence} | {verification} |".format(
            severity=_cell(claim.severity.value),
            domain=_cell(claim.domain),
            claim=_cell(claim.user_safe_language or claim.assertion),
            evidence=_cell(", ".join(str(evidence_id) for evidence_id in claim.evidence_ids)),
            verification=_cell(claim.verification_task or "none"),
        )
        for claim in claims
    ]


def _confidence_rows(report_run: ReportRunContract) -> list[str]:
    by_domain: dict[str, list[EvidenceContract]] = defaultdict(list)
    for evidence in report_run.evidence:
        by_domain[evidence.domain].append(evidence)
    if not by_domain:
        return ["| unknown | unknown | none | no evidence available |"]
    source_names = _source_names_by_id(report_run)
    rows = []
    for domain in sorted(by_domain):
        records = by_domain[domain]
        confidences = sorted({record.confidence.value for record in records})
        names = sorted(
            {source_names.get(str(record.source_id), str(record.source_id)) for record in records}
        )
        missing = (
            "source failure present"
            if any(record.is_source_failure for record in records)
            else "none recorded"
        )
        rows.append(
            "| {domain} | {confidence} | {sources} | {missing} |".format(
                domain=_cell(domain),
                confidence=_cell(", ".join(confidences)),
                sources=_cell(", ".join(names)),
                missing=_cell(missing),
            )
        )
    return rows


def _domain_summary(report_run: ReportRunContract, domain: str) -> str:
    records = [record for record in report_run.evidence if record.domain == domain]
    if not records:
        return "not evaluated"
    return "; ".join(_cell(record.observation) for record in records)


def _domain_caveats(report_run: ReportRunContract, domains: set[str]) -> str:
    caveats = sorted(
        {
            record.caveat.strip()
            for record in report_run.evidence
            if record.domain in domains and record.caveat is not None and record.caveat.strip()
        }
    )
    if not caveats:
        return "none recorded"
    return "; ".join(_cell(caveat) for caveat in caveats)


def _domain_verification(report_run: ReportRunContract, domain: str) -> str:
    tasks = sorted(
        {
            claim.verification_task.strip()
            for claim in report_run.claims
            if claim.domain == domain
            and claim.verification_task is not None
            and claim.verification_task.strip()
        }
    )
    if not tasks:
        return "not specified"
    return "; ".join(_cell(task) for task in tasks)


def _unknown_rows(report_run: ReportRunContract) -> list[str]:
    if not report_run.unknowns:
        return ["| none | none | none | none |"]
    return [
        "| {domain} | {unknown} | {why} | {resolve} |".format(
            domain=_cell(claim.domain),
            unknown=_cell(claim.user_safe_language or claim.assertion),
            why=_cell("missing, failed, or review-gated evidence"),
            resolve=_cell(claim.verification_task or "human review required"),
        )
        for claim in report_run.unknowns
    ]


def _verification_rows(report_run: ReportRunContract) -> list[str]:
    if not report_run.verification_tasks:
        return ["| none | none | none | none |"]
    return [
        "| {priority} | {task} | {contact} | {evidence} |".format(
            priority=index,
            task=_cell(task),
            contact="qualified local reviewer",
            evidence="source document, official response, or reviewed field note",
        )
        for index, task in enumerate(report_run.verification_tasks, start=1)
    ]


def _source_rows(report_run: ReportRunContract) -> list[str]:
    details = report_run.source_manifest.get("source_details")
    if not isinstance(details, list) or not details:
        return ["| unknown | unknown | screening input | none recorded | unknown |"]
    rows = []
    for raw_detail in details:
        if not isinstance(raw_detail, dict):
            continue
        detail = dict(raw_detail)
        rows.append(
            "| {source} | {version} | {use} | {caveat} | {url} |".format(
                source=_cell(str(detail.get("name", "unknown"))),
                version=_cell(
                    str(detail.get("last_checked_at") or detail.get("freshness_class") or "unknown")
                ),
                use=_cell(str(detail.get("review_status", "unknown"))),
                caveat=_cell(str(detail.get("license_status", "unknown"))),
                url="unknown",
            )
        )
    if not rows:
        return ["| unknown | unknown | screening input | none recorded | unknown |"]
    return rows


def _source_names_by_id(report_run: ReportRunContract) -> dict[str, str]:
    details = report_run.source_manifest.get("source_details")
    if not isinstance(details, list):
        return {}
    result: dict[str, str] = {}
    for detail in details:
        if not isinstance(detail, dict):
            continue
        source_id = detail.get("source_id")
        name = detail.get("name")
        if isinstance(source_id, str) and isinstance(name, str):
            result[source_id] = name
    return result


def _cell(value: str) -> str:
    return " ".join(value.replace("|", "\\|").split())


__all__ = ["build_rural_land_dossier"]
