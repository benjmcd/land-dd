from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import ApiServices
from app.api.live_connector_jobs import run_next_live_connector_job
from app.connectors.live_jobs import (
    LIVE_CONNECTOR_JOB_TYPE,
    SqlAlchemyLiveConnectorJobStore,
)
from app.connectors.nwi import NwiBbox
from app.db.engine import build_engine
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


def _area(area_id: UUID, *, workspace_id: UUID | None = None) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        workspace_id=workspace_id,
        label="NWI API test area",
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


def _feature() -> dict[str, object]:
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


def _client_with_seeded_services(
    *,
    fetch_payload: dict[str, object],
    fetch_urls: list[str] | None = None,
) -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id, workspace_id=_WORKSPACE_ID))

    def fetch_json(url: str, _timeout_seconds: float) -> dict[str, object]:
        if fetch_urls is not None:
            fetch_urls.append(url)
        return fetch_payload

    services.nwi_fetch_json = fetch_json
    return TestClient(app), services, area_id


def test_nwi_query_bbox_persists_spatial_evidence_and_review_queue() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )

    response = client.post(
        "/connector-runs/nwi/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "nwi_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 1
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"
    assert body["queue_name"] == "connector-quality-review"
    assert body["source_registry_id"] == "DS-004"

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence[0].domain == "wetlands"
    assert evidence[0].observed_value["intersects_mapped_wetlands"] is True
    assert evidence[0].observed_value["wetland_type"] == "Lake"

    status_response = client.get(
        f"/connector-runs/{body['ingest_run_id']}/review-status",
        headers=_VALID_HEADERS,
    )
    assert status_response.status_code == 200
    assert status_response.json()["disposition"] == "ready_for_connector_qa"

    queue_response = client.get(
        f"/connector-runs/{body['ingest_run_id']}/review-queue",
        headers=_VALID_HEADERS,
    )
    assert queue_response.status_code == 200
    assert queue_response.json()["status"] == "queued"


def test_nwi_schedule_bbox_enqueues_without_fetch_or_report() -> None:
    fetch_urls: list[str] = []
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        fetch_urls=fetch_urls,
    )

    response = client.post(
        "/connector-runs/nwi/schedule-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["area_id"] == str(area_id)
    assert body["source_registry_id"] == "DS-004"
    assert body["connector_name"] == "nwi_live"
    assert body["connector_ingest_run_id"] is None
    assert body["payload"]["source_registry_id"] == "DS-004"
    assert body["payload"]["connector_name"] == "nwi_live"
    assert "report_run_id" not in body["payload"]
    assert fetch_urls == []
    assert services.evidence_service.list_by_area(area_id) == []

    queued_job_response = client.get(
        f"/connector-runs/live-jobs/{body['job_id']}",
        headers=_VALID_HEADERS,
    )
    assert queued_job_response.status_code == 200
    queued_job = queued_job_response.json()
    assert queued_job["status"] == "queued"
    assert queued_job["source_registry_id"] == "DS-004"
    assert queued_job["connector_ingest_run_id"] is None

    result = run_next_live_connector_job(
        services=services,
        worker_id="nwi-worker-1",
    )

    assert result is not None
    assert result.succeeded is True
    assert result.connector_result is not None
    assert result.job.status.value == "succeeded"
    assert result.job.connector_ingest_run_id == result.connector_result.ingest_run_id
    assert result.job.connector_review_status == "queued"
    assert "report_run_id" not in result.job.payload
    assert len(fetch_urls) == 1
    assert len(services.evidence_service.list_by_area(area_id)) == 1
    queue_item = services.connector_review_queue.get_by_ingest_run_id(
        result.connector_result.ingest_run_id,
    )
    assert queue_item is not None
    assert queue_item.status.value == "queued"

    finished_job_response = client.get(
        f"/connector-runs/live-jobs/{body['job_id']}",
        headers=_VALID_HEADERS,
    )
    assert finished_job_response.status_code == 200
    finished_job = finished_job_response.json()
    assert finished_job["status"] == "succeeded"
    assert finished_job["connector_ingest_run_id"] == str(
        result.connector_result.ingest_run_id,
    )
    assert finished_job["connector_review_status"] == "queued"


def test_nwi_query_bbox_persists_source_failure_for_empty_response() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": []},
    )

    response = client.post(
        "/connector-runs/nwi/query-bbox",
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
    assert evidence[0].domain == "wetlands"
    assert evidence[0].observed_value["failure_reason"] == "nwi_no_features"

    status_response = client.get(
        f"/connector-runs/{body['ingest_run_id']}/review-status",
        headers=_VALID_HEADERS,
    )
    assert status_response.status_code == 200
    assert status_response.json()["signal_codes"] == [
        "retrieval_not_succeeded",
        "retrieval_errors_present",
        "source_failure_evidence_present",
    ]


def test_approved_nwi_connector_run_feeds_report_without_refetch() -> None:
    fetch_urls: list[str] = []
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
        fetch_urls=fetch_urls,
    )
    connector_response = client.post(
        "/connector-runs/nwi/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )
    assert connector_response.status_code == 202
    ingest_run_id = connector_response.json()["ingest_run_id"]
    assert len(fetch_urls) == 1

    approval_response = client.post(
        f"/connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa",
        headers=_VALID_HEADERS,
    )
    assert approval_response.status_code == 200
    assert approval_response.json()["new_status"] == "succeeded"

    create_report_response = client.post(
        f"/connector-runs/{ingest_run_id}/report-runs",
        json={"intent_code": "homestead_feasibility"},
        headers=_VALID_HEADERS,
    )

    assert create_report_response.status_code == 202
    body = create_report_response.json()
    assert body["status"] == "queued"
    assert body["connector_ingest_run_id"] == ingest_run_id
    assert len(fetch_urls) == 1

    report_response = client.get(f"/report-runs/{body['report_run_id']}")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["status"] == "succeeded"
    assert "WETLAND_001" in {claim["claim_code"] for claim in report["claims"]}
    assert "WETLAND_001" in {claim["claim_code"] for claim in report["red_flags"]}
    connector_evidence = [
        record
        for record in report["evidence"]
        if record["source_ingest_run_id"] == ingest_run_id
    ]
    assert len(connector_evidence) == 1
    assert connector_evidence[0]["observed_value"]["intersects_mapped_wetlands"] is True
    assert connector_evidence[0]["observed_value"]["wetland_type"] == "Lake"


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_nwi_live_connector_job_store_persists_and_leases_ds004_payload() -> None:
    engine = build_engine()
    area_id = uuid4()
    bbox = NwiBbox(xmin=-77.10, ymin=38.80, xmax=-77.00, ymax=38.90)
    job_id: UUID | None = None

    try:
        with Session(engine) as session:
            store = SqlAlchemyLiveConnectorJobStore(session)
            queued = store.enqueue_nwi(
                area_id=area_id,
                bbox=bbox,
                max_features=1,
                workspace_id=_WORKSPACE_ID,
                requested_by=_USER_ID,
            )
            job_id = queued.job_id
            assert queued.source_registry_id == "DS-004"
            assert queued.connector_name == "nwi_live"
            assert queued.workspace_id == _WORKSPACE_ID
            assert queued.requested_by == _USER_ID
            assert queued.payload["source_registry_id"] == "DS-004"
            assert queued.payload["connector_name"] == "nwi_live"
            assert queued.payload["workspace_id"] == str(_WORKSPACE_ID)
            assert queued.payload["requested_by"] == str(_USER_ID)

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

            leased = store.lease_next(worker_id="db-nwi-worker-1")
            assert leased is not None
            assert leased.job_id == queued.job_id
            assert leased.source_registry_id == "DS-004"
            assert leased.connector_name == "nwi_live"
            assert leased.workspace_id == _WORKSPACE_ID
            assert leased.requested_by == _USER_ID
            assert isinstance(leased.bbox, NwiBbox)
            assert leased.bbox.fingerprint == bbox.fingerprint
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


def test_nwi_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )

    response = client.post("/connector-runs/nwi/query-bbox", json=_body(area_id))

    assert response.status_code == 401


