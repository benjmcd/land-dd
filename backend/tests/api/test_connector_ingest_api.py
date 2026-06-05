from __future__ import annotations

import os
from pathlib import Path
from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import ApiServices
from app.area_geometry.area_repo import SqlAlchemyAreaRepository
from app.area_geometry.service import AreaService
from app.core.config import Settings
from app.db.engine import build_engine
from app.domain.area_contracts import AreaContract
from app.domain.source_contracts import (
    SourceContract,
)
from app.main import create_app
from app.source_registry.service import SourceService
from app.source_registry.source_repo import SqlAlchemySourceRepository

_FIXTURE_SOURCE_ID = UUID("55555555-5555-4555-8555-555555555555")
_FIXTURE_AREA_ID = UUID("44444444-4444-4444-8444-444444444444")
_FIXTURE_DATASET_ID = UUID("11111111-2222-4333-8444-555555555555")
_FIXTURE_DATASET_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")
_FIXTURE_INGEST_RUN_ID = UUID("11111111-1111-4111-8111-111111111111")
_FIXTURE_FAILURE_INGEST_RUN_ID = UUID("66666666-6666-4666-8666-666666666666")
_FIXTURE_AREA_GEOJSON: dict[str, object] = {
    "type": "Polygon",
    "coordinates": [
        [
            [-120.0, 38.0],
            [-119.9, 38.0],
            [-119.9, 38.1],
            [-120.0, 38.1],
            [-120.0, 38.0],
        ]
    ],
}


def _seed(services: ApiServices) -> None:
    services.source_service.register(
        SourceContract(
            source_id=_FIXTURE_SOURCE_ID,
            name="Fixture Flood Source",
            domain="flood",
            license_status="approved",
            commercial_use_status="approved",
            redistribution_status="approved",
            cache_allowed="approved",
            export_allowed="approved",
            raw_data_allowed="approved",
            ai_use_allowed="approved",
            review_status="approved",
        )
    )
    services.area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            geom_geojson=_FIXTURE_AREA_GEOJSON,
        )
    )


def _seed_db(session: Session) -> None:
    source_service = SourceService(SqlAlchemySourceRepository(session))
    area_service = AreaService(SqlAlchemyAreaRepository(session))

    area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            geom_geojson=_FIXTURE_AREA_GEOJSON,
        )
    )
    source_service.register(
        SourceContract(
            source_id=_FIXTURE_SOURCE_ID,
            name="Fixture Flood Source",
            organization="fixture-connector-ingest-smoke",
            domain="flood",
            license_status="approved",
            commercial_use_status="approved",
            redistribution_status="approved",
            cache_allowed="approved",
            export_allowed="approved",
            raw_data_allowed="approved",
            ai_use_allowed="approved",
            review_status="approved",
        )
    )
    session.commit()


def _cleanup_db(session: Session) -> None:
    _idempotency_key = "connector_review_status:{}"
    session.execute(
        text(
            """
            DELETE FROM jobs.job_queue
            WHERE job_type = 'connector_review_status'
              AND idempotency_key IN (:success_key, :failure_key)
            """
        ),
        {
            "success_key": _idempotency_key.format(_FIXTURE_INGEST_RUN_ID),
            "failure_key": _idempotency_key.format(_FIXTURE_FAILURE_INGEST_RUN_ID),
        },
    )
    session.execute(
        text(
            """
            DELETE FROM audit.events
            WHERE target_id IN (
                SELECT evidence_id
                FROM evidence.observations
                WHERE area_id = :area_id
            )
            """
        ),
        {"area_id": _FIXTURE_AREA_ID},
    )
    session.execute(
        text("DELETE FROM evidence.observations WHERE area_id = :area_id"),
        {"area_id": _FIXTURE_AREA_ID},
    )
    session.execute(
        text(
            """
            DELETE FROM source.ingest_runs
            WHERE ingest_run_id IN (:success_run_id, :failure_run_id)
            """
        ),
        {
            "success_run_id": _FIXTURE_INGEST_RUN_ID,
            "failure_run_id": _FIXTURE_FAILURE_INGEST_RUN_ID,
        },
    )
    session.execute(
        text(
            "DELETE FROM source.dataset_versions WHERE dataset_version_id = :id"
        ),
        {"id": _FIXTURE_DATASET_VERSION_ID},
    )
    session.execute(
        text("DELETE FROM source.datasets WHERE dataset_id = :id"),
        {"id": _FIXTURE_DATASET_ID},
    )
    session.execute(
        text("DELETE FROM source.sources WHERE source_id = :id"),
        {"id": _FIXTURE_SOURCE_ID},
    )
    session.execute(
        text("DELETE FROM core.areas WHERE area_id = :id"),
        {"id": _FIXTURE_AREA_ID},
    )
    session.commit()


