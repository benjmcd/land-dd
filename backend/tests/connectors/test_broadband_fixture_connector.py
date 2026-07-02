from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

import app.connectors.broadband_fixture as broadband_fixture_module
from app.connectors import FixtureConnectorError, StaticBroadbandFixtureConnector
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceRetrievalStatus

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


def _fixture_payload(name: str) -> dict[str, Any]:
    payload = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _write_fixture(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "broadband-fixture.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_success_fixture_emits_broadband_source_observation() -> None:
    result = StaticBroadbandFixtureConnector().load_fixture(
        FIXTURE_DIR / "nc_buncombe_bun_broadband_no_access.json",
    )

    assert result.retrieval_run.connector_name == "fixture_broadband_static"
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.dataset_version_id is not None
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.metrics["fixture_only"] is True

    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.domain == "broadband"
    assert evidence.dataset_version_id == result.retrieval_run.dataset_version_id
    assert evidence.observed_value["has_any_broadband"] is False
    assert evidence.is_source_failure is False
    assert evidence.confidence == ConfidenceBand.LOW


def test_failure_fixture_emits_blocked_retrieval_and_source_failure_input() -> None:
    result = StaticBroadbandFixtureConnector().load_fixture(
        FIXTURE_DIR / "nc_buncombe_bun_broadband_unavailable.json",
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.BLOCKED
    assert result.retrieval_run.error_count == 1
    assert result.retrieval_run.metrics["failure_reason"] == "source_unavailable"

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.domain == "broadband"
    assert evidence.is_source_failure is True
    assert evidence.confidence == ConfidenceBand.UNKNOWN
    assert evidence.observed_value["failure_reason"] == "source_unavailable"


def test_connector_rejects_uri_like_fixture_paths() -> None:
    with pytest.raises(FixtureConnectorError, match="local file paths"):
        StaticBroadbandFixtureConnector().load_fixture(
            "https://example.test/broadband.json"
        )


def test_connector_rejects_connector_name_mismatch(tmp_path: Path) -> None:
    payload = _fixture_payload("nc_buncombe_bun_broadband_no_access.json")
    payload["retrieval_run"]["connector_name"] = "fixture_flood_static"

    with pytest.raises(FixtureConnectorError, match="connector_name mismatch"):
        StaticBroadbandFixtureConnector().load_fixture(_write_fixture(tmp_path, payload))


def test_connector_rejects_non_broadband_evidence(tmp_path: Path) -> None:
    payload = _fixture_payload("nc_buncombe_bun_broadband_no_access.json")
    payload["evidence"][0]["domain"] = "flood"

    with pytest.raises(FixtureConnectorError, match="non-broadband evidence"):
        StaticBroadbandFixtureConnector().load_fixture(_write_fixture(tmp_path, payload))


def test_success_fixture_requires_non_failure_source_observation(tmp_path: Path) -> None:
    payload = _fixture_payload("nc_buncombe_bun_broadband_unavailable.json")
    payload["retrieval_run"]["status"] = "succeeded"
    payload["retrieval_run"]["row_count"] = 1
    payload["retrieval_run"]["error_count"] = 0
    payload["retrieval_run"]["metrics"] = {
        "fixture_only": True,
        "source": "local_json",
    }

    with pytest.raises(FixtureConnectorError, match="non-failure evidence"):
        StaticBroadbandFixtureConnector().load_fixture(_write_fixture(tmp_path, payload))


def test_blocked_fixture_requires_source_failure_evidence(tmp_path: Path) -> None:
    payload = _fixture_payload("nc_buncombe_bun_broadband_no_access.json")
    payload["retrieval_run"]["status"] = "blocked"
    payload["retrieval_run"]["row_count"] = 0
    payload["retrieval_run"]["error_count"] = 1
    payload["retrieval_run"]["metrics"] = {
        "fixture_only": True,
        "source": "local_json",
        "failure_reason": "source_unavailable",
    }

    with pytest.raises(FixtureConnectorError, match="source-failure evidence"):
        StaticBroadbandFixtureConnector().load_fixture(_write_fixture(tmp_path, payload))


def test_connector_stays_before_claims_reports_and_live_io() -> None:
    source = inspect.getsource(broadband_fixture_module)

    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
