"""Tests for US-077: DB connection pool explicit configuration.

Verifies that Settings exposes the four pool knobs, that their defaults
are correct, and that they can be overridden via environment variables.
"""
from __future__ import annotations

import pytest

from app.core.config import Settings


def test_default_db_pool_size() -> None:
    s = Settings()
    assert s.db_pool_size == 5


def test_default_db_max_overflow() -> None:
    s = Settings()
    assert s.db_max_overflow == 10


def test_default_db_pool_timeout() -> None:
    s = Settings()
    assert s.db_pool_timeout == 30


def test_default_db_pool_recycle() -> None:
    s = Settings()
    assert s.db_pool_recycle == 1800


def test_env_override_db_pool_size(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_POOL_SIZE", "20")
    s = Settings()
    assert s.db_pool_size == 20


def test_env_override_db_max_overflow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_MAX_OVERFLOW", "25")
    s = Settings()
    assert s.db_max_overflow == 25


def test_env_override_db_pool_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_POOL_TIMEOUT", "60")
    s = Settings()
    assert s.db_pool_timeout == 60


def test_env_override_db_pool_recycle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_POOL_RECYCLE", "3600")
    s = Settings()
    assert s.db_pool_recycle == 3600


def test_all_pool_fields_accessible() -> None:
    """All four pool settings are reachable as attributes on Settings()."""
    s = Settings()
    assert hasattr(s, "db_pool_size")
    assert hasattr(s, "db_max_overflow")
    assert hasattr(s, "db_pool_timeout")
    assert hasattr(s, "db_pool_recycle")
