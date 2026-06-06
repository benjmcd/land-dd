from __future__ import annotations

import json
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
