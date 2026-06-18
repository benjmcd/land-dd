from __future__ import annotations

import importlib.util
import json
import os
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = REPO_ROOT / "scripts" / "load_test_runner.py"


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "load_test_runner_under_test",
        RUNNER_PATH,
    )
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _last_result(module: ModuleType) -> dict[str, Any]:
    payload = cast(Any, module).LAST_RESULT
    assert isinstance(payload, dict)
    return payload


def test_run_load_test_ps1_exists_and_is_not_empty() -> None:
    path = REPO_ROOT / "scripts" / "run_load_test.ps1"
    assert path.is_file(), f"missing: {path}"
    assert os.path.getsize(path) > 0, f"empty: {path}"


def test_run_load_test_sh_exists_and_is_not_empty() -> None:
    path = REPO_ROOT / "scripts" / "run_load_test.sh"
    assert path.is_file(), f"missing: {path}"
    assert os.path.getsize(path) > 0, f"empty: {path}"


def test_load_testing_runbook_exists_and_is_not_empty() -> None:
    path = REPO_ROOT / "docs" / "runbooks" / "load_testing.md"
    assert path.is_file(), f"missing: {path}"
    assert os.path.getsize(path) > 0, f"empty: {path}"


def test_load_testing_runbook_documents_validate_only_flag() -> None:
    path = REPO_ROOT / "docs" / "runbooks" / "load_testing.md"
    content = path.read_text(encoding="utf-8")
    assert "--validate-only" in content or "validate-only" in content, (
        "runbook must document the --validate-only flag"
    )


def test_load_testing_runbook_mentions_sequential_request_count() -> None:
    path = REPO_ROOT / "docs" / "runbooks" / "load_testing.md"
    content = path.read_text(encoding="utf-8")
    assert "20" in content, "runbook must mention the sequential request count (20)"


def test_load_testing_runbook_mentions_scope_limitations() -> None:
    path = REPO_ROOT / "docs" / "runbooks" / "load_testing.md"
    content = path.read_text(encoding="utf-8")
    lower = content.lower()
    assert "scope" in lower or "limitation" in lower or "sequential" in lower, (
        "runbook must describe scope limitations of the load test"
    )


def test_load_runner_sequential_success_records_json_result(
    monkeypatch: Any,
) -> None:
    runner = _load_runner()

    def fake_send_request(
        base_url: str,
        method: str,
        path: str,
        body: str | None = None,
        timeout: float = 5.0,
    ) -> tuple[int, float]:
        assert base_url == "http://testserver"
        assert timeout > 0
        assert method in {"GET", "POST"}
        assert path in {"/health", "/version", "/metrics", "/areas", "/report-runs"}
        if method == "POST":
            assert body is not None
        return 200, 0.01

    monkeypatch.setattr(runner, "send_request", fake_send_request)

    assert cast(Any, runner).run_sequential("http://testserver") == 0

    result = _last_result(runner)
    assert result["schema_version"] == "load_test_result_v1"
    assert result["scenario"] == "sequential"
    assert result["base_url"] == "http://testserver"
    assert result["total_requests"] == 20
    assert result["ok"] is True
    assert result["failures"] == []
    assert result["thresholds"] == {"max_request_seconds": 5.0}
    assert result["summary"]["passed"] == 20
    assert result["summary"]["failed"] == 0
    assert len(result["requests"]) == 20
    assert {request["path"] for request in result["requests"]} == {
        "/health",
        "/version",
        "/metrics",
        "/areas",
        "/report-runs",
    }
    assert all(request["passed"] is True for request in result["requests"])


def test_load_runner_main_writes_json_output(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    runner = _load_runner()

    def fake_send_request(
        base_url: str,
        method: str,
        path: str,
        body: str | None = None,
        timeout: float = 5.0,
    ) -> tuple[int, float]:
        return 200, 0.01

    output_path = tmp_path / "sequential.json"
    monkeypatch.setattr(runner, "send_request", fake_send_request)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "load_test_runner.py",
            "--scenario",
            "sequential",
            "--base-url",
            "http://testserver",
            "--json-output",
            str(output_path),
        ],
    )

    assert cast(Any, runner).main() == 0

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload == _last_result(runner)
    assert payload["schema_version"] == "load_test_result_v1"
    assert payload["scenario"] == "sequential"


