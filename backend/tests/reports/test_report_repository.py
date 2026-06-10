from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.area_geometry.area_repo import InMemoryAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.claim_repo import InMemoryClaimRepository
from app.claims_engine.not_evaluated import (
    NOT_EVALUATED_CLAIM_CODES,
    NOT_EVALUATED_DOMAINS,
    NOT_EVALUATED_SOURCE_NAME,
)
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.db.engine import build_engine
from app.domain.area_contracts import AreaContract
from app.domain.enums import ConfidenceBand, EvidenceType, IntentCode
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService
from app.reports.report_repo import SqlAlchemyReportRunRepository
from app.reports.service import ReportRunService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


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


def register_area(area_service: AreaService, area_id: UUID) -> AreaContract:
    return area_service.create(
        AreaContract(
            area_id=area_id,
            label="fixture polygon",
            geom_geojson=load_geometry("valid_polygon.geojson"),
            geom_source="report repository fixture",
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


def _seed_area_row(session: Session, area: AreaContract) -> None:
    session.execute(
        text(
            """
            INSERT INTO core.areas (
                area_id,
                area_type,
                label,
                geom,
                geom_validated,
                geom_source,
                metadata
            )
            VALUES (
                :area_id,
                'polygon',
                :label,
                ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geom_geojson), 4326)),
                :geom_validated,
                :geom_source,
                '{}'::jsonb
            )
            """
        ),
        {
            "area_id": area.area_id,
            "label": area.label,
            "geom_geojson": json.dumps(area.geom_geojson),
            "geom_validated": area.geom_validated,
            "geom_source": area.geom_source,
        },
    )


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_report_run_repository_persists_and_round_trips(
    tmp_path: Path,
) -> None:
    engine = build_engine()
    area_id = uuid4()
    source_service = SourceService(InMemorySourceRepository())
    area_service = AreaService(InMemoryAreaRepository())
    evidence_repo = InMemoryEvidenceRepository()
    evidence_service = EvidenceService(evidence_repo, source_service, area_service)
    claim_service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    report_store = tmp_path / "object-store"

    source = register_source(source_service)
    area = register_area(area_service, area_id)
    evidence_service.create_observation(flood_evidence(area, source))
    evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        method_code="fixture_fema_request",
        caveat="Fixture source request returned 503.",
        domain="flood",
    )

    with Session(engine) as session:
        _seed_area_row(session, area)
        repo = SqlAlchemyReportRunRepository(session, report_store)
        report_service = ReportRunService(
            source_service=source_service,
            area_service=area_service,
            evidence_service=evidence_service,
            claim_service=claim_service,
            rule_engine=RuleEngine.from_file(),
            report_repo=repo,
        )

        report_run = report_service.create_report_run(
            area_id=area.area_id,
            intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        )
        session.commit()

    report_uri = report_run.output_uri
    assert report_uri is not None
    assert Path(report_uri).exists()
    assert report_run.artifact_metadata["persistence"] == "postgres+object_store"
    assert report_run.artifact_metadata["artifact_kind"] == "report_run"
    cost_metrics = cast(dict[str, Any], report_run.artifact_metadata["cost_metrics"])
    n_domains = len(NOT_EVALUATED_DOMAINS)
    # 2 flood evidence records (observation + source failure), one per NOT_EVALUATED
    # domain, plus the injected zoning source-unavailable sentinel (no zoning evidence).
    assert cost_metrics["evidence_count"] == n_domains + 3
    assert cost_metrics["estimated_total_usd_cents"] == 0
    assert cost_metrics["paid_data_usd_cents"] == 0
    assert cost_metrics["human_review_minutes"] == 0
    assert report_run.source_manifest["source_names"] == [
        "Fixture FEMA Flood Map",
        NOT_EVALUATED_SOURCE_NAME,
    ]
    assert [record.domain for record in report_run.evidence[2:]] == [
        *NOT_EVALUATED_DOMAINS,
        "zoning",
    ]
    assert [claim.claim_code for claim in report_run.unknowns][-(n_domains + 1) :] == [
        *(NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS),
        "ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
    ]

    # Verify intent_id is populated in the DB row (not NULL), confirming the
    # intent_code → intent_id lookup in SqlAlchemyReportRunRepository works.
    with Session(engine) as session:
        row = session.execute(
            text(
                "SELECT intent_id FROM reports.report_runs " "WHERE report_run_id = :report_run_id"
            ),
            {"report_run_id": report_run.report_run_id},
        ).one_or_none()
    assert row is not None, "report run row not found in DB"
    db_intent_id = row[0]
    assert db_intent_id is not None, (
        "intent_id is NULL in reports.report_runs — "
        "_resolve_intent_id did not find 'homestead_feasibility' in core.intents"
    )

    with Session(engine) as session:
        repo = SqlAlchemyReportRunRepository(session, report_store)
        retrieved = repo.get(report_run.report_run_id)

    assert retrieved == report_run

    with Session(engine) as session:
        session.execute(
            text("DELETE FROM reports.report_runs WHERE report_run_id = :report_run_id"),
            {"report_run_id": report_run.report_run_id},
        )
        session.execute(
            text("DELETE FROM core.areas WHERE area_id = :area_id"),
            {"area_id": area.area_id},
        )
        session.commit()
