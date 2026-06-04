from __future__ import annotations

from typing import cast

from sqlalchemy import Table

from app.source_registry.models import (
    SourceDatasetModel,
    SourceDatasetVersionModel,
    SourceIngestRunModel,
)


def test_source_dataset_model_maps_to_source_datasets_table() -> None:
    assert SourceDatasetModel.__tablename__ == "datasets"
    assert SourceDatasetModel.__table__.schema == "source"
    assert list(cast(Table, SourceDatasetModel.__table__).columns.keys()) == [
        "dataset_id",
        "source_id",
        "dataset_name",
        "dataset_code",
        "domain",
        "geometry_type",
        "spatial_resolution",
        "temporal_coverage",
        "legal_caveat",
        "source_url",
        "metadata",
    ]


def test_source_dataset_version_model_maps_to_source_dataset_versions_table() -> None:
    assert SourceDatasetVersionModel.__tablename__ == "dataset_versions"
    assert SourceDatasetVersionModel.__table__.schema == "source"
    assert list(cast(Table, SourceDatasetVersionModel.__table__).columns.keys()) == [
        "dataset_version_id",
        "dataset_id",
        "version_label",
        "published_at",
        "retrieved_at",
        "valid_from",
        "valid_to",
        "checksum",
        "storage_uri",
        "manifest",
        "is_current",
        "notes",
    ]


def test_source_ingest_run_model_maps_to_source_ingest_runs_table() -> None:
    assert SourceIngestRunModel.__tablename__ == "ingest_runs"
    assert SourceIngestRunModel.__table__.schema == "source"
    assert list(cast(Table, SourceIngestRunModel.__table__).columns.keys()) == [
        "ingest_run_id",
        "dataset_version_id",
        "connector_name",
        "started_at",
        "finished_at",
        "status",
        "row_count",
        "error_count",
        "warning_count",
        "log_uri",
        "metrics",
    ]