def test_load_runner_sequential_fails_on_timeout(monkeypatch: Any) -> None:
    runner = _load_runner()

    def fake_send_request(
        base_url: str,
        method: str,
        path: str,
        body: str | None = None,
        timeout: float = 5.0,
    ) -> tuple[int, float]:
        return 200, 5.01

    monkeypatch.setattr(runner, "send_request", fake_send_request)

    assert cast(Any, runner).run_sequential("http://testserver") == 1
    result = _last_result(runner)
    assert result["ok"] is False
    assert result["summary"]["failed"] == 20
    assert "elapsed 5.010s > 5.0s" in result["failures"][0]


def test_load_runner_sequential_fails_on_status_zero(monkeypatch: Any) -> None:
    runner = _load_runner()

    def fake_send_request(
        base_url: str,
        method: str,
        path: str,
        body: str | None = None,
        timeout: float = 5.0,
    ) -> tuple[int, float]:
        return 0, 0.01

    monkeypatch.setattr(runner, "send_request", fake_send_request)

    assert cast(Any, runner).run_sequential("http://testserver") == 1
    result = _last_result(runner)
    assert result["ok"] is False
    assert result["summary"]["failed"] == 20
    assert "runtime status 0" in result["failures"][0]


def test_load_runner_sequential_fails_on_5xx(monkeypatch: Any) -> None:
    runner = _load_runner()

    def fake_send_request(
        base_url: str,
        method: str,
        path: str,
        body: str | None = None,
        timeout: float = 5.0,
    ) -> tuple[int, float]:
        return 503, 0.01

    monkeypatch.setattr(runner, "send_request", fake_send_request)

    assert cast(Any, runner).run_sequential("http://testserver") == 1
    result = _last_result(runner)
    assert result["ok"] is False
    assert result["summary"]["failed"] == 20
    assert "runtime status 503" in result["failures"][0]


def test_load_runner_sequential_keeps_4xx_non_error(monkeypatch: Any) -> None:
    runner = _load_runner()

    def fake_send_request(
        base_url: str,
        method: str,
        path: str,
        body: str | None = None,
        timeout: float = 5.0,
    ) -> tuple[int, float]:
        return 404, 0.01

    monkeypatch.setattr(runner, "send_request", fake_send_request)

    assert cast(Any, runner).run_sequential("http://testserver") == 0
    result = _last_result(runner)
    assert result["ok"] is True
    assert result["summary"]["failed"] == 0
    assert {request["status"] for request in result["requests"]} == {404}


def test_load_runner_concurrent_fails_on_p95(monkeypatch: Any) -> None:
    runner = _load_runner()

    def fake_send_request(
        base_url: str,
        method: str,
        path: str,
        body: str | None = None,
        timeout: float = 5.0,
    ) -> tuple[int, float]:
        return 200, 3.01

    monkeypatch.setattr(runner, "send_request", fake_send_request)

    assert cast(Any, runner).run_concurrent("http://testserver", n_workers=8) == 1
    result = _last_result(runner)
    assert result["ok"] is False
    assert result["summary"]["p95_seconds"] > 3.0
    assert any("p95 latency" in failure for failure in result["failures"])


def test_load_runner_concurrent_fails_on_error_rate(monkeypatch: Any) -> None:
    runner = _load_runner()
    counter = 0
    lock = threading.Lock()

    def fake_send_request(
        base_url: str,
        method: str,
        path: str,
        body: str | None = None,
        timeout: float = 5.0,
    ) -> tuple[int, float]:
        nonlocal counter
        with lock:
            counter += 1
            call_number = counter
        return (500 if call_number <= 5 else 200), 0.01

    monkeypatch.setattr(runner, "send_request", fake_send_request)

    assert cast(Any, runner).run_concurrent("http://testserver", n_workers=8) == 1
    result = _last_result(runner)
    assert result["ok"] is False
    assert result["summary"]["error_count"] == 5
    assert result["summary"]["error_rate"] == 0.125
    assert any("error rate" in failure for failure in result["failures"])


def test_load_test_wrappers_support_result_output_arguments() -> None:
    windows = (REPO_ROOT / "scripts" / "run_load_test.ps1").read_text(encoding="utf-8")
    posix = (REPO_ROOT / "scripts" / "run_load_test.sh").read_text(encoding="utf-8")

    assert "config\\performance_baseline.yaml" in windows
    assert "ResultDir" in windows
    assert "--json-output" in windows
    assert "config/performance_baseline.yaml" in posix
    assert "--result-dir" in posix
    assert "--json-output" in posix
