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
EXPECTED_DISABLED_AUTH_LABELS = [
    "auth-disabled-api-key",
    "auth-disabled-api-key-logout",
    "auth-disabled-reviewer",
    "auth-disabled-reviewer-logout",
    "auth-disabled-identity",
    "auth-disabled-identity-logout",
    "auth-disabled-ui-login",
    "auth-disabled-ui-account",
    "auth-disabled-login",
    "auth-disabled-account",
]


class _SmokeHandler(BaseHTTPRequestHandler):
    route_bodies: ClassVar[dict[str, str | list[str]]] = {}
    route_get_counts: ClassVar[dict[str, int]] = {}
    post_bodies: ClassVar[list[tuple[str, dict[str, list[str]]]]] = []
    operator_report_ids: ClassVar[list[str]] = ["operator-smoke"]
    supported_aoi_report_ids: ClassVar[list[str]] = ["supported-aoi-smoke"]
    custom_report_ids: ClassVar[list[str]] = ["custom-smoke"]

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in self.route_bodies:
            self.send_response(404)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"detail":"Not Found"}')
            return

        route_body = self.route_bodies[self.path]
        if isinstance(route_body, list):
            route_index = self.route_get_counts.get(self.path, 0)
            self.route_get_counts[self.path] = route_index + 1
            body = route_body[min(route_index, len(route_body) - 1)]
        else:
            body = route_body
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
        is_approval_path = self.path.startswith("/ui/report-runs/") and self.path.endswith(
            "/approve"
        )
        report_paths = {
            "/ui/operator-cases/report",
            "/ui/operator-cases/supported-aoi/report",
            "/ui/intake",
        }
        if (
            not is_approval_path
            and self.path not in report_paths
            and self.path not in self.route_bodies
        ):
            self.send_response(404)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"detail":"Not Found"}')
            return
        length = int(self.headers.get("content-length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length else ""
        self.post_bodies.append((self.path, parse_qs(raw_body)))
        self.send_response(303)
        report_index = sum(1 for path, _body in self.post_bodies if path == self.path) - 1
        if is_approval_path:
            location = self.path.removesuffix("/approve")
            self.route_bodies[location] = _operator_report_html()
        elif self.path == "/ui/operator-cases/report":
            report_id = self.operator_report_ids[
                min(report_index, len(self.operator_report_ids) - 1)
            ]
            location = f"/ui/report-runs/{report_id}"
        elif self.path == "/ui/operator-cases/supported-aoi/report":
            report_id = self.supported_aoi_report_ids[
                min(report_index, len(self.supported_aoi_report_ids) - 1)
            ]
            location = f"/ui/report-runs/{report_id}"
        elif self.path == "/ui/intake":
            report_id = self.custom_report_ids[
                min(report_index, len(self.custom_report_ids) - 1)
            ]
            location = f"/ui/report-runs/{report_id}"
        else:
            location = "/ui/"
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


def _required_routes(*, reviewer_session: bool = False) -> dict[str, str | list[str]]:
    operations = ["Operations Dashboard"]
    if reviewer_session:
        operations.append("Using reviewer session")
    else:
        operations.append('name="reviewer_token"')
    return {
        "/ui/": _html("Land Diligence"),
        "/ui/raw-data": _html(
            "Raw Data Inventory",
            "Local raw-data inventory view only",
            "does not seed fixtures",
            "does not run connectors",
            "does not create reports",
            "does not approve DS-017",
        ),
        "/ui/report-runs": _html(
            "Report Runs",
            '<form method="GET" action="/ui/compare"></form>',
        ),
        "/ui/connector-review-queue": _html(
            "Connector Review Queue",
            "<select name='status'></select>",
        ),
        "/ui/operations": _html(*operations),
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


def _pending_report_html(*body: str) -> str:
    return _html(
        "Report Pending Approval",
        "Approve Report",
        "Review status: needs_review",
        *body,
    )


def _run_server(route_bodies: dict[str, str | list[str]]) -> tuple[ThreadingHTTPServer, str]:
    handler = type(
        "SmokeHandler",
        (_SmokeHandler,),
        {
            "route_bodies": route_bodies,
            "route_get_counts": {},
            "post_bodies": [],
            "operator_report_ids": ["operator-smoke"],
            "custom_report_ids": ["custom-smoke"],
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
        "raw-data",
        "report-runs",
        "connector-review-queue",
        "operations",
        *EXPECTED_DISABLED_AUTH_LABELS,
    ]
    for route in payload["routes"]:
        if route["label"].startswith("auth-disabled"):
            assert route["status"] == 404
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


def test_ui_runtime_smoke_supported_aoi_flag_posts_and_checks_report_page() -> None:
    routes = _required_routes()
    routes["/ui/report-runs/supported-aoi-smoke"] = _operator_report_html()
    routes["/ui/report-runs/supported-aoi-smoke/lineage"] = _operator_lineage_html()
    server, base_url = _run_server(routes)
    handler = cast(type[_SmokeHandler], server.RequestHandlerClass)
    try:
        result = _run_smoke(
            base_url,
            "--supported-aoi-area-id",
            "33333333-3333-4333-8333-333333333333",
            "--json",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    supported_result = payload["routes"][-2]
    assert supported_result == {
        "label": "supported-aoi-report",
        "path": "/ui/report-runs/supported-aoi-smoke",
        "status": 200,
        "ok": True,
        "failures": [],
    }
    lineage_result = payload["routes"][-1]
    assert lineage_result == {
        "label": "supported-aoi-lineage",
        "path": "/ui/report-runs/supported-aoi-smoke/lineage",
        "status": 200,
        "ok": True,
        "failures": [],
    }
    assert (
        "/ui/operator-cases/supported-aoi/report",
        {
            "area_id": ["33333333-3333-4333-8333-333333333333"],
            "intent": ["rural_land_purchase"],
        },
    ) in handler.post_bodies


def test_ui_runtime_smoke_custom_aoi_fixture_posts_and_checks_report_page() -> None:
    routes = _required_routes()
    routes["/ui/report-runs/custom-smoke"] = _operator_report_html()
    routes["/ui/report-runs/custom-smoke/lineage"] = _operator_lineage_html()
    server, base_url = _run_server(routes)
    handler = cast(type[_SmokeHandler], server.RequestHandlerClass)
    try:
        result = _run_smoke(
            base_url,
            "--custom-aoi-fixture",
            str(ROOT / "tests" / "fixtures" / "geometries" / "valid_polygon.geojson"),
            "--json",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    custom_result = payload["routes"][-2]
    assert custom_result == {
        "label": "custom-aoi-report",
        "path": "/ui/report-runs/custom-smoke",
        "status": 200,
        "ok": True,
        "failures": [],
    }
    lineage_result = payload["routes"][-1]
    assert lineage_result == {
        "label": "custom-aoi-lineage",
        "path": "/ui/report-runs/custom-smoke/lineage",
        "status": 200,
        "ok": True,
        "failures": [],
    }
    custom_posts = [body for path, body in handler.post_bodies if path == "/ui/intake"]
    assert len(custom_posts) == 1
    custom_body = custom_posts[0]
    assert custom_body["intent"] == ["rural_land_purchase"]
    assert json.loads(custom_body["area_geojson"][0])["type"] == "Polygon"


def test_ui_runtime_smoke_custom_aoi_waits_for_report_delivery_page() -> None:
    routes = _required_routes()
    routes["/ui/report-runs/custom-smoke"] = [
        _html("Generating Report", "Status: queued"),
        _operator_report_html(),
    ]
    routes["/ui/report-runs/custom-smoke/lineage"] = _operator_lineage_html()
    server, base_url = _run_server(routes)
    handler = cast(type[_SmokeHandler], server.RequestHandlerClass)
    try:
        result = _run_smoke(
            base_url,
            "--custom-aoi-fixture",
            str(ROOT / "tests" / "fixtures" / "geometries" / "valid_polygon.geojson"),
            "--json",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["routes"][-2]["label"] == "custom-aoi-report"
    assert payload["routes"][-2]["ok"] is True
    assert handler.route_get_counts["/ui/report-runs/custom-smoke"] >= 2


def test_ui_runtime_smoke_custom_aoi_approves_pending_report_with_reviewer_session() -> None:
    routes = _required_routes(reviewer_session=True)
    routes["/ui/"] = _html(
        "Land Diligence",
        '<input name="csrf_token" type="hidden" value="csrf-home">',
    )
    routes["/ui/auth/reviewer"] = _html("Reviewer session")
    routes["/ui/report-runs/custom-smoke"] = _pending_report_html(
        '<input name="csrf_token" type="hidden" value="csrf-report">',
    )
    routes["/ui/report-runs/custom-smoke/lineage"] = _operator_lineage_html()
    routes["/report-runs/custom-smoke/artifact"] = json.dumps(
        {"artifact_metadata": {"persistence": "postgres+object_store"}},
    )
    server, base_url = _run_server(routes)
    handler = cast(type[_SmokeHandler], server.RequestHandlerClass)
    try:
        result = _run_smoke(
            base_url,
            "--reviewer-id",
            "fixture-reviewer",
            "--reviewer-token",
            "fixture-token-123",
            "--custom-aoi-fixture",
            str(ROOT / "tests" / "fixtures" / "geometries" / "valid_polygon.geojson"),
            "--report-wait-seconds",
            "0.1",
            "--expect-artifact-persistence",
            "postgres+object_store",
            "--json",
        )
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["routes"][-2]["label"] == "custom-aoi-report"
    assert payload["routes"][-2]["ok"] is True
    assert (
        "/ui/report-runs/custom-smoke/approve",
        {"csrf_token": ["csrf-report"]},
    ) in handler.post_bodies


def test_ui_runtime_smoke_operator_case_uses_csrf_with_api_key_cookie() -> None:
    routes = _required_routes()
    routes["/ui/"] = _html(
        "Land Diligence",
        '<input name="csrf_token" type="hidden" value="csrf-fixture">',
    )
    routes["/ui/auth"] = _html('name="api_key"')
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
    routes["/ui/auth/reviewer"] = _html("Reviewer session")
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


def test_ui_runtime_smoke_operator_case_uses_direct_reviewer_fields() -> None:
    routes = _required_routes()
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
            "reviewer_id": ["fixture-reviewer"],
            "reviewer_token": ["fixture-token-123"],
        },
    ) in handler.post_bodies
    payload = json.loads(result.stdout)
    reviewer_disabled = next(
        route for route in payload["routes"] if route["label"] == "auth-disabled-reviewer"
    )
    assert reviewer_disabled["path"] == "/ui/auth/reviewer"
    assert reviewer_disabled["status"] == 404
    assert reviewer_disabled["ok"] is True


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
    routes["/ui/"] = _html(
        "Land Diligence",
        '<input name="csrf_token" type="hidden" value="csrf-fixture">',
    )
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
            "--reviewer-id",
            "fixture-reviewer",
            "--reviewer-token",
            "fixture-token-123",
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
        {
            "selected_county_case_id": ["BUN-slope"],
            "reviewer_id": ["fixture-reviewer"],
            "reviewer_token": ["fixture-token-123"],
        },
    ) in handler.post_bodies
    assert (
        "/ui/operator-cases/report",
        (
            {
                "selected_county_case_id": ["BUN-slope"],
                "reviewer_id": ["fixture-reviewer"],
                "reviewer_token": ["fixture-token-123"],
                "csrf_token": ["csrf-fixture"],
            }
        ),
    ) in handler.post_bodies


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
    routes = _required_routes(reviewer_session=True)
    routes["/ui/auth/reviewer"] = _html("Reviewer session")
    routes["/ui/auth"] = _html('name="api_key"')
    server, base_url = _run_server(routes)
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
    assert "ok: reviewer-auth /ui/auth/reviewer status=200" in result.stdout


def test_ui_runtime_smoke_script_supports_api_key_auth_when_requested() -> None:
    routes = _required_routes()
    routes["/ui/auth"] = _html('name="api_key"')
    server, base_url = _run_server(routes)
    try:
        result = _run_smoke(base_url, "--api-key", "fixture-key")
    finally:
        server.shutdown()
        server.server_close()

    assert result.returncode == 0, result.stderr + result.stdout
    assert "ok: api-key-auth /ui/auth status=200" in result.stdout


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
