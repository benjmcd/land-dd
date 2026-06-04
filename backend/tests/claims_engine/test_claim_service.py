from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.claims_engine.claim_repo import InMemoryClaimRepository
from app.claims_engine.service import ClaimService
from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, EvidenceType, SeverityBand
from app.domain.evidence_contracts import EvidenceContract
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


def make_evidence_repo(
    *,
    area_ids: set[UUID],
    source_id: UUID,
) -> tuple[InMemoryEvidenceRepository, EvidenceService]:
    evidence_repo = InMemoryEvidenceRepository()
    evidence_service = EvidenceService(
        evidence_repo,
        StubSourceChecker({source_id}),
        StubAreaChecker(area_ids),
    )
    return evidence_repo, evidence_service


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
        verification_required=True,
        verification_task="Confirm floodplain status with the local floodplain administrator.",
    )


def test_create_claim_stores_evidence_linked_claim() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_repo, evidence_service = make_evidence_repo(
        area_ids={area_id},
        source_id=source_id,
    )
    evidence = evidence_service.create_observation(make_observation(area_id, source_id))
    service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    claim = make_claim(area_id, evidence.evidence_id)

    created = service.create_claim(claim, [evidence.evidence_id])

    assert service.get(created.claim_id) == created
    assert service.claim_exists(created.claim_id) is True
    assert created.severity == SeverityBand.HIGH
    assert created.confidence == ConfidenceBand.MEDIUM
    assert service.list_by_area(area_id) == [created]
    assert service.list_all() == [created]


def test_create_claim_rejects_missing_evidence() -> None:
    area_id = uuid4()
    missing_evidence_id = uuid4()
    service = ClaimService(InMemoryClaimRepository(), InMemoryEvidenceRepository())
    claim = make_claim(area_id, missing_evidence_id)

    with pytest.raises(ValueError, match="Evidence .* is not registered"):
        service.create_claim(claim, [missing_evidence_id])
    assert service.claim_exists(claim.claim_id) is False


def test_create_claim_rejects_empty_evidence_ids_even_if_contract_is_constructed() -> None:
    area_id = uuid4()
    service = ClaimService(InMemoryClaimRepository(), InMemoryEvidenceRepository())
    claim = ClaimContract.model_construct(
        area_id=area_id,
        claim_code="UNSUPPORTED_EMPTY_CLAIM",
        domain="flood",
        assertion="This invalid claim intentionally has no evidence.",
        user_safe_language="This invalid claim intentionally has no evidence.",
        severity=SeverityBand.UNKNOWN,
        confidence=ConfidenceBand.UNKNOWN,
        evidence_ids=[],
        verification_required=True,
        verification_task="Verify invalid construction is rejected.",
    )

    with pytest.raises(ValueError, match="at least one evidence_id"):
        service.create_claim(claim, [])


def test_create_claim_rejects_duplicate_evidence_ids() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_repo, evidence_service = make_evidence_repo(
        area_ids={area_id},
        source_id=source_id,
    )
    evidence = evidence_service.create_observation(make_observation(area_id, source_id))
    service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    claim = ClaimContract(
        area_id=area_id,
        claim_code="DUPLICATE_EVIDENCE_CLAIM",
        domain="flood",
        assertion="Invalid claim repeats the same evidence ID.",
        user_safe_language="Invalid claim repeats the same evidence ID.",
        severity=SeverityBand.UNKNOWN,
        confidence=ConfidenceBand.UNKNOWN,
        evidence_ids=[evidence.evidence_id, evidence.evidence_id],
        verification_required=True,
        verification_task="Verify duplicate evidence is rejected.",
    )

    with pytest.raises(ValueError, match="duplicate evidence_ids"):
        service.create_claim(claim, claim.evidence_ids)


def test_create_claim_rejects_superseded_evidence() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_repo, evidence_service = make_evidence_repo(
        area_ids={area_id},
        source_id=source_id,
    )
    evidence = evidence_service.create_observation(make_observation(area_id, source_id))
    replacement = evidence_service.create_observation(
        make_observation(area_id, source_id)
    )
    evidence_repo.mark_superseded(evidence.evidence_id, replacement.evidence_id)
    service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    claim = make_claim(area_id, evidence.evidence_id)

    with pytest.raises(ValueError, match="superseded evidence"):
        service.create_claim(claim, [evidence.evidence_id])


