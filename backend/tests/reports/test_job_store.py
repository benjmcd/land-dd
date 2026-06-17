from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.engine import build_engine
from app.domain.enums import IntentCode, JobStatus
from app.domain.job_health import STALE_RUNNING_THRESHOLD_SECONDS
from app.reports.job_store import AsyncReportJobStore, SqlAlchemyAsyncReportJobStore


def test_create_returns_queued_record() -> None:
    store = AsyncReportJobStore()
    area_id = uuid4()
    record = store.create(area_id=area_id, intent_code=IntentCode.RURAL_LAND_PURCHASE)
    assert record.status == JobStatus.QUEUED
    assert record.area_id == area_id
    assert record.intent_code == IntentCode.RURAL_LAND_PURCHASE
    assert record.report_run_id is not None
    assert record.error_msg is None


def test_create_can_record_retry_lineage() -> None:
    store = AsyncReportJobStore()
    retry_of_report_run_id = uuid4()

    record = store.create(
        area_id=uuid4(),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        retry_of_report_run_id=retry_of_report_run_id,
    )

    assert record.retry_of_report_run_id == retry_of_report_run_id
    found = store.get(record.report_run_id)
    assert found is not None
    assert found.retry_of_report_run_id == retry_of_report_run_id


def test_create_can_record_workspace_and_requester() -> None:
    store = AsyncReportJobStore()
    workspace_id = uuid4()
    requested_by = uuid4()

    record = store.create(
        area_id=uuid4(),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        workspace_id=workspace_id,
        requested_by=requested_by,
    )

    assert record.workspace_id == workspace_id
    assert record.requested_by == requested_by
    found = store.get(record.report_run_id)
    assert found is not None
    assert found.workspace_id == workspace_id
    assert found.requested_by == requested_by


def test_get_returns_none_for_unknown() -> None:
    store = AsyncReportJobStore()
    assert store.get(uuid4()) is None


def test_get_returns_created_record() -> None:
    store = AsyncReportJobStore()
    record = store.create(area_id=uuid4(), intent_code=IntentCode.RURAL_LAND_PURCHASE)
    found = store.get(record.report_run_id)
    assert found is not None
    assert found.report_run_id == record.report_run_id


def test_mark_running() -> None:
    store = AsyncReportJobStore()
    record = store.create(area_id=uuid4(), intent_code=IntentCode.RURAL_LAND_PURCHASE)
    store.mark_running(record.report_run_id)
    result = store.get(record.report_run_id)
    assert result is not None
    assert result.status == JobStatus.RUNNING
    assert result.started_at is not None


def test_mark_succeeded() -> None:
    store = AsyncReportJobStore()
    record = store.create(area_id=uuid4(), intent_code=IntentCode.RURAL_LAND_PURCHASE)
    store.mark_running(record.report_run_id)
    store.mark_succeeded(record.report_run_id)
    result = store.get(record.report_run_id)
    assert result is not None
    assert result.status == JobStatus.SUCCEEDED


def test_mark_failed_stores_error_msg() -> None:
    store = AsyncReportJobStore()
    record = store.create(area_id=uuid4(), intent_code=IntentCode.RURAL_LAND_PURCHASE)
    store.mark_failed(record.report_run_id, error_msg="boom")
    result = store.get(record.report_run_id)
    assert result is not None
    assert result.status == JobStatus.FAILED
    assert result.error_msg == "boom"


def test_mark_running_noop_for_unknown() -> None:
    store = AsyncReportJobStore()
    store.mark_running(uuid4())  # must not raise


def test_each_job_gets_unique_id() -> None:
    store = AsyncReportJobStore()
    area_id = uuid4()
    r1 = store.create(area_id=area_id, intent_code=IntentCode.RURAL_LAND_PURCHASE)
    r2 = store.create(area_id=area_id, intent_code=IntentCode.RURAL_LAND_PURCHASE)
    assert r1.report_run_id != r2.report_run_id


def test_health_counts_report_job_statuses() -> None:
    store = AsyncReportJobStore()
    queued = store.create(area_id=uuid4(), intent_code=IntentCode.RURAL_LAND_PURCHASE)
    failed = store.create(area_id=uuid4(), intent_code=IntentCode.HOMESTEAD_FEASIBILITY)
    store.mark_failed(failed.report_run_id, error_msg="boom")

    health = store.health()

    assert health.job_type == "report_run"
    assert health.total == 2
    assert health.queued == 1
    assert health.running == 0
    assert health.succeeded == 0
    assert health.failed == 1
    assert health.cancelled == 0
    assert health.needs_review == 0
    assert health.oldest_queued_age_seconds is not None
    assert health.oldest_queued_age_seconds >= 0
    assert health.oldest_running_age_seconds is None
    assert health.oldest_running_job_id is None
    assert health.stale_running == 0
    assert health.stale_running_threshold_seconds == STALE_RUNNING_THRESHOLD_SECONDS
    assert store.get(queued.report_run_id) is queued


