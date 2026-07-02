from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalStatus

from .flood_fixture import FixtureConnectorResultProtocol


class ConnectorFixtureQualityIssueCode(StrEnum):
    RETRIEVAL_STATUS_UNSUPPORTED = "retrieval_status_unsupported"
    RETRIEVAL_FINISHED_BEFORE_STARTED = "retrieval_finished_before_started"
    RETRIEVAL_CONNECTOR_NAME_MISMATCH = "retrieval_connector_name_mismatch"
    RETRIEVAL_DATASET_VERSION_MISSING = "retrieval_dataset_version_missing"
    EVIDENCE_AREA_ID_MISMATCH = "evidence_area_id_mismatch"
    EVIDENCE_SOURCE_ID_MISMATCH = "evidence_source_id_mismatch"
    EVIDENCE_DOMAIN_MISMATCH = "evidence_domain_mismatch"
    EVIDENCE_DATASET_VERSION_MISMATCH = "evidence_dataset_version_mismatch"
    EVIDENCE_METHOD_CODE_MISMATCH = "evidence_method_code_mismatch"
    FIXTURE_LOG_URI_NOT_LOCAL = "fixture_log_uri_not_local"
    FIXTURE_METRIC_MISSING = "fixture_metric_missing"
    SUCCEEDED_ROW_COUNT_MISMATCH = "succeeded_row_count_mismatch"
    SUCCEEDED_ERROR_COUNT_NONZERO = "succeeded_error_count_nonzero"
    SUCCEEDED_HAS_FAILURE_REASON = "succeeded_has_failure_reason"
    SUCCEEDED_SPATIAL_EVIDENCE_MISSING = "succeeded_spatial_evidence_missing"
    BLOCKED_OR_FAILED_ROW_COUNT_NOT_ZERO = "blocked_or_failed_row_count_not_zero"
    BLOCKED_OR_FAILED_ERROR_COUNT_MISSING = "blocked_or_failed_error_count_missing"
    BLOCKED_OR_FAILED_SOURCE_FAILURE_MISSING = (
        "blocked_or_failed_source_failure_missing"
    )
    RETRIEVAL_FAILURE_REASON_MISSING = "retrieval_failure_reason_missing"
    SUCCEEDED_HAS_SOURCE_FAILURE = "succeeded_has_source_failure"
    BLOCKED_HAS_NON_FAILURE_EVIDENCE = "blocked_has_non_failure_evidence"
    SPATIAL_EVIDENCE_GEOMETRY_MISSING = "spatial_evidence_geometry_missing"
    SOURCE_FAILURE_GEOMETRY_PRESENT = "source_failure_geometry_present"
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
    SOURCE_FAILURE_PAYLOAD_INVALID = "source_failure_payload_invalid"
    SOURCE_FAILURE_TYPE_MISMATCH = "source_failure_type_mismatch"
    SOURCE_FAILURE_REASON_MISMATCH = "source_failure_reason_mismatch"
    SOURCE_FAILURE_CONFIDENCE_NOT_UNKNOWN = "source_failure_confidence_not_unknown"


_FLOOD_FIXTURE_DOMAIN = "flood"
_FLOOD_FIXTURE_CONNECTOR_NAME = "fixture_flood_static"
_FLOOD_FIXTURE_METHOD_PREFIX = "fixture_flood_"

_ACCESS_FIXTURE_DOMAIN = "access"
_ACCESS_FIXTURE_CONNECTOR_NAME = "fixture_access_static"
_ACCESS_FIXTURE_METHOD_PREFIX = "fixture_access_"

_ZONING_FIXTURE_DOMAIN = "zoning"
_ZONING_FIXTURE_CONNECTOR_NAME = "fixture_zoning_static"
_ZONING_FIXTURE_METHOD_PREFIX = "fixture_zoning_"

_BUILDABILITY_FIXTURE_DOMAIN = "buildability"
_BUILDABILITY_FIXTURE_CONNECTOR_NAME = "fixture_buildability_static"
_BUILDABILITY_FIXTURE_METHOD_PREFIX = "fixture_buildability_"

_TERRAIN_FIXTURE_DOMAIN = "terrain"
_TERRAIN_FIXTURE_CONNECTOR_NAME = "fixture_terrain_static"
_TERRAIN_FIXTURE_METHOD_PREFIX = "fixture_terrain_"

