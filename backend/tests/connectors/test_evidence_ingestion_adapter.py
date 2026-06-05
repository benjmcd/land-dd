from __future__ import annotations

import inspect
from pathlib import Path
from uuid import UUID

import pytest

import app.connectors.evidence_ingestion as evidence_ingestion_module
from app.connectors import (
    ConnectorEvidenceIngestionAdapter,
    ConnectorEvidenceIngestionError,
    FloodFixtureConnectorResult,
    StaticFloodFixtureConnector,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"
_WORKSPACE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


class RecordingEvidencePort:
    def __init__(self, initial: tuple[EvidenceContract, ...] = ()) -> None:
        self.created_observations: list[EvidenceContract] = []
        self.observation_workspace_ids: list[UUID | None] = []
        self.source_failure_calls: list[dict[str, object]] = []
        self._stored = {evidence.evidence_id: evidence for evidence in initial}
        self._source_failure_counter = 1

    def create_observation(
        self,
        evidence: EvidenceContract,
        *,
        workspace_id: UUID | None = None,
    ) -> EvidenceContract:
        self.created_observations.append(evidence)
        self.observation_workspace_ids.append(workspace_id)
        self._stored[evidence.evidence_id] = evidence
        return evidence

    def create_source_failure(
        self,
        *,
        evidence_id: UUID | None = None,
        area_id: UUID,
        source_id: UUID,
        method_code: str,
        caveat: str,
        evidence_code: str = "SOURCE_FAILURE",
        domain: str = "unknown",
        observation: str | None = None,
        observed_value: dict[str, object] | None = None,
        workspace_id: UUID | None = None,
    ) -> EvidenceContract:
        call: dict[str, object] = {
            "evidence_id": evidence_id,
            "area_id": area_id,
            "source_id": source_id,
            "method_code": method_code,
            "caveat": caveat,
            "evidence_code": evidence_code,
            "domain": domain,
            "observation": observation,
            "observed_value": observed_value,
            "workspace_id": workspace_id,
        }
        self.source_failure_calls.append(call)
        created = EvidenceContract(
            evidence_id=evidence_id or UUID(int=self._source_failure_counter),
            area_id=area_id,
            source_id=source_id,
            method_code=method_code,
            evidence_type=EvidenceType.SOURCE_FAILURE,
            evidence_code=evidence_code,
            domain=domain,
            observation=observation or f"Source unavailable or failed: {caveat}",
            observed_value=observed_value or {},
            confidence=ConfidenceBand.UNKNOWN,
            caveat=caveat,
            is_source_failure=True,
        )
        self._source_failure_counter += 1
        self._stored[created.evidence_id] = created
        return created

    def evidence_exists(self, evidence_id: UUID) -> bool:
        return evidence_id in self._stored

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        return [
            evidence
            for evidence in self._stored.values()
            if evidence.area_id == area_id
        ]


def _load_success_result() -> FloodFixtureConnectorResult:
    return StaticFloodFixtureConnector().load_fixture(FIXTURE_DIR / "flood_success.json")


def _load_failure_result() -> FloodFixtureConnectorResult:
    return StaticFloodFixtureConnector().load_fixture(FIXTURE_DIR / "flood_failure.json")


def test_ingestion_adapter_routes_normal_evidence_to_create_observation() -> None:
    port = RecordingEvidencePort()
    result = ConnectorEvidenceIngestionAdapter(port).ingest(_load_success_result())

    expected = _load_success_result().evidence_inputs[0]
    assert port.created_observations == [expected]
    assert port.observation_workspace_ids == [None]
    assert port.source_failure_calls == []
    assert result.created_evidence == (expected,)
    assert result.skipped_evidence == ()


def test_ingestion_adapter_routes_source_failure_to_public_failure_method() -> None:
    failure_result = _load_failure_result()
    failure_input = failure_result.evidence_inputs[0]
    port = RecordingEvidencePort()

    result = ConnectorEvidenceIngestionAdapter(port).ingest(failure_result)

    assert port.created_observations == []
    assert len(port.source_failure_calls) == 1
    call = port.source_failure_calls[0]
    assert call["evidence_id"] == failure_input.evidence_id
    assert call["area_id"] == failure_input.area_id
    assert call["source_id"] == failure_input.source_id
    assert call["method_code"] == failure_input.method_code
    assert call["caveat"] == failure_input.caveat
    assert call["evidence_code"] == failure_input.evidence_code
    assert call["domain"] == failure_input.domain
    assert call["observation"] == failure_input.observation
    assert call["observed_value"] == failure_input.observed_value
    assert call["workspace_id"] is None
    assert result.created_evidence[0].evidence_id == failure_input.evidence_id
    assert result.created_evidence[0].is_source_failure is True
    assert result.skipped_evidence == ()


def test_ingestion_adapter_forwards_workspace_scope_to_evidence_port() -> None:
    failure_result = _load_failure_result()
    port = RecordingEvidencePort()

    ConnectorEvidenceIngestionAdapter(
        port,
        workspace_id=_WORKSPACE_ID,
    ).ingest(failure_result)

    assert port.source_failure_calls[0]["workspace_id"] == _WORKSPACE_ID


def test_ingestion_adapter_skips_duplicate_deterministic_evidence_ids() -> None:
    success_result = _load_success_result()
    existing = success_result.evidence_inputs[0]
    port = RecordingEvidencePort(initial=(existing,))

    result = ConnectorEvidenceIngestionAdapter(port).ingest(success_result)

    assert port.created_observations == []
    assert port.source_failure_calls == []
    assert result.created_evidence == ()
    assert result.skipped_evidence == (existing,)


def test_ingestion_adapter_skips_repeated_source_failures_by_fingerprint() -> None:
    failure_result = _load_failure_result()
    port = RecordingEvidencePort()
    adapter = ConnectorEvidenceIngestionAdapter(port)

    first = adapter.ingest(failure_result)
    second = adapter.ingest(failure_result)

    assert len(port.source_failure_calls) == 1
    assert first.created_evidence[0].is_source_failure is True
    assert second.created_evidence == ()
    assert second.skipped_evidence == first.created_evidence


def test_ingestion_adapter_rejects_misaligned_source_failure_flags() -> None:
    evidence = _load_failure_result().evidence_inputs[0].model_copy(
        update={"is_source_failure": False},
    )

    with pytest.raises(ConnectorEvidenceIngestionError, match="must set"):
        ConnectorEvidenceIngestionAdapter(RecordingEvidencePort()).ingest_evidence(
            (evidence,),
        )


def test_evidence_ingestion_adapter_stays_before_claims_reports_and_live_io() -> None:
    source = inspect.getsource(evidence_ingestion_module)

    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