def test_health_reports_oldest_running_job_and_stale_running_count() -> None:
    store = AsyncReportJobStore()
    running = store.create(area_id=uuid4(), intent_code=IntentCode.RURAL_LAND_PURCHASE)
    fresh = store.create(area_id=uuid4(), intent_code=IntentCode.HOMESTEAD_FEASIBILITY)
    store.mark_running(running.report_run_id)
    store.mark_running(fresh.report_run_id)
    running_record = store.get(running.report_run_id)
    assert running_record is not None
    running_record.started_at = datetime.now(UTC) - timedelta(
        seconds=STALE_RUNNING_THRESHOLD_SECONDS + 1,
    )

    health = store.health()

    assert health.running == 2
    assert health.oldest_running_age_seconds is not None
    assert health.oldest_running_age_seconds >= STALE_RUNNING_THRESHOLD_SECONDS
    assert health.oldest_running_job_id == running.report_run_id
    assert health.stale_running == 1
    assert health.stale_running_threshold_seconds == STALE_RUNNING_THRESHOLD_SECONDS


def test_list_recent_offset_paginates_results() -> None:
    store = AsyncReportJobStore()
    area_id = uuid4()
    # Create 5 jobs
    ids = [
        store.create(area_id=area_id, intent_code=IntentCode.RURAL_LAND_PURCHASE).report_run_id
        for _ in range(5)
    ]
    all_jobs = store.list_recent(limit=10, offset=0)
    assert len(all_jobs) == 5
    page1 = store.list_recent(limit=2, offset=0)
    page2 = store.list_recent(limit=2, offset=2)
    page3 = store.list_recent(limit=2, offset=4)
    assert len(page1) == 2
    assert len(page2) == 2
    assert len(page3) == 1
    # Combined pages should equal full list
    combined = page1 + page2 + page3
    assert [r.report_run_id for r in combined] == [r.report_run_id for r in all_jobs]
    _ = ids  # suppress unused-variable warning


def test_list_recent_status_filter_in_memory() -> None:
    store = AsyncReportJobStore()
    area_id = uuid4()
    queued = store.create(area_id=area_id, intent_code=IntentCode.RURAL_LAND_PURCHASE)
    failed = store.create(area_id=area_id, intent_code=IntentCode.HOMESTEAD_FEASIBILITY)
    store.mark_failed(failed.report_run_id, error_msg="boom")

    queued_jobs = store.list_recent(limit=50, status=JobStatus.QUEUED)
    failed_jobs = store.list_recent(limit=50, status=JobStatus.FAILED)

    assert all(r.status == JobStatus.QUEUED for r in queued_jobs)
    assert queued.report_run_id in {r.report_run_id for r in queued_jobs}
    assert all(r.status == JobStatus.FAILED for r in failed_jobs)
    assert failed.report_run_id in {r.report_run_id for r in failed_jobs}


def test_list_recent_filters_by_workspace_in_memory() -> None:
    store = AsyncReportJobStore()
    workspace_a = uuid4()
    workspace_b = uuid4()
    area_id = uuid4()
    job_a = store.create(
        area_id=area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        workspace_id=workspace_a,
    )
    job_b = store.create(
        area_id=area_id,
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        workspace_id=workspace_b,
    )
    store.create(area_id=area_id, intent_code=IntentCode.HOMESTEAD_FEASIBILITY)

    jobs = store.list_recent(limit=50, workspace_id=workspace_a)

    assert [job.report_run_id for job in jobs] == [job_a.report_run_id]
    assert job_b.report_run_id not in {job.report_run_id for job in jobs}


def test_list_recent_offset_beyond_end_returns_empty() -> None:
    store = AsyncReportJobStore()
    store.create(area_id=uuid4(), intent_code=IntentCode.RURAL_LAND_PURCHASE)
    result = store.list_recent(limit=10, offset=999)
    assert result == []


