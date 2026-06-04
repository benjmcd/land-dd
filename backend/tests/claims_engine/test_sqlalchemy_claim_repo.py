from __future__ import annotations

import json
import os
from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.claims_engine.claim_repo import SqlAlchemyClaimRepository
from app.claims_engine.service import ClaimService
from app.db.engine import build_engine
from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, EvidenceType, SeverityBand
from app.domain.evidence_contracts import EvidenceContract
from app.evidence_ledger.evidence_repo import SqlAlchemyEvidenceRepository

AREA_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [
        [
            [-120.0, 38.0],
            [-119.9, 38.0],
            [-119.9, 38.1],
            [-120.0, 38.1],
            [-120.0, 38.0],
        ]
    ],
}


@pytest.fixture
def session() -> Iterator[Session]:
    if os.getenv("RUN_DB_SMOKE") != "1":
        pytest.skip("DB smoke not enabled")

    engine = build_engine()
    with Session(engine) as db_session:
        try:
            yield db_session
        finally:
            db_session.rollback()


def make_observation(area_id: UUID, source_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="FLOOD_ZONE_SCREEN",
        domain="flood",
        observation="Fixture source intersects a mapped flood zone.",
        observed_value={"flood_zone": "AE"},
        method_code="fixture_flood_overlay",
        confidence=ConfidenceBand.MEDIUM,
        caveat="Screening fixture only; confirm locally.",
    )


def make_source_failure(area_id: UUID, source_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="FLOOD_SOURCE_FAILURE",
        domain="flood",
        observation="Fixture flood source request failed.",
        observed_value={"status_code": 503},
        method_code="fixture_flood_overlay",
        confidence=ConfidenceBand.UNKNOWN,
        caveat="FEMA fixture endpoint returned 503.",
        is_source_failure=True,
    )


def make_claim(area_id: UUID, evidence_id: UUID) -> ClaimContract:
    return ClaimContract(
        area_id=area_id,
        claim_code="FLOOD_CONSTRAINT_PRESENT",
        domain="flood",
        assertion="Mapped data indicates possible flood constraint.",
        user_safe_language=(
            "Mapped screening data indicates a possible flood constraint; confirm locally."
        ),
        severity=SeverityBand.HIGH,
        confidence=ConfidenceBand.MEDIUM,
        evidence_ids=[evidence_id],
        rule_code="FLOOD_G001",
        ruleset_id="homestead_mvp_v0_1",
        ruleset_version="0.1",
        verification_required=True,
        verification_task="Confirm floodplain status with the local administrator.",
    )


