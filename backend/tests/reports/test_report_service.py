from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pytest

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
from app.reports.report_repo import ReportRunRepository
from app.reports.service import ReportRunService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def make_service(
    report_repo: ReportRunRepository | None = None,
) -> tuple[
    SourceService,
    AreaService,
    EvidenceService,
    ClaimService,
    ReportRunService,
]:
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
        report_repo=report_repo,
    )
    return source_service, area_service, evidence_service, claim_service, report_service


def register_source(source_service: SourceService) -> SourceContract:
    return source_service.register(
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


def register_area(area_service: AreaService) -> AreaContract:
    return area_service.create(
        AreaContract(
            label="fixture polygon",
            geom_geojson=load_geometry("valid_polygon.geojson"),
            geom_source="report service fixture",
        )
    )


def flood_evidence(area: AreaContract, source: SourceContract) -> EvidenceContract:
    return EvidenceContract(
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


def test_create_report_run_collects_evidence_claims_unknowns_and_caveats() -> None:
    source_service, area_service, evidence_service, _, report_service = make_service()
    source = register_source(source_service)
    area = register_area(area_service)
    observation = evidence_service.create_observation(flood_evidence(area, source))
    failure = evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        method_code="fixture_flood_overlay",
        evidence_code="FLOOD_SOURCE_FAILURE",
        domain="flood",
        caveat="FEMA fixture endpoint returned 503.",
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    assert report_run.status == JobStatus.SUCCEEDED
    assert report_run.finished_at is not None
    assert report_run.evidence == [observation, failure]
    assert [claim.claim_code for claim in report_run.claims] == [
        "FLOOD_001",
        "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        "FLOOD_EVIDENCE_NEEDS_REVIEW",
    ]
    assert [claim.claim_code for claim in report_run.unknowns] == [
        "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        "FLOOD_EVIDENCE_NEEDS_REVIEW",
    ]
    assert [claim.claim_code for claim in report_run.red_flags] == ["FLOOD_001"]
    assert report_run.source_manifest["ruleset_id"] == "homestead_mvp_v0_1"
    assert report_run.source_manifest["ruleset_version"] == "0.1"
    assert report_run.source_manifest["source_ids"] == [str(source.source_id)]
    assert report_run.source_manifest["evidence_count"] == 2
    assert report_run.source_manifest["claim_count"] == 3
    source_details = cast(
        list[dict[str, Any]], report_run.source_manifest["source_details"]
    )
    assert source_details[0]["freshness_class"] == "unknown"
    assert source_details[0]["review_status"] == "approved"
    assert report_run.caveats == [
        "FEMA fixture endpoint returned 503.",
        "Screening fixture only; confirm locally.",
    ]
    assert any(
        "local floodplain administrator" in task
        for task in report_run.verification_tasks
    )
    assert report_run.artifact_metadata["artifact_kind"] == "report_run"
    assert report_run.artifact_metadata["report_schema"] == "report_run_contract_v1"
    assert report_run.artifact_metadata["persistence"] == "memory"
    cost_metrics = cast(dict[str, Any], report_run.artifact_metadata["cost_metrics"])
    assert cost_metrics["evidence_count"] == 2
    assert report_service.get_report_run(report_run.report_run_id) == report_run


def test_create_report_run_is_repeatable_for_same_fixture_evidence() -> None:
    source_service, area_service, evidence_service, claim_service, report_service = (
        make_service()
    )
    source = register_source(source_service)
    area = register_area(area_service)
    evidence_service.create_observation(flood_evidence(area, source))

    first_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    second_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    assert first_run.report_run_id != second_run.report_run_id
    assert [claim.claim_id for claim in second_run.claims] == [
        claim.claim_id for claim in first_run.claims
    ]
    assert claim_service.list_by_area(area.area_id) == first_run.claims


def test_create_report_run_without_evidence_carries_explicit_caveat() -> None:
    _, area_service, _, _, report_service = make_service()
    area = register_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    assert report_run.status == JobStatus.SUCCEEDED
    assert report_run.evidence == []
    assert report_run.claims == []
    assert report_run.unknowns == []
    assert report_run.caveats == [
        "No evidence records were available for this area; report contains no "
        "due-diligence findings."
    ]
    assert report_run.source_manifest["evidence_count"] == 0
    assert report_run.source_manifest["claim_count"] == 0


def test_create_report_run_rejects_unregistered_area() -> None:
    _, _, _, _, report_service = make_service()

    with pytest.raises(ValueError, match="is not registered"):
        report_service.create_report_run(
            area_id=uuid4(),
            intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        )
