from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domain.enums import AuthorityLevel


class SourceRegistryBase(DeclarativeBase):
    pass


authority_level_enum = ENUM(
    *(level.value for level in AuthorityLevel),
    name="authority_level",
    schema="evidence",
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


__all__ = ["SourceModel", "SourceRegistryBase"]
