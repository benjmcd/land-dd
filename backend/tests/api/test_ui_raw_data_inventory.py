from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode
from app.domain.source_contracts import SourceContract
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def _valid_geojson() -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _source() -> SourceContract:
    return SourceContract(
        name="Raw inventory source",
        organization="Raw inventory test org",
        source_type="test fixture",
        domain="flood",
        license_status="approved",
        commercial_use_status="yes",
        redistribution_status="yes",
        cache_allowed="yes",
        export_allowed="yes",
        ai_use_allowed="yes",
        raw_data_allowed="yes",
        freshness_class="current-effective",
        last_checked_at="2026-06-20",
        review_owner="operator",
        review_status="approved",
        metadata={"source_registry_id": "DS-RAW"},
    )


def _seed_runtime_inventory(services: ApiServices) -> str:
    source = services.source_service.register(_source())
    area = services.area_service.create(
        AreaContract(
            label="raw inventory fixture area",
            geom_geojson=_valid_geojson(),
            geom_source="raw-data-ui-test",
        )
    )
    services.evidence_service.create_source_failure(
        area_id=area.area_id,
        source_id=source.source_id,
        method_code="raw_inventory_test",
        evidence_code="RAW_INVENTORY_SOURCE_FAILURE",
        domain="flood",
        observation="Raw inventory evidence is available for display.",
        caveat="raw inventory display fixture",
    )
    report_job = services.async_report_jobs.create(
        area_id=area.area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    report = services.report_service.create_report_run(
        area_id=area.area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        report_run_id=report_job.report_run_id,
    )
    services.async_report_jobs.mark_succeeded(report.report_run_id)
    services.live_connector_jobs.enqueue_nwi(area_id=area.area_id, max_features=1)
    return str(report.report_run_id)


def test_ui_raw_data_inventory_renders_runtime_counts_and_links() -> None:
    app = create_app()
    services = cast(ApiServices, app.state.services)
    report_run_id = _seed_runtime_inventory(services)
    client = TestClient(app)

    response = client.get("/ui/raw-data")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "Raw Data Inventory" in response.text
    assert "Sources" in response.text
    assert "Areas" in response.text
    assert "Evidence" in response.text
    assert "Claims" in response.text
    assert "Report Run Contracts" in response.text
    assert "Report Jobs" in response.text
    assert "Connector Review Items" in response.text
    assert "Live Connector Jobs" in response.text
    assert "Raw inventory source" in response.text
    assert "raw inventory fixture area" in response.text
    assert "Raw inventory evidence is available for display." in response.text
    assert report_run_id in response.text
    assert f'href="/ui/report-runs/{report_run_id}"' in response.text
    assert f'href="/report-runs/{report_run_id}/dossier?download=1"' in response.text
    assert f'href="/report-runs/{report_run_id}/artifact"' in response.text
    assert f'href="/ui/report-runs/{report_run_id}/lineage"' in response.text
    assert 'href="/ui/live-connector-jobs/' in response.text
    assert "succeeded" in response.text
    assert "queued" in response.text


def test_ui_raw_data_inventory_plain_get_is_read_only_on_empty_runtime() -> None:
    app = create_app()
    services = cast(ApiServices, app.state.services)
    client = TestClient(app)

    before_sources = services.source_service.list_all()
    before_areas = services.area_service.list_all()
    before_evidence = services.evidence_service.list_all()
    before_report_jobs = services.async_report_jobs.list_recent(limit=100)
    before_live_jobs = services.live_connector_jobs.list_recent(limit=100)

    response = client.get("/ui/raw-data")

    assert response.status_code == 200
    assert services.source_service.list_all() == before_sources
    assert services.area_service.list_all() == before_areas
    assert services.evidence_service.list_all() == before_evidence
    assert services.async_report_jobs.list_recent(limit=100) == before_report_jobs
    assert services.live_connector_jobs.list_recent(limit=100) == before_live_jobs
    assert "No sources." in response.text
    assert "No report jobs." in response.text
    assert "Local raw-data inventory view only" in response.text
    assert "does not seed fixtures" in response.text
    assert "does not run connectors" in response.text
    assert "does not create reports" in response.text


def test_ui_home_links_to_raw_data_inventory_with_summary_counts() -> None:
    app = create_app()
    services = cast(ApiServices, app.state.services)
    _seed_runtime_inventory(services)
    client = TestClient(app)

    response = client.get("/ui/")

    assert response.status_code == 200
    assert 'href="/ui/raw-data"' in response.text
    assert "Raw data inventory" in response.text
    assert "Runtime inventory" in response.text
    assert "sources:" in response.text
    assert "areas: 1" in response.text
    assert "evidence:" in response.text
    assert "report runs: 1" in response.text
    assert "report jobs: 1" in response.text
    assert "live jobs: 1" in response.text


def test_ui_home_inventory_summary_fails_closed_when_live_jobs_raise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app()
    services = cast(ApiServices, app.state.services)
    client = TestClient(app)

    def raise_list_recent(*, limit: int) -> list[object]:
        raise RuntimeError(f"live connector inventory unavailable for limit {limit}")

    monkeypatch.setattr(services.live_connector_jobs, "list_recent", raise_list_recent)

    response = client.get("/ui/")

    assert response.status_code == 200
    assert 'href="/ui/raw-data"' in response.text
    assert "Runtime inventory" in response.text
    assert "live jobs: n/a" in response.text
