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
        f"- Parcel ID/APN: {_parcel_id(report_run)}",
        "- Jurisdiction: unknown",
        f"- Acreage: {_parcel_acreage(report_run)}",
        f"- Zoning designation: {_parcel_zoning(report_run)}",
        f"- Area ID: {report_run.area_id}",
        "- Geometry confidence: unknown",
        f"- Intent: {report_run.intent_code.value}",
        f"- Report generated at: {_format_datetime(report_run.finished_at)}",
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
        f"- Apparent road adjacency: {_access_road_result(report_run)}",
        "- Public/private/unknown road context: unknown",
        "- Legal access conclusion: not determined",
        f"- Required verification: {_domain_verification(report_run, 'access')}",
        "",
        "Required language:",
        f"> {_ROAD_PROXY_LANGUAGE}",
        "",
        "## 6. Buildability Screen",
        "",
        f"- Terrain / slope screening: {_buildability_summary(report_run)}",
        f"- Terrain constraints: {_buildability_constraint(report_run)}",
        f"- Required verification: {_domain_verification(report_run, 'buildability')}",
        "",
        "## 7. Flood and Wetlands Screen",
        "",
        f"- FEMA/NFHL result: {_flood_zone_result(report_run)}",
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
        f"- Zoning district: {_zoning_district_result(report_run)}",
        f"- Intended-use compatibility: {_zoning_use_compatibility(report_run)}",
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
            evidence=_cell(
                f"{len(claim.evidence_ids)} record(s)"
                if claim.evidence_ids
                else "none"
            ),
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


def _parcel_id(report_run: ReportRunContract) -> str:
    for record in report_run.evidence:
        if record.domain == "parcels" and not record.is_source_failure:
            pin = record.observed_value.get("parcel_pin")
            if pin is not None:
                return str(pin)
    return "unknown"


def _parcel_acreage(report_run: ReportRunContract) -> str:
    for record in report_run.evidence:
        if record.domain == "parcels" and not record.is_source_failure:
            acres = record.observed_value.get("parcel_acres")
            if acres is not None:
                return f"{acres} acres (parcel record)"
    return "unknown"


def _parcel_zoning(report_run: ReportRunContract) -> str:
    for record in report_run.evidence:
        if record.domain == "parcels" and not record.is_source_failure:
            zoning = record.observed_value.get("parcel_zoning")
            if zoning is not None:
                return str(zoning)
    return "unknown"


def _access_road_result(report_run: ReportRunContract) -> str:
    for record in report_run.evidence:
        if record.domain == "access" and not record.is_source_failure:
            has_road = record.observed_value.get("has_public_road_adjacency")
            dist = record.observed_value.get("road_distance_m")
            if has_road is True:
                if dist is not None and float(dist) == 0.0:  # type: ignore[arg-type]
                    return "public road adjacency observed (abutting)"
                if dist is not None:
                    return f"public road adjacency observed (~{float(dist):.0f}m)"  # type: ignore[arg-type]
                return "public road adjacency observed"
            if has_road is False:
                return "no public road adjacency observed — physical proxy only; legal access status unknown"  # noqa: E501
    records = [r for r in report_run.evidence if r.domain == "access"]
    if records:
        return _domain_summary(report_run, "access")
    return "unknown"


def _flood_zone_result(report_run: ReportRunContract) -> str:
    records = [r for r in report_run.evidence if r.domain == "flood" and not r.is_source_failure]
    if not records:
        return "not evaluated"
    parts: list[str] = []
    for record in records:
        zone_code = record.observed_value.get("flood_zone_code")
        ratio = record.observed_value.get("intersection_ratio")
        if zone_code:
            part = f"FEMA zone {zone_code}"
            if ratio is not None:
                try:
                    part += f" ({float(ratio):.0%} area intersection)"  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    pass
            parts.append(part)
        else:
            parts.append(_cell(record.observation))
    return "; ".join(parts) if parts else _domain_summary(report_run, "flood")


def _zoning_district_result(report_run: ReportRunContract) -> str:
    records = [r for r in report_run.evidence if r.domain == "zoning" and not r.is_source_failure]
    if not records:
        return "not evaluated"
    parts: list[str] = []
    for record in records:
        district = record.observed_value.get("zoning_district")
        if district:
            parts.append(str(district))
        else:
            parts.append(_cell(record.observation))
    return "; ".join(parts) if parts else _domain_summary(report_run, "zoning")


def _zoning_use_compatibility(report_run: ReportRunContract) -> str:
    records = [r for r in report_run.evidence if r.domain == "zoning" and not r.is_source_failure]
    if not records:
        return "not determined"
    for record in records:
        allowed = record.observed_value.get("intended_residential_use_allowed")
        prohibited = record.observed_value.get("intended_residential_use_prohibited")
        edge = record.observed_value.get("jurisdiction_edge")
        if allowed is True:
            return "residential use appears permitted (screening only; verify with county planning)"
        if prohibited is True:
            return "residential use appears restricted (screening only; verify with county planning)"  # noqa: E501
        if edge is True:
            return "at jurisdiction boundary — zoning status ambiguous; verify with county planning"
    return "not determined"


def _buildability_summary(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence
        if r.domain == "buildability" and not r.is_source_failure
    ]
    if not records:
        return "not evaluated"
    parts: list[str] = []
    for record in records:
        relief = record.observed_value.get("relief_m")
        mean_slope = record.observed_value.get("mean_slope_pct")
        ratio = record.observed_value.get("low_slope_area_ratio")
        elev = record.observed_value.get("mean_elevation_m")
        metric_val = record.observed_value.get("value")
        metric_unit = record.observed_value.get("unit")
        metric_code = record.observed_value.get("metric_code")
        if relief is not None:
            parts.append(f"terrain relief ~{float(relief):.0f}m")  # type: ignore[arg-type]
        if mean_slope is not None:
            parts.append(f"mean slope ~{float(mean_slope):.0f}%")  # type: ignore[arg-type]
        if ratio is not None:
            parts.append(f"{float(ratio):.0%} low-slope buildable area")  # type: ignore[arg-type]
        if elev is not None:
            parts.append(f"mean elevation ~{float(elev):.0f}m")  # type: ignore[arg-type]
        if metric_code and metric_val is not None and metric_unit:
            parts.append(f"{metric_code}: {float(metric_val):.1f} {metric_unit}")  # type: ignore[arg-type]
    return "; ".join(parts) if parts else "; ".join(r.observation for r in records)


def _buildability_constraint(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence
        if r.domain == "buildability" and not r.is_source_failure
    ]
    if not records:
        return "not determined"
    for record in records:
        insufficient = record.observed_value.get("insufficient_low_slope_buildable_area")
        if insufficient is True:
            return "insufficient low-slope buildable area detected (screening only; confirm with survey)"  # noqa: E501
        if insufficient is False:
            return "no slope constraint detected in screening (confirm with survey before construction)"  # noqa: E501
    failures = [
        r for r in report_run.evidence
        if r.domain == "buildability" and r.is_source_failure
    ]
    if failures:
        return "terrain data unavailable — source failure recorded; manual verification required"
    return "screening data available; interpret with caveat"


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
                url=_cell(str(detail.get("homepage_url") or "unknown")),
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
