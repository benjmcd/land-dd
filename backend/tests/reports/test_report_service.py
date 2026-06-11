from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

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
from app.domain.enums import ConfidenceBand, EvidenceType, IntentCode, JobStatus
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService
from app.reports.report_repo import ReportRunRepository
from app.reports.service import (
    ConnectorReviewQueueItemProtocol,
    ConnectorReviewQueueProtocol,
    ReportRunService,
)
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


@dataclass(frozen=True)
class FakeConnectorReviewQueueItem:
    status: JobStatus
    payload: dict[str, object]


class FakeConnectorReviewQueue:
    def __init__(
        self,
        items: dict[UUID, FakeConnectorReviewQueueItem] | None = None,
    ) -> None:
        self._items = items or {}

    def get_by_ingest_run_id(
        self,
        ingest_run_id: UUID,
    ) -> ConnectorReviewQueueItemProtocol | None:
        return self._items.get(ingest_run_id)


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def make_service(
    report_repo: ReportRunRepository | None = None,
    connector_review_queue: ConnectorReviewQueueProtocol | None = None,
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
        connector_review_queue=connector_review_queue,
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


def fema_live_evidence(
    area: AreaContract,
    source: SourceContract,
    ingest_run_id: UUID,
) -> EvidenceContract:
    return EvidenceContract(
        area_id=area.area_id,
        source_id=source.source_id,
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="FLOOD_ZONE_SCREEN",
        domain="flood",
        observation="FEMA NFHL feature intersects a mapped flood hazard zone.",
        observed_value={"flood_zone_code": "AE", "intersects": True},
        method_code="fema_nfhl_bbox_query_v1",
        confidence=ConfidenceBand.MEDIUM,
        caveat="FEMA NFHL screening only; confirm locally.",
        source_ingest_run_id=ingest_run_id,
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
    assert report_run.evidence[:2] == [observation, failure]
    assert [record.domain for record in report_run.evidence[2:]] == [
        *NOT_EVALUATED_DOMAINS, "zoning"
    ]
    assert [claim.claim_code for claim in report_run.claims] == [
        "FLOOD_001",
        "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        "FLOOD_EVIDENCE_NEEDS_REVIEW",
        *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS],
        "ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
    ]
    assert [claim.claim_code for claim in report_run.unknowns] == [
        "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        "FLOOD_EVIDENCE_NEEDS_REVIEW",
        *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS],
        "ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
    ]
    assert [claim.claim_code for claim in report_run.red_flags] == ["FLOOD_001"]
    assert report_run.source_manifest["ruleset_id"] == "homestead_mvp_v0_1"
    assert report_run.source_manifest["ruleset_version"] == "0.1"
    assert str(source.source_id) in cast(list[str], report_run.source_manifest["source_ids"])
    assert report_run.source_manifest["evidence_count"] == 8
    assert report_run.source_manifest["claim_count"] == 9
    assert report_run.source_manifest["source_count"] == 2
    assert NOT_EVALUATED_SOURCE_NAME in cast(list[str], report_run.source_manifest["source_names"])
    source_details = cast(list[dict[str, Any]], report_run.source_manifest["source_details"])
    assert len(source_details) == 2
    details_by_name = {str(detail["name"]): detail for detail in source_details}
    assert details_by_name["Fixture FEMA Flood Map"]["freshness_class"] == "unknown"
    assert details_by_name["Fixture FEMA Flood Map"]["review_status"] == "approved"
    assert set(report_run.caveats) == {
        "FEMA fixture endpoint returned 503.",
        "Screening fixture only; confirm locally.",
        *[NOT_EVALUATED_CAVEATS[domain] for domain in NOT_EVALUATED_DOMAINS],
        "No zoning source data was available for this area. "
        "Zoning use classification requires verification with the "
        "relevant county planning or zoning authority.",
    }
    assert any("local floodplain administrator" in task for task in report_run.verification_tasks)
    assert report_run.artifact_metadata["artifact_kind"] == "report_run"
    assert report_run.artifact_metadata["report_schema"] == "report_run_contract_v1"
    assert report_run.artifact_metadata["persistence"] == "memory"
    assert report_run.artifact_metadata["validation"] == {
        "contract_name": "ReportRunContract",
        "contract_version": "report_run_contract_v1",
        "validation_profile": "fixture_report_contract_v1",
        "ruleset_id": "homestead_mvp_v0_1",
        "ruleset_version": "0.1",
    }
    cost_metrics = cast(dict[str, Any], report_run.artifact_metadata["cost_metrics"])
    assert cost_metrics["evidence_count"] == 8
    assert cost_metrics["claim_count"] == 9
    assert cost_metrics["unknown_count"] == 8
    assert cost_metrics["red_flag_count"] == 1
    assert cost_metrics["estimated_total_usd_cents"] == 0
    assert cost_metrics["compute_usd_cents"] == 0
    assert cost_metrics["storage_usd_cents"] == 0
    assert cost_metrics["llm_usd_cents"] == 0
    assert cost_metrics["map_tile_usd_cents"] == 0
    assert cost_metrics["geocoding_usd_cents"] == 0
    assert cost_metrics["paid_data_usd_cents"] == 0
    assert cost_metrics["human_review_usd_cents"] == 0
    assert cost_metrics["human_review_minutes"] == 0
    assert report_service.get_report_run(report_run.report_run_id) == report_run


