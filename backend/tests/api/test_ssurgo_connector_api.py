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
from app.connectors.ssurgo import SsurgoBbox
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
        label="SSURGO API test area",
        geom_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-77.10, 38.80],
                    [-77.09, 38.80],
                    [-77.09, 38.81],
                    [-77.10, 38.81],
                    [-77.10, 38.80],
                ]
            ],
        },
        geom_source="api-test",
        geom_validated=True,
    )


def _source() -> SourceContract:
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


def _table() -> dict[str, object]:
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
            "xmax": -77.09,
            "ymax": 38.81,
        },
        "max_rows": 1,
    }


def _client_with_seeded_services(
    *,
    fetch_payload: dict[str, object],
    fetch_queries: list[str] | None = None,
) -> tuple[TestClient, ApiServices, UUID]:
    app = create_app()
    services = app.state.services
    assert isinstance(services, ApiServices)
    area_id = uuid4()
    services.source_service.register(_source())
    services.area_service.create(_area(area_id, workspace_id=_WORKSPACE_ID))

    def fetch_json(query: str, _timeout_seconds: float) -> dict[str, object]:
        if fetch_queries is not None:
            fetch_queries.append(query)
        return fetch_payload

    services.ssurgo_fetch_json = fetch_json
    return TestClient(app), services, area_id


