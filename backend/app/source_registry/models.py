from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domain.enums import AuthorityLevel, JobStatus


class SourceRegistryBase(DeclarativeBase):
    pass


authority_level_enum = ENUM(
    *(level.value for level in AuthorityLevel),
    name="authority_level",
    schema="evidence",
    create_type=False,
)

job_status_enum = ENUM(
    *(status.value for status in JobStatus),
    name="job_status",
    schema="jobs",
    create_type=False,
)


class SourceModel(SourceRegistryBase):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("name", "organization"),
        {"schema": "source"},
    )

    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    organization: Mapped[str | None] = mapped_column(Text)
    homepage_url: Mapped[str | None] = mapped_column(Text)
    authority_level: Mapped[str] = mapped_column(
        authority_level_enum,
        nullable=False,
        server_default=text("'unknown'"),
    )
    geographic_scope: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    update_cadence: Mapped[str | None] = mapped_column(Text)
    commercial_use_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'unknown'"),
    )
    license_summary: Mapped[str | None] = mapped_column(Text)
    attribution_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    ai_use_allowed: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'unknown'"),
    )
    cache_allowed: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'unknown'"),
    )
    export_allowed: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'unknown'"),
    )
    raw_data_allowed: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'unknown'"),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("now()"),
    )
    source_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )


class SourceDatasetModel(SourceRegistryBase):
    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint("source_id", "dataset_name"),
        {"schema": "source"},
    )

    dataset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source.sources.source_id"),
        nullable=False,
    )
    dataset_name: Mapped[str] = mapped_column(Text, nullable=False)
    dataset_code: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    geometry_type: Mapped[str | None] = mapped_column(Text)
    spatial_resolution: Mapped[str | None] = mapped_column(Text)
    temporal_coverage: Mapped[str | None] = mapped_column(Text)
    legal_caveat: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    dataset_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )


class SourceDatasetVersionModel(SourceRegistryBase):
    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint("dataset_id", "version_label", "retrieved_at"),
        {"schema": "source"},
    )

    dataset_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    dataset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source.datasets.dataset_id"),
        nullable=False,
    )
    version_label: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column()
    retrieved_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("now()"),
    )
    valid_from: Mapped[datetime | None] = mapped_column()
    valid_to: Mapped[datetime | None] = mapped_column()
    checksum: Mapped[str | None] = mapped_column(Text)
    storage_uri: Mapped[str | None] = mapped_column(Text)
    manifest: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    notes: Mapped[str | None] = mapped_column(Text)


class SourceIngestRunModel(SourceRegistryBase):
    __tablename__ = "ingest_runs"
    __table_args__ = {"schema": "source"}

    ingest_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    dataset_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source.dataset_versions.dataset_version_id"),
    )
    connector_name: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("now()"),
    )
    finished_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[str] = mapped_column(
        job_status_enum,
        nullable=False,
        server_default=text("'queued'"),
    )
    row_count: Mapped[int | None] = mapped_column(Integer)
    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    warning_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    log_uri: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )


__all__ = [
    "SourceDatasetModel",
    "SourceDatasetVersionModel",
    "SourceIngestRunModel",
    "SourceModel",
    "SourceRegistryBase",
]
