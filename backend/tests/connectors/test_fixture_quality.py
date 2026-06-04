from __future__ import annotations

import inspect
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import app.connectors.fixture_quality as fixture_quality_module
from app.connectors import (
    ConnectorFixtureQualityIssueCode,
    FloodFixtureConnectorResult,
    StaticFloodFixtureConnector,
    evaluate_flood_fixture_quality,
)
from app.domain.enums import ConfidenceBand

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


def _load_success() -> FloodFixtureConnectorResult:
    return StaticFloodFixtureConnector().load_fixture(FIXTURE_DIR / "flood_success.json")


def _load_failure() -> FloodFixtureConnectorResult:
    return StaticFloodFixtureConnector().load_fixture(FIXTURE_DIR / "flood_failure.json")


def test_fixture_quality_accepts_success_fixture() -> None:
    profile = evaluate_flood_fixture_quality(_load_success())

    assert profile.passed is True
    assert profile.blocking_issue_count == 0
    assert profile.evidence_count == 1
    assert profile.source_failure_count == 0
    assert profile.issues == ()


def test_fixture_quality_accepts_source_failure_fixture() -> None:
    profile = evaluate_flood_fixture_quality(_load_failure())

    assert profile.passed is True
    assert profile.blocking_issue_count == 0
    assert profile.evidence_count == 1
    assert profile.source_failure_count == 1
    assert profile.issues == ()


def test_fixture_quality_flags_dataset_version_mismatch() -> None:
    result = _load_success()
    mismatched = result.evidence_inputs[0].model_copy(
        update={"dataset_version_id": UUID("99999999-9999-4999-8999-999999999999")},
    )

    profile = evaluate_flood_fixture_quality(
        FloodFixtureConnectorResult(
            retrieval_run=result.retrieval_run,
            evidence_inputs=(mismatched,),
        ),
    )

    assert profile.passed is False
    assert tuple(issue.code for issue in profile.issues) == (
        ConnectorFixtureQualityIssueCode.EVIDENCE_DATASET_VERSION_MISMATCH,
    )


def test_fixture_quality_flags_success_metric_and_geometry_gaps() -> None:
    result = _load_success()
    retrieval_run = result.retrieval_run.model_copy(
        update={"row_count": 2, "error_count": 1},
    )
    evidence = result.evidence_inputs[0].model_copy(
        update={"geometry_geojson": None, "spatial_precision_meters": None},
    )

    profile = evaluate_flood_fixture_quality(
        FloodFixtureConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
        ),
    )

    assert profile.passed is False
    assert tuple(issue.code for issue in profile.issues) == (
        ConnectorFixtureQualityIssueCode.SUCCEEDED_ROW_COUNT_MISMATCH,
        ConnectorFixtureQualityIssueCode.SUCCEEDED_ERROR_COUNT_NONZERO,
        ConnectorFixtureQualityIssueCode.SPATIAL_EVIDENCE_GEOMETRY_MISSING,
    )


def test_fixture_quality_flags_blocked_or_failed_metric_gaps() -> None:
    result = _load_failure()
    retrieval_run = result.retrieval_run.model_copy(
        update={"row_count": 1, "error_count": 0, "metrics": {"fixture_only": True}},
    )

    profile = evaluate_flood_fixture_quality(
        FloodFixtureConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=result.evidence_inputs,
        ),
    )

    assert profile.passed is False
    assert tuple(issue.code for issue in profile.issues) == (
        ConnectorFixtureQualityIssueCode.BLOCKED_OR_FAILED_ROW_COUNT_NOT_ZERO,
        ConnectorFixtureQualityIssueCode.BLOCKED_OR_FAILED_ERROR_COUNT_MISSING,
        ConnectorFixtureQualityIssueCode.RETRIEVAL_FAILURE_REASON_MISSING,
    )


def test_fixture_quality_flags_duplicate_evidence_ids() -> None:
    result = _load_success()
    retrieval_run = result.retrieval_run.model_copy(update={"row_count": 2})

    profile = evaluate_flood_fixture_quality(
        FloodFixtureConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(result.evidence_inputs[0], result.evidence_inputs[0]),
        ),
    )

    assert profile.passed is False
    assert tuple(issue.code for issue in profile.issues) == (
        ConnectorFixtureQualityIssueCode.DUPLICATE_EVIDENCE_ID,
    )