def test_create_claim_rejects_mismatched_supplied_evidence_ids() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_repo, evidence_service = make_evidence_repo(
        area_ids={area_id},
        source_id=source_id,
    )
    evidence = evidence_service.create_observation(make_observation(area_id, source_id))
    service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    claim = make_claim(area_id, evidence.evidence_id)

    with pytest.raises(ValueError, match="must match"):
        service.create_claim(claim, [uuid4()])


def test_create_claim_rejects_cross_area_evidence() -> None:
    area_id = uuid4()
    other_area_id = uuid4()
    source_id = uuid4()
    evidence_repo, evidence_service = make_evidence_repo(
        area_ids={area_id, other_area_id},
        source_id=source_id,
    )
    evidence = evidence_service.create_observation(
        make_observation(other_area_id, source_id)
    )
    service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    claim = make_claim(area_id, evidence.evidence_id)

    with pytest.raises(ValueError, match="same area"):
        service.create_claim(claim, [evidence.evidence_id])


def test_create_claim_requires_user_safe_language() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_repo, evidence_service = make_evidence_repo(
        area_ids={area_id},
        source_id=source_id,
    )
    evidence = evidence_service.create_observation(make_observation(area_id, source_id))
    service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    claim = make_claim(area_id, evidence.evidence_id).model_copy(
        update={"user_safe_language": "", "verification_task": None}
    )

    with pytest.raises(ValueError, match="user_safe_language is required"):
        service.create_claim(claim, [evidence.evidence_id])


def test_create_claim_requires_verification_task_when_required() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_repo, evidence_service = make_evidence_repo(
        area_ids={area_id},
        source_id=source_id,
    )
    evidence = evidence_service.create_observation(make_observation(area_id, source_id))
    service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    claim = make_claim(area_id, evidence.evidence_id).model_copy(
        update={"verification_task": None}
    )

    with pytest.raises(ValueError, match="verification_task is required"):
        service.create_claim(claim, [evidence.evidence_id])


def test_create_unknown_generates_blocker_claim_from_source_failure() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_repo, evidence_service = make_evidence_repo(
        area_ids={area_id},
        source_id=source_id,
    )
    failure = evidence_service.create_source_failure(
        area_id=area_id,
        source_id=source_id,
        method_code="fixture_fema_request",
        caveat="FEMA fixture endpoint returned 503.",
        domain="flood",
    )
    service = ClaimService(InMemoryClaimRepository(), evidence_repo)

    created = service.create_unknown(
        area_id=area_id,
        claim_code="FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        reason="Flood source data could not be retrieved.",
        evidence_ids=[failure.evidence_id],
        domain="flood",
    )

    assert created.severity == SeverityBand.UNKNOWN
    assert created.confidence == ConfidenceBand.UNKNOWN
    assert created.evidence_ids == [failure.evidence_id]
    assert created.verification_required is True
    assert created.verification_task is not None
    assert "503" in created.user_safe_language
    assert service.get(created.claim_id) == created


def test_create_unknown_requires_source_failure_evidence() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_repo, evidence_service = make_evidence_repo(
        area_ids={area_id},
        source_id=source_id,
    )
    evidence = evidence_service.create_observation(make_observation(area_id, source_id))
    service = ClaimService(InMemoryClaimRepository(), evidence_repo)

    with pytest.raises(ValueError, match="source-failure evidence"):
        service.create_unknown(
            area_id=area_id,
            claim_code="FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
            reason="Flood source data could not be retrieved.",
            evidence_ids=[evidence.evidence_id],
            domain="flood",
        )


def test_repository_rejects_duplicate_claim_id_without_overwrite() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence_repo, evidence_service = make_evidence_repo(
        area_ids={area_id},
        source_id=source_id,
    )
    evidence = evidence_service.create_observation(make_observation(area_id, source_id))
    service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    claim = make_claim(area_id, evidence.evidence_id)

    service.create_claim(claim, [evidence.evidence_id])

    with pytest.raises(ValueError, match="already stored"):
        service.create_claim(claim, [evidence.evidence_id])
    assert service.get(claim.claim_id) == claim
