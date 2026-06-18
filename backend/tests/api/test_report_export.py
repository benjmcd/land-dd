from __future__ import annotations

import json
import os
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices
from app.domain.enums import IntentCode
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"

# Forbidden phrases imported from the overclaim test module to keep a single list.
_FORBIDDEN_PHRASES = (
    "You can build here",
    "This parcel has legal access",
    "This property has water rights",
    "This is a good investment",
    "This land is safe",
    "This property is worth",
)


def _valid_geojson() -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / "valid_polygon.geojson").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _make_app_client_with_approved_report() -> tuple[FastAPI, TestClient, str]:
    app = create_app()
    client = TestClient(app)
    area_resp = client.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]
    run_resp = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert run_resp.status_code == 202
    report_run_id = run_resp.json()["report_run_id"]
    services = cast(ApiServices, app.state.services)
    services.report_service.approve_report_run(UUID(report_run_id), reviewer_id="test-reviewer")
    return app, client, report_run_id


def _make_app_client_with_unapproved_report() -> tuple[FastAPI, TestClient, str]:
    app = create_app()
    client = TestClient(app)
    area_resp = client.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]
    run_resp = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
    )
    assert run_resp.status_code == 202
    return app, client, run_resp.json()["report_run_id"]


def _trusted_header_identity(workspace_id: UUID, user_id: UUID) -> dict[str, str]:
    return {
        "X-Workspace-Id": str(workspace_id),
        "X-User-Id": str(user_id),
    }


# ---------------------------------------------------------------------------
# Dossier download param tests
# ---------------------------------------------------------------------------


def test_dossier_without_download_has_no_disposition() -> None:
    _app, client, report_run_id = _make_app_client_with_approved_report()
    resp = client.get(f"/report-runs/{report_run_id}/dossier")
    assert resp.status_code == 200
    assert "content-disposition" not in resp.headers


def test_dossier_with_download_true_has_attachment_disposition() -> None:
    _app, client, report_run_id = _make_app_client_with_approved_report()
    resp = client.get(f"/report-runs/{report_run_id}/dossier?download=1")
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    cd = resp.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert f"dossier_{report_run_id}.md" in cd


def test_dossier_download_body_identical_to_non_download() -> None:
    _app, client, report_run_id = _make_app_client_with_approved_report()
    normal_resp = client.get(f"/report-runs/{report_run_id}/dossier")
    download_resp = client.get(f"/report-runs/{report_run_id}/dossier?download=1")
    assert normal_resp.content == download_resp.content


def test_dossier_download_false_has_no_disposition() -> None:
    _app, client, report_run_id = _make_app_client_with_approved_report()
    resp = client.get(f"/report-runs/{report_run_id}/dossier?download=false")
    assert resp.status_code == 200
    assert "content-disposition" not in resp.headers


# ---------------------------------------------------------------------------
# Artifact endpoint gating (mirrors dossier gating)
# ---------------------------------------------------------------------------


def test_artifact_returns_404_for_unknown_id() -> None:
    _app, client, _report_run_id = _make_app_client_with_unapproved_report()
    resp = client.get(f"/report-runs/{uuid4()}/artifact")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "report run not found"


def test_artifact_returns_409_for_unapproved_report() -> None:
    _app, client, report_run_id = _make_app_client_with_unapproved_report()
    resp = client.get(f"/report-runs/{report_run_id}/artifact")
    assert resp.status_code == 409
    assert "not approved" in resp.json()["detail"]


def test_artifact_returns_202_when_job_pending() -> None:
    app = create_app()
    client = TestClient(app)
    area_resp = client.post(
        "/areas",
        json={"geom_geojson": _valid_geojson(), "geom_source": "test fixture"},
    )
    assert area_resp.status_code == 201
    services = cast(ApiServices, app.state.services)
    job = services.async_report_jobs.create(
        area_id=UUID(area_resp.json()["area_id"]),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
    )
    resp = client.get(f"/report-runs/{job.report_run_id}/artifact")
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "pending"
    assert body["report_run_id"] == str(job.report_run_id)


# ---------------------------------------------------------------------------
# Artifact endpoint content + disposition
# ---------------------------------------------------------------------------


def test_artifact_returns_json_with_attachment_disposition() -> None:
    _app, client, report_run_id = _make_app_client_with_approved_report()
    resp = client.get(f"/report-runs/{report_run_id}/artifact")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    cd = resp.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert f"report_{report_run_id}.json" in cd


def test_artifact_json_contains_report_run_id() -> None:
    _app, client, report_run_id = _make_app_client_with_approved_report()
    resp = client.get(f"/report-runs/{report_run_id}/artifact")
    assert resp.status_code == 200
    body = resp.json()
    assert body["report_run_id"] == report_run_id


