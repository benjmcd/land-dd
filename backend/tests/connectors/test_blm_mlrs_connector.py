from __future__ import annotations

from urllib.error import URLError
from uuid import uuid4

import pytest

from app.connectors.blm_mlrs import (
    BLM_MLRS_CAVEAT,
    BLM_MLRS_CONNECTOR_NAME,
    BLM_MLRS_LAYER_URL,
    BLM_MLRS_MAX_FEATURES,
    BLM_MLRS_METHOD_CODE,
    BlmMlrsBbox,
    BlmMlrsConnector,
    BlmMlrsConnectorError,
)
from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="BLM MLRS",
        organization="BLM",
        source_type="Public official",
        domain="Mineral/land records",
        geographic_scope="Federal lands/US",
        license_status=license_status,
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        update_cadence="continuous",
        freshness_class="current-effective",
        last_checked_at="2026-06-11",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-007"},
    )


def _bbox() -> BlmMlrsBbox:
    return BlmMlrsBbox(xmin=-118.0, ymin=37.0, xmax=-117.5, ymax=37.5)


def _feature_payload() -> dict[str, object]:
    return {
        "features": [
            {
                "attributes": {
                    "OBJECTID": 4601950,
                    "CSE_NR": "NV105228507",
                    "LEG_CSE_NR": "",
                    "CSE_NAME": "Rosemalis Mine",
                    "CSE_DISP": "Active",
                    "CSE_TYPE_NR": "384101",
                    "BLM_PROD": "Lode Claim",
                    "QLTY": "0: 25 sections retrieved",
                    "RCRD_ACRS": 20.66115702,
                }
            }
        ]
    }


def test_bbox_rejects_invalid_span() -> None:
    with pytest.raises(BlmMlrsConnectorError):
        BlmMlrsBbox(xmin=-118.0, ymin=37.0, xmax=-117.4, ymax=37.5)


def test_query_bbox_emits_active_mining_claim_context_evidence() -> None:
    area_id = uuid4()
    urls: list[str] = []

    def fetch(url: str, _timeout_seconds: float) -> dict[str, object]:
        urls.append(url)
        return _feature_payload()

    result = BlmMlrsConnector(source=_source(), fetch_json=fetch).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert result.retrieval_run.connector_name == BLM_MLRS_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-007"
    assert result.request_url.startswith(BLM_MLRS_LAYER_URL)
    assert len(urls) == 1

    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "BLM_MLRS_ACTIVE_MINING_CLAIM_CONTEXT"
    assert evidence.domain == "minerals"
    assert evidence.method_code == BLM_MLRS_METHOD_CODE
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.observed_value["has_blm_active_mining_claim_context"] is True
    assert evidence.observed_value["mineral_rights_determined"] is False
    assert evidence.observed_value["blm_active_mining_claim_count"] == 1
    assert evidence.observed_value["primary_blm_mlrs_case_serial_number"] == (
        "NV105228507"
    )
    assert evidence.observed_value["primary_blm_mlrs_case_name"] == "Rosemalis Mine"
    assert evidence.observed_value["blm_mlrs_recorded_acres"] == [20.66115702]


def test_query_bbox_empty_response_succeeds_as_no_context() -> None:
    result = BlmMlrsConnector(
        source=_source(),
        fetch_json=lambda _url, _timeout_seconds: {"features": []},
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 0
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["has_blm_active_mining_claim_context"] is False
    assert evidence.observed_value["no_blm_active_mining_claim_context"] is True
    assert evidence.observed_value["blm_active_mining_claim_count"] == 0


def test_query_bbox_service_error_returns_source_failure() -> None:
    result = BlmMlrsConnector(
        source=_source(),
        fetch_json=lambda _url, _timeout_seconds: {
            "error": {"code": 400, "message": "Invalid query"}
        },
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.evidence_code == "BLM_MLRS_SOURCE_FAILURE"
    assert evidence.observed_value["failure_reason"] == "blm_mlrs_service_error"


def test_query_bbox_network_error_returns_source_failure() -> None:
    def fetch_error(_url: str, _timeout_seconds: float) -> dict[str, object]:
        raise URLError("temporary network error")

    result = BlmMlrsConnector(source=_source(), fetch_json=fetch_error).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].observed_value["failure_reason"] == (
        "blm_mlrs_request_error"
    )


def test_query_bbox_rejects_excessive_max_features() -> None:
    with pytest.raises(BlmMlrsConnectorError):
        BlmMlrsConnector(
            source=_source(),
            fetch_json=lambda _url, _timeout: {"features": []},
        ).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
            max_features=BLM_MLRS_MAX_FEATURES + 1,
        )


def test_query_bbox_transfer_limit_fails_closed() -> None:
    result = BlmMlrsConnector(
        source=_source(),
        fetch_json=lambda _url, _timeout_seconds: {
            "exceededTransferLimit": True,
            "features": [],
        },
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].observed_value["failure_reason"] == (
        "blm_mlrs_response_truncated"
    )


def test_query_bbox_malformed_feature_returns_source_failure() -> None:
    result = BlmMlrsConnector(
        source=_source(),
        fetch_json=lambda _url, _timeout_seconds: {"features": [{"attributes": {}}]},
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].observed_value["failure_reason"] == (
        "blm_mlrs_malformed_response"
    )


def test_license_guard_blocks_unapproved_source() -> None:
    with pytest.raises(ConnectorLicenseBlockedError):
        BlmMlrsConnector(source=_source(license_status="blocked")).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
        )


def test_caveat_excludes_mineral_rights_title_hazards_and_finance_claims() -> None:
    assert "private mineral rights" in BLM_MLRS_CAVEAT
    assert "claim-boundary" in BLM_MLRS_CAVEAT
    assert "title status" in BLM_MLRS_CAVEAT
    assert "mine hazards" in BLM_MLRS_CAVEAT
    assert "resource value" in BLM_MLRS_CAVEAT
    assert "buildability" in BLM_MLRS_CAVEAT
    assert "appraisal" in BLM_MLRS_CAVEAT
    assert "lending suitability" in BLM_MLRS_CAVEAT
    assert "investment suitability" in BLM_MLRS_CAVEAT