def test_run_flood_connector_success_creates_evidence() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    response = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "flood_success"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["ingest_run_id"] == "11111111-1111-4111-8111-111111111111"
    assert body["connector_name"] == "fixture_flood_static"
    assert body["retrieval_status"] == "succeeded"
    assert body["evidence_created"] == 1
    assert body["evidence_skipped"] == 0
    assert body["review_required"] is False
    assert body["queue_job_id"] is not None


def test_run_flood_connector_failure_sets_review_required() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    response = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "flood_failure"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["retrieval_status"] == "blocked"
    assert body["evidence_created"] == 1  # source-failure evidence is first-class
    assert body["review_required"] is True
    assert body["queue_job_id"] is not None


def test_run_zoning_connector_allowed_creates_evidence() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    response = client.post(
        "/connector-runs",
        json={
            "connector_name": "fixture_zoning_static",
            "fixture_key": "zoning_allowed",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["connector_name"] == "fixture_zoning_static"
    assert body["retrieval_status"] == "succeeded"
    assert body["evidence_created"] == 1
    assert body["evidence_skipped"] == 0
    assert body["review_required"] is False
    assert body["queue_job_id"] is not None


def test_run_zoning_connector_failure_sets_review_required() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    response = client.post(
        "/connector-runs",
        json={
            "connector_name": "fixture_zoning_static",
            "fixture_key": "zoning_failure",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["retrieval_status"] == "blocked"
    assert body["evidence_created"] == 1
    assert body["review_required"] is True


def test_run_connector_returns_422_for_unsupported_connector_name() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/connector-runs",
        json={"connector_name": "unknown_connector", "fixture_key": "flood_success"},
    )

    assert response.status_code == 422
    assert "unsupported connector" in response.json()["detail"]


def test_run_connector_returns_422_for_unknown_fixture_key() -> None:
    app = create_app()
    client = TestClient(app)
    _seed(cast(ApiServices, app.state.services))

    response = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "does_not_exist"},
    )

    assert response.status_code == 422
    assert "fixture not found" in response.json()["detail"]


def test_run_connector_returns_422_for_invalid_fixture_key_characters() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "../etc/passwd"},
    )

    assert response.status_code == 422
    assert "fixture_key" in response.json()["detail"]


def test_run_connector_returns_422_when_fixture_source_is_missing() -> None:
    app = create_app()
    client = TestClient(app)
    services = cast(ApiServices, app.state.services)
    services.area_service.create(
        AreaContract(
            area_id=_FIXTURE_AREA_ID,
            geom_geojson=_FIXTURE_AREA_GEOJSON,
        )
    )

    response = client.post(
        "/connector-runs",
        json={"connector_name": "fixture_flood_static", "fixture_key": "flood_success"},
    )

    assert response.status_code == 422
    assert "is not registered" in response.json()["detail"]


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_db_backed_api_connector_ingest_persists_evidence_and_queue_item(
    tmp_path: Path,
) -> None:
    engine = build_engine()
    try:
        with Session(engine) as session:
            _cleanup_db(session)
            _seed_db(session)

        settings = Settings(OBJECT_STORE_ROOT=str(tmp_path / "object-store"))
        app = create_app(settings=settings, use_db_services=True)
        client = TestClient(app)

        response = client.post(
            "/connector-runs",
            json={
                "connector_name": "fixture_flood_static",
                "fixture_key": "flood_success",
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["ingest_run_id"] == str(_FIXTURE_INGEST_RUN_ID)
        assert body["retrieval_status"] == "succeeded"
        assert body["evidence_created"] == 1
        assert body["evidence_skipped"] == 0
        assert body["review_required"] is False
        assert body["queue_job_id"] is not None

        with Session(engine) as session:
            run_row = session.execute(
                text(
                    "SELECT connector_name, status, dataset_version_id "
                    "FROM source.ingest_runs WHERE ingest_run_id = :id"
                ),
                {"id": _FIXTURE_INGEST_RUN_ID},
            ).one_or_none()
            assert run_row is not None
            assert run_row[0] == "fixture_flood_static"
            assert run_row[1] == "succeeded"
            assert run_row[2] == _FIXTURE_DATASET_VERSION_ID

            ev_rows = session.execute(
                text(
                    "SELECT evidence_id FROM evidence.observations "
                    "WHERE area_id = :area_id"
                ),
                {"area_id": _FIXTURE_AREA_ID},
            ).fetchall()
            assert len(ev_rows) == 1

            job_row = session.execute(
                text(
                    "SELECT status FROM jobs.job_queue "
                    "WHERE job_type = 'connector_review_status' "
                    "  AND idempotency_key = :key"
                ),
                {"key": f"connector_review_status:{_FIXTURE_INGEST_RUN_ID}"},
            ).one_or_none()
            assert job_row is not None
            assert job_row[0] == "queued"
    finally:
        with Session(engine) as session:
            _cleanup_db(session)
