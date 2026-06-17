from __future__ import annotations

from urllib.error import URLError
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.core.config import Settings
from app.domain.area_contracts import AreaContract
from app.domain.enums import EvidenceType
from app.domain.source_contracts import SourceContract
from app.main import create_app

_WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
_VALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
    "X-Workspace-Id": str(_WORKSPACE_ID),
    "X-User-Id": str(_USER_ID),
}


def _area(area_id: UUID, *, workspace_id: UUID | None = _WORKSPACE_ID) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        workspace_id=workspace_id,
        label="Chatham parcels API test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-79.40, 35.60],
                    [-79.10, 35.60],
                    [-79.10, 35.80],
                    [-79.40, 35.80],
                    [-79.40, 35.60],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


def _source() -> SourceContract:
    return SourceContract(
        name="Chatham County CAMA Parcels",
        organization="Chatham County GIS",
        source_type="Local official",
        domain="Parcels",
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
        last_checked_at="2026-06-06",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-010"},
    )


def _feature() -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {
            "PIN": "0012345",
            "ACRES": 1.5,
            "ZONING": "RA",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-79.30, 35.65],
                    [-79.25, 35.65],
                    [-79.25, 35.70],
                    [-79.30, 35.70],
                    [-79.30, 35.65],
                ]
            ],
        },
    }


def _body(area_id: UUID) -> dict[str, object]:
    return {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -79.40,
            "ymin": 35.60,
            "xmax": -79.10,
            "ymax": 35.80,
        },
        "max_features": 100,
    }


def _client_with_seeded_services(
    *,
    fetch_payload: dict[str, object] | None = None,
    fetch_error: Exception | None = None,
) -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id))

    def fetch_json(url: str, _timeout_seconds: float) -> dict[str, object]:
        if fetch_error is not None:
            raise fetch_error
        assert fetch_payload is not None
        return fetch_payload

    services.chatham_parcels_fetch_json = fetch_json
    return TestClient(app), services, area_id


def test_chatham_parcels_query_bbox_returns_202_and_persists_evidence() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )

    response = client.post(
        "/connector-runs/chatham-parcels/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "chatham_parcels_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 1
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["source_registry_id"] == "DS-010"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence[0].domain == "parcels"
    assert evidence[0].is_source_failure is False
    assert evidence[0].observed_value.get("parcel_pin") == "0012345"


def test_chatham_parcels_query_bbox_empty_response_emits_source_failure() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )

    response = client.post(
        "/connector-runs/chatham-parcels/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["retrieval_status"] == "failed"
    assert body["source_failure_created_count"] == 1
    assert body["review_required"] is True

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence[0].is_source_failure is True
    assert evidence[0].observed_value.get("failure_reason") == "chatham_parcels_no_features"


def test_chatham_parcels_query_bbox_connection_error_emits_source_failure() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_error=URLError("connection refused"),
    )

    response = client.post(
        "/connector-runs/chatham-parcels/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["retrieval_status"] == "failed"
    assert body["source_failure_created_count"] == 1
    assert body["review_required"] is True

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence[0].observed_value.get("failure_reason") == "chatham_parcels_request_error"


def test_chatham_parcels_query_bbox_rejects_unregistered_area() -> None:
    client, _services, _area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )
    missing_id = uuid4()

    response = client.post(
        "/connector-runs/chatham-parcels/query-bbox",
        json={
            "area_id": str(missing_id),
            "bbox": {"xmin": -79.40, "ymin": 35.60, "xmax": -79.10, "ymax": 35.80},
            "max_features": 10,
        },
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422


def test_chatham_parcels_query_bbox_rejects_missing_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )

    response = client.post(
        "/connector-runs/chatham-parcels/query-bbox",
        json=_body(area_id),
    )

    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Orchestration-loop tests
# ---------------------------------------------------------------------------

def _usgs_tnm_source() -> SourceContract:
    return SourceContract(
        name="USGS The National Map",
        organization="USGS",
        source_type="Public official",
        domain="Terrain/elevation/hydro/boundaries",
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
        last_checked_at="2026-06-06",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-001"},
    )


def _fema_source() -> SourceContract:
    return SourceContract(
        name="FEMA NFHL",
        organization="FEMA",
        source_type="Public official",
        domain="Flood",
        geographic_scope="US",
        license_status="approved-with-restrictions",
        commercial_use_status="restricted",
        redistribution_status="restricted",
        attribution_required=True,
        cache_allowed="restricted",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="restricted",
        freshness_class="current-effective",
        last_checked_at="2026-06-06",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-002"},
    )


def _nwi_source() -> SourceContract:
    return SourceContract(
        name="National Wetlands Inventory",
        organization="USFWS",
        source_type="Public official",
        domain="Wetlands",
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
        last_checked_at="2026-06-06",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-004"},
    )


def _ssurgo_source() -> SourceContract:
    return SourceContract(
        name="USDA Web Soil Survey/SSURGO",
        organization="USDA NRCS",
        source_type="Public official",
        domain="Soils",
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
        last_checked_at="2026-06-06",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-003"},
    )


def _usgs_tnm_payload(elevation_m: float = 120.0) -> dict[str, object]:
    return {
        "location": {"x": -79.14, "y": 35.72, "spatialReference": {"wkid": 4326}},
        "locationId": 0,
        "value": str(elevation_m),
        "rasterId": 1,
        "resolution": 10,
        "attributes": {"AcquisitionDate": "11/3/2022"},
    }


def _ssurgo_table() -> dict[str, object]:
    return {
        "Table": [
            [
                "mukey", "musym", "muname", "cokey", "compname",
                "comppct_r", "majcompflag", "hydricrating",
                "drainagecl", "hydgrp", "slope_r",
            ],
            ["1912968", "30A", "Cecil sandy loam", "27342553", "Cecil",
             "55", "Yes", "No", "Well drained", "B", "5"],
        ]
    }


