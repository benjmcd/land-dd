from __future__ import annotations

from uuid import uuid4

from app.domain.enums import EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceContract
from app.source_registry.usage_rights import (
    source_production_use_allowed,
    source_report_exposure_allowed,
    source_report_exposure_sensitive_fields,
)


def _reviewed_source(**updates: str) -> SourceContract:
    return SourceContract(
        name="Fixture County GIS",
        organization="Fixture County",
        domain="parcels",
        license_status="approved",
        commercial_use_status="approved",
        redistribution_status="restricted",
        cache_allowed="approved",
        export_allowed="approved-with-restrictions",
        raw_data_allowed="restricted",
        ai_use_allowed="restricted",
        review_status="approved-with-restrictions",
    ).model_copy(update=updates)


def _evidence(
    source: SourceContract,
    observed_value: dict[str, object],
    *,
    is_source_failure: bool = False,
) -> EvidenceContract:
    return EvidenceContract(
        area_id=uuid4(),
        source_id=source.source_id,
        evidence_type=(
            EvidenceType.SOURCE_FAILURE
            if is_source_failure
            else EvidenceType.SPATIAL_INTERSECTION
        ),
        evidence_code=(
            "COUNTY_PARCEL_SOURCE_FAILURE"
            if is_source_failure
            else "COUNTY_PARCEL_SCREEN"
        ),
        domain="parcels",
        observation="Fixture county parcel screening.",
        observed_value=observed_value,
        method_code="fixture_county_parcel",
        is_source_failure=is_source_failure,
    )


def test_restricted_source_still_allows_production_use_readiness() -> None:
    source = _reviewed_source()

    assert source_production_use_allowed(source) is True


def test_restricted_source_allows_non_sensitive_screening_report_exposure() -> None:
    source = _reviewed_source()
    evidence = _evidence(
        source,
        {
            "intersects": True,
            "parcel_count": 1,
            "parcel_county": "Chatham",
            "parcel_zoning": "R-1",
        },
    )

    assert source_report_exposure_allowed(source, evidence) is True


def test_restricted_source_allows_generic_metric_value_report_exposure() -> None:
    source = _reviewed_source(domain="buildability", source_type="Public official")
    evidence = _evidence(
        source,
        {
            "metric_code": "tnm_epqs_sampled_relief_m",
            "value": 14.2,
            "unit": "m",
            "sample_count": 5,
        },
    )

    assert source_report_exposure_allowed(source, evidence) is True


def test_restricted_source_blocks_sensitive_report_exposure() -> None:
    source = _reviewed_source()

    for key in (
        "owner_name",
        "parcel_owner",
        "mailing_address",
        "situs_address",
        "parcel_total_value",
        "parcelTotalValue",
        "marketValue",
        "taxValue",
        "appraisedValue",
        "sale_price",
        "comps_count",
        "raw_vendor_payload",
        "pii_flag",
    ):
        evidence = _evidence(source, {"intersects": True, key: "sensitive"})

        assert source_report_exposure_allowed(source, evidence) is False


def test_restricted_source_blocks_nested_sensitive_report_exposure() -> None:
    source = _reviewed_source()
    evidence = _evidence(
        source,
        {
            "parcel_summary": [
                {
                    "intersects": True,
                    "owner_name": "Fixture Owner",
                    "metrics": {"assessed_value": 250000},
                }
            ]
        },
    )

    assert source_report_exposure_allowed(source, evidence) is False
    assert source_report_exposure_sensitive_fields(evidence) == (
        "parcel_summary.0.metrics.assessed_value",
        "parcel_summary.0.owner_name",
    )


def test_blocked_source_non_failure_evidence_is_not_reportable() -> None:
    source = _reviewed_source(export_allowed="unknown")
    evidence = _evidence(source, {"intersects": True, "parcel_count": 1})

    assert source_production_use_allowed(source) is False
    assert source_report_exposure_allowed(source, evidence) is False


def test_blocked_source_failure_without_sensitive_fields_is_reportable() -> None:
    source = _reviewed_source(export_allowed="blocked")
    evidence = _evidence(
        source,
        {
            "failure_reason": "license_blocked",
            "error_message": "Source rights review blocked live parcel export.",
            "retryable": False,
        },
        is_source_failure=True,
    )

    assert source_production_use_allowed(source) is False
    assert source_report_exposure_allowed(source, evidence) is True
