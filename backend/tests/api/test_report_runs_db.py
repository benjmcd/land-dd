from __future__ import annotations

import json
import os
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.claims_engine.not_evaluated import (
    NOT_EVALUATED_CLAIM_CODES,
    NOT_EVALUATED_DOMAINS,
    NOT_EVALUATED_SOURCE_NAME,
    NOT_EVALUATED_SOURCE_ORG,
)
from app.core.config import Settings
from app.db.engine import build_engine
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_backed_api_creates_and_retrieves_persisted_report_run(
    tmp_path: Path,
) -> None:
    engine = build_engine()
    settings = Settings(OBJECT_STORE_ROOT=str(tmp_path / "object-store"))
    app = create_app(settings=settings, use_db_services=True)
    client = TestClient(app)

    area_response = client.post(
        "/areas",
        json={
            "label": "db api fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "db api fixture",
        },
    )
    assert area_response.status_code == 201
    area_id = area_response.json()["area_id"]
    report_run_id: UUID | None = None
    sentinel_preexisting = _sentinel_source_exists()

    try:
        list_response = client.get("/areas")
        assert list_response.status_code == 200
        assert area_id in {area["area_id"] for area in list_response.json()}

        create_response = client.post(
            "/report-runs",
            json={
                "area_id": area_id,
                "intent_code": "homestead_feasibility",
            },
        )

        assert create_response.status_code == 202
        job = create_response.json()
        report_run_id = UUID(job["report_run_id"])

        get_response = client.get(f"/report-runs/{report_run_id}")
        assert get_response.status_code == 200
        report_run = get_response.json()
        assert report_run["artifact_metadata"]["persistence"] == "postgres+object_store"
        n_domains = len(NOT_EVALUATED_DOMAINS)
        assert report_run["artifact_metadata"]["cost_metrics"]["evidence_count"] == n_domains
        assert report_run["artifact_metadata"]["cost_metrics"]["unknown_count"] == n_domains
        assert report_run["artifact_metadata"]["cost_metrics"]["estimated_total_usd_cents"] == 0
        assert report_run["artifact_metadata"]["cost_metrics"]["paid_data_usd_cents"] == 0
        assert report_run["artifact_metadata"]["cost_metrics"]["human_review_minutes"] == 0
        assert [record["domain"] for record in report_run["evidence"]] == list(
            NOT_EVALUATED_DOMAINS
        )
        assert [claim["claim_code"] for claim in report_run["unknowns"]] == [
            NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS
        ]
        assert report_run["source_manifest"]["source_names"] == [
            NOT_EVALUATED_SOURCE_NAME
        ]

        with Session(engine) as session:
            row = session.execute(
                text(
                    """
                    SELECT intent_id, output_uri, machine_json_uri
                    FROM reports.report_runs
                    WHERE report_run_id = :report_run_id
                    """
                ),
                {"report_run_id": report_run_id},
            ).one_or_none()
        assert row is not None
        assert row[0] is not None
        assert row[1] == report_run["output_uri"]
        assert row[2] == report_run["artifact_metadata"]["machine_json_uri"]
        assert Path(report_run["output_uri"]).exists()
    finally:
        _cleanup_db_api_report(
            area_id=UUID(area_id),
            report_run_id=report_run_id,
            delete_sentinel_source=not sentinel_preexisting,
        )


