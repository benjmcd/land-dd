from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, Request
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import ApiServices, create_db_api_services, get_services
from app.api.live_connector_jobs import run_next_live_connector_job
from app.claims_engine.not_evaluated import NOT_EVALUATED_SOURCE_NAME, NOT_EVALUATED_SOURCE_ORG
from app.connectors.live_jobs import LIVE_CONNECTOR_JOB_TYPE
from app.core.config import Settings
from app.db.engine import build_engine
from app.db.session import get_db_session
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
        label="FEMA NFHL API test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-77.10, 38.80],
                    [-77.00, 38.80],
                    [-77.00, 38.90],
                    [-77.10, 38.90],
                    [-77.10, 38.80],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


def _source() -> SourceContract:
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
        last_checked_at="2026-06-05",
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
        last_checked_at="2026-06-05",
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
        last_checked_at="2026-06-05",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-003"},
    )


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
        last_checked_at="2026-06-05",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-001"},
    )


def _usgs_tnm_payload(elevation_m: float) -> dict[str, object]:
    return {
        "location": {
            "x": -77.05,
            "y": 38.85,
            "spatialReference": {"wkid": 4326, "latestWkid": 4326},
        },
        "locationId": 0,
        "value": str(elevation_m),
        "rasterId": 20689,
        "resolution": 1,
        "attributes": {"AcquisitionDate": "11/3/2022"},
    }


def _feature() -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {
            "OBJECTID": 42,
            "FLD_ZONE": "AE",
            "ZONE_SUBTY": "RIVERINE FLOODPLAIN",
            "SFHA_TF": "T",
            "SOURCE_CIT": "11001C_STUDY",
            "GlobalID": "{global-42}",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-77.05, 38.82],
                    [-77.03, 38.82],
                    [-77.03, 38.84],
                    [-77.05, 38.84],
                    [-77.05, 38.82],
                ]
            ],
        },
    }


def _nwi_feature() -> dict[str, object]:
    return {
        "type": "Feature",
        "id": 2808733,
        "properties": {
            "Wetlands.OBJECTID": 2808733,
            "Wetlands.ATTRIBUTE": "L1UBH",
            "Wetlands.WETLAND_TYPE": "Lake",
            "Wetlands.ACRES": 106.82272375751111,
            "Wetlands.GLOBALID": "{3FE208B5-9945-4564-B466-FF415177DE3B}",
            "NWI_Wetland_Codes.SYSTEM_NAME": "Lacustrine",
            "NWI_Wetland_Codes.CLASS_NAME": "Unconsolidated Bottom",
            "NWI_Wetland_Codes.WATER_REGIME_NAME": "Permanently Flooded",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-77.05, 38.82],
                    [-77.03, 38.82],
                    [-77.03, 38.84],
                    [-77.05, 38.84],
                    [-77.05, 38.82],
                ]
            ],
        },
    }


def _ssurgo_table() -> dict[str, object]:
    return {
        "Table": [
            [
                "mukey",
                "musym",
                "muname",
                "cokey",
                "compname",
                "comppct_r",
                "majcompflag",
                "hydricrating",
                "drainagecl",
                "hydgrp",
                "slope_r",
            ],
            [
                "1912968",
                "30A",
                "Codorus and Hatboro soils, 0 to 2 percent slopes, occasionally flooded",
                "27342553",
                "Codorus",
                "55",
                "Yes",
                "No",
                "Somewhat poorly drained",
                "B/D",
                "1",
            ],
        ]
    }


def _body(area_id: UUID) -> dict[str, object]:
    return {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -77.10,
            "ymin": 38.80,
            "xmax": -77.00,
            "ymax": 38.90,
        },
        "max_features": 1,
    }


def _sequence_body(area_id: UUID) -> dict[str, object]:
    body = _body(area_id)
    body["max_sample_points"] = 2
    body["max_rows"] = 1
    return body


def _client_with_seeded_services(
    *,
    fetch_payload: dict[str, object],
    settings: Settings | None = None,
    fetch_urls: list[str] | None = None,
    usgs_tnm_fetch_urls: list[str] | None = None,
    nwi_fetch_payload: dict[str, object] | None = None,
    nwi_fetch_urls: list[str] | None = None,
    ssurgo_fetch_payload: dict[str, object] | None = None,
    ssurgo_fetch_queries: list[str] | None = None,
) -> tuple[TestClient, ApiServices, UUID]:
    app = create_app(settings=settings)
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id))

    def fetch_json(url: str, _timeout_seconds: float) -> dict[str, object]:
        if fetch_urls is not None:
            fetch_urls.append(url)
        return fetch_payload

    services.fema_nfhl_fetch_json = fetch_json
    if settings is not None and settings.enable_live_connectors:
        services.source_service.register(_usgs_tnm_source())
        usgs_elevations = [9.0, 13.0]
        usgs_call_count = 0

        def fetch_usgs_tnm_json(url: str, _timeout_seconds: float) -> dict[str, object]:
            nonlocal usgs_call_count
            if usgs_tnm_fetch_urls is not None:
                usgs_tnm_fetch_urls.append(url)
            elevation = usgs_elevations[usgs_call_count % len(usgs_elevations)]
            usgs_call_count += 1
            return _usgs_tnm_payload(elevation)

        services.usgs_tnm_fetch_json = fetch_usgs_tnm_json
    if nwi_fetch_payload is not None:
        services.source_service.register(_nwi_source())

        def fetch_nwi_json(url: str, _timeout_seconds: float) -> dict[str, object]:
            if nwi_fetch_urls is not None:
                nwi_fetch_urls.append(url)
            return nwi_fetch_payload

        services.nwi_fetch_json = fetch_nwi_json
    if ssurgo_fetch_payload is not None:
        services.source_service.register(_ssurgo_source())

        def fetch_ssurgo_json(query: str, _timeout_seconds: float) -> dict[str, object]:
            if ssurgo_fetch_queries is not None:
                ssurgo_fetch_queries.append(query)
            return ssurgo_fetch_payload

        services.ssurgo_fetch_json = fetch_ssurgo_json
    return TestClient(app), services, area_id


