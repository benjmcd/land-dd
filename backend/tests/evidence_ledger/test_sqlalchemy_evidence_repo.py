from __future__ import annotations

import json
import os
from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.engine import build_engine
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.evidence_ledger.audit_log import (
    EvidenceAuditEventType,
    SqlAlchemyEvidenceAuditLog,
)
from app.evidence_ledger.evidence_repo import SqlAlchemyEvidenceRepository
from app.evidence_ledger.service import EvidenceService

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


class StubSourceChecker:
    def __init__(self, registered: set[UUID]) -> None:
        self._registered = registered

    def source_is_registered(self, source_id: UUID) -> bool:
        return source_id in self._registered

    def source_production_use_allowed(self, source_id: UUID) -> bool:
        return source_id in self._registered


class StubAreaChecker:
    def __init__(self, registered: set[UUID]) -> None:
        self._registered = registered

    def area_is_registered(
        self,
        area_id: UUID,
        *,
        workspace_id: UUID | None = None,
    ) -> bool:
        return area_id in self._registered


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
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="FLOOD_ZONE_AE",
        domain="flood",
        observation="Fixture source indicates mapped flood zone AE intersection.",
        observed_value={"flood_zone": "AE"},
        method_code="fixture_flood_overlay",
        method_version="0.2.0",
        confidence=ConfidenceBand.MEDIUM,
        caveat="Screening fixture only; confirm locally.",
        source_date="2026-06-04",
    )


