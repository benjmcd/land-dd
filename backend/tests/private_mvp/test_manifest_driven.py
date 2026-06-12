from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
import yaml

from app.area_geometry.area_repo import InMemoryAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.claim_repo import InMemoryClaimRepository
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.connectors import (
    StaticAccessFixtureConnector,
    StaticBuildabilityFixtureConnector,
    StaticFloodFixtureConnector,
    StaticParcelFixtureConnector,
    StaticSoilsFixtureConnector,
    StaticTerrainFixtureConnector,
    StaticWetlandsFixtureConnector,
    StaticZoningFixtureConnector,
    build_fixture_workflow_with_public_services,
    evaluate_access_fixture_quality,
    evaluate_buildability_fixture_quality,
    evaluate_flood_fixture_quality,
    evaluate_parcel_fixture_quality,
    evaluate_soils_fixture_quality,
    evaluate_terrain_fixture_quality,
    evaluate_wetlands_fixture_quality,
    evaluate_zoning_fixture_quality,
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

ROOT = Path(__file__).resolve().parents[3]
GOLDEN_AOI_DIR = ROOT / "tests" / "fixtures" / "golden_aois"
CONNECTOR_DIR = ROOT / "tests" / "fixtures" / "connectors"
MANIFEST_PATH = GOLDEN_AOI_DIR / "manifest.yaml"

_FIXTURE_AREA_ID = UUID("44444444-4444-4444-8444-444444444444")
_FIXTURE_SOURCE_ID = UUID("55555555-5555-4555-8555-555555555555")

_DOMAIN_CONNECTOR_MAP: dict[str, tuple[type[Any], Any]] = {
    "flood": (StaticFloodFixtureConnector, evaluate_flood_fixture_quality),
    "access": (StaticAccessFixtureConnector, evaluate_access_fixture_quality),
    "buildability": (StaticBuildabilityFixtureConnector, evaluate_buildability_fixture_quality),
    "terrain": (StaticTerrainFixtureConnector, evaluate_terrain_fixture_quality),
    "parcels": (StaticParcelFixtureConnector, evaluate_parcel_fixture_quality),
    "soils": (StaticSoilsFixtureConnector, evaluate_soils_fixture_quality),
    "wetlands": (StaticWetlandsFixtureConnector, evaluate_wetlands_fixture_quality),
    "zoning": (StaticZoningFixtureConnector, evaluate_zoning_fixture_quality),
}


class _InMemoryRetrievalPort:
    def __init__(self) -> None:
        self._store: dict[UUID, SourceRetrievalRunContract] = {}

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        return ingest_run_id in self._store

    def record_retrieval_run(
        self, retrieval_run: SourceRetrievalRunContract
    ) -> SourceRetrievalRunContract:
        self._store[retrieval_run.ingest_run_id] = retrieval_run
        return retrieval_run


def _load_manifest_cases() -> list[dict[str, Any]]:
    data: Any = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    return data["cases"]  # type: ignore[no-any-return]


def _run_case(case: dict[str, Any]) -> str:
    source_service = SourceService(InMemorySourceRepository())
    area_service = AreaService(InMemoryAreaRepository())
    evidence_repo = InMemoryEvidenceRepository()
    evidence_service = EvidenceService(evidence_repo, source_service, area_service)
    claim_service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    retrieval_port = _InMemoryRetrievalPort()

    source_service.register(
        SourceContract(
            source_id=_FIXTURE_SOURCE_ID,
            name="Manifest Fixture Source",
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

    raw: Any = json.loads((GOLDEN_AOI_DIR / case["geometry_file"]).read_text(encoding="utf-8"))
    geom: dict[str, object] = raw["geometry"] if raw.get("type") == "Feature" else raw
    area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            label=f"manifest-{case['case_id']}",
            geom_geojson=geom,
            geom_source="golden-aoi-fixture",
        )
    )

    for domain, fixture_file in case["connector_fixture_files"].items():
        connector_cls, quality_eval = _DOMAIN_CONNECTOR_MAP[domain]
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
    assert report_run.status == JobStatus.SUCCEEDED, (
        f"Case {case['case_id']!r}: report run failed"
    )
    return build_rural_land_dossier(report_run)


_MANIFEST_CASES = _load_manifest_cases()


@pytest.mark.parametrize("case", _MANIFEST_CASES, ids=lambda c: c["case_id"])
def test_manifest_expected_caveats_surface_in_dossier(case: dict[str, Any]) -> None:
    """Every expected_caveats phrase from the manifest must appear in the dossier."""
    dossier = _run_case(case)
    for phrase in case.get("expected_caveats", []):
        assert phrase in dossier, (
            f"Case {case['case_id']!r}: caveat phrase {phrase!r} not found.\n"
            f"Dossier (first 3000 chars):\n{dossier[:3000]}"
        )


@pytest.mark.parametrize("case", _MANIFEST_CASES, ids=lambda c: c["case_id"])
def test_manifest_forbidden_claims_absent_from_dossier(case: dict[str, Any]) -> None:
    """Every forbidden_claims phrase from the manifest must NOT appear in the dossier."""
    dossier = _run_case(case)
    dossier_lower = dossier.lower()
    for phrase in case.get("forbidden_claims", []):
        assert phrase.lower() not in dossier_lower, (
            f"Case {case['case_id']!r}: forbidden phrase {phrase!r} found in dossier"
        )