def test_artifact_body_matches_shared_serializer_for_approved_report() -> None:
    from app.reports.artifacts import serialize_report_artifact

    app, client, report_run_id = _make_app_client_with_approved_report()
    services = cast(ApiServices, app.state.services)
    report = services.report_service.get_report_run(UUID(report_run_id))
    assert report is not None

    resp = client.get(f"/report-runs/{report_run_id}/artifact")
    assert resp.status_code == 200
    assert resp.text == serialize_report_artifact(report)


def test_artifact_json_contains_claims_with_evidence_ids() -> None:
    _app, client, report_run_id = _make_app_client_with_approved_report()
    resp = client.get(f"/report-runs/{report_run_id}/artifact")
    assert resp.status_code == 200
    body = resp.json()
    # unknowns are claims; all claims have evidence_ids field
    all_claims = body.get("claims", []) + body.get("unknowns", []) + body.get("red_flags", [])
    for claim in all_claims:
        assert "evidence_ids" in claim, f"claim missing evidence_ids: {claim}"


def test_artifact_json_contains_caveats() -> None:
    _app, client, report_run_id = _make_app_client_with_approved_report()
    resp = client.get(f"/report-runs/{report_run_id}/artifact")
    assert resp.status_code == 200
    body = resp.json()
    assert "caveats" in body


def test_artifact_json_contains_source_manifest() -> None:
    _app, client, report_run_id = _make_app_client_with_approved_report()
    resp = client.get(f"/report-runs/{report_run_id}/artifact")
    assert resp.status_code == 200
    body = resp.json()
    assert "source_manifest" in body
    manifest = body["source_manifest"]
    assert "source_ids" in manifest


def test_artifact_json_no_forbidden_phrases() -> None:
    _app, client, report_run_id = _make_app_client_with_approved_report()
    resp = client.get(f"/report-runs/{report_run_id}/artifact")
    assert resp.status_code == 200
    body_text = resp.text.lower()
    for phrase in _FORBIDDEN_PHRASES:
        assert phrase.lower() not in body_text, (
            f"Forbidden certainty phrase found in artifact JSON: {phrase!r}"
        )


