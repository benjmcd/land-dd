from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.db.engine import get_session


def get_db_session() -> Iterator[Session]:
    """FastAPI dependency that yields sessions from the shared engine pool."""
    yield from get_session()


__all__ = ["get_db_session"]
