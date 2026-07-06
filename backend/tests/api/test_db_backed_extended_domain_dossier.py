from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import create_db_api_services
from app.area_geometry.area_repo import SqlAlchemyAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.not_evaluated import (
    NOT_EVALUATED_SOURCE_NAME,
    NOT_EVALUATED_SOURCE_ORG,
)
from app.connectors import (
    StaticMineralsFixtureConnector,
    build_fixture_workflow_with_public_lane_services,
    evaluate_minerals_fixture_quality,
)
from app.connectors.fixture_resources import (
    fixture_dataset_contract,
    fixture_dataset_version_contract,
)
from app.core.config import Settings
from app.db.engine import build_engine
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode
from app.domain.source_contracts import SourceContract
from app.reports.dossier import build_rural_land_dossier
from app.source_registry.service import SourceService
from app.source_registry.source_repo import SqlAlchemySourceRepository

GOLDEN_AOI_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "golden_aois"
CONNECTOR_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"

_FIXTURE_AREA_ID = UUID("44444444-4444-4444-8444-444444444444")
_FIXTURE_SOURCE_ID = UUID("55555555-5555-4555-8555-555555555555")
_FIXTURE_DATASET_ID = UUID("11111111-2222-4333-8444-555555555555")
_FIXTURE_DATASET_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")
_FIXTURE_INGEST_RUN_ID = UUID("c1c1c1c1-c1c1-4c1c-8c1c-c1c1c1c1c1c1")
_FIXTURE_EVIDENCE_ID = UUID("c1c2c3c4-c1c2-4c3c-8c4c-c1c2c3c4c5c6")


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_backed_minerals_fixture_flows_to_claim_evidence_and_dossier(
    tmp_path: Path,
) -> None:
    engine = build_engine()
    settings = Settings(OBJECT_STORE_ROOT=str(tmp_path / "object-store"))
    sentinel_preexisting = _sentinel_source_exists()
    report_run_id: UUID | None = None

    try:
        with Session(engine) as session:
            _cleanup_db_spine_fixture(
                session,
                report_run_id=None,
                delete_sentinel_source=False,
            )
            services = create_db_api_services(
                session,
                object_store_root=settings.object_store_root,
                settings=settings,
            )
            _seed_area_source_and_fixture_provenance(session)

            workflow = build_fixture_workflow_with_public_lane_services(
                source_provenance_service=services.source_provenance_service,
                evidence_service=services.evidence_service,
                connector=StaticMineralsFixtureConnector(),
                quality_evaluator=evaluate_minerals_fixture_quality,
            )
            ingest_result = workflow.ingest_fixture(
                CONNECTOR_DIR / "nc_buncombe_bun_minerals_active.json"
            )
            created_evidence_ids = {
                record.evidence_id
                for record in ingest_result.evidence_ingestion.created_evidence
            }
            assert created_evidence_ids == {_FIXTURE_EVIDENCE_ID}

            report_run = services.report_service.create_report_run(
                area_id=_FIXTURE_AREA_ID,
                intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
            )
            report_run_id = report_run.report_run_id
            session.commit()

        with Session(engine) as session:
            claim_rows = session.execute(
                text(
                    """
                    SELECT claims.claim_code
                    FROM claims.claim_evidence AS link
                    JOIN claims.claims AS claims
                        ON claims.claim_id = link.claim_id
                    WHERE link.evidence_id = :evidence_id
                        AND claims.area_id = :area_id
                    ORDER BY claims.claim_code
                    """
                ),
                {"evidence_id": _FIXTURE_EVIDENCE_ID, "area_id": _FIXTURE_AREA_ID},
            ).fetchall()
            assert [row[0] for row in claim_rows] == ["MINERALS_ACTIVE_CLAIMS_001"]

            evidence_row = session.execute(
                text(
                    """
                    SELECT domain, metadata->>'evidence_code', is_source_failure
                    FROM evidence.observations
                    WHERE evidence_id = :evidence_id
                    """
                ),
                {"evidence_id": _FIXTURE_EVIDENCE_ID},
            ).one()
            assert tuple(evidence_row) == (
                "minerals",
                "BLM_MLRS_ACTIVE_MINING_CLAIM_CONTEXT",
                False,
            )

            services = create_db_api_services(
                session,
                object_store_root=settings.object_store_root,
                settings=settings,
            )
            persisted_report = services.report_service.get_report_run(report_run_id)
            assert persisted_report is not None
            assert persisted_report.artifact_metadata["persistence"] == "postgres+object_store"

            minerals_evidence_ids = {
                record.evidence_id
                for record in persisted_report.evidence
                if record.domain == "minerals" and not record.is_source_failure
            }
            assert _FIXTURE_EVIDENCE_ID in minerals_evidence_ids
            assert any(
                claim.claim_code == "MINERALS_ACTIVE_CLAIMS_001"
                and _FIXTURE_EVIDENCE_ID in claim.evidence_ids
                for claim in persisted_report.claims
            )

            dossier = build_rural_land_dossier(persisted_report)
            resource_section = dossier.split("## 14. Resource / Geologic Context", 1)[1]
            resource_section = resource_section.split("## 15. Market Context", 1)[0]
            resource_caveat_line = next(
                line
                for line in resource_section.splitlines()
                if line.startswith("- Caveats:")
            )
            assert "2 active federal mining claim record" in resource_section.lower()
            assert resource_caveat_line != "- Caveats: none recorded"
    finally:
        with Session(engine) as session:
            _cleanup_db_spine_fixture(
                session,
                report_run_id=report_run_id,
                delete_sentinel_source=not sentinel_preexisting,
            )


