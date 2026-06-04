from __future__ import annotations

import json
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import TextClause

from app.domain.claim_contracts import ClaimContract
from app.domain.enums import SeverityBand


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

        self._session.execute(
            text(
                """
                INSERT INTO claims.claims (
                    claim_id,
                    area_id,
                    claim_code,
                    domain,
                    assertion,
                    severity,
                    confidence,
                    user_safe_language,
                    verification_required,
                    verification_task,
                    metadata
                )
                VALUES (
                    :claim_id,
                    :area_id,
                    :claim_code,
                    :domain,
                    :assertion,
                    CAST(:severity AS claims.severity_band),
                    CAST(:confidence AS evidence.confidence_band),
                    :user_safe_language,
                    :verification_required,
                    :verification_task,
                    CAST(:metadata AS jsonb)
                )
                """
            ),
            _claim_params(claim),
        )
        self._insert_evidence_links(claim)
        self._insert_verification_task(claim)
        self._session.flush()
        stored = self.get(claim.claim_id)
        if stored is None:
            raise ValueError(f"Claim '{claim.claim_id}' was not stored")
        return stored

    def get(self, claim_id: UUID) -> ClaimContract | None:
        row = self._session.execute(
            _select_claim_statement("WHERE claim_id = :claim_id"),
            {"claim_id": claim_id},
        ).mappings().one_or_none()
        if row is None:
            return None
        return _row_to_claim(row, self._linked_evidence_ids(claim_id))

    def exists(self, claim_id: UUID) -> bool:
        return (
            self._session.execute(
                text(
                    """
                    SELECT 1
                    FROM claims.claims
                    WHERE claim_id = :claim_id
                    LIMIT 1
                    """
                ),
                {"claim_id": claim_id},
            ).first()
            is not None
        )

    def list_by_area(self, area_id: UUID) -> list[ClaimContract]:
        rows = self._session.execute(
            _select_claim_statement(
                "WHERE area_id = :area_id ORDER BY created_at, claim_id"
            ),
            {"area_id": area_id},
        ).mappings().all()
        return [
            _row_to_claim(row, self._linked_evidence_ids(row["claim_id"]))
            for row in rows
        ]

    def list_all(self) -> list[ClaimContract]:
        rows = self._session.execute(
            _select_claim_statement("ORDER BY created_at, claim_id")
        ).mappings().all()
        return [
            _row_to_claim(row, self._linked_evidence_ids(row["claim_id"]))
            for row in rows
        ]

    def _insert_evidence_links(self, claim: ClaimContract) -> None:
        for evidence_id in claim.evidence_ids:
            self._session.execute(
                text(
                    """
                    INSERT INTO claims.claim_evidence (
                        claim_id,
                        evidence_id,
                        support_role
                    )
                    VALUES (
                        :claim_id,
                        :evidence_id,
                        'supports'
                    )
                    """
                ),
                {"claim_id": claim.claim_id, "evidence_id": evidence_id},
            )

    def _insert_verification_task(self, claim: ClaimContract) -> None:
        if not claim.verification_required or claim.verification_task is None:
            return
        self._session.execute(
            text(
                """
                INSERT INTO claims.verification_tasks (
                    area_id,
                    claim_id,
                    task_code,
                    task_text,
                    priority,
                    status
                )
                VALUES (
                    :area_id,
                    :claim_id,
                    :task_code,
                    :task_text,
                    CAST(:priority AS claims.severity_band),
                    'open'
                )
                """
            ),
            {
                "area_id": claim.area_id,
                "claim_id": claim.claim_id,
                "task_code": claim.claim_code,
                "task_text": claim.verification_task,
                "priority": _verification_priority(claim.severity.value),
            },
        )

    def _linked_evidence_ids(self, claim_id: UUID) -> list[UUID]:
        return list(
            self._session.execute(
                text(
                    """
                    SELECT evidence_id
                    FROM claims.claim_evidence
                    WHERE claim_id = :claim_id
                    ORDER BY evidence_id
                    """
                ),
                {"claim_id": claim_id},
            ).scalars().all()
        )


def _select_claim_statement(suffix: str) -> TextClause:
    return text(
        f"""
        SELECT
            claim_id,
            area_id,
            claim_code,
            domain,
            assertion,
            severity::text AS severity,
            confidence::text AS confidence,
            user_safe_language,
            verification_required,
            verification_task,
            metadata AS claim_metadata
        FROM claims.claims
        {suffix}
        """
    )


def _claim_params(claim: ClaimContract) -> dict[str, object]:
    return {
        "claim_id": claim.claim_id,
        "area_id": claim.area_id,
        "claim_code": claim.claim_code,
        "domain": claim.domain,
        "assertion": claim.assertion,
        "severity": claim.severity.value,
        "confidence": claim.confidence.value,
        "user_safe_language": claim.user_safe_language,
        "verification_required": claim.verification_required,
        "verification_task": claim.verification_task,
        "metadata": json.dumps(_claim_metadata(claim)),
    }


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


def _row_to_claim(row: Any, linked_evidence_ids: list[UUID]) -> ClaimContract:
    metadata = _json_object(row["claim_metadata"], "claim metadata")
    evidence_ids = _metadata_evidence_ids(metadata, linked_evidence_ids)
    return ClaimContract(
        claim_id=row["claim_id"],
        area_id=row["area_id"],
        claim_code=row["claim_code"],
        domain=row["domain"],
        assertion=row["assertion"],
        user_safe_language=row["user_safe_language"],
        severity=row["severity"],
        confidence=row["confidence"],
        evidence_ids=evidence_ids,
        rule_code=_optional_metadata_str(metadata, "rule_code"),
        ruleset_id=_optional_metadata_str(metadata, "ruleset_id"),
        ruleset_version=_optional_metadata_str(metadata, "ruleset_version"),
        verification_required=row["verification_required"],
        verification_task=row["verification_task"],
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


def _json_object(value: object, label: str) -> dict[str, object]:
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError(f"claims.claims returned invalid {label}")
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
