from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.claims_engine.models import (
    ClaimEvidenceLinkModel,
    ClaimModel,
    VerificationTaskModel,
)
from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, SeverityBand


class ClaimRepository(Protocol):
    def add(self, claim: ClaimContract) -> ClaimContract: ...

    def get(self, claim_id: UUID) -> ClaimContract | None: ...

    def exists(self, claim_id: UUID) -> bool: ...

    def list_by_area(self, area_id: UUID) -> list[ClaimContract]: ...

    def list_all(self) -> list[ClaimContract]: ...


class InMemoryClaimRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, ClaimContract] = {}

    def add(self, claim: ClaimContract) -> ClaimContract:
        if claim.claim_id in self._store:
            raise ValueError(f"Claim '{claim.claim_id}' is already stored")
        self._store[claim.claim_id] = claim
        return claim

    def get(self, claim_id: UUID) -> ClaimContract | None:
        return self._store.get(claim_id)

    def exists(self, claim_id: UUID) -> bool:
        return claim_id in self._store

    def list_by_area(self, area_id: UUID) -> list[ClaimContract]:
        return [
            claim
            for claim in self._store.values()
            if claim.area_id == area_id
        ]

    def list_all(self) -> list[ClaimContract]:
        return list(self._store.values())


class SqlAlchemyClaimRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, claim: ClaimContract) -> ClaimContract:
        _validate_claim_for_persistence(claim)
        if self.exists(claim.claim_id):
            raise ValueError(f"Claim '{claim.claim_id}' is already stored")

        model = ClaimModel(
            claim_id=claim.claim_id,
            area_id=claim.area_id,
            claim_code=claim.claim_code,
            domain=claim.domain,
            assertion=claim.assertion,
            severity=claim.severity.value,
            confidence=claim.confidence.value,
            user_safe_language=claim.user_safe_language,
            verification_required=claim.verification_required,
            verification_task=claim.verification_task,
            claim_metadata=_claim_metadata(claim),
        )
        self._session.add(model)

        self._session.add_all(
            ClaimEvidenceLinkModel(
                claim_id=claim.claim_id,
                evidence_id=ev_id,
                support_role="supports",
            )
            for ev_id in claim.evidence_ids
        )

        if claim.verification_required and claim.verification_task is not None:
            self._session.add(
                VerificationTaskModel(
                    area_id=claim.area_id,
                    claim_id=claim.claim_id,
                    task_code=claim.claim_code,
                    task_text=claim.verification_task,
                    priority=_verification_priority(claim.severity.value),
                    status="open",
                )
            )

        self._session.flush()
        stored = self.get(claim.claim_id)
        if stored is None:
            raise ValueError(f"Claim '{claim.claim_id}' was not stored")
        return stored

    def get(self, claim_id: UUID) -> ClaimContract | None:
        model = self._session.get(ClaimModel, claim_id)
        if model is None:
            return None
        return _model_to_claim(model, self._linked_evidence_ids(claim_id))

    def exists(self, claim_id: UUID) -> bool:
        return self._session.get(ClaimModel, claim_id) is not None

    def list_by_area(self, area_id: UUID) -> list[ClaimContract]:
        stmt = (
            select(ClaimModel)
            .where(ClaimModel.area_id == area_id)
            .order_by(ClaimModel.created_at, ClaimModel.claim_id)
        )
        return [
            _model_to_claim(m, self._linked_evidence_ids(m.claim_id))
            for m in self._session.scalars(stmt).all()
        ]

    def list_all(self) -> list[ClaimContract]:
        stmt = select(ClaimModel).order_by(ClaimModel.created_at, ClaimModel.claim_id)
        return [
            _model_to_claim(m, self._linked_evidence_ids(m.claim_id))
            for m in self._session.scalars(stmt).all()
        ]

    def _linked_evidence_ids(self, claim_id: UUID) -> list[UUID]:
        stmt = (
            select(ClaimEvidenceLinkModel.evidence_id)
            .where(ClaimEvidenceLinkModel.claim_id == claim_id)
            .order_by(ClaimEvidenceLinkModel.evidence_id)
        )
        return list(self._session.scalars(stmt).all())


def _claim_metadata(claim: ClaimContract) -> dict[str, object]:
    metadata: dict[str, object] = {
        "evidence_ids": [str(evidence_id) for evidence_id in claim.evidence_ids],
    }
    if claim.rule_code is not None:
        metadata["rule_code"] = claim.rule_code
    if claim.ruleset_id is not None:
        metadata["ruleset_id"] = claim.ruleset_id
    if claim.ruleset_version is not None:
        metadata["ruleset_version"] = claim.ruleset_version
    return metadata


def _model_to_claim(model: ClaimModel, linked_evidence_ids: list[UUID]) -> ClaimContract:
    metadata = model.claim_metadata if isinstance(model.claim_metadata, dict) else {}
    evidence_ids = _metadata_evidence_ids(metadata, linked_evidence_ids)
    return ClaimContract(
        claim_id=model.claim_id,
        area_id=model.area_id,
        claim_code=model.claim_code,
        domain=model.domain,
        assertion=model.assertion,
        user_safe_language=model.user_safe_language,
        severity=SeverityBand(model.severity),
        confidence=ConfidenceBand(model.confidence),
        evidence_ids=evidence_ids,
        rule_code=_optional_metadata_str(metadata, "rule_code"),
        ruleset_id=_optional_metadata_str(metadata, "ruleset_id"),
        ruleset_version=_optional_metadata_str(metadata, "ruleset_version"),
        verification_required=model.verification_required,
        verification_task=model.verification_task,
    )


def _metadata_evidence_ids(
    metadata: dict[str, object],
    linked_evidence_ids: list[UUID],
) -> list[UUID]:
    ordered_value = metadata.get("evidence_ids")
    if ordered_value is None:
        return linked_evidence_ids
    if not isinstance(ordered_value, list) or not ordered_value:
        raise ValueError("claims.claims metadata.evidence_ids must be a non-empty list")
    ordered_ids = [UUID(str(value)) for value in ordered_value]
    if set(ordered_ids) != set(linked_evidence_ids):
        raise ValueError("claims.claims metadata evidence_ids conflict with links")
    return ordered_ids


def _optional_metadata_str(metadata: dict[str, object], key: str) -> str | None:
    value = metadata.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"claims.claims metadata.{key} must be a string")
    return value


def _validate_claim_for_persistence(claim: ClaimContract) -> None:
    if not claim.evidence_ids:
        raise ValueError("claims must cite at least one evidence_id")
    if len(set(claim.evidence_ids)) != len(claim.evidence_ids):
        raise ValueError("claims must not cite duplicate evidence_ids")
    if claim.verification_required:
        if claim.verification_task is None or not claim.verification_task.strip():
            raise ValueError(
                "verification_task is required when verification_required is true"
            )


def _verification_priority(severity: str) -> str:
    if severity == SeverityBand.UNKNOWN.value:
        return SeverityBand.MEDIUM.value
    return severity


__all__ = [
    "ClaimRepository",
    "InMemoryClaimRepository",
    "SqlAlchemyClaimRepository",
]
