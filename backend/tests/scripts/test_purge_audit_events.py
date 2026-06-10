"""DB-gated tests for scripts/purge_audit_events.py.

Gated by RUN_DB_SMOKE=1 (same convention as other DB tests in this repo).
Requires a live Postgres instance with the schema applied and DATABASE_URL_SYNC
(or DATABASE_URL) pointing at it.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "purge_audit_events.py"


def _load_purge_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("purge_audit_events", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["purge_audit_events"] = module
    spec.loader.exec_module(module)
    return module


def _resolve_db_url() -> str:
    url = os.environ.get(
        "DATABASE_URL_SYNC",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://land:land@localhost:5432/land_diligence",
        ),
    )
    url = url.replace("postgresql+psycopg://", "postgresql://")
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url


def _insert_audit_event(
    conn: Any,
    *,
    event_type: str,
    occurred_at: datetime,
) -> str:
    """Insert a minimal audit.events row and return audit_event_id as str."""
    event_id = str(uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit.events (audit_event_id, event_type, occurred_at, payload)
            VALUES (%s, %s, %s, '{}'::jsonb)
            """,
            (event_id, event_type, occurred_at),
        )
    conn.commit()
    return event_id


def _event_exists(conn: Any, event_id: str) -> bool:
    """Return True if the audit_event_id row still exists."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM audit.events WHERE audit_event_id = %s",
            (event_id,),
        )
        return cur.fetchone() is not None


def _delete_event(conn: Any, event_id: str) -> None:
    """Clean up a test row by id."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM audit.events WHERE audit_event_id = %s",
            (event_id,),
        )
    conn.commit()


@pytest.mark.skipif(os.getenv("RUN_DB_SMOKE") != "1", reason="DB smoke not enabled")
class TestPurgeAuditEventsDb:
    """DB-gated integration tests for purge_audit_events.run_purge."""

    def setup_method(self) -> None:
        self.module = _load_purge_module()
        self.db_url = _resolve_db_url()

        import psycopg

        self.conn: Any = psycopg.connect(self.db_url)
        self._inserted_ids: list[str] = []

    def teardown_method(self) -> None:
        # Clean up any rows we inserted (in case assertions failed mid-test)
        for event_id in self._inserted_ids:
            try:
                _delete_event(self.conn, event_id)
            except Exception:
                pass
        try:
            self.conn.close()
        except Exception:
            pass

    def _insert(self, *, event_type: str, occurred_at: datetime) -> str:
        eid = _insert_audit_event(self.conn, event_type=event_type, occurred_at=occurred_at)
        self._inserted_ids.append(eid)
        return eid

    def test_dry_run_deletes_nothing_and_reports_old_in_scope_row(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Dry-run must NOT delete rows and must report the old in-scope row."""
        old_ts = datetime.now(UTC) - timedelta(days=120)
        recent_ts = datetime.now(UTC) - timedelta(days=10)

        old_in_scope_id = self._insert(event_type="api_key_auth", occurred_at=old_ts)
        recent_in_scope_id = self._insert(event_type="created", occurred_at=recent_ts)

        # dry-run
        self.module.run_purge(
            db_url=self.db_url,
            retention_days=90,
            apply=False,
        )

        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out
        assert "api_key_auth" in captured.out
        # both rows must still exist
        assert _event_exists(self.conn, old_in_scope_id)
        assert _event_exists(self.conn, recent_in_scope_id)

    def test_dry_run_does_not_report_out_of_scope_event_type(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An old row with an unknown/future event_type must NOT appear in the report."""
        old_ts = datetime.now(UTC) - timedelta(days=120)
        out_of_scope_id = self._insert(event_type="unknown_future_type", occurred_at=old_ts)

        self.module.run_purge(
            db_url=self.db_url,
            retention_days=90,
            apply=False,
        )

        captured = capsys.readouterr()
        # The out-of-scope type must never appear in the output
        assert "unknown_future_type" not in captured.out
        # Row must still exist
        assert _event_exists(self.conn, out_of_scope_id)

    def test_apply_deletes_old_in_scope_row_only(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--apply must delete the old in-scope row and leave all others intact."""
        old_ts = datetime.now(UTC) - timedelta(days=120)
        recent_ts = datetime.now(UTC) - timedelta(days=10)

        old_in_scope_id = self._insert(event_type="api_key_auth", occurred_at=old_ts)
        recent_in_scope_id = self._insert(event_type="created", occurred_at=recent_ts)
        old_out_of_scope_id = self._insert(event_type="unknown_future_type", occurred_at=old_ts)

        # Remove old_in_scope from cleanup list — apply will delete it
        self._inserted_ids.remove(old_in_scope_id)

        self.module.run_purge(
            db_url=self.db_url,
            retention_days=90,
            apply=True,
        )

        captured = capsys.readouterr()
        assert "APPLY" in captured.out
        assert "deleted" in captured.out

        # Old in-scope row must be gone
        assert not _event_exists(self.conn, old_in_scope_id)
        # Recent in-scope row must remain
        assert _event_exists(self.conn, recent_in_scope_id)
        # Old out-of-scope row must remain
        assert _event_exists(self.conn, old_out_of_scope_id)

    def test_apply_all_evidence_event_types(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Both 'created' and 'superseded' event types must be purged when old."""
        old_ts = datetime.now(UTC) - timedelta(days=120)

        created_id = self._insert(event_type="created", occurred_at=old_ts)
        superseded_id = self._insert(event_type="superseded", occurred_at=old_ts)

        # Remove from cleanup — apply will delete them
        self._inserted_ids.remove(created_id)
        self._inserted_ids.remove(superseded_id)

        self.module.run_purge(
            db_url=self.db_url,
            retention_days=90,
            apply=True,
        )

        assert not _event_exists(self.conn, created_id)
        assert not _event_exists(self.conn, superseded_id)
