from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.connectors import (
    ConnectorEvidenceIngestionAdapter,
    ConnectorFixtureQualityIssue,
    ConnectorFixtureQualityIssueCode,
    ConnectorFixtureQualityProfile,
    ConnectorRetrievalProvenanceAdapter,
    FixtureConnectorIngestWorkflow,
    StaticFloodFixtureConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
    evaluate_flood_fixture_quality,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class ApiStatusRetrievalProvenancePort:
    def __init__(self) -> None:
        self._stored: dict[UUID, SourceRetrievalRunContract] = {}

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        return ingest_run_id in self._stored

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        self._stored[retrieval_run.ingest_run_id] = retrieval_run
        return retrieval_run


class ApiStatusEvidencePort:
    def __init__(self) -> None:
        self._stored: dict[UUID, EvidenceContract] = {}
        self._source_failure_counter = 1

    def create_observation(self, evidence: EvidenceContract) -> EvidenceContract:
        self._stored[evidence.evidence_id] = evidence
        return evidence

    def create_source_failure(
        self,
        *,
        area_id: UUID,
        source_id: UUID,
        method_code: str,
        caveat: str,
        evidence_code: str = "SOURCE_FAILURE",
        domain: str = "unknown",
        observation: str | None = None,
        observed_value: dict[str, object] | None = None,
    ) -> EvidenceContract:
        created = EvidenceContract(
            evidence_id=UUID(int=self._source_failure_counter),
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


def _workflow() -> FixtureConnectorIngestWorkflow:
    return FixtureConnectorIngestWorkflow(
        connector=StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            ApiStatusRetrievalProvenancePort(),
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(
            ApiStatusEvidencePort(),
        ),
    )


def _store_review_status(
    app: FastAPI,
    *,
    fixture_name: str,
    quality: ConnectorFixtureQualityProfile | None = None,
) -> str:
    result = _workflow().ingest_fixture(FIXTURE_DIR / fixture_name)
    packet = build_connector_run_review_packet(result)
    handoff = build_connector_review_handoff(packet)
    status = build_connector_run_review_status(
        handoff,
        quality or evaluate_flood_fixture_quality(result.connector_result),
    )
    services = cast(ApiServices, app.state.services)
    services.connector_review_statuses[packet.ingest_run_id] = status
    return str(packet.ingest_run_id)


def _enqueue_review_status(
    app: FastAPI,
    *,
    fixture_name: str,
) -> str:
    result = _workflow().ingest_fixture(FIXTURE_DIR / fixture_name)
    packet = build_connector_run_review_packet(result)
    handoff = build_connector_review_handoff(packet)
    status = build_connector_run_review_status(
        handoff,
        evaluate_flood_fixture_quality(result.connector_result),
    )
    services = cast(ApiServices, app.state.services)
    services.connector_review_queue.enqueue_review_status(status)
    return str(packet.ingest_run_id)


def test_connector_review_status_endpoint_returns_handoff_and_quality() -> None:
    app = create_app()
    client = TestClient(app)
    ingest_run_id = _store_review_status(app, fixture_name="flood_success.json")

    response = client.get(f"/connector-runs/{ingest_run_id}/review-status")

    assert response.status_code == 200
    record = response.json()
    assert record["connector_name"] == "fixture_flood_static"
    assert record["disposition"] == "ready_for_connector_qa"
    assert record["queue_name"] == "connector-quality-review"
    assert record["review_required"] is False
    assert record["quality"] == {
        "passed": True,
        "evidence_count": 1,
        "source_failure_count": 0,
        "blocking_issue_count": 0,
        "issues": [],
    }


def test_connector_review_status_endpoint_surfaces_source_failure_handoff() -> None:
    app = create_app()
    client = TestClient(app)
    ingest_run_id = _store_review_status(app, fixture_name="flood_failure.json")

    response = client.get(f"/connector-runs/{ingest_run_id}/review-status")

    assert response.status_code == 200
    record = response.json()
    assert record["disposition"] == "needs_human_review"
    assert record["priority"] == "high"
    assert record["review_required"] is True
    assert record["quality"]["passed"] is True
    assert record["quality"]["source_failure_count"] == 1
    assert record["signal_codes"] == [
        "retrieval_not_succeeded",
        "retrieval_errors_present",
        "source_failure_evidence_present",
    ]


def test_connector_review_status_endpoint_uses_quality_issues_as_review_required() -> None:
    app = create_app()
    client = TestClient(app)
    quality = ConnectorFixtureQualityProfile(
        connector_name="fixture_flood_static",
        evidence_count=1,
        source_failure_count=0,
        issues=(
            ConnectorFixtureQualityIssue(
                code=ConnectorFixtureQualityIssueCode.FIXTURE_METRIC_MISSING,
                message="fixture retrieval metrics must mark fixture_only as true",
            ),
        ),
    )
    ingest_run_id = _store_review_status(
        app,
        fixture_name="flood_success.json",
        quality=quality,
    )

    response = client.get(f"/connector-runs/{ingest_run_id}/review-status")

    assert response.status_code == 200
    record = response.json()
    assert record["disposition"] == "ready_for_connector_qa"
    assert record["review_required"] is True
    assert record["quality"]["passed"] is False
    assert record["quality"]["issues"] == [
        {
            "code": "fixture_metric_missing",
            "message": "fixture retrieval metrics must mark fixture_only as true",
            "blocking": True,
        },
    ]


def test_connector_review_status_endpoint_returns_404_for_unknown_run() -> None:
    client = TestClient(create_app())

    response = client.get(f"/connector-runs/{uuid4()}/review-status")

    assert response.status_code == 404
    assert response.json()["detail"] == "connector run review status not found"


def test_connector_review_queue_endpoint_returns_in_memory_queue_item() -> None:
    app = create_app()
    client = TestClient(app)
    ingest_run_id = _enqueue_review_status(app, fixture_name="flood_failure.json")

    response = client.get(f"/connector-runs/{ingest_run_id}/review-queue")

    assert response.status_code == 200
    record = response.json()
    assert record["ingest_run_id"] == ingest_run_id
    assert record["job_type"] == "connector_review_status"
    assert record["status"] == "needs_review"
    assert record["priority"] == 10
    assert record["idempotency_key"] == f"connector_review_status:{ingest_run_id}"
    assert record["payload"]["ingest_run_id"] == ingest_run_id
    assert record["payload"]["kind"] == "connector_review_status"
    assert record["attempts"] == 0
    assert record["max_attempts"] == 1
    assert record["locked_by"] is None
    assert record["locked_at"] is None
    assert record["started_at"] is None
    assert record["finished_at"] is None
    assert record["last_error"] is None


def test_connector_review_queue_endpoint_surfaces_in_memory_worker_state() -> None:
    app = create_app()
    client = TestClient(app)
    ingest_run_id = _enqueue_review_status(app, fixture_name="flood_failure.json")
    services = cast(ApiServices, app.state.services)
    leased = services.connector_review_queue.lease_next(worker_id="api-test-worker")

    assert leased is not None

    response = client.get(f"/connector-runs/{ingest_run_id}/review-queue")

    assert response.status_code == 200
    record = response.json()
    assert record["status"] == "running"
    assert record["attempts"] == 1
    assert record["max_attempts"] == 1
    assert record["locked_by"] == "api-test-worker"
    assert record["locked_at"] is not None
    assert record["started_at"] is not None
    assert record["finished_at"] is None
    assert record["last_error"] is None


def test_connector_review_queue_endpoint_returns_404_for_unknown_run() -> None:
    client = TestClient(create_app())

    response = client.get(f"/connector-runs/{uuid4()}/review-queue")

    assert response.status_code == 404
    assert response.json()["detail"] == "connector review queue item not found"
