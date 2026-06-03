from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService


class StubSourceChecker:
    def __init__(self, registered: set[UUID]) -> None:
        self._registered = registered

    def source_is_registered(self, source_id: UUID) -> bool:
        return source_id in self._registered

    def source_production_use_allowed(self, source_id: UUID) -> bool:
        return source_id in self._registered


class StubAreaChecker:
    def __init__(self, registered: set[UUID]) -> None:
        self._registered = registered

    def area_is_registered(self, area_id: UUID) -> bool:
        return area_id in self._registered


def make_service(
    *,
    area_id: UUID,
    source_id: UUID,
) -> EvidenceService:
    return EvidenceService(
        InMemoryEvidenceRepository(),
        StubSourceChecker({source_id}),
        StubAreaChecker({area_id}),
    )


def make_evidence(
    *,
    area_id: UUID,
    source_id: UUID,
    evidence_type: EvidenceType,
    observed_value: dict[str, object],
) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=source_id,
        evidence_type=evidence_type,
        evidence_code=f"{evidence_type.value.upper()}_FIXTURE",
        domain="flood",
        observation="Fixture evidence payload.",
        observed_value=observed_value,
        method_code="fixture_payload_validation",
        confidence=ConfidenceBand.MEDIUM,
        caveat="Fixture only.",
    )


def test_source_observation_rejects_empty_payload() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        observed_value={},
    )

    with pytest.raises(ValueError, match="source_observation observed_value"):
        service.create_observation(evidence)


def test_source_observation_rejects_nested_payload() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        observed_value={"raw_value": {"nested": "unsupported"}},
    )

    with pytest.raises(ValueError, match="scalar or list of scalars"):
        service.create_observation(evidence)


def test_source_observation_rejects_unsupported_payload_key() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        observed_value={"freeform": "not allowed"},
    )

    with pytest.raises(ValueError, match="unsupported fields"):
        service.create_observation(evidence)


def test_spatial_intersection_accepts_intersection_payload() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        observed_value={
            "intersects": True,
            "intersection_area_sq_m": 125.5,
            "flood_zone": "AE",
        },
    )

    created = service.create_observation(evidence)

    assert created.observed_value["intersects"] is True


def test_spatial_intersection_accepts_flood_zone_code_result() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        observed_value={"flood_zone_code": "AE"},
    )

    created = service.create_observation(evidence)

    assert created.observed_value["flood_zone_code"] == "AE"


def test_spatial_intersection_rejects_unsupported_payload_key() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        observed_value={"unstructured": "value"},
    )

    with pytest.raises(ValueError, match="unsupported fields"):
        service.create_observation(evidence)


def test_spatial_intersection_rejects_ratio_above_one() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        observed_value={"intersects": True, "intersection_ratio": 1.5},
    )

    with pytest.raises(ValueError, match="less than or equal to 1"):
        service.create_observation(evidence)


def test_derived_metric_accepts_metric_payload() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.DERIVED_METRIC,
        observed_value={
            "metric_code": "slope_percent",
            "value": 8.25,
            "unit": "percent",
        },
    )

    created = service.create_observation(evidence)

    assert created.observed_value["metric_code"] == "slope_percent"


def test_derived_metric_rejects_missing_metric_code() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.DERIVED_METRIC,
        observed_value={"value": 8.25, "unit": "percent"},
    )

    with pytest.raises(ValueError, match="metric_code"):
        service.create_observation(evidence)


def test_derived_metric_rejects_unsupported_payload_key() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.DERIVED_METRIC,
        observed_value={
            "metric_code": "slope_percent",
            "value": 8.25,
            "unit": "percent",
            "freeform": "not allowed",
        },
    )

    with pytest.raises(ValueError, match="unsupported fields"):
        service.create_observation(evidence)


def test_document_extract_accepts_extract_payload() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    evidence = make_evidence(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.DOCUMENT_EXTRACT,
        observed_value={
            "document_id": "fixture-doc-1",
            "extract_text": "County planning note requires floodplain confirmation.",
            "page": 3,
        },
    )

    created = service.create_observation(evidence)

    assert "floodplain" in str(created.observed_value["extract_text"])


def test_source_failure_accepts_structured_failure_payload() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)

    created = service.create_source_failure(
        area_id=area_id,
        source_id=source_id,
        method_code="fixture_fema_request",
        caveat="FEMA fixture endpoint returned 503.",
        domain="flood",
        observed_value={
            "status_code": 503,
            "error_message": "Service unavailable.",
            "retryable": True,
        },
    )

    assert created.observed_value["status_code"] == 503


def test_source_failure_rejects_arbitrary_failure_payload() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)

    with pytest.raises(ValueError, match="unsupported fields"):
        service.create_source_failure(
            area_id=area_id,
            source_id=source_id,
            method_code="fixture_fema_request",
            caveat="FEMA fixture endpoint returned 503.",
            domain="flood",
            observed_value={"raw_response": "not allowed"},
        )


def test_human_note_rejects_arbitrary_payload() -> None:
    area_id = uuid4()
    source_id = uuid4()
    service = make_service(area_id=area_id, source_id=source_id)
    note = EvidenceContract(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.HUMAN_VERIFICATION,
        evidence_code="REVIEW_NOTE",
        domain="review",
        observation="Reviewer noted a follow-up requirement.",
        method_code="human_review_note",
        observed_value={"freeform": "not a controlled payload field"},
        confidence=ConfidenceBand.UNKNOWN,
    )

    with pytest.raises(ValueError, match="human note observed_value"):
        service.create_human_note(note)
