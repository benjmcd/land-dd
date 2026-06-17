from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.area_contracts import AreaContract
from app.domain.enums import EvidenceType
from app.domain.source_contracts import SourceContract
from app.main import create_app

_VALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}
_WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
_VALID_HEADERS.update(
    {
        "X-Workspace-Id": str(_WORKSPACE_ID),
        "X-User-Id": str(_USER_ID),
    }
)


def _area(area_id: UUID, *, workspace_id: UUID | None = _WORKSPACE_ID) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        workspace_id=workspace_id,
        label="USGS MRDS API test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-117.20, 37.00],
                    [-116.80, 37.00],
                    [-116.80, 37.40],
                    [-117.20, 37.40],
                    [-117.20, 37.00],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


def _source() -> SourceContract:
    return SourceContract(
        name="USGS MRDS",
        organization="USGS",
        source_type="Public/stale official",
        domain="Minerals",
        geographic_scope="US/global selected",
        license_status="approved-with-restrictions",
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


def _body(area_id: UUID) -> dict[str, object]:
    return {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -117.20,
            "ymin": 37.00,
            "xmax": -116.80,
            "ymax": 37.40,
        },
    }


def _feature_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:ms="http://mapserver.gis.umn.edu/mapserver"
  xmlns:gml="http://www.opengis.net/gml" xmlns:wfs="http://www.opengis.net/wfs">
  <gml:featureMember>
    <ms:mrds>
      <ms:dep_id>10247270</ms:dep_id>
      <ms:site_name>Clarkdale Mine</ms:site_name>
      <ms:dev_stat>Past Producer</ms:dev_stat>
      <ms:url>https://mrdata.usgs.gov/mrds/show-mrds.php?dep_id=10247270</ms:url>
      <ms:code_list>AU AG</ms:code_list>
    </ms:mrds>
  </gml:featureMember>
</wfs:FeatureCollection>
"""


def _client_with_seeded_services() -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id))
    services.usgs_mrds_fetch_text = lambda _url, _timeout_seconds: _feature_xml()
    return TestClient(app), services, area_id


def test_usgs_mrds_query_bbox_returns_202_with_mineral_context() -> None:
    client, services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/usgs-mrds/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "usgs_mrds_mineral_occurrence_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 1
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["source_registry_id"] == "DS-008"
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence[0].domain == "minerals"
    assert evidence[0].observed_value["primary_mineral_deposit_id"] == "10247270"
    assert evidence[0].observed_value["mineral_rights_determined"] is False


def test_usgs_mrds_query_bbox_returns_422_for_missing_area() -> None:
    client, _services, _area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/usgs-mrds/query-bbox",
        json=_body(uuid4()),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_usgs_mrds_query_bbox_rejects_oversized_bbox() -> None:
    client, _services, area_id = _client_with_seeded_services()
    bad_body = {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -118.00,
            "ymin": 37.00,
            "xmax": -116.80,
            "ymax": 37.40,
        },
    }

    response = client.post(
        "/connector-runs/usgs-mrds/query-bbox",
        json=bad_body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_usgs_mrds_query_bbox_rejects_excessive_max_features() -> None:
    client, _services, area_id = _client_with_seeded_services()
    body = _body(area_id)
    body["max_features"] = 51

    response = client.post(
        "/connector-runs/usgs-mrds/query-bbox",
        json=body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_usgs_mrds_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/usgs-mrds/query-bbox",
        json=_body(area_id),
    )

    assert response.status_code == 401


def test_usgs_mrds_query_bbox_request_url_in_response() -> None:
    client, _services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/usgs-mrds/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    assert "mrdata.usgs.gov" in response.json()["request_url"]
