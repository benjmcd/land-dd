"""End-to-end fixture-ingestion regression for the extended `env_hazard` domain."""

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
    StaticEnvHazardFixtureConnector,
    build_fixture_workflow_with_public_services,
    evaluate_env_hazard_fixture_quality,
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
    "No environmental problems exist",
    "No contamination exists",
    "Contamination is confirmed",
    "Environmental liability is established",
    "No Phase I ESA required",
    "This site is clean",
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


def _ingest_env_hazard_fixture(
    evidence_service: EvidenceService,
    retrieval_port: _InMemoryRetrievalPort,
    fixture_file: str,
) -> None:
    workflow = build_fixture_workflow_with_public_services(
        retrieval_provenance_port=retrieval_port,
        evidence_service=evidence_service,
        connector=StaticEnvHazardFixtureConnector(),
        quality_evaluator=evaluate_env_hazard_fixture_quality,
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


def test_buncombe_env_hazard_facilities_end_to_end() -> None:
    """Regulated-facility fixture flows to an ENV_001 claim with caveats."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()
    _register_fixture_source(source_service)
    _create_area(area_service, "buncombe-env-hazard-facilities")
    _ingest_env_hazard_fixture(
        evidence_service,
        retrieval_port,
        "nc_buncombe_bun_env_hazard_facilities.json",
    )

    report_run = _run_report(
        source_service, area_service, evidence_service, claim_service
    )
    assert report_run.status == JobStatus.SUCCEEDED

    env_evidence = [
        rec
        for rec in report_run.evidence
        if rec.domain == "env_hazard" and not rec.is_source_failure
    ]
    assert len(env_evidence) == 1
    assert env_evidence[0].evidence_code == "ENV_HAZ_FACILITY_SCREEN"
    assert env_evidence[0].observed_value["has_env_hazard_proximity"] is True
    assert env_evidence[0].observed_value["regulated_facility_count"] == 2
    assert "does not prove subject-property contamination" in (
        env_evidence[0].caveat or ""
    )
    assert "Phase I/II ESA" in (env_evidence[0].caveat or "")

    env_claims = [
        claim
        for claim in report_run.claims
        if claim.claim_code == "ENV_001"
    ]
    assert env_claims, "ENV_001 missing from claims"
    assert "does not prove subject-property contamination" in (
        env_claims[0].user_safe_language
    )

    env_evidence_ids = {rec.evidence_id for rec in env_evidence}
    assert any(
        eid in env_evidence_ids for eid in env_claims[0].evidence_ids
    ), "ENV_001 must cite the ingested env-hazard evidence"

    dossier = build_rural_land_dossier(report_run)
    section_11 = _section(dossier, "## 11. Environmental", "## 12.")
    assert "2 regulated facility/facilities" in section_11
    assert "Phase I ESA required" in section_11
    assert "not a contamination determination" not in section_11
    _assert_no_overclaim(dossier)


def test_buncombe_env_hazard_source_unavailable_end_to_end() -> None:
    """A source failure becomes an unknown, not a no-hazard conclusion."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()
    _register_fixture_source(source_service)
    _create_area(area_service, "buncombe-env-hazard-unavailable")
    _ingest_env_hazard_fixture(
        evidence_service,
        retrieval_port,
        "nc_buncombe_bun_env_hazard_unavailable.json",
    )

    report_run = _run_report(
        source_service, area_service, evidence_service, claim_service
    )
    assert report_run.status == JobStatus.SUCCEEDED

    env_failures = [
        rec
        for rec in report_run.evidence
        if rec.domain == "env_hazard" and rec.is_source_failure
    ]
    assert len(env_failures) == 1

    unknown_claims = [
        claim
        for claim in report_run.unknowns
        if claim.claim_code == "ENV_SOURCE_UNAVAILABLE_UNKNOWN"
    ]
    assert unknown_claims, "ENV_SOURCE_UNAVAILABLE_UNKNOWN missing from unknowns"

    failure_evidence_ids = {rec.evidence_id for rec in env_failures}
    assert any(
        eid in failure_evidence_ids for eid in unknown_claims[0].evidence_ids
    ), "ENV_SOURCE_UNAVAILABLE_UNKNOWN must cite the source-failure evidence"

    claim_codes = {claim.claim_code for claim in report_run.claims} | {
        claim.claim_code for claim in report_run.advisory_claims
    }
    assert "ENV_001" not in claim_codes

    dossier = build_rural_land_dossier(report_run)
    section_11 = _section(dossier, "## 11. Environmental", "## 12.")
    assert "source failure" in section_11
    assert "ECHO source unavailable" in section_11
    assert "regulated facility/facilities detected" not in section_11
    _assert_no_overclaim(dossier)
