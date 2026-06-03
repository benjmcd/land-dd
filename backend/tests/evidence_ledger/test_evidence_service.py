from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService


class StubSourceChecker:
    def __init__(
        self,
        registered: set[UUID],
        production_allowed: set[UUID] | None = None,
    ) -> None:
        self._registered = registered
        self._production_allowed = registered if production_allowed is None else production_allowed

    def source_is_registered(self, source_id: UUID) -> bool:
        return source_id in self._registered

    def source_production_use_allowed(self, source_id: UUID) -> bool:
        return source_id in self._production_allowed


class StubAreaChecker:
    def __init__(self, registered: set[UUID]) -> None:
        self._registered = registered

    def area_is_registered(self, area_id: UUID) -> bool:
        return area_id in self._registered


def make_service(
    *,
    area_id: UUID,
    source_id: UUID,
    production_allowed: bool = True,
) -> EvidenceService:
    allowed_sources = {source_id} if production_allowed else set()
    return EvidenceService(
        InMemoryEvidenceRepository(),
        StubSourceChecker({source_id}, allowed_sources),
        StubAreaChecker({area_id}),
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
        caveat="Screening fixture only; confirm with local floodplain administrator.",
    )


def test_create_observation_stores_and_retrieves_area_source_and_type() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    observation = make_observation(area_id, source_id)

    created = service.create_observation(observation)

    assert service.get(created.evidence_id) == created
    assert service.evidence_exists(created.evidence_id) is True
    assert service.list_by_area(area_id) == [created]
    assert service.list_by_source(source_id) == [created]
    assert service.list_by_type(EvidenceType.SOURCE_OBSERVATION) == [created]


def test_create_observation_rejects_unknown_source() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = EvidenceService(
        InMemoryEvidenceRepository(),
        StubSourceChecker(set()),
        StubAreaChecker({area_id}),
    )

    with pytest.raises(ValueError, match="Source .* is not registered"):
        service.create_observation(make_observation(area_id, source_id))


def test_create_observation_rejects_disallowed_source_use() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(
        area_id=area_id,
        source_id=source_id,
        production_allowed=False,
    )

    with pytest.raises(ValueError, match="not allowed for production use"):
        service.create_observation(make_observation(area_id, source_id))


def test_create_observation_rejects_unknown_area() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = EvidenceService(
        InMemoryEvidenceRepository(),
        StubSourceChecker({source_id}),
        StubAreaChecker(set()),
    )

    with pytest.raises(ValueError, match="Area .* is not registered"):
        service.create_observation(make_observation(area_id, source_id))


def test_create_observation_rejects_source_failure_type() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_observation(area_id, source_id).model_copy(
        update={
            "evidence_type": EvidenceType.SOURCE_FAILURE,
            "is_source_failure": True,
        }
    )

    with pytest.raises(ValueError, match="source-derived evidence type"):
        service.create_observation(evidence)


def test_create_source_failure_records_missing_data_as_evidence() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(
        area_id=area_id,
        source_id=source_id,
        production_allowed=False,
    )

    created = service.create_source_failure(
        area_id=area_id,
        source_id=source_id,
        method_code="fixture_fema_request",
        caveat="FEMA fixture endpoint returned 503.",
        domain="flood",
    )

    assert created.evidence_type == EvidenceType.SOURCE_FAILURE
    assert created.is_source_failure is True
    assert created.confidence == ConfidenceBand.UNKNOWN
    assert "503" in (created.caveat or "")
    assert service.list_by_area(area_id) == [created]


def test_create_source_failure_requires_registered_source() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = EvidenceService(
        InMemoryEvidenceRepository(),
        StubSourceChecker(set()),
        StubAreaChecker({area_id}),
    )

    with pytest.raises(ValueError, match="Source .* is not registered"):
        service.create_source_failure(
            area_id=area_id,
            source_id=source_id,
            method_code="fixture_fema_request",
            caveat="Source unreachable.",
        )


def test_create_human_note_is_typed_separately_from_source_observation() -> None:
    area_id = uuid4()
    reviewer_id = uuid4()
    unrelated_source_id = uuid4()
    service = EvidenceService(
        InMemoryEvidenceRepository(),
        StubSourceChecker({unrelated_source_id}),
        StubAreaChecker({area_id}),
    )
    note = EvidenceContract(
        area_id=area_id,
        source_id=reviewer_id,
        evidence_type=EvidenceType.HUMAN_VERIFICATION,
        evidence_code="REVIEW_NOTE",
        domain="review",
        observation="Reviewer confirmed the fixture observation needs follow-up.",
        method_code="human_review_note",
        confidence=ConfidenceBand.UNKNOWN,
        caveat="Human note; does not overwrite source evidence.",
    )

    created = service.create_human_note(note)

    assert created.evidence_type == EvidenceType.HUMAN_VERIFICATION
    assert created.source_id == reviewer_id
    assert service.list_by_type(EvidenceType.HUMAN_VERIFICATION) == [created]


def test_create_human_note_rejects_source_observation_type() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)

    with pytest.raises(ValueError, match="human notes must use"):
        service.create_human_note(make_observation(area_id, source_id))


def test_repository_rejects_duplicate_evidence_id_without_overwrite() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    observation = make_observation(area_id, source_id)

    service.create_observation(observation)

    with pytest.raises(ValueError, match="already stored"):
        service.create_observation(observation)
    assert service.get(observation.evidence_id) == observation
