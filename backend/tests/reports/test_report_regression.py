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
            "evidence_count": 5,
            "claim_count": 5,
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
        ],
        "claim_codes": [
            "FLOOD_001",
            *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS],
        ],
        "unknown_codes": [
            NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS
        ],
        "red_flag_codes": ["FLOOD_001"],
        "caveats": sorted(
            [
            "Screening fixture only; confirm locally.",
            *[NOT_EVALUATED_CAVEATS[domain] for domain in NOT_EVALUATED_DOMAINS],
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
                "evidence_count": 5,
                "claim_count": 5,
                "unknown_count": 4,
                "red_flag_count": 1,
                "verification_task_count": 5,
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
        "caveats": report["caveats"],
        "artifact_metadata": report["artifact_metadata"],
    }
