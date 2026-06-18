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
    operator_report_ids: ClassVar[list[str]] = ["operator-smoke"]

    def do_GET(self) -> None:  # noqa: N802
        body = self.route_bodies.get(self.path, "")
        self.send_response(200)
        content_type = (
            "application/json"
            if (
                self.path.endswith("/artifact")
                or self.path.startswith("/report-runs/compare?")
                or "/diff?" in self.path
            )
            else "text/html; charset=utf-8"
        )
        self.send_header("content-type", content_type)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("content-length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length else ""
        self.post_bodies.append((self.path, parse_qs(raw_body)))
        self.send_response(303)
        report_index = sum(1 for path, _body in self.post_bodies if path == self.path) - 1
        report_id = self.operator_report_ids[min(report_index, len(self.operator_report_ids) - 1)]
        location = (
            f"/ui/report-runs/{report_id}"
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


def _operator_report_html() -> str:
    return _html(
        "Executive Summary",
        "Download dossier (.md)",
        "Download report (.json)",
        "View evidence lineage",
    )


def _operator_lineage_html(*body: str) -> str:
    return _html(
        "Evidence Lineage",
        "Sources: 1",
        "Evidence records: 2",
        "Claims: 1",
        "Sources -> Ingest Runs",
        "Claims -> Evidence",
        "Evidence -> Claims",
        *body,
    )


def _run_server(route_bodies: dict[str, str]) -> tuple[ThreadingHTTPServer, str]:
    handler = type(
        "SmokeHandler",
        (_SmokeHandler,),
        {
            "route_bodies": route_bodies,
            "post_bodies": [],
            "operator_report_ids": ["operator-smoke"],
        },
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
    routes["/ui/report-runs/operator-smoke"] = _operator_report_html()
    routes["/ui/report-runs/operator-smoke/lineage"] = _operator_lineage_html()
    server, base_url = _run_server(routes)
    handler = cast(type[_SmokeHandler], server.RequestHandlerClass)
    try:
        result = _run_smoke(base_url, "--operator-case-id", "BUN-slope", "--json")
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    operator_result = payload["routes"][-2]
    assert operator_result == {
        "label": "operator-case-report",
        "path": "/ui/report-runs/operator-smoke",
        "status": 200,
        "ok": True,
        "failures": [],
    }
    lineage_result = payload["routes"][-1]
    assert lineage_result == {
        "label": "operator-case-lineage",
        "path": "/ui/report-runs/operator-smoke/lineage",
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
    routes["/ui/report-runs/operator-smoke"] = _operator_report_html()
    routes["/ui/report-runs/operator-smoke/lineage"] = _operator_lineage_html()
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


def test_ui_runtime_smoke_operator_case_uses_csrf_with_reviewer_session() -> None:
    routes = _required_routes(reviewer_session=True)
    routes["/ui/"] = _html(
        "Land Diligence",
        '<input name="csrf_token" type="hidden" value="csrf-fixture">',
    )
    routes["/ui/report-runs/operator-smoke"] = _operator_report_html()
    routes["/ui/report-runs/operator-smoke/lineage"] = _operator_lineage_html()
    server, base_url = _run_server(routes)
    handler = cast(type[_SmokeHandler], server.RequestHandlerClass)
    try:
        result = _run_smoke(
            base_url,
            "--reviewer-id",
            "fixture-reviewer",
            "--reviewer-token",
            "fixture-token-123",
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


def test_ui_runtime_smoke_operator_case_can_assert_artifact_persistence() -> None:
    routes = _required_routes()
    routes["/ui/report-runs/operator-smoke"] = _operator_report_html()
    routes["/ui/report-runs/operator-smoke/lineage"] = _operator_lineage_html()
    routes["/report-runs/operator-smoke/artifact"] = json.dumps(
        {"artifact_metadata": {"persistence": "postgres+object_store"}},
    )
    server, base_url = _run_server(routes)
    try:
        result = _run_smoke(
            base_url,
            "--operator-case-id",
            "BUN-slope",
            "--expect-artifact-persistence",
            "postgres+object_store",
            "--json",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["routes"][-1]["ok"] is True


def test_ui_runtime_smoke_operator_case_can_follow_compare_and_diff() -> None:
    routes = _required_routes()
    routes["/ui/report-runs/operator-smoke-a"] = _operator_report_html()
    routes["/ui/report-runs/operator-smoke-a/lineage"] = _operator_lineage_html()
    routes["/ui/report-runs/operator-smoke-b"] = _operator_report_html()
    routes["/ui/compare?ids=operator-smoke-a&ids=operator-smoke-b"] = _html(
        "Compare Report Runs",
        "Review Status",
        "Delivery Status",
        "Delivery available",
        "View dossier",
        "Download JSON",
        "Lineage",
        "Change Review",
        "Same Area",
        "Added Claim Codes",
        "Removed Claim Codes",
        "Added Sources",
        "Removed Sources",
        "Evidence Count Delta",
        "Screening Tool Only.",
    )
    routes["/report-runs/compare?ids=operator-smoke-a%2Coperator-smoke-b"] = json.dumps(
        {
            "summaries": [
                {
                    "report_run_id": "operator-smoke-a",
                    "area_id": "area-smoke",
                    "intent_code": "rural_land_purchase",
                    "claims_count": 1,
                    "unknowns_count": 1,
                    "red_flags_count": 0,
                    "high_severity_claims": [],
                    "verification_tasks_count": 1,
                },
                {
                    "report_run_id": "operator-smoke-b",
                    "area_id": "area-smoke",
                    "intent_code": "rural_land_purchase",
                    "claims_count": 1,
                    "unknowns_count": 1,
                    "red_flags_count": 0,
                    "high_severity_claims": [],
                    "verification_tasks_count": 1,
                },
            ],
        },
    )
    routes["/report-runs/operator-smoke-b/diff?base_id=operator-smoke-a"] = json.dumps(
        {
            "report_run_id": "operator-smoke-b",
            "base_report_run_id": "operator-smoke-a",
            "area_id": "area-smoke",
            "same_area": True,
            "ruleset_changed": False,
            "added_claim_codes": [],
            "removed_claim_codes": [],
            "added_sources": [],
            "removed_sources": [],
            "evidence_count_delta": 0,
        },
    )
    server, base_url = _run_server(routes)
    handler = cast(type[_SmokeHandler], server.RequestHandlerClass)
    handler.operator_report_ids = ["operator-smoke-a", "operator-smoke-b"]
    try:
        result = _run_smoke(
            base_url,
            "--operator-case-id",
            "BUN-slope",
            "--compare-same-area",
            "--json",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    labels = [route["label"] for route in payload["routes"]]
    assert labels[-6:] == [
        "operator-case-report",
        "operator-case-lineage",
        "operator-case-report-compare",
        "operator-case-compare-ui",
        "operator-case-compare-api",
        "operator-case-diff-api",
    ]
    assert (
        "/ui/operator-cases/report",
        {"selected_county_case_id": ["BUN-slope"]},
    ) in handler.post_bodies
    assert handler.post_bodies.count(
        (
            "/ui/operator-cases/report",
            {"selected_county_case_id": ["BUN-slope"]},
        )
    ) == 2


def test_ui_runtime_smoke_compare_same_area_requires_operator_case() -> None:
    server, base_url = _run_server(_required_routes())
    try:
        result = _run_smoke(base_url, "--compare-same-area", "--json")
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "--compare-same-area requires --operator-case-id" in payload["error"]


def test_ui_runtime_smoke_compare_api_rejects_recommendation_semantics() -> None:
    routes = _required_routes()
    routes["/ui/report-runs/operator-smoke-a"] = _operator_report_html()
    routes["/ui/report-runs/operator-smoke-a/lineage"] = _operator_lineage_html()
    routes["/ui/report-runs/operator-smoke-b"] = _operator_report_html()
    routes["/ui/compare?ids=operator-smoke-a&ids=operator-smoke-b"] = _html(
        "Compare Report Runs",
        "Review Status",
        "Delivery Status",
        "Delivery available",
        "View dossier",
        "Download JSON",
        "Lineage",
        "Change Review",
        "Same Area",
        "Added Claim Codes",
        "Removed Claim Codes",
        "Added Sources",
        "Removed Sources",
        "Evidence Count Delta",
        "Screening Tool Only.",
    )
    routes["/report-runs/compare?ids=operator-smoke-a%2Coperator-smoke-b"] = json.dumps(
        {
            "summaries": [
                {
                    "report_run_id": "operator-smoke-a",
                    "area_id": "area-smoke",
                    "intent_code": "rural_land_purchase",
                    "claims_count": 1,
                    "unknowns_count": 1,
                    "red_flags_count": 0,
                    "high_severity_claims": [],
                    "verification_tasks_count": 1,
                    "recommendation": "choose this report",
                },
                {
                    "report_run_id": "operator-smoke-b",
                    "area_id": "area-smoke",
                    "intent_code": "rural_land_purchase",
                    "claims_count": 1,
                    "unknowns_count": 1,
                    "red_flags_count": 0,
                    "high_severity_claims": [],
                    "verification_tasks_count": 1,
                },
            ],
        },
    )
    routes["/report-runs/operator-smoke-b/diff?base_id=operator-smoke-a"] = json.dumps(
        {
            "report_run_id": "operator-smoke-b",
            "base_report_run_id": "operator-smoke-a",
            "area_id": "area-smoke",
            "same_area": True,
            "ruleset_changed": False,
            "added_claim_codes": [],
            "removed_claim_codes": [],
            "added_sources": [],
            "removed_sources": [],
            "evidence_count_delta": 0,
        },
    )
    server, base_url = _run_server(routes)
    handler = cast(type[_SmokeHandler], server.RequestHandlerClass)
    handler.operator_report_ids = ["operator-smoke-a", "operator-smoke-b"]
    try:
        result = _run_smoke(
            base_url,
            "--operator-case-id",
            "BUN-slope",
            "--compare-same-area",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 1
    assert "fail: operator-case-compare-api" in result.stdout
    assert "ranking/recommendation keys: recommendation" in result.stdout


def test_ui_runtime_smoke_operator_case_fails_on_artifact_persistence_mismatch() -> None:
    routes = _required_routes()
    routes["/ui/report-runs/operator-smoke"] = _operator_report_html()
    routes["/report-runs/operator-smoke/artifact"] = json.dumps(
        {"artifact_metadata": {"persistence": "memory"}},
    )
    server, base_url = _run_server(routes)
    try:
        result = _run_smoke(
            base_url,
            "--operator-case-id",
            "BUN-slope",
            "--expect-artifact-persistence",
            "postgres+object_store",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 1
    assert "artifact persistence mismatch" in result.stdout
    assert "postgres+object_store" in result.stdout
    assert "memory" in result.stdout


def test_ui_runtime_smoke_artifact_persistence_requires_operator_case() -> None:
    server, base_url = _run_server(_required_routes())
    try:
        result = _run_smoke(
            base_url,
            "--expect-artifact-persistence",
            "postgres+object_store",
            "--json",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "--expect-artifact-persistence requires --operator-case-id" in payload["error"]


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


def test_ui_runtime_smoke_operator_case_fails_when_lineage_records_missing() -> None:
    routes = _required_routes()
    routes["/ui/report-runs/operator-smoke"] = _operator_report_html()
    routes["/ui/report-runs/operator-smoke/lineage"] = _html(
        "Evidence Lineage",
        "Sources: 1",
        "Evidence records: 0",
        "Claims: 1",
        "No evidence records.",
    )
    server, base_url = _run_server(routes)
    try:
        result = _run_smoke(base_url, "--operator-case-id", "BUN-slope")
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 1
    assert (
        "fail: operator-case-lineage /ui/report-runs/operator-smoke/lineage status=200"
        in result.stdout
    )
    assert "found forbidden text: No evidence records." in result.stdout


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
