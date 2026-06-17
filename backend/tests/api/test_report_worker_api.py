from __future__ import annotations

from datetime import timedelta
from typing import cast
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.api.report_auth import create_report_identity_token
from app.core.config import Settings
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode, JobStatus
from app.main import create_app

SECRET = "report-worker-secret-with-at-least-32-characters"


def _make_client() -> tuple[FastAPI, TestClient]:
    app = create_app(
        settings=Settings(
            REPORT_AUTH_MODE="signed_token",
            REPORT_IDENTITY_TOKEN_SECRET=SECRET,
        )
    )
    return app, TestClient(app)


def _headers(workspace_id: UUID, user_id: UUID) -> dict[str, str]:
    token = create_report_identity_token(
        workspace_id=workspace_id,
        user_id=user_id,
        secret=SECRET,
        expires_in=timedelta(minutes=10),
    )
    return {"Authorization": f"Bearer {token}"}


def _create_area(services: ApiServices, *, workspace_id: UUID, user_id: UUID) -> UUID:
    area = services.area_service.create(
        AreaContract(
            workspace_id=workspace_id,
            created_by=user_id,
            label="worker route fixture",
            geom_geojson={
                "type": "Polygon",
                "coordinates": [
                    [
                        [-79.0, 35.0],
                        [-79.0, 35.01],
                        [-78.99, 35.01],
                        [-78.99, 35.0],
                        [-79.0, 35.0],
                    ]
                ],
            },
            geom_source="api worker fixture",
        )
    )
    return area.area_id


def test_execute_next_report_job_runs_one_authenticated_workspace_job() -> None:
    app, client = _make_client()
    services = cast(ApiServices, app.state.services)
    workspace_id = uuid4()
    user_id = uuid4()
    area_id = _create_area(services, workspace_id=workspace_id, user_id=user_id)
    job = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        workspace_id=workspace_id,
        requested_by=user_id,
    )

    response = client.post(
        "/report-runs/jobs/execute-next",
        json={"worker_id": "report-worker-1"},
        headers=_headers(workspace_id, user_id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "job_id": str(job.report_run_id),
        "status": "succeeded",
        "report_run_id": str(job.report_run_id),
    }
    stored_job = services.async_report_jobs.get(job.report_run_id)
    assert stored_job is not None
    assert stored_job.status == JobStatus.SUCCEEDED
    report = client.get(
        f"/report-runs/{job.report_run_id}",
        headers=_headers(workspace_id, user_id),
    )
    assert report.status_code == 200
    assert report.json()["status"] == "succeeded"


def test_execute_next_report_job_returns_404_for_empty_workspace_queue() -> None:
    _app, client = _make_client()
    response = client.post(
        "/report-runs/jobs/execute-next",
        json={"worker_id": "report-worker-1"},
        headers=_headers(uuid4(), uuid4()),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "no queued report job available"


def test_execute_next_report_job_does_not_cross_workspace() -> None:
    app, client = _make_client()
    services = cast(ApiServices, app.state.services)
    workspace_a = uuid4()
    workspace_b = uuid4()
    user_id = uuid4()
    area_id = _create_area(services, workspace_id=workspace_a, user_id=user_id)
    job = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        workspace_id=workspace_a,
        requested_by=user_id,
    )

    response = client.post(
        "/report-runs/jobs/execute-next",
        json={"worker_id": "report-worker-1"},
        headers=_headers(workspace_b, user_id),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "no queued report job available"
    stored_job = services.async_report_jobs.get(job.report_run_id)
    assert stored_job is not None
    assert stored_job.status == JobStatus.QUEUED


def test_execute_next_report_job_requires_report_identity() -> None:
    _app, client = _make_client()

    response = client.post(
        "/report-runs/jobs/execute-next",
        json={"worker_id": "report-worker-1"},
    )

    assert response.status_code == 401
