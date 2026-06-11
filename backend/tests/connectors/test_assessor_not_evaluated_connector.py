from __future__ import annotations

from uuid import UUID, uuid4

from app.connectors.assessor_not_evaluated import (
    ASSESSOR_NOT_EVALUATED_CAVEAT,
    ASSESSOR_NOT_EVALUATED_CONNECTOR_NAME,
    ASSESSOR_NOT_EVALUATED_METHOD_CODE,
    AssessorNotEvaluatedConnector,
    AssessorNotEvaluatedConnectorResult,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus

_AREA_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_SOURCE_ID = UUID("00000000-0000-4000-8000-000000000011")


def _make_source() -> SourceContract:
    return SourceContract(
        source_id=_SOURCE_ID,
        name="County assessor",
        organization="County",
        source_type="local_official",
        domain="assessor",
        license_status="approved-with-restrictions",
        commercial_use_status="restricted",
        metadata={"source_registry_id": "DS-011"},
    )


def test_query_returns_assessor_not_evaluated_connector_result() -> None:
    connector = AssessorNotEvaluatedConnector()
    source = _make_source()

    result = connector.query(area_id=_AREA_ID, source=source)

    assert isinstance(result, AssessorNotEvaluatedConnectorResult)


def test_retrieval_run_connector_name() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )

    assert result.retrieval_run.connector_name == ASSESSOR_NOT_EVALUATED_CONNECTOR_NAME


def test_retrieval_run_status_succeeded() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED


def test_evidence_inputs_has_exactly_one_element() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )

    assert len(result.evidence_inputs) == 1


def test_evidence_code_is_assessor_not_evaluated() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )
    evidence = result.evidence_inputs[0]

    assert evidence.evidence_code == "ASSESSOR_NOT_EVALUATED"


def test_evidence_domain_is_assessor() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )
    evidence = result.evidence_inputs[0]

    assert evidence.domain == "assessor"


def test_evidence_is_source_failure_is_true() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )
    evidence = result.evidence_inputs[0]

    assert evidence.is_source_failure is True


def test_evidence_observed_value_not_evaluated_is_true() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )
    evidence = result.evidence_inputs[0]

    assert evidence.observed_value["not_evaluated"] is True


def test_evidence_observed_value_reason() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )
    evidence = result.evidence_inputs[0]

    assert evidence.observed_value["reason"] == "machine_access_terms_not_reviewed"


def test_evidence_ids_are_deterministic_for_same_area_and_source() -> None:
    source = _make_source()

    result1 = AssessorNotEvaluatedConnector().query(area_id=_AREA_ID, source=source)
    result2 = AssessorNotEvaluatedConnector().query(area_id=_AREA_ID, source=source)

    assert result1.retrieval_run.ingest_run_id == result2.retrieval_run.ingest_run_id
    assert result1.evidence_inputs[0].evidence_id == result2.evidence_inputs[0].evidence_id


def test_different_area_id_produces_different_evidence_id() -> None:
    source = _make_source()
    area_id_a = uuid4()
    area_id_b = uuid4()

    result_a = AssessorNotEvaluatedConnector().query(area_id=area_id_a, source=source)
    result_b = AssessorNotEvaluatedConnector().query(area_id=area_id_b, source=source)

    assert result_a.evidence_inputs[0].evidence_id != result_b.evidence_inputs[0].evidence_id


def test_evidence_caveat_contains_assessed_value_is_not_market_value() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )
    evidence = result.evidence_inputs[0]

    assert evidence.caveat is not None
    assert "Assessed value is not market value" in evidence.caveat


def test_evidence_type_is_source_failure() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )
    evidence = result.evidence_inputs[0]

    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE


def test_evidence_confidence_is_unknown() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )
    evidence = result.evidence_inputs[0]

    assert evidence.confidence == ConfidenceBand.UNKNOWN


def test_evidence_method_code() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )
    evidence = result.evidence_inputs[0]

    assert evidence.method_code == ASSESSOR_NOT_EVALUATED_METHOD_CODE


def test_retrieval_run_metrics_contain_source_registry_id() -> None:
    result = AssessorNotEvaluatedConnector().query(
        area_id=_AREA_ID, source=_make_source()
    )

    assert result.retrieval_run.metrics["source_registry_id"] == "DS-011"
    assert result.retrieval_run.metrics["reason"] == "machine_access_terms_not_reviewed"


def test_caveat_constant_contains_no_programmatic_access_terms() -> None:
    assert "No programmatic access terms have been" in ASSESSOR_NOT_EVALUATED_CAVEAT