def test_list_recent_status_filter_no_match_returns_empty() -> None:
    store = AsyncReportJobStore()
    store.create(area_id=uuid4(), intent_code=IntentCode.RURAL_LAND_PURCHASE)
    result = store.list_recent(limit=10, status=JobStatus.CANCELLED)
    assert result == []


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_job_store_persists_status_transitions() -> None:
    store = SqlAlchemyAsyncReportJobStore()
    record = store.create(
        area_id=uuid4(),
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    try:
        created = store.get(record.report_run_id)
        assert created is not None
        assert created.status == JobStatus.QUEUED
        assert created.area_id == record.area_id
        assert created.intent_code == IntentCode.HOMESTEAD_FEASIBILITY

        store.mark_running(record.report_run_id)
        running = store.get(record.report_run_id)
        assert running is not None
        assert running.status == JobStatus.RUNNING

        store.mark_succeeded(record.report_run_id)
        succeeded = store.get(record.report_run_id)
        assert succeeded is not None
        assert succeeded.status == JobStatus.SUCCEEDED
        assert succeeded.error_msg is None
    finally:
        _delete_report_job(record.report_run_id)


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_job_store_persists_failure_message() -> None:
    store = SqlAlchemyAsyncReportJobStore()
    record = store.create(
        area_id=uuid4(),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    try:
        store.mark_failed(record.report_run_id, error_msg="boom")

        failed = store.get(record.report_run_id)
        assert failed is not None
        assert failed.status == JobStatus.FAILED
        assert failed.error_msg == "boom"
    finally:
        _delete_report_job(record.report_run_id)


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_job_store_persists_retry_lineage() -> None:
    store = SqlAlchemyAsyncReportJobStore()
    retry_of_report_run_id = uuid4()
    record = store.create(
        area_id=uuid4(),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        retry_of_report_run_id=retry_of_report_run_id,
    )
    try:
        found = store.get(record.report_run_id)
        assert found is not None
        assert found.retry_of_report_run_id == retry_of_report_run_id
    finally:
        _delete_report_job(record.report_run_id)


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_job_store_health_counts_status_delta() -> None:
    store = SqlAlchemyAsyncReportJobStore()
    baseline = store.health()
    queued = store.create(
        area_id=uuid4(),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    failed = store.create(
        area_id=uuid4(),
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
    )
    try:
        store.mark_failed(failed.report_run_id, error_msg="boom")

        health = store.health()

        assert health.total == baseline.total + 2
        assert health.queued == baseline.queued + 1
        assert health.failed == baseline.failed + 1
        assert health.oldest_queued_age_seconds is not None
        assert health.oldest_queued_age_seconds >= 0
    finally:
        _delete_report_job(queued.report_run_id)
        _delete_report_job(failed.report_run_id)


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_job_store_list_recent_offset_and_status() -> None:
    store = SqlAlchemyAsyncReportJobStore()
    area_id = uuid4()
    records = [
        store.create(area_id=area_id, intent_code=IntentCode.RURAL_LAND_PURCHASE)
        for _ in range(4)
    ]
    failed_record = records[0]
    store.mark_failed(failed_record.report_run_id, error_msg="test")
    try:
        # Status filter: only failed jobs
        failed_jobs = store.list_recent(limit=50, status=JobStatus.FAILED)
        failed_ids = {r.report_run_id for r in failed_jobs}
        assert failed_record.report_run_id in failed_ids
        # Status filter: only queued jobs should not include the failed one
        queued_jobs = store.list_recent(limit=50, status=JobStatus.QUEUED)
        queued_ids = {r.report_run_id for r in queued_jobs}
        assert failed_record.report_run_id not in queued_ids
        # Offset: page 1 of 2 (limit=2) then page 2
        all_jobs = store.list_recent(limit=50, offset=0)
        # Filter to just our records by id set
        our_ids = {r.report_run_id for r in records}
        our_jobs = [r for r in all_jobs if r.report_run_id in our_ids]
        if len(our_jobs) >= 2:
            page1 = [r for r in store.list_recent(limit=2, offset=0) if r.report_run_id in our_ids]
            page2 = [r for r in store.list_recent(limit=2, offset=2) if r.report_run_id in our_ids]
            combined_ids = {r.report_run_id for r in page1 + page2}
            # All our IDs should appear across both pages
            for r in our_jobs[:4]:
                assert r.report_run_id in combined_ids
    finally:
        for r in records:
            _delete_report_job(r.report_run_id)


def _delete_report_job(report_run_id: object) -> None:
    engine = build_engine()
    with Session(engine) as session:
        session.execute(
            text("DELETE FROM jobs.job_queue WHERE job_id = :job_id"),
            {"job_id": str(report_run_id)},
        )
        session.commit()
