from __future__ import annotations

from pathlib import Path

from app.connectors.fixture_quality import (
    ConnectorFixtureQualityIssueCode,
    evaluate_zoning_fixture_quality,
)
from app.connectors.zoning_fixture import StaticZoningFixtureConnector

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


def test_zoning_allowed_fixture_passes_quality_check() -> None:
    connector = StaticZoningFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "zoning_allowed.json")
    profile = evaluate_zoning_fixture_quality(result)

    assert profile.passed
    assert profile.connector_name == "fixture_zoning_static"
    assert profile.evidence_count == 1
    assert profile.source_failure_count == 0
    assert profile.blocking_issue_count == 0


def test_zoning_prohibited_fixture_passes_quality_check() -> None:
    connector = StaticZoningFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "zoning_prohibited.json")
    profile = evaluate_zoning_fixture_quality(result)

    assert profile.passed
    assert profile.evidence_count == 1
    assert profile.source_failure_count == 0


def test_zoning_failure_fixture_passes_quality_check() -> None:
    connector = StaticZoningFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "zoning_failure.json")
    profile = evaluate_zoning_fixture_quality(result)

    assert profile.passed
    assert profile.evidence_count == 1
    assert profile.source_failure_count == 1


def test_wrong_connector_name_raises_blocking_issue() -> None:
    from datetime import UTC, datetime
    from uuid import UUID

    from app.connectors.zoning_fixture import ZoningFixtureConnectorResult
    from app.domain.source_contracts import SourceRetrievalRunContract, SourceRetrievalStatus

    bad_run = SourceRetrievalRunContract(
        connector_name="not_zoning_static",
        status=SourceRetrievalStatus.SUCCEEDED,
        row_count=0,
        error_count=0,
        warning_count=0,
        log_uri="fixture://connectors/zoning_allowed",
        metrics={"fixture_only": True},
        started_at=datetime(2026, 6, 4, 9, tzinfo=UTC),
        finished_at=datetime(2026, 6, 4, 9, 0, 1, tzinfo=UTC),
    )
    from app.domain.enums import ConfidenceBand, EvidenceType
    from app.domain.evidence_contracts import EvidenceContract

    good_evidence = EvidenceContract(
        area_id=UUID("44444444-4444-4444-8444-444444444444"),
        source_id=UUID("55555555-5555-4555-8555-555555555555"),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="ZONING_USE_CLASSIFICATION",
        domain="zoning",
        observation="test",
        observed_value={"intended_residential_use_allowed": True},
        method_code="fixture_zoning_test",
        method_version="0.1.0",
        confidence=ConfidenceBand.MEDIUM,
        caveat="test caveat",
        source_date="2026-06-04",
        observed_at=datetime(2026, 6, 4, 9, 0, 1, tzinfo=UTC),
    )
    result = ZoningFixtureConnectorResult(
        retrieval_run=bad_run,
        evidence_inputs=(good_evidence,),
    )
    profile = evaluate_zoning_fixture_quality(result)

    assert not profile.passed
    issue_codes = {issue.code for issue in profile.issues}
    assert ConnectorFixtureQualityIssueCode.RETRIEVAL_CONNECTOR_NAME_MISMATCH in issue_codes
