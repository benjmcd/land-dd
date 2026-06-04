from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from app.domain.enums import AuthorityLevel, ConfidenceBand


class GeometryFromGeoJSON(UserDefinedType[Any]):
    cache_ok = True

    def get_col_spec(self, **_: Any) -> str:
        return "geometry(Geometry,4326)"


authority_level_enum = ENUM(
    *(level.value for level in AuthorityLevel),
    name="authority_level",
    schema="evidence",
    create_type=False,
)

confidence_band_enum = ENUM(
    *(level.value for level in ConfidenceBand),
    name="confidence_band",
    schema="evidence",
    create_type=False,
)


class EvidenceLedgerBase(DeclarativeBase):
    pass


class EvidenceObservationModel(EvidenceLedgerBase):
    __tablename__ = "observations"
    __table_args__ = {"schema": "evidence"}

    evidence_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    area_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.areas.area_id"),
        nullable=False,
    )
    dataset_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source.dataset_versions.dataset_version_id"),
    )
    ingest_run_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source.ingest_runs.ingest_run_id"),
    )
    evidence_type: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    observed_value: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    method_code: Mapped[str] = mapped_column(Text, nullable=False)
    method_version: Mapped[str] = mapped_column(Text, nullable=False)
    authority_level: Mapped[str] = mapped_column(
        authority_level_enum,
        nullable=False,
        server_default=text("'unknown'"),
    )
    confidence: Mapped[str] = mapped_column(
        confidence_band_enum,
        nullable=False,
        server_default=text("'unknown'"),
    )
    source_date: Mapped[date | None] = mapped_column(Date)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    caveat: Mapped[str | None] = mapped_column(Text)
    is_negative_evidence: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    is_source_failure: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    geometry: Mapped[str | None] = mapped_column(GeometryFromGeoJSON())
    observation_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )


class AuditEventModel(EvidenceLedgerBase):
    __tablename__ = "events"
    __table_args__ = {"schema": "audit"}

    audit_event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    workspace_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.workspaces.workspace_id"),
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.users.user_id"),
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_table: Mapped[str | None] = mapped_column(Text)
    target_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    ip_address: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )


__all__ = [
    "AuditEventModel",
    "EvidenceLedgerBase",
    "EvidenceObservationModel",
]
