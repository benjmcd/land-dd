from __future__ import annotations

import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import ApiServices
from app.api.live_connector_jobs import run_next_live_connector_job
from app.connectors.live_jobs import (
    LIVE_CONNECTOR_JOB_TYPE,
    InMemoryLiveConnectorJobStore,
    SqlAlchemyLiveConnectorJobStore,
)
from app.connectors.usgs_tnm import UsgsTnmBbox
from app.core.config import Settings
from app.db.engine import build_engine
from app.domain.area_contracts import AreaContract
from app.domain.enums import EvidenceType
from app.domain.job_health import STALE_RUNNING_THRESHOLD_SECONDS
from app.domain.source_contracts import SourceContract
from app.main import create_app

_VALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}
_WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
_OTHER_WORKSPACE_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
_OTHER_USER_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
_LIVE_HEADERS = {
    **_VALID_HEADERS,
    "X-Workspace-Id": str(_WORKSPACE_ID),
    "X-User-Id": str(_USER_ID),
}


def _area(area_id: UUID, *, workspace_id: UUID | None = None) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        workspace_id=workspace_id,
        label="USGS TNM API test area",
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


def _payload(elevation_m: float, *, acquisition_date: str = "11/3/2022") -> dict[str, object]:
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
        "attributes": {"AcquisitionDate": acquisition_date},
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
        "max_sample_points": 2,
    }


def _client_with_seeded_services(
    *,
    elevations: list[float],
    fetch_urls: list[str] | None = None,
    workspace_id: UUID | None = _WORKSPACE_ID,
) -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id, workspace_id=workspace_id))
    remaining_elevations = iter(elevations)

    def fetch_json(url: str, _timeout_seconds: float) -> dict[str, object]:
        if fetch_urls is not None:
            fetch_urls.append(url)
        return _payload(next(remaining_elevations))

    services.usgs_tnm_fetch_json = fetch_json
    return TestClient(app), services, area_id


