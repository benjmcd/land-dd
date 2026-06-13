from __future__ import annotations

import json
import re
from pathlib import Path
from typing import cast

from app.area_geometry.area_repo import InMemoryAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.claim_repo import InMemoryClaimRepository
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.domain.area_contracts import AreaContract
from app.domain.enums import ConfidenceBand, EvidenceType, IntentCode, JobStatus
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService
from app.reports.dossier import build_rural_land_dossier
from app.reports.service import ReportRunService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def _load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def _make_services() -> tuple[SourceService, AreaService, EvidenceService, ReportRunService]:
    source_service = SourceService(InMemorySourceRepository())
    area_service = AreaService(InMemoryAreaRepository())
    evidence_repo = InMemoryEvidenceRepository()
    evidence_service = EvidenceService(evidence_repo, source_service, area_service)
    claim_service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    report_service = ReportRunService(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        claim_service=claim_service,
        rule_engine=RuleEngine.from_file(),
    )
    return source_service, area_service, evidence_service, report_service


def _registered_source(source_service: SourceService, domain: str) -> SourceContract:
    return source_service.register(
        SourceContract(
            name=f"Fixture {domain} source",
            organization="fixture",
            domain=domain,
            license_status="approved",
            commercial_use_status="approved",
            redistribution_status="approved",
            cache_allowed="approved",
            export_allowed="approved",
            raw_data_allowed="approved",
            ai_use_allowed="approved",
            review_status="approved",
        )
    )


def _registered_area(area_service: AreaService) -> AreaContract:
    return area_service.create(
        AreaContract(
            label="enrichment-test",
            geom_geojson=_load_geometry("valid_polygon.geojson"),
            geom_source="test",
        )
    )


def test_dossier_renders_fema_flood_zone_code_from_evidence() -> None:
    """Flood zone code in observed_value must appear in the dossier flood section."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "flood")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="FLOOD_ZONE_SCREEN",
            domain="flood",
            method_code="fixture_flood_overlay",
            observation="AE zone intersection",
            observed_value={"flood_zone_code": "AE", "intersection_ratio": 0.72},
            confidence=ConfidenceBand.MEDIUM,
            caveat="Fixture flood screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    assert report_run.status == JobStatus.SUCCEEDED

    dossier = build_rural_land_dossier(report_run)
    assert "FEMA zone AE" in dossier, (
        "Expected flood zone code 'FEMA zone AE' in dossier; dossier flood section: "
        + dossier[dossier.find("## 7."):dossier.find("## 8.")]
    )
    assert "72%" in dossier, "Expected intersection ratio '72%' in dossier"


def test_dossier_flood_zone_description_appears_for_known_codes() -> None:
    """AE zone must include human-readable description in the flood section."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "flood")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="FLOOD_ZONE_SCREEN",
            domain="flood",
            method_code="fema_nfhl_live",
            observation="AE zone intersection.",
            observed_value={"flood_zone_code": "AE"},
            confidence=ConfidenceBand.MEDIUM,
            caveat="FEMA NFHL screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec7 = dossier[dossier.find("## 7."):dossier.find("## 8.")]
    assert "1% annual chance" in sec7, (
        "AE zone must include '1% annual chance' description; got:\n" + sec7
    )


def test_dossier_renders_road_adjacency_observed_from_evidence() -> None:
    """has_public_road_adjacency=True must appear as a positive road result in the dossier."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "access")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
            domain="access",
            method_code="fixture_access_road_adjacency_overlay",
            observation="Public road adjacency found.",
            observed_value={"has_public_road_adjacency": True, "road_distance_m": 0.0},
            confidence=ConfidenceBand.MEDIUM,
            caveat="Fixture road screening only; does not establish legal access.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    assert "public road adjacency observed" in dossier.lower(), (
        "Expected positive road result in access section of dossier"
    )


def test_dossier_renders_no_road_adjacency_from_evidence() -> None:
    """has_public_road_adjacency=False must appear as a negative road result in the dossier."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "access")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
            domain="access",
            method_code="fixture_access_road_adjacency_overlay",
            observation="No public road adjacency found.",
            observed_value={"has_public_road_adjacency": False, "public_road_adjacency": False},
            confidence=ConfidenceBand.MEDIUM,
            caveat="Fixture road screening only.",
            is_negative_evidence=True,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    assert "no public road adjacency observed" in dossier.lower(), (
        "Expected negative road result in access section of dossier"
    )


