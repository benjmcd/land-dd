from __future__ import annotations

from uuid import UUID

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.protocols import AreaExistsProtocol, SourceExistsProtocol
from app.evidence_ledger.evidence_repo import EvidenceRepository

HUMAN_EVIDENCE_TYPES = {
    EvidenceType.HUMAN_VERIFICATION,
    EvidenceType.MANUAL_NOTE,
}
SOURCE_OBSERVATION_TYPES = {
    EvidenceType.SOURCE_OBSERVATION,
    EvidenceType.SPATIAL_INTERSECTION,
    EvidenceType.DERIVED_METRIC,
    EvidenceType.DOCUMENT_EXTRACT,
}


class EvidenceService:
    def __init__(
        self,
        repo: EvidenceRepository,
        source_checker: SourceExistsProtocol,
        area_checker: AreaExistsProtocol,
    ) -> None:
        self._repo = repo
        self._source_checker = source_checker
        self._area_checker = area_checker

    def create_observation(self, evidence: EvidenceContract) -> EvidenceContract:
        self._validate_area_registered(evidence.area_id)
        self._validate_source_registered(evidence.source_id)
        if not self._source_checker.source_production_use_allowed(evidence.source_id):
            raise ValueError(f"Source '{evidence.source_id}' is not allowed for production use")
        if evidence.evidence_type not in SOURCE_OBSERVATION_TYPES:
            raise ValueError("source observations must use a source-derived evidence type")
        if evidence.is_source_failure:
            raise ValueError("source failure evidence must use create_source_failure")
        self._validate_required_text(evidence)
        return self._repo.add(evidence)

    def create_source_failure(
        self,
        *,
        area_id: UUID,
        source_id: UUID,
        method_code: str,
        caveat: str,
        evidence_code: str = "SOURCE_FAILURE",
        domain: str = "unknown",
        observation: str | None = None,
        observed_value: dict[str, object] | None = None,
    ) -> EvidenceContract:
        self._validate_area_registered(area_id)
        self._validate_source_registered(source_id)
        _require_non_empty(method_code, "method_code")
        _require_non_empty(caveat, "caveat")
        failure_observation = observation or f"Source unavailable or failed: {caveat}"
        evidence = EvidenceContract(
            area_id=area_id,
            source_id=source_id,
            method_code=method_code,
            evidence_type=EvidenceType.SOURCE_FAILURE,
            evidence_code=evidence_code,
            domain=domain,
            observation=failure_observation,
            observed_value=observed_value or {},
            confidence=ConfidenceBand.UNKNOWN,
            caveat=caveat,
            is_source_failure=True,
        )
        return self._repo.add(evidence)

    def create_human_note(self, evidence: EvidenceContract) -> EvidenceContract:
        self._validate_area_registered(evidence.area_id)
        if evidence.evidence_type not in HUMAN_EVIDENCE_TYPES:
            raise ValueError("human notes must use manual_note or human_verification")
        if evidence.is_source_failure:
            raise ValueError("human notes cannot be source-failure evidence")
        self._validate_required_text(evidence)
        return self._repo.add(evidence)

    def get(self, evidence_id: UUID) -> EvidenceContract | None:
        return self._repo.get(evidence_id)

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        return self._repo.list_by_area(area_id)

    def list_by_source(self, source_id: UUID) -> list[EvidenceContract]:
        return self._repo.list_by_source(source_id)

    def list_by_type(self, evidence_type: EvidenceType) -> list[EvidenceContract]:
        return self._repo.list_by_type(evidence_type)

    def evidence_exists(self, evidence_id: UUID) -> bool:
        return self._repo.exists(evidence_id)

    def _validate_area_registered(self, area_id: UUID) -> None:
        if not self._area_checker.area_is_registered(area_id):
            raise ValueError(f"Area '{area_id}' is not registered")

    def _validate_source_registered(self, source_id: UUID) -> None:
        if not self._source_checker.source_is_registered(source_id):
            raise ValueError(f"Source '{source_id}' is not registered")

    def _validate_required_text(self, evidence: EvidenceContract) -> None:
        _require_non_empty(evidence.evidence_code, "evidence_code")
        _require_non_empty(evidence.domain, "domain")
        _require_non_empty(evidence.observation, "observation")
        _require_non_empty(evidence.method_code, "method_code")


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


__all__ = ["EvidenceService"]