def test_usgs_tnm_query_bbox_persists_relief_evidence_and_review_queue() -> None:
    fetch_urls: list[str] = []
    client, services, area_id = _client_with_seeded_services(
        elevations=[9.0, 13.0],
        fetch_urls=fetch_urls,
    )

    response = client.post(
        "/connector-runs/usgs-tnm/query-bbox",
        json=_body(area_id),
        headers=_LIVE_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "usgs_tnm_elevation_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 2
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"
    assert body["queue_name"] == "connector-quality-review"
    assert body["source_registry_id"] == "DS-001"
    assert body["request_url"].startswith("https://epqs.nationalmap.gov/v1/json?")
    assert len(fetch_urls) == 2
    assert all("includeDate=true" in url for url in fetch_urls)

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.DERIVED_METRIC
    assert evidence[0].domain == "buildability"
    assert evidence[0].observed_value == {
        "metric_code": "tnm_epqs_sampled_relief_m",
        "value": 4.0,
        "unit": "m",
        "min_elevation_m": 9.0,
        "max_elevation_m": 13.0,
        "mean_elevation_m": 11.0,
        "sample_count": 2,
        "calculation_method": "center_and_corner_epqs_point_sample_relief",
    }

    status_response = client.get(
        f"/connector-runs/{body['ingest_run_id']}/review-status",
        headers=_LIVE_HEADERS,
    )
    assert status_response.status_code == 200
    assert status_response.json()["disposition"] == "ready_for_connector_qa"

    queue_response = client.get(
        f"/connector-runs/{body['ingest_run_id']}/review-queue",
        headers=_LIVE_HEADERS,
    )
    assert queue_response.status_code == 200
    assert queue_response.json()["status"] == "queued"


def test_usgs_tnm_query_bbox_persists_source_failure_for_no_data() -> None:
    client, services, area_id = _client_with_seeded_services(
        elevations=[-1000000.0],
    )

    response = client.post(
        "/connector-runs/usgs-tnm/query-bbox",
        json=_body(area_id),
        headers=_LIVE_HEADERS,
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
    assert evidence[0].domain == "buildability"
    assert evidence[0].observed_value["failure_reason"] == "usgs_tnm_no_elevation"

    status_response = client.get(
        f"/connector-runs/{body['ingest_run_id']}/review-status",
        headers=_LIVE_HEADERS,
    )
    assert status_response.status_code == 200
    assert status_response.json()["signal_codes"] == [
        "retrieval_not_succeeded",
        "retrieval_errors_present",
        "source_failure_evidence_present",
    ]


def test_usgs_tnm_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(elevations=[9.0, 13.0])

    response = client.post("/connector-runs/usgs-tnm/query-bbox", json=_body(area_id))

    assert response.status_code == 401


def test_usgs_tnm_query_bbox_returns_409_when_ds001_is_not_registered() -> None:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.area_service.create(_area(area_id, workspace_id=_WORKSPACE_ID))
    client = TestClient(app)

    response = client.post(
        "/connector-runs/usgs-tnm/query-bbox",
        json=_body(area_id),
        headers=_LIVE_HEADERS,
    )

    assert response.status_code == 409
    assert "DS-001" in response.json()["detail"]


def test_usgs_tnm_query_bbox_rejects_oversized_bbox() -> None:
    client, _services, area_id = _client_with_seeded_services(elevations=[9.0, 13.0])
    body = _body(area_id)
    body["bbox"] = {
        "xmin": -77.50,
        "ymin": 38.80,
        "xmax": -77.00,
        "ymax": 38.90,
    }

    response = client.post(
        "/connector-runs/usgs-tnm/query-bbox",
        json=body,
        headers=_LIVE_HEADERS,
    )

    assert response.status_code == 422
    assert "USGS TNM limit" in response.json()["detail"]


def test_usgs_tnm_query_bbox_does_not_schedule_or_report() -> None:
    fetch_urls: list[str] = []
    client, services, area_id = _client_with_seeded_services(
        elevations=[9.0, 13.0],
        fetch_urls=fetch_urls,
    )

    response = client.post(
        "/connector-runs/usgs-tnm/query-bbox",
        json=_body(area_id),
        headers=_LIVE_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert "report_run_id" not in body
    assert "job_id" not in body
    assert len(fetch_urls) == 2
    assert len(services.evidence_service.list_by_area(area_id)) == 1


def test_usgs_tnm_schedule_bbox_enqueues_without_fetch_or_report() -> None:
    fetch_urls: list[str] = []
    client, services, area_id = _client_with_seeded_services(
        elevations=[9.0, 13.0],
        fetch_urls=fetch_urls,
        workspace_id=_WORKSPACE_ID,
    )

    response = client.post(
        "/connector-runs/usgs-tnm/schedule-bbox",
        json=_body(area_id),
        headers=_LIVE_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["area_id"] == str(area_id)
    assert body["workspace_id"] == str(_WORKSPACE_ID)
    assert body["requested_by"] == str(_USER_ID)
    assert body["source_registry_id"] == "DS-001"
    assert body["connector_name"] == "usgs_tnm_elevation_live"
    assert body["connector_ingest_run_id"] is None
    assert body["payload"]["workspace_id"] == str(_WORKSPACE_ID)
    assert body["payload"]["requested_by"] == str(_USER_ID)
    assert body["payload"]["source_registry_id"] == "DS-001"
    assert body["payload"]["connector_name"] == "usgs_tnm_elevation_live"
    assert body["payload"]["max_sample_points"] == 2
    assert "report_run_id" not in body["payload"]
    assert fetch_urls == []
    assert services.evidence_service.list_by_area(area_id) == []

    queued_job_response = client.get(
        f"/connector-runs/live-jobs/{body['job_id']}",
        headers=_LIVE_HEADERS,
    )
    assert queued_job_response.status_code == 200
    queued_job = queued_job_response.json()
    assert queued_job["status"] == "queued"
    assert queued_job["source_registry_id"] == "DS-001"
    assert queued_job["connector_ingest_run_id"] is None

    result = run_next_live_connector_job(
        services=services,
        worker_id="usgs-tnm-worker-1",
    )

    assert result is not None
    assert result.succeeded is True
    assert result.connector_result is not None
    assert result.job.status.value == "succeeded"
    assert result.job.connector_ingest_run_id == result.connector_result.ingest_run_id
    assert result.job.connector_review_status == "queued"
    assert "report_run_id" not in result.job.payload
    assert len(fetch_urls) == 2
    assert len(services.evidence_service.list_by_area(area_id)) == 1
    queue_item = services.connector_review_queue.get_by_ingest_run_id(
        result.connector_result.ingest_run_id,
    )
    assert queue_item is not None
    assert queue_item.status.value == "queued"

    finished_job_response = client.get(
        f"/connector-runs/live-jobs/{body['job_id']}",
        headers=_LIVE_HEADERS,
    )
    assert finished_job_response.status_code == 200
    finished_job = finished_job_response.json()
    assert finished_job["status"] == "succeeded"
    assert finished_job["connector_ingest_run_id"] == str(
        result.connector_result.ingest_run_id,
    )
    assert finished_job["connector_review_status"] == "queued"


def test_usgs_tnm_schedule_bbox_requires_workspace_identity() -> None:
    client, _services, area_id = _client_with_seeded_services(
        elevations=[9.0, 13.0],
        workspace_id=_WORKSPACE_ID,
    )

    response = client.post(
        "/connector-runs/usgs-tnm/schedule-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "X-Workspace-Id header is required"


def test_usgs_tnm_schedule_bbox_hides_area_from_other_workspace() -> None:
    client, _services, area_id = _client_with_seeded_services(
        elevations=[9.0, 13.0],
        workspace_id=_OTHER_WORKSPACE_ID,
    )

    response = client.post(
        "/connector-runs/usgs-tnm/schedule-bbox",
        json=_body(area_id),
        headers=_LIVE_HEADERS,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "area not found"


def test_list_live_connector_jobs_filters_running_and_stale_jobs() -> None:
    app = create_app()
    client = TestClient(app)
    services = cast(ApiServices, app.state.services)
    area_id = uuid4()
    running = services.live_connector_jobs.enqueue_nwi(
        area_id=area_id,
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
        max_features=1,
    )
    queued = services.live_connector_jobs.enqueue_fema_nfhl(
        area_id=area_id,
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
        max_features=1,
    )
    leased = services.live_connector_jobs.lease_next(worker_id="api-live-worker")
    assert leased is not None
    assert leased.job_id == running.job_id
    store = services.live_connector_jobs
    assert isinstance(store, InMemoryLiveConnectorJobStore)
    with store._lock:
        stale_started_at = datetime.now(UTC) - timedelta(
            seconds=STALE_RUNNING_THRESHOLD_SECONDS + 1,
        )
        store._jobs[running.job_id] = replace(
            store._jobs[running.job_id],
            started_at=stale_started_at,
        )

    running_resp = client.get(
        "/connector-runs/live-jobs?status=running",
        headers=_LIVE_HEADERS,
    )
    stale_resp = client.get(
        "/connector-runs/live-jobs?status=running&stale=true",
        headers=_LIVE_HEADERS,
    )
    queued_resp = client.get(
        "/connector-runs/live-jobs?status=queued",
        headers=_LIVE_HEADERS,
    )
    invalid_resp = client.get(
        "/connector-runs/live-jobs?status=failed&stale=true",
        headers=_LIVE_HEADERS,
    )

    assert running_resp.status_code == 200
    running_items = running_resp.json()
    assert [item["job_id"] for item in running_items] == [str(running.job_id)]
    assert running_items[0]["locked_by"] == "api-live-worker"
    assert running_items[0]["running_age_seconds"] >= STALE_RUNNING_THRESHOLD_SECONDS
    assert running_items[0]["is_stale_running"] is True
    assert stale_resp.status_code == 200
    assert [item["job_id"] for item in stale_resp.json()] == [str(running.job_id)]
    assert queued_resp.status_code == 200
    assert [item["job_id"] for item in queued_resp.json()] == [str(queued.job_id)]
    assert invalid_resp.status_code == 422


def test_live_connector_job_inspection_requires_operations_read_scope() -> None:
    client = TestClient(create_app())
    no_auth_list = client.get("/connector-runs/live-jobs")
    no_auth_detail = client.get(f"/connector-runs/live-jobs/{uuid4()}")
    under_scoped = TestClient(
        create_app(
            Settings(
                REVIEWER_ACCOUNTS="runner:runner-token",
                REVIEWER_ACCOUNT_SCOPES="runner:connector:run",
            )
        )
    )
    under_scoped_headers = {
        "X-Reviewer-Id": "runner",
        "X-Reviewer-Token": "runner-token",
        "X-Workspace-Id": str(_WORKSPACE_ID),
        "X-User-Id": str(_USER_ID),
    }

    under_scoped_list = under_scoped.get(
        "/connector-runs/live-jobs",
        headers=under_scoped_headers,
    )
    under_scoped_detail = under_scoped.get(
        f"/connector-runs/live-jobs/{uuid4()}",
        headers=under_scoped_headers,
    )

    assert no_auth_list.status_code == 401
    assert no_auth_detail.status_code == 401
    assert under_scoped_list.status_code == 403
    assert under_scoped_detail.status_code == 403
    assert under_scoped_list.json()["detail"] == ("reviewer scope is required: operations:read")


def test_live_connector_job_inspection_requires_workspace_identity() -> None:
    client = TestClient(create_app())

    no_identity_list = client.get("/connector-runs/live-jobs", headers=_VALID_HEADERS)
    no_identity_detail = client.get(
        f"/connector-runs/live-jobs/{uuid4()}",
        headers=_VALID_HEADERS,
    )

    assert no_identity_list.status_code == 401
    assert no_identity_detail.status_code == 401
    assert no_identity_list.json()["detail"] == "X-Workspace-Id header is required"


def test_live_connector_job_list_and_detail_hide_other_workspace_jobs() -> None:
    app = create_app()
    client = TestClient(app)
    services = cast(ApiServices, app.state.services)
    job = services.live_connector_jobs.enqueue_nwi(
        area_id=uuid4(),
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
        max_features=1,
    )
    other_headers = {
        **_VALID_HEADERS,
        "X-Workspace-Id": str(_OTHER_WORKSPACE_ID),
        "X-User-Id": str(_OTHER_USER_ID),
    }

    listed = client.get("/connector-runs/live-jobs", headers=other_headers)
    fetched = client.get(
        f"/connector-runs/live-jobs/{job.job_id}",
        headers=other_headers,
    )

    assert listed.status_code == 200
    assert listed.json() == []
    assert fetched.status_code == 404


def test_live_connector_worker_fails_closed_for_cross_workspace_area() -> None:
    app = create_app()
    services = cast(ApiServices, app.state.services)
    area_id = uuid4()
    services.area_service.create(_area(area_id, workspace_id=_OTHER_WORKSPACE_ID))
    job = services.live_connector_jobs.enqueue_usgs_tnm(
        area_id=area_id,
        workspace_id=_WORKSPACE_ID,
        requested_by=_USER_ID,
        bbox=UsgsTnmBbox(xmin=-77.10, ymin=38.80, xmax=-77.00, ymax=38.90),
        max_sample_points=2,
    )

    result = run_next_live_connector_job(
        services=services,
        worker_id="usgs-tnm-worker-1",
    )

    assert result is not None
    assert result.succeeded is False
    assert result.job.job_id == job.job_id
    assert result.job.status.value == "failed"
    assert result.error == "area not found"


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_usgs_tnm_live_connector_job_store_persists_and_leases_ds001_payload() -> None:
    engine = build_engine()
    area_id = uuid4()
    bbox = UsgsTnmBbox(xmin=-77.10, ymin=38.80, xmax=-77.00, ymax=38.90)
    job_id: UUID | None = None

    try:
        with Session(engine) as session:
            store = SqlAlchemyLiveConnectorJobStore(session)
            queued = store.enqueue_usgs_tnm(
                area_id=area_id,
                bbox=bbox,
                max_sample_points=2,
                workspace_id=_WORKSPACE_ID,
                requested_by=_USER_ID,
            )
            job_id = queued.job_id
            assert queued.source_registry_id == "DS-001"
            assert queued.connector_name == "usgs_tnm_elevation_live"
            assert queued.workspace_id == _WORKSPACE_ID
            assert queued.requested_by == _USER_ID
            assert queued.payload["source_registry_id"] == "DS-001"
            assert queued.payload["connector_name"] == "usgs_tnm_elevation_live"
            assert queued.payload["workspace_id"] == str(_WORKSPACE_ID)
            assert queued.payload["requested_by"] == str(_USER_ID)
            assert queued.payload["max_sample_points"] == 2

            retrieved = store.get(queued.job_id)
            assert retrieved is not None
            assert retrieved.workspace_id == _WORKSPACE_ID
            assert retrieved.requested_by == _USER_ID
            assert queued.job_id in {
                job.job_id for job in store.list_recent(workspace_id=_WORKSPACE_ID)
            }
            assert queued.job_id not in {
                job.job_id for job in store.list_recent(workspace_id=uuid4())
            }

            leased = store.lease_next(worker_id="db-usgs-tnm-worker-1")
            assert leased is not None
            assert leased.job_id == queued.job_id
            assert leased.source_registry_id == "DS-001"
            assert leased.connector_name == "usgs_tnm_elevation_live"
            assert leased.workspace_id == _WORKSPACE_ID
            assert leased.requested_by == _USER_ID
            assert isinstance(leased.bbox, UsgsTnmBbox)
            assert leased.bbox.fingerprint == bbox.fingerprint
            assert leased.payload["max_sample_points"] == 2
            session.commit()
    finally:
        if job_id is not None:
            with Session(engine) as session:
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
                        "job_id": str(job_id),
                    },
                )
                session.commit()
