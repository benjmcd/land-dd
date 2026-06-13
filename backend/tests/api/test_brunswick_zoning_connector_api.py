from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.area_contracts import AreaContract
from app.domain.source_contracts import SourceContract
from app.main import create_app

_VALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}


def _zoning_source() -> SourceContract:
    return SourceContract(
        name="Brunswick County UDO Zoning Recorded",
        organization="Brunswick County Planning",
        source_type="Local official",
        domain="Zoning",
        geographic_scope="County",
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
        metadata={"source_registry_id": "DS-023"},
    )


def _area(area_id: object) -> AreaContract:
    return AreaContract(
        area_id=area_id,  # type: ignore[arg-type]
        label="Brunswick zoning API test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-78.40, 34.05],
                    [-78.35, 34.05],
                    [-78.35, 34.10],
                    [-78.40, 34.10],
                    [-78.40, 34.05],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


def _client_with_seeded_services() -> tuple[TestClient, ApiServices, object]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_zoning_source())
    services.area_service.create(_area(area_id))
    return TestClient(app), services, area_id


def test_query_brunswick_zoning_district_requires_auth() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/connector-runs/brunswick-zoning/query-district",
        json={"area_id": str(uuid4()), "zoning_code": "RR"},
    )
    assert response.status_code in (401, 403, 422)


def test_query_brunswick_zoning_district_unregistered_area_returns_422() -> None:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    services.source_service.register(_zoning_source())
    client = TestClient(app)
    missing_id = uuid4()

    response = client.post(
        "/connector-runs/brunswick-zoning/query-district",
        json={"area_id": str(missing_id), "zoning_code": "RR"},
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422
    assert "not registered" in response.json()["detail"]


def test_query_brunswick_zoning_district_returns_202_known_code() -> None:
    client, services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/brunswick-zoning/query-district",
        json={"area_id": str(area_id), "zoning_code": "RR"},
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "brunswick_zoning_udo_recorded"
    assert body["retrieval_status"] == "succeeded"
    assert body["evidence_code"] == "ZONING_USE_CLASSIFICATION"
    assert body["zoning_code"] == "RR"
    assert body["district_name"] == "Rural Low Density Residential"
    assert body["residential_use_screening"] == "ALLOWED_WITH_RESTRICTIONS"
    assert body["source_registry_id"] == "DS-023"


def test_query_brunswick_zoning_district_unknown_code_returns_needs_review() -> None:
    client, services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/brunswick-zoning/query-district",
        json={"area_id": str(area_id), "zoning_code": "XYZ"},
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["evidence_code"] == "ZONING_EVIDENCE_NEEDS_REVIEW"
    assert body["residential_use_screening"] == "NEEDS_REVIEW"


def test_query_brunswick_zoning_district_no_code_returns_unknown() -> None:
    client, services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/brunswick-zoning/query-district",
        json={"area_id": str(area_id)},
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["evidence_code"] == "ZONING_UNKNOWN"
    assert body["residential_use_screening"] == "UNKNOWN"


def test_brunswick_zoning_allowed_district_emits_canonical_rule_engine_key() -> None:
    """RR district (ALLOWED_WITH_RESTRICTIONS) must emit intended_residential_use_allowed=True."""
    client, services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/brunswick-zoning/query-district",
        json={"area_id": str(area_id), "zoning_code": "RR"},
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body.get("intended_residential_use_allowed") is True, (
        "RR (ALLOWED_WITH_RESTRICTIONS) must include intended_residential_use_allowed=True "
        "so the rule engine classifies zoning as allowed; got: " + str(body)
    )
    assert body.get("intended_residential_use_prohibited") is None


def test_brunswick_zoning_industrial_district_emits_canonical_prohibited_key() -> None:
    """C-I (Commercial-Intensive, UNLIKELY_VERIFY) must emit intended_residential_use_prohibited."""
    client, services, area_id = _client_with_seeded_services()

    response = client.post(
        "/connector-runs/brunswick-zoning/query-district",
        json={"area_id": str(area_id), "zoning_code": "C-I"},
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body.get("intended_residential_use_prohibited") is True, (
        "C-I (Commercial-Intensive/UNLIKELY_VERIFY) must include "
        "intended_residential_use_prohibited=True; got: " + str(body)
    )