def test_dossier_access_road_count_surfaces_in_adjacency_result() -> None:
    """road_count from OSM connector must appear in the access road adjacency line."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "access")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
            domain="access",
            method_code="osm_road_adjacency_live",
            observation="OSM Overpass query found road ways adjacent to the query area.",
            observed_value={
                "has_public_road_adjacency": True,
                "road_distance_m": 0.0,
                "road_count": 3,
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="OSM road screening only; does not establish legal access.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec5_start = dossier.find("## 5. Access")
    sec6_start = dossier.find("## 6.")
    section_5 = dossier[sec5_start:sec6_start]
    assert "3 segment" in section_5, (
        "road_count=3 must appear as '3 segment(s)' in Section 5 access line; "
        "got:\n" + section_5
    )


def test_dossier_renders_zoning_district_from_evidence() -> None:
    """zoning_district in observed_value must appear in the dossier zoning section."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "zoning")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_USE_CLASSIFICATION",
            domain="zoning",
            method_code="fixture_zoning_classification_lookup",
            observation="Zoning RA district found.",
            observed_value={
                "zoning_district": "RA",
                "intended_residential_use_allowed": True,
                "intended_residential_use_prohibited": False,
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="Fixture zoning screening only; verify with county planning.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    assert "RA" in dossier, "Expected zoning district 'RA' in dossier zoning section"
    assert "permitted" in dossier.lower() or "allowed" in dossier.lower(), (
        "Expected residential use compatibility text in dossier"
    )


def test_dossier_renders_district_name_and_code_from_chatham_style_evidence() -> None:
    """district_name + zoning_code (Chatham/Brunswick format) must appear in Section 10."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "zoning")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_USE_CLASSIFICATION",
            domain="zoning",
            method_code="chatham_zoning_udo_recorded_lookup",
            observation="Chatham UDO lookup: code 'RA' matches 'Rural Agricultural'.",
            observed_value={
                "zoning_code": "RA",
                "district_name": "Rural Agricultural",
                "use_category": "agricultural_low_intensity_residential",
                "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
                "intended_residential_use_allowed": True,
            },
            confidence=ConfidenceBand.LOW,
            caveat="Chatham County UDO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec10_start = dossier.find("## 10. Zoning")
    sec11_start = dossier.find("## 11.")
    assert sec10_start != -1
    section_10 = dossier[sec10_start:sec11_start]
    assert "Rural Agricultural" in section_10, (
        "Expected 'Rural Agricultural' district name in Section 10; got:\n" + section_10
    )
    assert "RA" in section_10, (
        "Expected zoning code 'RA' in Section 10; got:\n" + section_10
    )
    assert "permitted" in section_10, (
        "Expected 'permitted' use compatibility in Section 10; got:\n" + section_10
    )


def test_dossier_zoning_prohibited_beats_allowed_when_multiple_districts() -> None:
    """prohibited district must override an allowed district in use-compatibility output."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "zoning")
    area = _registered_area(area_service)

    for code, allowed, prohibited in [
        ("RR", True, False),
        ("C-I", False, True),
    ]:
        evidence_service.create_observation(
            EvidenceContract(
                area_id=area.area_id,
                source_id=source.source_id,
                evidence_type=EvidenceType.SOURCE_OBSERVATION,
                evidence_code="ZONING_USE_CLASSIFICATION",
                domain="zoning",
                method_code="brunswick_zoning_udo_recorded_lookup",
                observation=f"Brunswick UDO lookup: code '{code}'.",
                observed_value={
                    "zoning_code": code,
                    "intended_residential_use_allowed": allowed,
                    "intended_residential_use_prohibited": prohibited,
                },
                confidence=ConfidenceBand.LOW,
                caveat="Brunswick County UDO screening only.",
            )
        )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec10_start = dossier.find("## 10. Zoning")
    sec11_start = dossier.find("## 11.")
    section_10 = dossier[sec10_start:sec11_start]
    compat_line = next(
        (ln for ln in section_10.splitlines() if "Intended-use compatibility" in ln), ""
    )
    assert "restricted" in compat_line, (
        "prohibited district must override allowed district in use-compatibility; "
        "got:\n" + compat_line
    )
    assert "permitted" not in compat_line, (
        "should not show 'permitted' on use-compatibility line when any district is prohibited; "
        "got:\n" + compat_line
    )


def test_dossier_red_flag_row_contains_evidence_id_prefix() -> None:
    """Red-flag Evidence column must show a short 8-hex prefix, not just a bare count."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "flood")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="FLOOD_ZONE_SCREEN",
            domain="flood",
            method_code="fixture_flood_overlay",
            observation="Fixture: AE zone intersection.",
            observed_value={"flood_zone": "AE"},
            confidence=ConfidenceBand.MEDIUM,
            caveat="FEMA NFHL screening only; confirm locally.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    assert report_run.red_flags, "Expected FLOOD_001 red flag for this test"

    dossier = build_rural_land_dossier(report_run)

    # The red-flag table Evidence column must include the pattern "N record(s): <hex>"
    # Locate Section 3 (Top Red Flags) in the dossier
    sec3_start = dossier.find("## 3. Top Red Flags")
    sec4_start = dossier.find("## 4.")
    assert sec3_start != -1, "Section 3 not found"
    section_3 = dossier[sec3_start:sec4_start]

    assert re.search(r"\d+ record\(s\):\s*[0-9a-f]{8}", section_3), (
        "Expected evidence ID prefix pattern '1 record(s): <8hexchars>' in Section 3 red flags; "
        f"got:\n{section_3}"
    )
    # Verify no bare "1 record(s)" without the colon-separated IDs
    assert "record(s)" in section_3, "Evidence column should contain 'record(s)'"
    # Confirm the ID prefix is exactly 8 hex chars (first 8 of UUID without dashes)
    red_flag_claim = report_run.red_flags[0]
    expected_prefix = str(red_flag_claim.evidence_ids[0]).replace("-", "")[:8]
    assert expected_prefix in section_3, (
        f"Expected evidence ID prefix '{expected_prefix}' in Section 3; got:\n{section_3}"
    )


def test_dossier_renders_parcel_acreage_from_evidence() -> None:
    """parcel_acres in observed_value must appear in the dossier area identity section."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "parcels")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="COUNTY_PARCEL_INTERSECTION",
            domain="parcels",
            method_code="county_parcel_overlay",
            observation="Parcel boundary intersects the area of interest.",
            observed_value={
                "intersects": True,
                "parcel_pin": "0099887",
                "parcel_acres": 4.75,
                "parcel_zoning": "RA",
            },
            confidence=ConfidenceBand.LOW,
            caveat="Parcel record acreage; verify with county GIS.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    assert "4.75 acres" in dossier, "Expected parcel acreage '4.75 acres' in dossier"
    assert "0099887" in dossier, "Expected parcel PIN '0099887' in dossier"
    section_2_start = dossier.find("## 2.")
    section_3_start = dossier.find("## 3.")
    assert section_2_start != -1, "Expected Section 2 heading in dossier"
    assert section_3_start != -1, "Expected Section 3 heading in dossier"
    section_2 = dossier[section_2_start:section_3_start]
    assert "Zoning designation: RA" in section_2, (
        "Expected parcel zoning 'RA' in Section 2 area identity; got: " + section_2
    )


def test_dossier_renders_parcel_caveat_in_area_identity() -> None:
    """Parcel evidence caveat text must appear in Section 2 Area Identity."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "parcels")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="COUNTY_PARCEL_INTERSECTION",
            domain="parcels",
            method_code="county_parcel_overlay",
            observation="Parcel boundary intersects the area of interest.",
            observed_value={
                "intersects": True,
                "parcel_pin": "0099887",
                "parcel_acres": 4.75,
                "parcel_zoning": "RA",
            },
            confidence=ConfidenceBand.LOW,
            caveat="Parcel boundaries are approximate; not survey-grade.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    section_2_start = dossier.find("## 2.")
    section_3_start = dossier.find("## 3.")
    assert section_2_start != -1
    section_2 = dossier[section_2_start:section_3_start]
    assert "Parcel boundaries are approximate" in section_2, (
        "Expected parcel caveat text in Section 2 area identity; got: " + section_2
    )


def test_dossier_renders_water_monitoring_stations_from_evidence() -> None:
    """plausible_water_context=True + monitoring_station_count must appear in Section 9."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "water")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="WATER_MONITORING_STATION_SCREEN",
            domain="water",
            method_code="fixture_water_monitoring_bbox",
            observation="3 USGS monitoring stations detected in screening bbox.",
            observed_value={
                "plausible_water_context": True,
                "no_plausible_water_context": False,
                "monitoring_station_count": 3,
                "water_context_status": "monitoring_stations_found",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="USGS NWIS screening only; verify active station status.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec9_start = dossier.find("## 9. Water Context")
    sec10_start = dossier.find("## 10.")
    assert sec9_start != -1, "Section 9 not found in dossier"
    section_9 = dossier[sec9_start:sec10_start]
    assert "3 monitoring station(s) detected in screening bbox" in section_9, (
        "Expected station count text in Section 9; got:\n" + section_9
    )


def test_dossier_renders_water_no_monitoring_from_evidence() -> None:
    """no_plausible_water_context=True must appear as a negative result in Section 9."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "water")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="WATER_MONITORING_STATION_SCREEN",
            domain="water",
            method_code="fixture_water_monitoring_bbox",
            observation="No USGS monitoring stations detected in screening bbox.",
            observed_value={
                "plausible_water_context": False,
                "no_plausible_water_context": True,
                "monitoring_station_count": 0,
                "water_context_status": "no_monitoring_stations_found",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="USGS NWIS screening only.",
            is_negative_evidence=True,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec9_start = dossier.find("## 9. Water Context")
    sec10_start = dossier.find("## 10.")
    assert sec9_start != -1, "Section 9 not found in dossier"
    section_9 = dossier[sec9_start:sec10_start]
    assert "no monitoring stations detected in screening bbox" in section_9, (
        "Expected negative monitoring text in Section 9; got:\n" + section_9
    )


def test_dossier_renders_env_hazard_facilities_from_evidence() -> None:
    """has_env_hazard_proximity=True + regulated_facility_count must appear in Section 11."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "env_hazard")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ENV_HAZARD_PROXIMITY_SCREEN",
            domain="env_hazard",
            method_code="fixture_env_hazard_bbox",
            observation="2 regulated facilities detected in screening bbox.",
            observed_value={
                "has_env_hazard_proximity": True,
                "no_env_hazard_proximity": False,
                "regulated_facility_count": 2,
                "env_hazard_status": "regulated_facilities_found",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="EPA ECHO screening only; verify current facility status.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec11_start = dossier.find("## 11. Environmental")
    sec12_start = dossier.find("## 12.")
    assert sec11_start != -1, "Section 11 not found in dossier"
    section_11 = dossier[sec11_start:sec12_start]
    assert "2 regulated facility/facilities detected in screening bbox" in section_11, (
        "Expected facility count text in Section 11; got:\n" + section_11
    )


def test_dossier_renders_jurisdiction_from_parcel_county_evidence() -> None:
    """parcel_county in observed_value must appear as Jurisdiction in Section 2."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "parcels")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="COUNTY_PARCEL_INTERSECTION",
            domain="parcels",
            method_code="county_parcel_overlay",
            observation="Parcel boundary intersects the area of interest",
            observed_value={
                "intersects": True,
                "parcel_county": "Chatham County, NC",
                "parcel_pin": "12345",
                "parcel_acres": 5.0,
                "parcel_zoning": "RA",
            },
            confidence=ConfidenceBand.LOW,
            caveat="Parcel screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec2_start = dossier.find("## 2. Area Identity")
    sec3_start = dossier.find("## 3.")
    assert sec2_start != -1, "Section 2 not found in dossier"
    section_2 = dossier[sec2_start:sec3_start]
    assert "Chatham County, NC" in section_2, (
        "Expected 'Chatham County, NC' in Section 2 Jurisdiction; got:\n" + section_2
    )
    assert "Jurisdiction: unknown" not in section_2, (
        "Section 2 must not show 'unknown' when parcel_county is present"
    )


def test_dossier_renders_ssurgo_mapunit_from_evidence() -> None:
    """intersects_soil_mapunit=True + soil_mapunit_name must appear in Section 8."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "soil_septic")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
            domain="soil_septic",
            method_code="live_usda_ssurgo_soil_mapunit_query",
            observation=(
                "USDA NRCS SSURGO mapunit intersects the query area "
                "for soil/septic/ag screening."
            ),
            observed_value={
                "intersects_soil_mapunit": True,
                "soil_mapunit_key": "123456",
                "soil_mapunit_symbol": "CmB",
                "soil_mapunit_name": "Cecil sandy loam",
                "soil_component_name": "Cecil",
                "drainage_class": "well drained",
                "hydric_rating": "No",
                "hydrologic_group": "B",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="USDA NRCS SSURGO screening only; not a site-specific soil report.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec8_start = dossier.find("## 8. Soil")
    sec9_start = dossier.find("## 9.")
    assert sec8_start != -1, "Section 8 not found in dossier"
    section_8 = dossier[sec8_start:sec9_start]
    assert "Cecil sandy loam" in section_8, (
        "Expected mapunit name 'Cecil sandy loam' in Section 8; got:\n" + section_8
    )
    assert "1 map unit(s)" in section_8, (
        "Expected map unit count in Section 8; got:\n" + section_8
    )
    assert "not evaluated" not in section_8, (
        "Section 8 must not show 'not evaluated' when SSURGO evidence is present"
    )


def test_dossier_soil_shows_major_component_name_and_percent() -> None:
    """Major soil component name and percentage must appear in Section 8."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "soil_septic")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
            domain="soil_septic",
            method_code="live_usda_ssurgo_soil_mapunit_query",
            observation="USDA NRCS SSURGO mapunit intersects the query area.",
            observed_value={
                "intersects_soil_mapunit": True,
                "soil_mapunit_key": "789012",
                "soil_mapunit_name": "Wilkes sandy loam",
                "soil_component_name": "Wilkes",
                "soil_component_percent": 65.0,
                "soil_major_component": True,
                "drainage_class": "well drained",
                "hydric_rating": "No",
                "hydrologic_group": "D",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="USDA NRCS SSURGO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec8_start = dossier.find("## 8. Soil")
    sec9_start = dossier.find("## 9.")
    section_8 = dossier[sec8_start:sec9_start]
    assert "Wilkes" in section_8, (
        "Expected major component name 'Wilkes' in Section 8; got:\n" + section_8
    )
    assert "65%" in section_8, (
        "Expected component percent '65%' in Section 8; got:\n" + section_8
    )
    assert "Major soil components:" in section_8, (
        "Expected 'Major soil components:' label in Section 8; got:\n" + section_8
    )


def test_dossier_renders_soil_source_failure_from_evidence() -> None:
    """SSURGO source failure must appear as a failure message in Section 8."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "soil_septic")
    area = _registered_area(area_service)

    evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        evidence_code="SSURGO_SOURCE_FAILURE",
        domain="soil_septic",
        method_code="live_usda_ssurgo_soil_mapunit_query",
        observation="USDA NRCS SSURGO query did not produce usable source data.",
        observed_value={
            "attempted_url": "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest",
            "failure_reason": "ssurgo_http_error",
            "error_message": "HTTP 503",
            "retryable": True,
        },
        caveat="USDA NRCS SSURGO screening only.",
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec8_start = dossier.find("## 8. Soil")
    sec9_start = dossier.find("## 9.")
    assert sec8_start != -1, "Section 8 not found in dossier"
    section_8 = dossier[sec8_start:sec9_start]
    assert "source failure" in section_8, (
        "Expected 'source failure' text in Section 8 when SSURGO fails; got:\n" + section_8
    )


def test_dossier_confidence_band_medium_when_core_connector_succeeded() -> None:
    """Confidence band must be 'medium' when a core connector ran with clear results."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "flood")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="FLOOD_ZONE_SCREEN",
            domain="flood",
            method_code="fixture_flood_overlay",
            observation="AE zone intersection.",
            observed_value={"flood_zone_code": "AE", "intersection_ratio": 0.5},
            confidence=ConfidenceBand.MEDIUM,
            caveat="FEMA NFHL screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec1_start = dossier.find("## 1.")
    sec2_start = dossier.find("## 2.")
    assert sec1_start != -1
    section_1 = dossier[sec1_start:sec2_start]
    assert "Confidence band: medium" in section_1, (
        "Expected 'medium' confidence band when core flood connector succeeded; "
        "structural unknowns (soil_septic/parcels/resource_context/market_context/assessor) "
        "must not drag it to 'low'. Got:\n" + section_1
    )


def test_dossier_confidence_band_low_when_core_connector_failed() -> None:
    """Confidence band must be 'low' when a core domain connector reports a source failure."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "flood")
    area = _registered_area(area_service)

    evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        evidence_code="FEMA_NFHL_SOURCE_FAILURE",
        domain="flood",
        method_code="fixture_flood_overlay",
        observation="FEMA NFHL query failed.",
        observed_value={"failure_reason": "http_error", "retryable": True},
        caveat="FEMA NFHL screening; verify offline.",
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec1_start = dossier.find("## 1.")
    sec2_start = dossier.find("## 2.")
    assert sec1_start != -1
    section_1 = dossier[sec1_start:sec2_start]
    assert "Confidence band: low" in section_1, (
        "Expected 'low' confidence band when core flood connector failed (non-structural "
        "UNKNOWN claim present); got:\n" + section_1
    )


def test_dossier_confidence_band_unknown_when_no_core_evidence() -> None:
    """Confidence band must be 'unknown' when only structural domains have evidence."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "parcels")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="COUNTY_PARCEL_INTERSECTION",
            domain="parcels",
            method_code="county_parcel_overlay",
            observation="Parcel boundary intersects the area of interest",
            observed_value={"intersects": True, "parcel_pin": "12345"},
            confidence=ConfidenceBand.LOW,
            caveat="Parcel screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec1_start = dossier.find("## 1.")
    sec2_start = dossier.find("## 2.")
    assert sec1_start != -1
    section_1 = dossier[sec1_start:sec2_start]
    assert "Confidence band: unknown" in section_1, (
        "Expected 'unknown' confidence band when only parcel (structural) evidence is "
        "present and no core domain connectors ran; got:\n" + section_1
    )


def test_dossier_renders_env_hazard_no_facilities_from_evidence() -> None:
    """no_env_hazard_proximity=True must appear as a negative result in Section 11."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "env_hazard")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ENV_HAZARD_PROXIMITY_SCREEN",
            domain="env_hazard",
            method_code="fixture_env_hazard_bbox",
            observation="No regulated facilities detected in screening bbox.",
            observed_value={
                "has_env_hazard_proximity": False,
                "no_env_hazard_proximity": True,
                "regulated_facility_count": 0,
                "env_hazard_status": "no_regulated_facilities_found",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="EPA ECHO screening only.",
            is_negative_evidence=True,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec11_start = dossier.find("## 11. Environmental")
    sec12_start = dossier.find("## 12.")
    assert sec11_start != -1, "Section 11 not found in dossier"
    section_11 = dossier[sec11_start:sec12_start]
    assert "no regulated facilities detected in screening bbox" in section_11, (
        "Expected negative facility text in Section 11; got:\n" + section_11
    )


def test_dossier_renders_nwi_wetland_features_from_evidence() -> None:
    """NWI intersects_mapped_wetlands=True must appear in Section 7 wetlands line."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "wetlands")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="NWI_WETLAND_INTERSECTION",
            domain="wetlands",
            method_code="live_usfws_nwi_wetland_intersection_query",
            observation="USFWS NWI: mapped wetland feature intersects query area.",
            observed_value={
                "intersects_mapped_wetlands": True,
                "wetland_type": "Freshwater Emergent Wetland",
                "mapped_wetland_area_sq_m": 4047.0,
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="USFWS NWI screening only; not jurisdictional delineation.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec7_start = dossier.find("## 7. Flood")
    sec8_start = dossier.find("## 8.")
    assert sec7_start != -1, "Section 7 not found in dossier"
    section_7 = dossier[sec7_start:sec8_start]
    assert "1 mapped wetland" in section_7, (
        "Expected wetland feature count in Section 7; got:\n" + section_7
    )
    assert "Freshwater Emergent Wetland" in section_7, (
        "Expected wetland type in Section 7; got:\n" + section_7
    )
    assert "not evaluated" not in section_7.split("USFWS/NWI result:")[1][:80], (
        "Section 7 NWI line must not show 'not evaluated' when wetland evidence present"
    )


def test_dossier_shows_not_evaluated_for_wetlands_with_no_evidence() -> None:
    """With no wetland evidence, Section 7 NWI line must say 'not evaluated'."""
    source_service, area_service, evidence_service, report_service = _make_services()
    area = _registered_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec7_start = dossier.find("## 7. Flood")
    sec8_start = dossier.find("## 8.")
    assert sec7_start != -1
    section_7 = dossier[sec7_start:sec8_start]
    assert "USFWS/NWI result: not evaluated" in section_7, (
        "Expected 'not evaluated' when no wetland evidence; got:\n" + section_7
    )


def test_dossier_renders_buildability_terrain_from_evidence() -> None:
    """USGS TNM terrain relief/slope evidence must appear in Section 6 buildability."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "buildability")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.DERIVED_METRIC,
            evidence_code="USGS_TNM_EPQS_RELIEF_SCREEN",
            domain="buildability",
            method_code="usgs_tnm_epqs_terrain_relief_screen",
            observation="USGS TNM terrain screening: moderate slope area.",
            observed_value={
                "metric_code": "tnm_epqs_sampled_relief_m",
                "value": 12.5,
                "unit": "m",
                "relief_m": 12.5,
                "mean_slope_pct": 6.3,
                "low_slope_area_ratio": 0.68,
                "insufficient_low_slope_buildable_area": False,
            },
            confidence=ConfidenceBand.MEDIUM,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec6_start = dossier.find("## 6. Buildability")
    sec7_start = dossier.find("## 7.")
    assert sec6_start != -1, "Section 6 not found"
    section_6 = dossier[sec6_start:sec7_start]
    assert "terrain relief" in section_6, (
        "Expected terrain relief in Section 6; got:\n" + section_6
    )
    assert "mean slope" in section_6, (
        "Expected mean slope in Section 6; got:\n" + section_6
    )
    assert "low-slope buildable area" in section_6, (
        "Expected buildable area ratio in Section 6; got:\n" + section_6
    )
    assert "no slope constraint" in section_6, (
        "Expected no-constraint text in Section 6; got:\n" + section_6
    )
    assert "not evaluated" not in section_6.split("Terrain / slope screening:")[1][:80], (
        "Section 6 must not show 'not evaluated' when buildability evidence present"
    )


def test_dossier_renders_broadband_availability_from_evidence() -> None:
    """FCC BDC broadband evidence must appear in Section 12 connectivity."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "broadband")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="FCC_BROADBAND_AVAILABILITY_SCREEN",
            domain="broadband",
            method_code="fcc_bdc_broadband_availability_query",
            observation="FCC BDC: 4 provider(s) offer service at this location.",
            observed_value={
                "has_any_broadband": True,
                "has_high_speed_broadband": True,
                "provider_count": 4,
                "technology_types": ["fiber", "cable"],
                "max_download_mbps": 1000,
                "max_upload_mbps": 100,
                "fcc_bdc_lat": 35.85,
                "fcc_bdc_lon": -79.05,
            },
            confidence=ConfidenceBand.LOW,
            caveat="Provider-reported availability; confirm on-site.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec12_start = dossier.find("## 12. Internet")
    sec13_start = dossier.find("## 13.")
    assert sec12_start != -1, "Section 12 not found"
    section_12 = dossier[sec12_start:sec13_start]
    assert "4 provider(s)" in section_12, (
        "Expected provider count in Section 12; got:\n" + section_12
    )
    assert "fiber" in section_12, (
        "Expected technology type in Section 12; got:\n" + section_12
    )
    assert "1000" in section_12, (
        "Expected max download Mbps in Section 12; got:\n" + section_12
    )
    assert "high-speed" in section_12, (
        "Expected high-speed indicator in Section 12; got:\n" + section_12
    )
    assert "not evaluated" not in section_12.split("Broadband availability:")[1][:80], (
        "Section 12 must not show 'not evaluated' when broadband evidence present"
    )


def test_dossier_renders_broadband_no_access_from_evidence() -> None:
    """FCC BDC evidence with has_any_broadband=False must render 'no providers reported'."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "broadband")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="FCC_BROADBAND_AVAILABILITY_SCREEN",
            domain="broadband",
            method_code="fcc_bdc_broadband_availability_query",
            observation="FCC BDC: no broadband service reported at this location.",
            observed_value={
                "has_any_broadband": False,
                "has_high_speed_broadband": False,
                "provider_count": 0,
                "technology_types": [],
                "max_download_mbps": None,
                "max_upload_mbps": None,
                "fcc_bdc_lat": 35.85,
                "fcc_bdc_lon": -79.05,
            },
            confidence=ConfidenceBand.LOW,
            caveat="Provider-reported availability; confirm on-site.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec12_start = dossier.find("## 12. Internet")
    sec13_start = dossier.find("## 13.")
    assert sec12_start != -1, "Section 12 not found"
    section_12 = dossier[sec12_start:sec13_start]
    assert "no providers reported" in section_12, (
        "Expected 'no providers reported' in Section 12 for has_any_broadband=False; got:\n"
        + section_12
    )
    assert "not evaluated" not in section_12.split("Broadband availability:")[1][:80], (
        "Section 12 must not show 'not evaluated' when broadband evidence present"
    )


def test_dossier_renders_advisory_claims_in_section_3() -> None:
    """BLM active mining-claim evidence fires LOW advisory claim visible in Section 3."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "minerals")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="BLM_MLRS_ACTIVE_MINING_CLAIM_CONTEXT",
            domain="minerals",
            method_code="blm_mlrs_active_mining_claims_query",
            observation="BLM MLRS: 2 active mining claim(s) intersect this area.",
            observed_value={
                "blm_active_mining_claim_count": 2,
            },
            confidence=ConfidenceBand.LOW,
            caveat="Federal active mining claims only; does not determine private mineral rights.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    assert len(report_run.advisory_claims) >= 1, (
        "Expected at least one advisory claim from BLM active mining evidence"
    )
    dossier = build_rural_land_dossier(report_run)
    sec3_start = dossier.find("## 3. Top Red Flags")
    sec4_start = dossier.find("## 4.")
    assert sec3_start != -1
    section_3 = dossier[sec3_start:sec4_start]
    assert "Advisory findings" in section_3, (
        "Expected 'Advisory findings' header in Section 3; got:\n" + section_3
    )
    assert "minerals" in section_3, (
        "Expected minerals domain in advisory table; got:\n" + section_3
    )


def test_dossier_shows_not_evaluated_for_buildability_with_no_evidence() -> None:
    """With no buildability evidence, Section 6 terrain line must say 'not evaluated'."""
    source_service, area_service, evidence_service, report_service = _make_services()
    area = _registered_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec6_start = dossier.find("## 6. Buildability")
    sec7_start = dossier.find("## 7.")
    assert sec6_start != -1
    section_6 = dossier[sec6_start:sec7_start]
    assert "not evaluated" in section_6.split("Terrain / slope screening:")[1][:80], (
        "Expected 'not evaluated' when no buildability evidence; got:\n" + section_6
    )


def test_dossier_renders_buildability_source_failure() -> None:
    """USGS TNM source failure must show 'source failure' in Section 6 terrain line."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "buildability")
    area = _registered_area(area_service)

    evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        evidence_code="USGS_TNM_EPQS_SOURCE_FAILURE",
        domain="buildability",
        method_code="usgs_tnm_epqs_terrain_relief_screen",
        observation="USGS TNM EPQS query did not produce usable terrain data.",
        observed_value={
            "failure_reason": "usgs_tnm_request_error",
            "error_message": "HTTP 503",
            "retryable": True,
        },
        caveat="USGS TNM EPQS terrain screening only.",
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec6_start = dossier.find("## 6. Buildability")
    sec7_start = dossier.find("## 7.")
    assert sec6_start != -1
    section_6 = dossier[sec6_start:sec7_start]
    assert "source failure" in section_6, (
        "Expected 'source failure' text in Section 6 when terrain data unavailable; got:\n"
        + section_6
    )


def test_dossier_shows_not_evaluated_for_broadband_with_no_evidence() -> None:
    """With no broadband evidence, Section 12 must say 'not evaluated'."""
    source_service, area_service, evidence_service, report_service = _make_services()
    area = _registered_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec12_start = dossier.find("## 12. Internet")
    sec13_start = dossier.find("## 13.")
    assert sec12_start != -1
    section_12 = dossier[sec12_start:sec13_start]
    assert "not evaluated" in section_12.split("Broadband availability:")[1][:80], (
        "Expected 'not evaluated' when no broadband evidence; got:\n" + section_12
    )


def test_dossier_renders_broadband_source_failure() -> None:
    """FCC BDC source failure must show 'source failure' in Section 12."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "broadband")
    area = _registered_area(area_service)

    evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        evidence_code="BROADBAND_SOURCE_UNAVAILABLE",
        domain="broadband",
        method_code="fcc_bdc_broadband_availability_query",
        observation="FCC BDC query failed to return availability data.",
        observed_value={
            "failure_reason": "fcc_bdc_request_error",
            "error_message": "HTTP 503",
            "retryable": True,
        },
        caveat="FCC BDC broadband availability screening only.",
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec12_start = dossier.find("## 12. Internet")
    sec13_start = dossier.find("## 13.")
    assert sec12_start != -1
    section_12 = dossier[sec12_start:sec13_start]
    assert "source failure" in section_12, (
        "Expected 'source failure' text in Section 12 when broadband data unavailable; got:\n"
        + section_12
    )


def test_dossier_renders_fema_flood_source_failure() -> None:
    """FEMA NFHL source failure must show 'source failure' in Section 7 flood line."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "flood")
    area = _registered_area(area_service)

    evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        evidence_code="FEMA_NFHL_SOURCE_FAILURE",
        domain="flood",
        method_code="live_fema_nfhl_flood_zone_query",
        observation="FEMA NFHL query did not produce usable flood zone data.",
        observed_value={
            "failure_reason": "fema_nfhl_request_error",
            "error_message": "HTTP 503",
            "retryable": True,
        },
        caveat="FEMA NFHL flood zone screening only.",
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec7_start = dossier.find("## 7. Flood")
    sec8_start = dossier.find("## 8.")
    assert sec7_start != -1, "Section 7 not found"
    section_7 = dossier[sec7_start:sec8_start]
    assert "source failure" in section_7, (
        "Expected 'source failure' text in Section 7 flood line when FEMA data unavailable; "
        "got:\n" + section_7
    )


def test_dossier_renders_zoning_source_failure() -> None:
    """Zoning source failure must show 'source failure' in Section 10 zoning district line."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "zoning")
    area = _registered_area(area_service)

    evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        evidence_code="ZONING_SOURCE_FAILURE",
        domain="zoning",
        method_code="live_zoning_query",
        observation="Zoning data query did not produce usable results.",
        observed_value={
            "failure_reason": "zoning_request_error",
            "error_message": "service unavailable",
            "retryable": True,
        },
        caveat="Zoning screening only; verify with county planning.",
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec10_start = dossier.find("## 10. Zoning")
    sec11_start = dossier.find("## 11.")
    assert sec10_start != -1, "Section 10 not found"
    section_10 = dossier[sec10_start:sec11_start]
    assert "source failure" in section_10, (
        "Expected 'source failure' text in Section 10 when zoning data unavailable; got:\n"
        + section_10
    )


def test_dossier_renders_nws_climate_zone_from_evidence() -> None:
    """NWS climate zone evidence must appear in Section 13 climate section."""
    from app.connectors.noaa_climate import NOAA_CLIMATE_CAVEAT

    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "climate")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="NWS_CLIMATE_ZONE",
            domain="climate",
            method_code="live_noaa_nws_point_query",
            observation="NOAA NWS point query: office=RAH, zone=NCZ087, timezone=America/New_York",
            observed_value={
                "has_nws_coverage": True,
                "nws_office_code": "RAH",
                "nws_forecast_zone": "NCZ087",
                "nws_forecast_zone_name": "Southern Chatham",
                "timezone": "America/New_York",
                "nws_radar_station": "KRAX",
            },
            confidence=ConfidenceBand.HIGH,
            caveat=NOAA_CLIMATE_CAVEAT,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec13_start = dossier.find("## 13. Climate")
    sec14_start = dossier.find("## 14.")
    assert sec13_start != -1, "Section 13 (Climate) not found"
    section_13 = dossier[sec13_start:sec14_start]
    assert "NCZ087" in section_13, (
        "Expected forecast zone NCZ087 in Section 13; got:\n" + section_13
    )
    assert "Southern Chatham" in section_13, (
        "Expected zone name 'Southern Chatham' in Section 13; got:\n" + section_13
    )
    assert "RAH" in section_13, (
        "Expected office code RAH in Section 13; got:\n" + section_13
    )


def test_dossier_shows_not_evaluated_for_climate_with_no_evidence() -> None:
    """With no climate evidence, Section 13 climate line must say 'not evaluated'."""
    source_service, area_service, evidence_service, report_service = _make_services()
    area = _registered_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec13_start = dossier.find("## 13. Climate")
    sec14_start = dossier.find("## 14.")
    assert sec13_start != -1, "Section 13 (Climate) not found"
    section_13 = dossier[sec13_start:sec14_start]
    assert "not evaluated" in section_13.split("NWS forecast zone:")[1][:80], (
        "Expected 'not evaluated' when no climate evidence; got:\n" + section_13
    )


def test_dossier_renders_access_caveat_in_section5() -> None:
    """Access evidence caveat text must appear in Section 5 Access Screen."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "access")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
            domain="access",
            method_code="fixture_access_road_adjacency_overlay",
            observation="Public road adjacency found.",
            observed_value={"has_public_road_adjacency": True, "road_distance_m": 0.0},
            confidence=ConfidenceBand.MEDIUM,
            caveat="Road presence does not confirm legal access, right-of-way, or easements.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec5_start = dossier.find("## 5. Access Screen")
    sec6_start = dossier.find("## 6.")
    assert sec5_start != -1, "Section 5 not found in dossier"
    section_5 = dossier[sec5_start:sec6_start]
    assert "Road presence does not confirm legal access" in section_5, (
        "Expected access caveat text in Section 5 Access Screen; got:\n" + section_5
    )


def test_dossier_renders_noaa_nws_source_failure() -> None:
    """NOAA NWS source failure must show 'source failure' in Section 13 climate line."""
    from app.connectors.noaa_climate import NOAA_CLIMATE_CAVEAT

    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "climate")
    area = _registered_area(area_service)

    evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        evidence_code="NOAA_NWS_SOURCE_FAILURE",
        domain="climate",
        method_code="live_noaa_nws_point_query",
        observation="NOAA NWS point query did not produce usable source data.",
        observed_value={
            "failure_reason": "noaa_nws_request_error",
            "error_message": "HTTP 503",
            "retryable": True,
        },
        caveat=NOAA_CLIMATE_CAVEAT,
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec13_start = dossier.find("## 13. Climate")
    sec14_start = dossier.find("## 14.")
    assert sec13_start != -1, "Section 13 (Climate) not found"
    section_13 = dossier[sec13_start:sec14_start]
    assert "source failure" in section_13, (
        "Expected 'source failure' text in Section 13 when NOAA NWS data unavailable; got:\n"
        + section_13
    )


def test_dossier_renders_census_geography_tract_in_area_identity() -> None:
    """Census tract GEOID must appear in Section 2 Area Identity."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "census_geography")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="CENSUS_TIGER_GEOGRAPHY_CONTEXT",
            domain="census_geography",
            method_code="live_census_tiger_geography_query",
            observation="Census TIGERweb query found 1 tract(s).",
            observed_value={
                "primary_census_tract_geoid": "37021060200",
                "primary_census_block_group_geoid": "370210602001",
                "census_tract_count": 1,
                "census_demographics_used": False,
            },
            confidence=ConfidenceBand.LOW,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec2_start = dossier.find("## 2. Area Identity")
    sec3_start = dossier.find("## 3.")
    section_2 = dossier[sec2_start:sec3_start]
    assert "37021060200" in section_2, (
        "Expected census tract GEOID in Section 2; got:\n" + section_2
    )


def test_dossier_renders_blm_mining_claims_in_section14() -> None:
    """BLM active mining claim count must appear in Section 14."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "minerals")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="BLM_MLRS_ACTIVE_MINING_CLAIM_CONTEXT",
            domain="minerals",
            method_code="live_blm_mlrs_mining_claims_query",
            observation="BLM MLRS query found 3 active mining claim record(s).",
            observed_value={
                "blm_active_mining_claim_count": 3,
                "has_blm_active_mining_claim_context": True,
                "mineral_rights_determined": False,
            },
            confidence=ConfidenceBand.LOW,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec14_start = dossier.find("## 14. Resource")
    sec15_start = dossier.find("## 15.")
    assert sec14_start != -1, "Section 14 (Resource) not found"
    section_14 = dossier[sec14_start:sec15_start]
    assert "3 active federal mining claim" in section_14, (
        "Expected BLM mining claim count in Section 14; got:\n" + section_14
    )


def test_dossier_renders_mrds_mineral_occurrences_in_section14() -> None:
    """USGS MRDS mineral occurrence count must appear in Section 14."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "minerals")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="MRDS_MINERAL_OCCURRENCE_SCREEN",
            domain="minerals",
            method_code="live_usgs_mrds_wfs_query",
            observation="USGS MRDS WFS query found 7 historical mineral occurrence record(s).",
            observed_value={
                "mineral_occurrence_count": 7,
                "has_mineral_occurrence_context": True,
                "mineral_rights_determined": False,
            },
            confidence=ConfidenceBand.LOW,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec14_start = dossier.find("## 14. Resource")
    sec15_start = dossier.find("## 15.")
    assert sec14_start != -1
    section_14 = dossier[sec14_start:sec15_start]
    assert "7 historical mineral occurrence" in section_14, (
        "Expected MRDS occurrence count in Section 14; got:\n" + section_14
    )


def test_dossier_mrds_shows_primary_site_name_and_commodity() -> None:
    """Primary site name, commodity code, and dev status must appear in Section 14."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "minerals")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="MRDS_MINERAL_OCCURRENCE_SCREEN",
            domain="minerals",
            method_code="live_usgs_mrds_wfs_query",
            observation="USGS MRDS WFS query found 2 historical mineral occurrence record(s).",
            observed_value={
                "mineral_occurrence_count": 2,
                "has_mineral_occurrence_context": True,
                "mineral_rights_determined": False,
                "primary_mineral_site_name": "Clarkdale Mine",
                "primary_mineral_development_status": "Past Producer",
                "mineral_commodity_codes": ["AU AG", "FE"],
            },
            confidence=ConfidenceBand.LOW,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec14_start = dossier.find("## 14. Resource")
    sec15_start = dossier.find("## 15.")
    section_14 = dossier[sec14_start:sec15_start]
    assert "Clarkdale Mine" in section_14, (
        "Expected primary site name in Section 14; got:\n" + section_14
    )
    assert "AU AG" in section_14, (
        "Expected commodity code in Section 14; got:\n" + section_14
    )
    assert "past producer" in section_14.lower(), (
        "Expected development status in Section 14; got:\n" + section_14
    )
    assert "1 additional record(s)" in section_14, (
        "Expected additional record count in Section 14; got:\n" + section_14
    )


def test_dossier_mrds_zero_occurrences_shows_none_found() -> None:
    """Zero mineral occurrences must produce 'no historical mineral occurrences' output."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "minerals")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="MRDS_MINERAL_OCCURRENCE_SCREEN",
            domain="minerals",
            method_code="live_usgs_mrds_wfs_query",
            observation="USGS MRDS WFS query found 0 historical mineral occurrence record(s).",
            observed_value={
                "mineral_occurrence_count": 0,
                "has_mineral_occurrence_context": False,
                "mineral_rights_determined": False,
            },
            confidence=ConfidenceBand.LOW,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec14_start = dossier.find("## 14. Resource")
    sec15_start = dossier.find("## 15.")
    section_14 = dossier[sec14_start:sec15_start]
    assert "no historical mineral occurrences" in section_14, (
        "Expected 'no historical mineral occurrences' in Section 14; got:\n" + section_14
    )


def test_dossier_renders_ncgs_geologic_unit_in_section14() -> None:
    """NCGS geologic unit label must appear in Section 14."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "geology")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="NC_GEOLOGIC_MAP_UNIT_CONTEXT",
            domain="geology",
            method_code="live_nc_geologic_map_query",
            observation="NCGS 1985 geologic map query found 1 map unit(s).",
            observed_value={
                "primary_geologic_unit_label": "Cha",
                "primary_geologic_formation": "Chauga River Formation",
                "nc_geologic_map_deprecated": True,
                "geologic_hazard_determined": False,
            },
            confidence=ConfidenceBand.LOW,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec14_start = dossier.find("## 14. Resource")
    sec15_start = dossier.find("## 15.")
    assert sec14_start != -1
    section_14 = dossier[sec14_start:sec15_start]
    assert "Chauga River Formation" in section_14, (
        "Expected NCGS formation name in Section 14; got:\n" + section_14
    )


def test_dossier_renders_terrain_fixture_domain_in_buildability_section() -> None:
    """Evidence with domain 'terrain' must appear in Section 6 Buildability Screen."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "terrain")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.DERIVED_METRIC,
            evidence_code="TERRAIN_RELIEF_SCREEN",
            domain="terrain",
            method_code="fixture_terrain_relief_sample",
            observation="Fixture terrain screening: high-relief mountain terrain.",
            observed_value={
                "metric_code": "fixture_terrain_relief_sample",
                "value": 215,
                "unit": "m",
                "relief_m": 215,
            },
            confidence=ConfidenceBand.LOW,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec6_start = dossier.find("## 6. Buildability")
    sec7_start = dossier.find("## 7.")
    assert sec6_start != -1
    section_6 = dossier[sec6_start:sec7_start]
    assert "215" in section_6, (
        "Expected terrain relief value in Section 6 Buildability; got:\n" + section_6
    )


def test_dossier_renders_soils_fixture_domain_in_soil_section() -> None:
    """Evidence with domain 'soils' must appear in Section 8 Soil/Septic Proxy."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "soils")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="SOIL_SURVEY_SCREEN",
            domain="soils",
            method_code="fixture_soils_survey_screen",
            observation="Fixture soil survey: hydric soils.",
            observed_value={
                "dominant_map_unit": "Murville sand",
                "drainage_class": "Very poorly drained",
                "hydric_rating": "yes",
            },
            confidence=ConfidenceBand.LOW,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec8_start = dossier.find("## 8. Soil")
    sec9_start = dossier.find("## 9.")
    assert sec8_start != -1
    section_8 = dossier[sec8_start:sec9_start]
    assert "Murville sand" in section_8, (
        "Expected soils fixture map unit in Section 8; got:\n" + section_8
    )


def test_overall_suitability_screening_clear_when_only_structural_unknowns() -> None:
    """With only structural NOT_EVALUATED unknowns, suitability is 'screening_clear'."""
    source_service, area_service, evidence_service, report_service = _make_services()
    area = _registered_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec1_start = dossier.find("## 1. Executive Summary")
    sec2_start = dossier.find("## 2.")
    assert sec1_start != -1
    section_1 = dossier[sec1_start:sec2_start]
    assert "screening_clear" in section_1, (
        "Expected 'screening_clear' suitability when only structural unknowns; got:\n"
        + section_1
    )


def test_overall_suitability_unknown_when_non_structural_unknown() -> None:
    """A real source-failure UNKNOWN claim (access domain) sets suitability to 'unknown'."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "access")
    area = _registered_area(area_service)

    evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        evidence_code="ACCESS_SOURCE_FAILURE",
        domain="access",
        method_code="osm_road_access_screen",
        observation="OSM road access query failed.",
        observed_value={
            "failure_reason": "osm_timeout",
            "error_message": "timeout",
            "retryable": True,
        },
        caveat="OSM road access screening only.",
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec1_start = dossier.find("## 1. Executive Summary")
    sec2_start = dossier.find("## 2.")
    assert sec1_start != -1
    section_1 = dossier[sec1_start:sec2_start]
    assert "Overall suitability band: unknown" in section_1, (
        "Expected 'unknown' suitability with non-structural UNKNOWN claim; got:\n" + section_1
    )


def test_dossier_renders_soil_drainage_from_ssurgo_evidence() -> None:
    """SSURGO drainage_class and hydrologic_group must appear in Section 8 drainage line."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "soil_septic")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
            domain="soil_septic",
            method_code="live_usda_ssurgo_soil_mapunit_query",
            observation="USDA NRCS SSURGO mapunit intersects the query area.",
            observed_value={
                "intersects_soil_mapunit": True,
                "soil_mapunit_key": "654321",
                "soil_mapunit_symbol": "PaA",
                "soil_mapunit_name": "Pacolet sandy loam",
                "drainage_class": "well drained",
                "hydric_rating": "No",
                "hydrologic_group": "C",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="USDA NRCS SSURGO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec8_start = dossier.find("## 8. Soil")
    sec9_start = dossier.find("## 9.")
    assert sec8_start != -1
    section_8 = dossier[sec8_start:sec9_start]
    assert "well drained" in section_8, (
        "Expected 'well drained' drainage class in Section 8; got:\n" + section_8
    )
    assert "hydrologic group: C" in section_8, (
        "Expected hydrologic group C in Section 8; got:\n" + section_8
    )
    assert "not evaluated" not in section_8.split("- Drainage")[1].split("\n")[0], (
        "Drainage line must not say 'not evaluated' when SSURGO drainage data is present"
    )


def test_dossier_renders_hydric_soils_flag_when_hydric_rating_yes() -> None:
    """hydric_rating=Yes must trigger 'hydric soils present' warning in Section 8."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "soil_septic")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
            domain="soil_septic",
            method_code="live_usda_ssurgo_soil_mapunit_query",
            observation="USDA NRCS SSURGO mapunit intersects the query area.",
            observed_value={
                "intersects_soil_mapunit": True,
                "soil_mapunit_key": "789012",
                "soil_mapunit_name": "Roanoke fine sandy loam",
                "drainage_class": "poorly drained",
                "hydric_rating": "Yes",
                "hydrologic_group": "D",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="USDA NRCS SSURGO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec8_start = dossier.find("## 8. Soil")
    sec9_start = dossier.find("## 9.")
    assert sec8_start != -1
    section_8 = dossier[sec8_start:sec9_start]
    assert "hydric soils present" in section_8, (
        "Expected hydric soils warning in Section 8; got:\n" + section_8
    )
    assert "poorly drained" in section_8, (
        "Expected 'poorly drained' in Section 8; got:\n" + section_8
    )


def test_dossier_septic_proxy_confidence_low_for_poor_drainage() -> None:
    """SSURGO poorly-drained soil sets septic proxy confidence to 'low'."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "soil_septic")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
            domain="soil_septic",
            method_code="live_usda_ssurgo_soil_mapunit_query",
            observation="USDA NRCS SSURGO mapunit intersects the query area.",
            observed_value={
                "intersects_soil_mapunit": True,
                "soil_mapunit_key": "111222",
                "soil_mapunit_name": "Wehadkee silt loam",
                "drainage_class": "poorly drained",
                "hydric_rating": "No",
                "hydrologic_group": "D",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="USDA NRCS SSURGO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec8_start = dossier.find("## 8. Soil")
    sec9_start = dossier.find("## 9.")
    section_8 = dossier[sec8_start:sec9_start]
    assert "low (poor drainage" in section_8, (
        "Expected 'low (poor drainage' in septic proxy confidence; got:\n" + section_8
    )


def test_dossier_septic_proxy_confidence_medium_for_well_drained() -> None:
    """SSURGO well-drained soil sets septic proxy confidence to 'medium'."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "soil_septic")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
            domain="soil_septic",
            method_code="live_usda_ssurgo_soil_mapunit_query",
            observation="USDA NRCS SSURGO mapunit intersects the query area.",
            observed_value={
                "intersects_soil_mapunit": True,
                "soil_mapunit_key": "333444",
                "soil_mapunit_name": "Madison sandy clay loam",
                "drainage_class": "well drained",
                "hydric_rating": "No",
                "hydrologic_group": "B",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="USDA NRCS SSURGO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec8_start = dossier.find("## 8. Soil")
    sec9_start = dossier.find("## 9.")
    section_8 = dossier[sec8_start:sec9_start]
    assert "medium (drainage screening favorable" in section_8, (
        "Expected 'medium' septic proxy confidence for well-drained soil; got:\n" + section_8
    )


def test_dossier_verification_plan_shows_domain_specific_contact() -> None:
    """Verification plan Section 17 must show domain-specific contacts, not generic."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "flood")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="FEMA_NFHL_FLOOD_HAZARD_ZONE_INTERSECTION",
            domain="flood",
            method_code="fema_nfhl_live",
            observation="AE zone intersection.",
            observed_value={
                "flood_zone_code": "AE",
                "intersects_high_risk_flood_zone": True,
                "intersection_ratio": 0.6,
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="FEMA NFHL screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec17_start = dossier.find("## 17. Verification")
    sec18_start = dossier.find("## 18.")
    section_17 = dossier[sec17_start:sec18_start]
    assert "floodplain administrator" in section_17.lower(), (
        "Flood domain verification task must list 'floodplain administrator' as contact; "
        "got:\n" + section_17
    )


def test_dossier_wetland_class_name_preferred_over_raw_type_code() -> None:
    """When wetland_class is present, dossier must show it instead of raw wetland_type."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "wetlands")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="NWI_MAPPED_WETLAND_INTERSECTION",
            domain="wetlands",
            method_code="live_usfws_nwi_wetland_intersection_query",
            observation="USFWS NWI mapped wetland/deepwater feature intersects the query area.",
            observed_value={
                "intersects_mapped_wetlands": True,
                "wetland_type": "L1UBH",
                "wetland_class": "Unconsolidated Bottom",
                "wetland_system": "Lacustrine",
                "mapped_wetland_area_sq_m": 8094.0,
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="USFWS NWI screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec7_start = dossier.find("## 7. Flood")
    sec8_start = dossier.find("## 8.")
    section_7 = dossier[sec7_start:sec8_start]
    assert "Unconsolidated Bottom" in section_7, (
        "wetland_class 'Unconsolidated Bottom' must appear in Section 7; got:\n" + section_7
    )
    assert "L1UBH" not in section_7, (
        "Raw Cowardin code 'L1UBH' must not appear when wetland_class is available; "
        "got:\n" + section_7
    )


def test_dossier_census_tract_name_shown_when_available() -> None:
    """When census connector provides tract/block-group names, dossier must show them."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "census_geography")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="CENSUS_TIGER_GEOGRAPHY_CONTEXT",
            domain="census_geography",
            method_code="live_census_tiger_geography_query",
            observation="Census TIGERweb query found 1 tract(s).",
            observed_value={
                "primary_census_tract_geoid": "37021060200",
                "primary_census_tract_name": "Census Tract 602, Brunswick County",
                "primary_census_block_group_geoid": "370210602001",
                "primary_census_block_group_name": "Block Group 1, Census Tract 602",
                "census_tract_count": 1,
                "census_demographics_used": False,
            },
            confidence=ConfidenceBand.LOW,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec2_start = dossier.find("## 2. Area Identity")
    sec3_start = dossier.find("## 3.")
    section_2 = dossier[sec2_start:sec3_start]
    assert "Census Tract 602, Brunswick County" in section_2, (
        "Expected census tract name in Section 2; got:\n" + section_2
    )
    assert "Block Group 1, Census Tract 602" in section_2, (
        "Expected block group name in Section 2; got:\n" + section_2
    )


def test_dossier_source_appendix_shows_udo_url_when_homepage_url_absent() -> None:
    """Source appendix must fall back to udo_source_url from evidence when homepage_url is null."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "zoning")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="BRUNSWICK_ZONING_DISTRICT_SCREEN",
            domain="zoning",
            method_code="brunswick_zoning_recorded_lookup",
            observation="Brunswick County zoning: RR district found.",
            observed_value={
                "zoning_code": "RR",
                "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
                "intended_residential_use_allowed": True,
                "udo_source_url": "https://brunswick.example.gov/udo.pdf",
            },
            confidence=ConfidenceBand.MEDIUM,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec18_start = dossier.find("## 18. Source Appendix")
    section_18 = dossier[sec18_start:]
    assert "https://brunswick.example.gov/udo.pdf" in section_18, (
        "Source appendix must show udo_source_url when homepage_url is not set; "
        "got:\n" + section_18
    )


def test_dossier_soil_drainage_shows_water_table_depth_when_present() -> None:
    """Soil drainage note must include water_table_depth_cm when available."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "soil_septic")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
            domain="soil_septic",
            method_code="live_usda_ssurgo_soil_mapunit_query",
            observation="USDA NRCS SSURGO mapunit intersects the query area.",
            observed_value={
                "intersects_soil_mapunit": True,
                "soil_mapunit_key": "111222",
                "drainage_class": "Very poorly drained",
                "hydric_rating": "yes",
                "water_table_depth_cm": 10,
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="SSURGO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec8_start = dossier.find("## 8. Soil")
    sec9_start = dossier.find("## 9.")
    section_8 = dossier[sec8_start:sec9_start]
    assert "water table" in section_8.lower(), (
        "Section 8 drainage note must include water table depth when available; "
        "got:\n" + section_8
    )
    assert "10" in section_8, (
        "Section 8 drainage note must show water table depth value (10cm); "
        "got:\n" + section_8
    )


def test_dossier_soil_drainage_shows_slope_range_from_ssurgo() -> None:
    """Soil drainage note must include mapunit slope range from SSURGO slope_percent."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "soil_septic")
    area = _registered_area(area_service)

    for slope, mukey in [(2.0, "aaa111"), (8.0, "bbb222")]:
        evidence_service.create_observation(
            EvidenceContract(
                area_id=area.area_id,
                source_id=source.source_id,
                evidence_type=EvidenceType.SPATIAL_INTERSECTION,
                evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
                domain="soil_septic",
                method_code="live_usda_ssurgo_soil_mapunit_query",
                observation="USDA NRCS SSURGO mapunit intersects the query area.",
                observed_value={
                    "intersects_soil_mapunit": True,
                    "soil_mapunit_key": mukey,
                    "drainage_class": "well drained",
                    "slope_percent": slope,
                },
                confidence=ConfidenceBand.MEDIUM,
                caveat="SSURGO screening only.",
            )
        )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec8_start = dossier.find("## 8. Soil")
    sec9_start = dossier.find("## 9.")
    section_8 = dossier[sec8_start:sec9_start]
    assert "slope" in section_8.lower(), (
        "Section 8 must show slope range from SSURGO; got:\n" + section_8
    )
    assert "2" in section_8 and "8" in section_8, (
        "Section 8 must show min and max slope values; got:\n" + section_8
    )


def test_dossier_geologic_section_shows_types_and_belts_when_present() -> None:
    """Section 14 geologic result must surface geologic_types and geologic_belts."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "geology")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="NC_GEOLOGIC_MAP_UNIT_CONTEXT",
            domain="geology",
            method_code="live_nc_geologic_map_query",
            observation="NCGS 1985 geologic map query found 1 map unit(s).",
            observed_value={
                "primary_geologic_unit_label": "Xls",
                "primary_geologic_formation": "Phyllite and slate",
                "geologic_types": ["metamorphic", "metamorphic"],
                "geologic_belts": ["Carolina slate belt"],
                "geologic_unit_count": 1,
                "nc_geologic_map_deprecated": True,
                "geologic_hazard_determined": False,
                "has_geologic_map_context": True,
                "no_geologic_map_context": False,
                "buildability_determined": False,
            },
            confidence=ConfidenceBand.LOW,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec14_start = dossier.find("## 14. Resource")
    sec15_start = dossier.find("## 15.")
    section_14 = dossier[sec14_start:sec15_start]
    assert "metamorphic" in section_14, (
        "Section 14 must show deduped geologic type; got:\n" + section_14
    )
    assert "Carolina slate belt" in section_14, (
        "Section 14 must show geologic belt; got:\n" + section_14
    )


def test_dossier_climate_shows_nearest_city_when_present() -> None:
    """nws_nearest_city and nws_nearest_state must appear in Section 13 when stored."""
    from app.connectors.noaa_climate import NOAA_CLIMATE_CAVEAT

    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "climate")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="NWS_CLIMATE_ZONE",
            domain="climate",
            method_code="live_noaa_nws_point_query",
            observation="NOAA NWS point query: office=RAH, zone=NCZ087, nearest=Wilmington",
            observed_value={
                "has_nws_coverage": True,
                "nws_office_code": "RAH",
                "nws_forecast_zone": "NCZ087",
                "nws_forecast_zone_name": "Southern Chatham",
                "timezone": "America/New_York",
                "nws_radar_station": "KRAX",
                "nws_nearest_city": "Wilmington",
                "nws_nearest_state": "NC",
            },
            confidence=ConfidenceBand.HIGH,
            caveat=NOAA_CLIMATE_CAVEAT,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec13_start = dossier.find("## 13. Climate")
    sec14_start = dossier.find("## 14.")
    assert sec13_start != -1, "Section 13 (Climate) not found"
    section_13 = dossier[sec13_start:sec14_start]
    assert "Wilmington" in section_13, (
        "Expected nearest city 'Wilmington' in Section 13; got:\n" + section_13
    )
    assert "NC" in section_13, (
        "Expected nearest state 'NC' in Section 13; got:\n" + section_13
    )


def test_dossier_broadband_shows_combined_down_up_speed() -> None:
    """max_upload_mbps must appear alongside download in combined down/up format."""
    from app.connectors.fcc_broadband import FCC_BROADBAND_CAVEAT

    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "broadband")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="FCC_BROADBAND_AVAILABILITY_SCREEN",
            domain="broadband",
            method_code="fcc_bdc_broadband_availability_query",
            observation="FCC BDC: 2 provider(s) offer service at this location.",
            observed_value={
                "has_any_broadband": True,
                "has_high_speed_broadband": False,
                "provider_count": 2,
                "technology_types": ["dsl"],
                "max_download_mbps": 25,
                "max_upload_mbps": 3,
            },
            confidence=ConfidenceBand.LOW,
            caveat=FCC_BROADBAND_CAVEAT,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec12_start = dossier.find("## 12. Internet")
    sec13_start = dossier.find("## 13.")
    assert sec12_start != -1, "Section 12 not found"
    section_12 = dossier[sec12_start:sec13_start]
    assert "25/3" in section_12, (
        "Expected combined down/up speed '25/3' in Section 12; got:\n" + section_12
    )
    assert "down/up" in section_12, (
        "Expected 'down/up' label in Section 12; got:\n" + section_12
    )


def test_dossier_access_shows_highway_types_when_present() -> None:
    """highway_types from OSM evidence must appear in Section 5 access line."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "access")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
            domain="access",
            method_code="live_osm_road_adjacency_bbox_screen",
            observation="OSM Overpass query found road ways adjacent to the query area.",
            observed_value={
                "has_public_road_adjacency": True,
                "public_road_adjacency": True,
                "road_distance_m": 0.0,
                "road_count": 2,
                "highway_types": ["primary", "track"],
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="OSM road screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec5_start = dossier.find("## 5. Access")
    sec6_start = dossier.find("## 6.")
    section_5 = dossier[sec5_start:sec6_start]
    assert "primary" in section_5, (
        "Expected highway type 'primary' in Section 5; got:\n" + section_5
    )
    assert "track" in section_5, (
        "Expected highway type 'track' in Section 5; got:\n" + section_5
    )


def test_dossier_access_road_context_shows_osm_filter_when_roads_present() -> None:
    """Public/private road context line must state OSM filter and highway types when roads exist."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "access")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
            domain="access",
            method_code="live_osm_road_adjacency_bbox_screen",
            observation="OSM Overpass query found road ways adjacent to the query area.",
            observed_value={
                "has_public_road_adjacency": True,
                "public_road_adjacency": True,
                "road_distance_m": 0.0,
                "road_count": 1,
                "highway_types": ["secondary"],
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="OSM road screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec5_start = dossier.find("## 5. Access")
    sec6_start = dossier.find("## 6.")
    section_5 = dossier[sec5_start:sec6_start]
    assert "OSM query filtered to public/unrestricted-access ways" in section_5, (
        "Expected OSM filter context in Section 5; got:\n" + section_5
    )
    assert "secondary" in section_5, (
        "Expected highway type 'secondary' in road context line; got:\n" + section_5
    )


def test_dossier_zoning_shows_udo_note_when_present() -> None:
    """udo_note from zoning evidence must appear in Section 10 district description line."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "zoning")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_USE_CLASSIFICATION",
            domain="zoning",
            method_code="chatham_zoning_udo_recorded_lookup",
            observation="Chatham UDO lookup: code 'RA' matches 'Rural Agricultural'.",
            observed_value={
                "zoning_code": "RA",
                "district_name": "Rural Agricultural",
                "use_category": "agricultural_low_intensity_residential",
                "udo_note": "Rural agricultural district. Verify with Chatham County Planning.",
                "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
                "intended_residential_use_allowed": True,
            },
            confidence=ConfidenceBand.LOW,
            caveat="Chatham County UDO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec10_start = dossier.find("## 10. Zoning")
    sec11_start = dossier.find("## 11.")
    section_10 = dossier[sec10_start:sec11_start]
    assert "Rural agricultural district" in section_10, (
        "Expected udo_note text in Section 10 district description; got:\n" + section_10
    )
    assert "District description:" in section_10, (
        "Expected 'District description:' label in Section 10; got:\n" + section_10
    )


def test_dossier_zoning_district_note_not_available_when_udo_note_absent() -> None:
    """When udo_note is absent, district description line must show 'not available'."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "zoning")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_USE_CLASSIFICATION",
            domain="zoning",
            method_code="chatham_zoning_udo_recorded_lookup",
            observation="Chatham UDO lookup: code 'RA'.",
            observed_value={
                "zoning_code": "RA",
                "district_name": "Rural Agricultural",
                "intended_residential_use_allowed": True,
            },
            confidence=ConfidenceBand.LOW,
            caveat="Chatham County UDO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec10_start = dossier.find("## 10. Zoning")
    sec11_start = dossier.find("## 11.")
    section_10 = dossier[sec10_start:sec11_start]
    assert "District description: not available" in section_10, (
        "Expected 'District description: not available' in Section 10; got:\n" + section_10
    )


def test_dossier_env_contamination_context_shows_count_when_facilities_found() -> None:
    """When ECHO found N > 0 facilities, contamination context must mention the count."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "env_hazard")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ENV_HAZ_FACILITY_SCREEN",
            domain="env_hazard",
            method_code="fixture_env_hazard_bbox",
            observation="3 regulated facilities detected in screening bbox.",
            observed_value={
                "has_env_hazard_proximity": True,
                "regulated_facility_count": 3,
                "env_hazard_status": "regulated_facilities_found",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="EPA ECHO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec11_start = dossier.find("## 11. Environmental")
    sec12_start = dossier.find("## 12.")
    section_11 = dossier[sec11_start:sec12_start]
    assert "3 regulated facility/facilities" in section_11
    assert "Phase I ESA required" in section_11


def test_dossier_env_contamination_context_shows_no_facilities_when_none_found() -> None:
    """When ECHO found 0 facilities, contamination context must say so explicitly."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "env_hazard")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="ENV_HAZ_FACILITY_SCREEN",
            domain="env_hazard",
            method_code="fixture_env_hazard_bbox",
            observation="No regulated facilities detected in screening bbox.",
            observed_value={
                "no_env_hazard_proximity": True,
                "regulated_facility_count": 0,
                "env_hazard_status": "no_regulated_facilities_found",
            },
            confidence=ConfidenceBand.MEDIUM,
            caveat="EPA ECHO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec11_start = dossier.find("## 11. Environmental")
    sec12_start = dossier.find("## 12.")
    section_11 = dossier[sec11_start:sec12_start]
    assert "no regulated facilities in proximity" in section_11


def test_dossier_zoning_overlay_result_surfaces_udo_url() -> None:
    """Overlays line must reference the UDO source URL when zoning evidence is present."""
    source_service, area_service, evidence_service, report_service = _make_services()
    source = _registered_source(source_service, "zoning")
    area = _registered_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_USE_CLASSIFICATION",
            domain="zoning",
            method_code="chatham_zoning_udo_recorded_lookup",
            observation="Chatham UDO lookup: code 'RA'.",
            observed_value={
                "zoning_code": "RA",
                "district_name": "Rural Agricultural",
                "intended_residential_use_allowed": True,
                "udo_source_url": "https://example.gov/udo",
            },
            confidence=ConfidenceBand.LOW,
            caveat="Chatham County UDO screening only.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec10_start = dossier.find("## 10. Zoning")
    sec11_start = dossier.find("## 11.")
    section_10 = dossier[sec10_start:sec11_start]
    assert "not geographically screened" in section_10
    assert "https://example.gov/udo" in section_10
    assert "not captured in recorded fixture" in section_10


def test_dossier_zoning_overlay_result_no_zoning_evidence() -> None:
    """Overlays line must say 'not screened' when no zoning evidence exists."""
    source_service, area_service, evidence_service, report_service = _make_services()
    area = _registered_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    sec10_start = dossier.find("## 10. Zoning")
    sec11_start = dossier.find("## 11.")
    section_10 = dossier[sec10_start:sec11_start]
    assert "not screened — no zoning data available" in section_10
    assert "not captured — no zoning data available" in section_10
