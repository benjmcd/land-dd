from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable, Iterable
from email.message import Message
from io import BytesIO
from pathlib import Path
from types import ModuleType
from typing import cast
from urllib.error import HTTPError
from urllib.request import Request

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "run_report_worker.py"


def load_worker_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_report_worker", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_report_worker"] = module
    spec.loader.exec_module(module)
    return module


def test_worker_client_posts_authenticated_execute_request() -> None:
    module = load_worker_module()
    calls: list[Request] = []

    def opener(request: Request, timeout: int) -> FakeResponse:
        assert timeout == 20
        calls.append(request)
        return FakeResponse(
            200,
            {
                "job_id": "job-1",
                "status": "succeeded",
                "report_run_id": "report-1",
            },
        )

    client = module.ApiClient(
        "http://api.test",
        workspace_id="workspace-1",
        user_id="user-1",
        opener=opener,
    )

    result = client.execute_next_report_job("worker-1")

    assert result.job_id == "job-1"
    assert result.status == "succeeded"
    assert result.report_run_id == "report-1"
    assert len(calls) == 1
    request = calls[0]
    assert request.full_url == "http://api.test/report-runs/jobs/execute-next"
    assert request.get_method() == "POST"
    assert request.headers["X-workspace-id"] == "workspace-1"
    assert request.headers["X-user-id"] == "user-1"
    request_data = cast(bytes, request.data or b"")
    assert json.loads(request_data.decode("utf-8")) == {"worker_id": "worker-1"}


def test_execute_bounded_report_jobs_stops_when_queue_is_empty() -> None:
    module = load_worker_module()
    responses: list[FakeResponse | HTTPError] = [
        FakeResponse(
            200,
            {
                "job_id": "job-1",
                "status": "succeeded",
                "report_run_id": "report-1",
            },
        ),
        FakeHttpError(404, {"detail": "no queued report job available"}),
    ]

    client = module.ApiClient(
        "http://api.test",
        workspace_id="workspace-1",
        user_id="user-1",
        opener=sequence_opener(responses),
    )

    summary = module.execute_bounded_report_jobs(
        client,
        worker_id="worker-1",
        max_jobs=5,
    )

    assert summary.executed_count == 1
    assert summary.stopped_on_empty_queue is True
    assert [result.job_id for result in summary.results] == ["job-1"]


def test_execute_bounded_report_jobs_requires_positive_bound() -> None:
    module = load_worker_module()
    client = module.ApiClient(
        "http://api.test",
        workspace_id="workspace-1",
        user_id="user-1",
        opener=lambda _request, timeout: FakeResponse(200, {}),
    )

    with pytest.raises(ValueError, match="max_jobs"):
        module.execute_bounded_report_jobs(client, worker_id="worker-1", max_jobs=0)


def sequence_opener(
    responses: Iterable[FakeResponse | HTTPError],
) -> Callable[[Request, int], FakeResponse]:
    pending = list(responses)

    def opener(_request: Request, timeout: int) -> FakeResponse:
        assert timeout == 20
        if not pending:
            raise AssertionError("unexpected request")
        response = pending.pop(0)
        if isinstance(response, HTTPError):
            raise response
        return response

    return opener


class FakeResponse:
    def __init__(self, status: int, body: dict[str, object]) -> None:
        self.status = status
        self._body = body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._body).encode("utf-8")


class FakeHttpError(HTTPError):
    def __init__(self, status: int, body: dict[str, object]) -> None:
        super().__init__(
            url="http://api.test/report-runs/jobs/execute-next",
            code=status,
            msg="error",
            hdrs=Message(),
            fp=BytesIO(json.dumps(body).encode("utf-8")),
        )
