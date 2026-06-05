from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class UrlOpener(Protocol):
    def __call__(self, request: Request, timeout: int) -> Any: ...


@dataclass(frozen=True)
class WorkerResult:
    job_id: str
    status: str
    report_run_id: str | None


@dataclass(frozen=True)
class WorkerSummary:
    executed_count: int
    stopped_on_empty_queue: bool
    results: list[WorkerResult]


class ApiClient:
    def __init__(
        self,
        base_url: str,
        *,
        workspace_id: str,
        user_id: str,
        opener: UrlOpener = urlopen,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.workspace_id = workspace_id
        self.user_id = user_id
        self._opener = opener

    def execute_next_report_job(self, worker_id: str) -> WorkerResult | None:
        response = self._request(
            "POST",
            "/report-runs/jobs/execute-next",
            {"worker_id": worker_id},
            ok_statuses=(200, 404),
        )
        if response is None:
            return None
        if response.get("detail") == "no queued report job available":
            return None
        return WorkerResult(
            job_id=_required_str(response, "job_id"),
            status=_required_str(response, "status"),
            report_run_id=_optional_str(response, "report_run_id"),
        )

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, object],
        *,
        ok_statuses: tuple[int, ...],
    ) -> dict[str, object] | None:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Workspace-Id": self.workspace_id,
                "X-User-Id": self.user_id,
            },
            method=method,
        )
        try:
            with self._opener(request, timeout=20) as response:
                body = _read_json(response.read())
                if response.status not in ok_statuses:
                    raise RuntimeError(f"{method} {path} returned {response.status}: {body}")
                return _response_dict(body)
        except HTTPError as exc:
            body = _read_json(exc.read())
            if exc.code in ok_statuses:
                return _response_dict(body)
            raise RuntimeError(f"{method} {path} returned {exc.code}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(
                f"Could not reach API at {self.base_url}. Start it with scripts/run_api first."
            ) from exc


def execute_bounded_report_jobs(
    client: ApiClient,
    *,
    worker_id: str,
    max_jobs: int,
) -> WorkerSummary:
    if max_jobs < 1:
        raise ValueError("max_jobs must be at least 1")
    results: list[WorkerResult] = []
    stopped_on_empty_queue = False
    for _ in range(max_jobs):
        result = client.execute_next_report_job(worker_id)
        if result is None:
            stopped_on_empty_queue = True
            break
        results.append(result)
    return WorkerSummary(
        executed_count=len(results),
        stopped_on_empty_queue=stopped_on_empty_queue,
        results=results,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute a bounded number of queued report jobs through the public API."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--worker-id", default="report-worker-operator")
    parser.add_argument("--max-jobs", type=int, default=1)
    args = parser.parse_args()

    client = ApiClient(
        args.base_url,
        workspace_id=args.workspace_id,
        user_id=args.user_id,
    )
    summary = execute_bounded_report_jobs(
        client,
        worker_id=args.worker_id,
        max_jobs=args.max_jobs,
    )
    for result in summary.results:
        print(
            "report job: "
            f"{result.job_id} status={result.status} report_run_id={result.report_run_id}"
        )
    if summary.stopped_on_empty_queue:
        print("report job queue: empty")
    print(f"report jobs executed: {summary.executed_count}")


def _read_json(raw: bytes) -> object:
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def _response_dict(body: object) -> dict[str, object] | None:
    if body is None:
        return None
    if not isinstance(body, dict):
        raise RuntimeError(f"Expected object response, got {body!r}")
    return body


def _required_str(record: dict[str, object], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"Expected non-empty string field {field!r}, got {value!r}")
    return value


def _optional_str(record: dict[str, object], field: str) -> str | None:
    value = record.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"Expected string field {field!r}, got {value!r}")
    return value


if __name__ == "__main__":
    main()