def test_ssurgo_query_bbox_persists_spatial_evidence_and_review_queue() -> None:
    fetch_queries: list[str] = []
    client, services, area_id = _client_with_seeded_services(
        fetch_payload=_table(),
        fetch_queries=fetch_queries,
    )

    response = client.post(
        "/connector-runs/ssurgo/query-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["connector_name"] == "ssurgo_live"
    assert body["retrieval_status"] == "succeeded"
    assert body["row_count"] == 1
    assert body["evidence_created_count"] == 1
    assert body["source_failure_created_count"] == 0
    assert body["review_required"] is False
    assert body["queue_item_status"] == "queued"
    assert body["queue_name"] == "connector-quality-review"
    assert body["source_registry_id"] == "DS-003"
    assert body["request_url"] == "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest"
    assert len(fetch_queries) == 1
    assert "SDA_Get_Mukey_from_intersection_with_WktWgs84" in fetch_queries[0]

    evidence = services.evidence_service.list_by_area(area_id)
    assert len(evidence) == 1
    assert evidence[0].evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence[0].domain == "soil_septic"
    assert evidence[0].observed_value["intersects_soil_mapunit"] is True
    assert evidence[0].observed_value["soil_mapunit_key"] == "1912968"

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


def test_ssurgo_schedule_bbox_enqueues_without_fetch_or_report() -> None:
    fetch_queries: list[str] = []
    client, services, area_id = _client_with_seeded_services(
        fetch_payload=_table(),
        fetch_queries=fetch_queries,
    )

    response = client.post(
        "/connector-runs/ssurgo/schedule-bbox",
        json=_body(area_id),
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["area_id"] == str(area_id)
    assert body["source_registry_id"] == "DS-003"
    assert body["connector_name"] == "ssurgo_live"
    assert body["connector_ingest_run_id"] is None
    assert body["payload"]["source_registry_id"] == "DS-003"
    assert body["payload"]["connector_name"] == "ssurgo_live"
    assert body["payload"]["max_rows"] == 1
    assert "report_run_id" not in body["payload"]
    assert fetch_queries == []
    assert services.evidence_service.list_by_area(area_id) == []

    queued_job_response = client.get(
        f"/connector-runs/live-jobs/{body['job_id']}",
        headers=_VALID_HEADERS,
    )
    assert queued_job_response.status_code == 200
    queued_job = queued_job_response.json()
    assert queued_job["status"] == "queued"
    assert queued_job["source_registry_id"] == "DS-003"
    assert queued_job["connector_ingest_run_id"] is None

    result = run_next_live_connector_job(
        services=services,
        worker_id="ssurgo-worker-1",
    )

    assert result is not None
    assert result.succeeded is True
    assert result.connector_result is not None
    assert result.job.status.value == "succeeded"
    assert result.job.connector_ingest_run_id == result.connector_result.ingest_run_id
    assert result.job.connector_review_status == "queued"
    assert "report_run_id" not in result.job.payload
    assert len(fetch_queries) == 1
    assert "SDA_Get_Mukey_from_intersection_with_WktWgs84" in fetch_queries[0]
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


def test_ssurgo_query_bbox_persists_source_failure_for_empty_response() -> None:
    client, services, area_id = _client_with_seeded_services(
        fetch_payload={"Table": [["mukey", "musym", "muname"]]},
    )

    response = client.post(
        "/connector-runs/ssurgo/query-bbox",
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
    assert evidence[0].domain == "soil_septic"
    assert evidence[0].observed_value["failure_reason"] == "ssurgo_no_mapunits"

    status_response = client.get(
        f"/connector-runs/{body['ingest_run_id']}/review-status",
    )
    assert status_response.status_code == 200
    assert status_response.json()["signal_codes"] == [
        "retrieval_not_succeeded",
        "retrieval_errors_present",
        "source_failure_evidence_present",
    ]


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_ssurgo_live_connector_job_store_persists_and_leases_ds003_payload() -> None:
    engine = build_engine()
    area_id = uuid4()
    bbox = SsurgoBbox(xmin=-77.10, ymin=38.80, xmax=-77.09, ymax=38.81)
    job_id: UUID | None = None

    try:
        with Session(engine) as session:
            store = SqlAlchemyLiveConnectorJobStore(session)
            queued = store.enqueue_ssurgo(
                area_id=area_id,
                bbox=bbox,
                max_rows=1,
                workspace_id=_WORKSPACE_ID,
                requested_by=_USER_ID,
            )
            job_id = queued.job_id
            assert queued.source_registry_id == "DS-003"
            assert queued.connector_name == "ssurgo_live"
            assert queued.workspace_id == _WORKSPACE_ID
            assert queued.requested_by == _USER_ID
            assert queued.payload["source_registry_id"] == "DS-003"
            assert queued.payload["connector_name"] == "ssurgo_live"
            assert queued.payload["workspace_id"] == str(_WORKSPACE_ID)
            assert queued.payload["requested_by"] == str(_USER_ID)
            assert queued.payload["max_rows"] == 1

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

            leased = store.lease_next(worker_id="db-ssurgo-worker-1")
            assert leased is not None
            assert leased.job_id == queued.job_id
            assert leased.source_registry_id == "DS-003"
            assert leased.connector_name == "ssurgo_live"
            assert leased.workspace_id == _WORKSPACE_ID
            assert leased.requested_by == _USER_ID
            assert isinstance(leased.bbox, SsurgoBbox)
            assert leased.bbox.fingerprint == bbox.fingerprint
            assert leased.payload["max_rows"] == 1
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


def test_ssurgo_query_bbox_requires_reviewer_auth() -> None:
    client, _services, area_id = _client_with_seeded_services(fetch_payload=_table())

    response = client.post("/connector-runs/ssurgo/query-bbox", json=_body(area_id))

    assert response.status_code == 401


def test_ssurgo_query_bbox_rejects_oversized_bbox() -> None:
    client, _services, area_id = _client_with_seeded_services(fetch_payload=_table())
    body = _body(area_id)
    body["bbox"] = {
        "xmin": -77.50,
        "ymin": 38.80,
        "xmax": -77.00,
        "ymax": 38.81,
    }

    response = client.post(
        "/connector-runs/ssurgo/query-bbox",
        json=body,
        headers=_VALID_HEADERS,
    )

    assert response.status_code == 422
    assert "longitude span exceeds SSURGO limit" in response.json()["detail"]
