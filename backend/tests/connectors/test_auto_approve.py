"""Tests for CONNECTOR_AUTO_APPROVE setting."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from app.api.connectors import _maybe_auto_approve
from app.api.dependencies import create_api_services
from app.connectors import (
    ConnectorEvidenceIngestionAdapter,
    ConnectorRetrievalProvenanceAdapter,
    ConnectorRunReviewStatus,
    FixtureConnectorIngestWorkflow,
    InMemoryConnectorReviewQueueRepository,
    StaticFloodFixtureConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
    evaluate_flood_fixture_quality,
)
from app.core.config import Settings
from app.domain.enums import ConfidenceBand, EvidenceType, JobStatus
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceRetrievalRunContract

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class _RetrievalProvenancePort:
    def __init__(self) -> None:
        self._stored: dict[UUID, SourceRetrievalRunContract] = {}

    def retrieval_run_exists(self, ingest_run_id: UUID) -> bool:
        return ingest_run_id in self._stored

    def record_retrieval_run(
        self, retrieval_run: SourceRetrievalRunContract
    ) -> SourceRetrievalRunContract:
        self._stored[retrieval_run.ingest_run_id] = retrieval_run
        return retrieval_run


class _EvidencePort:
    def __init__(self) -> None:
        self._stored: dict[UUID, EvidenceContract] = {}
        self._counter = 1

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
        source_ingest_run_id: UUID | None = None,
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
            source_ingest_run_id=source_ingest_run_id,
        )
        self._counter += 1
        self._stored[created.evidence_id] = created
        return created

    def evidence_exists(self, evidence_id: UUID) -> bool:
        return evidence_id in self._stored

    def list_by_area(self, area_id: UUID) -> list[EvidenceContract]:
        return [e for e in self._stored.values() if e.area_id == area_id]


def _workflow() -> FixtureConnectorIngestWorkflow:
    return FixtureConnectorIngestWorkflow(
        connector=StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(_RetrievalProvenancePort()),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(_EvidencePort()),
    )


def _review_status(fixture_name: str) -> ConnectorRunReviewStatus:
    result = _workflow().ingest_fixture(FIXTURE_DIR / fixture_name)
    packet = build_connector_run_review_packet(result)
    handoff = build_connector_review_handoff(packet)
    quality = evaluate_flood_fixture_quality(result.connector_result)
    return build_connector_run_review_status(handoff, quality)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_maybe_auto_approve_approves_when_enabled_and_quality_passes() -> None:
    """Setting enabled + READY_FOR_CONNECTOR_QA disposition -> item is auto-approved."""
    review_status = _review_status("flood_success.json")
    repo = InMemoryConnectorReviewQueueRepository()
    queue_item = repo.enqueue_review_status(review_status)

    services = create_api_services()
    # Swap in our controlled repo
    services.connector_review_queue._store.update(repo._store)  # type: ignore[attr-defined]

    mock_settings = Settings.model_construct(connector_auto_approve=True)
    with patch("app.api.connectors.get_settings", return_value=mock_settings):
        result = _maybe_auto_approve(services, queue_item, review_status)

    assert result.status == JobStatus.SUCCEEDED
    assert result.payload["review_decision"]["action"] == "approve_for_connector_qa"
    assert result.payload["review_decision"]["reviewer_id"] == "system-auto-approve"


def test_maybe_auto_approve_does_not_approve_when_classification_is_needs_human_review() -> None:
    """Setting enabled but NEEDS_HUMAN_REVIEW disposition -> item is NOT auto-approved."""
    review_status = _review_status("flood_failure.json")
    repo = InMemoryConnectorReviewQueueRepository()
    queue_item = repo.enqueue_review_status(review_status)

    services = create_api_services()
    services.connector_review_queue._store.update(repo._store)  # type: ignore[attr-defined]

    mock_settings = Settings.model_construct(connector_auto_approve=True)
    with patch("app.api.connectors.get_settings", return_value=mock_settings):
        result = _maybe_auto_approve(services, queue_item, review_status)

    # Must be unchanged — still NEEDS_REVIEW, not auto-approved
    assert result.status == JobStatus.NEEDS_REVIEW
    assert "review_decision" not in result.payload


def test_maybe_auto_approve_does_not_approve_when_setting_is_false() -> None:
    """Setting disabled + READY_FOR_CONNECTOR_QA disposition -> item is NOT auto-approved."""
    review_status = _review_status("flood_success.json")
    repo = InMemoryConnectorReviewQueueRepository()
    queue_item = repo.enqueue_review_status(review_status)

    services = create_api_services()
    services.connector_review_queue._store.update(repo._store)  # type: ignore[attr-defined]

    mock_settings = Settings.model_construct(connector_auto_approve=False)
    with patch("app.api.connectors.get_settings", return_value=mock_settings):
        result = _maybe_auto_approve(services, queue_item, review_status)

    # Must be unchanged — still QUEUED, not approved
    assert result.status == JobStatus.QUEUED
    assert "review_decision" not in result.payload
