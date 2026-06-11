from __future__ import annotations

from uuid import UUID

from pydantic import HttpUrl

from app.connectors.brunswick_zoning_recorded import (
    BRUNSWICK_ZONING_CONNECTOR_NAME,
    BRUNSWICK_ZONING_UDO_EFFECTIVE,
    BrunswickZoningRecordedConnector,
)
from app.domain.enums import AuthorityLevel, ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus

_AREA_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
_SOURCE_ID = UUID("66666666-6666-4666-8666-666666666666")


def _make_source() -> SourceContract:
    return SourceContract(
        source_id=_SOURCE_ID,
        name="Local zoning ordinance PDFs",
        organization="County/municipality",
        domain="Zoning/legal text",
        homepage_url=HttpUrl("https://www.brunswickcountync.gov/"),
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


def test_known_rural_residential_district_returns_classification_evidence() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="RR", source=source)

    assert result.retrieval_run.connector_name == BRUNSWICK_ZONING_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert len(result.evidence_inputs) == 1
    evidence = result.evidence_inputs[0]
    assert evidence.domain == "zoning"
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.is_source_failure is False
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.observed_value["zoning_code"] == "RR"
    assert evidence.observed_value["district_name"] == "Rural Low Density Residential"
    assert evidence.observed_value["use_category"] == "rural_low_density_residential"
    assert evidence.observed_value["residential_use_screening"] == "ALLOWED_WITH_RESTRICTIONS"
    assert evidence.source_date == BRUNSWICK_ZONING_UDO_EFFECTIVE


def test_multifamily_residential_returns_allowed_with_restrictions() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="MR-3200", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "ALLOWED_WITH_RESTRICTIONS"
    assert evidence.observed_value["district_name"] == "Multifamily Residential"
    assert evidence.is_source_failure is False


def test_commercial_intensive_returns_unlikely_verify_screening() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="C-I", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "UNLIKELY_VERIFY"
    assert evidence.is_source_failure is False


def test_industrial_general_returns_unlikely_verify_screening() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="I-G", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "UNLIKELY_VERIFY"
    assert evidence.observed_value["district_name"] == "Industrial-General"


def test_neighborhood_commercial_returns_needs_review_screening() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="N-C", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "NEEDS_REVIEW"


def test_conservation_protection_returns_unlikely_verify() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="CP", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "UNLIKELY_VERIFY"
    assert evidence.observed_value["district_name"] == "Conservation and Protection"


def test_overlay_planned_development_returns_needs_review() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="PD", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "NEEDS_REVIEW"
    assert evidence.observed_value["district_name"] == "Planned Development"


def test_water_quality_protection_overlay_returns_needs_review() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="WQP", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION"
    assert evidence.observed_value["residential_use_screening"] == "NEEDS_REVIEW"


def test_unknown_zoning_code_returns_needs_review_not_source_failure() -> None:
    connector = BrunswickZoningRecordedConnector()
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
    connector = BrunswickZoningRecordedConnector()
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
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="", source=source)

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_code == "ZONING_UNKNOWN"
    assert evidence.is_source_failure is False


def test_zoning_code_is_case_insensitive() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result_upper = connector.query_district(area_id=_AREA_ID, zoning_code="RR", source=source)
    result_lower = connector.query_district(area_id=_AREA_ID, zoning_code="rr", source=source)

    assert result_upper.evidence_inputs[0].evidence_code == "ZONING_USE_CLASSIFICATION"
    assert result_lower.evidence_inputs[0].evidence_code == "ZONING_USE_CLASSIFICATION"
    assert (
        result_upper.evidence_inputs[0].observed_value["district_name"]
        == result_lower.evidence_inputs[0].observed_value["district_name"]
    )


def test_evidence_ids_are_deterministic_for_same_inputs() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result1 = connector.query_district(area_id=_AREA_ID, zoning_code="RR", source=source)
    result2 = connector.query_district(area_id=_AREA_ID, zoning_code="RR", source=source)

    assert result1.evidence_inputs[0].evidence_id == result2.evidence_inputs[0].evidence_id
    assert result1.retrieval_run.ingest_run_id == result2.retrieval_run.ingest_run_id


def test_evidence_always_carries_caveat() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    for code in ["RR", "C-I", "XYZ-UNKNOWN", None]:
        result = connector.query_district(area_id=_AREA_ID, zoning_code=code, source=source)
        assert result.evidence_inputs[0].caveat
        assert "verify" in result.evidence_inputs[0].caveat.lower()


def test_retrieval_run_has_udo_provenance() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    result = connector.query_district(area_id=_AREA_ID, zoning_code="RR", source=source)

    metrics = result.retrieval_run.metrics
    assert metrics["udo_effective"] == BRUNSWICK_ZONING_UDO_EFFECTIVE
    assert metrics["lookup_type"] == "recorded_fixture"
    assert metrics["source_registry_id"] == "DS-023"


def test_all_base_districts_are_known() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    base_districts = ["RR", "R-7500", "R-6000", "SBR-6000", "MR-3200", "C-LD", "N-C", "C-I", "RU-I", "I-G", "MI", "CP"]  # noqa: E501
    for code in base_districts:
        result = connector.query_district(area_id=_AREA_ID, zoning_code=code, source=source)
        evidence = result.evidence_inputs[0]
        assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION", (
            f"Expected ZONING_USE_CLASSIFICATION for district {code!r}, "
            f"got {evidence.evidence_code!r}"
        )


def test_all_overlay_districts_are_known() -> None:
    connector = BrunswickZoningRecordedConnector()
    source = _make_source()

    overlay_districts = ["CZ", "ED", "PD", "TO", "WQP"]
    for code in overlay_districts:
        result = connector.query_district(area_id=_AREA_ID, zoning_code=code, source=source)
        evidence = result.evidence_inputs[0]
        assert evidence.evidence_code == "ZONING_USE_CLASSIFICATION", (
            f"Expected ZONING_USE_CLASSIFICATION for overlay {code!r}, "
            f"got {evidence.evidence_code!r}"
        )
