from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.connectors.live_jobs import LIVE_CONNECTOR_JOB_TYPE
from app.core.config import Settings
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode
from app.domain.job_health import JobQueueHealth
from app.main import create_app
from app.operations.backpressure import (
    QueueBackpressureThresholds,
    evaluate_queue_backpressure,
)
from app.reports.job_store import REPORT_RUN_JOB_TYPE, ReportJobRecord

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"
WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
USER_ID = UUID("22222222-2222-4222-8222-222222222222")
VALID_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
    "X-Workspace-Id": str(WORKSPACE_ID),
    "X-User-Id": str(USER_ID),
}


def _valid_geojson() -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _area(area_id: UUID, *, workspace_id: UUID | None = None) -> AreaContract:
    return AreaContract(
        area_id=area_id,
        workspace_id=workspace_id,
        label="Backpressure test area",
        geom_geojson=_valid_geojson(),
        geom_source="api-test",
        geom_validated=True,
    )


def _client_services_area(
    settings: Settings | None = None,
    *,
    workspace_id: UUID | None = None,
) -> tuple[TestClient, ApiServices, UUID]:
    app = create_app(settings)
    services = cast(ApiServices, app.state.services)
    area_id = uuid4()
    services.area_service.create(_area(area_id, workspace_id=workspace_id))
    return TestClient(app), services, area_id


def _sequence_body(area_id: UUID) -> dict[str, object]:
    return {
        "area_id": str(area_id),
        "bbox": {
            "xmin": -77.10,
            "ymin": 38.80,
            "xmax": -77.00,
            "ymax": 38.90,
        },
        "max_sample_points": 2,
        "max_features": 2,
        "max_rows": 1,
    }


def test_backpressure_helper_allows_when_disabled() -> None:
    health = JobQueueHealth(
        job_type=REPORT_RUN_JOB_TYPE,
        total=10,
        queued=10,
        running=0,
        succeeded=0,
        failed=0,
        cancelled=0,
        needs_review=0,
        oldest_queued_age_seconds=1000.0,
        stale_running=3,
    )

    decision = evaluate_queue_backpressure(
        health,
        QueueBackpressureThresholds(
            enabled=False,
            max_report_queue_depth=0,
            max_live_connector_queue_depth=0,
            max_queue_oldest_queued_seconds=1,
            max_queue_stale_running=0,
        ),
    )

    assert decision.allowed is True
    assert decision.detail is None


def test_backpressure_helper_blocks_on_depth_before_age_or_stale_running() -> None:
    health = JobQueueHealth(
        job_type=LIVE_CONNECTOR_JOB_TYPE,
        total=4,
        queued=2,
        running=1,
        succeeded=1,
        failed=0,
        cancelled=0,
        needs_review=0,
        oldest_queued_age_seconds=60.0,
        stale_running=1,
    )

    decision = evaluate_queue_backpressure(
        health,
        QueueBackpressureThresholds(
            enabled=True,
            max_report_queue_depth=100,
            max_live_connector_queue_depth=1,
            max_queue_oldest_queued_seconds=30,
            max_queue_stale_running=0,
        ),
    )

    assert decision.allowed is False
    assert decision.detail == {
        "type": "queue_backpressure",
        "queue": LIVE_CONNECTOR_JOB_TYPE,
        "reason": "queue_depth_exceeded",
        "observed": 3,
        "threshold": 1,
        "current_queued": 2,
        "admission_count": 1,
    }


def test_backpressure_helper_blocks_on_oldest_queued_age() -> None:
    health = JobQueueHealth(
        job_type=REPORT_RUN_JOB_TYPE,
        total=1,
        queued=0,
        running=0,
        succeeded=0,
        failed=0,
        cancelled=0,
        needs_review=0,
        oldest_queued_age_seconds=31.5,
        stale_running=0,
    )

    decision = evaluate_queue_backpressure(
        health,
        QueueBackpressureThresholds(
            enabled=True,
            max_report_queue_depth=10,
            max_live_connector_queue_depth=10,
            max_queue_oldest_queued_seconds=30,
            max_queue_stale_running=0,
        ),
    )

    assert decision.allowed is False
    assert decision.detail == {
        "type": "queue_backpressure",
        "queue": REPORT_RUN_JOB_TYPE,
        "reason": "oldest_queued_age_exceeded",
        "observed": 31.5,
        "threshold": 30,
    }


def test_backpressure_helper_blocks_on_stale_running() -> None:
    health = JobQueueHealth(
        job_type=LIVE_CONNECTOR_JOB_TYPE,
        total=1,
        queued=0,
        running=1,
        succeeded=0,
        failed=0,
        cancelled=0,
        needs_review=0,
        stale_running=1,
    )

    decision = evaluate_queue_backpressure(
        health,
        QueueBackpressureThresholds(
            enabled=True,
            max_report_queue_depth=10,
            max_live_connector_queue_depth=10,
            max_queue_oldest_queued_seconds=30,
            max_queue_stale_running=0,
        ),
    )

    assert decision.allowed is False
    assert decision.detail == {
        "type": "queue_backpressure",
        "queue": LIVE_CONNECTOR_JOB_TYPE,
        "reason": "stale_running_exceeded",
        "observed": 1,
        "threshold": 0,
    }


