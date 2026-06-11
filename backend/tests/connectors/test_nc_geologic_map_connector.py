from __future__ import annotations

from urllib.error import URLError
from uuid import uuid4

import pytest

from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.nc_geologic_map import (
    NC_GEOLOGIC_MAP_CAVEAT,
    NC_GEOLOGIC_MAP_CONNECTOR_NAME,
    NC_GEOLOGIC_MAP_LAYER_URL,
    NC_GEOLOGIC_MAP_MAX_FEATURES,
    NC_GEOLOGIC_MAP_METHOD_CODE,
    NcGeologicMapBbox,
    NcGeologicMapConnector,
    NcGeologicMapConnectorError,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="State geological survey",
        organization="NC Geological Survey",
        source_type="State official",
        domain="Geology/minerals",
        geographic_scope="North Carolina",
        license_status=license_status,
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        update_cadence="deprecated",
        freshness_class="historical",
        last_checked_at="2026-06-11",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-015"},
    )


def _bbox() -> NcGeologicMapBbox:
    return NcGeologicMapBbox(xmin=-82.45, ymin=35.55, xmax=-82.44, ymax=35.56)


def _feature_payload() -> dict[str, object]:
    return {
        "features": [
            {
                "attributes": {
                    "OBJECTID": 1836,
                    "UnitLabel": "Zatm",
                    "Belt": "Blue Ridge Belt",
                    "Type": "Sedimentary and Metamorphic Rocks",
                    "Formation": "Muscovite-biotite gneiss",
                    "Description": "Locally sulfidic; interlayered with mica schist",
                }
            }
        ]
    }


def test_bbox_rejects_invalid_span() -> None:
    with pytest.raises(NcGeologicMapConnectorError):
        NcGeologicMapBbox(xmin=-82.45, ymin=35.55, xmax=-81.90, ymax=35.56)


def test_query_bbox_emits_geologic_map_context_evidence() -> None:
    area_id = uuid4()
    urls: list[str] = []

    def fetch(url: str, _timeout_seconds: float) -> dict[str, object]:
        urls.append(url)
        return _feature_payload()

    result = NcGeologicMapConnector(source=_source(), fetch_json=fetch).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert result.retrieval_run.connector_name == NC_GEOLOGIC_MAP_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-015"
    assert result.request_url.startswith(NC_GEOLOGIC_MAP_LAYER_URL)
    assert len(urls) == 1

    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "NC_GEOLOGIC_MAP_UNIT_CONTEXT"
    assert evidence.domain == "geology"
    assert evidence.method_code == NC_GEOLOGIC_MAP_METHOD_CODE
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.observed_value["has_geologic_map_context"] is True
    assert evidence.observed_value["geologic_unit_count"] == 1
    assert evidence.observed_value["primary_geologic_unit_label"] == "Zatm"
    assert evidence.observed_value["geologic_hazard_determined"] is False
    assert evidence.observed_value["buildability_determined"] is False


def test_query_bbox_empty_response_succeeds_as_no_context() -> None:
    result = NcGeologicMapConnector(
        source=_source(),
        fetch_json=lambda _url, _timeout_seconds: {"features": []},
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 0
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["has_geologic_map_context"] is False
    assert evidence.observed_value["no_geologic_map_context"] is True
    assert evidence.observed_value["geologic_unit_count"] == 0


def test_query_bbox_service_error_returns_source_failure() -> None:
    result = NcGeologicMapConnector(
        source=_source(),
        fetch_json=lambda _url, _timeout_seconds: {
            "error": {"code": 400, "message": "Invalid query"}
        },
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.evidence_code == "NC_GEOLOGIC_MAP_SOURCE_FAILURE"
    assert evidence.observed_value["failure_reason"] == "nc_geologic_map_service_error"


def test_query_bbox_network_error_returns_source_failure() -> None:
    def fetch_error(_url: str, _timeout_seconds: float) -> dict[str, object]:
        raise URLError("temporary network error")

    result = NcGeologicMapConnector(source=_source(), fetch_json=fetch_error).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].observed_value["failure_reason"] == (
        "nc_geologic_map_request_error"
    )


def test_query_bbox_rejects_excessive_max_features() -> None:
    with pytest.raises(NcGeologicMapConnectorError):
        NcGeologicMapConnector(
            source=_source(),
            fetch_json=lambda _url, _timeout: {"features": []},
        ).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
            max_features=NC_GEOLOGIC_MAP_MAX_FEATURES + 1,
        )


def test_query_bbox_transfer_limit_fails_closed() -> None:
    result = NcGeologicMapConnector(
        source=_source(),
        fetch_json=lambda _url, _timeout_seconds: {
            "exceededTransferLimit": True,
            "features": [],
        },
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].observed_value["failure_reason"] == (
        "nc_geologic_map_response_truncated"
    )


def test_license_guard_blocks_unapproved_source() -> None:
    with pytest.raises(ConnectorLicenseBlockedError):
        NcGeologicMapConnector(source=_source(license_status="blocked")).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
        )


def test_caveat_excludes_hazard_buildability_and_finance_claims() -> None:
    assert "deprecated" in NC_GEOLOGIC_MAP_CAVEAT
    assert "hazard" in NC_GEOLOGIC_MAP_CAVEAT
    assert "buildability" in NC_GEOLOGIC_MAP_CAVEAT
    assert "appraisal" in NC_GEOLOGIC_MAP_CAVEAT
    assert "lending" in NC_GEOLOGIC_MAP_CAVEAT
    assert "insurance" in NC_GEOLOGIC_MAP_CAVEAT
