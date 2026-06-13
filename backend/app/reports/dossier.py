from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import UUID

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
        f"- Advisory findings: {len(report_run.advisory_claims)}",
        f"- High-priority unknowns: {len(report_run.unknowns)}",
        f"- Recommended next action: {_recommended_next_action(report_run)}",
        "",
        "## 2. Area Identity",
        "",
        f"- Parcel ID/APN: {_parcel_id(report_run)}",
        f"- Jurisdiction: {_jurisdiction_from_evidence(report_run)}",
        f"- Census geography: {_census_geography_result(report_run)}",
        f"- Acreage: {_parcel_acreage(report_run)}",
        f"- Zoning designation: {_parcel_zoning(report_run)}",
        f"- Parcel data caveats: {_domain_caveats(report_run, {'parcels'})}",
        "- Assessor and tax data: Assessor and tax data were not available",
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
        "**Advisory findings** (further verification recommended)",
        "",
        "| Domain | Claim | Evidence | Verification |",
        "|---|---|---|---|",
        *_advisory_rows(report_run.advisory_claims),
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
        f"- Caveats: {_domain_caveats(report_run, {'access'})}",
        f"- Required verification: {_domain_verification(report_run, 'access')}",
        "",
        "Required language:",
        f"> {_ROAD_PROXY_LANGUAGE}",
        "",
        "## 6. Buildability Screen",
        "",
        f"- Terrain / slope screening: {_buildability_summary(report_run)}",
        f"- Terrain constraints: {_buildability_constraint(report_run)}",
        f"- Caveats: {_domain_caveats(report_run, {'buildability', 'terrain'})}",
        f"- Required verification: {_domain_verification_multi(report_run, {'buildability', 'terrain'})}",  # noqa: E501
        "",
        "## 7. Flood and Wetlands Screen",
        "",
        f"- FEMA/NFHL result: {_flood_zone_result(report_run)}",
        f"- USFWS/NWI result: {_wetland_result(report_run)}",
        f"- Caveats: {_domain_caveats(report_run, {'flood', 'wetlands'})}",
        f"- Required verification: {_domain_verification_multi(report_run, {'flood', 'wetlands'})}",
        "",
        "## 8. Soil / Septic Proxy",
        "",
        f"- Soil map units: {_soil_septic_result(report_run)}",
        f"- Drainage/limitation notes: {_soil_drainage_result(report_run)}",
        f"- Septic proxy confidence: {_septic_proxy_confidence(report_run)}",
        f"- Caveats: {_domain_caveats(report_run, {'soil_septic', 'soils'})}",
        f"- Required verification: {_domain_verification_multi(report_run, {'soil_septic', 'soils'})}",  # noqa: E501
        "",
        "## 9. Water Context",
        "",
        f"- Nearby monitoring stations: {_water_monitoring_result(report_run)}",
        "- Water-rights status: not determined",
        f"- Caveats: {_domain_caveats(report_run, {'water'})}",
        f"- Required verification: {_domain_verification(report_run, 'water')}",
        "",
        "## 10. Zoning / Land Use",
        "",
        f"- Zoning district: {_zoning_district_result(report_run)}",
        f"- Intended-use compatibility: {_zoning_use_compatibility(report_run)}",
        "- Overlays: unknown",
        "- Minimum lot size/setbacks: unknown",
        "- Source excerpts: see source appendix",
        f"- Caveats: {_domain_caveats(report_run, {'zoning'})}",
        f"- Required verification: {_domain_verification(report_run, 'zoning')}",
        "",
        "## 11. Environmental / Compliance Hazards",
        "",
        f"- Nearby regulated facilities: {_env_hazard_result(report_run)}",
        "- Known contamination/remediation context: unknown",
        f"- Caveats: {_domain_caveats(report_run, {'env_hazard'})}",
        f"- Required verification: {_domain_verification(report_run, 'env_hazard')}",
        "",
        "## 12. Internet / Connectivity",
        "",
        f"- Broadband availability: {_broadband_result(report_run)}",
        f"- Caveats: {_domain_caveats(report_run, {'broadband'})}",
        f"- Required verification: {_domain_verification(report_run, 'broadband')}",
        "",
        "## 13. Climate / Weather Context",
        "",
        f"- NWS forecast zone: {_climate_result(report_run)}",
        f"- Caveats: {_domain_caveats(report_run, {'climate'})}",
        f"- Required verification: {_domain_verification(report_run, 'climate')}",
        "",
        "## 14. Resource / Geologic Context",
        "",
        f"- BLM active mining claims: {_mineral_mining_result(report_run)}",
        f"- Historical mineral occurrences: {_mineral_occurrence_result(report_run)}",
        f"- Geologic map unit context: {_geologic_context_result(report_run)}",
        "- Mineral rights status: not determined — consult title search",
        f"- Caveats: {_domain_caveats(report_run, {'minerals', 'geology'})}",
        f"- Required verification: {_domain_verification_multi(report_run, {'minerals', 'geology'})}",  # noqa: E501
        "",
        "## 15. Market Context",
        "",
        "- Price/acre: not evaluated",
        "- Nearby comps/listings: not evaluated",
        "- Liquidity context: unknown",
        "- Caveats: no appraisal, valuation, or investment conclusion is provided",
        "",
        "## 16. Unknowns",
        "",
        "| Domain | Unknown | Why unknown | How to resolve |",
        "|---|---|---|---|",
        *_unknown_rows(report_run),
        "",
        "## 17. Verification Plan",
        "",
        "| Priority | Task | Who to contact | Evidence to request |",
        "|---|---|---|---|",
        *_verification_rows(report_run),
        "",
        "## 18. Source Appendix",
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
    structural_ids = {
        r.evidence_id
        for r in report_run.evidence
        if r.domain in _STRUCTURAL_DOMAINS or r.evidence_code in _STRUCTURAL_EVIDENCE_CODES
    }
    non_structural_unknowns = [
        claim for claim in report_run.unknowns
        if not all(eid in structural_ids for eid in claim.evidence_ids)
    ]
    if non_structural_unknowns:
        return "unknown"
    return "screening_clear"


