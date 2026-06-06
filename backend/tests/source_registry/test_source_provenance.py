from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.engine import build_engine
from app.domain.source_contracts import (
    SourceContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)
from app.source_registry.provenance_repo import (
    InMemorySourceProvenanceRepository,
    SqlAlchemySourceProvenanceRepository,
)
from app.source_registry.provenance_service import SourceProvenanceService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository, SqlAlchemySourceRepository


def _make_source() -> SourceContract:
    return SourceContract(
        name="Fixture FEMA NFHL",
        organization="FEMA",
        domain="flood",
        license_status="approved",
        commercial_use_status="approved",
        redistribution_status="restricted",
        cache_allowed="approved",
        export_allowed="approved-with-restrictions",
        raw_data_allowed="approved",
        ai_use_allowed="restricted",
        review_status="approved",
    )


def test_source_provenance_service_exports_review_bundle() -> None:
    source_service = SourceService(InMemorySourceRepository())
    provenance_service = SourceProvenanceService(
        source_service=source_service,
        repo=InMemorySourceProvenanceRepository(),
    )
    source = source_service.register(_make_source())

    dataset = provenance_service.create_dataset(
        source_id=source.source_id,
        dataset_name="National Flood Hazard Layer",
        domain="flood",
        legal_caveat="Screening only; not a flood determination.",
    )
    version = provenance_service.create_dataset_version(
        dataset_id=dataset.dataset_id,
        version_label="2026-06",
        published_at=datetime(2026, 6, 1, tzinfo=UTC),
        retrieved_at=datetime(2026, 6, 3, 9, 0, tzinfo=UTC),
        manifest={"flood_zone": "fixture"},
        is_current=True,
        notes="Fixture version for review bundle tests.",
    )
    provenance_service.record_retrieval_run(
        dataset_version_id=version.dataset_version_id,
        connector_name="fixture_fema",
        status=SourceRetrievalStatus.RUNNING,
        started_at=datetime(2026, 6, 3, 9, 5, tzinfo=UTC),
        metrics={"rows_seen": 12},
    )
    provenance_service.record_retrieval_run(
        dataset_version_id=version.dataset_version_id,
        connector_name="fixture_fema",
        status=SourceRetrievalStatus.BLOCKED,
        started_at=datetime(2026, 6, 3, 9, 10, tzinfo=UTC),
        finished_at=datetime(2026, 6, 3, 9, 12, tzinfo=UTC),
        error_count=1,
        warning_count=1,
        log_uri="file:///tmp/fixture.log",
        metrics={"reason": "fixture endpoint returned 503"},
    )

    bundle = provenance_service.export_review_bundle(source.source_id)

    datasets = cast(list[dict[str, Any]], bundle["datasets"])
    versions = cast(list[dict[str, Any]], bundle["dataset_versions"])
    runs = cast(list[dict[str, Any]], bundle["retrieval_runs"])

    assert bundle["production_use_allowed"] is True
    assert bundle["review_summary"] == {
        "source_count": 1,
        "dataset_count": 1,
        "dataset_version_count": 1,
        "retrieval_run_count": 2,
    }
    assert bundle["latest_retrieval_status"] == "blocked"
    assert datasets[0]["dataset_name"] == "National Flood Hazard Layer"
    assert versions[0]["is_current"] is True
    assert runs[1]["status"] == "blocked"
    assert runs[1]["warning_count"] == 1


def test_source_provenance_service_exposes_stale_and_failed_states() -> None:
    source_service = SourceService(InMemorySourceRepository())
    provenance_service = SourceProvenanceService(
        source_service=source_service,
        repo=InMemorySourceProvenanceRepository(),
    )
    source = source_service.register(
        _make_source().model_copy(update={"freshness_class": "stale"})
    )

    dataset = provenance_service.create_dataset(
        source_id=source.source_id,
        dataset_name="National Flood Hazard Layer",
        domain="flood",
        legal_caveat="Screening only; not a flood determination.",
    )
    version = provenance_service.create_dataset_version(
        dataset_id=dataset.dataset_id,
        version_label="2026-05",
        published_at=datetime(2026, 5, 1, tzinfo=UTC),
        retrieved_at=datetime(2026, 6, 3, 8, 45, tzinfo=UTC),
        manifest={"flood_zone": "fixture"},
        is_current=False,
    )
    provenance_service.record_retrieval_run(
        dataset_version_id=version.dataset_version_id,
        connector_name="fixture_fema",
        status=SourceRetrievalStatus.FAILED,
        started_at=datetime(2026, 6, 3, 8, 50, tzinfo=UTC),
        finished_at=datetime(2026, 6, 3, 8, 51, tzinfo=UTC),
        error_count=2,
        log_uri="file:///tmp/failed.log",
        metrics={"reason": "timeout"},
    )

    bundle = provenance_service.export_review_bundle(source.source_id)
    source_bundle = cast(dict[str, Any], bundle["source"])

    assert source_bundle["freshness_class"] == "stale"
    assert bundle["latest_retrieval_status"] == "failed"


def test_record_retrieval_run_contract_preserves_supplied_identity() -> None:
    source_service = SourceService(InMemorySourceRepository())
    provenance_service = SourceProvenanceService(
        source_service=source_service,
        repo=InMemorySourceProvenanceRepository(),
    )
    source = source_service.register(_make_source())
    dataset = provenance_service.create_dataset(
        source_id=source.source_id,
        dataset_name="National Flood Hazard Layer",
        domain="flood",
    )
    version = provenance_service.create_dataset_version(
        dataset_id=dataset.dataset_id,
        version_label="2026-06",
    )
    supplied_run = SourceRetrievalRunContract(
        dataset_version_id=version.dataset_version_id,
        connector_name="fixture_flood_static",
        status=SourceRetrievalStatus.SUCCEEDED,
        started_at=datetime(2026, 6, 4, 9, 0, tzinfo=UTC),
        finished_at=datetime(2026, 6, 4, 9, 1, tzinfo=UTC),
        row_count=1,
    )

    recorded = provenance_service.record_retrieval_run_contract(supplied_run)

    assert recorded.ingest_run_id == supplied_run.ingest_run_id
    assert recorded.dataset_version_id == version.dataset_version_id
    assert provenance_service.retrieval_run_exists(supplied_run.ingest_run_id) is True


