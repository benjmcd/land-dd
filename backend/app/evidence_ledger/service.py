from __future__ import annotations

from typing import Any
from uuid import UUID

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.protocols import AreaExistsProtocol, SourceExistsProtocol
from app.evidence_ledger.audit_log import (
    EvidenceAuditEvent,
    EvidenceAuditEventType,
    EvidenceAuditLog,
)
from app.evidence_ledger.evidence_repo import EvidenceRepository
from app.evidence_ledger.payload_validation import validate_observed_value

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
        audit_log: EvidenceAuditLog | None = None,
    ) -> None:
        self._repo = repo
        self._source_checker = source_checker
        self._area_checker = area_checker
        self._audit_log = audit_log

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
        validate_observed_value(evidence)
        self._validate_new_record_not_superseded(evidence)
        created = self._repo.add(evidence)
        self._record_created(created)
        return created

    def create_source_failure(
        self,
        *,
        evidence_id: UUID | None = None,
        area_id: UUID,
        source_id: UUID,
        method_code: str,
        caveat: str,
        evidence_code: str = "SOURCE_FAILURE",
        domain: str = "unknown",
        observation: str | None = None,
        observed_value: dict[str, object] | None = None,
        source_ingest_run_id: UUID | None = None,
    ) -> EvidenceContract:
        self._validate_area_registered(area_id)
        self._validate_source_registered(source_id)
        _require_non_empty(method_code, "method_code")
        _require_non_empty(caveat, "caveat")
        failure_observation = observation or f"Source unavailable or failed: {caveat}"
        evidence_data: dict[str, Any] = {
            "area_id": area_id,
            "source_id": source_id,
            "method_code": method_code,
            "evidence_type": EvidenceType.SOURCE_FAILURE,
            "evidence_code": evidence_code,
            "domain": domain,
            "observation": failure_observation,
            "observed_value": observed_value or {},
            "confidence": ConfidenceBand.UNKNOWN,
            "caveat": caveat,
            "is_source_failure": True,
            "source_ingest_run_id": source_ingest_run_id,
        }
        if evidence_id is not None:
            evidence_data["evidence_id"] = evidence_id
        evidence = EvidenceContract(**evidence_data)
        return self._create_source_failure_evidence(evidence)

    def create_human_note(self, evidence: EvidenceContract) -> EvidenceContract:
        self._validate_area_registered(evidence.area_id)
        if evidence.evidence_type not in HUMAN_EVIDENCE_TYPES:
            raise ValueError("human notes must use manual_note or human_verification")
        if evidence.is_source_failure:
            raise ValueError("human notes cannot be source-failure evidence")
        self._validate_required_text(evidence)
        validate_observed_value(evidence)
        self._validate_new_record_not_superseded(evidence)
        created = self._repo.add(evidence)
        self._record_created(created)
        return created

    def supersede(
        self,
        evidence_id: UUID,
        replacement: EvidenceContract,
    ) -> EvidenceContract:
        original = self._repo.get(evidence_id)
        if original is None:
            raise ValueError(f"Evidence '{evidence_id}' is not registered")
        if original.superseded_by is not None:
            raise ValueError(f"Evidence '{evidence_id}' is already superseded")
        if replacement.evidence_id == evidence_id:
            raise ValueError("replacement evidence must use a new evidence_id")
        if replacement.superseded_by is not None:
            raise ValueError("replacement evidence must not already be superseded")
        if replacement.area_id != original.area_id:
            raise ValueError("replacement evidence must reference the same area")

        created = self._create_validated_replacement(replacement)
        superseded_original = self._repo.mark_superseded(evidence_id, created.evidence_id)
        self._record_superseded(superseded_original)
        return created

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

    def _create_validated_replacement(
        self,
        evidence: EvidenceContract,
    ) -> EvidenceContract:
        if evidence.evidence_type in HUMAN_EVIDENCE_TYPES:
            return self.create_human_note(evidence)
        if evidence.evidence_type == EvidenceType.SOURCE_FAILURE:
            return self._create_source_failure_evidence(evidence)
        return self.create_observation(evidence)

    def _create_source_failure_evidence(
        self,
        evidence: EvidenceContract,
    ) -> EvidenceContract:
        self._validate_area_registered(evidence.area_id)
        self._validate_source_registered(evidence.source_id)
        if not evidence.is_source_failure:
            raise ValueError("source failure evidence must set is_source_failure")
        self._validate_required_text(evidence)
        validate_observed_value(evidence)
        self._validate_new_record_not_superseded(evidence)
        if evidence.caveat is None or not evidence.caveat.strip():
            raise ValueError("caveat is required")
        created = self._repo.add(evidence)
        self._record_created(created)
        return created

    def _validate_required_text(self, evidence: EvidenceContract) -> None:
        _require_non_empty(evidence.evidence_code, "evidence_code")
        _require_non_empty(evidence.domain, "domain")
        _require_non_empty(evidence.observation, "observation")
        _require_non_empty(evidence.method_code, "method_code")

    def _validate_new_record_not_superseded(self, evidence: EvidenceContract) -> None:
        if evidence.superseded_by is not None:
            raise ValueError("new evidence records must not already be superseded")

    def _record_created(self, evidence: EvidenceContract) -> None:
        if self._audit_log is None:
            return
        self._audit_log.record(
            EvidenceAuditEvent(
                event_type=EvidenceAuditEventType.CREATED,
                evidence_id=evidence.evidence_id,
                area_id=evidence.area_id,
                source_id=evidence.source_id,
                evidence_type=evidence.evidence_type,
            )
        )

    def _record_superseded(self, evidence: EvidenceContract) -> None:
        if self._audit_log is None:
            return
        self._audit_log.record(
            EvidenceAuditEvent(
                event_type=EvidenceAuditEventType.SUPERSEDED,
                evidence_id=evidence.evidence_id,
                area_id=evidence.area_id,
                source_id=evidence.source_id,
                evidence_type=evidence.evidence_type,
                superseded_by=evidence.superseded_by,
            )
        )


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


__all__ = ["EvidenceService"]