def test_live_connector_job_status_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )
    schedule_response = client.post(
        "/connector-runs/nwi/schedule-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )
    assert schedule_response.status_code == 202

    response = client.get(
        f"/connector-runs/live-jobs/{schedule_response.json()['job_id']}",
    )

    assert response.status_code == 401


def test_live_connector_job_status_returns_404_for_unknown_job() -> None:
    client, _services, _area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )

    response = client.get(
        f"/connector-runs/live-jobs/{uuid4()}",
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "live connector job not found"


def test_nwi_query_bbox_returns_409_when_ds004_is_not_registered() -> None:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.area_service.create(_area(area_id, workspace_id=_WORKSPACE_ID))
    client = TestClient(app)

    response = client.post(
        "/connector-runs/nwi/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "source registry id DS-004 is not registered"


def test_nwi_query_bbox_rejects_oversized_bbox() -> None:
    client, _services, area_id = _client_with_seeded_services(
        fetch_payload={"type": "FeatureCollection", "features": [_feature()]},
    )
    body = _body(area_id)
    body["bbox"] = {"xmin": -77.0, "ymin": 38.0, "xmax": -76.4, "ymax": 38.5}

    response = client.post(
        "/connector-runs/nwi/query-bbox",
        json=body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "bbox longitude span exceeds NWI limit"
