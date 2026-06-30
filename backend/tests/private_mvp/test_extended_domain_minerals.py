"""End-to-end fixture-ingestion regression for the extended `minerals` domain.

The 8 core domains have an end-to-end fixture->claim->dossier proof in
`test_utility_closure.py`. The extended public connectors (minerals/geology/water/
env-hazard/broadband) were only covered in isolation (unit + per-connector API) or
via synthetic evidence on a generic polygon (`test_dossier_enrichment.py`). This test
closes that seam for `minerals` on a real Buncombe AOI, for both the active-claim and
source-failure paths (the latter exercises "source failures are first-class evidence").
"""

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
    StaticMineralsFixtureConnector,
    build_fixture_workflow_with_public_services,
    evaluate_minerals_fixture_quality,
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


def _ingest_minerals_fixture(
    evidence_service: EvidenceService,
    retrieval_port: _InMemoryRetrievalPort,
    fixture_file: str,
) -> None:
    workflow = build_fixture_workflow_with_public_services(
        retrieval_provenance_port=retrieval_port,
        evidence_service=evidence_service,
        connector=StaticMineralsFixtureConnector(),
        quality_evaluator=evaluate_minerals_fixture_quality,
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


def test_buncombe_minerals_active_claims_end_to_end() -> None:
    """Active federal mining-claim fixture flows to a MINERALS_ACTIVE_CLAIMS_001 claim."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()
    _register_fixture_source(source_service)
    _create_area(area_service, "buncombe-minerals-active")
    _ingest_minerals_fixture(
        evidence_service, retrieval_port, "nc_buncombe_bun_minerals_active.json"
    )

    report_run = _run_report(
        source_service, area_service, evidence_service, claim_service
    )
    assert report_run.status == JobStatus.SUCCEEDED

    minerals_evidence = [
        rec
        for rec in report_run.evidence
        if rec.domain == "minerals" and not rec.is_source_failure
    ]
    assert len(minerals_evidence) >= 1, "Expected at least one minerals evidence record"

    active_claims = [
        claim
        for claim in (*report_run.claims, *report_run.advisory_claims)
        if claim.claim_code == "MINERALS_ACTIVE_CLAIMS_001"
    ]
    assert active_claims, "MINERALS_ACTIVE_CLAIMS_001 missing from claims/advisory"

    # The claim must cite the ingested minerals evidence (real evidence->claim linkage).
    minerals_evidence_ids = {rec.evidence_id for rec in minerals_evidence}
    assert any(
        eid in minerals_evidence_ids for eid in active_claims[0].evidence_ids
    ), "MINERALS_ACTIVE_CLAIMS_001 must cite the ingested minerals evidence"

    dossier = build_rural_land_dossier(report_run)
    assert "2 active" in dossier.lower(), (
        "Active mining-claim count from observed_value must surface in the dossier"
    )
    _assert_no_overclaim(dossier)


def test_buncombe_minerals_source_unavailable_end_to_end() -> None:
    """A minerals source failure becomes a first-class MINERALS_SOURCE_UNAVAILABLE unknown."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()
    _register_fixture_source(source_service)
    _create_area(area_service, "buncombe-minerals-unavailable")
    _ingest_minerals_fixture(
        evidence_service, retrieval_port, "nc_buncombe_bun_minerals_unavailable.json"
    )

    report_run = _run_report(
        source_service, area_service, evidence_service, claim_service
    )
    assert report_run.status == JobStatus.SUCCEEDED

    minerals_failures = [
        rec
        for rec in report_run.evidence
        if rec.domain == "minerals" and rec.is_source_failure
    ]
    assert len(minerals_failures) >= 1, "Expected a minerals source-failure evidence record"

    unknown_codes = {claim.claim_code for claim in report_run.unknowns}
    assert "MINERALS_SOURCE_UNAVAILABLE" in unknown_codes, (
        f"MINERALS_SOURCE_UNAVAILABLE missing; got {sorted(unknown_codes)}"
    )

    # Negative: the active-claims finding must NOT appear on the source-failure path.
    claim_codes = {claim.claim_code for claim in report_run.claims} | {
        claim.claim_code for claim in report_run.advisory_claims
    }
    assert "MINERALS_ACTIVE_CLAIMS_001" not in claim_codes

    dossier = build_rural_land_dossier(report_run)
    _assert_no_overclaim(dossier)
    # Failure-specific (not boilerplate): the source-failure caveat must reach the dossier,
    # distinguishing this path from a silent "no issue found".
    assert "recorded as a source failure" in dossier.lower(), (
        "Minerals source failure must surface its caveat in the dossier, not a silent pass"
    )
