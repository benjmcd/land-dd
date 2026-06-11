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


def _area(area_id: UUID) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        label="EPA ECHO API test area",
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
        name="EPA ECHO",
        organization="U.S. Environmental Protection Agency",
        source_type="Public official",
        domain="Environmental compliance",
        geographic_scope="US",
        license_status="approved-with-restrictions",
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        attribution_required=True,
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        freshness_class="current-live",
        last_checked_at="2026-06-11",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-006"},
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


def _client_with_seeded_services(
    *,
    fetch_payload: dict[str, object],
) -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id))

    def fetch_json(url: str, _timeout_seconds: float) -> dict[str, object]:
        return fetch_payload

    services.epa_echo_fetch_json = fetch_json
    return TestClient(app), services, area_id


def test_epa_echo_query_bbox_returns_202_with_facilities_found() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={
            "Results": {
                "TotalFacilityCount": "2",
                "FRSFacility": [
                    {"RegistryId": "110000001"},
                    {"RegistryId": "110000002"},
                ],
            }
        },
    )

    response = client.post(
        "/connector-runs/epa-echo/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "epa_echo_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 2
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["source_registry_id"] == "DS-006"
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_OBSERVATION
    assert evidence[0].domain == "env_hazard"


def test_epa_echo_query_bbox_returns_422_for_missing_area() -> None:
    client, _services, _area_id = _client_with_seeded_services(
        fetch_payload={"Results": {"TotalFacilityCount": "0", "FRSFacility": []}},
    )
    body = _body(uuid4())  # unregistered area

    response = client.post(
        "/connector-runs/epa-echo/query-bbox",
        json=body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_epa_echo_query_bbox_returns_422_for_invalid_bbox() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"Results": {"TotalFacilityCount": "0", "FRSFacility": []}},
    )
    bad_body = {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -79.00,
            "ymin": 35.80,
            "xmax": -79.10,  # xmax < xmin
            "ymax": 35.90,
        },
    }

    response = client.post(
        "/connector-runs/epa-echo/query-bbox",
        json=bad_body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_epa_echo_query_bbox_source_registry_id_is_ds006() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={
            "Results": {
                "TotalFacilityCount": "1",
                "FRSFacility": [{"RegistryId": "110000003"}],
            }
        },
    )

    response = client.post(
        "/connector-runs/epa-echo/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    assert response.json()["source_registry_id"] == "DS-006"


def test_epa_echo_query_bbox_no_facilities_returns_succeeded() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={
            "Results": {
                "TotalFacilityCount": "0",
                "FRSFacility": [],
            }
        },
    )

    response = client.post(
        "/connector-runs/epa-echo/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 0
    assert body["evidence_created_count"] == 1

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].observed_value.get("no_env_hazard_proximity") is True


def test_epa_echo_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"Results": {"TotalFacilityCount": "0", "FRSFacility": []}},
    )

    response = client.post(
        "/connector-runs/epa-echo/query-bbox",
        json=_body(area_id),
    )

    assert response.status_code == 401
