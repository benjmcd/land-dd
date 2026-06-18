from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener


@dataclass(frozen=True)
class RouteCheck:
    label: str
    path: str
    required: tuple[str, ...]
    forbidden: tuple[str, ...] = ("Traceback", "Internal Server Error")
    expect_html: bool = True
    expect_viewport: bool = True


@dataclass
class RouteResult:
    label: str
    path: str
    status: int | None
    ok: bool
    failures: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "path": self.path,
            "status": self.status,
            "ok": self.ok,
            "failures": self.failures,
        }


class CsrfTokenParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.token: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "input":
            return
        fields = dict(attrs)
        if fields.get("name") == "csrf_token":
            self.token = fields.get("value")


def build_route_checks(*, reviewer_session: bool) -> list[RouteCheck]:
    operations_forbidden = () if not reviewer_session else ('name="reviewer_token"',)
    operations_required: tuple[str, ...] = ("Operations Dashboard",)
    if not reviewer_session:
        operations_required = (*operations_required, "reviewer_token")
    else:
        operations_required = (*operations_required, "Using reviewer session")

    return [
        RouteCheck("home", "/ui/", ("Land Diligence",)),
        RouteCheck(
            "report-runs",
            "/ui/report-runs",
            ("Report Runs", '<form method="GET" action="/ui/compare"'),
            forbidden=("Traceback", "Internal Server Error", "<script>"),
        ),
        RouteCheck(
            "connector-review-queue",
            "/ui/connector-review-queue",
            ("Connector Review Queue", "<select name='status'>"),
        ),
        RouteCheck(
            "operations",
            "/ui/operations",
            operations_required,
            forbidden=("Traceback", "Internal Server Error", *operations_forbidden),
        ),
        RouteCheck("api-key-auth", "/ui/auth", ('name="api_key"',)),
        RouteCheck(
            "reviewer-auth",
            "/ui/auth/reviewer",
            ('name="reviewer_id"', 'name="reviewer_token"'),
        ),
    ]


OPERATOR_CASE_REPORT_CHECK = RouteCheck(
    "operator-case-report",
    "/ui/operator-cases/report",
    (
        "Executive Summary",
        "Download dossier (.md)",
        "Download report (.json)",
        "View evidence lineage",
    ),
)


def request_form(opener: Any, url: str, fields: dict[str, str], timeout: float) -> None:
    body = urlencode(fields).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"content-type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with opener.open(request, timeout=timeout) as response:
        if response.status >= 400:
            raise RuntimeError(f"POST {url} returned HTTP {response.status}")


def extract_csrf_token(html: str) -> str | None:
    parser = CsrfTokenParser()
    parser.feed(html)
    return parser.token


