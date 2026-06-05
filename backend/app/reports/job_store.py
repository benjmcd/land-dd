from __future__ import annotations

import threading
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.domain.enums import IntentCode, JobStatus


@dataclass
class ReportJobRecord:
    report_run_id: UUID
    area_id: UUID
    intent_code: IntentCode
    status: JobStatus = JobStatus.QUEUED
    error_msg: str | None = None


class AsyncReportJobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[UUID, ReportJobRecord] = {}

    def create(self, *, area_id: UUID, intent_code: IntentCode) -> ReportJobRecord:
        record = ReportJobRecord(
            report_run_id=uuid4(),
            area_id=area_id,
            intent_code=intent_code,
        )
        with self._lock:
            self._jobs[record.report_run_id] = record
        return record

    def get(self, report_run_id: UUID) -> ReportJobRecord | None:
        with self._lock:
            return self._jobs.get(report_run_id)

    def mark_running(self, report_run_id: UUID) -> None:
        with self._lock:
            record = self._jobs.get(report_run_id)
            if record is not None:
                record.status = JobStatus.RUNNING

    def mark_succeeded(self, report_run_id: UUID) -> None:
        with self._lock:
            record = self._jobs.get(report_run_id)
            if record is not None:
                record.status = JobStatus.SUCCEEDED

    def mark_failed(self, report_run_id: UUID, *, error_msg: str) -> None:
        with self._lock:
            record = self._jobs.get(report_run_id)
            if record is not None:
                record.status = JobStatus.FAILED
                record.error_msg = error_msg


__all__ = ["AsyncReportJobStore", "ReportJobRecord"]
