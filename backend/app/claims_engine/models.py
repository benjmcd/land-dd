from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import AppBase
from app.db.types import confidence_band_enum, severity_band_enum


class ClaimModel(AppBase):
    """ORM model for claims.claims.

    Schema verified against db/migrations/0001_initial_spine.sql.
    Note: the 'metadata' column is mapped as 'claim_metadata' to avoid
    colliding with DeclarativeBase.metadata (a SQLAlchemy reserved attribute).
    """

    __tablename__ = "claims"
    __table_args__ = {"schema": "claims"}

    claim_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    area_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.areas.area_id"),
        nullable=False,
    )
    # rule_execution_run_id and intent_id are nullable FKs present in the DB
    # schema but not yet populated by the current rule engine path.
    rule_execution_run_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rules.rule_execution_runs.rule_execution_run_id"),
        nullable=True,
    )
    intent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.intents.intent_id"),
        nullable=True,
    )
    claim_code: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    assertion: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        severity_band_enum,
        nullable=False,
        server_default=text("'unknown'"),
    )
    confidence: Mapped[str] = mapped_column(
        confidence_band_enum,
        nullable=False,
        server_default=text("'unknown'"),
    )
    user_safe_language: Mapped[str] = mapped_column(Text, nullable=False)
    verification_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    verification_task: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    # DB column is named 'metadata'; mapped as 'claim_metadata' to avoid
    # colliding with DeclarativeBase.metadata.
    claim_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )


class ClaimEvidenceLinkModel(AppBase):
    """ORM model for claims.claim_evidence.

    Composite primary key (claim_id, evidence_id).
    """

    __tablename__ = "claim_evidence"
    __table_args__ = {"schema": "claims"}

    claim_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("claims.claims.claim_id", ondelete="CASCADE"),
        primary_key=True,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("evidence.observations.evidence_id"),
        primary_key=True,
    )
    support_role: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'supports'"),
    )


class VerificationTaskModel(AppBase):
    """ORM model for claims.verification_tasks."""

    __tablename__ = "verification_tasks"
    __table_args__ = {"schema": "claims"}

    verification_task_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    area_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.areas.area_id"),
        nullable=False,
    )
    claim_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("claims.claims.claim_id"),
        nullable=True,
    )
    task_code: Mapped[str] = mapped_column(Text, nullable=False)
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    responsible_party: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(
        severity_band_enum,
        nullable=False,
        server_default=text("'medium'"),
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'open'"),
    )
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completion_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )


__all__ = ["ClaimEvidenceLinkModel", "ClaimModel", "VerificationTaskModel"]
