from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

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
from app.domain.enums import (
    ConfidenceBand,
    EvidenceType,
    IntentCode,
    JobStatus,
    ReportReviewStatus,
)
from app.domain.evidence_contracts import EvidenceContract
from app.domain.report_contracts import ReportRunJobContract
from app.domain.source_contracts import SourceContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService
from app.reports import service as report_service_module
from app.reports.job_repo import InMemoryReportRunJobRepository
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
    report_job_repo: InMemoryReportRunJobRepository | None = None,
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
        report_job_repo=report_job_repo,
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
    assert report_run.review_status == ReportReviewStatus.NEEDS_REVIEW
    assert report_run.review_actions == []
    assert report_run.finished_at is not None
    assert report_run.evidence[:2] == [observation, failure]
    assert [record.domain for record in report_run.evidence[2:]] == list(NOT_EVALUATED_DOMAINS)
    assert [claim.claim_code for claim in report_run.claims] == [
        "FLOOD_001",
        "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        "FLOOD_EVIDENCE_NEEDS_REVIEW",
        *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS],
    ]
    assert [claim.claim_code for claim in report_run.unknowns] == [
        "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        "FLOOD_EVIDENCE_NEEDS_REVIEW",
        *[NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS],
    ]
    assert [claim.claim_code for claim in report_run.red_flags] == ["FLOOD_001"]
    assert report_run.source_manifest["ruleset_id"] == "homestead_mvp_v0_1"
    assert report_run.source_manifest["ruleset_version"] == "0.1"
    assert str(source.source_id) in cast(list[str], report_run.source_manifest["source_ids"])
    assert report_run.source_manifest["evidence_count"] == 6
    assert report_run.source_manifest["claim_count"] == 7
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
    }
    assert any("local floodplain administrator" in task for task in report_run.verification_tasks)
    assert report_run.artifact_metadata["artifact_kind"] == "report_run"
    assert report_run.artifact_metadata["report_schema"] == "report_run_contract_v1"
    assert report_run.artifact_metadata["persistence"] == "memory"
    cost_metrics = cast(dict[str, Any], report_run.artifact_metadata["cost_metrics"])
    assert cost_metrics["evidence_count"] == 6
    assert cost_metrics["claim_count"] == 7
    assert cost_metrics["unknown_count"] == 6
    assert cost_metrics["red_flag_count"] == 1
    assert report_service.get_report_run(report_run.report_run_id) == report_run


def test_report_review_lifecycle_approves_and_supersedes_report() -> None:
    _, area_service, _, _, report_service = make_service()
    area = register_area(area_service)
    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    approved = report_service.approve_report_run(
        report_run.report_run_id,
        reviewer_id="reviewer-1",
        reason="ready for beta handoff",
    )

    assert approved.review_status == ReportReviewStatus.APPROVED
    assert approved.reviewed_by == "reviewer-1"
    assert approved.reviewed_at is not None
    assert len(approved.review_actions) == 1
    assert approved.review_actions[0].from_status == ReportReviewStatus.NEEDS_REVIEW
    assert approved.review_actions[0].to_status == ReportReviewStatus.APPROVED
    assert approved.review_actions[0].reason == "ready for beta handoff"

    superseded = report_service.supersede_report_run(
        report_run.report_run_id,
        reviewer_id="reviewer-2",
        reason="new source evidence available",
    )

    assert superseded.review_status == ReportReviewStatus.SUPERSEDED
    assert superseded.reviewed_by == "reviewer-2"
    assert len(superseded.review_actions) == 2
    assert superseded.review_actions[-1].from_status == ReportReviewStatus.APPROVED
    assert superseded.review_actions[-1].to_status == ReportReviewStatus.SUPERSEDED
    assert report_service.get_report_run(report_run.report_run_id) == superseded


def test_render_approved_dossier_requires_approved_report_and_preserves_caveats() -> None:
    source_service, area_service, evidence_service, _, report_service = make_service()
    source = register_source(source_service)
    area = register_area(area_service)
    evidence_service.create_observation(flood_evidence(area, source))
    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    with pytest.raises(ValueError, match="requires approved review status"):
        report_service.render_approved_dossier(report_run.report_run_id)

    approved = report_service.approve_report_run(
        report_run.report_run_id,
        reviewer_id="reviewer-1",
        reason="ready for dossier delivery",
    )
    dossier = report_service.render_approved_dossier(approved.report_run_id)

    assert dossier is not None
    assert "# Rural Land Dossier" in dossier
    assert f"- Report run ID: {approved.report_run_id}" in dossier
    assert "- Review status: approved" in dossier
    assert "Fixture FEMA Flood Map" in dossier
    assert "Screening fixture only; confirm locally." in dossier
    assert "Road proximity is a physical proxy only" in dossier
    assert "not legal, title, water-rights, insurance, lending, appraisal" in dossier


