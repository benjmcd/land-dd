from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Naming convention for consistent constraint naming across all schemas.
# Required for Alembic autogenerate to produce deterministic migration names.
_convention = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class AppBase(DeclarativeBase):
    """Single shared ORM base for all land-diligence SQLAlchemy models.

    All model files must inherit from this class rather than declaring
    their own DeclarativeBase. A single base ensures:
    - One unified MetaData registry (enables cross-lane FK resolution
      once relationship() declarations are added)
    - No duplicate ENUM type objects for the same PostgreSQL type
    - Consistent constraint naming for future Alembic migrations

    Note: bare ForeignKey() column declarations referencing tables that
    have no ORM model class (e.g. core.workspaces, core.users) are safe
    without stub models as long as no relationship() calls resolve them.
    Add stub models before adding relationship() declarations to those FKs.
    """

    metadata = MetaData(naming_convention=_convention)


__all__ = ["AppBase"]
