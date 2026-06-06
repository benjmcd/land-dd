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


def _make_client_with_area() -> tuple[TestClient, str]:
    app = create_app()
    client = TestClient(app)
    resp = client.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert resp.status_code == 201
    return client, resp.json()["area_id"]


def _make_client_with_report_run() -> tuple[TestClient, str, str]:
    """Return (client, area_id, report_run_id) with a completed report run."""
    client, area_id = _make_client_with_area()
    post = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert post.status_code == 202
    report_run_id = post.json()["report_run_id"]
    # TestClient runs BackgroundTasks synchronously — report is complete here
    get = client.get(f"/report-runs/{report_run_id}")
    assert get.status_code == 200
    assert get.json()["status"] == "succeeded"
    return client, area_id, report_run_id


def test_report_lineage_not_found() -> None:
    client = TestClient(create_app())
    resp = client.get(f"/report-runs/{uuid4()}/lineage")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "report run not found"


def test_report_lineage_returns_chain() -> None:
    client, area_id, report_run_id = _make_client_with_report_run()
    resp = client.get(f"/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    data = resp.json()
    assert data["report_run_id"] == report_run_id
    assert data["area_id"] == area_id
    assert data["intent_code"] == "rural_land_purchase"
    assert "sources" in data
    assert "evidence_lineage" in data
    assert "claim_lineage" in data
    assert isinstance(data["sources"], list)
    assert isinstance(data["evidence_lineage"], list)
    assert isinstance(data["claim_lineage"], list)


def test_report_lineage_source_list() -> None:
    client, _area_id, report_run_id = _make_client_with_report_run()
    resp = client.get(f"/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    data = resp.json()
    # The fixture connector always produces at least one evidence record with a
    # source_id, so the fallback derivation must yield at least one source entry.
    assert len(data["sources"]) >= 1
    for src in data["sources"]:
        assert "source_id" in src
        assert "source_name" in src
        assert "ingest_run_ids" in src
        assert isinstance(src["ingest_run_ids"], list)


def test_report_lineage_evidence_has_claim_ids() -> None:
    client, _area_id, report_run_id = _make_client_with_report_run()
    resp = client.get(f"/report-runs/{report_run_id}/lineage")
    assert resp.status_code == 200
    data = resp.json()
    for ev_entry in data["evidence_lineage"]:
        assert "evidence_id" in ev_entry
        assert "source_id" in ev_entry
        assert "evidence_code" in ev_entry
        assert "domain" in ev_entry
        assert isinstance(ev_entry["claim_ids"], list)
