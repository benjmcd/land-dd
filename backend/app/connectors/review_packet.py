from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.domain.source_contracts import SourceRetrievalStatus

from .fixture_workflow import FixtureConnectorIngestWorkflowResult


class ConnectorReviewSignalCode(StrEnum):
    RETRIEVAL_NOT_SUCCEEDED = "retrieval_not_succeeded"
    RETRIEVAL_ERRORS_PRESENT = "retrieval_errors_present"
    RETRIEVAL_WARNINGS_PRESENT = "retrieval_warnings_present"
    SOURCE_FAILURE_EVIDENCE_PRESENT = "source_failure_evidence_present"
    IDEMPOTENT_SKIP_OBSERVED = "idempotent_skip_observed"
    NO_EVIDENCE_PERSISTED = "no_evidence_persisted"


@dataclass(frozen=True)
class ConnectorReviewSignal:
    code: ConnectorReviewSignalCode
    message: str
    requires_human_review: bool


@dataclass(frozen=True)
class ConnectorRunReviewPacket:
    connector_name: str
    ingest_run_id: UUID
    dataset_version_id: UUID | None
    retrieval_status: SourceRetrievalStatus
    started_at: datetime
    finished_at: datetime | None
    row_count: int | None
    error_count: int
    warning_count: int
    log_uri: str | None
    metrics: dict[str, object]
    retrieval_recorded: bool
    retrieval_skipped: bool
    evidence_input_count: int
    evidence_created_count: int
    evidence_skipped_count: int
    source_failure_created_count: int
    source_failure_skipped_count: int
    created_evidence_ids: tuple[UUID, ...]
    skipped_evidence_ids: tuple[UUID, ...]
    source_failure_evidence_ids: tuple[UUID, ...]
    review_required: bool
    signals: tuple[ConnectorReviewSignal, ...]
    human_review_tasks: tuple[str, ...]


def build_connector_run_review_packet(
    workflow_result: FixtureConnectorIngestWorkflowResult,
) -> ConnectorRunReviewPacket:
    retrieval_run = workflow_result.connector_result.retrieval_run
    created_evidence = workflow_result.evidence_ingestion.created_evidence
    skipped_evidence = workflow_result.evidence_ingestion.skipped_evidence
    source_failure_created = tuple(
        evidence for evidence in created_evidence if evidence.is_source_failure
    )
    source_failure_skipped = tuple(
        evidence for evidence in skipped_evidence if evidence.is_source_failure
    )
    signals = _review_signals(
        workflow_result=workflow_result,
        source_failure_created_count=len(source_failure_created),
        source_failure_skipped_count=len(source_failure_skipped),
    )
    return ConnectorRunReviewPacket(
        connector_name=retrieval_run.connector_name,
        ingest_run_id=retrieval_run.ingest_run_id,
        dataset_version_id=retrieval_run.dataset_version_id,
        retrieval_status=retrieval_run.status,
        started_at=retrieval_run.started_at,
        finished_at=retrieval_run.finished_at,
        row_count=retrieval_run.row_count,
        error_count=retrieval_run.error_count,
        warning_count=retrieval_run.warning_count,
        log_uri=retrieval_run.log_uri,
        metrics=dict(retrieval_run.metrics),
        retrieval_recorded=workflow_result.retrieval_provenance.recorded_run
        is not None,
        retrieval_skipped=workflow_result.retrieval_provenance.skipped_run is not None,
        evidence_input_count=len(workflow_result.connector_result.evidence_inputs),
        evidence_created_count=len(created_evidence),
        evidence_skipped_count=len(skipped_evidence),
        source_failure_created_count=len(source_failure_created),
        source_failure_skipped_count=len(source_failure_skipped),
        created_evidence_ids=tuple(
            evidence.evidence_id for evidence in created_evidence
        ),
        skipped_evidence_ids=tuple(
            evidence.evidence_id for evidence in skipped_evidence
        ),
        source_failure_evidence_ids=tuple(
            evidence.evidence_id
            for evidence in (*source_failure_created, *source_failure_skipped)
        ),
        review_required=any(signal.requires_human_review for signal in signals),
        signals=signals,
        human_review_tasks=_human_review_tasks(signals),
    )


def _review_signals(
    *,
    workflow_result: FixtureConnectorIngestWorkflowResult,
    source_failure_created_count: int,
    source_failure_skipped_count: int,
) -> tuple[ConnectorReviewSignal, ...]:
    retrieval_run = workflow_result.connector_result.retrieval_run
    created_count = len(workflow_result.evidence_ingestion.created_evidence)
    skipped_count = len(workflow_result.evidence_ingestion.skipped_evidence)
    signals: list[ConnectorReviewSignal] = []

    if retrieval_run.status != SourceRetrievalStatus.SUCCEEDED:
        signals.append(
            ConnectorReviewSignal(
                code=ConnectorReviewSignalCode.RETRIEVAL_NOT_SUCCEEDED,
                message="Connector retrieval did not finish with succeeded status.",
                requires_human_review=True,
            ),
        )
    if retrieval_run.error_count > 0:
        signals.append(
            ConnectorReviewSignal(
                code=ConnectorReviewSignalCode.RETRIEVAL_ERRORS_PRESENT,
                message="Connector retrieval reported one or more errors.",
                requires_human_review=True,
            ),
        )
    if retrieval_run.warning_count > 0:
        signals.append(
            ConnectorReviewSignal(
                code=ConnectorReviewSignalCode.RETRIEVAL_WARNINGS_PRESENT,
                message="Connector retrieval reported one or more warnings.",
                requires_human_review=True,
            ),
        )
    if source_failure_created_count + source_failure_skipped_count > 0:
        signals.append(
            ConnectorReviewSignal(
                code=ConnectorReviewSignalCode.SOURCE_FAILURE_EVIDENCE_PRESENT,
                message="Connector workflow produced source-failure evidence.",
                requires_human_review=True,
            ),
        )
    if workflow_result.retrieval_provenance.skipped_run is not None or skipped_count > 0:
        signals.append(
            ConnectorReviewSignal(
                code=ConnectorReviewSignalCode.IDEMPOTENT_SKIP_OBSERVED,
                message="Connector workflow skipped existing retrieval or evidence records.",
                requires_human_review=False,
            ),
        )
    if created_count == 0 and skipped_count == 0:
        signals.append(
            ConnectorReviewSignal(
                code=ConnectorReviewSignalCode.NO_EVIDENCE_PERSISTED,
                message="Connector workflow did not create or match persisted evidence.",
                requires_human_review=True,
            ),
        )

    return tuple(signals)


def _human_review_tasks(
    signals: tuple[ConnectorReviewSignal, ...],
) -> tuple[str, ...]:
    if any(signal.requires_human_review for signal in signals):
        return (
            "Review connector retrieval status, error counts, warnings, and log URI.",
            "Confirm source-failure evidence before downstream claim or report use.",
            "Verify fixture evidence counts against the connector source manifest.",
        )

    return (
        "Confirm connector provenance and evidence counts before promotion.",
        "Keep fixture-only connector evidence out of claims and reports until "
        "the next approved workflow gate.",
    )


__all__ = [
    "ConnectorReviewSignal",
    "ConnectorReviewSignalCode",
    "ConnectorRunReviewPacket",
    "build_connector_run_review_packet",
]
