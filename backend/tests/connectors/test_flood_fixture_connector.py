from __future__ import annotations

import inspect
from pathlib import Path

import pytest

import app.connectors.flood_fixture as flood_fixture_module
from app.connectors import FixtureConnectorError, StaticFloodFixtureConnector
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceRetrievalStatus

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


def test_success_fixture_emits_retrieval_run_and_flood_evidence_inputs() -> None:
    result = StaticFloodFixtureConnector().load_fixture(
        FIXTURE_DIR / "flood_success.json",
    )

    assert result.retrieval_run.connector_name == "fixture_flood_static"
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.dataset_version_id is not None
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.metrics["fixture_only"] is True

    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence.domain == "flood"
    assert evidence.dataset_version_id == result.retrieval_run.dataset_version_id
    assert evidence.observed_value["flood_zone_code"] == "AE"
    assert evidence.is_source_failure is False
    assert evidence.confidence == ConfidenceBand.MEDIUM


def test_failure_fixture_emits_blocked_retrieval_and_source_failure_input() -> None:
    result = StaticFloodFixtureConnector().load_fixture(
        FIXTURE_DIR / "flood_failure.json",
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.BLOCKED
    assert result.retrieval_run.error_count == 1
    assert result.retrieval_run.metrics["failure_reason"] == "fixture_source_unavailable"

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.domain == "flood"
    assert evidence.is_source_failure is True
    assert evidence.confidence == ConfidenceBand.UNKNOWN
    assert evidence.observed_value["failure_reason"] == "fixture_source_unavailable"


def test_fixture_output_is_idempotent_for_same_file() -> None:
    connector = StaticFloodFixtureConnector()
    first = connector.load_fixture(FIXTURE_DIR / "flood_success.json")
    second = connector.load_fixture(FIXTURE_DIR / "flood_success.json")

    assert first.retrieval_run.ingest_run_id == second.retrieval_run.ingest_run_id
    assert first.evidence_inputs[0].evidence_id == second.evidence_inputs[0].evidence_id


def test_connector_rejects_uri_like_fixture_paths() -> None:
    with pytest.raises(FixtureConnectorError, match="local file paths"):
        StaticFloodFixtureConnector().load_fixture("https://example.test/flood.json")


def test_connector_stays_before_claims_reports_and_live_io() -> None:
    source = inspect.getsource(flood_fixture_module)

    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
