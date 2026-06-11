from __future__ import annotations

from urllib.error import URLError
from uuid import uuid4

import pytest

from app.connectors.census_tiger import (
    CENSUS_TIGER_CAVEAT,
    CENSUS_TIGER_CONNECTOR_NAME,
    CENSUS_TIGER_MAX_FEATURES,
    CENSUS_TIGER_METHOD_CODE,
    CENSUS_TIGER_SERVICE_URL,
    CensusTigerBbox,
    CensusTigerConnector,
    CensusTigerConnectorError,
)
from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="Census TIGER/ACS",
        organization="Census",
        source_type="Public official",
        domain="Boundaries/demographics",
        geographic_scope="US",
        license_status=license_status,
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        attribution_required=True,
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        freshness_class="current-effective",
        last_checked_at="2026-06-11",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-022"},
    )


def _bbox() -> CensusTigerBbox:
    return CensusTigerBbox(xmin=-79.10, ymin=35.80, xmax=-79.00, ymax=35.90)


def _tract_payload() -> dict[str, object]:
    return {
        "features": [
            {
                "attributes": {
                    "GEOID": "37037020105",
                    "NAME": "Census Tract 201.05",
                    "STATE": "37",
                    "COUNTY": "037",
                    "TRACT": "020105",
                }
            }
        ]
    }


def _block_group_payload() -> dict[str, object]:
    return {
        "features": [
            {
                "attributes": {
                    "GEOID": "370370201051",
                    "NAME": "Block Group 1",
                    "STATE": "37",
                    "COUNTY": "037",
                    "TRACT": "020105",
                    "BLKGRP": "1",
                }
            }
        ]
    }


class _TwoLayerFetch:
    def __init__(
        self,
        *,
        tracts: dict[str, object] | None = None,
        block_groups: dict[str, object] | None = None,
    ) -> None:
        self.tracts = tracts or _tract_payload()
        self.block_groups = block_groups or _block_group_payload()
        self.urls: list[str] = []

    def __call__(self, url: str, _timeout_seconds: float) -> dict[str, object]:
        self.urls.append(url)
        if "/0/query" in url:
            return self.tracts
        if "/1/query" in url:
            return self.block_groups
        raise AssertionError(f"unexpected layer URL: {url}")


def test_bbox_rejects_invalid_span() -> None:
    with pytest.raises(CensusTigerConnectorError):
        CensusTigerBbox(xmin=-80.0, ymin=35.8, xmax=-79.0, ymax=35.9)


def test_query_bbox_emits_geography_context_evidence() -> None:
    area_id = uuid4()
    fetch = _TwoLayerFetch()

    result = CensusTigerConnector(source=_source(), fetch_json=fetch).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert result.retrieval_run.connector_name == CENSUS_TIGER_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 2
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-022"
    assert result.request_url.startswith(CENSUS_TIGER_SERVICE_URL)
    assert len(fetch.urls) == 2

    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "CENSUS_TIGER_GEOGRAPHY_CONTEXT"
    assert evidence.domain == "census_geography"
    assert evidence.method_code == CENSUS_TIGER_METHOD_CODE
    assert evidence.confidence == ConfidenceBand.MEDIUM
    assert evidence.observed_value["has_census_geography_context"] is True
    assert evidence.observed_value["census_tract_count"] == 1
    assert evidence.observed_value["census_block_group_count"] == 1
    assert evidence.observed_value["primary_census_tract_geoid"] == "37037020105"
    assert evidence.observed_value["primary_census_block_group_geoid"] == "370370201051"
    assert evidence.observed_value["census_demographics_used"] is False


def test_query_bbox_empty_layers_succeeds_with_low_confidence() -> None:
    result = CensusTigerConnector(
        source=_source(),
        fetch_json=_TwoLayerFetch(
            tracts={"features": []},
            block_groups={"features": []},
        ),
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 0
    evidence = result.evidence_inputs[0]
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.observed_value["has_census_geography_context"] is False
    assert evidence.observed_value["census_tract_geoids"] == []


def test_query_bbox_transfer_limit_returns_source_failure() -> None:
    result = CensusTigerConnector(
        source=_source(),
        fetch_json=_TwoLayerFetch(tracts={"features": [], "exceededTransferLimit": True}),
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.evidence_code == "CENSUS_TIGER_SOURCE_FAILURE"
    assert evidence.observed_value["failure_reason"] == "census_tiger_response_truncated"
    assert evidence.observed_value["retryable"] is False


def test_query_bbox_malformed_payload_returns_source_failure() -> None:
    result = CensusTigerConnector(
        source=_source(),
        fetch_json=_TwoLayerFetch(tracts={"unexpected": []}),
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].observed_value["failure_reason"] == (
        "census_tiger_malformed_response"
    )


def test_query_bbox_network_error_returns_source_failure() -> None:
    def fetch_error(_url: str, _timeout_seconds: float) -> dict[str, object]:
        raise URLError("temporary network error")

    result = CensusTigerConnector(source=_source(), fetch_json=fetch_error).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].observed_value["failure_reason"] == (
        "census_tiger_request_error"
    )


def test_query_bbox_rejects_excessive_max_features() -> None:
    with pytest.raises(CensusTigerConnectorError):
        CensusTigerConnector(source=_source(), fetch_json=_TwoLayerFetch()).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
            max_features=CENSUS_TIGER_MAX_FEATURES + 1,
        )


def test_license_guard_blocks_unapproved_source() -> None:
    with pytest.raises(ConnectorLicenseBlockedError):
        CensusTigerConnector(source=_source(license_status="blocked")).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
        )


def test_caveat_excludes_acs_demographic_scoring() -> None:
    assert "does not use ACS demographic variables" in CENSUS_TIGER_CAVEAT
    assert "residential steering" in CENSUS_TIGER_CAVEAT
