from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ui_runtime_smoke.py"


class _SmokeHandler(BaseHTTPRequestHandler):
    route_bodies: ClassVar[dict[str, str]] = {}

    def do_GET(self) -> None:  # noqa: N802
        body = self.route_bodies.get(self.path, "")
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("content-length", "0"))
        if length:
            self.rfile.read(length)
        self.send_response(303)
        self.send_header("location", "/ui/")
        self.send_header("set-cookie", "land_dd_ui_reviewer=test; Path=/ui; HttpOnly")
        self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        return


def _html(*body: str) -> str:
    return (
        '<!doctype html><html><head><meta name="viewport" '
        'content="width=device-width, initial-scale=1"></head><body>'
        + "\n".join(body)
        + "</body></html>"
    )


def _required_routes(*, reviewer_session: bool = False) -> dict[str, str]:
    operations = ["Operations Dashboard"]
    if reviewer_session:
        operations.append("Using reviewer session")
    else:
        operations.append('name="reviewer_token"')
    return {
        "/ui/": _html("Land Diligence"),
        "/ui/report-runs": _html(
            "Report Runs",
            '<form method="GET" action="/ui/compare"></form>',
        ),
        "/ui/connector-review-queue": _html(
            "Connector Review Queue",
            "<select name='status'></select>",
        ),
        "/ui/operations": _html(*operations),
        "/ui/auth": _html('name="api_key"'),
        "/ui/auth/reviewer": _html('name="reviewer_id"', 'name="reviewer_token"'),
    }


def _run_server(route_bodies: dict[str, str]) -> tuple[ThreadingHTTPServer, str]:
    handler = type("SmokeHandler", (_SmokeHandler,), {"route_bodies": route_bodies})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    address = server.server_address
    assert isinstance(address, tuple)
    host = str(address[0])
    port = int(address[1])
    return server, f"http://{host}:{port}"


def _run_smoke(base_url: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--base-url", base_url, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_ui_runtime_smoke_script_passes_against_core_ui_routes() -> None:
    server, base_url = _run_server(_required_routes())
    try:
        result = _run_smoke(base_url, "--json")
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert {route["label"] for route in payload["routes"]} == {
        "api-key-auth",
        "connector-review-queue",
        "home",
        "operations",
        "report-runs",
        "reviewer-auth",
    }


def test_ui_runtime_smoke_script_supports_reviewer_session_expectations() -> None:
    server, base_url = _run_server(_required_routes(reviewer_session=True))
    try:
        result = _run_smoke(
            base_url,
            "--reviewer-id",
            "fixture-reviewer",
            "--reviewer-token",
            "fixture-token-123",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    assert "ok: operations /ui/operations status=200" in result.stdout


def test_ui_runtime_smoke_script_fails_closed_on_empty_page() -> None:
    routes = _required_routes()
    routes["/ui/report-runs"] = ""
    server, base_url = _run_server(routes)
    try:
        result = _run_smoke(base_url)
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 1
    assert "fail: report-runs /ui/report-runs status=200" in result.stdout
    assert "empty body" in result.stdout
