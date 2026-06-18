from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def _valid_geojson() -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _make_client() -> TestClient:
    return TestClient(create_app())


FORBIDDEN_COMPARE_KEYS = {
    "rank",
    "ranking",
    "recommendation",
    "recommended",
    "recommendations",
    "suitability_score",
}
COMPARE_SUMMARY_KEYS = {
    "report_run_id",
    "area_id",
    "intent_code",
    "claims_count",
    "unknowns_count",
    "red_flags_count",
    "high_severity_claims",
    "verification_tasks_count",
}
DIFF_KEYS = {
    "report_run_id",
    "base_report_run_id",
    "area_id",
    "same_area",
    "ruleset_changed",
    "added_claim_codes",
    "removed_claim_codes",
    "added_sources",
    "removed_sources",
    "evidence_count_delta",
}


def _assert_no_forbidden_keys(value: object) -> None:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_COMPARE_KEYS & {str(key).lower() for key in value}
        assert not forbidden, f"forbidden compare/diff keys present: {sorted(forbidden)}"
        for nested in value.values():
            _assert_no_forbidden_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_forbidden_keys(nested)


def _create_area(client: TestClient) -> str:
    resp = client.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert resp.status_code == 201
    return str(resp.json()["area_id"])


def _create_report_run(client: TestClient, area_id: str) -> str:
    post = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert post.status_code == 202
    return str(post.json()["report_run_id"])


# ---------------------------------------------------------------------------
# US-080 compare
# ---------------------------------------------------------------------------


def test_compare_requires_min_2_ids() -> None:
    client = _make_client()
    area_id = _create_area(client)
    run_id = _create_report_run(client, area_id)
    resp = client.get(f"/report-runs/compare?ids={run_id}")
    assert resp.status_code == 400
    assert "2" in resp.json()["detail"]


def test_compare_requires_max_4_ids() -> None:
    client = _make_client()
    area_id = _create_area(client)
    ids = ",".join(_create_report_run(client, area_id) for _ in range(5))
    resp = client.get(f"/report-runs/compare?ids={ids}")
    assert resp.status_code == 400
    assert "4" in resp.json()["detail"]


def test_compare_unknown_id() -> None:
    client = _make_client()
    area_id = _create_area(client)
    good_id = _create_report_run(client, area_id)
    missing_id = str(uuid4())
    resp = client.get(f"/report-runs/compare?ids={good_id},{missing_id}")
    assert resp.status_code == 404


def test_compare_returns_summaries() -> None:
    client = _make_client()
    area1 = _create_area(client)
    area2 = _create_area(client)
    run1 = _create_report_run(client, area1)
    run2 = _create_report_run(client, area2)

    resp = client.get(f"/report-runs/compare?ids={run1},{run2}")
    assert resp.status_code == 200
    data = resp.json()
    assert "summaries" in data
    summaries = data["summaries"]
    assert len(summaries) == 2
    ids_returned = {s["report_run_id"] for s in summaries}
    assert run1 in ids_returned
    assert run2 in ids_returned
    for s in summaries:
        assert set(s) == COMPARE_SUMMARY_KEYS
        _assert_no_forbidden_keys(s)
    _assert_no_forbidden_keys(data)


# ---------------------------------------------------------------------------
# US-081 diff
# ---------------------------------------------------------------------------


def test_diff_not_found() -> None:
    client = _make_client()
    area_id = _create_area(client)
    run_id = _create_report_run(client, area_id)
    missing = str(uuid4())
    # target run missing
    resp = client.get(f"/report-runs/{missing}/diff?base_id={run_id}")
    assert resp.status_code == 404
    # base run missing
    resp2 = client.get(f"/report-runs/{run_id}/diff?base_id={missing}")
    assert resp2.status_code == 404


def test_diff_different_areas() -> None:
    client = _make_client()
    area1 = _create_area(client)
    area2 = _create_area(client)
    run1 = _create_report_run(client, area1)
    run2 = _create_report_run(client, area2)
    resp = client.get(f"/report-runs/{run1}/diff?base_id={run2}")
    assert resp.status_code == 400
    assert "area_id" in resp.json()["detail"]


def test_diff_same_area() -> None:
    client = _make_client()
    area_id = _create_area(client)
    run1 = _create_report_run(client, area_id)
    run2 = _create_report_run(client, area_id)

    resp = client.get(f"/report-runs/{run1}/diff?base_id={run2}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["report_run_id"] == run1
    assert data["base_report_run_id"] == run2
    assert data["area_id"] == area_id
    assert data["same_area"] is True
    assert set(data) == DIFF_KEYS
    _assert_no_forbidden_keys(data)
    assert "ruleset_changed" in data
    assert isinstance(data["added_claim_codes"], list)
    assert isinstance(data["removed_claim_codes"], list)
    assert isinstance(data["added_sources"], list)
    assert isinstance(data["removed_sources"], list)
    assert isinstance(data["evidence_count_delta"], int)