def test_create_report_run_is_repeatable_for_same_fixture_evidence() -> None:
    source_service, area_service, evidence_service, claim_service, report_service = make_service()
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
    assert len(evidence_service.list_by_area(area.area_id)) == 7
    assert [record.domain for record in evidence_service.list_by_area(area.area_id)[1:]] == [
        *NOT_EVALUATED_DOMAINS, "zoning"
    ]
    assert [source.name for source in source_service.list_all()].count(
        NOT_EVALUATED_SOURCE_NAME
    ) == 1


def test_create_report_run_without_source_evidence_surfaces_not_evaluated_unknowns() -> None:
    source_service, area_service, evidence_service, _, report_service = make_service()
    area = register_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    assert report_run.status == JobStatus.SUCCEEDED
    assert [record.domain for record in report_run.evidence] == [*NOT_EVALUATED_DOMAINS, "zoning"]
    assert all(record.is_source_failure for record in report_run.evidence)
    assert evidence_service.list_by_area(area.area_id) == report_run.evidence
    assert [claim.claim_code for claim in report_run.claims] == [
        *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS],
        "ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
    ]
    assert report_run.claims == report_run.unknowns
    assert report_run.red_flags == []
    assert set(report_run.caveats) == {
        *[NOT_EVALUATED_CAVEATS[domain] for domain in NOT_EVALUATED_DOMAINS],
        "No zoning source data was available for this area. "
        "Zoning use classification requires verification with the "
        "relevant county planning or zoning authority.",
    }
    assert report_run.source_manifest["evidence_count"] == 6
    assert report_run.source_manifest["claim_count"] == 6
    assert report_run.source_manifest["source_count"] == 1
    assert report_run.source_manifest["source_names"] == [NOT_EVALUATED_SOURCE_NAME]
    assert [source.name for source in source_service.list_all()] == [NOT_EVALUATED_SOURCE_NAME]
    cost_metrics = cast(dict[str, Any], report_run.artifact_metadata["cost_metrics"])
    assert cost_metrics["evidence_count"] == 6
    assert cost_metrics["claim_count"] == 6
    assert cost_metrics["unknown_count"] == 6
    assert cost_metrics["red_flag_count"] == 0
    assert cost_metrics["estimated_total_usd_cents"] == 0
    assert cost_metrics["human_review_minutes"] == 0


def test_create_report_run_excludes_unapproved_connector_evidence() -> None:
    source_service, area_service, evidence_service, _, report_service = make_service()
    source = register_source(source_service)
    area = register_area(area_service)
    ingest_run_id = uuid4()
    stored = evidence_service.create_observation(
        fema_live_evidence(area, source, ingest_run_id)
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    assert stored not in report_run.evidence
    assert [claim.claim_code for claim in report_run.claims] == [
        *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS],
        "ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
    ]
    assert report_run.red_flags == []
    assert report_run.source_manifest["evidence_count"] == 6


def test_create_report_run_includes_approved_connector_evidence() -> None:
    ingest_run_id = uuid4()
    review_queue = FakeConnectorReviewQueue(
        {
            ingest_run_id: FakeConnectorReviewQueueItem(
                status=JobStatus.SUCCEEDED,
                payload={
                    "review_decision": {
                        "action": "approve_for_connector_qa",
                        "reviewer_id": "fixture-reviewer",
                    }
                },
            )
        }
    )
    source_service, area_service, evidence_service, _, report_service = make_service(
        connector_review_queue=review_queue,
    )
    source = register_source(source_service)
    area = register_area(area_service)
    stored = evidence_service.create_observation(
        fema_live_evidence(area, source, ingest_run_id)
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    assert report_run.evidence[0] == stored
    assert "FLOOD_001" in [claim.claim_code for claim in report_run.claims]
    assert report_run.red_flags[0].claim_code == "FLOOD_001"
    assert "FEMA NFHL screening only; confirm locally." in report_run.caveats
    assert report_run.source_manifest["evidence_count"] == 7


def test_create_report_run_rejects_unregistered_area() -> None:
    _, _, _, _, report_service = make_service()

    with pytest.raises(ValueError, match="is not registered"):
        report_service.create_report_run(
            area_id=uuid4(),
            intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        )
