from __future__ import annotations

from uuid import UUID

from app.claims_engine.claim_repo import ClaimRepository
from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, EvidenceType, SeverityBand
from app.domain.evidence_contracts import EvidenceContract
from app.evidence_ledger.evidence_repo import EvidenceRepository


class ClaimService:
    def __init__(
        self,
        repo: ClaimRepository,
        evidence_repo: EvidenceRepository,
    ) -> None:
        self._repo = repo
        self._evidence_repo = evidence_repo

    def create_claim(
        self,
        claim: ClaimContract,
        evidence_ids: list[UUID],
    ) -> ClaimContract:
        self._validate_claim_text(claim)
        self._validate_claim_evidence_ids_match(claim, evidence_ids)
        evidence = self._load_evidence(evidence_ids)
        self._validate_evidence_area(claim.area_id, evidence)
        return self._repo.add(claim)

    def create_unknown(
        self,
        *,
        area_id: UUID,
        claim_code: str,
        reason: str,
        evidence_ids: list[UUID],
        domain: str = "unknown",
        verification_task: str | None = None,
        rule_code: str | None = None,
        ruleset_id: str | None = None,
        ruleset_version: str | None = None,
    ) -> ClaimContract:
        _require_non_empty(claim_code, "claim_code")
        _require_non_empty(domain, "domain")
        _require_non_empty(reason, "reason")
        evidence = self._load_evidence(evidence_ids)
        self._validate_evidence_area(area_id, evidence)
        self._validate_has_source_failure(evidence)
        claim = ClaimContract(
            area_id=area_id,
            claim_code=claim_code,
            domain=domain,
            assertion=reason,
            user_safe_language=_unknown_user_safe_language(reason, evidence),
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=list(evidence_ids),
            rule_code=rule_code,
            ruleset_id=ruleset_id,
            ruleset_version=ruleset_version,
            verification_required=True,
            verification_task=verification_task
            or "Re-run or manually verify the failed source before treating this item as resolved.",
        )
        return self.create_claim(claim, evidence_ids)

    def get(self, claim_id: UUID) -> ClaimContract | None:
        return self._repo.get(claim_id)

    def list_by_area(self, area_id: UUID) -> list[ClaimContract]:
        return self._repo.list_by_area(area_id)

    def list_all(self) -> list[ClaimContract]:
        return self._repo.list_all()

    def claim_exists(self, claim_id: UUID) -> bool:
        return self._repo.exists(claim_id)

    def _validate_claim_text(self, claim: ClaimContract) -> None:
        _require_non_empty(claim.claim_code, "claim_code")
        _require_non_empty(claim.domain, "domain")
        _require_non_empty(claim.assertion, "assertion")
        _require_non_empty(claim.user_safe_language, "user_safe_language")
        if claim.verification_required:
            if claim.verification_task is None or not claim.verification_task.strip():
                raise ValueError("verification_task is required when verification_required is true")

    def _validate_claim_evidence_ids_match(
        self,
        claim: ClaimContract,
        evidence_ids: list[UUID],
    ) -> None:
        _validate_evidence_ids(evidence_ids)
        if claim.evidence_ids != evidence_ids:
            raise ValueError("claim.evidence_ids must match the supplied evidence_ids")

    def _load_evidence(self, evidence_ids: list[UUID]) -> list[EvidenceContract]:
        _validate_evidence_ids(evidence_ids)
        evidence_records: list[EvidenceContract] = []
        for evidence_id in evidence_ids:
            evidence = self._evidence_repo.get(evidence_id)
            if evidence is None:
                raise ValueError(f"Evidence '{evidence_id}' is not registered")
            if evidence.superseded_by is not None:
                raise ValueError("claims must not cite superseded evidence")
            evidence_records.append(evidence)
        return evidence_records

    def _validate_evidence_area(
        self,
        area_id: UUID,
        evidence_records: list[EvidenceContract],
    ) -> None:
        for evidence in evidence_records:
            if evidence.area_id != area_id:
                raise ValueError("claim evidence must reference the same area as the claim")

    def _validate_has_source_failure(
        self,
        evidence_records: list[EvidenceContract],
    ) -> None:
        if not any(
            evidence.is_source_failure
            or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
            for evidence in evidence_records
        ):
            raise ValueError("unknown claims require at least one source-failure evidence record")


def _validate_evidence_ids(evidence_ids: list[UUID]) -> None:
    if not evidence_ids:
        raise ValueError("claims must cite at least one evidence_id")
    if len(set(evidence_ids)) != len(evidence_ids):
        raise ValueError("claims must not cite duplicate evidence_ids")


def _unknown_user_safe_language(
    reason: str,
    evidence_records: list[EvidenceContract],
) -> str:
    caveats = [
        evidence.caveat.strip()
        for evidence in evidence_records
        if evidence.caveat is not None and evidence.caveat.strip()
    ]
    language = (
        f"{reason} The available evidence records a source failure, so this item "
        "remains unknown and requires verification."
    )
    if caveats:
        language = f"{language} Evidence caveat: {'; '.join(caveats)}"
    return language


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


__all__ = ["ClaimService"]