def fetch_csrf_token(opener: Any, base_url: str, timeout: float) -> str | None:
    url = urljoin(base_url.rstrip("/") + "/", "ui/")
    with opener.open(url, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
    return extract_csrf_token(body)


def fetch_route(opener: Any, base_url: str, check: RouteCheck, timeout: float) -> RouteResult:
    url = urljoin(base_url.rstrip("/") + "/", check.path.lstrip("/"))
    failures: list[str] = []
    status: int | None = None
    try:
        with opener.open(url, timeout=timeout) as response:
            status = int(response.status)
            content_type = response.headers.get("content-type", "")
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        status = int(exc.code)
        body = exc.read().decode("utf-8", errors="replace")
        content_type = exc.headers.get("content-type", "")
        failures.append(f"HTTP {status}")
    except URLError as exc:
        return RouteResult(
            check.label,
            check.path,
            None,
            False,
            [f"runtime unavailable: {exc.reason}"],
        )

    if status != 200:
        failures.append(f"expected HTTP 200, got {status}")
    if not body.strip():
        failures.append("empty body")
    if check.expect_html and "text/html" not in content_type.lower():
        failures.append(f"expected text/html content-type, got {content_type or '<missing>'}")
    if check.expect_viewport and 'name="viewport"' not in body:
        failures.append("missing viewport meta")
    for text in check.required:
        if text not in body:
            failures.append(f"missing required text: {text}")
    for text in check.forbidden:
        if text in body:
            failures.append(f"found forbidden text: {text}")

    return RouteResult(check.label, check.path, status, not failures, failures)


def result_path_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.query:
        return f"{parsed.path}?{parsed.query}"
    return parsed.path


def artifact_path_for_ui_report(path: str) -> str | None:
    path_only = urlparse(path).path
    prefix = "/ui/report-runs/"
    if not path_only.startswith(prefix):
        return None
    report_run_id = path_only[len(prefix) :].split("/", 1)[0]
    if not report_run_id:
        return None
    return f"/report-runs/{report_run_id}/artifact"


def check_artifact_persistence(
    opener: Any,
    base_url: str,
    report_ui_path: str,
    expected_persistence: str,
    timeout: float,
) -> list[str]:
    artifact_path = artifact_path_for_ui_report(report_ui_path)
    if artifact_path is None:
        return [f"could not derive artifact route from final path: {report_ui_path}"]
    url = urljoin(base_url.rstrip("/") + "/", artifact_path.lstrip("/"))
    try:
        with opener.open(url, timeout=timeout) as response:
            status = int(response.status)
            content_type = response.headers.get("content-type", "")
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return [f"artifact persistence check returned HTTP {int(exc.code)}: {body[:200]}"]
    except URLError as exc:
        return [f"artifact persistence check failed: {exc.reason}"]

    failures: list[str] = []
    if status != 200:
        failures.append(f"artifact persistence check expected HTTP 200, got {status}")
    if "application/json" not in content_type.lower():
        failures.append(
            "artifact persistence check expected application/json, got "
            f"{content_type or '<missing>'}"
        )
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        return [*failures, f"artifact persistence check returned invalid JSON: {exc}"]
    metadata = payload.get("artifact_metadata")
    if not isinstance(metadata, dict):
        failures.append("artifact persistence check missing artifact_metadata object")
        return failures
    actual = metadata.get("persistence")
    if actual != expected_persistence:
        failures.append(
            "artifact persistence mismatch: "
            f"expected {expected_persistence!r}, got {actual!r}"
        )
    return failures


def post_operator_case_report(
    opener: Any,
    base_url: str,
    case_id: str,
    timeout: float,
    *,
    include_csrf: bool,
    expected_artifact_persistence: str,
) -> RouteResult:
    check = OPERATOR_CASE_REPORT_CHECK
    url = urljoin(base_url.rstrip("/") + "/", "ui/operator-cases/report")
    fields = {"selected_county_case_id": case_id}
    failures: list[str] = []
    status: int | None = None
    final_path = check.path

    if include_csrf:
        try:
            csrf_token = fetch_csrf_token(opener, base_url, timeout)
        except HTTPError as exc:
            csrf_token = None
            failures.append(f"csrf token fetch returned HTTP {int(exc.code)}")
        except URLError as exc:
            csrf_token = None
            failures.append(f"csrf token fetch failed: {exc.reason}")
        if csrf_token:
            fields["csrf_token"] = csrf_token
        else:
            failures.append("missing csrf token on /ui/")

    try:
        body_bytes = urlencode(fields).encode("utf-8")
        request = Request(
            url,
            data=body_bytes,
            headers={"content-type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with opener.open(request, timeout=timeout) as response:
            status = int(response.status)
            content_type = response.headers.get("content-type", "")
            body = response.read().decode("utf-8", errors="replace")
            final_path = result_path_from_url(response.geturl())
    except HTTPError as exc:
        status = int(exc.code)
        body = exc.read().decode("utf-8", errors="replace")
        content_type = exc.headers.get("content-type", "")
        final_path = result_path_from_url(exc.geturl())
        failures.append(f"HTTP {status}")
    except URLError as exc:
        return RouteResult(
            check.label,
            final_path,
            None,
            False,
            [f"runtime unavailable: {exc.reason}"],
        )

    if status != 200:
        failures.append(f"expected HTTP 200, got {status}")
    if not body.strip():
        failures.append("empty body")
    if check.expect_html and "text/html" not in content_type.lower():
        failures.append(f"expected text/html content-type, got {content_type or '<missing>'}")
    if check.expect_viewport and 'name="viewport"' not in body:
        failures.append("missing viewport meta")
    for text in check.required:
        if text not in body:
            failures.append(f"missing required text: {text}")
    for text in check.forbidden:
        if text in body:
            failures.append(f"found forbidden text: {text}")
    if expected_artifact_persistence:
        failures.extend(
            check_artifact_persistence(
                opener,
                base_url,
                final_path,
                expected_artifact_persistence,
                timeout,
            )
        )

    return RouteResult(check.label, final_path, status, not failures, failures)


def run_smoke(args: argparse.Namespace) -> list[RouteResult]:
    cookie_jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar))
    base_url = args.base_url.rstrip("/")

    if args.api_key:
        request_form(opener, f"{base_url}/ui/auth", {"api_key": args.api_key}, args.timeout)

    reviewer_session = bool(args.reviewer_id or args.reviewer_token)
    if reviewer_session:
        if not args.reviewer_id or not args.reviewer_token:
            raise RuntimeError("--reviewer-id and --reviewer-token must be provided together")
        request_form(
            opener,
            f"{base_url}/ui/auth/reviewer",
            {
                "reviewer_id": args.reviewer_id,
                "reviewer_token": args.reviewer_token,
            },
            args.timeout,
        )
    if args.expect_artifact_persistence and not args.operator_case_id:
        raise RuntimeError("--expect-artifact-persistence requires --operator-case-id")

    results = [
        fetch_route(opener, base_url, check, args.timeout)
        for check in build_route_checks(reviewer_session=reviewer_session)
    ]
    if args.operator_case_id:
        results.append(
            post_operator_case_report(
                opener,
                base_url,
                args.operator_case_id,
                args.timeout,
                include_csrf=bool(args.api_key) or reviewer_session,
                expected_artifact_persistence=args.expect_artifact_persistence,
            )
        )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-check the running land_dd server-rendered UI.",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--reviewer-id", default="")
    parser.add_argument("--reviewer-token", default="")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument(
        "--operator-case-id",
        default="",
        help="opt in to creating and checking one selected-county UI report",
    )
    parser.add_argument(
        "--expect-artifact-persistence",
        default="",
        help="with --operator-case-id, assert final report artifact persistence value",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        results = run_smoke(args)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ui runtime smoke failed: {exc}", file=sys.stderr)
        return 1

    ok = all(result.ok for result in results)
    if args.json:
        print(json.dumps({"ok": ok, "routes": [r.as_dict() for r in results]}, indent=2))
    else:
        for result in results:
            status = result.status if result.status is not None else "unavailable"
            marker = "ok" if result.ok else "fail"
            print(f"{marker}: {result.label} {result.path} status={status}")
            for failure in result.failures:
                print(f"  - {failure}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
