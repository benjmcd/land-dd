from __future__ import annotations

from uuid import UUID

from pydantic import HttpUrl

from app.connectors.chatham_zoning_recorded import (
    CHATHAM_ZONING_CONNECTOR_NAME,
    CHATHAM_ZONING_UDO_EFFECTIVE,
    ChathamZoningRecordedConnector,
    _CHATHAM_UDO_DISTRICTS,
)
from app.domain.enums import AuthorityLevel, ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus

_AREA_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_SOURCE_ID = UUID("55555555-5555-4555-8555-555555555555")


def _make_source() -> SourceContract:
    return SourceContract(
        source_id=_SOURCE_ID,
        name="Local zoning ordinance PDFs",
        organization="County/municipality",
        domain="Zoning/legal text",
        homepage_url=HttpUrl("https://www.chathamcountync.gov/"),
        authority_level=AuthorityLevel.OFFICIAL_PRIMARY,
        license_status="approved-with-restrictions",
        commercial_use_status="approved-with-restrictions",
        redistribution_status="restricted",
        cache_allowed="restricted",
        export_allowed="restricted",
        raw_data_allowed="restricted",
        ai_use_allowed="restricted",
        review_status="approved-with-restrictions",
        metadata={
            "source_registry_id": "DS-023",
            "mvp_priority": "Must",
        },
    )


def test_known_agricultural_district_returns_classification_evidence() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="RA", source=source)

    assert result.retrieval_run.connector_name == CHATHAM_ZONING_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.domain == "zoning"
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.is_source_failure is False
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.observed_value["zoning_code"] == "RA"
    assert evidence.observed_value["district_name"] == "Rural Agricultural"
    assert evidence.observed_value["use_category"] == "agricultural_low_intensity_residential"
    assert evidence.observed_value["residential_use_screening"] == "ALLOWED_WITH_RESTRICTIONS"
    assert evidence.source_date == CHATHAM_ZONING_UDO_EFFECTIVE


def test_known_residential_district_returns_allowed_screening() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="R-1", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "ALLOWED_WITH_RESTRICTIONS"
    assert evidence.is_source_failure is False


def test_industrial_district_returns_unlikely_verify_screening() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="I", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "UNLIKELY_VERIFY"
    assert evidence.is_source_failure is False


def test_commercial_district_returns_needs_review_screening() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="B-1", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "NEEDS_REVIEW"


def test_unknown_zoning_code_returns_needs_review_not_source_failure() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(
        area_id=_AREA_ID, zoning_code="XYZ-UNKNOWN", source=source
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_EVIDENCE_NEEDS_REVIEW"
    assert evidence.is_source_failure is False
    assert evidence.confidence == ConfidenceBand.UNKNOWN
    assert evidence.observed_value["zoning_code"] == "XYZ-UNKNOWN"
    assert evidence.observed_value["district_name"] is None


def test_none_zoning_code_returns_unknown_evidence() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code=None, source=source)

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_UNKNOWN"
    assert evidence.is_source_failure is False
    assert evidence.confidence == ConfidenceBand.UNKNOWN
    assert evidence.observed_value["zoning_code"] is None
    assert evidence.observed_value["residential_use_screening"] == "UNKNOWN"


def test_empty_string_zoning_code_returns_unknown() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_UNKNOWN"
    assert evidence.is_source_failure is False


def test_zoning_code_is_case_insensitive() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result_upper = connector.query_district(area_id=_AREA_ID, zoning_code="RA", source=source)
    result_lower = connector.query_district(area_id=_AREA_ID, zoning_code="ra", source=source)

    assert result_upper.evidence_inputs[0].evidence_code == "ZONING_USE_CLASSIFICATION"
    assert result_lower.evidence_inputs[0].evidence_code == "ZONING_USE_CLASSIFICATION"
    assert (
        result_upper.evidence_inputs[0].observed_value["district_name"]
        == result_lower.evidence_inputs[0].observed_value["district_name"]
    )


def test_evidence_ids_are_deterministic_for_same_inputs() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result1 = connector.query_district(area_id=_AREA_ID, zoning_code="RA", source=source)
    result2 = connector.query_district(area_id=_AREA_ID, zoning_code="RA", source=source)

    assert result1.evidence_inputs[0].evidence_id == result2.evidence_inputs[0].evidence_id
    assert result1.retrieval_run.ingest_run_id == result2.retrieval_run.ingest_run_id


def test_unzoned_district_returns_needs_review() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(
        area_id=_AREA_ID, zoning_code="UNZONED", source=source
    )

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "NEEDS_REVIEW"


def test_evidence_always_carries_caveat() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    for code in ["RA", "I", "XYZ-UNKNOWN", None]:
        result = connector.query_district(area_id=_AREA_ID, zoning_code=code, source=source)
        assert result.evidence_inputs[0].caveat
        assert "verify" in result.evidence_inputs[0].caveat.lower()


def test_retrieval_run_has_udo_provenance() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="RA", source=source)

    metrics = result.retrieval_run.metrics
    assert metrics["udo_effective"] == CHATHAM_ZONING_UDO_EFFECTIVE
    assert metrics["lookup_type"] == "recorded_fixture"
    assert metrics["source_registry_id"] == "DS-023"


def test_planned_development_returns_needs_review() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="PD", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "NEEDS_REVIEW"


def test_all_districts_are_known() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    for code in _CHATHAM_UDO_DISTRICTS:
        result = connector.query_district(area_id=_AREA_ID, zoning_code=code, source=source)
        evidence = result.evidence_inputs[0]
        assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION", (
            f"Expected ZONING_USE_CLASSIFICATION for district {code!r}, "
            f"got {evidence.evidence_code!r}"
        )
        assert evidence.observed_value["district_name"] is not None
        assert evidence.observed_value["use_category"] is not None


def test_all_residential_districts_have_consistent_screening() -> None:
    connector = ChathamZoningRecordedConnector()
    source = _make_source()

    residential_codes = ["RA", "RR", "R-1", "R-2", "R-3", "MHP"]
    for code in residential_codes:
        result = connector.query_district(area_id=_AREA_ID, zoning_code=code, source=source)
        evidence = result.evidence_inputs[0]
        assert evidence.observed_value["residential_use_screening"] == "ALLOWED_WITH_RESTRICTIONS", (
            f"Expected ALLOWED_WITH_RESTRICTIONS for residential district {code!r}, "
            f"got {evidence.observed_value['residential_use_screening']!r}"
        )

    industrial_codes = ["I", "I-1", "I-2"]
    for code in industrial_codes:
        result = connector.query_district(area_id=_AREA_ID, zoning_code=code, source=source)
        evidence = result.evidence_inputs[0]
        assert evidence.observed_value["residential_use_screening"] == "UNLIKELY_VERIFY", (
            f"Expected UNLIKELY_VERIFY for industrial district {code!r}, "
            f"got {evidence.observed_value['residential_use_screening']!r}"
        )
