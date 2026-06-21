from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from app.area_geometry.area_repo import InMemoryAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.claim_repo import InMemoryClaimRepository
from app.claims_engine.not_evaluated import (
    NOT_EVALUATED_CAVEATS,
    NOT_EVALUATED_CLAIM_CODES,
    NOT_EVALUATED_DOMAINS,
    NOT_EVALUATED_SOURCE_NAME,
)
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.domain.area_contracts import AreaContract
from app.domain.enums import ConfidenceBand, EvidenceType, IntentCode
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService
from app.reports.service import ReportRunService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def test_fixture_report_artifact_semantics_are_stable() -> None:
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
    source = source_service.register(
        SourceContract(
            name="Fixture FEMA Flood Map",
            organization="FEMA",
            domain="flood",
            license_status="approved",
            commercial_use_status="approved",
            redistribution_status="restricted",
            cache_allowed="approved",
            export_allowed="approved-with-restrictions",
            raw_data_allowed="approved",
            ai_use_allowed="restricted",
            review_status="approved",
        )
    )
    area = area_service.create(
        AreaContract(
            label="fixture polygon",
            geom_geojson=load_geometry("valid_polygon.geojson"),
            geom_source="report regression fixture",
        )
    )
    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="FLOOD_ZONE_SCREEN",
            domain="flood",
            observation="Fixture flood source intersects a mapped flood zone.",
            observed_value={"flood_zone": "AE"},
            method_code="fixture_flood_overlay",
            confidence=ConfidenceBand.MEDIUM,
            caveat="Screening fixture only; confirm locally.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    assert stable_report_projection(report_run.model_dump(mode="json")) == {
        "status": "succeeded",
        "intent_code": "homestead_feasibility",
        "source_manifest": {
            "source_count": 2,
            "evidence_count": 7,
            "claim_count": 7,
            "ruleset_id": "homestead_mvp_v0_1",
            "ruleset_version": "0.1",
            "source_names": [
                "Fixture FEMA Flood Map",
                NOT_EVALUATED_SOURCE_NAME,
            ],
        },
        "evidence": [
            {
                "evidence_type": "spatial_intersection",
                "evidence_code": "FLOOD_ZONE_SCREEN",
                "domain": "flood",
                "method_code": "fixture_flood_overlay",
                "confidence": "medium",
                "is_source_failure": False,
                "observed_value": {"flood_zone": "AE"},
            },
            *[
                {
                    "evidence_type": "source_failure",
                    "evidence_code": f"{domain.upper()}_NOT_EVALUATED",
                    "domain": domain,
                    "method_code": f"{domain}_not_evaluated",
                    "confidence": "unknown",
                    "is_source_failure": True,
                    "observed_value": {
                        "failure_reason": "unsupported_screening_domain"
                    },
                }
                for domain in NOT_EVALUATED_DOMAINS
            ],
            {
                "evidence_type": "source_failure",
                "evidence_code": "ZONING_NOT_SCREENED",
                "domain": "zoning",
                "method_code": "zoning_not_screened",
                "confidence": "unknown",
                "is_source_failure": True,
                "observed_value": {"failure_reason": "zoning_not_screened"},
            },
        ],
        "claim_codes": [
            "FLOOD_001",
            *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS],
            "ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
        ],
        "unknown_codes": [
            *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS],
            "ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
        ],
        "red_flag_codes": ["FLOOD_001"],
        "advisory_claim_codes": [],
        "caveats": sorted(
            [
                "Screening fixture only; confirm locally.",
                *[NOT_EVALUATED_CAVEATS[domain] for domain in NOT_EVALUATED_DOMAINS],
                "No zoning source data was available for this area. "
                "Zoning use classification requires verification with the "
                "relevant county planning or zoning authority.",
            ]
        ),
        "artifact_metadata": {
            "artifact_kind": "report_run",
            "report_schema": "report_run_contract_v1",
            "persistence": "memory",
            "validation": {
                "contract_name": "ReportRunContract",
                "contract_version": "report_run_contract_v1",
                "validation_profile": "fixture_report_contract_v1",
                "ruleset_id": "homestead_mvp_v0_1",
                "ruleset_version": "0.1",
            },
            "cost_metrics": {
                "evidence_count": 7,
                "claim_count": 7,
                "unknown_count": 6,
                "advisory_count": 0,
                "red_flag_count": 1,
                "verification_task_count": 7,
                "estimated_total_usd_cents": 0,
                "compute_usd_cents": 0,
                "storage_usd_cents": 0,
                "llm_usd_cents": 0,
                "map_tile_usd_cents": 0,
                "geocoding_usd_cents": 0,
                "paid_data_usd_cents": 0,
                "human_review_usd_cents": 0,
                "human_review_minutes": 0,
            },
        },
    }


