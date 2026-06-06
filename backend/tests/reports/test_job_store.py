from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.engine import build_engine
from app.domain.enums import IntentCode, JobStatus
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
    assert store.get(queued.report_run_id) is queued


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


def _delete_report_job(report_run_id: object) -> None:
    engine = build_engine()
    with Session(engine) as session:
        session.execute(
            text("DELETE FROM jobs.job_queue WHERE job_id = :job_id"),
            {"job_id": str(report_run_id)},
        )
        session.commit()
