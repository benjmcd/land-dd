from __future__ import annotations

from uuid import uuid4

from app.domain.enums import IntentCode, JobStatus
from app.reports.job_store import AsyncReportJobStore


def test_create_returns_queued_record() -> None:
    store = AsyncReportJobStore()
    area_id = uuid4()
    record = store.create(area_id=area_id, intent_code=IntentCode.RURAL_LAND_PURCHASE)
    assert record.status == JobStatus.QUEUED
    assert record.area_id == area_id
    assert record.intent_code == IntentCode.RURAL_LAND_PURCHASE
    assert record.report_run_id is not None
    assert record.error_msg is None


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
