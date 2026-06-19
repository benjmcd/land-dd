"""DB-gated tests for scripts/purge_audit_events.py.

Gated by RUN_DB_SMOKE=1 (same convention as other DB tests in this repo).
Requires a live Postgres instance with the schema applied and DATABASE_URL_SYNC
(or DATABASE_URL) pointing at it.

Apply-mode purge tests additionally require AUDIT_PURGE_TEST_DB_ISOLATED=1 and
abort if the target DB already contains old in-scope audit rows.
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
APPLY_ISOLATION_ENV = "AUDIT_PURGE_TEST_DB_ISOLATED"


def _load_purge_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("purge_audit_events", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["purge_audit_events"] = module
    spec.loader.exec_module(module)
    return module


def _load_data_retention_check_module() -> ModuleType:
    script_path = ROOT / "scripts" / "data_retention_check.py"
    spec = importlib.util.spec_from_file_location("data_retention_check", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _catalog_text(
    *,
    audit_retention_period: str = "90_days_target",
    api_key_retention_period: str = "90_days_target",
) -> str:
    return f"""
schema_version: data_retention_v1
retention_classes:
  - id: audit_events
    retention_period: {audit_retention_period}
  - id: api_key_audit_events
    retention_period: {api_key_retention_period}
"""


def test_default_retention_days_are_derived_from_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_purge_module()
    catalog_path = tmp_path / "data_retention.yaml"
    catalog_path.write_text(
        _catalog_text(
            audit_retention_period="45_days_target",
            api_key_retention_period="45_days_target",
        ),
        encoding="utf-8",
    )
    calls: list[dict[str, Any]] = []

    monkeypatch.setattr(module, "_CONFIG_PATH", catalog_path)
    monkeypatch.setattr(module, "run_purge", lambda **kwargs: calls.append(kwargs))

    module.main(["--db-url", "postgresql://example/db"])

    assert calls == [
        {
            "db_url": "postgresql://example/db",
            "retention_days": 45,
            "apply": False,
        }
    ]


def test_missing_catalog_fails_closed_when_retention_days_omitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _load_purge_module()
    missing_path = tmp_path / "missing.yaml"

    monkeypatch.setattr(module, "_CONFIG_PATH", missing_path)
    monkeypatch.setattr(
        module,
        "run_purge",
        lambda **_: pytest.fail("run_purge must not execute when catalog is missing"),
    )

    with pytest.raises(SystemExit) as exc_info:
        module.main(["--db-url", "postgresql://example/db"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "data_retention.yaml" in captured.err
    assert "unable to read" in captured.err


def test_malformed_catalog_fails_closed_when_retention_days_omitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _load_purge_module()
    catalog_path = tmp_path / "data_retention.yaml"
    catalog_path.write_text("retention_classes: [", encoding="utf-8")

    monkeypatch.setattr(module, "_CONFIG_PATH", catalog_path)
    monkeypatch.setattr(
        module,
        "run_purge",
        lambda **_: pytest.fail("run_purge must not execute when catalog is malformed"),
    )

    with pytest.raises(SystemExit) as exc_info:
        module.main(["--db-url", "postgresql://example/db"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "data_retention.yaml" in captured.err
    assert "malformed" in captured.err


def test_unsupported_audit_events_retention_period_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _load_purge_module()
    catalog_path = tmp_path / "data_retention.yaml"
    catalog_path.write_text(
        _catalog_text(audit_retention_period="indefinite_mvp"),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "_CONFIG_PATH", catalog_path)
    monkeypatch.setattr(
        module,
        "run_purge",
        lambda **_: pytest.fail("run_purge must not execute with unsupported retention"),
    )

    with pytest.raises(SystemExit) as exc_info:
        module.main(["--db-url", "postgresql://example/db"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "audit_events" in captured.err
    assert "unsupported retention_period" in captured.err


def test_explicit_retention_days_overrides_window_after_catalog_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_purge_module()
    catalog_path = tmp_path / "data_retention.yaml"
    catalog_path.write_text(_catalog_text(), encoding="utf-8")
    calls: list[dict[str, Any]] = []

    monkeypatch.setattr(module, "_CONFIG_PATH", catalog_path)
    monkeypatch.setattr(module, "run_purge", lambda **kwargs: calls.append(kwargs))

    module.main(
        ["--retention-days", "30", "--apply", "--db-url", "postgresql://example/db"]
    )

    assert calls == [
        {
            "db_url": "postgresql://example/db",
            "retention_days": 30,
            "apply": True,
        }
    ]


def test_explicit_retention_days_does_not_bypass_missing_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _load_purge_module()

    monkeypatch.setattr(module, "_CONFIG_PATH", tmp_path / "missing.yaml")
    monkeypatch.setattr(
        module,
        "run_purge",
        lambda **_: pytest.fail("run_purge must not execute when catalog is missing"),
    )

    with pytest.raises(SystemExit) as exc_info:
        module.main(
            ["--retention-days", "30", "--apply", "--db-url", "postgresql://example/db"]
        )

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "data_retention.yaml" in captured.err
    assert "unable to read" in captured.err


def test_data_retention_checker_rejects_obsolete_fallback_script(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_data_retention_check_module()

    def fake_read_text(path_text: str) -> str:
        if path_text == "scripts/purge_audit_events.py":
            return "_DEFAULT_RETENTION_DAYS = 90  # fallback"
        return ""

    monkeypatch.setattr(module, "read_text", fake_read_text)

    with pytest.raises(SystemExit) as exc_info:
        module.validate_purge_default_retention_semantics()

    assert "must fail closed" in str(exc_info.value)


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


def _eligible_in_scope_count(conn: Any, *, retention_days: int) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*)
            FROM audit.events
            WHERE event_type IN ('api_key_auth', 'created', 'superseded')
              AND occurred_at < %s
            """,
            (cutoff,),
        )
        return int(cur.fetchone()[0])


