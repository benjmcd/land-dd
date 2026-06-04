from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalStatus

from .flood_fixture import FloodFixtureConnectorResult


class ConnectorFixtureQualityIssueCode(StrEnum):
    RETRIEVAL_FINISHED_BEFORE_STARTED = "retrieval_finished_before_started"
    RETRIEVAL_DATASET_VERSION_MISSING = "retrieval_dataset_version_missing"
    EVIDENCE_DATASET_VERSION_MISMATCH = "evidence_dataset_version_mismatch"
    FIXTURE_LOG_URI_NOT_LOCAL = "fixture_log_uri_not_local"
    FIXTURE_METRIC_MISSING = "fixture_metric_missing"
    SUCCEEDED_ROW_COUNT_MISMATCH = "succeeded_row_count_mismatch"
    SUCCEEDED_HAS_SOURCE_FAILURE = "succeeded_has_source_failure"
    BLOCKED_HAS_NON_FAILURE_EVIDENCE = "blocked_has_non_failure_evidence"
    SPATIAL_EVIDENCE_GEOMETRY_MISSING = "spatial_evidence_geometry_missing"
    DUPLICATE_EVIDENCE_ID = "duplicate_evidence_id"
    EVIDENCE_OBSERVED_BEFORE_RETRIEVAL = "evidence_observed_before_retrieval"
    EVIDENCE_OBSERVED_AFTER_RETRIEVAL_FINISHED = (
        "evidence_observed_after_retrieval_finished"
    )
    EVIDENCE_PROVENANCE_TEXT_MISSING = "evidence_provenance_text_missing"
    EVIDENCE_CAVEAT_MISSING = "evidence_caveat_missing"
    SOURCE_OBSERVATION_SOURCE_DATE_MISSING = (
        "source_observation_source_date_missing"
    )
    SOURCE_FAILURE_PAYLOAD_INCOMPLETE = "source_failure_payload_incomplete"
    SOURCE_FAILURE_CONFIDENCE_NOT_UNKNOWN = "source_failure_confidence_not_unknown"


@dataclass(frozen=True)
class ConnectorFixtureQualityIssue:
    code: ConnectorFixtureQualityIssueCode
    message: str
    blocking: bool = True


@dataclass(frozen=True)
class ConnectorFixtureQualityProfile:
    connector_name: str
    evidence_count: int
    source_failure_count: int
    issues: tuple[ConnectorFixtureQualityIssue, ...]

    @property
    def passed(self) -> bool:
        return not any(issue.blocking for issue in self.issues)

    @property
    def blocking_issue_count(self) -> int:
        return sum(1 for issue in self.issues if issue.blocking)


