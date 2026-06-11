"""Tests for Idempotency-Key support on POST /report-runs and POST /intake."""

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

from app.api.dependencies import ApiServices
from app.db.engine import build_engine
from app.domain.enums import IntentCode
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


# ---------------------------------------------------------------------------
# POST /report-runs — in-memory mode
# ---------------------------------------------------------------------------


class TestReportRunsIdempotencyInMemory:
    def test_same_key_same_payload_returns_same_id(self) -> None:
        client, area_id = _make_client_with_area()
        key = str(uuid4())
        payload = {"area_id": area_id, "intent_code": "rural_land_purchase"}

        r1 = client.post("/report-runs", json=payload, headers={"Idempotency-Key": key})
        r2 = client.post("/report-runs", json=payload, headers={"Idempotency-Key": key})

        assert r1.status_code == 202
        assert r2.status_code == 200
        assert r1.json()["report_run_id"] == r2.json()["report_run_id"]

    def test_same_key_different_area_returns_409(self) -> None:
        client, area_id_1 = _make_client_with_area()
        # Register a second area on the same client (same app state)
        resp2 = client.post(
            "/areas",
            json={"geom_geojson": _valid_geojson(), "geom_source": "second fixture"},
        )
        assert resp2.status_code == 201
        area_id_2 = resp2.json()["area_id"]

        key = str(uuid4())
        r1 = client.post(
            "/report-runs",
            json={"area_id": area_id_1, "intent_code": "rural_land_purchase"},
            headers={"Idempotency-Key": key},
        )
        assert r1.status_code == 202

        r2 = client.post(
            "/report-runs",
            json={"area_id": area_id_2, "intent_code": "rural_land_purchase"},
            headers={"Idempotency-Key": key},
        )
        assert r2.status_code == 409
        detail = r2.json()["detail"].lower()
        assert "already used" in detail or "different payload" in detail

    def test_same_key_different_intent_returns_409(self) -> None:
        client, area_id = _make_client_with_area()
        key = str(uuid4())

        r1 = client.post(
            "/report-runs",
            json={"area_id": area_id, "intent_code": "rural_land_purchase"},
            headers={"Idempotency-Key": key},
        )
        assert r1.status_code == 202

        r2 = client.post(
            "/report-runs",
            json={"area_id": area_id, "intent_code": "homestead_feasibility"},
            headers={"Idempotency-Key": key},
        )
        assert r2.status_code == 409

    def test_no_key_behavior_unchanged(self) -> None:
        client, area_id = _make_client_with_area()
        payload = {"area_id": area_id, "intent_code": "rural_land_purchase"}

        r1 = client.post("/report-runs", json=payload)
        r2 = client.post("/report-runs", json=payload)

        assert r1.status_code == 202
        assert r2.status_code == 202
        # Without key, two distinct jobs are created.
        assert r1.json()["report_run_id"] != r2.json()["report_run_id"]

    def test_blank_key_treated_as_no_key(self) -> None:
        client, area_id = _make_client_with_area()
        payload = {"area_id": area_id, "intent_code": "rural_land_purchase"}

        r1 = client.post("/report-runs", json=payload, headers={"Idempotency-Key": "  "})
        r2 = client.post("/report-runs", json=payload, headers={"Idempotency-Key": "  "})

        assert r1.status_code == 202
        assert r2.status_code == 202
        # Blank key = no key; creates separate jobs.
        assert r1.json()["report_run_id"] != r2.json()["report_run_id"]

    def test_retry_path_unaffected_by_idempotency(self) -> None:
        """Retry endpoint is independent of Idempotency-Key and always creates a new job."""
        app = create_app()
        client = TestClient(app)
        area_resp = client.post(
            "/areas",
            json={"geom_geojson": _valid_geojson(), "geom_source": "retry test"},
        )
        assert area_resp.status_code == 201
        area_id = area_resp.json()["area_id"]

        services = cast(ApiServices, app.state.services)
        failed_job = services.async_report_jobs.create(
            area_id=UUID(area_id),
            intent_code=IntentCode.RURAL_LAND_PURCHASE,
        )
        services.async_report_jobs.mark_failed(
            failed_job.report_run_id, error_msg="test failure"
        )

        retry = client.post(
            f"/report-runs/{failed_job.report_run_id}/retry",
            headers={
                "X-Reviewer-Id": "fixture-reviewer",
                "X-Reviewer-Token": "fixture-token-123",
            },
        )
        assert retry.status_code == 202
        assert retry.json()["report_run_id"] != str(failed_job.report_run_id)
        assert retry.json()["retry_of_report_run_id"] == str(failed_job.report_run_id)


# ---------------------------------------------------------------------------
# POST /intake — in-memory mode
# ---------------------------------------------------------------------------