def test_render_approved_dossier_blocks_forbidden_report_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, area_service, _, _, report_service = make_service()
    area = register_area(area_service)
    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    approved = report_service.approve_report_run(
        report_run.report_run_id,
        reviewer_id="reviewer-1",
        reason="ready for dossier delivery",
    )
    monkeypatch.setattr(
        report_service_module,
        "build_rural_land_dossier",
        lambda _report_run: "This parcel has legal access.",
    )

    with pytest.raises(ValueError, match="forbidden language"):
        report_service.render_approved_dossier(approved.report_run_id)


def test_report_review_lifecycle_rejects_report_with_required_reason() -> None:
    _, area_service, _, _, report_service = make_service()
    area = register_area(area_service)
    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    with pytest.raises(ValueError, match="reason is required"):
        report_service.reject_report_run(
            report_run.report_run_id,
            reviewer_id="reviewer-1",
            reason="",
        )

    rejected = report_service.reject_report_run(
        report_run.report_run_id,
        reviewer_id="reviewer-1",
        reason="missing source caveat",
    )

    assert rejected.review_status == ReportReviewStatus.REJECTED
    assert rejected.review_actions[-1].to_status == ReportReviewStatus.REJECTED
    with pytest.raises(ValueError, match="cannot mark report review approved from rejected"):
        report_service.approve_report_run(
            report_run.report_run_id,
            reviewer_id="reviewer-2",
        )


def test_report_review_lifecycle_requires_known_report_and_reviewer() -> None:
    _, area_service, _, _, report_service = make_service()
    area = register_area(area_service)
    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    with pytest.raises(ValueError, match="reviewer_id is required"):
        report_service.approve_report_run(report_run.report_run_id, reviewer_id=" ")
    with pytest.raises(ValueError, match="was not found"):
        report_service.approve_report_run(uuid4(), reviewer_id="reviewer-1")


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
    assert len(evidence_service.list_by_area(area.area_id)) == 5
    assert [record.domain for record in evidence_service.list_by_area(area.area_id)[1:]] == list(
        NOT_EVALUATED_DOMAINS
    )
    assert [source.name for source in source_service.list_all()].count(
        NOT_EVALUATED_SOURCE_NAME
    ) == 1


def test_create_report_run_reuses_matching_idempotency_key() -> None:
    _, area_service, _, _, report_service = make_service()
    area = register_area(area_service)
    workspace_id = uuid4()
    requested_by = uuid4()

    first_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        workspace_id=workspace_id,
        requested_by=requested_by,
        idempotency_key=" report-key-1 ",
    )
    second_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        workspace_id=workspace_id,
        requested_by=requested_by,
        idempotency_key="report-key-1",
    )

    assert second_run == first_run
    assert first_run.workspace_id == workspace_id
    assert first_run.requested_by == requested_by
    assert first_run.idempotency_key == "report-key-1"
    assert report_service.list_report_runs(workspace_id=workspace_id) == [first_run]

    other_workspace_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        workspace_id=uuid4(),
        requested_by=requested_by,
        idempotency_key="report-key-1",
    )

    assert other_workspace_run.report_run_id != first_run.report_run_id
    with pytest.raises(ValueError, match="workspace_id is required"):
        report_service.create_report_run(
            area_id=area.area_id,
            intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
            requested_by=requested_by,
            idempotency_key="report-key-2",
        )


def test_submit_report_run_job_is_idempotent_and_requires_key() -> None:
    _, area_service, _, _, report_service = make_service()
    area = register_area(area_service)
    workspace_id = uuid4()

    first_job = report_service.submit_report_run_job(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        workspace_id=workspace_id,
        idempotency_key=" async-key-1 ",
    )
    second_job = report_service.submit_report_run_job(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        workspace_id=workspace_id,
        idempotency_key="async-key-1",
    )

    assert second_job == first_job
    assert first_job.status == JobStatus.QUEUED
    assert first_job.workspace_id == workspace_id
    assert first_job.idempotency_key == "async-key-1"
    assert report_service.get_report_run_job(first_job.job_id) == first_job
    other_workspace_job = report_service.submit_report_run_job(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        workspace_id=uuid4(),
        idempotency_key="async-key-1",
    )
    assert other_workspace_job.job_id != first_job.job_id
    with pytest.raises(ValueError, match="workspace_id is required"):
        report_service.submit_report_run_job(
            area_id=area.area_id,
            intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
            requested_by=uuid4(),
            idempotency_key="async-key-2",
        )
    with pytest.raises(ValueError, match="idempotency_key is required"):
        report_service.submit_report_run_job(
            area_id=area.area_id,
            intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
            idempotency_key=" ",
        )