_WETLANDS_FIXTURE_DOMAIN = "wetlands"
_WETLANDS_FIXTURE_CONNECTOR_NAME = "fixture_wetlands_static"
_WETLANDS_FIXTURE_METHOD_PREFIX = "fixture_wetlands_"

_SOILS_FIXTURE_DOMAIN = "soils"
_SOILS_FIXTURE_CONNECTOR_NAME = "fixture_soils_static"
_SOILS_FIXTURE_METHOD_PREFIX = "fixture_soils_"

_PARCEL_FIXTURE_DOMAIN = "parcels"
_PARCEL_FIXTURE_CONNECTOR_NAME = "fixture_parcel_static"
_PARCEL_FIXTURE_METHOD_PREFIX = "fixture_parcel_"

_MINERALS_FIXTURE_DOMAIN = "minerals"
_MINERALS_FIXTURE_CONNECTOR_NAME = "fixture_minerals_static"
_MINERALS_FIXTURE_METHOD_PREFIX = "fixture_minerals_"

_BROADBAND_FIXTURE_DOMAIN = "broadband"
_BROADBAND_FIXTURE_CONNECTOR_NAME = "fixture_broadband_static"
_BROADBAND_FIXTURE_METHOD_PREFIX = "fixture_broadband_"

_ENV_HAZARD_FIXTURE_DOMAIN = "env_hazard"
_ENV_HAZARD_FIXTURE_CONNECTOR_NAME = "fixture_env_hazard_static"
_ENV_HAZARD_FIXTURE_METHOD_PREFIX = "fixture_env_hazard_"


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
    connector_result: FixtureConnectorResultProtocol,
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
    if retrieval_run.connector_name != _FLOOD_FIXTURE_CONNECTOR_NAME:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.RETRIEVAL_CONNECTOR_NAME_MISMATCH,
                "flood fixture retrieval connector_name must be fixture_flood_static",
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
    _append_retrieval_status_issue(issues, retrieval_run.status)

    if (
        retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
        and retrieval_run.row_count != non_failure_count
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SUCCEEDED_ROW_COUNT_MISMATCH,
                "succeeded fixture row_count must match non-failure evidence count",
            ),
        )
    if (
        retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
        and retrieval_run.error_count != 0
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SUCCEEDED_ERROR_COUNT_NONZERO,
                "succeeded fixture error_count must be zero",
            ),
        )
    if (
        retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
        and _non_empty_text(retrieval_run.metrics.get("failure_reason"))
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SUCCEEDED_HAS_FAILURE_REASON,
                "succeeded fixture must not record a failure reason metric",
            ),
        )
    if retrieval_run.status == SourceRetrievalStatus.SUCCEEDED and source_failure_count:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SUCCEEDED_HAS_SOURCE_FAILURE,
                "succeeded fixture must not emit source-failure evidence",
            ),
        )
    if (
        retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
        and not _has_spatial_evidence(evidence_inputs)
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SUCCEEDED_SPATIAL_EVIDENCE_MISSING,
                "succeeded flood fixture must emit spatial intersection evidence",
            ),
        )
    if retrieval_run.status in {
        SourceRetrievalStatus.BLOCKED,
        SourceRetrievalStatus.FAILED,
    }:
        if retrieval_run.row_count != 0:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.BLOCKED_OR_FAILED_ROW_COUNT_NOT_ZERO,
                    "blocked or failed fixture row_count must be zero",
                ),
            )
        if retrieval_run.error_count <= 0:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.BLOCKED_OR_FAILED_ERROR_COUNT_MISSING,
                    "blocked or failed fixture must record at least one error",
                ),
            )
        if not _non_empty_text(retrieval_run.metrics.get("failure_reason")):
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.RETRIEVAL_FAILURE_REASON_MISSING,
                    "blocked or failed fixture must record a failure reason metric",
                ),
            )
        if non_failure_count:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.BLOCKED_HAS_NON_FAILURE_EVIDENCE,
                    "blocked or failed fixture must not emit non-failure evidence",
                ),
            )
        if source_failure_count == 0:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.BLOCKED_OR_FAILED_SOURCE_FAILURE_MISSING,
                    "blocked or failed fixture must emit source-failure evidence",
                ),
            )

    evidence_ids = set()
    area_ids = {evidence.area_id for evidence in evidence_inputs}
    if len(area_ids) > 1:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.EVIDENCE_AREA_ID_MISMATCH,
                "fixture evidence area_id values must match within one run",
            ),
        )
    source_ids = {evidence.source_id for evidence in evidence_inputs}
    if len(source_ids) > 1:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.EVIDENCE_SOURCE_ID_MISMATCH,
                "fixture evidence source_id values must match within one run",
            ),
        )
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
        if evidence.is_source_failure != (
            evidence.evidence_type == EvidenceType.SOURCE_FAILURE
        ):
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_TYPE_MISMATCH,
                    "source-failure flag must match source-failure evidence type",
                ),
            )
        if evidence.domain != _FLOOD_FIXTURE_DOMAIN:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.EVIDENCE_DOMAIN_MISMATCH,
                    "flood fixture evidence domain must be flood",
                ),
            )
        if evidence.method_code.strip() and not evidence.method_code.startswith(
            _FLOOD_FIXTURE_METHOD_PREFIX,
        ):
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.EVIDENCE_METHOD_CODE_MISMATCH,
                    "flood fixture evidence method_code must use fixture_flood prefix",
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
            if (
                evidence.geometry_geojson is not None
                or evidence.spatial_precision_meters is not None
            ):
                issues.append(
                    _issue(
                        ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_GEOMETRY_PRESENT,
                        "source-failure fixture evidence must not include geometry",
                    ),
                )
            _append_source_failure_issues(
                issues,
                evidence,
                retrieval_failure_reason=retrieval_run.metrics.get("failure_reason"),
            )

    return ConnectorFixtureQualityProfile(
        connector_name=retrieval_run.connector_name,
        evidence_count=len(evidence_inputs),
        source_failure_count=source_failure_count,
        issues=tuple(issues),
    )


