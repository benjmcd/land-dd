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
