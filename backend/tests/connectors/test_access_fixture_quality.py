from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from app.connectors.access_fixture import StaticAccessFixtureConnector
from app.connectors.fixture_quality import (
    ConnectorFixtureQualityIssueCode,
    evaluate_access_fixture_quality,
)

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


def test_access_no_road_fixture_passes_quality_check() -> None:
    connector = StaticAccessFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "access_no_road.json")
    profile = evaluate_access_fixture_quality(result)

    assert profile.passed
    assert profile.connector_name == "fixture_access_static"
    assert profile.evidence_count == 1
    assert profile.source_failure_count == 0
    assert profile.blocking_issue_count == 0


def test_access_road_fixture_passes_quality_check() -> None:
    connector = StaticAccessFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "access_road.json")
    profile = evaluate_access_fixture_quality(result)

    assert profile.passed
    assert profile.evidence_count == 1
    assert profile.source_failure_count == 0


def test_access_failure_fixture_passes_quality_check() -> None:
    connector = StaticAccessFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "access_failure.json")
    profile = evaluate_access_fixture_quality(result)

    assert profile.passed
    assert profile.evidence_count == 1
    assert profile.source_failure_count == 1


def test_access_wrong_connector_name_raises_blocking_issue() -> None:
    result = StaticAccessFixtureConnector().load_fixture(
        FIXTURE_DIR / "access_no_road.json",
    )
    bad_run = result.retrieval_run.model_copy(
        update={"connector_name": "not_access_static"}
    )
    profile = evaluate_access_fixture_quality(
        type(result)(retrieval_run=bad_run, evidence_inputs=result.evidence_inputs)
    )

    assert not profile.passed
    issue_codes = {issue.code for issue in profile.issues}
    assert ConnectorFixtureQualityIssueCode.RETRIEVAL_CONNECTOR_NAME_MISMATCH in issue_codes


def test_access_succeeded_with_failure_reason_raises_blocking_issue() -> None:
    result = StaticAccessFixtureConnector().load_fixture(
        FIXTURE_DIR / "access_no_road.json",
    )
    bad_run = result.retrieval_run.model_copy(
        update={"metrics": {**result.retrieval_run.metrics, "failure_reason": "x"}}
    )
    profile = evaluate_access_fixture_quality(
        type(result)(retrieval_run=bad_run, evidence_inputs=result.evidence_inputs)
    )

    assert not profile.passed
    issue_codes = {issue.code for issue in profile.issues}
    assert ConnectorFixtureQualityIssueCode.SUCCEEDED_HAS_FAILURE_REASON in issue_codes


def test_access_evidence_area_id_mismatch_raises_blocking_issue() -> None:
    result = StaticAccessFixtureConnector().load_fixture(
        FIXTURE_DIR / "access_no_road.json",
    )
    original_evidence = result.evidence_inputs[0]
    second_evidence = original_evidence.model_copy(
        update={"area_id": uuid4(), "evidence_id": uuid4()}
    )
    profile = evaluate_access_fixture_quality(
        type(result)(
            retrieval_run=result.retrieval_run,
            evidence_inputs=(original_evidence, second_evidence),
        )
    )

    assert not profile.passed
    issue_codes = {issue.code for issue in profile.issues}
    assert ConnectorFixtureQualityIssueCode.EVIDENCE_AREA_ID_MISMATCH in issue_codes


def test_access_evidence_source_id_mismatch_raises_blocking_issue() -> None:
    result = StaticAccessFixtureConnector().load_fixture(
        FIXTURE_DIR / "access_no_road.json",
    )
    original_evidence = result.evidence_inputs[0]
    second_evidence = original_evidence.model_copy(
        update={"source_id": uuid4(), "evidence_id": uuid4()}
    )
    profile = evaluate_access_fixture_quality(
        type(result)(
            retrieval_run=result.retrieval_run,
            evidence_inputs=(original_evidence, second_evidence),
        )
    )

    assert not profile.passed
    issue_codes = {issue.code for issue in profile.issues}
    assert ConnectorFixtureQualityIssueCode.EVIDENCE_SOURCE_ID_MISMATCH in issue_codes


def test_access_evidence_observed_before_retrieval_raises_blocking_issue() -> None:
    result = StaticAccessFixtureConnector().load_fixture(
        FIXTURE_DIR / "access_no_road.json",
    )
    early_observed_at = result.retrieval_run.started_at - timedelta(seconds=1)
    bad_evidence = result.evidence_inputs[0].model_copy(
        update={"observed_at": early_observed_at}
    )
    profile = evaluate_access_fixture_quality(
        type(result)(
            retrieval_run=result.retrieval_run,
            evidence_inputs=(bad_evidence,),
        )
    )

    assert not profile.passed
    issue_codes = {issue.code for issue in profile.issues}
    assert ConnectorFixtureQualityIssueCode.EVIDENCE_OBSERVED_BEFORE_RETRIEVAL in issue_codes


def test_access_evidence_observed_after_retrieval_finished_raises_blocking_issue() -> None:
    result = StaticAccessFixtureConnector().load_fixture(
        FIXTURE_DIR / "access_no_road.json",
    )
    assert result.retrieval_run.finished_at is not None
    late_observed_at = result.retrieval_run.finished_at + timedelta(seconds=1)
    bad_evidence = result.evidence_inputs[0].model_copy(
        update={"observed_at": late_observed_at}
    )
    profile = evaluate_access_fixture_quality(
        type(result)(
            retrieval_run=result.retrieval_run,
            evidence_inputs=(bad_evidence,),
        )
    )

    assert not profile.passed
    issue_codes = {issue.code for issue in profile.issues}
    assert (
        ConnectorFixtureQualityIssueCode.EVIDENCE_OBSERVED_AFTER_RETRIEVAL_FINISHED
        in issue_codes
    )