def test_execute_next_report_run_job_creates_report_and_finishes_job() -> None:
    _, area_service, _, _, report_service = make_service()
    area = register_area(area_service)
    job = report_service.submit_report_run_job(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        idempotency_key="execute-key-1",
    )

    executed = report_service.execute_next_report_run_job(worker_id=" report-worker-1 ")

    assert executed is not None
    assert executed.job_id == job.job_id
    assert executed.status == JobStatus.SUCCEEDED
    assert executed.attempts == 1
    assert executed.locked_by is None
    assert executed.report_run_id is not None
    report_run = report_service.get_report_run(executed.report_run_id)
    assert report_run is not None
    assert report_run.idempotency_key == "execute-key-1"
    assert report_run.review_status == ReportReviewStatus.NEEDS_REVIEW
    assert report_service.execute_next_report_run_job(worker_id="report-worker-1") is None


def test_execute_next_report_run_job_respects_workspace_filter() -> None:
    _, area_service, _, _, report_service = make_service()
    area = register_area(area_service)
    workspace_id = uuid4()
    other_workspace_id = uuid4()
    job = report_service.submit_report_run_job(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        workspace_id=workspace_id,
        idempotency_key="workspace-execute-key-1",
    )

    assert (
        report_service.execute_next_report_run_job(
            worker_id="report-worker-1",
            workspace_id=other_workspace_id,
        )
        is None
    )

    executed = report_service.execute_next_report_run_job(
        worker_id="report-worker-1",
        workspace_id=workspace_id,
    )

    assert executed is not None
    assert executed.job_id == job.job_id
    assert executed.workspace_id == workspace_id
    assert executed.status == JobStatus.SUCCEEDED


def test_execute_next_report_run_job_marks_failed_and_allows_requeue() -> None:
    report_job_repo = InMemoryReportRunJobRepository()
    _, _, _, _, report_service = make_service(report_job_repo=report_job_repo)
    missing_area_id = uuid4()
    report_job_repo.enqueue(
        ReportRunJobContract(
            area_id=missing_area_id,
            intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
            idempotency_key="failing-job-key-1",
        )
    )

    failed = report_service.execute_next_report_run_job(worker_id="report-worker-1")

    assert failed is not None
    assert failed.status == JobStatus.FAILED
    assert failed.last_error is not None
    assert "is not registered" in failed.last_error
    requeued = report_service.requeue_report_run_job(
        failed.job_id,
        reason="retry after area registration",
    )
    assert requeued.status == JobStatus.QUEUED
    assert requeued.attempts == 1


def test_create_report_run_without_source_evidence_surfaces_not_evaluated_unknowns() -> None:
    source_service, area_service, evidence_service, _, report_service = make_service()
    area = register_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    assert report_run.status == JobStatus.SUCCEEDED
    assert [record.domain for record in report_run.evidence] == list(NOT_EVALUATED_DOMAINS)
    assert all(record.is_source_failure for record in report_run.evidence)
    assert evidence_service.list_by_area(area.area_id) == report_run.evidence
    assert [claim.claim_code for claim in report_run.claims] == [
        NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS
    ]
    assert report_run.claims == report_run.unknowns
    assert report_run.red_flags == []
    assert set(report_run.caveats) == {
        NOT_EVALUATED_CAVEATS[domain] for domain in NOT_EVALUATED_DOMAINS
    }
    assert report_run.source_manifest["evidence_count"] == 4
    assert report_run.source_manifest["claim_count"] == 4
    assert report_run.source_manifest["source_count"] == 1
    assert report_run.source_manifest["source_names"] == [NOT_EVALUATED_SOURCE_NAME]
    assert [source.name for source in source_service.list_all()] == [NOT_EVALUATED_SOURCE_NAME]
    cost_metrics = cast(dict[str, Any], report_run.artifact_metadata["cost_metrics"])
    assert cost_metrics["evidence_count"] == 4
    assert cost_metrics["claim_count"] == 4
    assert cost_metrics["unknown_count"] == 4
    assert cost_metrics["red_flag_count"] == 0


def test_create_report_run_rejects_unregistered_area() -> None:
    _, _, _, _, report_service = make_service()

    with pytest.raises(ValueError, match="is not registered"):
        report_service.create_report_run(
            area_id=uuid4(),
            intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        )
