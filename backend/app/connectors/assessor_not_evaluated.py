from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid5

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)

ASSESSOR_NOT_EVALUATED_CONNECTOR_NAME = "county_assessor_not_evaluated"
ASSESSOR_NOT_EVALUATED_METHOD_CODE = "assessor_not_evaluated_mvp"
ASSESSOR_NOT_EVALUATED_CAVEAT = (
    "Assessor and tax data were not available through a machine-queryable county "
    "connection for this analysis. Tax records, assessed value, and ownership "
    "information require confirmation by the county Tax Administration office. "
    "Assessed value is not market value. No programmatic access terms have been "
    "reviewed for any private-MVP county assessor portal."
)

_NAMESPACE = UUID("b2c4e6a8-1d3f-4b7c-9e5a-0f2d4c6e8a0b")


@dataclass(frozen=True)
class AssessorNotEvaluatedConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]


class AssessorNotEvaluatedConnector:
    """Connector for county assessor data that explicitly records NOT_EVALUATED evidence.

    No live county assessor connection is established in the private MVP because
    machine-access terms have not been reviewed for any county assessor portal.
    This connector records that fact explicitly in the evidence ledger so the
    absence of assessor data is auditable and attributed to DS-011.
    """

    connector_name = ASSESSOR_NOT_EVALUATED_CONNECTOR_NAME
    domain = "assessor"

    def query_area(
        self,
        *,
        area_id: UUID,
        source: SourceContract,
    ) -> AssessorNotEvaluatedConnectorResult:
        """Return explicit ASSESSOR_NOT_EVALUATED evidence for the given area."""
        ingest_run_id = uuid5(_NAMESPACE, f"assessor-not-evaluated|{area_id}")
        now = datetime.now(UTC)
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=ASSESSOR_NOT_EVALUATED_CONNECTOR_NAME,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=now,
            finished_at=now,
            row_count=1,
            error_count=0,
            warning_count=0,
            metrics={
                "source_registry_id": source.metadata.get("source_registry_id"),
                "method": ASSESSOR_NOT_EVALUATED_METHOD_CODE,
                "reason": "machine_access_terms_not_reviewed",
            },
        )
        evidence = EvidenceContract(
            evidence_id=uuid5(_NAMESPACE, f"assessor-not-evaluated-evidence|{area_id}"),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_FAILURE,
            evidence_code="ASSESSOR_NOT_EVALUATED",
            domain="assessor",
            observation=(
                "County assessor data not evaluated: no machine-queryable county "
                "connection established for this area in the private MVP."
            ),
            observed_value={
                "not_evaluated": True,
                "reason": "machine_access_terms_not_reviewed",
                "connector": ASSESSOR_NOT_EVALUATED_CONNECTOR_NAME,
            },
            source_id=source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=ASSESSOR_NOT_EVALUATED_METHOD_CODE,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=ASSESSOR_NOT_EVALUATED_CAVEAT,
            is_source_failure=True,
        )
        return AssessorNotEvaluatedConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
        )


__all__ = [
    "ASSESSOR_NOT_EVALUATED_CAVEAT",
    "ASSESSOR_NOT_EVALUATED_CONNECTOR_NAME",
    "ASSESSOR_NOT_EVALUATED_METHOD_CODE",
    "AssessorNotEvaluatedConnector",
    "AssessorNotEvaluatedConnectorResult",
]