def _small_area(
    area_id: UUID,
    *,
    workspace_id: UUID | None = _WORKSPACE_ID,
) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        workspace_id=workspace_id,
        label="Chatham small test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-79.15, 35.73],
                    [-79.10, 35.73],
                    [-79.10, 35.78],
                    [-79.15, 35.78],
                    [-79.15, 35.73],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


def _client_with_all_five_connectors(
    *,
    area_id: UUID,
) -> tuple[TestClient, ApiServices]:
    settings = Settings(ENABLE_LIVE_CONNECTORS=True)
    app = create_app(settings=settings)
    services = app.state.services
    assert isinstance(services, ApiServices)

    services.area_service.create(_small_area(area_id))
    services.source_service.register(_usgs_tnm_source())
    services.source_service.register(_fema_source())
    services.source_service.register(_nwi_source())
    services.source_service.register(_ssurgo_source())
    services.source_service.register(_source())  # DS-010 Chatham

    usgs_call = 0

    def fetch_usgs(url: str, _t: float) -> dict[str, object]:
        nonlocal usgs_call
        usgs_call += 1
        return _usgs_tnm_payload(float(usgs_call) * 10.0)

    def fetch_fema(url: str, _t: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": []}

    def fetch_nwi(url: str, _t: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": []}

    def fetch_ssurgo(q: str, _t: float) -> dict[str, object]:
        return _ssurgo_table()

    def fetch_chatham(url: str, _t: float) -> dict[str, object]:
        return {"type": "FeatureCollection", "features": [_feature()]}

    services.usgs_tnm_fetch_json = fetch_usgs
    services.fema_nfhl_fetch_json = fetch_fema
    services.nwi_fetch_json = fetch_nwi
    services.ssurgo_fetch_json = fetch_ssurgo
    services.chatham_parcels_fetch_json = fetch_chatham
    return TestClient(app), services


def _approve(client: TestClient, ingest_run_id: str) -> None:
    r = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert r.status_code == 200


def _report_runs_body(area_id: UUID) -> dict[str, object]:
    return {"area_id": str(area_id), "intent_code": "homestead_feasibility"}


def test_chatham_parcels_is_fifth_connector_in_live_orchestration_sequence() -> None:
    area_id = uuid4()
    client, _ = _client_with_all_five_connectors(area_id=area_id)

    seen_run_ids: set[str] = set()

    # Step through USGS TNM → FEMA → NWI → SSURGO, approving each
    for _step in range(4):
        pending = client.post("/report-runs", json=_report_runs_body(area_id))
        assert pending.status_code == 202
        body = pending.json()
        assert body["status"] == "pending_connector_review"
        run_id = body["connector_ingest_run_id"]
        assert run_id is not None
        assert run_id not in seen_run_ids
        seen_run_ids.add(run_id)
        _approve(client, run_id)

    # 5th request should block on Chatham parcels
    chatham_pending = client.post("/report-runs", json=_report_runs_body(area_id))
    assert chatham_pending.status_code == 202
    chatham_body = chatham_pending.json()
    assert chatham_body["status"] == "pending_connector_review"
    chatham_run_id = chatham_body["connector_ingest_run_id"]
    assert chatham_run_id is not None
    assert chatham_run_id not in seen_run_ids

    # Approve Chatham — now the report should queue
    _approve(client, chatham_run_id)
    final = client.post("/report-runs", json=_report_runs_body(area_id))
    assert final.status_code == 202
    assert final.json()["status"] == "queued"
    assert final.json()["report_run_id"] is not None


def test_chatham_parcels_skipped_in_orchestration_when_ds010_not_registered() -> None:
    area_id = uuid4()
    client, _ = _client_with_all_five_connectors(area_id=area_id)

    # Unregister DS-010 — the helper registered it; clear sources and re-register without it
    # Instead, build a client without DS-010
    settings = Settings(ENABLE_LIVE_CONNECTORS=True)
    app2 = create_app(settings=settings)
    services2 = app2.state.services
    assert isinstance(services2, ApiServices)
    services2.area_service.create(_small_area(area_id))
    services2.source_service.register(_usgs_tnm_source())
    services2.source_service.register(_fema_source())
    services2.source_service.register(_nwi_source())
    services2.source_service.register(_ssurgo_source())
    # DS-010 intentionally not registered

    usgs_call = 0

    def fetch_usgs(url: str, _t: float) -> dict[str, object]:
        nonlocal usgs_call
        usgs_call += 1
        return _usgs_tnm_payload(float(usgs_call) * 10.0)

    services2.usgs_tnm_fetch_json = fetch_usgs
    services2.fema_nfhl_fetch_json = lambda u, t: {"type": "FeatureCollection", "features": []}
    services2.nwi_fetch_json = lambda u, t: {"type": "FeatureCollection", "features": []}
    services2.ssurgo_fetch_json = lambda q, t: _ssurgo_table()
    client2 = TestClient(app2)

    seen_run_ids2: set[str] = set()
    # Approve all 4 connectors
    for _step in range(4):
        pending = client2.post("/report-runs", json=_report_runs_body(area_id))
        assert pending.status_code == 202
        body = pending.json()
        assert body["status"] == "pending_connector_review"
        run_id = body["connector_ingest_run_id"]
        assert run_id not in seen_run_ids2
        seen_run_ids2.add(run_id)
        _approve(client2, run_id)

    # Without DS-010, the 5th request should succeed (report queued, not pending Chatham)
    final = client2.post("/report-runs", json=_report_runs_body(area_id))
    assert final.status_code == 202
    assert final.json()["status"] == "queued"
    assert final.json()["report_run_id"] is not None
