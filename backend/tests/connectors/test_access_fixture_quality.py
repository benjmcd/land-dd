from __future__ import annotations

from pathlib import Path

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