def test_sqlalchemy_claim_repository_round_trips_claim_links_and_task(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    evidence_repo = SqlAlchemyEvidenceRepository(session)
    evidence = evidence_repo.add(make_observation(area_id, source_id))
    claim_repo = SqlAlchemyClaimRepository(session)
    service = ClaimService(claim_repo, evidence_repo)
    claim = make_claim(area_id, evidence.evidence_id)

    created = service.create_claim(claim, [evidence.evidence_id])
    session.commit()

    try:
        assert created == claim

        with Session(session.get_bind()) as read_session:
            read_repo = SqlAlchemyClaimRepository(read_session)
            assert read_repo.get(claim.claim_id) == claim
            assert read_repo.exists(claim.claim_id) is True
            assert read_repo.list_by_area(area_id) == [claim]
            assert read_repo.list_all() == [claim]

        stored = session.execute(
            text(
                """
                SELECT metadata
                FROM claims.claims
                WHERE claim_id = :claim_id
                """
            ),
            {"claim_id": claim.claim_id},
        ).mappings().one()
        assert stored["metadata"]["rule_code"] == "FLOOD_G001"
        assert stored["metadata"]["ruleset_id"] == "homestead_mvp_v0_1"
        assert stored["metadata"]["ruleset_version"] == "0.1"
        assert stored["metadata"]["evidence_ids"] == [str(evidence.evidence_id)]

        link_rows = session.execute(
            text(
                """
                SELECT evidence_id, support_role
                FROM claims.claim_evidence
                WHERE claim_id = :claim_id
                """
            ),
            {"claim_id": claim.claim_id},
        ).mappings().all()
        assert [dict(row) for row in link_rows] == [
            {"evidence_id": evidence.evidence_id, "support_role": "supports"}
        ]

        task = session.execute(
            text(
                """
                SELECT task_code, task_text, priority, status
                FROM claims.verification_tasks
                WHERE claim_id = :claim_id
                """
            ),
            {"claim_id": claim.claim_id},
        ).mappings().one()
        assert task["task_code"] == claim.claim_code
        assert task["task_text"] == claim.verification_task
        assert task["priority"] == SeverityBand.HIGH.value
        assert task["status"] == "open"
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_claim_service_persists_unknown_from_source_failure(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    evidence_repo = SqlAlchemyEvidenceRepository(session)
    failure = evidence_repo.add(make_source_failure(area_id, source_id))
    service = ClaimService(SqlAlchemyClaimRepository(session), evidence_repo)

    created = service.create_unknown(
        area_id=area_id,
        claim_code="FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        reason="Flood source data could not be retrieved.",
        evidence_ids=[failure.evidence_id],
        domain="flood",
        rule_code="FLOOD_G001",
        ruleset_id="homestead_mvp_v0_1",
        ruleset_version="0.1",
    )
    session.commit()

    try:
        assert created.severity == SeverityBand.UNKNOWN
        assert created.confidence == ConfidenceBand.UNKNOWN
        assert created.evidence_ids == [failure.evidence_id]

        with Session(session.get_bind()) as read_session:
            retrieved = SqlAlchemyClaimRepository(read_session).get(created.claim_id)

        assert retrieved == created
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_claim_repository_rejects_duplicate_claim_id(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    evidence_repo = SqlAlchemyEvidenceRepository(session)
    evidence = evidence_repo.add(make_observation(area_id, source_id))
    service = ClaimService(SqlAlchemyClaimRepository(session), evidence_repo)
    claim = make_claim(area_id, evidence.evidence_id)

    service.create_claim(claim, [evidence.evidence_id])

    try:
        with pytest.raises(ValueError, match="already stored"):
            service.create_claim(claim, [evidence.evidence_id])
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_claim_repository_rolls_back_add(session: Session) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    evidence_repo = SqlAlchemyEvidenceRepository(session)
    evidence = evidence_repo.add(make_observation(area_id, source_id))
    session.commit()
    claim_repo = SqlAlchemyClaimRepository(session)
    service = ClaimService(claim_repo, evidence_repo)
    claim = make_claim(area_id, evidence.evidence_id)

    try:
        service.create_claim(claim, [evidence.evidence_id])
        session.rollback()

        assert claim_repo.get(claim.claim_id) is None
    finally:
        _delete_area_tree(session, area_id)


def _insert_area(session: Session) -> UUID:
    area_id = uuid4()
    session.execute(
        text(
            """
            INSERT INTO core.areas (
                area_id,
                area_type,
                label,
                geom,
                metadata
            )
            VALUES (
                :area_id,
                'polygon',
                'claim fixture area',
                ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geom_geojson), 4326)),
                '{"domain_area_type": "drawn_polygon"}'::jsonb
            )
            """
        ),
        {"area_id": area_id, "geom_geojson": json.dumps(AREA_GEOMETRY)},
    )
    session.commit()
    return area_id


def _delete_area_tree(session: Session, area_id: UUID) -> None:
    session.rollback()
    session.execute(
        text("DELETE FROM claims.verification_tasks WHERE area_id = :area_id"),
        {"area_id": area_id},
    )
    session.execute(
        text("DELETE FROM claims.claims WHERE area_id = :area_id"),
        {"area_id": area_id},
    )
    session.execute(
        text(
            """
            DELETE FROM audit.events
            WHERE target_table = 'evidence.observations'
                AND target_id IN (
                    SELECT evidence_id
                    FROM evidence.observations
                    WHERE area_id = :area_id
                )
            """
        ),
        {"area_id": area_id},
    )
    session.execute(
        text("DELETE FROM evidence.observations WHERE area_id = :area_id"),
        {"area_id": area_id},
    )
    session.execute(
        text("DELETE FROM core.areas WHERE area_id = :area_id"),
        {"area_id": area_id},
    )
    session.commit()