_STRUCTURAL_DOMAINS = frozenset({
    "soil_septic",       # always screening-grade; UNKNOWN is by design
    "parcels",           # always screening-grade; UNKNOWN is by design
    "resource_context",  # permanently not evaluated in this version
    "market_context",    # permanently not evaluated in this version
    "assessor",          # permanently not evaluated in this version
})
# Sentinel evidence codes injected by the report service when no connector ran for a domain.
_STRUCTURAL_EVIDENCE_CODES = frozenset({
    "ZONING_NOT_SCREENED",  # added when no zoning connector was dispatched for an area
})


def _confidence_band(report_run: ReportRunContract) -> str:
    structural_ids = {
        r.evidence_id
        for r in report_run.evidence
        if r.domain in _STRUCTURAL_DOMAINS or r.evidence_code in _STRUCTURAL_EVIDENCE_CODES
    }
    non_structural_evidence = [
        r for r in report_run.evidence if r.evidence_id not in structural_ids
    ]
    if not non_structural_evidence:
        return "unknown"
    non_structural_unknowns = [
        claim for claim in report_run.unknowns
        if not all(eid in structural_ids for eid in claim.evidence_ids)
    ]
    if not non_structural_unknowns:
        return "medium"
    return "low"


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


_FLOOD_ZONE_LABELS: dict[str, str] = {
    "X": "minimal flood hazard",
    "X500": "0.2% annual chance flood zone",
    "AE": "1% annual chance; base flood elevation available",
    "A": "1% annual chance; no base flood elevation",
    "AH": "1% annual chance shallow ponding",
    "AO": "1% annual chance shallow sheet flow",
    "VE": "coastal high hazard; base flood elevation available",
    "V": "coastal high hazard; no base flood elevation",
    "D": "undetermined flood hazard",
}

_EVIDENCE_ID_CAP = 4


