from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar, cast
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ui_runtime_smoke.py"


class _SmokeHandler(BaseHTTPRequestHandler):
    route_bodies: ClassVar[dict[str, str]] = {}
    post_bodies: ClassVar[list[tuple[str, dict[str, list[str]]]]] = []

    def do_GET(self) -> None:  # noqa: N802
        body = self.route_bodies.get(self.path, "")
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("content-length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length else ""
        self.post_bodies.append((self.path, parse_qs(raw_body)))
        self.send_response(303)
        location = (
            "/ui/report-runs/operator-smoke"
            if self.path == "/ui/operator-cases/report"
            else "/ui/"
        )
        self.send_header("location", location)
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
    handler = type(
        "SmokeHandler",
        (_SmokeHandler,),
        {"route_bodies": route_bodies, "post_bodies": []},
    )
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
    labels = [route["label"] for route in payload["routes"]]
    assert labels == [
        "home",
        "report-runs",
        "connector-review-queue",
        "operations",
        "api-key-auth",
        "reviewer-auth",
    ]
    assert "operator-case-report" not in labels


def test_ui_runtime_smoke_operator_case_flag_posts_and_checks_report_page() -> None:
    routes = _required_routes()
    routes["/ui/report-runs/operator-smoke"] = _html(
        "Executive Summary",
        "Download dossier (.md)",
        "Download report (.json)",
        "View evidence lineage",
    )
    server, base_url = _run_server(routes)
    handler = cast(type[_SmokeHandler], server.RequestHandlerClass)
    try:
        result = _run_smoke(base_url, "--operator-case-id", "BUN-slope", "--json")
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    operator_result = payload["routes"][-1]
    assert operator_result == {
        "label": "operator-case-report",
        "path": "/ui/report-runs/operator-smoke",
        "status": 200,
        "ok": True,
        "failures": [],
    }
    assert (
        "/ui/operator-cases/report",
        {"selected_county_case_id": ["BUN-slope"]},
    ) in handler.post_bodies


def test_ui_runtime_smoke_operator_case_uses_csrf_with_api_key_cookie() -> None:
    routes = _required_routes()
    routes["/ui/"] = _html(
        "Land Diligence",
        '<input name="csrf_token" type="hidden" value="csrf-fixture">',
    )
    routes["/ui/report-runs/operator-smoke"] = _html(
        "Executive Summary",
        "Download dossier (.md)",
        "Download report (.json)",
        "View evidence lineage",
    )
    server, base_url = _run_server(routes)
    handler = cast(type[_SmokeHandler], server.RequestHandlerClass)
    try:
        result = _run_smoke(
            base_url,
            "--api-key",
            "fixture-key",
            "--operator-case-id",
            "BUN-slope",
            "--json",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    assert (
        "/ui/operator-cases/report",
        {
            "selected_county_case_id": ["BUN-slope"],
            "csrf_token": ["csrf-fixture"],
        },
    ) in handler.post_bodies


def test_ui_runtime_smoke_operator_case_fails_when_report_delivery_link_missing() -> None:
    routes = _required_routes()
    routes["/ui/report-runs/operator-smoke"] = _html(
        "Executive Summary",
        "Download dossier (.md)",
        "View evidence lineage",
    )
    server, base_url = _run_server(routes)
    try:
        result = _run_smoke(base_url, "--operator-case-id", "BUN-slope")
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 1
    assert (
        "fail: operator-case-report /ui/report-runs/operator-smoke status=200"
        in result.stdout
    )
    assert "missing required text: Download report (.json)" in result.stdout


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
