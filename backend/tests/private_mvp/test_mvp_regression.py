from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from app.area_geometry.area_repo import InMemoryAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.claim_repo import InMemoryClaimRepository
from app.claims_engine.not_evaluated import NOT_EVALUATED_CLAIM_CODES
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.connectors import (
    StaticAccessFixtureConnector,
    StaticBuildabilityFixtureConnector,
    StaticFloodFixtureConnector,
    build_fixture_workflow_with_public_services,
    evaluate_access_fixture_quality,
    evaluate_buildability_fixture_quality,
    evaluate_flood_fixture_quality,
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

_SKIP_FIXTURE_SMOKE = pytest.mark.skipif(
    os.getenv("RUN_DB_SMOKE") != "1",
    reason=(
        "Fixture MVP regression not enabled (set RUN_DB_SMOKE=1 to run;"
        " uses InMemory repos, not a Postgres-backed test)"
    ),
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
    # GeoJSON Feature — extract inner geometry for AreaContract
    if data.get("type") == "Feature":
        return data["geometry"]  # type: ignore[no-any-return]
    return data


def _run_mvp_case(
    *,
    geom_file: str,
    connector_fixtures: list[tuple[str, Any, Any]],
) -> None:
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

    geom = _load_geometry(GOLDEN_AOI_DIR / geom_file)
    area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            label=f"mvp-regression-{geom_file}",
            geom_geojson=geom,
            geom_source="golden-aoi-fixture",
        )
    )

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
    assert NOT_EVALUATED_CLAIM_CODES["parcels"] in unknown_codes, (
        f"PARCEL_NOT_EVALUATED missing from unknowns; got {sorted(unknown_codes)}"
    )
    assert NOT_EVALUATED_CLAIM_CODES["assessor"] in unknown_codes, (
        f"ASSESSOR_NOT_EVALUATED missing from unknowns; got {sorted(unknown_codes)}"
    )

    connector_evidence = [rec for rec in report_run.evidence if not rec.is_source_failure]
    assert len(connector_evidence) >= len(connector_fixtures), (
        f"Expected >= {len(connector_fixtures)} connector evidence records; "
        f"got {len(connector_evidence)}"
    )

    evidence_count = report_run.source_manifest.get("evidence_count", 0)
    assert isinstance(evidence_count, int) and evidence_count > len(NOT_EVALUATED_CLAIM_CODES), (
        f"source_manifest evidence_count={evidence_count!r} — expected connector evidence "
        "beyond NOT_EVALUATED domains only"
    )

    dossier = build_rural_land_dossier(report_run)
    dossier_lower = dossier.lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase.lower() not in dossier_lower, (
            f"Forbidden phrase {phrase!r} found in Markdown dossier"
        )

    assert "## 1. Executive Summary" in dossier
    assert "not determined" in dossier_lower or "not evaluated" in dossier_lower


@_SKIP_FIXTURE_SMOKE
def test_buncombe_mvp_regression() -> None:
    _run_mvp_case(
        geom_file="bun_slope.geojson",
        connector_fixtures=[
            (
                "nc_buncombe_bun_slope_flood.json",
                StaticFloodFixtureConnector,
                evaluate_flood_fixture_quality,
            ),
            (
                "nc_buncombe_bun_slope_access.json",
                StaticAccessFixtureConnector,
                evaluate_access_fixture_quality,
            ),
            (
                "nc_buncombe_bun_slope_buildability.json",
                StaticBuildabilityFixtureConnector,
                evaluate_buildability_fixture_quality,
            ),
        ],
    )


@_SKIP_FIXTURE_SMOKE
def test_chatham_mvp_regression() -> None:
    _run_mvp_case(
        geom_file="cha_rural_use.geojson",
        connector_fixtures=[
            (
                "nc_chatham_cha_rural_use_flood.json",
                StaticFloodFixtureConnector,
                evaluate_flood_fixture_quality,
            ),
            (
                "nc_chatham_cha_rural_use_access.json",
                StaticAccessFixtureConnector,
                evaluate_access_fixture_quality,
            ),
        ],
    )


@_SKIP_FIXTURE_SMOKE
def test_brunswick_mvp_regression() -> None:
    _run_mvp_case(
        geom_file="bru_coastal_flood.geojson",
        connector_fixtures=[
            (
                "nc_brunswick_bru_coastal_flood_flood.json",
                StaticFloodFixtureConnector,
                evaluate_flood_fixture_quality,
            ),
        ],
    )
