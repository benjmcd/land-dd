"""Live connector smoke driver.

Drives the four existing query-bbox routes once each for a small Buncombe NC bbox.
All connector logic lives in the existing API routes; this script only orchestrates
HTTP calls and writes a timestamped transcript.

Usage (called by run_live_smoke.ps1 / run_live_smoke.sh):
    py -3.12 scripts/run_live_smoke.py --api-url http://127.0.0.1:8103 [--output-dir local_artifacts]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Buncombe NC test bbox (-82.60,35.55 to -82.55,35.60)
# ---------------------------------------------------------------------------
BBOX = {"xmin": -82.60, "ymin": 35.55, "xmax": -82.55, "ymax": 35.60}

REVIEWER_ID = "fixture-reviewer"
REVIEWER_TOKEN = "fixture-token-123"
SMOKE_WORKSPACE_ID = "11111111-1111-4111-8111-111111111111"
SMOKE_USER_ID = "22222222-2222-4222-8222-222222222222"

# The four smoke legs, in order: (label, endpoint, request_body_key, body_extra)
_SMOKE_LEGS = [
    (
        "DS-001 USGS TNM",
        "/connector-runs/usgs-tnm/query-bbox",
        "bbox",
        {"max_sample_points": 9},
    ),
    (
        "DS-002 FEMA NFHL",
        "/connector-runs/fema-nfhl/query-bbox",
        "bbox",
        {"max_features": 100},
    ),
    (
        "DS-004 NWI",
        "/connector-runs/nwi/query-bbox",
        "bbox",
        {"max_features": 100},
    ),
    (
        "DS-003 SSURGO",
        "/connector-runs/ssurgo/query-bbox",
        "bbox",
        {"max_rows": 50},
    ),
]


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _post(base_url: str, path: str, body: dict, headers: dict | None = None) -> tuple[int, dict]:
    url = base_url.rstrip("/") + path
    data = json.dumps(body).encode()
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        try:
            body_text = exc.read().decode(errors="replace")
        except Exception:  # noqa: BLE001
            body_text = "<unreadable>"
        try:
            body_json = json.loads(body_text)
        except Exception:  # noqa: BLE001
            body_json = {"raw": body_text}
        return exc.code, body_json


def _reviewer_headers() -> dict[str, str]:
    return {
        "X-Reviewer-Id": REVIEWER_ID,
        "X-Reviewer-Token": REVIEWER_TOKEN,
    }


def _identity_headers() -> dict[str, str]:
    return {
        "X-Workspace-Id": SMOKE_WORKSPACE_ID,
        "X-User-Id": SMOKE_USER_ID,
    }


def _operator_headers() -> dict[str, str]:
    return {**_identity_headers(), **_reviewer_headers()}


def _wait_for_api(base_url: str, retries: int = 30, delay: float = 1.0) -> bool:
    url = base_url.rstrip("/") + "/health"
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=5):
                return True
        except Exception:  # noqa: BLE001
            time.sleep(delay)
    return False


def _register_sources(base_url: str, seeds_path: Path) -> list[str]:
    """Register DS-001 through DS-004 from the CSV seeds; return list of messages."""
    sys.path.insert(0, str(seeds_path.parent.parent / "backend"))
    from db.seeds.source_registry_seeds import load_registry_sources  # noqa: PLC0415

    sources = load_registry_sources(
        seeds_path,
        priority=None,  # load all so we can filter by Source ID
    )
    target_ids = {"DS-001", "DS-002", "DS-003", "DS-004"}
    messages = []
    for src in sources:
        if src.metadata.get("source_registry_id") not in target_ids:
            continue
        reg_id = src.metadata["source_registry_id"]
        body = json.loads(src.model_dump_json())
        status_code, resp = _post(base_url, "/sources", body, _reviewer_headers())
        if status_code in (200, 201, 409):
            messages.append(f"  source {reg_id}: registered (HTTP {status_code})")
        else:
            messages.append(f"  source {reg_id}: FAILED (HTTP {status_code}) {resp}")
    return messages


def _register_area(base_url: str, headers: dict[str, str]) -> str | None:
    """Register a Buncombe NC bbox area; return area_id string or None on failure."""
    body = {
        "area_type": "drawn_polygon",
        "geom_geojson": {
            "type": "Polygon",
            "coordinates": [
                [
                    [BBOX["xmin"], BBOX["ymin"]],
                    [BBOX["xmax"], BBOX["ymin"]],
                    [BBOX["xmax"], BBOX["ymax"]],
                    [BBOX["xmin"], BBOX["ymax"]],
                    [BBOX["xmin"], BBOX["ymin"]],
                ]
            ],
        },
    }
    status_code, resp = _post(base_url, "/areas", body, headers)
    if status_code in (200, 201):
        return str(resp.get("area_id"))
    return None


def run_smoke(base_url: str, output_dir: Path) -> int:
    """Run the four smoke legs; return 0 on full pass, 1 on any failure."""
    ts = _now_iso()
    transcript_path = output_dir / f"live_smoke_{ts}.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    transcript: dict = {
        "run_at": ts,
        "bbox": BBOX,
        "api_url": base_url,
        "setup": [],
        "legs": [],
        "summary": {},
    }

    print(f"[smoke] run_at={ts}  api={base_url}")
    print(f"[smoke] transcript will be written to: {transcript_path}")

    # ------------------------------------------------------------------
    # Wait for API
    # ------------------------------------------------------------------
    print("[smoke] waiting for API health check...")
    if not _wait_for_api(base_url):
        msg = "API did not become healthy within 30 s"
        transcript["summary"] = {"status": "FAIL", "reason": msg}
        transcript_path.write_text(json.dumps(transcript, indent=2, default=str))
        print(f"[smoke] FAIL: {msg}")
        return 1
    transcript["setup"].append("API health: OK")

    # ------------------------------------------------------------------
    # Register sources
    # ------------------------------------------------------------------
    root = Path(__file__).resolve().parents[1]
    seeds_csv = root / "registers" / "data_source_registry.csv"
    source_msgs = _register_sources(base_url, seeds_csv)
    transcript["setup"].extend(source_msgs)
    for m in source_msgs:
        print(f"[smoke] {m.strip()}")

    # ------------------------------------------------------------------
    # Register area
    # ------------------------------------------------------------------
    area_id = _register_area(base_url, _identity_headers())
    if area_id is None:
        msg = "Failed to register Buncombe NC test area"
        transcript["setup"].append(f"area registration: FAIL - {msg}")
        transcript["summary"] = {"status": "FAIL", "reason": msg}
        transcript_path.write_text(json.dumps(transcript, indent=2, default=str))
        print(f"[smoke] FAIL: {msg}")
        return 1
    transcript["setup"].append(f"area registered: {area_id}")
    print(f"[smoke] area registered: {area_id}")

    # ------------------------------------------------------------------
    # Reviewer auth headers
    # ------------------------------------------------------------------
    operator_headers = _operator_headers()

    # ------------------------------------------------------------------
    # Run each smoke leg
    # ------------------------------------------------------------------
    failures = 0
    for label, endpoint, bbox_key, extra in _SMOKE_LEGS:
        body: dict = {"area_id": area_id, bbox_key: BBOX}
        body.update(extra)

        leg_start = datetime.now(UTC).isoformat()
        print(f"[smoke] {label}: POST {endpoint} ...", end=" ", flush=True)
        status_code, resp = _post(base_url, endpoint, body, operator_headers)
        leg_end = datetime.now(UTC).isoformat()

        success = status_code in (200, 201, 202)
        result_label = "PASS" if success else "FAIL"
        if not success:
            failures += 1

        leg_record = {
            "label": label,
            "endpoint": endpoint,
            "request_body": body,
            "started_at": leg_start,
            "finished_at": leg_end,
            "http_status": status_code,
            "result": result_label,
            "response_summary": {
                "connector_name": resp.get("connector_name"),
                "retrieval_status": resp.get("retrieval_status"),
                "row_count": resp.get("row_count"),
                "evidence_input_count": resp.get("evidence_input_count"),
                "evidence_created_count": resp.get("evidence_created_count"),
                "source_failure_created_count": resp.get("source_failure_created_count"),
                "review_required": resp.get("review_required"),
                "queue_item_status": resp.get("queue_item_status"),
                "queue_name": resp.get("queue_name"),
                "source_registry_id": resp.get("source_registry_id"),
                "request_url": resp.get("request_url"),
                "error_detail": resp.get("detail") if not success else None,
            },
        }
        transcript["legs"].append(leg_record)

        retrieval = resp.get("retrieval_status", "?")
        ev_created = resp.get("evidence_created_count", "?")
        sf_count = resp.get("source_failure_created_count", "?")
        print(
            f"{result_label} (HTTP {status_code})"
            f" retrieval={retrieval} ev_created={ev_created} sf_count={sf_count}"
        )

    # ------------------------------------------------------------------
    # Write transcript
    # ------------------------------------------------------------------
    passed = failures == 0
    transcript["summary"] = {
        "status": "PASS" if passed else "FAIL",
        "legs_total": len(_SMOKE_LEGS),
        "legs_passed": len(_SMOKE_LEGS) - failures,
        "legs_failed": failures,
    }
    transcript_path.write_text(json.dumps(transcript, indent=2, default=str))
    print(
        f"[smoke] {'PASS' if passed else 'FAIL'} — "
        f"{len(_SMOKE_LEGS) - failures}/{len(_SMOKE_LEGS)} legs passed"
    )
    print(f"[smoke] transcript: {transcript_path}")
    return 0 if passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Live connector smoke driver.")
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8103",
        help="Base URL of the running API (default: http://127.0.0.1:8103).",
    )
    parser.add_argument(
        "--output-dir",
        default="local_artifacts",
        help="Directory for the timestamped transcript (default: local_artifacts).",
    )
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir)
    return run_smoke(args.api_url, output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