def _db_client_with_fetcher(
    *,
    fetch_payload: dict[str, object],
    tmp_path: Path,
    enable_live_connectors: bool = False,
    fetch_urls: list[str] | None = None,
    usgs_tnm_fetch_urls: list[str] | None = None,
) -> TestClient:
    settings = Settings(
        OBJECT_STORE_ROOT=str(tmp_path / "object-store"),
        ENABLE_LIVE_CONNECTORS=enable_live_connectors,
    )
    app = create_app(settings=settings, use_db_services=True)

    def fetch_json(url: str, _timeout_seconds: float) -> dict[str, object]:
        if fetch_urls is not None:
            fetch_urls.append(url)
        return fetch_payload

    def db_services_with_fetcher(
        request: Request,
        session: Annotated[Session, Depends(get_db_session)],
    ) -> Iterator[ApiServices]:
        try:
            services = create_db_api_services(
                session,
                object_store_root=str(request.app.state.object_store_root),
                settings=settings,
            )
            services.fema_nfhl_fetch_json = fetch_json
            if enable_live_connectors:
                usgs_elevations = [9.0, 13.0]
                usgs_call_count = 0

                def fetch_usgs_tnm_json(
                    url: str,
                    _timeout_seconds: float,
                ) -> dict[str, object]:
                    nonlocal usgs_call_count
                    if usgs_tnm_fetch_urls is not None:
                        usgs_tnm_fetch_urls.append(url)
                    elevation = usgs_elevations[usgs_call_count % len(usgs_elevations)]
                    usgs_call_count += 1
                    return _usgs_tnm_payload(elevation)

                services.usgs_tnm_fetch_json = fetch_usgs_tnm_json
            yield services
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_services] = db_services_with_fetcher
    return TestClient(app)


