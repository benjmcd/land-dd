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
    StaticAccessFixtureConnector,
    StaticFloodFixtureConnector,
    StaticParcelFixtureConnector,
    build_fixture_workflow_with_public_services,
    evaluate_access_fixture_quality,
    evaluate_flood_fixture_quality,
    evaluate_parcel_fixture_quality,
)
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode, JobStatus, ReportReviewStatus
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


def _load_geometry(path: Path) -> dict[str, object]:
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    if data.get("type") == "Feature":
        return data["geometry"]  # type: ignore[no-any-return]
    return data


# Caveat-present / forbidden-claim-absent coverage is owned by test_manifest_driven.py;
# this test asserts ONLY the approval-state + artifact-shape delta.
def test_chatham_approved_path_emits_artifact_with_review_state() -> None:
    source_service = SourceService(InMemorySourceRepository())
    area_service = AreaService(InMemoryAreaRepository())
    evidence_repo = InMemoryEvidenceRepository()
    evidence_service = EvidenceService(evidence_repo, source_service, area_service)
    claim_service = ClaimService(InMemoryClaimRepository(), evidence_repo)
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

    geom = _load_geometry(GOLDEN_AOI_DIR / "cha_rural_use.geojson")
    area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            label="chatham-rural-use-approved-path",
            geom_geojson=geom,
            geom_source="golden-aoi-fixture",
        )
    )

    connector_fixtures: list[tuple[str, Any, Any]] = [
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
        (
            "nc_chatham_cha_rural_use_parcels.json",
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

    approved = report_service.approve_report_run(
        report_run.report_run_id,
        reviewer_id="cli-operator",
        reason="operator proof",
    )
    assert approved is not None
    assert approved.review_status == ReportReviewStatus.APPROVED
    assert approved.reviewed_by == "cli-operator"

    dossier = build_rural_land_dossier(approved)
    assert "Review status: approved" in dossier
    assert "Reviewed by: cli-operator" in dossier

    artifact = json.loads(
        json.dumps(approved.model_dump(mode="json"), indent=2, sort_keys=True)
    )
    assert artifact["report_run_id"] == str(approved.report_run_id)
    assert isinstance(artifact["source_manifest"]["source_ids"], list)
    assert len(artifact["source_manifest"]["source_ids"]) > 0

    all_claims = (
        artifact.get("claims", [])
        + artifact.get("unknowns", [])
        + artifact.get("red_flags", [])
    )
    assert len(all_claims) > 0
    for claim_dict in all_claims:
        assert "evidence_ids" in claim_dict
