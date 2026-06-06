from __future__ import annotations

from pathlib import Path

import pytest

from app.connectors.access_fixture import (
    AccessFixtureConnectorResult,
    StaticAccessFixtureConnector,
)
from app.connectors.flood_fixture import FixtureConnectorError, FixtureConnectorProtocol
from app.domain.enums import EvidenceType
from app.domain.source_contracts import SourceRetrievalStatus

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


def test_access_connector_satisfies_fixture_connector_protocol() -> None:
    connector: FixtureConnectorProtocol = StaticAccessFixtureConnector()
    assert connector


def test_load_access_no_road_fixture_returns_succeeded_run() -> None:
    connector = StaticAccessFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "access_no_road.json")

    assert isinstance(result, AccessFixtureConnectorResult)
    assert result.retrieval_run.connector_name == "fixture_access_static"
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.domain == "access"
    assert evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence.observed_value.get("no_public_road_adjacency") is True


def test_load_access_road_fixture_returns_adjacency_evidence() -> None:
    connector = StaticAccessFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "access_road.json")

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    evidence = result.evidence_inputs[0]
    assert evidence.domain == "access"
    assert evidence.observed_value.get("public_road_adjacency") is True


def test_load_access_failure_fixture_returns_source_failure() -> None:
    connector = StaticAccessFixtureConnector()
    result = connector.load_fixture(FIXTURE_DIR / "access_failure.json")

    assert result.retrieval_run.status == SourceRetrievalStatus.BLOCKED
    evidence = result.evidence_inputs[0]
    assert evidence.domain == "access"
    assert evidence.is_source_failure is True
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.evidence_code == "ACCESS_SOURCE_UNAVAILABLE"


def test_access_connector_raises_on_remote_path() -> None:
    connector = StaticAccessFixtureConnector()

    with pytest.raises(FixtureConnectorError, match="local file paths"):
        connector.load_fixture("https://example.com/access.json")


def test_access_connector_raises_on_missing_file() -> None:
    connector = StaticAccessFixtureConnector()

    with pytest.raises(FixtureConnectorError, match="does not exist"):
        connector.load_fixture(FIXTURE_DIR / "does_not_exist.json")
