from __future__ import annotations

import inspect
from pathlib import Path
from typing import cast
from uuid import UUID

import app.connectors.review_status as review_status_module
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
from app.domain.source_contracts import SourceRetrievalRunContract, SourceRetrievalStatus

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "connectors"


class ReviewStatusRetrievalProvenancePort:
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


class ReviewStatusEvidencePort:
    def __init__(self) -> None:
        self._stored: dict[UUID, EvidenceContract] = {}
        self._source_failure_counter = 1

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


def _workflow() -> FixtureConnectorIngestWorkflow:
    return FixtureConnectorIngestWorkflow(
        connector=StaticFloodFixtureConnector(),
        retrieval_provenance_adapter=ConnectorRetrievalProvenanceAdapter(
            ReviewStatusRetrievalProvenancePort(),
        ),
        evidence_ingestion_adapter=ConnectorEvidenceIngestionAdapter(
            ReviewStatusEvidencePort(),
        ),
    )


def test_review_status_combines_handoff_and_quality_profile() -> None:
    result = _workflow().ingest_fixture(FIXTURE_DIR / "flood_success.json")
    handoff = build_connector_review_handoff(build_connector_run_review_packet(result))
    quality = evaluate_flood_fixture_quality(result.connector_result)

    status = build_connector_run_review_status(handoff, quality)
    record = status.to_status_record()

    assert status.review_required is False
    assert record["review_required"] is False
    assert record["retrieval_status"] == SourceRetrievalStatus.SUCCEEDED.value
    assert record["quality"] == {
        "passed": True,
        "evidence_count": 1,
        "source_failure_count": 0,
        "blocking_issue_count": 0,
        "issues": (),
    }


def test_review_status_quality_issues_require_review() -> None:
    result = _workflow().ingest_fixture(FIXTURE_DIR / "flood_success.json")
    handoff = build_connector_review_handoff(build_connector_run_review_packet(result))
    quality = ConnectorFixtureQualityProfile(
        connector_name=handoff.packet.connector_name,
        evidence_count=1,
        source_failure_count=0,
        issues=(
            ConnectorFixtureQualityIssue(
                code=ConnectorFixtureQualityIssueCode.FIXTURE_LOG_URI_NOT_LOCAL,
                message="fixture retrieval log_uri must use the fixture:// scheme",
            ),
        ),
    )

    status = build_connector_run_review_status(handoff, quality)
    record = status.to_status_record()
    quality_record = cast(dict[str, object], record["quality"])

    assert status.review_required is True
    assert record["review_required"] is True
    assert quality_record["passed"] is False
    assert quality_record["blocking_issue_count"] == 1
    assert quality_record["issues"] == (
        {
            "code": "fixture_log_uri_not_local",
            "message": "fixture retrieval log_uri must use the fixture:// scheme",
            "blocking": True,
        },
    )


def test_review_status_rejects_connector_name_mismatch() -> None:
    result = _workflow().ingest_fixture(FIXTURE_DIR / "flood_success.json")
    handoff = build_connector_review_handoff(build_connector_run_review_packet(result))
    quality = ConnectorFixtureQualityProfile(
        connector_name="different_connector",
        evidence_count=1,
        source_failure_count=0,
        issues=(),
    )

    try:
        build_connector_run_review_status(handoff, quality)
    except ValueError as exc:
        assert str(exc) == "connector handoff and quality profile must use the same connector"
    else:
        raise AssertionError("connector mismatch should fail closed")


def test_review_status_stays_connector_owned_and_before_api_persistence() -> None:
    source = inspect.getsource(review_status_module)

    assert "app.source_registry" not in source
    assert "app.evidence_ledger" not in source
    assert "app.claims_engine" not in source
    assert "app.reports" not in source
    assert "app.api" not in source
    assert "app.db" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
