from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

FIXTURE_SOURCE_ID = "55555555-5555-4555-8555-555555555555"
FIXTURE_AREA_ID = "44444444-4444-4444-8444-444444444444"
DEMO_WORKSPACE_ID = "11111111-1111-4111-8111-111111111111"
DEMO_USER_ID = "22222222-2222-4222-8222-222222222222"
FIXTURE_AREA_GEOJSON: dict[str, object] = {
    "type": "Polygon",
    "coordinates": [
        [
            [-120.0, 38.0],
            [-119.9, 38.0],
            [-119.9, 38.1],
            [-120.0, 38.1],
            [-120.0, 38.0],
        ]
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the public API fixture-to-report MVP demo."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--reviewer-id", default=DEMO_USER_ID)
    parser.add_argument("--reviewer-token", default="fixture-token-123")
    parser.add_argument("--workspace-id", default=DEMO_WORKSPACE_ID)
    parser.add_argument("--user-id", default=DEMO_USER_ID)
    parser.add_argument("--identity-token")
    args = parser.parse_args()

    client = ApiClient(args.base_url)
    identity_headers = {
        "X-Workspace-Id": args.workspace_id,
        "X-User-Id": args.user_id,
    }
    if args.identity_token is not None:
        identity_headers["Authorization"] = f"Bearer {args.identity_token}"
    health = client.request("GET", "/health")
    print(f"health: {health['status']} ({health['environment']})")

    seed_fixture_source(client)
    seed_fixture_area(client, identity_headers)

    connector_results = [
        run_connector(
            client,
            "fixture_flood_static",
            "flood_success",
            identity_headers,
        ),
        run_connector(
            client,
            "fixture_zoning_static",
            "zoning_allowed",
            identity_headers,
        ),
        run_connector(
            client,
            "fixture_access_static",
            "access_no_road",
            identity_headers,
        ),
    ]
    created = sum(_int_field(result, "evidence_created") for result in connector_results)
    skipped = sum(_int_field(result, "evidence_skipped") for result in connector_results)
    print(f"connector evidence: created={created} skipped={skipped}")

    report = client.request(
        "POST",
        "/report-runs",
        {
            "area_id": FIXTURE_AREA_ID,
            "intent_code": "homestead_feasibility",
        },
        headers=identity_headers,
    )
    print(
        "report: "
        f"{report['report_run_id']} claims={len(report['claims'])} "
        f"red_flags={len(report['red_flags'])} unknowns={len(report['unknowns'])}"
    )

    # Step A: Approve the report run
    reviewer_headers = {
        "X-Reviewer-Id": args.reviewer_id,
        "X-Reviewer-Token": args.reviewer_token,
    }
    approved_report = client.request(
        "POST",
        f"/report-runs/{report['report_run_id']}/approve",
        {"reason": "demo review approval"},
        headers=reviewer_headers,
        ok_statuses=(200, 201),
    )
    print(f"report approval: {approved_report['review_status']} by {args.reviewer_id}")

    # Step B: Retrieve the dossier (text/markdown response)
    dossier_text = client.request(
        "GET",
        f"/report-runs/{report['report_run_id']}/dossier",
        headers=identity_headers,
        ok_statuses=(200,),
        parse_json=False,
    )
    lines = dossier_text.split("\n")[:5]
    print(f"dossier preview: {' | '.join(l.strip() for l in lines if l.strip())}")

    # Run failure connector, review it, then list reports
    failure_result = run_connector(
        client,
        "fixture_access_static",
        "access_failure",
        identity_headers,
    )
    queue_item = client.request(
        "GET",
        f"/connector-review-queue/{failure_result['ingest_run_id']}",
        headers=identity_headers,
    )
    if queue_item["status"] == "needs_review":
        approved = client.request(
            "POST",
            f"/connector-review-queue/{failure_result['ingest_run_id']}/approve",
            {
                "reviewer_id": args.reviewer_id,
                "reason": "demo review approval",
            },
            headers=identity_headers,
        )
        print(f"review action: {approved['status']} by {args.reviewer_id}")
    else:
        print(f"review action: skipped; queue status is {queue_item['status']}")

    report_runs = client.request(
        "GET",
        f"/report-runs?area_id={FIXTURE_AREA_ID}&intent_code=homestead_feasibility",
        headers=identity_headers,
    )
    print(f"listed report runs: {len(report_runs)}")


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
        *,
        headers: dict[str, str] | None = None,
        ok_statuses: tuple[int, ...] = (200, 201),
        parse_json: bool = True,
    ) -> Any:
        data = None
        request_headers = {"Accept": "application/json", **(headers or {})}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers=request_headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read()
                body = _read_json(raw) if parse_json else raw.decode("utf-8")
                if response.status not in ok_statuses:
                    raise RuntimeError(f"{method} {path} returned {response.status}: {body}")
                return body
        except HTTPError as exc:
            body = _read_json(exc.read())
            if exc.code in ok_statuses:
                return body
            raise RuntimeError(f"{method} {path} returned {exc.code}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(
                f"Could not reach API at {self.base_url}. Start it with scripts/run_api first."
            ) from exc


def seed_fixture_source(client: ApiClient) -> None:
    payload: dict[str, object] = {
        "source_id": FIXTURE_SOURCE_ID,
        "name": "Fixture Source",
        "organization": "fixture-mvp-demo",
        "domain": "fixture",
        "license_status": "approved",
        "commercial_use_status": "approved",
        "redistribution_status": "approved",
        "cache_allowed": "approved",
        "export_allowed": "approved",
        "raw_data_allowed": "approved",
        "ai_use_allowed": "approved",
        "review_status": "approved",
    }
    try:
        client.request("POST", "/sources", payload)
        print("source: created")
    except RuntimeError as exc:
        if "already registered" not in str(exc):
            raise
        print("source: already registered")


def seed_fixture_area(client: ApiClient, headers: dict[str, str]) -> None:
    payload: dict[str, object] = {
        "area_id": FIXTURE_AREA_ID,
        "label": "Fixture MVP demo area",
        "geom_geojson": FIXTURE_AREA_GEOJSON,
        "geom_source": "demo fixture",
    }
    try:
        client.request("POST", "/areas", payload, headers=headers)
        print("area: created")
    except RuntimeError as exc:
        if "already registered" not in str(exc):
            raise
        print("area: already registered")


def run_connector(
    client: ApiClient,
    connector_name: str,
    fixture_key: str,
    headers: dict[str, str],
) -> dict[str, object]:
    result = client.request(
        "POST",
        "/connector-runs",
        {"connector_name": connector_name, "fixture_key": fixture_key},
        headers=headers,
    )
    print(
        "connector: "
        f"{connector_name}/{fixture_key} status={result['retrieval_status']} "
        f"created={result['evidence_created']} skipped={result['evidence_skipped']} "
        f"review_required={result['review_required']}"
    )
    return result


def _read_json(raw: bytes) -> Any:
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def _int_field(record: dict[str, object], field: str) -> int:
    value = record[field]
    if not isinstance(value, int):
        raise RuntimeError(f"Expected integer field {field!r}, got {value!r}")
    return value


if __name__ == "__main__":
    main()
