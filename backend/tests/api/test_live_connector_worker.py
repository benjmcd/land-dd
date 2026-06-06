from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from uuid import UUID, uuid4

from pytest import CaptureFixture

from app.api.live_connector_jobs import LiveConnectorJobRunResult
from app.connectors.live_jobs import LiveConnectorJobRecord
from app.domain.enums import JobStatus


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_worker_module() -> ModuleType:
    module_path = _repo_root() / "scripts" / "live_connector_worker.py"
    spec = importlib.util.spec_from_file_location("live_connector_worker", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    def __enter__(self) -> _FakeSession:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1


def _job(job_id: UUID, *, status: JobStatus) -> LiveConnectorJobRecord:
    return LiveConnectorJobRecord(
        job_id=job_id,
        area_id=uuid4(),
        source_registry_id="DS-002",
        connector_name="fema_nfhl_live",
        status=status,
        priority=40,
        idempotency_key=f"live_connector_run:DS-002:{job_id}",
        payload={
            "kind": "live_connector_run",
            "source_registry_id": "DS-002",
            "connector_name": "fema_nfhl_live",
            "area_id": str(uuid4()),
            "max_features": 1,
        },
        created_at=datetime.now(UTC),
        max_features=1,
    )


def test_live_connector_worker_help_names_all_supported_sources() -> None:
    worker = _load_worker_module()

    help_text = worker.build_parser().format_help()

    assert "DS-001" in help_text
    assert "DS-002" in help_text
    assert "DS-003" in help_text
    assert "DS-004" in help_text


def test_live_connector_worker_commits_each_processed_job_and_stops_on_idle() -> None:
    worker = _load_worker_module()
    first_session = _FakeSession()
    second_session = _FakeSession()
    sessions = [first_session, second_session]
    job_id = uuid4()

    def session_factory() -> _FakeSession:
        return sessions.pop(0)

    def service_factory(
        session: _FakeSession,
        *,
        object_store_root: str,
        settings: object,
    ) -> _FakeSession:
        return session

    calls = 0

    def job_runner(
        *,
        services: _FakeSession,
        worker_id: str,
    ) -> LiveConnectorJobRunResult | None:
        nonlocal calls
        calls += 1
        assert worker_id == "worker-1"
        if calls == 1:
            return LiveConnectorJobRunResult(
                job=_job(job_id, status=JobStatus.SUCCEEDED),
                connector_result=None,
                succeeded=True,
            )
        return None

    summary = worker.run_live_connector_worker(
        worker_id=" worker-1 ",
        max_jobs=2,
        object_store_root="./local_artifacts/object_store",
        session_factory=session_factory,
        service_factory=service_factory,
        job_runner=job_runner,
    )

    assert summary.processed == 1
    assert summary.succeeded == 1
    assert summary.failed == 0
    assert summary.idle is True
    assert summary.job_ids == (str(job_id),)
    assert first_session.commits == 1
    assert second_session.commits == 0
    assert sessions == []


def test_live_connector_worker_commits_failed_job_state_and_reports_failure() -> None:
    worker = _load_worker_module()
    session = _FakeSession()
    job_id = uuid4()

    def job_runner(
        *,
        services: object,
        worker_id: str,
    ) -> LiveConnectorJobRunResult | None:
        return LiveConnectorJobRunResult(
            job=_job(job_id, status=JobStatus.FAILED),
            connector_result=None,
            succeeded=False,
            error="area is not registered",
        )

    summary = worker.run_live_connector_worker(
        worker_id="worker-2",
        max_jobs=1,
        object_store_root="./local_artifacts/object_store",
        session_factory=lambda: session,
        service_factory=lambda *_args, **_kwargs: object(),
        job_runner=job_runner,
    )

    assert session.commits == 1
    assert summary.processed == 1
    assert summary.succeeded == 0
    assert summary.failed == 1
    assert summary.failed_job_ids == (str(job_id),)


def test_live_connector_worker_main_returns_nonzero_for_processed_failure(
    capsys: CaptureFixture[str],
) -> None:
    worker = _load_worker_module()
    summary = worker.LiveConnectorWorkerSummary(
        processed=1,
        succeeded=0,
        failed=1,
        idle=False,
        job_ids=("job-1",),
        failed_job_ids=("job-1",),
    )

    def fake_run_live_connector_worker(**_kwargs: object) -> object:
        return summary

    worker.__dict__["run_live_connector_worker"] = fake_run_live_connector_worker

    assert worker.main(["--max-jobs", "1", "--json"]) == 1
    captured = capsys.readouterr()
    assert '"failed": 1' in captured.out


def test_live_connector_worker_loop_polls_until_bounded_idle() -> None:
    worker = _load_worker_module()
    sleeps: list[float] = []
    job_id = uuid4()
    calls = 0

    def job_runner(
        *,
        services: object,
        worker_id: str,
    ) -> LiveConnectorJobRunResult | None:
        nonlocal calls
        calls += 1
        if calls == 1:
            return LiveConnectorJobRunResult(
                job=_job(job_id, status=JobStatus.SUCCEEDED),
                connector_result=None,
                succeeded=True,
            )
        return None

    summary = worker.run_live_connector_worker_loop(
        worker_id="worker-loop",
        max_jobs=1,
        poll_seconds=2.5,
        idle_polls=2,
        object_store_root="./local_artifacts/object_store",
        session_factory=lambda: _FakeSession(),
        service_factory=lambda *_args, **_kwargs: object(),
        job_runner=job_runner,
        sleep_func=sleeps.append,
    )

    assert summary.processed == 1
    assert summary.succeeded == 1
    assert summary.failed == 0
    assert summary.idle is True
    assert summary.job_ids == (str(job_id),)
    assert calls == 3
    assert sleeps == [2.5, 2.5]


def test_live_connector_worker_loop_stops_after_failed_processed_job() -> None:
    worker = _load_worker_module()
    job_id = uuid4()

    def job_runner(
        *,
        services: object,
        worker_id: str,
    ) -> LiveConnectorJobRunResult | None:
        return LiveConnectorJobRunResult(
            job=_job(job_id, status=JobStatus.FAILED),
            connector_result=None,
            succeeded=False,
            error="unsupported source",
        )

    summary = worker.run_live_connector_worker_loop(
        worker_id="worker-loop",
        max_jobs=1,
        poll_seconds=5,
        idle_polls=None,
        object_store_root="./local_artifacts/object_store",
        session_factory=lambda: _FakeSession(),
        service_factory=lambda *_args, **_kwargs: object(),
        job_runner=job_runner,
        sleep_func=lambda _seconds: None,
    )

    assert summary.processed == 1
    assert summary.succeeded == 0
    assert summary.failed == 1
    assert summary.failed_job_ids == (str(job_id),)