class TestIntakeIdempotencyInMemory:
    def test_same_key_same_intent_returns_same_run_id(self) -> None:
        client = TestClient(create_app())
        key = str(uuid4())
        payload = {"area_geojson": _valid_geojson(), "intent_code": "rural_land_purchase"}

        r1 = client.post("/intake", json=payload, headers={"Idempotency-Key": key})
        r2 = client.post("/intake", json=payload, headers={"Idempotency-Key": key})

        assert r1.status_code == 202
        assert r2.status_code == 200
        assert r1.json()["report_run_id"] == r2.json()["report_run_id"]

    def test_same_key_different_intent_creates_distinct_runs_on_intake(self) -> None:
        client = TestClient(create_app())
        key = str(uuid4())

        r1 = client.post(
            "/intake",
            json={"area_geojson": _valid_geojson(), "intent_code": "rural_land_purchase"},
            headers={"Idempotency-Key": key},
        )
        r2 = client.post(
            "/intake",
            json={"area_geojson": _valid_geojson(), "intent_code": "homestead_feasibility"},
            headers={"Idempotency-Key": key},
        )

        assert r1.status_code == 202
        assert r2.status_code == 202
        assert r1.json()["report_run_id"] != r2.json()["report_run_id"]

    def test_no_key_creates_distinct_runs(self) -> None:
        client = TestClient(create_app())
        payload = {"area_geojson": _valid_geojson(), "intent_code": "rural_land_purchase"}

        r1 = client.post("/intake", json=payload)
        r2 = client.post("/intake", json=payload)

        assert r1.status_code == 202
        assert r2.status_code == 202
        assert r1.json()["report_run_id"] != r2.json()["report_run_id"]


# ---------------------------------------------------------------------------
# DB-gated tests (RUN_DB_SMOKE=1)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
class TestReportRunsIdempotencyDB:
    def test_same_key_same_payload_returns_same_id_db(self, tmp_path: Path) -> None:
        from app.core.config import Settings

        settings = Settings(OBJECT_STORE_ROOT=str(tmp_path / "object-store"))
        app = create_app(settings=settings, use_db_services=True)
        client = TestClient(app)

        area_resp = client.post(
            "/areas",
            json={
                "label": "idem db test polygon",
                "geom_geojson": _valid_geojson(),
                "geom_source": "idempotency db fixture",
            },
        )
        assert area_resp.status_code == 201
        area_id = area_resp.json()["area_id"]
        report_run_id: UUID | None = None

        engine = build_engine()
        try:
            key = str(uuid4())
            payload = {"area_id": area_id, "intent_code": "rural_land_purchase"}

            r1 = client.post("/report-runs", json=payload, headers={"Idempotency-Key": key})
            r2 = client.post("/report-runs", json=payload, headers={"Idempotency-Key": key})

            assert r1.status_code == 202
            assert r2.status_code == 200
            assert r1.json()["report_run_id"] == r2.json()["report_run_id"]
            report_run_id = UUID(r1.json()["report_run_id"])

            # Confirm DB has exactly one job for this idempotency key.
            with Session(engine) as session:
                row = session.execute(
                    text(
                        """
                        SELECT count(*) AS cnt
                        FROM jobs.job_queue
                        WHERE idempotency_key = :key
                        """
                    ),
                    {"key": f"report_run:client:{key}"},
                ).one()
            assert row[0] == 1
        finally:
            _cleanup_db_idem_test(
                engine=engine,
                area_id=UUID(area_id),
                report_run_id=report_run_id,
            )

    def test_same_key_different_payload_returns_409_db(self, tmp_path: Path) -> None:
        from app.core.config import Settings

        settings = Settings(OBJECT_STORE_ROOT=str(tmp_path / "object-store"))
        app = create_app(settings=settings, use_db_services=True)
        client = TestClient(app)

        area_resp1 = client.post(
            "/areas",
            json={
                "label": "idem db 409 area 1",
                "geom_geojson": _valid_geojson(),
                "geom_source": "idempotency 409 db fixture",
            },
        )
        area_resp2 = client.post(
            "/areas",
            json={
                "label": "idem db 409 area 2",
                "geom_geojson": _valid_geojson(),
                "geom_source": "idempotency 409 db fixture",
            },
        )
        assert area_resp1.status_code == 201
        assert area_resp2.status_code == 201
        area_id_1 = area_resp1.json()["area_id"]
        area_id_2 = area_resp2.json()["area_id"]
        report_run_id: UUID | None = None

        engine = build_engine()
        try:
            key = str(uuid4())
            r1 = client.post(
                "/report-runs",
                json={"area_id": area_id_1, "intent_code": "rural_land_purchase"},
                headers={"Idempotency-Key": key},
            )
            assert r1.status_code == 202
            report_run_id = UUID(r1.json()["report_run_id"])

            r2 = client.post(
                "/report-runs",
                json={"area_id": area_id_2, "intent_code": "rural_land_purchase"},
                headers={"Idempotency-Key": key},
            )
            assert r2.status_code == 409
        finally:
            _cleanup_db_idem_test(
                engine=engine,
                area_id=UUID(area_id_1),
                report_run_id=report_run_id,
                extra_area_ids=[UUID(area_id_2)],
            )


def _cleanup_db_idem_test(
    *,
    engine: object,
    area_id: UUID,
    report_run_id: UUID | None,
    extra_area_ids: list[UUID] | None = None,
) -> None:
    from sqlalchemy import Engine as _Engine

    assert isinstance(engine, _Engine)
    with Session(engine) as session:
        if report_run_id is not None:
            session.execute(
                text("DELETE FROM jobs.job_queue WHERE job_id = :id"),
                {"id": report_run_id},
            )
            session.execute(
                text("DELETE FROM reports.report_runs WHERE report_run_id = :id"),
                {"id": report_run_id},
            )
        for aid in [area_id] + (extra_area_ids or []):
            session.execute(
                text("DELETE FROM claims.verification_tasks WHERE area_id = :id"),
                {"id": aid},
            )
            session.execute(
                text("DELETE FROM claims.claims WHERE area_id = :id"),
                {"id": aid},
            )
            session.execute(
                text("DELETE FROM evidence.observations WHERE area_id = :id"),
                {"id": aid},
            )
            session.execute(
                text("DELETE FROM core.areas WHERE area_id = :id"),
                {"id": aid},
            )
        session.commit()