def test_fema_nfhl_query_bbox_persists_spatial_evidence_and_review_queue() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )

    response = client.post(
        "/connector-runs/fema-nfhl/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "fema_nfhl_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 1
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"
    assert body["queue_name"] == "connector-quality-review"
    assert body["source_registry_id"] == "DS-002"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence[0].observed_value["flood_zone_code"] == "AE"

    status_response = client.get(
        f"/connector-runs/{body['ingest_run_id']}/review-status",
    )
    assert status_response.status_code == 200
    assert status_response.json()["disposition"] == "ready_for_connector_qa"

    queue_response = client.get(
        f"/connector-runs/{body['ingest_run_id']}/review-queue",
    )
    assert queue_response.status_code == 200
    assert queue_response.json()["status"] == "queued"


def test_fema_nfhl_schedule_bbox_enqueues_without_fetch_or_report() -> None:
    fetch_urls: list[str] = []
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        fetch_urls=fetch_urls,
    )

    response = client.post(
        "/connector-runs/fema-nfhl/schedule-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["area_id"] == str(area_id)
    assert body["source_registry_id"] == "DS-002"
    assert body["connector_name"] == "fema_nfhl_live"
    assert body["connector_ingest_run_id"] is None
    assert fetch_urls == []
    assert services.evidence_service.list_by_area(area_id) == []

    result = run_next_live_connector_job(
        services=services,
        worker_id="live-worker-1",
    )

    assert result is not None
    assert result.succeeded is True
    assert result.connector_result is not None
    assert result.job.status.value == "succeeded"
    assert result.job.connector_ingest_run_id == result.connector_result.ingest_run_id
    assert result.job.connector_review_status == "queued"
    assert len(fetch_urls) == 1
    queue_item = services.connector_review_queue.get_by_ingest_run_id(
        result.connector_result.ingest_run_id,
    )
    assert queue_item is not None
    assert queue_item.status.value == "queued"


def test_fema_nfhl_schedule_bbox_rejects_reviewer_without_connector_run_scope() -> None:
    fetch_urls: list[str] = []
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        fetch_urls=fetch_urls,
        settings=Settings(
            REVIEWER_ACCOUNTS="reviewer:reviewer-token",
            REVIEWER_ACCOUNT_SCOPES="reviewer:connector:review",
        ),
    )

    response = client.post(
        "/connector-runs/fema-nfhl/schedule-bbox",
        json=_body(area_id),
        headers={
            "X-Reviewer-Id": "reviewer",
            "X-Reviewer-Token": "reviewer-token",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "reviewer scope is required: connector:run"
    assert fetch_urls == []


def test_live_connector_sequence_schedule_bbox_enqueues_ordered_jobs_without_fetch_or_report(
) -> None:
    fetch_urls: list[str] = []
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        fetch_urls=fetch_urls,
    )

    response = client.post(
        "/connector-runs/live-sequence/schedule-bbox",
        json=_sequence_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["area_id"] == str(area_id)
    assert body["policy_id"] == "reviewed_live_sequence_ds001_ds002_ds004_ds003_v1"
    jobs = body["jobs"]
    assert [job["source_registry_id"] for job in jobs] == [
        "DS-001",
        "DS-002",
        "DS-004",
        "DS-003",
    ]
    assert [job["connector_name"] for job in jobs] == [
        "usgs_tnm_elevation_live",
        "fema_nfhl_live",
        "nwi_live",
        "ssurgo_live",
    ]
    assert {job["status"] for job in jobs} == {"queued"}
    assert all(job["area_id"] == str(area_id) for job in jobs)
    assert all(job["connector_ingest_run_id"] is None for job in jobs)
    assert all(job["connector_review_status"] is None for job in jobs)
    assert all("report_run_id" not in job["payload"] for job in jobs)
    assert fetch_urls == []
    assert services.evidence_service.list_by_area(area_id) == []

    repeated = client.post(
        "/connector-runs/live-sequence/schedule-bbox",
        json=_sequence_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert repeated.status_code == 202
    assert [job["job_id"] for job in repeated.json()["jobs"]] == [
        job["job_id"] for job in jobs
    ]


def test_live_connector_sequence_schedule_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )

    response = client.post(
        "/connector-runs/live-sequence/schedule-bbox",
        json=_sequence_body(area_id),
    )

    assert response.status_code == 401


def test_live_connector_sequence_schedule_bbox_rejects_unregistered_area() -> None:
    client, _services, _area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )
    missing_area_id = uuid4()

    response = client.post(
        "/connector-runs/live-sequence/schedule-bbox",
        json=_sequence_body(missing_area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == f"Area '{missing_area_id}' is not registered"


def test_approved_fema_nfhl_connector_run_feeds_report_api() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )
    connector_response = client.post(
        "/connector-runs/fema-nfhl/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )
    assert connector_response.status_code == 202
    ingest_run_id = connector_response.json()["ingest_run_id"]

    approval_response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert approval_response.status_code == 200
    assert approval_response.json()["new_status"] == "succeeded"

    create_report_response = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
    )
    assert create_report_response.status_code == 202
    report_run_id = create_report_response.json()["report_run_id"]

    report_response = client.get(f"/report-runs/{report_run_id}")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["status"] == "succeeded"
    assert "FLOOD_001" in {claim["claim_code"] for claim in report["claims"]}
    assert "FLOOD_001" in {claim["claim_code"] for claim in report["red_flags"]}
    connector_evidence = [
        record
        for record in report["evidence"]
        if record["source_ingest_run_id"] == ingest_run_id
    ]
    assert len(connector_evidence) == 1
    assert connector_evidence[0]["observed_value"] == {
        "flood_zone_code": "AE",
        "intersects": True,
    }


def test_live_connector_report_run_pauses_for_connector_review() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        settings=Settings(ENABLE_LIVE_CONNECTORS=True),
    )

    response = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending_connector_review"
    assert body["report_run_id"] is None
    assert body["connector_ingest_run_id"] is not None
    assert body["connector_review_status"] == "queued"

    review_response = client.get(
        f"/connector-runs/{body['connector_ingest_run_id']}/review-queue",
    )
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "queued"


def test_live_connector_report_run_waits_for_ds001_ds002_ds004_ds003_then_reports() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        nwi_fetch_payload={"type": "FeatureCollection", "features": [_nwi_feature()]},
        ssurgo_fetch_payload=_ssurgo_table(),
        settings=Settings(ENABLE_LIVE_CONNECTORS=True),
    )
    pending = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
    )
    assert pending.status_code == 202
    usgs_tnm_ingest_run_id = pending.json()["connector_ingest_run_id"]

    approval = client.post(
        f"/connector-runs/{usgs_tnm_ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert approval.status_code == 200

    fema_pending = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
    )
    assert fema_pending.status_code == 202
    fema_pending_body = fema_pending.json()
    assert fema_pending_body["status"] == "pending_connector_review"
    assert fema_pending_body["report_run_id"] is None
    fema_ingest_run_id = fema_pending_body["connector_ingest_run_id"]
    assert fema_ingest_run_id is not None
    assert fema_ingest_run_id != usgs_tnm_ingest_run_id

    fema_approval = client.post(
        f"/connector-runs/{fema_ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert fema_approval.status_code == 200

    nwi_pending = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
    )
    assert nwi_pending.status_code == 202
    nwi_pending_body = nwi_pending.json()
    assert nwi_pending_body["status"] == "pending_connector_review"
    assert nwi_pending_body["report_run_id"] is None
    nwi_ingest_run_id = nwi_pending_body["connector_ingest_run_id"]
    assert nwi_ingest_run_id is not None
    assert nwi_ingest_run_id not in {usgs_tnm_ingest_run_id, fema_ingest_run_id}

    nwi_approval = client.post(
        f"/connector-runs/{nwi_ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert nwi_approval.status_code == 200

    ssurgo_pending = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
    )
    assert ssurgo_pending.status_code == 202
    ssurgo_pending_body = ssurgo_pending.json()
    assert ssurgo_pending_body["status"] == "pending_connector_review"
    assert ssurgo_pending_body["report_run_id"] is None
    ssurgo_ingest_run_id = ssurgo_pending_body["connector_ingest_run_id"]
    assert ssurgo_ingest_run_id is not None
    assert ssurgo_ingest_run_id not in {
        usgs_tnm_ingest_run_id,
        fema_ingest_run_id,
        nwi_ingest_run_id,
    }

    ssurgo_approval = client.post(
        f"/connector-runs/{ssurgo_ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert ssurgo_approval.status_code == 200

    response = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["report_run_id"] is not None
    report = client.get(f"/report-runs/{body['report_run_id']}").json()
    assert report["status"] == "succeeded"
    claim_codes = {claim["claim_code"] for claim in report["claims"]}
    assert "FLOOD_001" in claim_codes
    assert "WETLAND_001" in claim_codes
    assert "SOIL_NOT_EVALUATED" in claim_codes
    assert "BUILDABILITY_001" not in claim_codes
    soil_claim = next(
        claim for claim in report["claims"] if claim["claim_code"] == "SOIL_NOT_EVALUATED"
    )
    assert soil_claim["severity"] == "unknown"
    assert "screening only" in soil_claim["user_safe_language"]
    assert "does not determine septic approval" in soil_claim["user_safe_language"]
    ssurgo_evidence = [
        record
        for record in report["evidence"]
        if record["source_ingest_run_id"] == ssurgo_ingest_run_id
    ]
    assert len(ssurgo_evidence) == 1
    assert ssurgo_evidence[0]["domain"] == "soil_septic"
    assert ssurgo_evidence[0]["observed_value"]["intersects_soil_mapunit"] is True
    usgs_tnm_evidence = [
        record
        for record in report["evidence"]
        if record["source_ingest_run_id"] == usgs_tnm_ingest_run_id
    ]
    assert len(usgs_tnm_evidence) == 1
    assert usgs_tnm_evidence[0]["domain"] == "buildability"
    assert usgs_tnm_evidence[0]["observed_value"]["metric_code"] == (
        "tnm_epqs_sampled_relief_m"
    )


def test_live_connector_report_resume_requires_approval() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        settings=Settings(ENABLE_LIVE_CONNECTORS=True),
    )
    pending = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
    )
    assert pending.status_code == 202
    ingest_run_id = pending.json()["connector_ingest_run_id"]

    response = client.post(
        f"/connector-runs/{ingest_run_id}/report-runs",
        json={"intent_code": "homestead_feasibility"},
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "connector review item is not approved for report generation"
    )


