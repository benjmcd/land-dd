"""End-to-end fixture-ingestion regression for the extended `broadband` domain."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from app.area_geometry.area_repo import InMemoryAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.claim_repo import InMemoryClaimRepository
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.connectors import (
    StaticBroadbandFixtureConnector,
    build_fixture_workflow_with_public_services,
    evaluate_broadband_fixture_quality,
)
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode, JobStatus
from app.domain.report_contracts import ReportRunContract
from app.domain.source_contracts import SourceContract, SourceRetrievalRunContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService
from app.reports.dossier import build_rural_land_dossier
from app.reports.service import ReportRunService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository

GOLDEN_AOI_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "golden_aois"
CONNECTOR_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"

_FIXTURE_AREA_ID = UUID("44444444-4444-4444-8444-444444444444")
_FIXTURE_SOURCE_ID = UUID("55555555-5555-4555-8555-555555555555")

FORBIDDEN_PHRASES = (
    "You can build here",
    "This parcel has legal access",
    "This property has water rights",
    "This is a good investment",
    "This land is safe",
    "This property is worth",
    "guaranteed broadband",
    "guaranteed service",
)


class _InMemoryRetrievalPort:
    def __init__(self) -> None:
        self._store: dict[UUID, SourceRetrievalRunContract] = {}

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        return ingest_run_id in self._store

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        self._store[retrieval_run.ingest_run_id] = retrieval_run
        return retrieval_run


def _make_services() -> tuple[SourceService, AreaService, EvidenceService, ClaimService]:
    source_service = SourceService(InMemorySourceRepository())
    area_service = AreaService(InMemoryAreaRepository())
    evidence_repo = InMemoryEvidenceRepository()
    evidence_service = EvidenceService(evidence_repo, source_service, area_service)
    claim_service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    return source_service, area_service, evidence_service, claim_service


def _load_geometry(path: Path) -> dict[str, object]:
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    if data.get("type") == "Feature":
        return data["geometry"]  # type: ignore[no-any-return]
    return data


def _register_fixture_source(source_service: SourceService) -> None:
    source_service.register(
        SourceContract(
            source_id=_FIXTURE_SOURCE_ID,
            name="MVP Fixture Source",
            organization="fixture",
            domain="fixture",
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


def _create_area(area_service: AreaService, label: str) -> None:
    area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            label=label,
            geom_geojson=_load_geometry(GOLDEN_AOI_DIR / "bun_slope.geojson"),
            geom_source="golden-aoi-fixture",
        )
    )


def _ingest_broadband_fixture(
    evidence_service: EvidenceService,
    retrieval_port: _InMemoryRetrievalPort,
    fixture_file: str,
) -> None:
    workflow = build_fixture_workflow_with_public_services(
        retrieval_provenance_port=retrieval_port,
        evidence_service=evidence_service,
        connector=StaticBroadbandFixtureConnector(),
        quality_evaluator=evaluate_broadband_fixture_quality,
    )
    workflow.ingest_fixture(CONNECTOR_DIR / fixture_file)


def _run_report(
    source_service: SourceService,
    area_service: AreaService,
    evidence_service: EvidenceService,
    claim_service: ClaimService,
) -> ReportRunContract:
    report_service = ReportRunService(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        claim_service=claim_service,
        rule_engine=RuleEngine.from_file(),
    )
    return report_service.create_report_run(
        area_id=_FIXTURE_AREA_ID,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )


def _assert_no_overclaim(dossier: str) -> None:
    dossier_lower = dossier.lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase.lower() not in dossier_lower, (
            f"Forbidden phrase {phrase!r} found in Markdown dossier"
        )
    assert "## 1. Executive Summary" in dossier


def _section(dossier: str, heading: str, next_heading: str) -> str:
    section_start = dossier.find(heading)
    next_start = dossier.find(next_heading)
    assert section_start != -1, f"{heading} not found"
    assert next_start != -1, f"{next_heading} not found"
    return dossier[section_start:next_start]


def test_buncombe_broadband_no_access_end_to_end() -> None:
    """No-provider fixture flows to a BROADBAND_NO_ACCESS_001 advisory claim."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()
    _register_fixture_source(source_service)
    _create_area(area_service, "buncombe-broadband-no-access")
    _ingest_broadband_fixture(
        evidence_service,
        retrieval_port,
        "nc_buncombe_bun_broadband_no_access.json",
    )

    report_run = _run_report(
        source_service, area_service, evidence_service, claim_service
    )
    assert report_run.status == JobStatus.SUCCEEDED

    broadband_evidence = [
        rec
        for rec in report_run.evidence
        if rec.domain == "broadband" and not rec.is_source_failure
    ]
    assert len(broadband_evidence) == 1
    assert broadband_evidence[0].observed_value["has_any_broadband"] is False
    assert "does not guarantee service" in (broadband_evidence[0].caveat or "")
    assert "Verify internet options directly" in (broadband_evidence[0].caveat or "")

    no_access_claims = [
        claim
        for claim in report_run.advisory_claims
        if claim.claim_code == "BROADBAND_NO_ACCESS_001"
    ]
    assert no_access_claims, "BROADBAND_NO_ACCESS_001 missing from advisory claims"

    broadband_evidence_ids = {rec.evidence_id for rec in broadband_evidence}
    assert any(
        eid in broadband_evidence_ids for eid in no_access_claims[0].evidence_ids
    ), "BROADBAND_NO_ACCESS_001 must cite the ingested broadband evidence"

    dossier = build_rural_land_dossier(report_run)
    section_12 = _section(dossier, "## 12. Internet", "## 13.")
    assert "no providers reported" in section_12
    assert "not evaluated" not in section_12.split("Broadband availability:")[1][:80]
    _assert_no_overclaim(dossier)


def test_buncombe_broadband_source_unavailable_end_to_end() -> None:
    """A source failure becomes BROADBAND_SOURCE_UNAVAILABLE, not a no-provider claim."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()
    _register_fixture_source(source_service)
    _create_area(area_service, "buncombe-broadband-unavailable")
    _ingest_broadband_fixture(
        evidence_service,
        retrieval_port,
        "nc_buncombe_bun_broadband_unavailable.json",
    )

    report_run = _run_report(
        source_service, area_service, evidence_service, claim_service
    )
    assert report_run.status == JobStatus.SUCCEEDED

    broadband_failures = [
        rec
        for rec in report_run.evidence
        if rec.domain == "broadband" and rec.is_source_failure
    ]
    assert len(broadband_failures) == 1

    unknown_claims = [
        claim
        for claim in report_run.unknowns
        if claim.claim_code == "BROADBAND_SOURCE_UNAVAILABLE"
    ]
    assert unknown_claims, "BROADBAND_SOURCE_UNAVAILABLE missing from unknowns"

    failure_evidence_ids = {rec.evidence_id for rec in broadband_failures}
    assert any(
        eid in failure_evidence_ids for eid in unknown_claims[0].evidence_ids
    ), "BROADBAND_SOURCE_UNAVAILABLE must cite the source-failure evidence"

    claim_codes = {claim.claim_code for claim in report_run.claims} | {
        claim.claim_code for claim in report_run.advisory_claims
    }
    assert "BROADBAND_NO_ACCESS_001" not in claim_codes

    dossier = build_rural_land_dossier(report_run)
    section_12 = _section(dossier, "## 12. Internet", "## 13.")
    assert "source failure" in section_12
    assert "no providers reported" not in section_12
    _assert_no_overclaim(dossier)