_REVIEWER_HEADERS = {
    "X-Reviewer-Id": "fixture-reviewer",
    "X-Reviewer-Token": "fixture-token-123",
}


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_backed_full_reviewed_dossier_path(tmp_path: Path) -> None:
    """Full AOI→persist→run→pre-approval 409→approve→dossier 200→DB confirm."""
    engine = build_engine()
    settings = Settings(OBJECT_STORE_ROOT=str(tmp_path / "object-store"))
    app = create_app(settings=settings, use_db_services=True)
    client = TestClient(app)

    area_resp = client.post(
        "/areas",
        json={
            "label": "reviewed path fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "db reviewed path fixture",
        },
    )
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]
    report_run_id: UUID | None = None
    sentinel_preexisting = _sentinel_source_exists()

    try:
        run_resp = client.post(
            "/report-runs",
            json={"area_id": area_id, "intent_code": "rural_land_purchase"},
        )
        assert run_resp.status_code == 202
        report_run_id = UUID(run_resp.json()["report_run_id"])

        # Pre-approval: dossier must be gated (409)
        pre_resp = client.get(f"/report-runs/{report_run_id}/dossier")
        assert pre_resp.status_code == 409
        assert "not approved" in pre_resp.json()["detail"]

        # Approve via API
        approve_resp = client.post(
            f"/report-runs/{report_run_id}/approve",
            headers=_REVIEWER_HEADERS,
        )
        assert approve_resp.status_code == 200
        approved = approve_resp.json()
        assert approved["review_status"] == "approved"

        # Post-approval: dossier must be available (200, Markdown)
        dossier_resp = client.get(f"/report-runs/{report_run_id}/dossier")
        assert dossier_resp.status_code == 200
        assert "text/markdown" in dossier_resp.headers["content-type"]
        assert "## 1. Executive Summary" in dossier_resp.text

        # DB reload confirms row and artifact still present
        with Session(engine) as session:
            row = session.execute(
                text(
                    """
                    SELECT status, output_uri
                    FROM reports.report_runs
                    WHERE report_run_id = :report_run_id
                    """
                ),
                {"report_run_id": report_run_id},
            ).one_or_none()
        assert row is not None
        assert row[0] == "succeeded"
        assert row[1] is not None
        assert Path(row[1]).exists()

        # API reload confirms review_status persisted to artifact
        reload_resp = client.get(f"/report-runs/{report_run_id}")
        assert reload_resp.status_code == 200
        reloaded = reload_resp.json()
        assert reloaded["review_status"] == "approved"
        assert reloaded["reviewed_by"] == "fixture-reviewer"
    finally:
        _cleanup_db_api_report(
            area_id=UUID(area_id),
            report_run_id=report_run_id,
            delete_sentinel_source=not sentinel_preexisting,
        )


def _sentinel_source_exists() -> bool:
    engine = build_engine()
    with Session(engine) as session:
        return (
            session.execute(
                text(
                    """
                    SELECT 1
                    FROM source.sources
                    WHERE name = :name
                        AND organization = :organization
                    LIMIT 1
                    """
                ),
                {
                    "name": NOT_EVALUATED_SOURCE_NAME,
                    "organization": NOT_EVALUATED_SOURCE_ORG,
                },
            ).first()
            is not None
        )


def _cleanup_db_api_report(
    *,
    area_id: UUID,
    report_run_id: UUID | None,
    delete_sentinel_source: bool,
) -> None:
    engine = build_engine()
    with Session(engine) as session:
        if report_run_id is not None:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_id = :report_run_id"),
                {"report_run_id": report_run_id},
            )
            session.execute(
                text("DELETE FROM reports.report_runs WHERE report_run_id = :report_run_id"),
                {"report_run_id": report_run_id},
            )
        session.execute(
            text("DELETE FROM claims.verification_tasks WHERE area_id = :area_id"),
            {"area_id": area_id},
        )
        session.execute(
            text("DELETE FROM claims.claims WHERE area_id = :area_id"),
            {"area_id": area_id},
        )
        session.execute(
            text("DELETE FROM evidence.observations WHERE area_id = :area_id"),
            {"area_id": area_id},
        )
        session.execute(
            text("DELETE FROM core.areas WHERE area_id = :area_id"),
            {"area_id": area_id},
        )
        if delete_sentinel_source:
            session.execute(
                text(
                    """
                    DELETE FROM source.sources
                    WHERE name = :name
                        AND organization = :organization
                    """
                ),
                {
                    "name": NOT_EVALUATED_SOURCE_NAME,
                    "organization": NOT_EVALUATED_SOURCE_ORG,
                },
            )
        session.commit()
