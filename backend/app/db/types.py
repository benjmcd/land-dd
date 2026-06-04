from __future__ import annotations

from sqlalchemy.dialects.postgresql import ENUM

from app.domain.enums import AuthorityLevel, ConfidenceBand, JobStatus

# Canonical PostgreSQL ENUM type instances shared across all ORM model modules.
# Each enum corresponds to a type already declared in the SQL migration
# (db/migrations/0001_initial_spine.sql). All use create_type=False because
# DDL is managed by migrations, not by SQLAlchemy.
#
# Rule: import from here; never redeclare these in individual model files.

authority_level_enum = ENUM(
    *(level.value for level in AuthorityLevel),
    name="authority_level",
    schema="evidence",
    create_type=False,
)

confidence_band_enum = ENUM(
    *(confidence.value for confidence in ConfidenceBand),
    name="confidence_band",
    schema="evidence",
    create_type=False,
)

job_status_enum = ENUM(
    *(status.value for status in JobStatus),
    name="job_status",
    schema="jobs",
    create_type=False,
)

__all__ = [
    "authority_level_enum",
    "confidence_band_enum",
    "job_status_enum",
]
