from __future__ import annotations

import inspect
from pathlib import Path
from uuid import UUID

import app.connectors.retrieval_provenance as retrieval_provenance_module
from app.connectors import (
    ConnectorRetrievalProvenanceAdapter,
    StaticFloodFixtureConnector,
)
from app.domain.source_contracts import SourceRetrievalRunContract

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class RecordingRetrievalProvenancePort:
    def __init__(self, initial: tuple[SourceRetrievalRunContract, ...] = ()) -> None:
        self.recorded_runs: list[SourceRetrievalRunContract] = []
        self._stored = {run.ingest_run_id: run for run in initial}

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        return ingest_run_id in self._stored

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        self.recorded_runs.append(retrieval_run)
        self._stored[retrieval_run.ingest_run_id] = retrieval_run
        return retrieval_run


def _load_success_run() -> SourceRetrievalRunContract:
    return StaticFloodFixtureConnector().load_fixture(
        FIXTURE_DIR / "flood_success.json",
    ).retrieval_run


def test_retrieval_provenance_adapter_records_connector_run_with_identity() -> None:
    retrieval_run = _load_success_run()
    port = RecordingRetrievalProvenancePort()

    result = ConnectorRetrievalProvenanceAdapter(port).record_retrieval_run(
        retrieval_run,
    )

    assert port.recorded_runs == [retrieval_run]
    assert result.recorded_run == retrieval_run
    assert result.skipped_run is None
    assert result.recorded_run.ingest_run_id == retrieval_run.ingest_run_id
    assert result.recorded_run.dataset_version_id == retrieval_run.dataset_version_id


def test_retrieval_provenance_adapter_skips_duplicate_retrieval_runs() -> None:
    retrieval_run = _load_success_run()
    port = RecordingRetrievalProvenancePort(initial=(retrieval_run,))

    result = ConnectorRetrievalProvenanceAdapter(port).record_retrieval_run(
        retrieval_run,
    )

    assert port.recorded_runs == []
    assert result.recorded_run is None
    assert result.skipped_run == retrieval_run


def test_retrieval_provenance_adapter_records_before_evidence_ingestion() -> None:
    connector_result = StaticFloodFixtureConnector().load_fixture(
        FIXTURE_DIR / "flood_success.json",
    )
    port = RecordingRetrievalProvenancePort()

    result = ConnectorRetrievalProvenanceAdapter(port).record(connector_result)

    assert result.recorded_run == connector_result.retrieval_run
    assert connector_result.evidence_inputs
    assert port.recorded_runs == [connector_result.retrieval_run]


def test_retrieval_provenance_adapter_stays_connector_owned() -> None:
    source = inspect.getsource(retrieval_provenance_module)

    assert "app.source_registry" not in source
    assert "app.evidence_ledger" not in source
    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