def test_chatham_parcel_report_artifact_semantics_are_stable() -> None:
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
    source = source_service.register(
        SourceContract(
            name="Fixture Chatham Parcel Source",
            organization="Chatham County GIS",
            domain="parcels",
            license_status="approved",
            commercial_use_status="approved",
            redistribution_status="restricted",
            cache_allowed="approved",
            export_allowed="approved-with-restrictions",
            raw_data_allowed="approved",
            ai_use_allowed="restricted",
            review_status="approved",
        )
    )
    area = area_service.create(
        AreaContract(
            label="fixture polygon",
            geom_geojson=load_geometry("valid_polygon.geojson"),
            geom_source="report regression fixture",
        )
    )
    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="COUNTY_PARCEL_INTERSECTION",
            domain="parcels",
            observation="County GIS parcel intersects the area of interest.",
            observed_value={
                "intersects": True,
                "parcel_pin": "0060143",
                "parcel_acres": 42.5,
                "parcel_zoning": "RA",
            },
            method_code="chatham_parcels_live",
            confidence=ConfidenceBand.LOW,
            caveat="County GIS parcel data; approximate only; verify with Register of Deeds.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    parcel_domains_not_evaluated = [d for d in NOT_EVALUATED_DOMAINS if d != "parcels"]
    assert stable_report_projection(report_run.model_dump(mode="json")) == {
        "status": "succeeded",
        "intent_code": "homestead_feasibility",
        "source_manifest": {
            "source_count": 2,
            "evidence_count": 6,
            "claim_count": 6,
            "ruleset_id": "homestead_mvp_v0_1",
            "ruleset_version": "0.1",
            "source_names": [
                "Fixture Chatham Parcel Source",
                NOT_EVALUATED_SOURCE_NAME,
            ],
        },
        "evidence": [
            {
                "evidence_type": "spatial_intersection",
                "evidence_code": "COUNTY_PARCEL_INTERSECTION",
                "domain": "parcels",
                "method_code": "chatham_parcels_live",
                "confidence": "low",
                "is_source_failure": False,
                "observed_value": {
                    "intersects": True,
                    "parcel_pin": "0060143",
                    "parcel_acres": 42.5,
                    "parcel_zoning": "RA",
                },
            },
            *[
                {
                    "evidence_type": "source_failure",
                    "evidence_code": f"{domain.upper()}_NOT_EVALUATED",
                    "domain": domain,
                    "method_code": f"{domain}_not_evaluated",
                    "confidence": "unknown",
                    "is_source_failure": True,
                    "observed_value": {
                        "failure_reason": "unsupported_screening_domain"
                    },
                }
                for domain in parcel_domains_not_evaluated
            ],
            {
                "evidence_type": "source_failure",
                "evidence_code": "ZONING_NOT_SCREENED",
                "domain": "zoning",
                "method_code": "zoning_not_screened",
                "confidence": "unknown",
                "is_source_failure": True,
                "observed_value": {"failure_reason": "zoning_not_screened"},
            },
        ],
        "claim_codes": [
            "PARCEL_SCREEN_001",
            *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in parcel_domains_not_evaluated],
            "ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
        ],
        "unknown_codes": [
            "PARCEL_SCREEN_001",
            *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in parcel_domains_not_evaluated],
            "ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
        ],
        "red_flag_codes": [],
        "advisory_claim_codes": [],
        "caveats": sorted(
            [
                "County GIS parcel data; approximate only; verify with Register of Deeds.",
                *[NOT_EVALUATED_CAVEATS[domain] for domain in parcel_domains_not_evaluated],
                "No zoning source data was available for this area. "
                "Zoning use classification requires verification with the "
                "relevant county planning or zoning authority.",
            ]
        ),
        "artifact_metadata": {
            "artifact_kind": "report_run",
            "report_schema": "report_run_contract_v1",
            "persistence": "memory",
            "validation": {
                "contract_name": "ReportRunContract",
                "contract_version": "report_run_contract_v1",
                "validation_profile": "fixture_report_contract_v1",
                "ruleset_id": "homestead_mvp_v0_1",
                "ruleset_version": "0.1",
            },
            "cost_metrics": {
                "evidence_count": 6,
                "claim_count": 6,
                "unknown_count": 6,
                "advisory_count": 0,
                "red_flag_count": 0,
                "verification_task_count": 6,
                "estimated_total_usd_cents": 0,
                "compute_usd_cents": 0,
                "storage_usd_cents": 0,
                "llm_usd_cents": 0,
                "map_tile_usd_cents": 0,
                "geocoding_usd_cents": 0,
                "paid_data_usd_cents": 0,
                "human_review_usd_cents": 0,
                "human_review_minutes": 0,
            },
        },
    }


