from __future__ import annotations

from sqlalchemy.dialects.postgresql import ENUM

from app.domain.enums import AuthorityLevel, ConfidenceBand, IntentCode, JobStatus, SeverityBand

# Canonical PostgreSQL ENUM type instances — one definition per DB ENUM type.
# Source of truth: db/migrations/0001_initial_spine.sql.
# All use create_type=False — DDL is migration-managed, never ORM-managed.
#
# Rule: import from here; never redeclare in individual model files.

authority_level_enum = ENUM(
    *(v.value for v in AuthorityLevel),
    name="authority_level",
    schema="evidence",
    create_type=False,
)

confidence_band_enum = ENUM(
    *(v.value for v in ConfidenceBand),
    name="confidence_band",
    schema="evidence",
    create_type=False,
)

job_status_enum = ENUM(
    *(v.value for v in JobStatus),
    name="job_status",
    schema="jobs",
    create_type=False,
)

severity_band_enum = ENUM(
    *(v.value for v in SeverityBand),
    name="severity_band",
    schema="claims",
    create_type=False,
)

intent_code_enum = ENUM(
    *(v.value for v in IntentCode),
    name="intent_code",
    schema="core",
    create_type=False,
)

# area_type_enum is declared in app.area_geometry.models (not here) because its
# SQL values differ from the Python AreaType enum — a known schema mismatch that
# requires a coordinated migration before it can be unified here.
# See: db/migrations/0001_initial_spine.sql core.area_type (9 SQL values) vs
#      app.domain.enums.AreaType (6 Python values, only 2 overlap).

__all__ = [
    "authority_level_enum",
    "confidence_band_enum",
    "intent_code_enum",
    "job_status_enum",
    "severity_band_enum",
]
