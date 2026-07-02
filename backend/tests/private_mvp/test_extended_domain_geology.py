"""End-to-end fixture-ingestion regression for the extended `geology` domain."""

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
    StaticGeologyFixtureConnector,
    build_fixture_workflow_with_public_services,
    evaluate_geology_fixture_quality,
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
_FIXTURE_SOURCE_ID = UUID("88888888-8888-4888-8888-888888888888")

FORBIDDEN_PHRASES = (
    "You can build here",
    "This parcel has legal access",
    "This is a good investment",
    "This land is safe",
    "This property is worth",
    "No geologic hazards exist",
    "Geologic hazards are absent",
    "Buildability is confirmed",
    "Geotechnical suitability is confirmed",
    "Slope stability is confirmed",
    "No landslide risk",
    "No sinkhole risk",
    "Mineral resources are valuable",
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


def _ingest_geology_fixture(
    evidence_service: EvidenceService,
    retrieval_port: _InMemoryRetrievalPort,
    fixture_file: str,
) -> None:
    workflow = build_fixture_workflow_with_public_services(
        retrieval_provenance_port=retrieval_port,
        evidence_service=evidence_service,
        connector=StaticGeologyFixtureConnector(),
        quality_evaluator=evaluate_geology_fixture_quality,
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


def test_buncombe_geology_units_end_to_end() -> None:
    """Map-unit fixture flows to advisory geology-not-evaluated context."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()
    _register_fixture_source(source_service)
    _create_area(area_service, "buncombe-geology-units")
    _ingest_geology_fixture(
        evidence_service,
        retrieval_port,
        "nc_buncombe_bun_geology_units.json",
    )

    report_run = _run_report(
        source_service, area_service, evidence_service, claim_service
    )
    assert report_run.status == JobStatus.SUCCEEDED

    geology_evidence = [
        rec
        for rec in report_run.evidence
        if rec.domain == "geology" and not rec.is_source_failure
    ]
    assert len(geology_evidence) == 1
    assert geology_evidence[0].evidence_code == "NC_GEOLOGIC_MAP_UNIT_CONTEXT"
    assert geology_evidence[0].observed_value["has_geologic_map_context"] is True
    assert geology_evidence[0].observed_value["geologic_unit_count"] == 2
    assert geology_evidence[0].observed_value["geologic_hazard_determined"] is False
    assert geology_evidence[0].observed_value["buildability_determined"] is False
    assert "not parcel-scale geology" in (geology_evidence[0].caveat or "")

    advisory_claims = [
        claim
        for claim in report_run.advisory_claims
        if claim.claim_code == "GEOLOGY_NOT_EVALUATED"
    ]
    assert advisory_claims, "GEOLOGY_NOT_EVALUATED missing from advisory claims"
    assert "geologic hazard evaluation is not supported" in (
        advisory_claims[0].user_safe_language
    )

    geology_evidence_ids = {rec.evidence_id for rec in geology_evidence}
    assert any(eid in geology_evidence_ids for eid in advisory_claims[0].evidence_ids), (
        "GEOLOGY_NOT_EVALUATED must cite the ingested geology evidence"
    )

    dossier = build_rural_land_dossier(report_run)
    section_14 = _section(dossier, "## 14. Resource / Geologic Context", "## 15.")
    assert "primary unit: Zwe" in section_14
    assert "formation: Wilhite Formation" in section_14
    assert "type(s): metamorphic, metasedimentary" in section_14
    assert "belt(s): Blue Ridge belt, Inner Piedmont belt" in section_14
    assert "Mineral rights status: not determined" in section_14
    _assert_no_overclaim(dossier)


def test_buncombe_geology_no_units_end_to_end() -> None:
    """No-unit fixture remains context-only and still avoids hazard conclusions."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()
    _register_fixture_source(source_service)
    _create_area(area_service, "buncombe-geology-no-units")
    _ingest_geology_fixture(
        evidence_service,
        retrieval_port,
        "nc_buncombe_bun_geology_no_units.json",
    )

    report_run = _run_report(
        source_service, area_service, evidence_service, claim_service
    )
    assert report_run.status == JobStatus.SUCCEEDED

    geology_evidence = [
        rec
        for rec in report_run.evidence
        if rec.domain == "geology" and not rec.is_source_failure
    ]
    assert len(geology_evidence) == 1
    assert geology_evidence[0].observed_value["no_geologic_map_context"] is True
    assert geology_evidence[0].observed_value["geologic_unit_count"] == 0
    assert geology_evidence[0].observed_value["geologic_hazard_determined"] is False
    assert geology_evidence[0].observed_value["buildability_determined"] is False

    advisory_claims = [
        claim
        for claim in report_run.advisory_claims
        if claim.claim_code == "GEOLOGY_NOT_EVALUATED"
    ]
    assert advisory_claims, "GEOLOGY_NOT_EVALUATED missing from advisory claims"

    dossier = build_rural_land_dossier(report_run)
    section_14 = _section(dossier, "## 14. Resource / Geologic Context", "## 15.")
    assert "returned no map units" in section_14
    assert "no geologic hazards" not in section_14.lower()
    _assert_no_overclaim(dossier)


def test_buncombe_geology_source_unavailable_end_to_end() -> None:
    """A source failure renders unavailable context, not a no-hazard conclusion."""
    source_service, area_service, evidence_service, claim_service = _make_services()
    retrieval_port = _InMemoryRetrievalPort()
    _register_fixture_source(source_service)
    _create_area(area_service, "buncombe-geology-unavailable")
    _ingest_geology_fixture(
        evidence_service,
        retrieval_port,
        "nc_buncombe_bun_geology_unavailable.json",
    )

    report_run = _run_report(
        source_service, area_service, evidence_service, claim_service
    )
    assert report_run.status == JobStatus.SUCCEEDED

    geology_failures = [
        rec
        for rec in report_run.evidence
        if rec.domain == "geology" and rec.is_source_failure
    ]
    assert len(geology_failures) == 1
    assert geology_failures[0].evidence_code == "NC_GEOLOGIC_MAP_SOURCE_FAILURE"

    advisory_codes = {claim.claim_code for claim in report_run.advisory_claims}
    assert "GEOLOGY_NOT_EVALUATED" not in advisory_codes

    dossier = build_rural_land_dossier(report_run)
    section_14 = _section(dossier, "## 14. Resource / Geologic Context", "## 15.")
    assert "source failure" in section_14
    assert "NCGS geologic map data unavailable" in section_14
    assert "primary unit" not in section_14
    assert "no geologic hazards" not in section_14.lower()
    _assert_no_overclaim(dossier)