def evaluate_access_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
) -> ConnectorFixtureQualityProfile:
    return _evaluate_fixture_quality(
        connector_result,
        connector_name=_ACCESS_FIXTURE_CONNECTOR_NAME,
        domain=_ACCESS_FIXTURE_DOMAIN,
        method_prefix=_ACCESS_FIXTURE_METHOD_PREFIX,
        label="access",
        require_spatial_geometry=True,
    )


def evaluate_zoning_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
) -> ConnectorFixtureQualityProfile:
    return _evaluate_fixture_quality(
        connector_result,
        connector_name=_ZONING_FIXTURE_CONNECTOR_NAME,
        domain=_ZONING_FIXTURE_DOMAIN,
        method_prefix=_ZONING_FIXTURE_METHOD_PREFIX,
        label="zoning",
        require_spatial_geometry=False,
    )


def _evaluate_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
    *,
    connector_name: str,
    domain: str,
    method_prefix: str,
    label: str,
    require_spatial_geometry: bool,
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
    if retrieval_run.connector_name != connector_name:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.RETRIEVAL_CONNECTOR_NAME_MISMATCH,
                f"{label} fixture retrieval connector_name must be {connector_name}",
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
    _append_retrieval_status_issue(issues, retrieval_run.status)

    if (
        retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
        and retrieval_run.row_count != non_failure_count
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SUCCEEDED_ROW_COUNT_MISMATCH,
                "succeeded fixture row_count must match non-failure evidence count",
            ),
        )
    if (
        retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
        and retrieval_run.error_count != 0
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SUCCEEDED_ERROR_COUNT_NONZERO,
                "succeeded fixture error_count must be zero",
            ),
        )
    if (
        retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
        and _non_empty_text(retrieval_run.metrics.get("failure_reason"))
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SUCCEEDED_HAS_FAILURE_REASON,
                "succeeded fixture must not record a failure reason metric",
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
    }:
        if retrieval_run.row_count != 0:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.BLOCKED_OR_FAILED_ROW_COUNT_NOT_ZERO,
                    "blocked or failed fixture row_count must be zero",
                ),
            )
        if retrieval_run.error_count <= 0:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.BLOCKED_OR_FAILED_ERROR_COUNT_MISSING,
                    "blocked or failed fixture must record at least one error",
                ),
            )
        if not _non_empty_text(retrieval_run.metrics.get("failure_reason")):
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.RETRIEVAL_FAILURE_REASON_MISSING,
                    "blocked or failed fixture must record a failure reason metric",
                ),
            )
        if non_failure_count:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.BLOCKED_HAS_NON_FAILURE_EVIDENCE,
                    "blocked or failed fixture must not emit non-failure evidence",
                ),
            )
        if source_failure_count == 0:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.BLOCKED_OR_FAILED_SOURCE_FAILURE_MISSING,
                    "blocked or failed fixture must emit source-failure evidence",
                ),
            )

    evidence_ids: set[object] = set()
    area_ids = {evidence.area_id for evidence in evidence_inputs}
    if len(area_ids) > 1:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.EVIDENCE_AREA_ID_MISMATCH,
                "fixture evidence area_id values must match within one run",
            ),
        )
    source_ids = {evidence.source_id for evidence in evidence_inputs}
    if len(source_ids) > 1:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.EVIDENCE_SOURCE_ID_MISMATCH,
                "fixture evidence source_id values must match within one run",
            ),
        )

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
        if evidence.is_source_failure != (
            evidence.evidence_type == EvidenceType.SOURCE_FAILURE
        ):
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_TYPE_MISMATCH,
                    "source-failure flag must match source-failure evidence type",
                ),
            )
        if evidence.domain != domain:
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.EVIDENCE_DOMAIN_MISMATCH,
                    f"{label} fixture evidence domain must be {domain}",
                ),
            )
        if evidence.method_code.strip() and not evidence.method_code.startswith(
            method_prefix,
        ):
            issues.append(
                _issue(
                    ConnectorFixtureQualityIssueCode.EVIDENCE_METHOD_CODE_MISMATCH,
                    f"{label} fixture evidence method_code must use {method_prefix} prefix",
                ),
            )
        _append_evidence_provenance_issues(issues, evidence)
        if (
            require_spatial_geometry
            and evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
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
            if (
                evidence.geometry_geojson is not None
                or evidence.spatial_precision_meters is not None
            ):
                issues.append(
                    _issue(
                        ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_GEOMETRY_PRESENT,
                        "source-failure fixture evidence must not include geometry",
                    ),
                )
            _append_source_failure_issues(
                issues,
                evidence,
                retrieval_failure_reason=retrieval_run.metrics.get("failure_reason"),
            )

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
    *,
    retrieval_failure_reason: object,
) -> None:
    required_keys = {"failure_reason", "error_message", "retryable"}
    if not required_keys.issubset(evidence.observed_value):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_PAYLOAD_INCOMPLETE,
                "source-failure fixture evidence must include controlled failure keys",
            ),
        )
    elif (
        not _non_empty_text(evidence.observed_value["failure_reason"])
        or not _non_empty_text(evidence.observed_value["error_message"])
        or not isinstance(evidence.observed_value["retryable"], bool)
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_PAYLOAD_INVALID,
                "source-failure fixture payload values must be typed and non-empty",
            ),
        )
    else:
        _append_source_failure_reason_consistency_issue(
            issues,
            evidence,
            retrieval_failure_reason=retrieval_failure_reason,
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


def _append_retrieval_status_issue(
    issues: list[ConnectorFixtureQualityIssue],
    status: SourceRetrievalStatus,
) -> None:
    if status not in {
        SourceRetrievalStatus.SUCCEEDED,
        SourceRetrievalStatus.BLOCKED,
        SourceRetrievalStatus.FAILED,
    }:
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.RETRIEVAL_STATUS_UNSUPPORTED,
                "fixture quality only supports terminal succeeded, blocked, or failed retrievals",
            ),
        )