def _load_geometry(path: Path) -> dict[str, object]:
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    if data.get("type") == "Feature":
        geometry = data["geometry"]
        assert isinstance(geometry, dict)
        return cast(dict[str, object], geometry)
    return cast(dict[str, object], data)


def _seed_area_source_and_fixture_provenance(session: Session) -> None:
    source_service = SourceService(SqlAlchemySourceRepository(session))
    area_service = AreaService(SqlAlchemyAreaRepository(session))
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
    area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            label="db-backed minerals fixture polygon",
            geom_geojson=_load_geometry(GOLDEN_AOI_DIR / "bun_slope.geojson"),
            geom_source="golden-aoi-fixture",
        )
    )
    services = create_db_api_services(
        session,
        object_store_root=str(Path("unused-object-store")),
        settings=Settings(OBJECT_STORE_ROOT=str(Path("unused-object-store"))),
    )
    services.source_provenance_service.ensure_dataset(fixture_dataset_contract())
    services.source_provenance_service.ensure_dataset_version(fixture_dataset_version_contract())
    session.flush()


def _sentinel_source_exists() -> bool:
    engine = build_engine()
    with Session(engine) as session:
        return (
            session.execute(
                text(
                    """
                    SELECT 1
                    FROM source.sources
                    WHERE name = :name
                        AND organization = :organization
                    LIMIT 1
                    """
                ),
                {
                    "name": NOT_EVALUATED_SOURCE_NAME,
                    "organization": NOT_EVALUATED_SOURCE_ORG,
                },
            ).first()
            is not None
        )


def _cleanup_db_spine_fixture(
    session: Session,
    *,
    report_run_id: UUID | None,
    delete_sentinel_source: bool,
) -> None:
    if report_run_id is not None:
        session.execute(
            text("DELETE FROM jobs.job_queue WHERE job_id = :report_run_id"),
            {"report_run_id": report_run_id},
        )
        session.execute(
            text("DELETE FROM reports.report_runs WHERE report_run_id = :report_run_id"),
            {"report_run_id": report_run_id},
        )
    session.execute(
        text("DELETE FROM claims.verification_tasks WHERE area_id = :area_id"),
        {"area_id": _FIXTURE_AREA_ID},
    )
    session.execute(
        text("DELETE FROM claims.claims WHERE area_id = :area_id"),
        {"area_id": _FIXTURE_AREA_ID},
    )
    session.execute(
        text(
            """
            DELETE FROM audit.events
            WHERE target_id IN (
                SELECT evidence_id
                FROM evidence.observations
                WHERE area_id = :area_id
            )
            """
        ),
        {"area_id": _FIXTURE_AREA_ID},
    )
    session.execute(
        text("DELETE FROM evidence.observations WHERE area_id = :area_id"),
        {"area_id": _FIXTURE_AREA_ID},
    )
    session.execute(
        text("DELETE FROM source.ingest_runs WHERE ingest_run_id = :ingest_run_id"),
        {"ingest_run_id": _FIXTURE_INGEST_RUN_ID},
    )
    session.execute(
        text("DELETE FROM source.dataset_versions WHERE dataset_version_id = :id"),
        {"id": _FIXTURE_DATASET_VERSION_ID},
    )
    session.execute(
        text("DELETE FROM source.datasets WHERE dataset_id = :id"),
        {"id": _FIXTURE_DATASET_ID},
    )
    session.execute(
        text("DELETE FROM source.sources WHERE source_id = :source_id"),
        {"source_id": _FIXTURE_SOURCE_ID},
    )
    session.execute(
        text("DELETE FROM core.areas WHERE area_id = :area_id"),
        {"area_id": _FIXTURE_AREA_ID},
    )
    if delete_sentinel_source:
        session.execute(
            text(
                """
                DELETE FROM source.sources
                WHERE name = :name
                    AND organization = :organization
                """
            ),
            {
                "name": NOT_EVALUATED_SOURCE_NAME,
                "organization": NOT_EVALUATED_SOURCE_ORG,
            },
        )
    session.commit()
