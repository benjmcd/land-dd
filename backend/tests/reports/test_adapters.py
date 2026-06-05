from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService
from app.reports.adapters import AreaServiceProtocolAdapter, SourceServiceProtocolAdapter


class StubSourceService:
    def __init__(
        self,
        *,
        registered: set[UUID],
        production_allowed: set[UUID] | None = None,
    ) -> None:
        self._registered = registered
        self._production_allowed = registered if production_allowed is None else production_allowed

    def source_is_registered(self, source_id: UUID) -> bool:
        return source_id in self._registered

    def source_production_use_allowed(self, source_id: UUID) -> bool:
        return source_id in self._production_allowed


class StubAreaService:
    def __init__(self, registered: set[UUID]) -> None:
        self._registered = registered

    def area_is_registered(
        self,
        area_id: UUID,
        *,
        workspace_id: UUID | None = None,
    ) -> bool:
        return area_id in self._registered


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


def test_source_service_protocol_adapter_delegates_lookup_methods() -> None:
    source_id = uuid4()
    adapter = SourceServiceProtocolAdapter(
        StubSourceService(registered={source_id}, production_allowed=set())
    )

    assert adapter.source_is_registered(source_id) is True
    assert adapter.source_production_use_allowed(source_id) is False


def test_area_service_protocol_adapter_delegates_registration_check() -> None:
    area_id = uuid4()
    adapter = AreaServiceProtocolAdapter(StubAreaService({area_id}))

    assert adapter.area_is_registered(area_id) is True
    assert adapter.area_is_registered(uuid4()) is False


def test_adapter_backed_evidence_service_preserves_guardrails() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_service = EvidenceService(
        InMemoryEvidenceRepository(),
        SourceServiceProtocolAdapter(
            StubSourceService(registered={source_id}, production_allowed=set())
        ),
        AreaServiceProtocolAdapter(StubAreaService({area_id})),
    )

    with pytest.raises(ValueError, match="not allowed for production use"):
        evidence_service.create_observation(make_observation(area_id, source_id))


def test_adapter_backed_evidence_service_can_create_source_failure() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_service = EvidenceService(
        InMemoryEvidenceRepository(),
        SourceServiceProtocolAdapter(StubSourceService(registered={source_id})),
        AreaServiceProtocolAdapter(StubAreaService({area_id})),
    )

    created = evidence_service.create_source_failure(
        area_id=area_id,
        source_id=source_id,
        method_code="fixture_fema_request",
        caveat="Fixture source request returned 503.",
        domain="flood",
    )

    assert created.is_source_failure is True
    assert created.source_id == source_id
