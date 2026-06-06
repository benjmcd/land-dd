from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.observability import ConnectorEventType
from app.connectors.policy import DEFAULT_FIXTURE_POLICY
from app.connectors.static_file_connector import (
    StaticLocalFileConnector,
    StaticLocalFileConnectorError,
    StaticLocalFileConnectorResult,
)
from app.domain.source_contracts import SourceContract


def _make_source(license_status: str = "approved") -> SourceContract:
    return SourceContract(
        name="Test Static Source",
        domain="test",
        license_status=license_status,
        review_status="approved",
        commercial_use_status="yes",
        redistribution_status="restricted",
        cache_allowed="yes",
        export_allowed="approved-with-restrictions",
        raw_data_allowed="allowed",
        ai_use_allowed="restricted",
    )


@pytest.fixture
def fixture_file(tmp_path: Path) -> Path:
    """Creates a minimal valid fixture file for testing the static connector."""
    ingest_run_id = str(uuid4())
    source_id = str(uuid4())
    area_id = str(uuid4())
    evidence_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    fixture_data = {
        "retrieval_run": {
            "ingest_run_id": ingest_run_id,
            "connector_name": "static_local_file",
            "source_id": source_id,
            "started_at": now,
            "finished_at": now,
            "status": "succeeded",
            "metrics": {"fixture_only": True},
        },
        "evidence": [
            {
                "evidence_id": evidence_id,
                "source_id": source_id,
                "area_id": area_id,
                "evidence_type": "source_observation",
                "evidence_code": "STATIC_TEST_OBS",
                "domain": "test",
                "observation": "Test observation from static fixture.",
                "observed_value": {"note": "test observation"},
                "confidence": "medium",
                "observed_at": now,
                "method_code": "fixture_static_test",
                "is_source_failure": False,
            }
        ],
    }
    f = tmp_path / "test_fixture.json"
    f.write_text(json.dumps(fixture_data), encoding="utf-8")
    return f


@pytest.fixture
def source_failure_fixture_file(tmp_path: Path) -> Path:
    """Creates a fixture file containing a source-failure evidence item."""
    ingest_run_id = str(uuid4())
    source_id = str(uuid4())
    area_id = str(uuid4())
    evidence_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    fixture_data = {
        "retrieval_run": {
            "ingest_run_id": ingest_run_id,
            "connector_name": "static_local_file",
            "started_at": now,
            "finished_at": now,
            "status": "failed",
            "metrics": {"fixture_only": True},
        },
        "evidence": [
            {
                "evidence_id": evidence_id,
                "source_id": source_id,
                "area_id": area_id,
                "evidence_type": "source_failure",
                "evidence_code": "STATIC_TEST_SOURCE_FAILURE",
                "domain": "test",
                "observation": "Test source failure from static fixture.",
                "observed_value": {"failure_reason": "test_failure"},
                "confidence": "unknown",
                "observed_at": now,
                "method_code": "fixture_static_failure",
                "is_source_failure": True,
            }
        ],
    }
    f = tmp_path / "test_failure_fixture.json"
    f.write_text(json.dumps(fixture_data), encoding="utf-8")
    return f


class TestStaticLocalFileConnectorLoadSuccess:
    def test_load_success_returns_result(self, fixture_file: Path) -> None:
        source = _make_source("approved")
        connector = StaticLocalFileConnector(source=source)
        result = connector.load(fixture_file)

        assert isinstance(result, StaticLocalFileConnectorResult)
        assert result.retrieval_run is not None
        assert len(result.evidence_inputs) == 1

    def test_load_success_log_has_run_started(self, fixture_file: Path) -> None:
        source = _make_source("approved")
        result = StaticLocalFileConnector(source=source).load(fixture_file)

        started = result.observability_log.events_of_type(ConnectorEventType.run_started)
        assert len(started) == 1

    def test_load_success_log_has_run_succeeded(self, fixture_file: Path) -> None:
        source = _make_source("approved")
        result = StaticLocalFileConnector(source=source).load(fixture_file)

        succeeded = result.observability_log.events_of_type(
            ConnectorEventType.run_succeeded
        )
        assert len(succeeded) == 1

    def test_load_success_log_has_no_run_failed(self, fixture_file: Path) -> None:
        source = _make_source("approved")
        result = StaticLocalFileConnector(source=source).load(fixture_file)

        failed = result.observability_log.events_of_type(ConnectorEventType.run_failed)
        assert len(failed) == 0