def evaluate_flood_fixture_quality(
    connector_result: FloodFixtureConnectorResult,
) -> ConnectorFixtureQualityProfile:
    retrieval_run = connector_result.retrieval_run
    evidence_inputs = connector_result.evidence_inputs
    issues: list[ConnectorFixtureQualityIssue] = []

    if (
        retrieval_run.finished_at is not None
        and retrieval_run.finished_at < retrieval_run.started_at
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.RETRIEVAL_FINISHED_BEFORE_STARTED,
                "fixture retrieval finished before it started",
            ),
        )
    if retrieval_run.dataset_version_id is None:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.RETRIEVAL_DATASET_VERSION_MISSING,
                "fixture retrieval must identify a dataset version",
            ),
        )
    if retrieval_run.log_uri is None or not retrieval_run.log_uri.startswith(
        "fixture://",
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.FIXTURE_LOG_URI_NOT_LOCAL,
                "fixture retrieval log_uri must use the fixture:// scheme",
            ),
        )
    if retrieval_run.metrics.get("fixture_only") is not True:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.FIXTURE_METRIC_MISSING,
                "fixture retrieval metrics must mark fixture_only as true",
            ),
        )

    non_failure_count = sum(
        1 for evidence in evidence_inputs if not evidence.is_source_failure
    )
    source_failure_count = len(evidence_inputs) - non_failure_count

    if (
        retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
        and retrieval_run.row_count is not None
        and retrieval_run.row_count != non_failure_count
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SUCCEEDED_ROW_COUNT_MISMATCH,
                "succeeded fixture row_count must match non-failure evidence count",
            ),
        )
    if retrieval_run.status == SourceRetrievalStatus.SUCCEEDED and source_failure_count:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SUCCEEDED_HAS_SOURCE_FAILURE,
                "succeeded fixture must not emit source-failure evidence",
            ),
        )
    if retrieval_run.status in {
        SourceRetrievalStatus.BLOCKED,
        SourceRetrievalStatus.FAILED,
    } and non_failure_count:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.BLOCKED_HAS_NON_FAILURE_EVIDENCE,
                "blocked or failed fixture must not emit non-failure evidence",
            ),
        )

    evidence_ids = set()
    for evidence in evidence_inputs:
        if evidence.evidence_id in evidence_ids:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.DUPLICATE_EVIDENCE_ID,
                    "fixture evidence IDs must be unique within one connector run",
                ),
            )
        evidence_ids.add(evidence.evidence_id)

        if evidence.observed_at < retrieval_run.started_at:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.EVIDENCE_OBSERVED_BEFORE_RETRIEVAL,
                    "fixture evidence observed_at must not precede retrieval start",
                ),
            )
        if (
            retrieval_run.finished_at is not None
            and evidence.observed_at > retrieval_run.finished_at
        ):
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.EVIDENCE_OBSERVED_AFTER_RETRIEVAL_FINISHED,
                    "fixture evidence observed_at must not follow retrieval finish",
                ),
            )

        if (
            retrieval_run.dataset_version_id is not None
            and evidence.dataset_version_id != retrieval_run.dataset_version_id
        ):
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.EVIDENCE_DATASET_VERSION_MISMATCH,
                    "fixture evidence dataset_version_id must match retrieval run",
                ),
            )
        _append_evidence_provenance_issues(issues, evidence)
        if (
            evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
            and not evidence.is_source_failure
            and (
                evidence.geometry_geojson is None
                or evidence.spatial_precision_meters is None
            )
        ):
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.SPATIAL_EVIDENCE_GEOMETRY_MISSING,
                    "spatial fixture evidence must include geometry and precision",
                ),
            )
        if evidence.is_source_failure:
            _append_source_failure_issues(issues, evidence)

    return ConnectorFixtureQualityProfile(
        connector_name=retrieval_run.connector_name,
        evidence_count=len(evidence_inputs),
        source_failure_count=source_failure_count,
        issues=tuple(issues),
    )


def _append_evidence_provenance_issues(
    issues: list[ConnectorFixtureQualityIssue],
    evidence: EvidenceContract,
) -> None:
    required_text = (
        evidence.evidence_code,
        evidence.observation,
        evidence.method_code,
        evidence.method_version,
    )
    if any(not value.strip() for value in required_text):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.EVIDENCE_PROVENANCE_TEXT_MISSING,
                "fixture evidence must include code, observation, method, and version",
            ),
        )
    if evidence.caveat is None or not evidence.caveat.strip():
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.EVIDENCE_CAVEAT_MISSING,
                "fixture evidence must include a caveat",
            ),
        )
    if not evidence.is_source_failure and (
        evidence.source_date is None or not evidence.source_date.strip()
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SOURCE_OBSERVATION_SOURCE_DATE_MISSING,
                "non-failure fixture evidence must include source_date",
            ),
        )


def _append_source_failure_issues(
    issues: list[ConnectorFixtureQualityIssue],
    evidence: EvidenceContract,
) -> None:
    required_keys = {"failure_reason", "error_message", "retryable"}
    if not required_keys.issubset(evidence.observed_value):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_PAYLOAD_INCOMPLETE,
                "source-failure fixture evidence must include controlled failure keys",
            ),
        )
    if evidence.confidence != ConfidenceBand.UNKNOWN:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_CONFIDENCE_NOT_UNKNOWN,
                "source-failure fixture evidence must use unknown confidence",
            ),
        )


def _issue(
    code: ConnectorFixtureQualityIssueCode,
    message: str,
) -> ConnectorFixtureQualityIssue:
    return ConnectorFixtureQualityIssue(code=code, message=message)


__all__ = [
    "ConnectorFixtureQualityIssue",
    "ConnectorFixtureQualityIssueCode",
    "ConnectorFixtureQualityProfile",
    "evaluate_flood_fixture_quality",
]
