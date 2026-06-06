from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.enums import EvidenceType
from app.domain.evidence_contracts import EvidenceContract

from .result import ConnectorResult


class ConnectorEvidenceIngestionError(ValueError):
    """Raised when connector evidence cannot be routed safely."""


class EvidenceIngestionPort(Protocol):
    def create_observation(self, evidence: EvidenceContract) -> EvidenceContract: ...

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
    ) -> EvidenceContract: ...

    def evidence_exists(self, evidence_id: UUID) -> bool: ...

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]: ...


@dataclass(frozen=True)
class ConnectorEvidenceIngestionResult:
    created_evidence: tuple[EvidenceContract, ...]
    skipped_evidence: tuple[EvidenceContract, ...]


class ConnectorEvidenceIngestionAdapter:
    def __init__(self, evidence_port: EvidenceIngestionPort) -> None:
        self._evidence_port = evidence_port

    def ingest(
        self,
        connector_result: ConnectorResult,
    ) -> ConnectorEvidenceIngestionResult:
        return self.ingest_evidence(connector_result.evidence_inputs)

    def ingest_evidence(
        self,
        evidence_inputs: Iterable[EvidenceContract],
    ) -> ConnectorEvidenceIngestionResult:
        created: list[EvidenceContract] = []
        skipped: list[EvidenceContract] = []

        for evidence in evidence_inputs:
            if evidence.is_source_failure:
                skipped_failure = self._matching_source_failure(evidence)
                if skipped_failure is not None:
                    skipped.append(skipped_failure)
                    continue
                if self._evidence_port.evidence_exists(evidence.evidence_id):
                    skipped.append(evidence)
                    continue
                created.append(self._create_source_failure(evidence))
                continue

            if self._evidence_port.evidence_exists(evidence.evidence_id):
                skipped.append(evidence)
                continue

            if evidence.evidence_type == EvidenceType.SOURCE_FAILURE:
                raise ConnectorEvidenceIngestionError(
                    "source-failure connector evidence must set is_source_failure",
                )
            created.append(self._evidence_port.create_observation(evidence))

        return ConnectorEvidenceIngestionResult(
            created_evidence=tuple(created),
            skipped_evidence=tuple(skipped),
        )

    def _create_source_failure(self, evidence: EvidenceContract) -> EvidenceContract:
        if evidence.caveat is None or not evidence.caveat.strip():
            raise ConnectorEvidenceIngestionError(
                "source-failure connector evidence must include caveat",
            )
        if evidence.evidence_type != EvidenceType.SOURCE_FAILURE:
            raise ConnectorEvidenceIngestionError(
                "is_source_failure connector evidence must use source_failure type",
            )
        return self._evidence_port.create_source_failure(
            evidence_id=evidence.evidence_id,
            area_id=evidence.area_id,
            source_id=evidence.source_id,
            method_code=evidence.method_code,
            caveat=evidence.caveat,
            evidence_code=evidence.evidence_code,
            domain=evidence.domain,
            observation=evidence.observation,
            observed_value=evidence.observed_value,
            source_ingest_run_id=evidence.source_ingest_run_id,
        )

    def _matching_source_failure(
        self,
        evidence: EvidenceContract,
    ) -> EvidenceContract | None:
        fingerprint = _source_failure_fingerprint(evidence)
        for existing in self._evidence_port.list_by_area(evidence.area_id):
            if not existing.is_source_failure:
                continue
            if _source_failure_fingerprint(existing) == fingerprint:
                return existing
        return None


def _source_failure_fingerprint(evidence: EvidenceContract) -> tuple[object, ...]:
    return (
        evidence.area_id,
        evidence.source_id,
        evidence.method_code,
        evidence.evidence_code,
        evidence.domain,
        evidence.observation,
        evidence.caveat,
        evidence.source_ingest_run_id,
        _stable_observed_value(evidence.observed_value),
    )


def _stable_observed_value(observed_value: dict[str, object]) -> str:
    return json.dumps(
        observed_value,
        default=str,
        separators=(",", ":"),
        sort_keys=True,
    )


__all__ = [
    "ConnectorEvidenceIngestionAdapter",
    "ConnectorEvidenceIngestionError",
    "ConnectorEvidenceIngestionResult",
    "EvidenceIngestionPort",
]
