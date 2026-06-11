from __future__ import annotations

from collections.abc import Mapping
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


def _area(area_id: UUID) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        label="NOAA Climate API test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-79.10, 35.80],
                    [-79.00, 35.80],
                    [-79.00, 35.90],
                    [-79.10, 35.90],
                    [-79.10, 35.80],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


def _source() -> SourceContract:
    return SourceContract(
        name="NOAA climate/weather",
        organization="NOAA",
        source_type="Public official",
        domain="Climate/weather",
        geographic_scope="US",
        license_status="approved-with-restrictions",
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
        metadata={"source_registry_id": "DS-020"},
    )


def _body(area_id: UUID) -> dict[str, object]:
    return {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -79.10,
            "ymin": 35.80,
            "xmax": -79.00,
            "ymax": 35.90,
        },
    }


def _nws_points_payload() -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {
            "cwa": "RAH",
            "forecastZone": "https://api.weather.gov/zones/forecast/NCZ087",
            "timeZone": "America/New_York",
            "radarStation": "KRAX",
            "relativeLocation": {
                "type": "Feature",
                "properties": {"city": "Pittsboro", "state": "NC"},
            },
        },
    }


def _nws_zone_payload() -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {"name": "Southern Chatham County"},
    }


class _TwoCallFetch:
    """Returns points response on first call, zone response on second."""

    def __init__(self) -> None:
        self._calls = 0

    def __call__(self, url: str, timeout: float) -> Mapping[str, object]:
        self._calls += 1
        if self._calls == 1:
            return _nws_points_payload()
        return _nws_zone_payload()


def _client_with_seeded_services(
    *,
    fetch: _TwoCallFetch | None = None,
) -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id))
    services.noaa_climate_fetch_json = fetch or _TwoCallFetch()
    return TestClient(app), services, area_id


def test_noaa_climate_query_bbox_returns_202_with_nws_zone() -> None:
    client, services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/noaa-climate/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "noaa_nws_climate_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 1
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["source_registry_id"] == "DS-020"
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence[0].domain == "climate"
    assert evidence[0].observed_value["has_nws_coverage"] is True


def test_noaa_climate_query_bbox_returns_422_for_missing_area() -> None:
    client, _services, _area_id = _client_with_seeded_services()
    body = _body(uuid4())  # unregistered area

    response = client.post(
        "/connector-runs/noaa-climate/query-bbox",
        json=body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_noaa_climate_query_bbox_rejects_oversized_bbox() -> None:
    client, _services, area_id = _client_with_seeded_services()
    bad_body = {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -82.00,
            "ymin": 35.00,
            "xmax": -79.00,  # 3 degree span > 1.0 limit
            "ymax": 35.90,
        },
    }

    response = client.post(
        "/connector-runs/noaa-climate/query-bbox",
        json=bad_body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_noaa_climate_query_bbox_source_registry_id_is_ds020() -> None:
    client, _services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/noaa-climate/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    assert response.json()["source_registry_id"] == "DS-020"


def test_noaa_climate_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/noaa-climate/query-bbox",
        json=_body(area_id),
    )

    assert response.status_code == 401


def test_noaa_climate_query_bbox_request_url_in_response() -> None:
    client, _services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/noaa-climate/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    assert "api.weather.gov" in response.json()["request_url"]
