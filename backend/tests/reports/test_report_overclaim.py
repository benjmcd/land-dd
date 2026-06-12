from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from app.area_geometry.area_repo import InMemoryAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.claim_repo import InMemoryClaimRepository
from app.claims_engine.not_evaluated import NOT_EVALUATED_SOURCE_NAME
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.domain.area_contracts import AreaContract
from app.domain.enums import ConfidenceBand, EvidenceType, IntentCode, JobStatus
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService
from app.reports.dossier import build_rural_land_dossier
from app.reports.service import (
    ConnectorReviewQueueItemProtocol,
    ConnectorReviewQueueProtocol,
    ReportRunService,
)
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"

FORBIDDEN_PHRASES = (
    "You can build here",
    "This parcel has legal access",
    "This property has water rights",
    "This is a good investment",
    "This land is safe",
    "This property is worth",
)


@dataclass(frozen=True)
class FakeQueueItem:
    status: JobStatus
    payload: dict[str, object]


class FakeReviewQueue:
    def __init__(self, items: dict[UUID, FakeQueueItem] | None = None) -> None:
        self._items = items or {}

    def get_by_ingest_run_id(
        self, ingest_run_id: UUID
    ) -> ConnectorReviewQueueItemProtocol | None:
        return self._items.get(ingest_run_id)


def _load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def _make_service(
    queue: ConnectorReviewQueueProtocol | None = None,
) -> tuple[SourceService, AreaService, EvidenceService, ReportRunService]:
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
        connector_review_queue=queue,
    )
    return source_service, area_service, evidence_service, report_service


def _register_area(area_service: AreaService) -> AreaContract:
    return area_service.create(
        AreaContract(
            label="overclaim-test",
            geom_geojson=_load_geometry("valid_polygon.geojson"),
            geom_source="test",
        )
    )


def _register_source(source_service: SourceService, domain: str = "flood") -> SourceContract:
    return source_service.register(
        SourceContract(
            name=f"Fixture {domain.upper()} Source",
            organization="fixture",
            domain=domain,
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


def _assert_no_forbidden_phrases(dossier: str) -> None:
    lower = dossier.lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase.lower() not in lower, (
            f"Forbidden certainty phrase found in dossier: {phrase!r}"
        )


def _assert_dossier_structure(dossier: str) -> None:
    assert "## 1. Executive Summary" in dossier
    assert "## 18. Source Appendix" in dossier
    # screening disclaimer always present
    assert "Screening output only" in dossier
    # not-determined language always appears in at least one section
    assert "not determined" in dossier.lower() or "not evaluated" in dossier.lower()


def _assert_source_citation(dossier: str) -> None:
    # Source Appendix must be non-empty (at minimum the NOT_EVALUATED source appears)
    appendix_start = dossier.find("## 18. Source Appendix")
    assert appendix_start >= 0
    appendix_text = dossier[appendix_start:]
    assert NOT_EVALUATED_SOURCE_NAME in appendix_text or "screening input" in appendix_text, (
        "Expected at least one source citation in Source Appendix"
    )


def test_dossier_with_no_connector_evidence_has_no_forbidden_phrases() -> None:
    _, area_service, _, report_service = _make_service()
    area = _register_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    assert report_run.status == JobStatus.SUCCEEDED

    dossier = build_rural_land_dossier(report_run)
    _assert_no_forbidden_phrases(dossier)
    _assert_dossier_structure(dossier)
    _assert_source_citation(dossier)


def test_dossier_with_flood_red_flag_has_no_overclaim() -> None:
    ingest_run_id = uuid4()
    queue = FakeReviewQueue(
        {
            ingest_run_id: FakeQueueItem(
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
    source_service, area_service, evidence_service, report_service = _make_service(queue=queue)
    source = _register_source(source_service)
    area = _register_area(area_service)

    evidence_service.create_observation(
        EvidenceContract(
            area_id=area.area_id,
            source_id=source.source_id,
            evidence_type=EvidenceType.SPATIAL_INTERSECTION,
            evidence_code="FLOOD_ZONE_SCREEN",
            domain="flood",
            method_code="fixture_flood_overlay",
            observation="Fixture: AE zone intersection.",
            observed_value={"flood_zone": "AE"},
            confidence=ConfidenceBand.MEDIUM,
            caveat="FEMA NFHL screening only; confirm locally.",
            source_ingest_run_id=ingest_run_id,
        )
    )

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    assert report_run.status == JobStatus.SUCCEEDED
    assert report_run.red_flags, "Expected FLOOD_001 red flag"

    dossier = build_rural_land_dossier(report_run)
    _assert_no_forbidden_phrases(dossier)
    _assert_dossier_structure(dossier)
    _assert_source_citation(dossier)

    # Flood finding surfaces without overstating certainty
    dossier_lower = dossier.lower()
    assert "flood" in dossier_lower
    assert "confirm" in dossier_lower or "verify" in dossier_lower


def test_dossier_not_evaluated_unknowns_show_as_not_determined() -> None:
    _, area_service, _, report_service = _make_service()
    area = _register_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    assert report_run.unknowns, "Expected NOT_EVALUATED unknowns"

    dossier = build_rural_land_dossier(report_run)
    dossier_lower = dossier.lower()
    # The dossier consistently phrases missing data as "not determined" / "not evaluated"
    assert "not determined" in dossier_lower or "not evaluated" in dossier_lower
    # Must not substitute a definitive conclusion for an unknown
    _assert_no_forbidden_phrases(dossier)


def test_dossier_always_includes_screening_disclaimer() -> None:
    _, area_service, _, report_service = _make_service()
    area = _register_area(area_service)

    report_run = report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    dossier = build_rural_land_dossier(report_run)
    assert "Screening output only" in dossier
    assert "not legal" in dossier.lower()
    assert "investment advice" in dossier.lower()