def _has_spatial_evidence(evidence_inputs: tuple[EvidenceContract, ...]) -> bool:
    return any(
        evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
        and not evidence.is_source_failure
        for evidence in evidence_inputs
    )


def _append_source_failure_reason_consistency_issue(
    issues: list[ConnectorFixtureQualityIssue],
    evidence: EvidenceContract,
    *,
    retrieval_failure_reason: object,
) -> None:
    if not isinstance(retrieval_failure_reason, str):
        return
    cleaned_retrieval_reason = retrieval_failure_reason.strip()
    if not cleaned_retrieval_reason:
        return
    payload_reason = evidence.observed_value["failure_reason"]
    if (
        isinstance(payload_reason, str)
        and payload_reason.strip() != cleaned_retrieval_reason
    ):
        issues.append(
            _issue(
                ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_REASON_MISMATCH,
                "source-failure reason must match retrieval failure metric",
            ),
        )


def _non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def evaluate_buildability_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
) -> ConnectorFixtureQualityProfile:
    return _evaluate_fixture_quality(
        connector_result,
        connector_name=_BUILDABILITY_FIXTURE_CONNECTOR_NAME,
        domain=_BUILDABILITY_FIXTURE_DOMAIN,
        method_prefix=_BUILDABILITY_FIXTURE_METHOD_PREFIX,
        label="buildability",
        require_spatial_geometry=False,
    )


