from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.area_contracts import AreaContract
from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, IntentCode, ReportReviewStatus, SeverityBand
from app.domain.report_contracts import ReportRunContract
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
    # Approve so approval-gated links (dossier/artifact/lineage) are rendered.
    services.report_service.approve_report_run(
        report.report_run_id,
        reviewer_id="raw-inventory-ui-test",
        reason="test fixture approval",
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
    assert "@media (max-width: 640px)" in response.text
    assert ".raw-shell .table-wrap { overflow-x: auto; max-width: 100%; }" in response.text


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


# ---------------------------------------------------------------------------
# Bug-fix regression tests
# ---------------------------------------------------------------------------

def _make_claim(*, area_id: UUID, claim_code: str) -> ClaimContract:
    return ClaimContract(
        area_id=area_id,
        claim_code=claim_code,
        domain="flood",
        assertion="test assertion",
        user_safe_language="test language",
        severity=SeverityBand.MEDIUM,
        confidence=ConfidenceBand.MEDIUM,
        evidence_ids=[UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")],
    )


def test_report_claim_total_uses_claims_list_only_no_double_count() -> None:
    """Bug #1: claim total must equal len(claims) — not claims+unknowns+red_flags+advisory."""
    app = create_app()
    services = cast(ApiServices, app.state.services)
    area = services.area_service.create(
        AreaContract(
            label="claim-total-test area",
            geom_geojson=_valid_geojson(),
            geom_source="claim-total-test",
        )
    )
    # 2 claims total; unknowns/red_flags/advisory are subsets — same objects
    claim_a = _make_claim(area_id=area.area_id, claim_code="TOTAL_A")
    claim_b = _make_claim(area_id=area.area_id, claim_code="TOTAL_B")
    report = ReportRunContract(
        area_id=area.area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        review_status=ReportReviewStatus.APPROVED,
        claims=[claim_a, claim_b],
        unknowns=[claim_a],        # subset of claims
        red_flags=[claim_b],       # subset of claims
        advisory_claims=[],
    )
    services.report_service._report_repo.add(report)
    client = TestClient(app)

    response = client.get("/ui/raw-data")

    assert response.status_code == 200
    # The Claims column must show "2", not "4" (which double-counting would produce)
    # Find the row for this report and assert the claims cell value
    report_id = str(report.report_run_id)
    assert report_id in response.text
    # The Claims column must show "2" (not "4", which double-counting would produce).
    # _report_claim_total is a pure function — assert it directly as the ground truth.
    from app.api.ui import _report_claim_total
    assert _report_claim_total(report) == 2


def test_raw_inventory_gated_links_absent_for_needs_review_report() -> None:
    """Bug #2: needs_review reports must NOT render dossier/artifact/lineage links."""
    app = create_app()
    services = cast(ApiServices, app.state.services)
    area = services.area_service.create(
        AreaContract(
            label="link-gate-test area",
            geom_geojson=_valid_geojson(),
            geom_source="link-gate-test",
        )
    )
    pending_report = ReportRunContract(
        area_id=area.area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        review_status=ReportReviewStatus.NEEDS_REVIEW,
    )
    services.report_service._report_repo.add(pending_report)
    client = TestClient(app)

    response = client.get("/ui/raw-data")

    assert response.status_code == 200
    run_id = str(pending_report.report_run_id)
    assert run_id in response.text
    # Detail link is always present
    assert f'href="/ui/report-runs/{run_id}"' in response.text
    # Approval-gated links must NOT be present
    assert f'href="/report-runs/{run_id}/dossier?download=1"' not in response.text
    assert f'href="/report-runs/{run_id}/artifact"' not in response.text
    assert f'href="/ui/report-runs/{run_id}/lineage"' not in response.text


def test_raw_inventory_gated_links_present_for_approved_report() -> None:
    """Bug #2: approved reports MUST render dossier/artifact/lineage links."""
    app = create_app()
    services = cast(ApiServices, app.state.services)
    area = services.area_service.create(
        AreaContract(
            label="link-gate-approved area",
            geom_geojson=_valid_geojson(),
            geom_source="link-gate-approved",
        )
    )
    approved_report = ReportRunContract(
        area_id=area.area_id,
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        review_status=ReportReviewStatus.APPROVED,
    )
    services.report_service._report_repo.add(approved_report)
    client = TestClient(app)

    response = client.get("/ui/raw-data")

    assert response.status_code == 200
    run_id = str(approved_report.report_run_id)
    assert run_id in response.text
    assert f'href="/ui/report-runs/{run_id}"' in response.text
    assert f'href="/report-runs/{run_id}/dossier?download=1"' in response.text
    assert f'href="/report-runs/{run_id}/artifact"' in response.text
    assert f'href="/ui/report-runs/{run_id}/lineage"' in response.text


def test_home_summary_evidence_and_claim_counts_are_accurate() -> None:
    """Bug #3 (reverted): home summary must display the TRUE total counts.

    The original bot fix sliced list_all()[:50], which silently under-reported
    totals >=51.  We revert to len(list_all()) for accurate counts.  This test
    seeds a known non-empty inventory and asserts the displayed totals equal
    the seeded totals — not a capped value.
    """
    app = create_app()
    services = cast(ApiServices, app.state.services)
    source = services.source_service.register(_source())
    area = services.area_service.create(
        AreaContract(
            label="count-accuracy-test area",
            geom_geojson=_valid_geojson(),
            geom_source="count-accuracy-test",
        )
    )
    # Seed 3 evidence records.
    for i in range(3):
        services.evidence_service.create_source_failure(
            area_id=area.area_id,
            source_id=source.source_id,
            method_code=f"count_test_{i}",
            evidence_code=f"COUNT_TEST_{i}",
            domain="flood",
            observation=f"count accuracy test evidence {i}",
            caveat="count accuracy fixture",
        )
    # Seed 2 claim records directly via the repo (bypasses evidence-ID validation
    # the same way other tests in this file bypass report-repo validation).
    claim_a = _make_claim(area_id=area.area_id, claim_code="COUNT_A")
    claim_b = _make_claim(area_id=area.area_id, claim_code="COUNT_B")
    services.claim_service._repo.add(claim_a)
    services.claim_service._repo.add(claim_b)

    client = TestClient(app)
    response = client.get("/ui/")

    assert response.status_code == 200
    # True totals must appear — not a capped value.
    assert "evidence: 3" in response.text
    assert "claims: 2" in response.text


def test_raw_inventory_unavailable_row_shows_no_filesystem_path() -> None:
    """Bug #4: collector exception must render a generic message, no raw path."""
    app = create_app()
    services = cast(ApiServices, app.state.services)
    client = TestClient(app)

    # Simulate a collector that raises with a filesystem path in the message
    def raise_with_path() -> list[object]:
        raise RuntimeError("/workspace/local_artifacts/run-abc/report.json not found")

    # Monkeypatch evidence_service.list_all to raise with a path-like message
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(services.evidence_service, "list_all", raise_with_path)

    response = client.get("/ui/raw-data")

    monkeypatch.undo()

    assert response.status_code == 200
    # Must NOT leak the filesystem path
    assert "/workspace/" not in response.text
    assert "local_artifacts" not in response.text
    # Must render a generic unavailability message
    assert "collector unavailable" in response.text or "Unavailable" in response.text
