from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from app.area_geometry.area_repo import InMemoryAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.claim_repo import InMemoryClaimRepository
from app.claims_engine.not_evaluated import NOT_EVALUATED_CLAIM_CODES
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.connectors import (
    StaticFloodFixtureConnector,
    StaticParcelFixtureConnector,
    StaticSoilsFixtureConnector,
    StaticWetlandsFixtureConnector,
    build_fixture_workflow_with_public_services,
    evaluate_flood_fixture_quality,
    evaluate_parcel_fixture_quality,
    evaluate_soils_fixture_quality,
    evaluate_wetlands_fixture_quality,
)
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode, JobStatus
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
    import json
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    if data.get("type") == "Feature":
        return data["geometry"]  # type: ignore[no-any-return]
    return data


def test_chatham_parcel_utility() -> None:
    """Chatham parcel utility: parcel evidence present; assessor still NOT_EVALUATED."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()

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

    geom = _load_geometry(GOLDEN_AOI_DIR / "cha_parcel_tax.geojson")
    area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            label="chatham-parcel-utility",
            geom_geojson=geom,
            geom_source="golden-aoi-fixture",
        )
    )

    connector_fixtures: list[tuple[str, Any, Any]] = [
        (
            "nc_chatham_cha_parcel_tax_flood.json",
            StaticFloodFixtureConnector,
            evaluate_flood_fixture_quality,
        ),
        (
            "nc_chatham_cha_parcel_tax_parcels.json",
            StaticParcelFixtureConnector,
            evaluate_parcel_fixture_quality,
        ),
    ]
    for fixture_file, connector_cls, quality_eval in connector_fixtures:
        workflow = build_fixture_workflow_with_public_services(
            retrieval_provenance_port=retrieval_port,
            evidence_service=evidence_service,
            connector=connector_cls(),
            quality_evaluator=quality_eval,
        )
        workflow.ingest_fixture(CONNECTOR_DIR / fixture_file)

    report_service = ReportRunService(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        claim_service=claim_service,
        rule_engine=RuleEngine.from_file(),
    )
    report_run = report_service.create_report_run(
        area_id=_FIXTURE_AREA_ID,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    assert report_run.status == JobStatus.SUCCEEDED

    unknown_codes = {claim.claim_code for claim in report_run.unknowns}
    assert NOT_EVALUATED_CLAIM_CODES["assessor"] in unknown_codes, (
        f"ASSESSOR_NOT_EVALUATED missing; got {sorted(unknown_codes)}"
    )

    parcel_evidence = [
        rec for rec in report_run.evidence
        if rec.domain == "parcels" and not rec.is_source_failure
    ]
    assert len(parcel_evidence) >= 1, "Expected at least one parcel evidence record"

    dossier = build_rural_land_dossier(report_run)
    dossier_lower = dossier.lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase.lower() not in dossier_lower, (
            f"Forbidden phrase {phrase!r} found in Markdown dossier"
        )
    assert "## 1. Executive Summary" in dossier


def test_brunswick_wetlands_soils_utility() -> None:
    """Brunswick wetlands+soils utility: wetlands and soils evidence present."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()

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

    geom = _load_geometry(GOLDEN_AOI_DIR / "bru_wetlands_soils.geojson")
    area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            label="brunswick-wetlands-soils-utility",
            geom_geojson=geom,
            geom_source="golden-aoi-fixture",
        )
    )

    connector_fixtures: list[tuple[str, Any, Any]] = [
        (
            "nc_brunswick_bru_wetlands_soils_flood.json",
            StaticFloodFixtureConnector,
            evaluate_flood_fixture_quality,
        ),
        (
            "nc_brunswick_bru_wetlands_soils_wetlands.json",
            StaticWetlandsFixtureConnector,
            evaluate_wetlands_fixture_quality,
        ),
        (
            "nc_brunswick_bru_wetlands_soils_soils.json",
            StaticSoilsFixtureConnector,
            evaluate_soils_fixture_quality,
        ),
    ]
    for fixture_file, connector_cls, quality_eval in connector_fixtures:
        workflow = build_fixture_workflow_with_public_services(
            retrieval_provenance_port=retrieval_port,
            evidence_service=evidence_service,
            connector=connector_cls(),
            quality_evaluator=quality_eval,
        )
        workflow.ingest_fixture(CONNECTOR_DIR / fixture_file)

    report_service = ReportRunService(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        claim_service=claim_service,
        rule_engine=RuleEngine.from_file(),
    )
    report_run = report_service.create_report_run(
        area_id=_FIXTURE_AREA_ID,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )

    assert report_run.status == JobStatus.SUCCEEDED

    unknown_codes = {claim.claim_code for claim in report_run.unknowns}
    assert NOT_EVALUATED_CLAIM_CODES["parcels"] in unknown_codes
    assert NOT_EVALUATED_CLAIM_CODES["assessor"] in unknown_codes

    wetlands_evidence = [
        rec for rec in report_run.evidence
        if rec.domain == "wetlands" and not rec.is_source_failure
    ]
    soils_evidence = [
        rec for rec in report_run.evidence
        if rec.domain == "soils" and not rec.is_source_failure
    ]
    assert len(wetlands_evidence) >= 1, "Expected at least one wetlands evidence record"
    assert len(soils_evidence) >= 1, "Expected at least one soils evidence record"

    dossier = build_rural_land_dossier(report_run)
    dossier_lower = dossier.lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase.lower() not in dossier_lower, (
            f"Forbidden phrase {phrase!r} found in Markdown dossier"
        )
    assert "## 1. Executive Summary" in dossier
    assert "not determined" in dossier_lower or "not evaluated" in dossier_lower
