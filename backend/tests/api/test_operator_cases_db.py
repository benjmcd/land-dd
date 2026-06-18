from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import app.operator_cases as selected_county_cases
from app.claims_engine.not_evaluated import (
    NOT_EVALUATED_SOURCE_NAME,
    NOT_EVALUATED_SOURCE_ORG,
)
from app.connectors.review_queue import CONNECTOR_REVIEW_STATUS_JOB_TYPE
from app.core.config import Settings
from app.db.engine import build_engine
from app.main import create_app

_ALL_SELECTED_COUNTY_CASE_IDS = tuple(
    case.case_id for case in selected_county_cases.list_selected_county_cases()
)
_SOURCE_NAME = "Selected County Private MVP Fixtures"
_DEMO_WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
_DEMO_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
_REVIEWER_ID = "fixture-reviewer"
_REVIEWER_TOKEN = "fixture-token-123"


@dataclass(frozen=True)
class _SelectedCountySnapshot:
    area_exists: bool
    source_exists: bool
    not_evaluated_source_exists: bool
    dataset_exists: bool
    dataset_version_exists: bool
    report_run_ids: frozenset[UUID]
    evidence_ids: frozenset[UUID]
    claim_ids: frozenset[UUID]
    verification_task_ids: frozenset[UUID]
    ingest_run_ids: frozenset[UUID]
    connector_review_keys: frozenset[str]


def _area_id_for(
    case_id: str,
    *,
    workspace_id: UUID | None = _DEMO_WORKSPACE_ID,
) -> UUID:
    case = selected_county_cases.get_selected_county_case(case_id)
    assert case is not None
    return selected_county_cases._area_id_for(case, workspace_id=workspace_id)


