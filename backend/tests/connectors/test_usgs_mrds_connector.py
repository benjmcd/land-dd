from __future__ import annotations

from urllib.error import URLError
from uuid import uuid4

import pytest

from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.usgs_mrds import (
    USGS_MRDS_CAVEAT,
    USGS_MRDS_CONNECTOR_NAME,
    USGS_MRDS_MAX_FEATURES,
    USGS_MRDS_METHOD_CODE,
    USGS_MRDS_WFS_URL,
    UsgsMrdsBbox,
    UsgsMrdsConnector,
    UsgsMrdsConnectorError,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.source_contracts import SourceContract, SourceRetrievalStatus


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="USGS MRDS",
        organization="USGS",
        source_type="Public/stale official",
        domain="Minerals",
        geographic_scope="US/global selected",
        license_status=license_status,
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        freshness_class="historical",
        last_checked_at="2026-06-11",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-008"},
    )


def _bbox() -> UsgsMrdsBbox:
    return UsgsMrdsBbox(xmin=-117.20, ymin=37.00, xmax=-116.80, ymax=37.40)


def _feature_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:ms="http://mapserver.gis.umn.edu/mapserver"
  xmlns:gml="http://www.opengis.net/gml" xmlns:wfs="http://www.opengis.net/wfs">
  <gml:featureMember>
    <ms:mrds>
      <ms:geometry><gml:Point><gml:coordinates>-116.915600,37.270260</gml:coordinates></gml:Point></ms:geometry>
      <ms:dep_id>10247270</ms:dep_id>
      <ms:site_name>Clarkdale Mine</ms:site_name>
      <ms:dev_stat>Past Producer</ms:dev_stat>
      <ms:url>https://mrdata.usgs.gov/mrds/show-mrds.php?dep_id=10247270</ms:url>
      <ms:code_list>AU AG</ms:code_list>
    </ms:mrds>
  </gml:featureMember>
</wfs:FeatureCollection>
"""


def _empty_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:gml="http://www.opengis.net/gml"
  xmlns:wfs="http://www.opengis.net/wfs">
  <gml:boundedBy><gml:Null>missing</gml:Null></gml:boundedBy>
</wfs:FeatureCollection>
"""


def _wfs_exception_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows">
  <ows:Exception><ows:ExceptionText>Invalid bbox</ows:ExceptionText></ows:Exception>
</ows:ExceptionReport>
"""


def test_bbox_rejects_invalid_span() -> None:
    with pytest.raises(UsgsMrdsConnectorError):
        UsgsMrdsBbox(xmin=-118.0, ymin=37.0, xmax=-116.8, ymax=37.4)


def test_query_bbox_emits_mineral_occurrence_evidence() -> None:
    area_id = uuid4()
    urls: list[str] = []

    def fetch(url: str, _timeout_seconds: float) -> str:
        urls.append(url)
        return _feature_xml()

    result = UsgsMrdsConnector(source=_source(), fetch_text=fetch).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert result.retrieval_run.connector_name == USGS_MRDS_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-008"
    assert result.request_url.startswith(USGS_MRDS_WFS_URL)
    assert len(urls) == 1

    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence.evidence_code == "MRDS_MINERAL_OCCURRENCE_SCREEN"
    assert evidence.domain == "minerals"
    assert evidence.method_code == USGS_MRDS_METHOD_CODE
    assert evidence.confidence == ConfidenceBand.LOW
    assert evidence.observed_value["has_mineral_occurrence_context"] is True
    assert evidence.observed_value["mineral_rights_determined"] is False
    assert evidence.observed_value["mineral_occurrence_count"] == 1
    assert evidence.observed_value["primary_mineral_deposit_id"] == "10247270"
    assert evidence.observed_value["primary_mineral_site_name"] == "Clarkdale Mine"


def test_query_bbox_empty_response_succeeds_as_no_context() -> None:
    result = UsgsMrdsConnector(
        source=_source(),
        fetch_text=lambda _url, _timeout_seconds: _empty_xml(),
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 0
    evidence = result.evidence_inputs[0]
    assert evidence.observed_value["has_mineral_occurrence_context"] is False
    assert evidence.observed_value["no_mineral_occurrence_context"] is True
    assert evidence.observed_value["mineral_occurrence_count"] == 0


def test_query_bbox_wfs_exception_returns_source_failure() -> None:
    result = UsgsMrdsConnector(
        source=_source(),
        fetch_text=lambda _url, _timeout_seconds: _wfs_exception_xml(),
    ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.evidence_code == "USGS_MRDS_SOURCE_FAILURE"
    assert evidence.observed_value["failure_reason"] == "usgs_mrds_request_or_parse_error"


def test_query_bbox_network_error_returns_source_failure() -> None:
    def fetch_error(_url: str, _timeout_seconds: float) -> str:
        raise URLError("temporary network error")

    result = UsgsMrdsConnector(source=_source(), fetch_text=fetch_error).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].observed_value["failure_reason"] == (
        "usgs_mrds_request_or_parse_error"
    )


def test_query_bbox_rejects_excessive_max_features() -> None:
    with pytest.raises(UsgsMrdsConnectorError):
        UsgsMrdsConnector(source=_source(), fetch_text=lambda _url, _timeout: "").query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
            max_features=USGS_MRDS_MAX_FEATURES + 1,
        )


def test_query_bbox_reaching_max_features_fails_closed() -> None:
    result = UsgsMrdsConnector(
        source=_source(),
        fetch_text=lambda _url, _timeout_seconds: _feature_xml(),
    ).query_bbox(area_id=uuid4(), bbox=_bbox(), max_features=1)

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.evidence_inputs[0].observed_value["failure_reason"] == (
        "usgs_mrds_response_may_be_truncated"
    )


def test_license_guard_blocks_unapproved_source() -> None:
    with pytest.raises(ConnectorLicenseBlockedError):
        UsgsMrdsConnector(source=_source(license_status="blocked")).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
        )


def test_caveat_excludes_resource_rights_and_value_claims() -> None:
    assert "mineral rights" in USGS_MRDS_CAVEAT
    assert "resource value" in USGS_MRDS_CAVEAT
    assert "buildability" in USGS_MRDS_CAVEAT
    assert "lending suitability" in USGS_MRDS_CAVEAT
    assert "appraisal" in USGS_MRDS_CAVEAT
    assert "investment suitability" in USGS_MRDS_CAVEAT