def test_sqlalchemy_evidence_repository_round_trips_observation(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    repo = SqlAlchemyEvidenceRepository(session)
    evidence = make_observation(area_id, source_id)

    created = repo.add(evidence)
    session.commit()

    try:
        assert created == evidence

        with Session(session.get_bind()) as read_session:
            read_repo = SqlAlchemyEvidenceRepository(read_session)
            assert read_repo.get(evidence.evidence_id) == evidence
            assert read_repo.exists(evidence.evidence_id) is True
            assert read_repo.list_by_area(area_id) == [evidence]
            assert read_repo.list_by_source(source_id) == [evidence]
            assert read_repo.list_by_type(EvidenceType.SOURCE_OBSERVATION) == [
                evidence
            ]
            assert read_repo.list_all() == [evidence]

        stored = session.execute(
            text(
                """
                SELECT evidence_type, metadata, source_date
                FROM evidence.observations
                WHERE evidence_id = :evidence_id
                """
            ),
            {"evidence_id": evidence.evidence_id},
        ).mappings().one()
        assert stored["evidence_type"] == EvidenceType.SOURCE_OBSERVATION.value
        assert stored["metadata"]["source_id"] == str(source_id)
        assert stored["metadata"]["evidence_code"] == "FLOOD_ZONE_AE"
        assert stored["source_date"].isoformat() == "2026-06-04"
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_evidence_repository_round_trips_geometry_and_precision(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    repo = SqlAlchemyEvidenceRepository(session)
    evidence = make_observation(area_id, source_id).model_copy(
        update={
            "evidence_type": EvidenceType.SPATIAL_INTERSECTION,
            "evidence_code": "FLOOD_INTERSECTION",
            "observed_value": {"intersects": True, "intersection_ratio": 0.2},
            "geometry_geojson": {
                "type": "Point",
                "coordinates": [-119.95, 38.05],
            },
            "spatial_precision_meters": 12.5,
        }
    )

    created = repo.add(evidence)
    session.commit()

    try:
        assert created == evidence

        stored = session.execute(
            text(
                """
                SELECT
                    ST_AsGeoJSON(geometry) AS geometry_geojson,
                    ST_SRID(geometry) AS geometry_srid,
                    metadata
                FROM evidence.observations
                WHERE evidence_id = :evidence_id
                """
            ),
            {"evidence_id": evidence.evidence_id},
        ).mappings().one()
        stored_geometry = json.loads(stored["geometry_geojson"])
        assert stored_geometry == evidence.geometry_geojson
        assert stored["geometry_srid"] == 4326
        assert stored["metadata"]["spatial_precision_meters"] == 12.5

        with Session(session.get_bind()) as read_session:
            retrieved = SqlAlchemyEvidenceRepository(read_session).get(
                evidence.evidence_id
            )

        assert retrieved == evidence
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_evidence_repository_rejects_duplicate_id(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    repo = SqlAlchemyEvidenceRepository(session)
    evidence = make_observation(area_id, source_id)

    repo.add(evidence)

    try:
        with pytest.raises(ValueError, match="already stored"):
            repo.add(evidence)
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_evidence_repository_marks_superseded_without_overwrite(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    repo = SqlAlchemyEvidenceRepository(session)
    original = repo.add(make_observation(area_id, source_id))
    replacement = repo.add(
        make_observation(area_id, source_id).model_copy(
            update={
                "evidence_code": "FLOOD_ZONE_X",
                "observation": "Corrected fixture source indicates zone X.",
                "observed_value": {"flood_zone": "X"},
            }
        )
    )
    session.commit()

    try:
        superseded = repo.mark_superseded(
            original.evidence_id,
            replacement.evidence_id,
        )
        session.commit()

        assert superseded.superseded_by == replacement.evidence_id
        assert repo.get(replacement.evidence_id) == replacement
        assert repo.list_by_area(area_id) == [superseded, replacement]
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_evidence_repository_rolls_back_add(session: Session) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    repo = SqlAlchemyEvidenceRepository(session)
    evidence = make_observation(area_id, source_id)

    try:
        repo.add(evidence)
        session.rollback()

        assert repo.get(evidence.evidence_id) is None
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_evidence_service_persists_audit_events(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    service = EvidenceService(
        SqlAlchemyEvidenceRepository(session),
        StubSourceChecker({source_id}),
        StubAreaChecker({area_id}),
        SqlAlchemyEvidenceAuditLog(session),
    )

    try:
        created = service.create_observation(make_observation(area_id, source_id))
        session.commit()

        with Session(session.get_bind()) as read_session:
            events = SqlAlchemyEvidenceAuditLog(read_session).list_by_evidence(
                created.evidence_id
            )

        assert len(events) == 1
        assert events[0].event_type == EvidenceAuditEventType.CREATED
        assert events[0].area_id == area_id
        assert events[0].source_id == source_id
        assert events[0].evidence_type == EvidenceType.SOURCE_OBSERVATION
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_evidence_service_persists_supersession_audit_events(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    service = EvidenceService(
        SqlAlchemyEvidenceRepository(session),
        StubSourceChecker({source_id}),
        StubAreaChecker({area_id}),
        SqlAlchemyEvidenceAuditLog(session),
    )

    try:
        original = service.create_observation(make_observation(area_id, source_id))
        replacement = make_observation(area_id, source_id).model_copy(
            update={
                "evidence_code": "FLOOD_ZONE_X",
                "observation": "Corrected fixture source indicates zone X.",
                "observed_value": {"flood_zone": "X"},
            }
        )

        created = service.supersede(original.evidence_id, replacement)
        session.commit()

        with Session(session.get_bind()) as read_session:
            audit_log = SqlAlchemyEvidenceAuditLog(read_session)
            original_events = audit_log.list_by_evidence(original.evidence_id)
            replacement_events = audit_log.list_by_evidence(created.evidence_id)

        assert [event.event_type for event in original_events] == [
            EvidenceAuditEventType.CREATED,
            EvidenceAuditEventType.SUPERSEDED,
        ]
        assert original_events[-1].superseded_by == created.evidence_id
        assert [event.event_type for event in replacement_events] == [
            EvidenceAuditEventType.CREATED,
        ]
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_evidence_service_persists_source_failure_and_human_note(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    reviewer_id = uuid4()
    repo = SqlAlchemyEvidenceRepository(session)
    service = EvidenceService(
        repo,
        StubSourceChecker({source_id}),
        StubAreaChecker({area_id}),
        SqlAlchemyEvidenceAuditLog(session),
    )

    try:
        failure = service.create_source_failure(
            area_id=area_id,
            source_id=source_id,
            method_code="fixture_fema_request",
            caveat="FEMA fixture endpoint returned 503.",
            domain="flood",
            observed_value={
                "status_code": 503,
                "error_message": "Service unavailable.",
            },
        )
        note = service.create_human_note(
            EvidenceContract(
                area_id=area_id,
                source_id=reviewer_id,
                evidence_type=EvidenceType.HUMAN_VERIFICATION,
                evidence_code="REVIEW_NOTE",
                domain="review",
                observation="Reviewer noted a follow-up requirement.",
                method_code="human_review_note",
                confidence=ConfidenceBand.UNKNOWN,
            )
        )
        session.commit()

        with Session(session.get_bind()) as read_session:
            read_repo = SqlAlchemyEvidenceRepository(read_session)
            assert read_repo.get(failure.evidence_id) == failure
            assert read_repo.get(note.evidence_id) == note
            assert read_repo.list_by_type(EvidenceType.SOURCE_FAILURE) == [failure]
            assert read_repo.list_by_type(EvidenceType.HUMAN_VERIFICATION) == [note]
    finally:
        _delete_area_tree(session, area_id)


@pytest.mark.parametrize(
    ("evidence_type", "observed_value", "domain"),
    [
        (
            EvidenceType.SPATIAL_INTERSECTION,
            {"intersects": True, "intersection_ratio": 0.25},
            "flood",
        ),
        (
            EvidenceType.DERIVED_METRIC,
            {"metric_code": "slope_percent", "value": 8.25, "unit": "percent"},
            "buildability",
        ),
        (
            EvidenceType.DOCUMENT_EXTRACT,
            {
                "document_id": "fixture-doc-1",
                "extract_text": "County planning note requires confirmation.",
            },
            "zoning",
        ),
    ],
)
def test_sqlalchemy_evidence_service_persists_source_derived_evidence_types(
    evidence_type: EvidenceType,
    observed_value: dict[str, object],
    domain: str,
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    service = EvidenceService(
        SqlAlchemyEvidenceRepository(session),
        StubSourceChecker({source_id}),
        StubAreaChecker({area_id}),
    )
    evidence = make_observation(area_id, source_id).model_copy(
        update={
            "evidence_type": evidence_type,
            "evidence_code": f"{evidence_type.value.upper()}_FIXTURE",
            "domain": domain,
            "observed_value": observed_value,
        }
    )

    try:
        created = service.create_observation(evidence)
        session.commit()

        with Session(session.get_bind()) as read_session:
            read_repo = SqlAlchemyEvidenceRepository(read_session)
            assert read_repo.get(created.evidence_id) == created
            assert read_repo.list_by_type(evidence_type) == [created]
    finally:
        _delete_area_tree(session, area_id)


def test_sqlalchemy_evidence_service_rejects_invalid_payload_without_storing(
    session: Session,
) -> None:
    area_id = _insert_area(session)
    source_id = uuid4()
    repo = SqlAlchemyEvidenceRepository(session)
    service = EvidenceService(
        repo,
        StubSourceChecker({source_id}),
        StubAreaChecker({area_id}),
    )
    evidence = make_observation(area_id, source_id).model_copy(
        update={"observed_value": {"freeform": "not allowed"}}
    )

    try:
        with pytest.raises(ValueError, match="unsupported fields"):
            service.create_observation(evidence)

        assert repo.list_by_area(area_id) == []
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
                'evidence fixture area',
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
    evidence_ids = session.execute(
        text(
            """
            SELECT evidence_id
            FROM evidence.observations
            WHERE area_id = :area_id
            """
        ),
        {"area_id": area_id},
    ).scalars().all()
    if evidence_ids:
        session.execute(
            text(
                """
                DELETE FROM audit.events
                WHERE target_table = 'evidence.observations'
                    AND target_id = ANY(:evidence_ids)
                """
            ),
            {"evidence_ids": evidence_ids},
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
