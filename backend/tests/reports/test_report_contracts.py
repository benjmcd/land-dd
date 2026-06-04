from __future__ import annotations

from uuid import uuid4

from app.domain.enums import IntentCode, JobStatus
from app.domain.report_contracts import ReportRunContract


def test_report_run_contract_defaults_to_queued_status() -> None:
    report_run = ReportRunContract(area_id=uuid4(), intent_code=IntentCode.HOMESTEAD_FEASIBILITY)

    assert report_run.status == JobStatus.QUEUED
    assert report_run.source_manifest == {}
    assert report_run.assumptions == []
    assert report_run.caveats == []