def test_fixture_quality_flags_evidence_observed_outside_retrieval_window() -> None:
    result = _load_success()
    before_retrieval = result.evidence_inputs[0].model_copy(
        update={
            "evidence_id": UUID("88888888-8888-4888-8888-888888888888"),
            "observed_at": datetime(2026, 6, 4, 8, 59, 59, tzinfo=UTC),
        },
    )
    after_retrieval = result.evidence_inputs[0].model_copy(
        update={
            "evidence_id": UUID("99999999-9999-4999-8999-999999999999"),
            "observed_at": datetime(2026, 6, 4, 9, 0, 2, tzinfo=UTC),
        },
    )
    retrieval_run = result.retrieval_run.model_copy(update={"row_count": 2})

    profile = evaluate_flood_fixture_quality(
        FloodFixtureConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(before_retrieval, after_retrieval),
        ),
    )

    assert profile.passed is False
    assert tuple(issue.code for issue in profile.issues) == (
        ConnectorFixtureQualityIssueCode.EVIDENCE_OBSERVED_BEFORE_RETRIEVAL,
        ConnectorFixtureQualityIssueCode.EVIDENCE_OBSERVED_AFTER_RETRIEVAL_FINISHED,
    )


def test_fixture_quality_flags_source_failure_payload_and_confidence_gaps() -> None:
    result = _load_failure()
    evidence = result.evidence_inputs[0].model_copy(
        update={
            "observed_value": {"failure_reason": "fixture_source_unavailable"},
            "confidence": ConfidenceBand.LOW,
        },
    )

    profile = evaluate_flood_fixture_quality(
        FloodFixtureConnectorResult(
            retrieval_run=result.retrieval_run,
            evidence_inputs=(evidence,),
        ),
    )

    assert profile.passed is False
    assert tuple(issue.code for issue in profile.issues) == (
        ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_PAYLOAD_INCOMPLETE,
        ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_CONFIDENCE_NOT_UNKNOWN,
    )


def test_fixture_quality_flags_source_failure_payload_type_gaps() -> None:
    result = _load_failure()
    evidence = result.evidence_inputs[0].model_copy(
        update={
            "observed_value": {
                "failure_reason": " ",
                "error_message": 503,
                "retryable": "false",
            },
        },
    )

    profile = evaluate_flood_fixture_quality(
        FloodFixtureConnectorResult(
            retrieval_run=result.retrieval_run,
            evidence_inputs=(evidence,),
        ),
    )

    assert profile.passed is False
    assert tuple(issue.code for issue in profile.issues) == (
        ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_PAYLOAD_INVALID,
    )


def test_fixture_quality_flags_source_failure_reason_mismatch() -> None:
    result = _load_failure()
    evidence = result.evidence_inputs[0].model_copy(
        update={
            "observed_value": {
                "failure_reason": "different_failure_reason",
                "error_message": "Fixture flood source unavailable.",
                "retryable": False,
            },
        },
    )

    profile = evaluate_flood_fixture_quality(
        FloodFixtureConnectorResult(
            retrieval_run=result.retrieval_run,
            evidence_inputs=(evidence,),
        ),
    )

    assert profile.passed is False
    assert tuple(issue.code for issue in profile.issues) == (
        ConnectorFixtureQualityIssueCode.SOURCE_FAILURE_REASON_MISMATCH,
    )


def test_fixture_quality_flags_evidence_provenance_text_gaps() -> None:
    result = _load_success()
    evidence = result.evidence_inputs[0].model_copy(
        update={
            "evidence_code": "",
            "observation": " ",
            "method_code": "",
            "method_version": "",
            "caveat": None,
            "source_date": None,
        },
    )

    profile = evaluate_flood_fixture_quality(
        FloodFixtureConnectorResult(
            retrieval_run=result.retrieval_run,
            evidence_inputs=(evidence,),
        ),
    )

    assert profile.passed is False
    assert tuple(issue.code for issue in profile.issues) == (
        ConnectorFixtureQualityIssueCode.EVIDENCE_PROVENANCE_TEXT_MISSING,
        ConnectorFixtureQualityIssueCode.EVIDENCE_CAVEAT_MISSING,
        ConnectorFixtureQualityIssueCode.SOURCE_OBSERVATION_SOURCE_DATE_MISSING,
    )


def test_fixture_quality_flags_nonlocal_log_and_missing_fixture_metric() -> None:
    result = _load_success()
    retrieval_run = result.retrieval_run.model_copy(
        update={"log_uri": "https://example.invalid/flood", "metrics": {}},
    )

    profile = evaluate_flood_fixture_quality(
        FloodFixtureConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=result.evidence_inputs,
        ),
    )

    assert profile.passed is False
    assert tuple(issue.code for issue in profile.issues) == (
        ConnectorFixtureQualityIssueCode.FIXTURE_LOG_URI_NOT_LOCAL,
        ConnectorFixtureQualityIssueCode.FIXTURE_METRIC_MISSING,
    )


def test_fixture_quality_stays_connector_owned_and_fixture_only() -> None:
    source = inspect.getsource(fixture_quality_module)

    assert "app.source_registry" not in source
    assert "app.evidence_ledger" not in source
    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "app.api" not in source
    assert "app.db" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