def test_live_connector_report_resume_after_approval_does_not_refetch() -> None:
    usgs_tnm_fetch_urls: list[str] = []
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        settings=Settings(ENABLE_LIVE_CONNECTORS=True),
        usgs_tnm_fetch_urls=usgs_tnm_fetch_urls,
    )
    pending = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
    )
    assert pending.status_code == 202
    ingest_run_id = pending.json()["connector_ingest_run_id"]
    assert len(usgs_tnm_fetch_urls) == 5

    approval = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert approval.status_code == 200

    response = client.post(
        f"/connector-runs/{ingest_run_id}/report-runs",
        json={"intent_code": "homestead_feasibility"},
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["connector_ingest_run_id"] == ingest_run_id
    assert len(usgs_tnm_fetch_urls) == 5
    report = client.get(f"/report-runs/{body['report_run_id']}").json()
    assert report["status"] == "succeeded"
    assert "FLOOD_001" not in {claim["claim_code"] for claim in report["claims"]}
    connector_evidence = [
        record
        for record in report["evidence"]
        if record["source_ingest_run_id"] == ingest_run_id
    ]
    assert len(connector_evidence) == 1
    assert connector_evidence[0]["domain"] == "buildability"


def test_live_connector_intake_pauses_for_connector_review() -> None:
    client, _services, _area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        settings=Settings(ENABLE_LIVE_CONNECTORS=True),
    )

    response = client.post(
        "/intake",
        json={
            "area_geojson": _area(uuid4()).geom_geojson,
            "intent_code": "homestead_feasibility",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending_connector_review"
    assert body["area_id"] is not None
    assert body["report_run_id"] is None
    assert body["connector_ingest_run_id"] is not None
    assert body["connector_review_status"] == "queued"


def test_live_connector_intake_can_continue_through_ds001_ds002_ds004_ds003_report_flow() -> None:
    client, _services, _area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        nwi_fetch_payload={"type": "FeatureCollection", "features": [_nwi_feature()]},
        ssurgo_fetch_payload=_ssurgo_table(),
        settings=Settings(ENABLE_LIVE_CONNECTORS=True),
    )

    intake_response = client.post(
        "/intake",
        json={
            "area_geojson": _area(uuid4()).geom_geojson,
            "intent_code": "homestead_feasibility",
        },
    )
    assert intake_response.status_code == 202
    intake = intake_response.json()
    assert intake["status"] == "pending_connector_review"
    area_id = intake["area_id"]
    usgs_tnm_ingest_run_id = intake["connector_ingest_run_id"]
    assert usgs_tnm_ingest_run_id is not None

    usgs_tnm_approval = client.post(
        f"/connector-runs/{usgs_tnm_ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert usgs_tnm_approval.status_code == 200

    fema_pending_response = client.post(
        "/report-runs",
        json={
            "area_id": area_id,
            "intent_code": "homestead_feasibility",
        },
    )
    assert fema_pending_response.status_code == 202
    fema_pending = fema_pending_response.json()
    assert fema_pending["status"] == "pending_connector_review"
    assert fema_pending["report_run_id"] is None
    fema_ingest_run_id = fema_pending["connector_ingest_run_id"]
    assert fema_ingest_run_id is not None
    assert fema_ingest_run_id != usgs_tnm_ingest_run_id

    fema_approval = client.post(
        f"/connector-runs/{fema_ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert fema_approval.status_code == 200

    nwi_pending_response = client.post(
        "/report-runs",
        json={
            "area_id": area_id,
            "intent_code": "homestead_feasibility",
        },
    )
    assert nwi_pending_response.status_code == 202
    nwi_pending = nwi_pending_response.json()
    assert nwi_pending["status"] == "pending_connector_review"
    assert nwi_pending["report_run_id"] is None
    nwi_ingest_run_id = nwi_pending["connector_ingest_run_id"]
    assert nwi_ingest_run_id is not None
    assert nwi_ingest_run_id not in {usgs_tnm_ingest_run_id, fema_ingest_run_id}

    nwi_approval = client.post(
        f"/connector-runs/{nwi_ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert nwi_approval.status_code == 200

    ssurgo_pending_response = client.post(
        "/report-runs",
        json={
            "area_id": area_id,
            "intent_code": "homestead_feasibility",
        },
    )
    assert ssurgo_pending_response.status_code == 202
    ssurgo_pending = ssurgo_pending_response.json()
    assert ssurgo_pending["status"] == "pending_connector_review"
    assert ssurgo_pending["report_run_id"] is None
    ssurgo_ingest_run_id = ssurgo_pending["connector_ingest_run_id"]
    assert ssurgo_ingest_run_id is not None
    assert ssurgo_ingest_run_id not in {
        usgs_tnm_ingest_run_id,
        fema_ingest_run_id,
        nwi_ingest_run_id,
    }

    ssurgo_approval = client.post(
        f"/connector-runs/{ssurgo_ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert ssurgo_approval.status_code == 200

    report_response = client.post(
        "/report-runs",
        json={
            "area_id": area_id,
            "intent_code": "homestead_feasibility",
        },
    )
    assert report_response.status_code == 202
    report_body = report_response.json()
    assert report_body["status"] == "queued"
    assert report_body["report_run_id"] is not None

    report = client.get(f"/report-runs/{report_body['report_run_id']}").json()
    assert report["status"] == "succeeded"
    claim_codes = {claim["claim_code"] for claim in report["claims"]}
    assert "FLOOD_001" in claim_codes
    assert "WETLAND_001" in claim_codes
    assert "SOIL_NOT_EVALUATED" in claim_codes
    assert "BUILDABILITY_001" not in claim_codes
    usgs_tnm_evidence = [
        record
        for record in report["evidence"]
        if record["source_ingest_run_id"] == usgs_tnm_ingest_run_id
    ]
    assert len(usgs_tnm_evidence) == 1
    assert usgs_tnm_evidence[0]["domain"] == "buildability"


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_fema_nfhl_approval_feeds_report_api(tmp_path: Path) -> None:
    engine = build_engine()
    client = _db_client_with_fetcher(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        tmp_path=tmp_path,
    )
    report_run_id: UUID | None = None
    ingest_run_id: UUID | None = None
    area_id: UUID | None = None
    ds001_snapshot: dict[str, object] | None = None
    ds002_snapshot: dict[str, object] | None = None
    sentinel_preexisting = _sentinel_source_exists()
    ds001_snapshot = _refresh_ds001_for_db_test()
    ds002_snapshot = _refresh_ds002_for_db_test()

    try:
        area_response = client.post(
            "/areas",
            json=_area(uuid4()).model_dump(mode="json"),
        )
        assert area_response.status_code == 201
        area_id = UUID(area_response.json()["area_id"])

        connector_response = client.post(
            "/connector-runs/fema-nfhl/query-bbox",
            json=_body(area_id),
            headers=_VALID_HEADERS,
        )
        assert connector_response.status_code == 202
        ingest_run_id = UUID(connector_response.json()["ingest_run_id"])

        approval_response = client.post(
            f"/connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa",
            headers=_VALID_HEADERS,
        )
        assert approval_response.status_code == 200
        assert approval_response.json()["new_status"] == "succeeded"

        create_report_response = client.post(
            "/report-runs",
            json={
                "area_id": str(area_id),
                "intent_code": "homestead_feasibility",
            },
        )
        assert create_report_response.status_code == 202
        report_run_id = UUID(create_report_response.json()["report_run_id"])

        report_response = client.get(f"/report-runs/{report_run_id}")
        assert report_response.status_code == 200
        report = report_response.json()
        assert report["status"] == "succeeded"
        assert "FLOOD_001" in {claim["claim_code"] for claim in report["claims"]}
        connector_evidence = [
            record
            for record in report["evidence"]
            if record["source_ingest_run_id"] == str(ingest_run_id)
        ]
        assert len(connector_evidence) == 1
        assert connector_evidence[0]["observed_value"] == {
            "flood_zone_code": "AE",
            "intersects": True,
        }

        with Session(engine) as session:
            queue_row = session.execute(
                text(
                    """
                    SELECT status::text AS status, payload
                    FROM jobs.job_queue
                    WHERE idempotency_key = :idempotency_key
                    """
                ),
                {
                    "idempotency_key": f"connector_review_status:{ingest_run_id}",
                },
            ).mappings().one()
            evidence_count = session.execute(
                text(
                    """
                    SELECT count(*)
                    FROM evidence.observations
                    WHERE area_id = :area_id
                        AND metadata->>'source_ingest_run_id' = :ingest_run_id
                    """
                ),
                {"area_id": area_id, "ingest_run_id": str(ingest_run_id)},
            ).scalar_one()

        assert queue_row["status"] == "succeeded"
        assert queue_row["payload"]["review_decision"]["action"] == (
            "approve_for_connector_qa"
        )
        assert evidence_count == 1
    finally:
        _cleanup_db_fema_report_flow(
            area_id=area_id,
            ingest_run_id=ingest_run_id,
            report_run_id=report_run_id,
            delete_sentinel_source=not sentinel_preexisting,
            ds001_snapshot=ds001_snapshot,
            ds002_snapshot=ds002_snapshot,
        )


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_live_connector_report_run_waits_for_approval_then_reports(
    tmp_path: Path,
) -> None:
    engine = build_engine()
    usgs_tnm_fetch_urls: list[str] = []
    client = _db_client_with_fetcher(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        tmp_path=tmp_path,
        enable_live_connectors=True,
        usgs_tnm_fetch_urls=usgs_tnm_fetch_urls,
    )
    report_run_id: UUID | None = None
    ingest_run_id: UUID | None = None
    area_id: UUID | None = None
    ds001_snapshot: dict[str, object] | None = None
    ds002_snapshot: dict[str, object] | None = None
    sentinel_preexisting = _sentinel_source_exists()
    ds001_snapshot = _refresh_ds001_for_db_test()
    ds002_snapshot = _refresh_ds002_for_db_test()

    try:
        area_response = client.post(
            "/areas",
            json=_area(uuid4()).model_dump(mode="json"),
        )
        assert area_response.status_code == 201
        area_id = UUID(area_response.json()["area_id"])

        pending_response = client.post(
            "/report-runs",
            json={
                "area_id": str(area_id),
                "intent_code": "homestead_feasibility",
            },
        )
        assert pending_response.status_code == 202
        pending = pending_response.json()
        assert pending["status"] == "pending_connector_review"
        assert pending["report_run_id"] is None
        ingest_run_id = UUID(pending["connector_ingest_run_id"])
        assert pending["connector_review_status"] == "queued"
        assert len(usgs_tnm_fetch_urls) == 5

        with Session(engine) as session:
            report_job_count = session.execute(
                text(
                    """
                    SELECT count(*)
                    FROM jobs.job_queue
                    WHERE job_type = 'report_run'
                        AND payload->>'area_id' = :area_id
                    """
                ),
                {"area_id": str(area_id)},
            ).scalar_one()
        assert report_job_count == 0

        approval_response = client.post(
            f"/connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa",
            headers=_VALID_HEADERS,
        )
        assert approval_response.status_code == 200

        report_response = client.post(
            f"/connector-runs/{ingest_run_id}/report-runs",
            json={"intent_code": "homestead_feasibility"},
            headers=_VALID_HEADERS,
        )
        assert report_response.status_code == 202
        report_run_id = UUID(report_response.json()["report_run_id"])
        assert report_response.json()["connector_ingest_run_id"] == str(ingest_run_id)
        assert len(usgs_tnm_fetch_urls) == 5

        fetched_response = client.get(f"/report-runs/{report_run_id}")
        assert fetched_response.status_code == 200
        fetched = fetched_response.json()
        assert fetched["status"] == "succeeded"
        assert "FLOOD_001" not in {claim["claim_code"] for claim in fetched["claims"]}
        connector_evidence = [
            record
            for record in fetched["evidence"]
            if record["source_ingest_run_id"] == str(ingest_run_id)
        ]
        assert len(connector_evidence) == 1
        assert connector_evidence[0]["domain"] == "buildability"
    finally:
        _cleanup_db_fema_report_flow(
            area_id=area_id,
            ingest_run_id=ingest_run_id,
            report_run_id=report_run_id,
            delete_sentinel_source=not sentinel_preexisting,
            ds001_snapshot=ds001_snapshot,
            ds002_snapshot=ds002_snapshot,
        )


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_live_connector_scheduler_enqueues_and_runs_without_report_job(
    tmp_path: Path,
) -> None:
    engine = build_engine()
    fetch_urls: list[str] = []
    client = _db_client_with_fetcher(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        tmp_path=tmp_path,
        fetch_urls=fetch_urls,
    )
    live_job_id: UUID | None = None
    ingest_run_id: UUID | None = None
    area_id: UUID | None = None
    ds002_snapshot: dict[str, object] | None = None
    sentinel_preexisting = _sentinel_source_exists()
    ds002_snapshot = _refresh_ds002_for_db_test()
    settings = Settings(OBJECT_STORE_ROOT=str(tmp_path / "object-store"))

    try:
        area_response = client.post(
            "/areas",
            json=_area(uuid4()).model_dump(mode="json"),
        )
        assert area_response.status_code == 201
        area_id = UUID(area_response.json()["area_id"])

        schedule_response = client.post(
            "/connector-runs/fema-nfhl/schedule-bbox",
            json=_body(area_id),
            headers=_VALID_HEADERS,
        )
        assert schedule_response.status_code == 202
        scheduled = schedule_response.json()
        live_job_id = UUID(scheduled["job_id"])
        assert scheduled["status"] == "queued"
        assert fetch_urls == []

        with Session(engine) as session:
            services = create_db_api_services(
                session,
                object_store_root=str(tmp_path / "object-store"),
                settings=settings,
            )

            def fetch_json(url: str, _timeout_seconds: float) -> dict[str, object]:
                fetch_urls.append(url)
                return {"type": "FeatureCollection", "features": [_feature()]}

            services.fema_nfhl_fetch_json = fetch_json
            result = run_next_live_connector_job(
                services=services,
                worker_id="db-live-worker-1",
            )
            session.commit()

        assert result is not None
        assert result.succeeded is True
        assert result.connector_result is not None
        ingest_run_id = result.connector_result.ingest_run_id
        assert len(fetch_urls) == 1

        with Session(engine) as session:
            live_job = session.execute(
                text(
                    """
                    SELECT status::text AS status, payload
                    FROM jobs.job_queue
                    WHERE job_id = :job_id
                    """
                ),
                {"job_id": str(live_job_id)},
            ).mappings().one()
            review_job = session.execute(
                text(
                    """
                    SELECT status::text AS status, payload
                    FROM jobs.job_queue
                    WHERE idempotency_key = :idempotency_key
                    """
                ),
                {"idempotency_key": f"connector_review_status:{ingest_run_id}"},
            ).mappings().one()
            report_job_count = session.execute(
                text(
                    """
                    SELECT count(*)
                    FROM jobs.job_queue
                    WHERE job_type = 'report_run'
                        AND payload->>'area_id' = :area_id
                    """
                ),
                {"area_id": str(area_id)},
            ).scalar_one()

        assert live_job["status"] == "succeeded"
        assert live_job["payload"]["connector_ingest_run_id"] == str(ingest_run_id)
        assert live_job["payload"]["connector_review_status"] == "queued"
        assert review_job["status"] == "queued"
        assert review_job["payload"]["ingest_run_id"] == str(ingest_run_id)
        assert report_job_count == 0
    finally:
        _cleanup_db_fema_report_flow(
            area_id=area_id,
            ingest_run_id=ingest_run_id,
            report_run_id=None,
            live_job_id=live_job_id,
            delete_sentinel_source=not sentinel_preexisting,
            ds002_snapshot=ds002_snapshot,
        )


def test_fema_nfhl_query_bbox_persists_source_failure_for_empty_response() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )

    response = client.post(
        "/connector-runs/fema-nfhl/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["retrieval_status"] == "failed"
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 1
    assert body["review_required"] is True
    assert body["queue_item_status"] == "needs_review"
    assert body["queue_name"] == "connector-human-review"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence[0].observed_value["failure_reason"] == "fema_nfhl_no_features"

    status_response = client.get(
        f"/connector-runs/{body['ingest_run_id']}/review-status",
    )
    assert status_response.status_code == 200
    assert status_response.json()["signal_codes"] == [
        "retrieval_not_succeeded",
        "retrieval_errors_present",
        "source_failure_evidence_present",
    ]


def test_fema_nfhl_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )

    response = client.post("/connector-runs/fema-nfhl/query-bbox", json=_body(area_id))

    assert response.status_code == 401


def test_fema_nfhl_query_bbox_returns_409_when_ds002_is_not_registered() -> None:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.area_service.create(_area(area_id))
    client = TestClient(app)

    response = client.post(
        "/connector-runs/fema-nfhl/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "source registry id DS-002 is not registered"


def test_fema_nfhl_query_bbox_rejects_oversized_bbox() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )
    body = _body(area_id)
    body["bbox"] = {"xmin": -77.0, "ymin": 38.0, "xmax": -75.8, "ymax": 38.5}

    response = client.post(
        "/connector-runs/fema-nfhl/query-bbox",
        json=body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "bbox longitude span exceeds FEMA NFHL limit"


def _sentinel_source_exists() -> bool:
    engine = build_engine()
    with Session(engine) as session:
        return (
            session.execute(
                text(
                    """
                    SELECT 1
                    FROM source.sources
                    WHERE name = :name
                        AND organization = :organization
                    LIMIT 1
                    """
                ),
                {
                    "name": NOT_EVALUATED_SOURCE_NAME,
                    "organization": NOT_EVALUATED_SOURCE_ORG,
                },
            ).first()
            is not None
        )


def _refresh_ds002_for_db_test() -> dict[str, object] | None:
    engine = build_engine()
    with Session(engine) as session:
        snapshot = session.execute(
            text(
                """
                SELECT
                    homepage_url,
                    commercial_use_status,
                    attribution_required,
                    ai_use_allowed,
                    cache_allowed,
                    export_allowed,
                    raw_data_allowed,
                    metadata
                FROM source.sources
                WHERE name = 'FEMA NFHL'
                    AND organization = 'FEMA'
                """
            )
        ).mappings().one_or_none()
        session.execute(
            text(
                """
                UPDATE source.sources
                SET
                    homepage_url = :homepage_url,
                    commercial_use_status = 'restricted',
                    attribution_required = true,
                    ai_use_allowed = 'restricted',
                    cache_allowed = 'restricted',
                    export_allowed = 'approved-with-restrictions',
                    raw_data_allowed = 'restricted',
                    metadata = metadata || CAST(:metadata AS jsonb)
                WHERE name = 'FEMA NFHL'
                    AND organization = 'FEMA'
                """
            ),
            {
                "homepage_url": (
                    "https://www.fema.gov/flood-maps/national-flood-hazard-layer"
                ),
                "metadata": (
                    '{"source_registry_id": "DS-002", '
                    '"source_type": "Public official", '
                    '"mvp_priority": "Must", '
                    '"license_status": "approved-with-restrictions", '
                    '"redistribution_status": "restricted", '
                    '"freshness_class": "current-effective", '
                    '"last_checked_at": "2026-06-05", '
                    '"review_owner": "operator", '
                    '"review_status": "approved-with-restrictions"}'
                ),
            },
        )
        session.commit()
        return dict(snapshot) if snapshot is not None else None


def _refresh_ds001_for_db_test() -> dict[str, object] | None:
    engine = build_engine()
    with Session(engine) as session:
        snapshot = session.execute(
            text(
                """
                SELECT
                    homepage_url,
                    commercial_use_status,
                    attribution_required,
                    ai_use_allowed,
                    cache_allowed,
                    export_allowed,
                    raw_data_allowed,
                    metadata
                FROM source.sources
                WHERE name = 'USGS The National Map'
                    AND organization = 'USGS'
                """
            )
        ).mappings().one_or_none()
        session.execute(
            text(
                """
                UPDATE source.sources
                SET
                    homepage_url = :homepage_url,
                    commercial_use_status = 'approved-with-restrictions',
                    attribution_required = true,
                    ai_use_allowed = 'restricted',
                    cache_allowed = 'approved-with-restrictions',
                    export_allowed = 'approved-with-restrictions',
                    raw_data_allowed = 'approved-with-restrictions',
                    metadata = metadata || CAST(:metadata AS jsonb)
                WHERE name = 'USGS The National Map'
                    AND organization = 'USGS'
                """
            ),
            {
                "homepage_url": "https://www.usgs.gov/the-national-map-data-delivery",
                "metadata": (
                    '{"source_registry_id": "DS-001", '
                    '"source_type": "Public official", '
                    '"mvp_priority": "Must", '
                    '"license_status": "approved-with-restrictions", '
                    '"redistribution_status": "approved-with-restrictions", '
                    '"freshness_class": "current-effective", '
                    '"last_checked_at": "2026-06-05", '
                    '"review_owner": "operator", '
                    '"review_status": "approved-with-restrictions"}'
                ),
            },
        )
        session.commit()
        return dict(snapshot) if snapshot is not None else None


def _cleanup_db_fema_report_flow(
    *,
    area_id: UUID | None,
    ingest_run_id: UUID | None,
    report_run_id: UUID | None,
    delete_sentinel_source: bool,
    ds002_snapshot: dict[str, object] | None,
    live_job_id: UUID | None = None,
    ds001_snapshot: dict[str, object] | None = None,
) -> None:
    engine = build_engine()
    with Session(engine) as session:
        if live_job_id is not None:
            session.execute(
                text(
                    """
                    DELETE FROM jobs.job_queue
                    WHERE job_type = :job_type
                        AND job_id = :job_id
                    """
                ),
                {
                    "job_type": LIVE_CONNECTOR_JOB_TYPE,
                    "job_id": str(live_job_id),
                },
            )
        if report_run_id is not None:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_id = :report_run_id"),
                {"report_run_id": report_run_id},
            )
            session.execute(
                text("DELETE FROM reports.report_runs WHERE report_run_id = :report_run_id"),
                {"report_run_id": report_run_id},
            )
        if ingest_run_id is not None:
            session.execute(
                text(
                    """
                    DELETE FROM jobs.job_queue
                    WHERE idempotency_key = :idempotency_key
                    """
                ),
                {"idempotency_key": f"connector_review_status:{ingest_run_id}"},
            )
        if area_id is not None:
            session.execute(
                text("DELETE FROM claims.verification_tasks WHERE area_id = :area_id"),
                {"area_id": area_id},
            )
            session.execute(
                text("DELETE FROM claims.claims WHERE area_id = :area_id"),
                {"area_id": area_id},
            )
            session.execute(
                text("DELETE FROM evidence.observations WHERE area_id = :area_id"),
                {"area_id": area_id},
            )
            session.execute(
                text("DELETE FROM core.areas WHERE area_id = :area_id"),
                {"area_id": area_id},
            )
        if ingest_run_id is not None:
            session.execute(
                text("DELETE FROM source.ingest_runs WHERE ingest_run_id = :ingest_run_id"),
                {"ingest_run_id": ingest_run_id},
            )
        if delete_sentinel_source:
            session.execute(
                text(
                    """
                    DELETE FROM source.sources
                    WHERE name = :name
                        AND organization = :organization
                    """
                ),
                {
                    "name": NOT_EVALUATED_SOURCE_NAME,
                    "organization": NOT_EVALUATED_SOURCE_ORG,
                },
            )
        if ds002_snapshot is not None:
            session.execute(
                text(
                    """
                    UPDATE source.sources
                    SET
                        homepage_url = :homepage_url,
                        commercial_use_status = :commercial_use_status,
                        attribution_required = :attribution_required,
                        ai_use_allowed = :ai_use_allowed,
                        cache_allowed = :cache_allowed,
                        export_allowed = :export_allowed,
                        raw_data_allowed = :raw_data_allowed,
                        metadata = CAST(:metadata AS jsonb)
                    WHERE name = 'FEMA NFHL'
                        AND organization = 'FEMA'
                    """
                ),
                {
                    "homepage_url": ds002_snapshot["homepage_url"],
                    "commercial_use_status": ds002_snapshot[
                        "commercial_use_status"
                    ],
                    "attribution_required": ds002_snapshot["attribution_required"],
                    "ai_use_allowed": ds002_snapshot["ai_use_allowed"],
                    "cache_allowed": ds002_snapshot["cache_allowed"],
                    "export_allowed": ds002_snapshot["export_allowed"],
                    "raw_data_allowed": ds002_snapshot["raw_data_allowed"],
                    "metadata": json.dumps(ds002_snapshot["metadata"]),
                },
            )
        if ds001_snapshot is not None:
            session.execute(
                text(
                    """
                    UPDATE source.sources
                    SET
                        homepage_url = :homepage_url,
                        commercial_use_status = :commercial_use_status,
                        attribution_required = :attribution_required,
                        ai_use_allowed = :ai_use_allowed,
                        cache_allowed = :cache_allowed,
                        export_allowed = :export_allowed,
                        raw_data_allowed = :raw_data_allowed,
                        metadata = CAST(:metadata AS jsonb)
                    WHERE name = 'USGS The National Map'
                        AND organization = 'USGS'
                    """
                ),
                {
                    "homepage_url": ds001_snapshot["homepage_url"],
                    "commercial_use_status": ds001_snapshot[
                        "commercial_use_status"
                    ],
                    "attribution_required": ds001_snapshot["attribution_required"],
                    "ai_use_allowed": ds001_snapshot["ai_use_allowed"],
                    "cache_allowed": ds001_snapshot["cache_allowed"],
                    "export_allowed": ds001_snapshot["export_allowed"],
                    "raw_data_allowed": ds001_snapshot["raw_data_allowed"],
                    "metadata": json.dumps(ds001_snapshot["metadata"]),
                },
            )
        session.commit()
