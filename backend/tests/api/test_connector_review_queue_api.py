from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.connectors import (
    CONNECTOR_REVIEW_STATUS_JOB_TYPE,
    ConnectorEvidenceIngestionAdapter,
    ConnectorRetrievalProvenanceAdapter,
    ConnectorRunReviewStatus,
    FixtureConnectorIngestWorkflow,
    StaticFloodFixtureConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
    evaluate_flood_fixture_quality,
)
from app.domain.enums import ConfidenceBand, EvidenceType, JobStatus
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class _RetrievalProvenancePort:
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


class _EvidencePort:
    def __init__(self) -> None:
        self._stored: dict[UUID, EvidenceContract] = {}
        self._counter: int = 1

    def create_observation(self, evidence: EvidenceContract) -> EvidenceContract:
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
    ) -> EvidenceContract:
        created = EvidenceContract(
            evidence_id=evidence_id or UUID(int=self._counter),
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
        self._counter += 1
        self._stored[created.evidence_id] = created
        return created

    def evidence_exists(self, evidence_id: UUID) -> bool:
        return evidence_id in self._stored

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        return [e for e in self._stored.values() if e.area_id == area_id]


def _make_workflow() -> FixtureConnectorIngestWorkflow:
    return FixtureConnectorIngestWorkflow(
        connector=StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            _RetrievalProvenancePort()
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(_EvidencePort()),
    )


def _build_review_status(fixture_name: str) -> ConnectorRunReviewStatus:
    result = _make_workflow().ingest_fixture(FIXTURE_DIR / fixture_name)
    packet = build_connector_run_review_packet(result)
    handoff = build_connector_review_handoff(packet)
    quality = evaluate_flood_fixture_quality(result.connector_result)
    return build_connector_run_review_status(handoff, quality)


def test_get_connector_review_queue_item_returns_queued_status() -> None:
    app = create_app()
    client = TestClient(app)
    services = cast(ApiServices, app.state.services)
    review_status = _build_review_status("flood_success.json")
    item = services.connector_review_queue_repo.enqueue_review_status(review_status)

    response = client.get(f"/connector-review-queue/{item.ingest_run_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["ingest_run_id"] == str(item.ingest_run_id)
    assert body["job_type"] == CONNECTOR_REVIEW_STATUS_JOB_TYPE
    assert body["status"] == JobStatus.QUEUED.value
    assert "idempotency_key" not in body


def test_get_connector_review_queue_item_returns_needs_review_for_failure_fixture() -> None:
    app = create_app()
    client = TestClient(app)
    services = cast(ApiServices, app.state.services)
    review_status = _build_review_status("flood_failure.json")
    item = services.connector_review_queue_repo.enqueue_review_status(review_status)

    response = client.get(f"/connector-review-queue/{item.ingest_run_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == JobStatus.NEEDS_REVIEW.value
    assert body["payload"]["review_required"] is True
    assert body["payload"]["kind"] == CONNECTOR_REVIEW_STATUS_JOB_TYPE


def test_get_connector_review_queue_item_returns_404_for_unknown_ingest_run_id() -> None:
    client = TestClient(create_app())

    response = client.get(f"/connector-review-queue/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "connector review queue item not found"


def test_get_connector_review_queue_item_returns_422_for_non_uuid_path_segment() -> None:
    client = TestClient(create_app())

    response = client.get("/connector-review-queue/not-a-uuid")

    assert response.status_code == 422
