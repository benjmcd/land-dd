from __future__ import annotations

from collections.abc import Iterator

import pytest
from pytest import MonkeyPatch

from app.db import session as session_module


def test_get_db_session_delegates_to_shared_get_session(
    monkeypatch: MonkeyPatch,
) -> None:
    yielded: object = object()
    closed = False

    def fake_get_session() -> Iterator[object]:
        nonlocal closed
        try:
            yield yielded
        finally:
            closed = True

    monkeypatch.setattr(session_module, "get_session", fake_get_session)

    db_session = session_module.get_db_session()

    assert next(db_session) is yielded
    with pytest.raises(StopIteration):
        next(db_session)
    assert closed is True