def _require_isolated_apply_db(conn: Any, *, retention_days: int) -> None:
    if os.getenv(APPLY_ISOLATION_ENV) != "1":
        pytest.skip(
            f"apply-mode purge tests require {APPLY_ISOLATION_ENV}=1 and an isolated DB"
        )
    eligible_count = _eligible_in_scope_count(conn, retention_days=retention_days)
    if eligible_count != 0:
        pytest.fail(
            "apply-mode purge tests require an isolated DB with zero pre-existing "
            f"eligible in-scope audit rows; found {eligible_count}"
        )


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

    def _use_temp_catalog(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        *,
        audit_retention_period: str = "90_days_target",
        api_key_retention_period: str = "90_days_target",
    ) -> None:
        catalog_path = tmp_path / "data_retention.yaml"
        catalog_path.write_text(
            _catalog_text(
                audit_retention_period=audit_retention_period,
                api_key_retention_period=api_key_retention_period,
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(self.module, "_CONFIG_PATH", catalog_path)

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
        _require_isolated_apply_db(self.conn, retention_days=90)
        old_ts = datetime.now(UTC) - timedelta(days=120)
        recent_ts = datetime.now(UTC) - timedelta(days=10)

        old_in_scope_id = self._insert(event_type="api_key_auth", occurred_at=old_ts)
        recent_in_scope_id = self._insert(event_type="created", occurred_at=recent_ts)
        old_out_of_scope_id = self._insert(event_type="unknown_future_type", occurred_at=old_ts)

        # Cleanup remains idempotent if apply already deleted the row.
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
        _require_isolated_apply_db(self.conn, retention_days=90)
        old_ts = datetime.now(UTC) - timedelta(days=120)

        created_id = self._insert(event_type="created", occurred_at=old_ts)
        superseded_id = self._insert(event_type="superseded", occurred_at=old_ts)

        # Cleanup remains idempotent if apply already deleted the rows.
        self.module.run_purge(
            db_url=self.db_url,
            retention_days=90,
            apply=True,
        )

        assert not _event_exists(self.conn, created_id)
        assert not _event_exists(self.conn, superseded_id)

    def test_cli_dry_run_uses_catalog_default_against_db(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._use_temp_catalog(
            tmp_path,
            monkeypatch,
            audit_retention_period="45_days_target",
            api_key_retention_period="45_days_target",
        )
        old_ts = datetime.now(UTC) - timedelta(days=50)
        old_in_scope_id = self._insert(event_type="api_key_auth", occurred_at=old_ts)

        self.module.main(["--db-url", self.db_url])

        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out
        assert "retention_days=45" in captured.out
        assert "api_key_auth" in captured.out
        assert _event_exists(self.conn, old_in_scope_id)

    def test_cli_apply_uses_catalog_default_against_isolated_db(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _require_isolated_apply_db(self.conn, retention_days=45)
        self._use_temp_catalog(
            tmp_path,
            monkeypatch,
            audit_retention_period="45_days_target",
            api_key_retention_period="45_days_target",
        )
        old_ts = datetime.now(UTC) - timedelta(days=50)
        old_in_scope_id = self._insert(event_type="api_key_auth", occurred_at=old_ts)

        self.module.main(["--apply", "--db-url", self.db_url])

        captured = capsys.readouterr()
        assert "APPLY" in captured.out
        assert "retention_days=45" in captured.out
        assert not _event_exists(self.conn, old_in_scope_id)
