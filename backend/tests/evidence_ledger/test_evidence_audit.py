from __future__ import annotations

from uuid import UUID, uuid4

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.evidence_ledger.audit_log import (
    EvidenceAuditEventType,
    InMemoryEvidenceAuditLog,
)
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService


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

    def area_is_registered(self, area_id: UUID) -> bool:
        return area_id in self._registered


def make_service(
    *,
    area_id: UUID,
    source_id: UUID,
    audit_log: InMemoryEvidenceAuditLog,
) -> EvidenceService:
    return EvidenceService(
        InMemoryEvidenceRepository(),
        StubSourceChecker({source_id}),
        StubAreaChecker({area_id}),
        audit_log,
    )


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
        confidence=ConfidenceBand.MEDIUM,
        caveat="Screening fixture only; confirm locally.",
    )


def test_create_observation_emits_created_audit_event() -> None:
    area_id = uuid4()
    source_id = uuid4()
    audit_log = InMemoryEvidenceAuditLog()
    service = make_service(area_id=area_id, source_id=source_id, audit_log=audit_log)

    created = service.create_observation(make_observation(area_id, source_id))
    events = audit_log.list_by_evidence(created.evidence_id)

    assert len(events) == 1
    assert events[0].event_type == EvidenceAuditEventType.CREATED
    assert events[0].area_id == area_id
    assert events[0].source_id == source_id
    assert events[0].evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert events[0].superseded_by is None


def test_create_source_failure_emits_created_audit_event() -> None:
    area_id = uuid4()
    source_id = uuid4()
    audit_log = InMemoryEvidenceAuditLog()
    service = make_service(area_id=area_id, source_id=source_id, audit_log=audit_log)

    created = service.create_source_failure(
        area_id=area_id,
        source_id=source_id,
        method_code="fixture_fema_request",
        caveat="FEMA fixture endpoint returned 503.",
        domain="flood",
    )
    events = audit_log.list_by_evidence(created.evidence_id)

    assert len(events) == 1
    assert events[0].event_type == EvidenceAuditEventType.CREATED
    assert events[0].evidence_type == EvidenceType.SOURCE_FAILURE


def test_create_human_note_emits_created_audit_event() -> None:
    area_id = uuid4()
    reviewer_id = uuid4()
    audit_log = InMemoryEvidenceAuditLog()
    service = make_service(area_id=area_id, source_id=reviewer_id, audit_log=audit_log)
    note = EvidenceContract(
        area_id=area_id,
        source_id=reviewer_id,
        evidence_type=EvidenceType.HUMAN_VERIFICATION,
        evidence_code="REVIEW_NOTE",
        domain="review",
        observation="Reviewer noted a follow-up requirement.",
        method_code="human_review_note",
        confidence=ConfidenceBand.UNKNOWN,
    )

    created = service.create_human_note(note)
    events = audit_log.list_by_evidence(created.evidence_id)

    assert len(events) == 1
    assert events[0].event_type == EvidenceAuditEventType.CREATED
    assert events[0].evidence_type == EvidenceType.HUMAN_VERIFICATION


def test_supersede_emits_replacement_created_and_original_superseded_events() -> None:
    area_id = uuid4()
    source_id = uuid4()
    audit_log = InMemoryEvidenceAuditLog()
    service = make_service(area_id=area_id, source_id=source_id, audit_log=audit_log)
    original = service.create_observation(make_observation(area_id, source_id))
    replacement = make_observation(area_id, source_id).model_copy(
        update={
            "evidence_code": "FLOOD_ZONE_X",
            "observation": "Corrected fixture source indicates zone X.",
            "observed_value": {"flood_zone": "X"},
        }
    )

    created = service.supersede(original.evidence_id, replacement)

    all_events = audit_log.list_all()
    original_events = audit_log.list_by_evidence(original.evidence_id)
    replacement_events = audit_log.list_by_evidence(created.evidence_id)

    assert [event.event_type for event in all_events] == [
        EvidenceAuditEventType.CREATED,
        EvidenceAuditEventType.CREATED,
        EvidenceAuditEventType.SUPERSEDED,
    ]
    assert [event.event_type for event in original_events] == [
        EvidenceAuditEventType.CREATED,
        EvidenceAuditEventType.SUPERSEDED,
    ]
    assert original_events[-1].superseded_by == created.evidence_id
    assert [event.event_type for event in replacement_events] == [
        EvidenceAuditEventType.CREATED,
    ]