def _auth_headers() -> dict[str, str]:
    return {
        "X-Workspace-Id": str(_DEMO_WORKSPACE_ID),
        "X-User-Id": str(_DEMO_USER_ID),
        "X-Reviewer-Id": _REVIEWER_ID,
        "X-Reviewer-Token": _REVIEWER_TOKEN,
    }


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
@pytest.mark.parametrize("case_id", _ALL_SELECTED_COUNTY_CASE_IDS)
def test_db_operator_case_report_persists_selected_county_fixture(
    tmp_path: Path,
    case_id: str,
) -> None:
    area_id = _area_id_for(case_id)
    engine = build_engine()
    object_store_root = (tmp_path / "object-store").resolve()
    with Session(engine) as session:
        before = _capture_selected_county_snapshot(session, area_id)

    app = create_app(
        settings=Settings(OBJECT_STORE_ROOT=str(object_store_root)),
        use_db_services=True,
    )
    client = TestClient(app)

    try:
        create_response = client.post(
            f"/operator-cases/{case_id}/report",
            headers=_auth_headers(),
        )

        assert create_response.status_code == 201
        created = create_response.json()
        report_run_id = UUID(created["report_run_id"])
        assert created["case_id"] == case_id
        assert created["review_status"] == "approved"
        assert created["status"] == "succeeded"
        assert created["evidence_count"] > 0

        artifact_response = client.get(created["links"]["artifact"])

        assert artifact_response.status_code == 200
        artifact_report = artifact_response.json()
        assert artifact_report["report_run_id"] == str(report_run_id)
        assert artifact_report["review_status"] == "approved"
        assert artifact_report["workspace_id"] == str(_DEMO_WORKSPACE_ID)
        assert artifact_report["requested_by"] == str(_DEMO_USER_ID)
        assert artifact_report["reviewed_by"] == _REVIEWER_ID
        assert artifact_report["artifact_metadata"]["persistence"] == "postgres+object_store"

        get_response = client.get(f"/report-runs/{report_run_id}")

        assert get_response.status_code == 200
        report = get_response.json()
        assert report["report_run_id"] == str(report_run_id)
        assert report["area_id"] == str(area_id)
        assert report["review_status"] == "approved"
        assert report["status"] == "succeeded"
        assert report["artifact_metadata"]["persistence"] == "postgres+object_store"
        assert report["artifact_metadata"]["cost_metrics"]["evidence_count"] > 0
        assert _SOURCE_NAME in report["source_manifest"]["source_names"]
        assert str(selected_county_cases._SOURCE_ID) in report["source_manifest"]["source_ids"]

        artifact_path = Path(report["artifact_metadata"]["machine_json_uri"]).resolve()
        assert artifact_path.exists()
        assert artifact_path.is_relative_to(object_store_root)
        stored_artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert stored_artifact["report_run_id"] == str(report_run_id)
        assert stored_artifact["review_status"] == "approved"
        assert stored_artifact == artifact_report

        with Session(engine) as session:
            after = _capture_selected_county_snapshot(session, area_id)
            report_row = session.execute(
                text(
                    """
                    SELECT area_id, workspace_id, requested_by, status, output_uri, machine_json_uri
                    FROM reports.report_runs
                    WHERE report_run_id = :report_run_id
                    """
                ),
                {"report_run_id": report_run_id},
            ).mappings().one_or_none()
            assert report_row is not None
            assert UUID(str(report_row["area_id"])) == area_id
            assert UUID(str(report_row["workspace_id"])) == _DEMO_WORKSPACE_ID
            assert UUID(str(report_row["requested_by"])) == _DEMO_USER_ID
            assert report_row["status"] == "succeeded"
            assert report_row["output_uri"] == report["output_uri"]
            assert report_row["machine_json_uri"] == report["artifact_metadata"]["machine_json_uri"]

            area_row = session.execute(
                text(
                    """
                    SELECT label, workspace_id, created_by
                    FROM core.areas
                    WHERE area_id = :area_id
                    """
                ),
                {"area_id": area_id},
            ).mappings().one_or_none()
            assert area_row is not None
            assert "selected-county-private-mvp" in str(area_row["label"])
            assert UUID(str(area_row["workspace_id"])) == _DEMO_WORKSPACE_ID
            assert UUID(str(area_row["created_by"])) == _DEMO_USER_ID

            new_evidence_ids = after.evidence_ids - before.evidence_ids
            new_ingest_run_ids = after.ingest_run_ids - before.ingest_run_ids
            new_connector_review_keys = (
                after.connector_review_keys - before.connector_review_keys
            )
            assert new_evidence_ids
            assert new_ingest_run_ids
            assert len(new_connector_review_keys) == len(new_ingest_run_ids)

            queue_rows = session.execute(
                text(
                    """
                    SELECT workspace_id, payload
                    FROM jobs.job_queue
                    WHERE job_type = :job_type
                        AND idempotency_key = ANY(:keys)
                    """
                ),
                {
                    "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                    "keys": list(new_connector_review_keys),
                },
            ).mappings().all()
            assert queue_rows
            assert {UUID(str(row["workspace_id"])) for row in queue_rows} == {
                _DEMO_WORKSPACE_ID
            }
            assert {row["payload"]["requested_by"] for row in queue_rows} == {
                str(_DEMO_USER_ID)
            }
            assert {
                row["payload"]["review_decision"]["reviewer_id"] for row in queue_rows
            } == {_REVIEWER_ID}

            evidence_count = session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM evidence.observations
                    WHERE area_id = :area_id
                    """
                ),
                {"area_id": area_id},
            ).scalar_one()
            assert evidence_count >= created["evidence_count"] > 0
    finally:
        _cleanup_selected_county_snapshot(engine, before, area_id)


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_ui_operator_case_report_persists_selected_county_fixture(
    tmp_path: Path,
) -> None:
    case_id = "BUN-slope"
    area_id = _area_id_for(case_id)
    engine = build_engine()
    object_store_root = (tmp_path / "object-store").resolve()
    with Session(engine) as session:
        before = _capture_selected_county_snapshot(session, area_id)

    app = create_app(
        settings=Settings(OBJECT_STORE_ROOT=str(object_store_root)),
        use_db_services=True,
    )
    client = TestClient(app)

    try:
        create_response = client.post(
            "/ui/operator-cases/report",
            data={
                "selected_county_case_id": case_id,
                "reviewer_id": _REVIEWER_ID,
                "reviewer_token": _REVIEWER_TOKEN,
            },
            follow_redirects=False,
        )

        assert create_response.status_code == 303
        location = create_response.headers["location"]
        assert location.startswith("/ui/report-runs/")
        report_run_id = UUID(location.rsplit("/", 1)[-1])

        report_page = client.get(location)

        assert report_page.status_code == 200
        assert "Executive Summary" in report_page.text
        assert "Download dossier (.md)" in report_page.text
        assert "Download report (.json)" in report_page.text
        assert "View evidence lineage" in report_page.text
        assert f'href="/report-runs/{report_run_id}/artifact"' in report_page.text

        artifact_response = client.get(f"/report-runs/{report_run_id}/artifact")

        assert artifact_response.status_code == 200
        artifact_report = artifact_response.json()
        assert artifact_report["report_run_id"] == str(report_run_id)
        assert artifact_report["review_status"] == "approved"
        assert artifact_report["workspace_id"] == str(_DEMO_WORKSPACE_ID)
        assert artifact_report["requested_by"] == str(_DEMO_USER_ID)
        assert artifact_report["reviewed_by"] == _REVIEWER_ID
        assert artifact_report["artifact_metadata"]["persistence"] == "postgres+object_store"
        assert _SOURCE_NAME in artifact_report["source_manifest"]["source_names"]
        assert (
            str(selected_county_cases._SOURCE_ID)
            in artifact_report["source_manifest"]["source_ids"]
        )

        artifact_path = Path(
            artifact_report["artifact_metadata"]["machine_json_uri"],
        ).resolve()
        assert artifact_path.exists()
        assert artifact_path.is_relative_to(object_store_root)
        stored_artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert stored_artifact == artifact_report

        with Session(engine) as session:
            after = _capture_selected_county_snapshot(session, area_id)
            report_row = session.execute(
                text(
                    """
                    SELECT area_id, workspace_id, requested_by, status, output_uri, machine_json_uri
                    FROM reports.report_runs
                    WHERE report_run_id = :report_run_id
                    """
                ),
                {"report_run_id": report_run_id},
            ).mappings().one_or_none()
            assert report_row is not None
            assert UUID(str(report_row["area_id"])) == area_id
            assert UUID(str(report_row["workspace_id"])) == _DEMO_WORKSPACE_ID
            assert UUID(str(report_row["requested_by"])) == _DEMO_USER_ID
            assert report_row["status"] == "succeeded"
            assert report_row["output_uri"] == artifact_report["output_uri"]
            assert (
                report_row["machine_json_uri"]
                == artifact_report["artifact_metadata"]["machine_json_uri"]
            )

            assert after.evidence_ids - before.evidence_ids
            assert after.ingest_run_ids - before.ingest_run_ids
            assert after.connector_review_keys - before.connector_review_keys
    finally:
        _cleanup_selected_county_snapshot(engine, before, area_id)


def _capture_selected_county_snapshot(
    session: Session,
    area_id: UUID,
) -> _SelectedCountySnapshot:
    return _SelectedCountySnapshot(
        area_exists=_row_exists(
            session,
            "SELECT 1 FROM core.areas WHERE area_id = :area_id",
            area_id=area_id,
        ),
        source_exists=_row_exists(
            session,
            "SELECT 1 FROM source.sources WHERE source_id = :source_id",
            source_id=selected_county_cases._SOURCE_ID,
        ),
        not_evaluated_source_exists=_row_exists(
            session,
            """
            SELECT 1
            FROM source.sources
            WHERE name = :name
                AND organization = :organization
            """,
            name=NOT_EVALUATED_SOURCE_NAME,
            organization=NOT_EVALUATED_SOURCE_ORG,
        ),
        dataset_exists=_row_exists(
            session,
            "SELECT 1 FROM source.datasets WHERE dataset_id = :dataset_id",
            dataset_id=selected_county_cases._DATASET_ID,
        ),
        dataset_version_exists=_row_exists(
            session,
            "SELECT 1 FROM source.dataset_versions WHERE dataset_version_id = :dataset_version_id",
            dataset_version_id=selected_county_cases._DATASET_VERSION_ID,
        ),
        report_run_ids=_uuid_set(
            session,
            """
            SELECT report_run_id
            FROM reports.report_runs
            WHERE area_id = :area_id
            """,
            area_id=area_id,
        ),
        evidence_ids=_uuid_set(
            session,
            """
            SELECT evidence_id
            FROM evidence.observations
            WHERE area_id = :area_id
            """,
            area_id=area_id,
        ),
        claim_ids=_uuid_set(
            session,
            """
            SELECT claim_id
            FROM claims.claims
            WHERE area_id = :area_id
            """,
            area_id=area_id,
        ),
        verification_task_ids=_uuid_set(
            session,
            """
            SELECT verification_task_id
            FROM claims.verification_tasks
            WHERE area_id = :area_id
            """,
            area_id=area_id,
        ),
        ingest_run_ids=_uuid_set(
            session,
            """
            SELECT DISTINCT ingest_run_id
            FROM evidence.observations
            WHERE area_id = :area_id
                AND ingest_run_id IS NOT NULL
            """,
            area_id=area_id,
        ),
        connector_review_keys=_string_set(
            session,
            """
            SELECT idempotency_key
            FROM jobs.job_queue
            WHERE job_type = :job_type
                AND payload->>'area_id' = :area_id
            """,
            area_id=str(area_id),
            job_type=CONNECTOR_REVIEW_STATUS_JOB_TYPE,
        ),
    )


def _cleanup_selected_county_snapshot(
    engine: Engine,
    before: _SelectedCountySnapshot,
    area_id: UUID,
) -> None:
    with Session(engine) as session:
        after = _capture_selected_county_snapshot(session, area_id)

        for review_key in after.connector_review_keys - before.connector_review_keys:
            session.execute(
                text(
                    """
                    DELETE FROM jobs.job_queue
                    WHERE job_type = :job_type
                        AND idempotency_key = :idempotency_key
                    """
                ),
                {
                    "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                    "idempotency_key": review_key,
                },
            )

        for report_run_id in after.report_run_ids - before.report_run_ids:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_id = :job_id"),
                {"job_id": report_run_id},
            )
            session.execute(
                text(
                    """
                    DELETE FROM reports.report_runs
                    WHERE report_run_id = :report_run_id
                    """
                ),
                {"report_run_id": report_run_id},
            )

        for verification_task_id in (
            after.verification_task_ids - before.verification_task_ids
        ):
            session.execute(
                text(
                    """
                    DELETE FROM claims.verification_tasks
                    WHERE verification_task_id = :verification_task_id
                    """
                ),
                {"verification_task_id": verification_task_id},
            )

        for claim_id in after.claim_ids - before.claim_ids:
            session.execute(
                text("DELETE FROM claims.claims WHERE claim_id = :claim_id"),
                {"claim_id": claim_id},
            )

        for evidence_id in after.evidence_ids - before.evidence_ids:
            session.execute(
                text(
                    """
                    DELETE FROM evidence.observations
                    WHERE evidence_id = :evidence_id
                    """
                ),
                {"evidence_id": evidence_id},
            )

        for ingest_run_id in after.ingest_run_ids - before.ingest_run_ids:
            session.execute(
                text(
                    """
                    DELETE FROM source.ingest_runs
                    WHERE ingest_run_id = :ingest_run_id
                    """
                ),
                {"ingest_run_id": ingest_run_id},
            )

        if not before.area_exists:
            session.execute(
                text("DELETE FROM core.area_versions WHERE area_id = :area_id"),
                {"area_id": area_id},
            )
            session.execute(
                text("DELETE FROM core.areas WHERE area_id = :area_id"),
                {"area_id": area_id},
            )

        if not before.dataset_version_exists:
            session.execute(
                text(
                    """
                    DELETE FROM source.dataset_versions
                    WHERE dataset_version_id = :dataset_version_id
                    """
                ),
                {"dataset_version_id": selected_county_cases._DATASET_VERSION_ID},
            )

        if not before.dataset_exists:
            session.execute(
                text("DELETE FROM source.datasets WHERE dataset_id = :dataset_id"),
                {"dataset_id": selected_county_cases._DATASET_ID},
            )

        if not before.source_exists:
            session.execute(
                text("DELETE FROM source.sources WHERE source_id = :source_id"),
                {"source_id": selected_county_cases._SOURCE_ID},
            )

        if not before.not_evaluated_source_exists:
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


def _row_exists(session: Session, query: str, **params: object) -> bool:
    return session.execute(text(query), params).first() is not None


def _uuid_set(session: Session, query: str, **params: object) -> frozenset[UUID]:
    return frozenset(
        UUID(str(value))
        for value in session.execute(text(query), params).scalars().all()
        if value is not None
    )


def _string_set(session: Session, query: str, **params: object) -> frozenset[str]:
    return frozenset(
        str(value)
        for value in session.execute(text(query), params).scalars().all()
        if value is not None
    )