def test_record_retrieval_run_contract_rejects_duplicate_identity() -> None:
    source_service = SourceService(InMemorySourceRepository())
    provenance_service = SourceProvenanceService(
        source_service=source_service,
        repo=InMemorySourceProvenanceRepository(),
    )
    supplied_run = SourceRetrievalRunContract(
        dataset_version_id=None,
        connector_name="fixture_flood_static",
        status=SourceRetrievalStatus.SKIPPED,
    )

    provenance_service.record_retrieval_run_contract(supplied_run)

    with pytest.raises(ValueError, match="already registered"):
        provenance_service.record_retrieval_run_contract(supplied_run)


@pytest.mark.parametrize(
    "field_name",
    ("row_count", "error_count", "warning_count"),
)
def test_source_retrieval_run_contract_rejects_negative_counts(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        SourceRetrievalRunContract.model_validate(
            {
                "connector_name": "fixture_flood_static",
                field_name: -1,
            },
        )


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
def test_sqlalchemy_source_provenance_repository_round_trips_records() -> None:
    engine = build_engine()
    source_service = SourceService(InMemorySourceRepository())

    with Session(engine) as session:
        source_service = SourceService(SqlAlchemySourceRepository(session))
        provenance_service = SourceProvenanceService(
            source_service=source_service,
            repo=SqlAlchemySourceProvenanceRepository(session),
        )
        source = source_service.register(
            _make_source().model_copy(
                update={"name": f"Fixture FEMA NFHL {uuid4()}"}
            )
        )
        dataset = provenance_service.create_dataset(
            source_id=source.source_id,
            dataset_name="National Flood Hazard Layer",
            domain="flood",
            legal_caveat="Screening only; not a flood determination.",
        )
        version = provenance_service.create_dataset_version(
            dataset_id=dataset.dataset_id,
            version_label="2026-06",
            published_at=datetime(2026, 6, 1, tzinfo=UTC),
            retrieved_at=datetime(2026, 6, 3, 9, 0, tzinfo=UTC),
            checksum="abc123",
            storage_uri="s3://fixtures/nfhl/2026-06",
            manifest={"rows": 12},
            is_current=True,
        )
        run = provenance_service.record_retrieval_run(
            dataset_version_id=version.dataset_version_id,
            connector_name="fixture_fema",
            status=SourceRetrievalStatus.SKIPPED,
            started_at=datetime(2026, 6, 3, 9, 5, tzinfo=UTC),
            finished_at=datetime(2026, 6, 3, 9, 6, tzinfo=UTC),
            warning_count=1,
            log_uri="file:///tmp/fixture.log",
            metrics={"reason": "fixture skipped"},
        )
        supplied_run = SourceRetrievalRunContract(
            dataset_version_id=version.dataset_version_id,
            connector_name="fixture_flood_static",
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=datetime(2026, 6, 3, 9, 7, tzinfo=UTC),
            finished_at=datetime(2026, 6, 3, 9, 8, tzinfo=UTC),
            row_count=2,
        )
        supplied_recorded_run = provenance_service.record_retrieval_run_contract(
            supplied_run,
        )
        session.commit()

    with Session(engine) as session:
        source_service = SourceService(SqlAlchemySourceRepository(session))
        repo = SqlAlchemySourceProvenanceRepository(session)
        retrieved_dataset = repo.get_dataset(dataset.dataset_id)
        retrieved_version = repo.get_dataset_version(version.dataset_version_id)
        retrieved_run = repo.get_retrieval_run(run.ingest_run_id)
        retrieved_supplied_run = repo.get_retrieval_run(supplied_run.ingest_run_id)
        review_service = SourceProvenanceService(
            source_service=source_service,
            repo=repo,
        )
        bundle = review_service.export_review_bundle(source.source_id)

    assert retrieved_dataset is not None
    assert retrieved_dataset.dataset_name == "National Flood Hazard Layer"
    assert retrieved_version is not None
    assert retrieved_version.checksum == "abc123"
    assert retrieved_run is not None
    assert retrieved_run.status == SourceRetrievalStatus.SKIPPED
    assert retrieved_supplied_run is not None
    assert retrieved_supplied_run.ingest_run_id == supplied_recorded_run.ingest_run_id
    assert bundle["latest_retrieval_status"] == "succeeded"

    with Session(engine) as session:
        session.execute(
            text("DELETE FROM source.ingest_runs WHERE ingest_run_id = :ingest_run_id"),
            {"ingest_run_id": supplied_run.ingest_run_id},
        )
        session.execute(
            text("DELETE FROM source.ingest_runs WHERE ingest_run_id = :ingest_run_id"),
            {"ingest_run_id": run.ingest_run_id},
        )
        session.execute(
            text(
                "DELETE FROM source.dataset_versions "
                "WHERE dataset_version_id = :dataset_version_id"
            ),
            {"dataset_version_id": version.dataset_version_id},
        )
        session.execute(
            text("DELETE FROM source.datasets WHERE dataset_id = :dataset_id"),
            {"dataset_id": dataset.dataset_id},
        )
        session.execute(
            text("DELETE FROM source.sources WHERE source_id = :source_id"),
            {"source_id": source.source_id},
        )
        session.commit()
