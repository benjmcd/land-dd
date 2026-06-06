from __future__ import annotations

from pathlib import Path

import pytest

from app.connectors.flood_fixture import FixtureConnectorError, FixtureConnectorProtocol
from app.connectors.zoning_fixture import StaticZoningFixtureConnector, ZoningFixtureConnectorResult
from app.domain.enums import EvidenceType
from app.domain.source_contracts import SourceRetrievalStatus

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


def test_zoning_connector_satisfies_fixture_connector_protocol() -> None:
    connector: FixtureConnectorProtocol = StaticZoningFixtureConnector()
    assert connector


def test_load_zoning_allowed_fixture_returns_succeeded_run() -> None:
    connector = StaticZoningFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "zoning_allowed.json")

    assert isinstance(result, ZoningFixtureConnectorResult)
    assert result.retrieval_run.connector_name == "fixture_zoning_static"
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.domain == "zoning"
    assert evidence.is_source_failure is False
    assert evidence.observed_value.get("intended_residential_use_allowed") is True


def test_load_zoning_prohibited_fixture_returns_prohibited_evidence() -> None:
    connector = StaticZoningFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "zoning_prohibited.json")

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    evidence = result.evidence_inputs[0]
    assert evidence.domain == "zoning"
    assert evidence.observed_value.get("intended_residential_use_prohibited") is True


def test_load_zoning_failure_fixture_returns_source_failure() -> None:
    connector = StaticZoningFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "zoning_failure.json")

    assert result.retrieval_run.status == SourceRetrievalStatus.BLOCKED
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.domain == "zoning"
    assert evidence.is_source_failure is True
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.evidence_code == "ZONING_SOURCE_UNAVAILABLE"


def test_zoning_connector_raises_on_remote_path() -> None:
    connector = StaticZoningFixtureConnector()

    with pytest.raises(FixtureConnectorError, match="local file paths"):
        connector.load_fixture("https://example.com/zoning.json")


def test_zoning_connector_raises_on_missing_file() -> None:
    connector = StaticZoningFixtureConnector()

    with pytest.raises(FixtureConnectorError, match="does not exist"):
        connector.load_fixture(FIXTURE_DIR / "does_not_exist.json")