def evaluate_terrain_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
) -> ConnectorFixtureQualityProfile:
    return _evaluate_fixture_quality(
        connector_result,
        connector_name=_TERRAIN_FIXTURE_CONNECTOR_NAME,
        domain=_TERRAIN_FIXTURE_DOMAIN,
        method_prefix=_TERRAIN_FIXTURE_METHOD_PREFIX,
        label="terrain",
        require_spatial_geometry=False,
    )


def evaluate_wetlands_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
) -> ConnectorFixtureQualityProfile:
    return _evaluate_fixture_quality(
        connector_result,
        connector_name=_WETLANDS_FIXTURE_CONNECTOR_NAME,
        domain=_WETLANDS_FIXTURE_DOMAIN,
        method_prefix=_WETLANDS_FIXTURE_METHOD_PREFIX,
        label="wetlands",
        require_spatial_geometry=True,
    )


def evaluate_soils_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
) -> ConnectorFixtureQualityProfile:
    return _evaluate_fixture_quality(
        connector_result,
        connector_name=_SOILS_FIXTURE_CONNECTOR_NAME,
        domain=_SOILS_FIXTURE_DOMAIN,
        method_prefix=_SOILS_FIXTURE_METHOD_PREFIX,
        label="soils",
        require_spatial_geometry=True,
    )


def evaluate_parcel_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
) -> ConnectorFixtureQualityProfile:
    return _evaluate_fixture_quality(
        connector_result,
        connector_name=_PARCEL_FIXTURE_CONNECTOR_NAME,
        domain=_PARCEL_FIXTURE_DOMAIN,
        method_prefix=_PARCEL_FIXTURE_METHOD_PREFIX,
        label="parcel",
        require_spatial_geometry=True,
    )


def evaluate_minerals_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
) -> ConnectorFixtureQualityProfile:
    return _evaluate_fixture_quality(
        connector_result,
        connector_name=_MINERALS_FIXTURE_CONNECTOR_NAME,
        domain=_MINERALS_FIXTURE_DOMAIN,
        method_prefix=_MINERALS_FIXTURE_METHOD_PREFIX,
        label="minerals",
        require_spatial_geometry=False,
    )


def evaluate_broadband_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
) -> ConnectorFixtureQualityProfile:
    return _evaluate_fixture_quality(
        connector_result,
        connector_name=_BROADBAND_FIXTURE_CONNECTOR_NAME,
        domain=_BROADBAND_FIXTURE_DOMAIN,
        method_prefix=_BROADBAND_FIXTURE_METHOD_PREFIX,
        label="broadband",
        require_spatial_geometry=False,
    )


def evaluate_env_hazard_fixture_quality(
    connector_result: FixtureConnectorResultProtocol,
) -> ConnectorFixtureQualityProfile:
    return _evaluate_fixture_quality(
        connector_result,
        connector_name=_ENV_HAZARD_FIXTURE_CONNECTOR_NAME,
        domain=_ENV_HAZARD_FIXTURE_DOMAIN,
        method_prefix=_ENV_HAZARD_FIXTURE_METHOD_PREFIX,
        label="env-hazard",
        require_spatial_geometry=False,
    )


__all__ = [
    "ConnectorFixtureQualityIssue",
    "ConnectorFixtureQualityIssueCode",
    "ConnectorFixtureQualityProfile",
    "evaluate_access_fixture_quality",
    "evaluate_broadband_fixture_quality",
    "evaluate_buildability_fixture_quality",
    "evaluate_env_hazard_fixture_quality",
    "evaluate_flood_fixture_quality",
    "evaluate_minerals_fixture_quality",
    "evaluate_parcel_fixture_quality",
    "evaluate_soils_fixture_quality",
    "evaluate_terrain_fixture_quality",
    "evaluate_wetlands_fixture_quality",
    "evaluate_zoning_fixture_quality",
]