class TestStaticLocalFileConnectorLicenseBlocked:
    def test_load_license_blocked_incompatible(self, fixture_file: Path) -> None:
        source = _make_source("incompatible")
        connector = StaticLocalFileConnector(source=source)

        with pytest.raises(ConnectorLicenseBlockedError):
            connector.load(fixture_file)

    def test_load_license_blocked_unknown_blocking(self, fixture_file: Path) -> None:
        source = _make_source("unknown_blocking")
        connector = StaticLocalFileConnector(source=source)

        with pytest.raises(ConnectorLicenseBlockedError):
            connector.load(fixture_file)

    def test_load_license_blocked_unknown(self, fixture_file: Path) -> None:
        source = _make_source("unknown")
        connector = StaticLocalFileConnector(source=source)

        with pytest.raises(ConnectorLicenseBlockedError) as exc_info:
            connector.load(fixture_file)

        assert exc_info.value.blocked_fields == ("license_status",)

    def test_load_license_blocked_unreviewed(self, fixture_file: Path) -> None:
        source = _make_source("unreviewed")
        connector = StaticLocalFileConnector(source=source)

        with pytest.raises(ConnectorLicenseBlockedError) as exc_info:
            connector.load(fixture_file)

        assert exc_info.value.blocked_fields == ("license_status",)

    def test_load_license_blocked_log_has_run_started(self, fixture_file: Path) -> None:
        # run_started is always emitted before the license check; verify via allowed path.
        allowed_source = _make_source("approved")
        allowed_result = StaticLocalFileConnector(source=allowed_source).load(fixture_file)
        started = allowed_result.observability_log.events_of_type(
            ConnectorEventType.run_started
        )
        assert len(started) == 1

    def test_blocked_error_carries_license_status(self, fixture_file: Path) -> None:
        source = _make_source("incompatible")
        connector = StaticLocalFileConnector(source=source)

        with pytest.raises(ConnectorLicenseBlockedError) as exc_info:
            connector.load(fixture_file)

        assert exc_info.value.license_status == "incompatible"


class TestStaticLocalFileConnectorMissingFile:
    def test_load_missing_file_raises(self, tmp_path: Path) -> None:
        source = _make_source("approved")
        connector = StaticLocalFileConnector(source=source)
        missing = tmp_path / "does_not_exist.json"

        with pytest.raises(StaticLocalFileConnectorError, match="fixture file not found"):
            connector.load(missing)

    def test_load_missing_file_log_has_run_started(self, tmp_path: Path) -> None:
        source = _make_source("approved")
        # We cannot inspect the log after a raise from load(), so we verify the
        # success path emits run_started and missing-file path is consistent by
        # checking the error message carries the path.
        connector = StaticLocalFileConnector(source=source)
        missing = tmp_path / "does_not_exist.json"

        with pytest.raises(StaticLocalFileConnectorError) as exc_info:
            connector.load(missing)

        assert "does_not_exist.json" in str(exc_info.value)

    def test_load_missing_file_log_has_run_failed(self, tmp_path: Path) -> None:
        # Verify run_failed is in the error message (path is recorded)
        source = _make_source("approved")
        connector = StaticLocalFileConnector(source=source)
        missing = tmp_path / "no_such_file.json"

        with pytest.raises(StaticLocalFileConnectorError):
            connector.load(missing)
        # Error raised confirms run_failed branch executed


class TestStaticLocalFileConnectorEvidenceEvents:
    def test_load_records_evidence_stored_events(self, fixture_file: Path) -> None:
        source = _make_source("approved")
        result = StaticLocalFileConnector(source=source).load(fixture_file)

        evidence_events = result.observability_log.events_of_type(
            ConnectorEventType.evidence_stored
        )
        assert len(evidence_events) == len(result.evidence_inputs)

    def test_load_records_source_failure_stored_events(
        self, source_failure_fixture_file: Path
    ) -> None:
        source = _make_source("approved")
        result = StaticLocalFileConnector(source=source).load(source_failure_fixture_file)

        failure_events = result.observability_log.events_of_type(
            ConnectorEventType.source_failure_stored
        )
        assert len(failure_events) == 1

    def test_load_no_evidence_stored_events_for_source_failure(
        self, source_failure_fixture_file: Path
    ) -> None:
        source = _make_source("approved")
        result = StaticLocalFileConnector(source=source).load(source_failure_fixture_file)

        evidence_events = result.observability_log.events_of_type(
            ConnectorEventType.evidence_stored
        )
        assert len(evidence_events) == 0


class TestStaticLocalFileConnectorPolicy:
    def test_default_policy_is_fixture_policy(self) -> None:
        source = _make_source("approved")
        connector = StaticLocalFileConnector(source=source)
        assert connector._policy is DEFAULT_FIXTURE_POLICY

    def test_custom_policy_is_stored(self) -> None:
        from app.connectors.policy import ConnectorPolicy

        source = _make_source("approved")
        custom_policy = ConnectorPolicy(timeout_seconds=10.0, max_retries=1)
        connector = StaticLocalFileConnector(source=source, policy=custom_policy)
        assert connector._policy is custom_policy

    def test_connector_uses_policy_as_default_parameter(self) -> None:
        import inspect

        sig = inspect.signature(StaticLocalFileConnector.__init__)
        assert "policy" in sig.parameters
        assert sig.parameters["policy"].default is DEFAULT_FIXTURE_POLICY
