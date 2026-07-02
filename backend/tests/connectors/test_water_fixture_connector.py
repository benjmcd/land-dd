from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

import app.connectors.water_fixture as water_fixture_module
from app.connectors import FixtureConnectorError, StaticWaterFixtureConnector
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceRetrievalStatus

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


def _fixture_payload(name: str) -> dict[str, Any]:
    payload = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _write_fixture(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "water-fixture.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_stations_fixture_emits_water_source_observation() -> None:
    result = StaticWaterFixtureConnector().load_fixture(
        FIXTURE_DIR / "nc_buncombe_bun_water_stations_found.json",
    )

    assert result.retrieval_run.connector_name == "fixture_water_static"
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.dataset_version_id is not None
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.metrics["fixture_only"] is True
    assert result.retrieval_run.metrics["station_count"] == 2

    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "WATER_MONITORING_SCREEN"
    assert evidence.domain == "water"
    assert evidence.dataset_version_id == result.retrieval_run.dataset_version_id
    assert evidence.observed_value["plausible_water_context"] is True
    assert evidence.observed_value["monitoring_station_count"] == 2
    assert evidence.is_source_failure is False
    assert evidence.confidence == ConfidenceBand.LOW


def test_no_stations_fixture_emits_water_no_context_observation() -> None:
    result = StaticWaterFixtureConnector().load_fixture(
        FIXTURE_DIR / "nc_buncombe_bun_water_no_stations.json",
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "WATER_MONITORING_SCREEN"
    assert evidence.domain == "water"
    assert evidence.observed_value["no_plausible_water_context"] is True
    assert evidence.observed_value["monitoring_station_count"] == 0
    assert evidence.is_source_failure is False


def test_failure_fixture_emits_failed_retrieval_and_source_failure_input() -> None:
    result = StaticWaterFixtureConnector().load_fixture(
        FIXTURE_DIR / "nc_buncombe_bun_water_unavailable.json",
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.error_count == 1
    assert result.retrieval_run.metrics["failure_reason"] == "usgs_water_request_error"

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.evidence_code == "WATER_SOURCE_UNAVAILABLE"
    assert evidence.domain == "water"
    assert evidence.is_source_failure is True
    assert evidence.confidence == ConfidenceBand.UNKNOWN
    assert evidence.observed_value["failure_reason"] == "usgs_water_request_error"


def test_connector_rejects_uri_like_fixture_paths() -> None:
    with pytest.raises(FixtureConnectorError, match="local file paths"):
        StaticWaterFixtureConnector().load_fixture("https://example.test/water.json")


def test_connector_rejects_connector_name_mismatch(tmp_path: Path) -> None:
    payload = _fixture_payload("nc_buncombe_bun_water_stations_found.json")
    payload["retrieval_run"]["connector_name"] = "fixture_env_hazard_static"

    with pytest.raises(FixtureConnectorError, match="connector_name mismatch"):
        StaticWaterFixtureConnector().load_fixture(_write_fixture(tmp_path, payload))


def test_connector_rejects_non_water_evidence(tmp_path: Path) -> None:
    payload = _fixture_payload("nc_buncombe_bun_water_stations_found.json")
    payload["evidence"][0]["domain"] = "env_hazard"

    with pytest.raises(FixtureConnectorError, match="non-water evidence"):
        StaticWaterFixtureConnector().load_fixture(_write_fixture(tmp_path, payload))


def test_connector_rejects_empty_evidence(tmp_path: Path) -> None:
    payload = _fixture_payload("nc_buncombe_bun_water_stations_found.json")
    payload["evidence"] = []

    with pytest.raises(FixtureConnectorError, match="must emit evidence inputs"):
        StaticWaterFixtureConnector().load_fixture(_write_fixture(tmp_path, payload))


def test_success_fixture_requires_non_failure_source_observation(tmp_path: Path) -> None:
    payload = _fixture_payload("nc_buncombe_bun_water_unavailable.json")
    payload["retrieval_run"]["status"] = "succeeded"
    payload["retrieval_run"]["row_count"] = 1
    payload["retrieval_run"]["error_count"] = 0
    payload["retrieval_run"]["metrics"] = {
        "fixture_only": True,
        "source": "local_json",
    }

    with pytest.raises(FixtureConnectorError, match="non-failure evidence"):
        StaticWaterFixtureConnector().load_fixture(_write_fixture(tmp_path, payload))


def test_failed_fixture_requires_source_failure_evidence(tmp_path: Path) -> None:
    payload = _fixture_payload("nc_buncombe_bun_water_stations_found.json")
    payload["retrieval_run"]["status"] = "failed"
    payload["retrieval_run"]["row_count"] = 0
    payload["retrieval_run"]["error_count"] = 1
    payload["retrieval_run"]["metrics"] = {
        "fixture_only": True,
        "source": "local_json",
        "failure_reason": "usgs_water_request_error",
    }

    with pytest.raises(FixtureConnectorError, match="source-failure evidence"):
        StaticWaterFixtureConnector().load_fixture(_write_fixture(tmp_path, payload))


def test_connector_stays_before_claims_reports_and_live_io() -> None:
    source = inspect.getsource(water_fixture_module)

    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