def test_advisory_claim_report_artifact_semantics_are_stable() -> None:
    """Moderate flood zone evidence fires FLOOD_G002 LOW advisory — pins advisory path shape."""
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
    source = source_service.register(
        SourceContract(
            name="Fixture FEMA Flood Map",
            organization="FEMA",
            domain="flood",
            license_status="approved",
            commercial_use_status="approved",
            redistribution_status="restricted",
            cache_allowed="approved",
            export_allowed="approved-with-restrictions",
            raw_data_allowed="approved",
            ai_use_allowed="restricted",
            review_status="approved",
        )
    )
    area = area_service.create(
        AreaContract(
            label="fixture polygon",
            geom_geojson=load_geometry("valid_polygon.geojson"),
            geom_source="advisory regression fixture",
        )
    )
    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="FLOOD_ZONE_SCREEN",
            domain="flood",
            observation="Fixture flood source intersects a moderate-risk flood zone.",
            observed_value={"flood_zone_code": "X500"},
            method_code="fixture_flood_overlay",
            confidence=ConfidenceBand.MEDIUM,
            caveat="Screening fixture only; confirm locally.",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    projection = stable_report_projection(report_run.model_dump(mode="json"))
    assert projection["red_flag_codes"] == []
    assert projection["advisory_claim_codes"] == ["FLOOD_MODERATE_001"]
    assert projection["artifact_metadata"]["cost_metrics"]["advisory_count"] == 1
    assert projection["artifact_metadata"]["cost_metrics"]["red_flag_count"] == 0


def test_generated_report_source_details_carries_rights_sub_fields() -> None:
    """Writer-presence guard: every source_details entry in a freshly-generated report
    must carry the 5 rights sub-fields (redistribution_status, cache_allowed,
    export_allowed, raw_data_allowed, ai_use_allowed).

    Per ADR lane-d-0021: these fields are optional in the *published schema* because
    pre-tightening v1 artifacts may lack them, but the writer is required to emit them
    for every new report. This test is the regression lock for that writer-level guarantee.
    It does NOT pin golden values — only presence of the keys.
    """
    _RIGHTS_KEYS = {
        "redistribution_status",
        "cache_allowed",
        "export_allowed",
        "raw_data_allowed",
        "ai_use_allowed",
    }
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
    source_service.register(
        SourceContract(
            name="Fixture FEMA Flood Map",
            organization="FEMA",
            domain="flood",
            license_status="approved",
            commercial_use_status="approved",
            redistribution_status="restricted",
            cache_allowed="approved",
            export_allowed="approved-with-restrictions",
            raw_data_allowed="approved",
            ai_use_allowed="restricted",
            review_status="approved",
        )
    )
    area = area_service.create(
        AreaContract(
            label="rights guard fixture polygon",
            geom_geojson=load_geometry("valid_polygon.geojson"),
            geom_source="rights sub-field guard fixture",
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    report_dict = report_run.model_dump(mode="json")
    source_details = cast(
        list[dict[str, Any]],
        report_dict["source_manifest"]["source_details"],
    )
    assert source_details, "source_manifest['source_details'] must be present and non-empty"
    for entry in source_details:
        missing = _RIGHTS_KEYS - entry.keys()
        assert not missing, (
            f"source_details entry '{entry.get('name', '?')}' is missing rights sub-fields: "
            f"{sorted(missing)}"
        )


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def stable_report_projection(report: dict[str, Any]) -> dict[str, Any]:
    source_manifest = cast(dict[str, Any], report["source_manifest"])
    return {
        "status": report["status"],
        "intent_code": report["intent_code"],
        "source_manifest": {
            "source_count": source_manifest["source_count"],
            "evidence_count": source_manifest["evidence_count"],
            "claim_count": source_manifest["claim_count"],
            "ruleset_id": source_manifest["ruleset_id"],
            "ruleset_version": source_manifest["ruleset_version"],
            "source_names": source_manifest["source_names"],
        },
        "evidence": [
            {
                "evidence_type": record["evidence_type"],
                "evidence_code": record["evidence_code"],
                "domain": record["domain"],
                "method_code": record["method_code"],
                "confidence": record["confidence"],
                "is_source_failure": record["is_source_failure"],
                "observed_value": record["observed_value"],
            }
            for record in cast(list[dict[str, Any]], report["evidence"])
        ],
        "claim_codes": [
            claim["claim_code"] for claim in cast(list[dict[str, Any]], report["claims"])
        ],
        "unknown_codes": [
            claim["claim_code"] for claim in cast(list[dict[str, Any]], report["unknowns"])
        ],
        "red_flag_codes": [
            claim["claim_code"] for claim in cast(list[dict[str, Any]], report["red_flags"])
        ],
        "advisory_claim_codes": [
            claim["claim_code"]
            for claim in cast(list[dict[str, Any]], report["advisory_claims"])
        ],
        "caveats": report["caveats"],
        "artifact_metadata": report["artifact_metadata"],
    }
