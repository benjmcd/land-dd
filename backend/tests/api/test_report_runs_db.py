from __future__ import annotations

import json
import os
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

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
    workspace_id, user_id = _seed_workspace_and_user()
    headers = {
        "X-Workspace-Id": str(workspace_id),
        "X-User-Id": str(user_id),
    }

    area_response = client.post(
        "/areas",
        json={
            "label": "db api fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "db api fixture",
        },
        headers=headers,
    )
    assert area_response.status_code == 201
    area_id = area_response.json()["area_id"]
    report_run_id: UUID | None = None
    sentinel_preexisting = _sentinel_source_exists()

    try:
        list_response = client.get("/areas", headers=headers)
        assert list_response.status_code == 200
        assert area_id in {area["area_id"] for area in list_response.json()}

        create_response = client.post(
            "/report-runs",
            json={
                "area_id": area_id,
                "intent_code": "homestead_feasibility",
            },
            headers=headers,
        )

        assert create_response.status_code == 201
        report_run = create_response.json()
        report_run_id = UUID(report_run["report_run_id"])
        assert report_run["artifact_metadata"]["persistence"] == "postgres+object_store"
        assert report_run["artifact_metadata"]["cost_metrics"]["evidence_count"] == 4
        assert report_run["artifact_metadata"]["cost_metrics"]["unknown_count"] == 4
        assert [record["domain"] for record in report_run["evidence"]] == list(
            NOT_EVALUATED_DOMAINS
        )
        assert [claim["claim_code"] for claim in report_run["unknowns"]] == [
            NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS
        ]
        assert report_run["source_manifest"]["source_names"] == [
            NOT_EVALUATED_SOURCE_NAME
        ]

        get_response = client.get(f"/report-runs/{report_run_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json() == report_run

        blocked_dossier_response = client.get(
            f"/report-runs/{report_run_id}/dossier",
            headers=headers,
        )
        assert blocked_dossier_response.status_code == 409

        approve_response = client.post(
            f"/report-runs/{report_run_id}/approve",
            json={"reviewer_id": str(user_id), "reason": "ready for delivery"},
            headers=headers,
        )
        assert approve_response.status_code == 200

        dossier_response = client.get(f"/report-runs/{report_run_id}/dossier", headers=headers)
        assert dossier_response.status_code == 200
        assert "# Rural Land Dossier" in dossier_response.text
        assert "- Review status: approved" in dossier_response.text

        list_response = client.get(
            f"/report-runs?area_id={area_id}&intent_code=homestead_feasibility",
            headers=headers,
        )
        assert list_response.status_code == 200
        assert [run["report_run_id"] for run in list_response.json()] == [
            str(report_run_id)
        ]
        assert client.get(f"/report-runs?area_id={UUID(int=0)}", headers=headers).json() == []

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
            user_id=user_id,
            workspace_id=workspace_id,
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


def _seed_workspace_and_user() -> tuple[UUID, UUID]:
    workspace_id = uuid4()
    user_id = uuid4()
    engine = build_engine()
    with Session(engine) as session:
        session.execute(
            text(
                """
                INSERT INTO core.workspaces (workspace_id, name)
                VALUES (:workspace_id, 'db api auth workspace')
                """
            ),
            {"workspace_id": workspace_id},
        )
        session.execute(
            text(
                """
                INSERT INTO core.users (user_id, workspace_id, email)
                VALUES (:user_id, :workspace_id, :email)
                """
            ),
            {
                "user_id": user_id,
                "workspace_id": workspace_id,
                "email": f"db-api-auth-{user_id}@example.test",
            },
        )
        session.commit()
    return workspace_id, user_id


def _cleanup_db_api_report(
    *,
    area_id: UUID,
    report_run_id: UUID | None,
    user_id: UUID,
    workspace_id: UUID,
    delete_sentinel_source: bool,
) -> None:
    engine = build_engine()
    with Session(engine) as session:
        if report_run_id is not None:
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
        session.execute(
            text("DELETE FROM core.users WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        session.execute(
            text("DELETE FROM core.workspaces WHERE workspace_id = :workspace_id"),
            {"workspace_id": workspace_id},
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
