from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

FIXTURE_SOURCE_ID = "55555555-5555-4555-8555-555555555555"
FIXTURE_AREA_ID = "44444444-4444-4444-8444-444444444444"
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
    parser.add_argument("--reviewer-id", default="demo-reviewer")
    args = parser.parse_args()

    client = ApiClient(args.base_url)
    health = client.request("GET", "/health")
    print(f"health: {health['status']} ({health['environment']})")

    seed_fixture_source(client)
    seed_fixture_area(client)

    connector_results = [
        run_connector(client, "fixture_flood_static", "flood_success"),
        run_connector(client, "fixture_zoning_static", "zoning_allowed"),
        run_connector(client, "fixture_access_static", "access_no_road"),
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
    )
    print(
        "report: "
        f"{report['report_run_id']} claims={len(report['claims'])} "
        f"red_flags={len(report['red_flags'])} unknowns={len(report['unknowns'])}"
    )

    failure_result = run_connector(client, "fixture_access_static", "access_failure")
    queue_item = client.request(
        "GET",
        f"/connector-review-queue/{failure_result['ingest_run_id']}",
    )
    if queue_item["status"] == "needs_review":
        approved = client.request(
            "POST",
            f"/connector-review-queue/{failure_result['ingest_run_id']}/approve",
            {
                "reviewer_id": args.reviewer_id,
                "reason": "demo review approval",
            },
        )
        print(f"review action: {approved['status']} by {args.reviewer_id}")
    else:
        print(f"review action: skipped; queue status is {queue_item['status']}")

    report_runs = client.request(
        "GET",
        f"/report-runs?area_id={FIXTURE_AREA_ID}&intent_code=homestead_feasibility",
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
        ok_statuses: tuple[int, ...] = (200, 201),
    ) -> Any:
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=20) as response:
                body = _read_json(response.read())
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
        "name": "Fixture Flood Source",
        "organization": "fixture-mvp-demo",
        "domain": "flood",
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


def seed_fixture_area(client: ApiClient) -> None:
    payload: dict[str, object] = {
        "area_id": FIXTURE_AREA_ID,
        "label": "Fixture MVP demo area",
        "geom_geojson": FIXTURE_AREA_GEOJSON,
        "geom_source": "demo fixture",
    }
    try:
        client.request("POST", "/areas", payload)
        print("area: created")
    except RuntimeError as exc:
        if "already registered" not in str(exc):
            raise
        print("area: already registered")


def run_connector(
    client: ApiClient,
    connector_name: str,
    fixture_key: str,
) -> dict[str, object]:
    result = client.request(
        "POST",
        "/connector-runs",
        {"connector_name": connector_name, "fixture_key": fixture_key},
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