# ---------------------------------------------------------------------------
# DB-gated test: persisted-artifact path
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_artifact_endpoint_serves_persisted_file(tmp_path: Path) -> None:
    """In DB mode the artifact endpoint reads the persisted JSON file."""
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    from app.claims_engine.not_evaluated import (
        NOT_EVALUATED_SOURCE_NAME,
        NOT_EVALUATED_SOURCE_ORG,
    )
    from app.core.config import Settings
    from app.db.engine import build_engine

    engine = build_engine()
    settings = Settings(OBJECT_STORE_ROOT=str(tmp_path / "object-store"))
    app = create_app(settings=settings, use_db_services=True)
    client = TestClient(app)
    workspace_a = uuid4()
    workspace_b = uuid4()
    user_id = uuid4()
    headers_a = _trusted_header_identity(workspace_a, user_id)
    headers_b = _trusted_header_identity(workspace_b, user_id)

    sentinel_preexisting: bool
    with Session(engine) as session:
        session.execute(
            text(
                """
                INSERT INTO core.workspaces (workspace_id, name)
                VALUES (:workspace_id, :name)
                ON CONFLICT (workspace_id) DO UPDATE SET name = EXCLUDED.name
                """
            ),
            {"workspace_id": workspace_a, "name": "artifact export workspace a"},
        )
        session.execute(
            text(
                """
                INSERT INTO core.workspaces (workspace_id, name)
                VALUES (:workspace_id, :name)
                ON CONFLICT (workspace_id) DO UPDATE SET name = EXCLUDED.name
                """
            ),
            {"workspace_id": workspace_b, "name": "artifact export workspace b"},
        )
        session.execute(
            text(
                """
                INSERT INTO core.users (user_id, workspace_id, email)
                VALUES (:user_id, :workspace_id, :email)
                ON CONFLICT (user_id) DO UPDATE SET
                    workspace_id = EXCLUDED.workspace_id,
                    email = EXCLUDED.email
                """
            ),
            {
                "user_id": user_id,
                "workspace_id": workspace_a,
                "email": "artifact-export-user@example.test",
            },
        )
        sentinel_preexisting = (
            session.execute(
                text(
                    "SELECT 1 FROM source.sources WHERE name = :n AND organization = :o LIMIT 1"
                ),
                {"n": NOT_EVALUATED_SOURCE_NAME, "o": NOT_EVALUATED_SOURCE_ORG},
            ).first()
            is not None
        )
        session.commit()

    area_resp = client.post(
        "/areas",
        json={
            "label": "artifact export fixture polygon",
            "geom_geojson": _valid_geojson(),
            "geom_source": "artifact export fixture",
        },
        headers=headers_a,
    )
    assert area_resp.status_code == 201
    area_id = area_resp.json()["area_id"]
    report_run_id: UUID | None = None

    try:
        run_resp = client.post(
            "/report-runs",
            json={"area_id": area_id, "intent_code": "rural_land_purchase"},
            headers=headers_a,
        )
        assert run_resp.status_code == 202
        report_run_id = UUID(run_resp.json()["report_run_id"])

        # Pre-approval: artifact must be gated (409)
        pre_resp = client.get(
            f"/report-runs/{report_run_id}/artifact",
            headers=headers_a,
        )
        assert pre_resp.status_code == 409

        # Approve
        approve_resp = client.post(
            f"/report-runs/{report_run_id}/approve",
            headers={
                "X-Reviewer-Id": "fixture-reviewer",
                "X-Reviewer-Token": "fixture-token-123",
            },
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["review_status"] == "approved"

        # Post-approval: artifact should come from the persisted file
        artifact_resp = client.get(
            f"/report-runs/{report_run_id}/artifact",
            headers=headers_a,
        )
        assert artifact_resp.status_code == 200
        assert "application/json" in artifact_resp.headers["content-type"]
        cd = artifact_resp.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert f"report_{report_run_id}.json" in cd

        body = artifact_resp.json()
        assert body["report_run_id"] == str(report_run_id)
        # Confirm the persisted file exists on disk
        artifact_path = Path(body["output_uri"])
        assert artifact_path.exists(), f"Artifact file not found: {artifact_path}"
        stored = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert body == stored
        assert stored["report_run_id"] == str(report_run_id)

        wrong_name_artifact = artifact_path.parent / "wrong-report.json"
        wrong_name_artifact.write_text(json.dumps(stored), encoding="utf-8")
        with Session(engine) as session:
            session.execute(
                text(
                    """
                    UPDATE reports.report_runs
                    SET output_uri = :artifact_uri,
                        machine_json_uri = :artifact_uri
                    WHERE report_run_id = :report_run_id
                    """
                ),
                {
                    "artifact_uri": str(wrong_name_artifact),
                    "report_run_id": report_run_id,
                },
            )
            session.commit()

        wrong_name_resp = client.get(
            f"/report-runs/{report_run_id}/artifact",
            headers=headers_a,
        )
        assert wrong_name_resp.status_code == 409
        assert "does not match expected file" in wrong_name_resp.json()["detail"]

        hidden_resp = client.get(
            f"/report-runs/{report_run_id}/artifact",
            headers=headers_b,
        )
        assert hidden_resp.status_code == 404

        outside_artifact = (tmp_path / "outside-report.json").resolve()
        outside_artifact.write_text(json.dumps(stored), encoding="utf-8")
        with Session(engine) as session:
            session.execute(
                text(
                    """
                    UPDATE reports.report_runs
                    SET output_uri = :artifact_uri,
                        machine_json_uri = :artifact_uri
                    WHERE report_run_id = :report_run_id
                    """
                ),
                {
                    "artifact_uri": str(outside_artifact),
                    "report_run_id": report_run_id,
                },
            )
            session.commit()

        tampered_resp = client.get(
            f"/report-runs/{report_run_id}/artifact",
            headers=headers_a,
        )
        assert tampered_resp.status_code == 409
        assert "outside object store root" in tampered_resp.json()["detail"]
    finally:
        with Session(engine) as session:
            if report_run_id is not None:
                session.execute(
                    text("DELETE FROM jobs.job_queue WHERE job_id = :id"),
                    {"id": report_run_id},
                )
                session.execute(
                    text(
                        "DELETE FROM reports.report_runs WHERE report_run_id = :id"
                    ),
                    {"id": report_run_id},
                )
            session.execute(
                text("DELETE FROM claims.verification_tasks WHERE area_id = :area_id"),
                {"area_id": UUID(area_id)},
            )
            session.execute(
                text("DELETE FROM claims.claims WHERE area_id = :area_id"),
                {"area_id": UUID(area_id)},
            )
            session.execute(
                text("DELETE FROM evidence.observations WHERE area_id = :area_id"),
                {"area_id": UUID(area_id)},
            )
            session.execute(
                text("DELETE FROM core.areas WHERE area_id = :area_id"),
                {"area_id": UUID(area_id)},
            )
            session.execute(
                text("DELETE FROM core.users WHERE user_id = :user_id"),
                {"user_id": user_id},
            )
            session.execute(
                text("DELETE FROM core.workspaces WHERE workspace_id IN (:a, :b)"),
                {"a": workspace_a, "b": workspace_b},
            )
            if not sentinel_preexisting:
                session.execute(
                    text(
                        "DELETE FROM source.sources WHERE name = :n AND organization = :o"
                    ),
                    {"n": NOT_EVALUATED_SOURCE_NAME, "o": NOT_EVALUATED_SOURCE_ORG},
                )
            session.commit()