def test_report_queue_guard_returns_503_and_creates_no_new_job() -> None:
    client, services, area_id = _client_services_area(
        Settings(ENABLE_QUEUE_BACKPRESSURE=True, MAX_REPORT_QUEUE_DEPTH=0)
    )
    services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    before_total = services.async_report_jobs.health().total

    response = client.post(
        "/report-runs",
        json={"area_id": str(area_id), "intent_code": "rural_land_purchase"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "type": "queue_backpressure",
        "queue": REPORT_RUN_JOB_TYPE,
        "reason": "queue_depth_exceeded",
        "observed": 2,
        "threshold": 0,
        "current_queued": 1,
        "admission_count": 1,
    }
    assert services.async_report_jobs.health().total == before_total


def test_report_queue_guard_preserves_idempotent_replay_for_existing_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, services, area_id = _client_services_area(
        Settings(ENABLE_QUEUE_BACKPRESSURE=True, MAX_REPORT_QUEUE_DEPTH=0)
    )
    existing = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        client_idempotency_key="same-request",
    )
    before_total = services.async_report_jobs.health().total
    original_lookup = services.async_report_jobs.get_by_client_idempotency_key
    lookup_calls = 0

    def racing_lookup(
        client_idempotency_key: str,
        *,
        area_id: UUID,
        intent_code: IntentCode,
    ) -> ReportJobRecord | None:
        nonlocal lookup_calls
        lookup_calls += 1
        if lookup_calls == 1:
            return None
        return original_lookup(
            client_idempotency_key,
            area_id=area_id,
            intent_code=intent_code,
        )

    monkeypatch.setattr(
        services.async_report_jobs,
        "get_by_client_idempotency_key",
        racing_lookup,
    )

    response = client.post(
        "/report-runs",
        headers={"Idempotency-Key": "same-request"},
        json={"area_id": str(area_id), "intent_code": "rural_land_purchase"},
    )

    assert response.status_code == 200
    assert response.json()["report_run_id"] == str(existing.report_run_id)
    assert services.async_report_jobs.health().total == before_total


def test_intake_queue_guard_returns_503_and_creates_no_new_job() -> None:
    app = create_app(Settings(ENABLE_QUEUE_BACKPRESSURE=True, MAX_REPORT_QUEUE_DEPTH=0))
    services = cast(ApiServices, app.state.services)
    services.async_report_jobs.create(
        area_id=uuid4(),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    before_total = services.async_report_jobs.health().total
    client = TestClient(app)

    response = client.post(
        "/intake",
        json={
            "area_geojson": _valid_geojson(),
            "intent_code": "rural_land_purchase",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "type": "queue_backpressure",
        "queue": REPORT_RUN_JOB_TYPE,
        "reason": "queue_depth_exceeded",
        "observed": 2,
        "threshold": 0,
        "current_queued": 1,
        "admission_count": 1,
    }
    assert services.async_report_jobs.health().total == before_total


def test_live_connector_queue_guard_returns_503_and_creates_no_new_jobs() -> None:
    client, services, area_id = _client_services_area(
        Settings(ENABLE_QUEUE_BACKPRESSURE=True, MAX_LIVE_CONNECTOR_QUEUE_DEPTH=0),
        workspace_id=WORKSPACE_ID,
    )
    before_total = services.live_connector_jobs.health().total

    response = client.post(
        "/connector-runs/live-sequence/schedule-bbox",
        headers=VALID_HEADERS,
        json=_sequence_body(area_id),
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "type": "queue_backpressure",
        "queue": LIVE_CONNECTOR_JOB_TYPE,
        "reason": "queue_depth_exceeded",
        "observed": 4,
        "threshold": 0,
        "current_queued": 0,
        "admission_count": 4,
    }
    assert services.live_connector_jobs.health().total == before_total


def test_disabled_guard_allows_existing_scheduling_behavior() -> None:
    client, services, area_id = _client_services_area(
        Settings(MAX_LIVE_CONNECTOR_QUEUE_DEPTH=0),
        workspace_id=WORKSPACE_ID,
    )
    services.live_connector_jobs.enqueue_nwi(area_id=area_id, max_features=1)
    before_total = services.live_connector_jobs.health().total

    response = client.post(
        "/connector-runs/live-sequence/schedule-bbox",
        headers=VALID_HEADERS,
        json=_sequence_body(area_id),
    )

    assert response.status_code == 202
    assert response.json()["policy_id"] == "reviewed_live_sequence_ds001_ds002_ds004_ds003_v1"
    assert services.live_connector_jobs.health().total == before_total + 4