def _fmt_evidence_ids(evidence_ids: list[UUID]) -> str:
    """Return a compact evidence-ID summary: count + first-8-hex prefixes, capped."""
    if not evidence_ids:
        return "none"
    count = len(evidence_ids)
    shown = evidence_ids[:_EVIDENCE_ID_CAP]
    prefixes = ", ".join(str(eid).replace("-", "")[:8] for eid in shown)
    overflow = count - len(shown)
    suffix = f" +{overflow} more" if overflow else ""
    return f"{count} record(s): {prefixes}{suffix}"


def _claim_rows(claims: list[ClaimContract]) -> list[str]:
    if not claims:
        return ["| none | none | none | none | none |"]
    return [
        "| {severity} | {domain} | {claim} | {evidence} | {verification} |".format(
            severity=_cell(claim.severity.value),
            domain=_cell(claim.domain),
            claim=_cell(claim.user_safe_language or claim.assertion),
            evidence=_cell(_fmt_evidence_ids(claim.evidence_ids)),
            verification=_cell(claim.verification_task or "none"),
        )
        for claim in claims
    ]


def _advisory_rows(claims: list[ClaimContract]) -> list[str]:
    if not claims:
        return ["| none | none | none | none |"]
    return [
        "| {domain} | {claim} | {evidence} | {verification} |".format(
            domain=_cell(claim.domain),
            claim=_cell(claim.user_safe_language or claim.assertion),
            evidence=_cell(_fmt_evidence_ids(claim.evidence_ids)),
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
            acres = record.observed_value.get("parcel_acres") or record.observed_value.get(
                "total_acres_approx"
            )
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


def _jurisdiction_from_evidence(report_run: ReportRunContract) -> str:
    for record in report_run.evidence:
        if record.domain == "parcels" and not record.is_source_failure:
            county = record.observed_value.get("parcel_county")
            if isinstance(county, str) and county.strip():
                return county.strip()
    return "unknown"


def _census_geography_result(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence
        if r.domain == "census_geography" and not r.is_source_failure
    ]
    if not records:
        failures = [
            r for r in report_run.evidence
            if r.evidence_code == "CENSUS_TIGER_SOURCE_FAILURE"
        ]
        return "source failure — Census TIGERweb data unavailable" if failures else "not evaluated"
    record = records[0]
    parts: list[str] = []
    tract = record.observed_value.get("primary_census_tract_geoid")
    tract_name = record.observed_value.get("primary_census_tract_name")
    bg = record.observed_value.get("primary_census_block_group_geoid")
    bg_name = record.observed_value.get("primary_census_block_group_name")
    if tract:
        label = str(tract_name) if isinstance(tract_name, str) and tract_name else f"tract {tract}"
        parts.append(label)
    if bg:
        label = str(bg_name) if isinstance(bg_name, str) and bg_name else f"block group {bg}"
        parts.append(label)
    return "; ".join(parts) if parts else _cell(record.observation)


def _access_road_result(report_run: ReportRunContract) -> str:
    for record in report_run.evidence:
        if record.domain == "access" and not record.is_source_failure:
            has_road = record.observed_value.get("has_public_road_adjacency")
            dist = record.observed_value.get("road_distance_m")
            count = record.observed_value.get("road_count")
            count_str = f", {int(count)} segment(s)" if isinstance(count, (int, float)) and int(count) > 0 else ""  # noqa: E501
            if has_road is True:
                if dist is not None and float(dist) == 0.0:  # type: ignore[arg-type]
                    return f"public road adjacency observed (abutting{count_str})"
                if dist is not None:
                    return f"public road adjacency observed (~{float(dist):.0f}m{count_str})"  # type: ignore[arg-type]
                return f"public road adjacency observed{count_str}"
            if has_road is False:
                return "no public road adjacency observed — physical proxy only; legal access status unknown"  # noqa: E501
    records = [r for r in report_run.evidence if r.domain == "access"]
    if records:
        return _domain_summary(report_run, "access")
    return "unknown"


def _flood_zone_result(report_run: ReportRunContract) -> str:
    records = [r for r in report_run.evidence if r.domain == "flood" and not r.is_source_failure]
    if not records:
        failures = [r for r in report_run.evidence if r.domain == "flood" and r.is_source_failure]
        if failures:
            return "source failure — FEMA NFHL data unavailable"
        return "not evaluated"
    parts: list[str] = []
    for record in records:
        zone_code = record.observed_value.get("flood_zone_code")
        ratio = record.observed_value.get("intersection_ratio")
        if zone_code:
            desc = _FLOOD_ZONE_LABELS.get(str(zone_code).upper(), "")
            part = f"FEMA zone {zone_code}" + (f" — {desc}" if desc else "")
            if ratio is not None:
                try:
                    part += f" ({float(ratio):.0%} area intersection)"  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    pass
            parts.append(part)
        else:
            parts.append(_cell(record.observation))
    return "; ".join(parts) if parts else _domain_summary(report_run, "flood")


def _wetland_result(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence
        if r.domain == "wetlands" and not r.is_source_failure
    ]
    if not records:
        failures = [
            r for r in report_run.evidence
            if r.domain == "wetlands" and r.is_source_failure
        ]
        if failures:
            return "source failure — NWI wetland data unavailable"
        return "not evaluated"
    total_area_sq_m = 0.0
    wetland_labels: list[str] = []
    seen_labels: set[str] = set()
    for record in records:
        area = record.observed_value.get("mapped_wetland_area_sq_m")
        if area is not None:
            total_area_sq_m += float(area)  # type: ignore[arg-type]
        wclass = record.observed_value.get("wetland_class")
        wtype = record.observed_value.get("wetland_type")
        label = str(wclass) if isinstance(wclass, str) and wclass else (
            str(wtype) if isinstance(wtype, str) and wtype else None
        )
        if label and label not in seen_labels:
            seen_labels.add(label)
            wetland_labels.append(label)
    parts: list[str] = [f"{len(records)} mapped wetland/deepwater feature(s) intersect query area"]
    if total_area_sq_m > 0:
        parts.append(f"~{total_area_sq_m / 4047:.2f} mapped acres")
    if wetland_labels:
        parts.append("types: " + ", ".join(wetland_labels[:3]))
    return "; ".join(parts)


def _domain_verification_multi(report_run: ReportRunContract, domains: set[str]) -> str:
    tasks = sorted(
        {
            claim.verification_task.strip()
            for claim in report_run.claims
            if claim.domain in domains
            and claim.verification_task is not None
            and claim.verification_task.strip()
        }
    )
    if not tasks:
        return "not specified"
    return "; ".join(_cell(task) for task in tasks)


def _zoning_district_result(report_run: ReportRunContract) -> str:
    records = [r for r in report_run.evidence if r.domain == "zoning" and not r.is_source_failure]
    if not records:
        failures = [r for r in report_run.evidence if r.domain == "zoning" and r.is_source_failure]
        if failures:
            return "source failure — zoning data unavailable"
        return "not evaluated"
    parts: list[str] = []
    for record in records:
        district = (
            record.observed_value.get("district_name")
            or record.observed_value.get("zoning_district")
        )
        code = record.observed_value.get("zoning_code")
        if district:
            label = str(district)
            if code:
                label = f"{code} — {label}"
            parts.append(label)
        else:
            parts.append(_cell(record.observation))
    return "; ".join(parts) if parts else _domain_summary(report_run, "zoning")


def _zoning_use_compatibility(report_run: ReportRunContract) -> str:
    records = [r for r in report_run.evidence if r.domain == "zoning" and not r.is_source_failure]
    if not records:
        return "not determined"
    any_prohibited = any(r.observed_value.get("intended_residential_use_prohibited") is True
                         for r in records)
    any_allowed = any(r.observed_value.get("intended_residential_use_allowed") is True
                      for r in records)
    any_edge = any(r.observed_value.get("jurisdiction_edge") is True for r in records)
    if any_prohibited:
        return "residential use appears restricted (screening only; verify with county planning)"
    if any_allowed:
        return "residential use appears permitted (screening only; verify with county planning)"
    if any_edge:
        return "at jurisdiction boundary — zoning status ambiguous; verify with county planning"
    return "not determined"


_BUILDABILITY_DOMAINS = frozenset({"buildability", "terrain"})


def _buildability_summary(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence
        if r.domain in _BUILDABILITY_DOMAINS and not r.is_source_failure
    ]
    if not records:
        failures = [
            r for r in report_run.evidence
            if r.domain in _BUILDABILITY_DOMAINS and r.is_source_failure
        ]
        if failures:
            return "source failure — terrain data unavailable"
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
        if r.domain in _BUILDABILITY_DOMAINS and not r.is_source_failure
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
        if r.domain in _BUILDABILITY_DOMAINS and r.is_source_failure
    ]
    if failures:
        return "terrain data unavailable — source failure recorded; manual verification required"
    return "screening data available; interpret with caveat"


def _water_monitoring_result(report_run: ReportRunContract) -> str:
    records = [r for r in report_run.evidence if r.domain == "water" and not r.is_source_failure]
    if not records:
        failures = [r for r in report_run.evidence if r.domain == "water" and r.is_source_failure]
        if failures:
            return "source failure — water monitoring data unavailable"
        return "not evaluated"
    parts: list[str] = []
    for record in records:
        station_count = record.observed_value.get("monitoring_station_count")
        has_context = record.observed_value.get("plausible_water_context")
        no_context = record.observed_value.get("no_plausible_water_context")
        if has_context is True and station_count is not None:
            n = int(station_count)  # type: ignore[call-overload]
            parts.append(f"{n} monitoring station(s) detected in screening bbox")
        elif has_context is True:
            parts.append("monitoring stations detected in screening bbox")
        elif no_context is True:
            parts.append("no monitoring stations detected in screening bbox")
        else:
            parts.append(_cell(record.observation))
    return "; ".join(parts) if parts else _domain_summary(report_run, "water")


def _env_hazard_result(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence if r.domain == "env_hazard" and not r.is_source_failure
    ]
    if not records:
        failures = [
            r for r in report_run.evidence if r.domain == "env_hazard" and r.is_source_failure
        ]
        if failures:
            return "source failure — environmental hazard data unavailable"
        return "not evaluated"
    parts: list[str] = []
    for record in records:
        facility_count = record.observed_value.get("regulated_facility_count")
        has_proximity = record.observed_value.get("has_env_hazard_proximity")
        no_proximity = record.observed_value.get("no_env_hazard_proximity")
        if has_proximity is True:
            if facility_count is not None and int(facility_count) > 0:  # type: ignore[call-overload]
                count = int(facility_count)  # type: ignore[call-overload]
                parts.append(
                    f"{count} regulated facility/facilities detected in screening bbox"
                )
            else:
                parts.append("regulated facilities detected in screening bbox")
        elif no_proximity is True:
            parts.append("no regulated facilities detected in screening bbox")
        else:
            parts.append(_cell(record.observation))
    return "; ".join(parts) if parts else _domain_summary(report_run, "env_hazard")


def _climate_result(report_run: ReportRunContract) -> str:
    records = [r for r in report_run.evidence if r.domain == "climate" and not r.is_source_failure]
    if not records:
        failures = [r for r in report_run.evidence if r.domain == "climate" and r.is_source_failure]
        if failures:
            return "source failure — NOAA NWS climate data unavailable"
        return "not evaluated"
    rec = records[0]
    v = rec.observed_value or {}
    zone = str(v.get("nws_forecast_zone", ""))
    zone_name = str(v.get("nws_forecast_zone_name", ""))
    office = str(v.get("nws_office_code", ""))
    timezone = str(v.get("timezone", ""))
    radar = str(v.get("nws_radar_station", ""))
    nearest_city = str(v.get("nws_nearest_city", ""))
    nearest_state = str(v.get("nws_nearest_state", ""))
    zone_str = f"{zone} ({zone_name})" if zone and zone_name else zone or "covered"
    parts = [f"NWS zone {zone_str}"]
    if nearest_city and nearest_state:
        parts.append(f"nearest city: {nearest_city}, {nearest_state}")
    elif nearest_city:
        parts.append(f"nearest city: {nearest_city}")
    if office:
        parts.append(f"office {office}")
    if timezone:
        parts.append(f"timezone {timezone}")
    if radar:
        parts.append(f"radar {radar}")
    return ", ".join(parts)


def _broadband_result(report_run: ReportRunContract) -> str:
    records = [r for r in report_run.evidence
               if r.domain == "broadband" and not r.is_source_failure]
    if not records:
        failures = [r for r in report_run.evidence
                    if r.domain == "broadband" and r.is_source_failure]
        if failures:
            return "source failure — broadband availability data unavailable"
        return "not evaluated"
    record = records[0]
    parts: list[str] = []
    provider_count = record.observed_value.get("provider_count")
    max_dl = record.observed_value.get("max_download_mbps")
    tech_types = record.observed_value.get("technology_types")
    has_any = record.observed_value.get("has_any_broadband")
    has_high = record.observed_value.get("has_high_speed_broadband")
    if has_any is False:
        return "no providers reported in FCC BDC for this area"
    if provider_count is not None:
        parts.append(f"{provider_count} provider(s) reported")
    if tech_types and isinstance(tech_types, list) and tech_types:
        parts.append("technologies: " + ", ".join(str(t) for t in tech_types))
    max_ul = record.observed_value.get("max_upload_mbps")
    if max_dl is not None and max_ul is not None:
        parts.append(f"max {max_dl}/{max_ul} Mbps (down/up)")
    elif max_dl is not None:
        parts.append(f"max download: {max_dl} Mbps")
    if has_high:
        parts.append("high-speed available (≥100 Mbps or fiber/cable)")
    return "; ".join(parts) if parts else "broadband data available (see source appendix)"


_SOIL_DOMAINS = frozenset({"soil_septic", "soils"})


def _soil_septic_result(report_run: ReportRunContract) -> str:
    records = [r for r in report_run.evidence
               if r.domain in _SOIL_DOMAINS and not r.is_source_failure]
    if not records:
        failures = [r for r in report_run.evidence
                    if r.domain in _SOIL_DOMAINS and r.is_source_failure]
        if failures:
            return "source failure — soil data unavailable"
        return "not evaluated"
    seen_keys: set[str] = set()
    mapunit_labels: list[str] = []
    for record in records:
        mukey = record.observed_value.get("soil_mapunit_key")
        if isinstance(mukey, str):
            if mukey in seen_keys:
                continue
            seen_keys.add(mukey)
            muname = record.observed_value.get("soil_mapunit_name")
            musym = record.observed_value.get("soil_mapunit_symbol")
            label = (
                str(muname) if isinstance(muname, str)
                else (str(musym) if isinstance(musym, str) else mukey)
            )
            mapunit_labels.append(label)
        else:
            # soils-fixture schema: dominant_map_unit / drainage_class
            dominant = record.observed_value.get("dominant_map_unit")
            drainage = record.observed_value.get("drainage_class")
            if isinstance(dominant, str):
                label = dominant
                if isinstance(drainage, str):
                    label += f" ({drainage})"
                mapunit_labels.append(label)
    count = len(seen_keys) if seen_keys else len(records)
    if mapunit_labels:
        shown = mapunit_labels[:3]
        overflow = len(mapunit_labels) - len(shown)
        suffix = f" +{overflow} more" if overflow else ""
        return (
            f"{count} map unit(s): {', '.join(shown)}{suffix}"
            " (screening only; not a site-specific soil report)"
        )
    return f"{count} soil map unit(s) intersecting screening bbox (screening only)"


def _soil_drainage_result(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence
        if r.domain in _SOIL_DOMAINS and not r.is_source_failure
    ]
    if not records:
        return "not evaluated"
    drainage_classes: list[str] = []
    hydro_groups: list[str] = []
    any_hydric = False
    seen_drain: set[str] = set()
    seen_hydro: set[str] = set()
    for record in records:
        dc = record.observed_value.get("drainage_class")
        if isinstance(dc, str) and dc not in seen_drain:
            seen_drain.add(dc)
            drainage_classes.append(dc)
        hg = record.observed_value.get("hydrologic_group")
        if isinstance(hg, str) and hg not in seen_hydro:
            seen_hydro.add(hg)
            hydro_groups.append(hg)
        hr = record.observed_value.get("hydric_rating")
        if isinstance(hr, str) and hr.lower() == "yes":
            any_hydric = True
    wt_depths: list[float] = []
    slope_pcts: list[float] = []
    for record in records:
        wt = record.observed_value.get("water_table_depth_cm")
        if isinstance(wt, (int, float)) and not isinstance(wt, bool):
            wt_depths.append(float(wt))
        sp = record.observed_value.get("slope_percent")
        if isinstance(sp, (int, float)) and not isinstance(sp, bool):
            slope_pcts.append(float(sp))
    if not drainage_classes and not hydro_groups and not any_hydric and not wt_depths:
        return "not evaluated"
    parts: list[str] = []
    if drainage_classes:
        parts.append(f"drainage: {', '.join(drainage_classes)}")
    if hydro_groups:
        parts.append(f"hydrologic group: {', '.join(hydro_groups)}")
    if any_hydric:
        parts.append("hydric soils present (screening only)")
    if wt_depths:
        min_wt = min(wt_depths)
        parts.append(f"water table ~{min_wt:.0f}cm depth (shallowest recorded unit)")
    if slope_pcts:
        parts.append(f"mapunit slope range ~{min(slope_pcts):.0f}–{max(slope_pcts):.0f}%")
    return "; ".join(parts) + " — screening only; verify with perc test"


_POOR_DRAINAGE = frozenset({"poorly drained", "very poorly drained"})
_MARGINAL_DRAINAGE = frozenset({"somewhat poorly drained"})


def _septic_proxy_confidence(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence
        if r.domain in _SOIL_DOMAINS and not r.is_source_failure
    ]
    if not records:
        source_failures = [r for r in report_run.evidence if r.domain in _SOIL_DOMAINS]
        if source_failures:
            return "unknown (soil data unavailable)"
        return "unknown"
    any_hydric = any(
        str(r.observed_value.get("hydric_rating", "")).lower() == "yes"
        for r in records
    )
    if any_hydric:
        return "low (hydric soils detected — perc test required)"
    drainage_classes = {
        str(r.observed_value["drainage_class"]).lower()
        for r in records
        if isinstance(r.observed_value.get("drainage_class"), str)
    }
    if drainage_classes & _POOR_DRAINAGE:
        return "low (poor drainage detected — perc test required)"
    if drainage_classes & _MARGINAL_DRAINAGE:
        return "medium-low (marginal drainage — perc test strongly recommended)"
    if drainage_classes:
        return "medium (drainage screening favorable — confirm with perc test)"
    return "unknown"


def _mineral_mining_result(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence
        if r.domain == "minerals" and not r.is_source_failure
        and r.evidence_code == "BLM_MLRS_ACTIVE_MINING_CLAIM_CONTEXT"
    ]
    if not records:
        failures = [
            r for r in report_run.evidence
            if r.evidence_code == "BLM_MLRS_SOURCE_FAILURE"
        ]
        return "source failure — BLM MLRS data unavailable" if failures else "not evaluated"
    record = records[0]
    count = record.observed_value.get("blm_active_mining_claim_count")
    if count is not None:
        return f"{count} active federal mining claim record(s) in query bbox (BLM MLRS)"
    return _cell(record.observation)


def _mineral_occurrence_result(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence
        if r.domain == "minerals" and not r.is_source_failure
        and r.evidence_code == "MRDS_MINERAL_OCCURRENCE_SCREEN"
    ]
    if not records:
        failures = [
            r for r in report_run.evidence
            if r.evidence_code == "USGS_MRDS_SOURCE_FAILURE"
        ]
        return "source failure — USGS MRDS data unavailable" if failures else "not evaluated"
    record = records[0]
    count = record.observed_value.get("mineral_occurrence_count")
    if count is not None:
        return (
            f"{count} historical mineral occurrence record(s) in query bbox"
            " (USGS MRDS — systematic updates ceased 2011)"
        )
    return _cell(record.observation)


def _geologic_context_result(report_run: ReportRunContract) -> str:
    records = [
        r for r in report_run.evidence
        if r.domain == "geology" and not r.is_source_failure
    ]
    if not records:
        failures = [
            r for r in report_run.evidence
            if r.evidence_code == "NC_GEOLOGIC_MAP_SOURCE_FAILURE"
        ]
        if failures:
            return "source failure — NCGS geologic map data unavailable"
        return "not evaluated"
    record = records[0]
    parts: list[str] = []
    unit = record.observed_value.get("primary_geologic_unit_label")
    formation = record.observed_value.get("primary_geologic_formation")
    gtypes = record.observed_value.get("geologic_types")
    gbelts = record.observed_value.get("geologic_belts")
    if unit:
        parts.append(f"primary unit: {unit}")
    if formation:
        parts.append(f"formation: {formation}")
    if isinstance(gtypes, list) and gtypes:
        unique = list(dict.fromkeys(str(t) for t in gtypes if t))
        parts.append("type(s): " + ", ".join(unique[:3]))
    if isinstance(gbelts, list) and gbelts:
        unique = list(dict.fromkeys(str(b) for b in gbelts if b))
        parts.append("belt(s): " + ", ".join(unique[:2]))
    return "; ".join(parts) if parts else _cell(record.observation)


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


_DOMAIN_CONTACT: dict[str, str] = {
    "access": "county Register of Deeds, title company, or real estate attorney",
    "zoning": "county planning department",
    "flood": "local floodplain administrator or FEMA map service center",
    "wetlands": "qualified wetland delineator",
    "buildability": "licensed surveyor or civil engineer",
    "terrain": "licensed surveyor or civil engineer",
    "soil_septic": "county health department or licensed septic engineer",
    "soils": "county health department or licensed septic engineer",
    "water": "county health department or state well permit office",
    "env_hazard": "state environmental agency or Phase I ESA provider",
    "minerals": "title attorney or state/federal mineral records office",
    "geology": "state geological survey office",
    "broadband": "local internet service providers",
    "parcels": "county Register of Deeds and licensed surveyor",
    "assessor": "county Tax Administration office",
}


def _task_contact(task: str, report_run: ReportRunContract) -> str:
    for claim in report_run.claims:
        if claim.verification_task and claim.verification_task.strip() == task.strip():
            return _DOMAIN_CONTACT.get(claim.domain, "qualified local reviewer")
    return "qualified local reviewer"


def _verification_rows(report_run: ReportRunContract) -> list[str]:
    if not report_run.verification_tasks:
        return ["| none | none | none | none |"]
    return [
        "| {priority} | {task} | {contact} | {evidence} |".format(
            priority=index,
            task=_cell(task),
            contact=_cell(_task_contact(task, report_run)),
            evidence="source document, official response, or reviewed field note",
        )
        for index, task in enumerate(report_run.verification_tasks, start=1)
    ]


def _source_rows(report_run: ReportRunContract) -> list[str]:
    details = report_run.source_manifest.get("source_details")
    if not isinstance(details, list) or not details:
        return ["| unknown | unknown | screening input | none recorded | unknown |"]
    udo_urls: dict[str, str] = {}
    for ev in report_run.evidence:
        sid = str(ev.source_id)
        if sid not in udo_urls:
            u = ev.observed_value.get("udo_source_url")
            if isinstance(u, str) and u.startswith("http"):
                udo_urls[sid] = u
    rows = []
    for raw_detail in details:
        if not isinstance(raw_detail, dict):
            continue
        detail = dict(raw_detail)
        source_id = str(detail.get("source_id", ""))
        url = detail.get("homepage_url") or udo_urls.get(source_id)
        rows.append(
            "| {source} | {version} | {use} | {caveat} | {url} |".format(
                source=_cell(str(detail.get("name", "unknown"))),
                version=_cell(
                    str(detail.get("last_checked_at") or detail.get("freshness_class") or "unknown")
                ),
                use=_cell(str(detail.get("review_status", "unknown"))),
                caveat=_cell(str(detail.get("license_status", "unknown"))),
                url=_cell(str(url) if url else "unknown"),
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
