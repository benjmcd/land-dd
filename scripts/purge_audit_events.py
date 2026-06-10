"""Purge old audit events from audit.events.

Retention classes covered (config/data_retention.yaml):
  - audit_events          — event_type IN ('created', 'superseded'), target 90 days
  - api_key_audit_events  — event_type = 'api_key_auth',             target 90 days

Event types NOT in scope (excluded from this purge):
  - Any event_type not listed above. Future event types with different retention
    policies must not be silently deleted by this script.

Usage
-----
  Dry run (default — prints what WOULD be deleted, no writes):
      python scripts/purge_audit_events.py

  Apply (deletes rows):
      python scripts/purge_audit_events.py --apply

  Custom retention window:
      python scripts/purge_audit_events.py --retention-days 30 --apply

Environment
-----------
  DATABASE_URL_SYNC   Postgres connection URL (sync driver). Falls back to
                      the DATABASE_URL env var used by the application, then
                      to the local-dev default.

Exit codes
----------
  0  success (dry-run or apply)
  1  error (connection failure, invalid args, etc.)
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve default retention_days from config/data_retention.yaml
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _REPO_ROOT / "config" / "data_retention.yaml"
_DEFAULT_RETENTION_DAYS = 90  # fallback if YAML is absent or unparseable

try:
    yaml = importlib.import_module("yaml")
    _catalog = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8"))
    for _cls in _catalog.get("retention_classes", []):
        if _cls.get("id") == "audit_events":
            period = _cls.get("retention_period", "")
            if isinstance(period, str) and period.startswith("90"):
                _DEFAULT_RETENTION_DAYS = 90
            break
except Exception:
    pass  # keep the hard-coded default

# ---------------------------------------------------------------------------
# In-scope event types (explicit allowlist — fail closed)
# ---------------------------------------------------------------------------

# audit_events class: evidence lifecycle events written by
# SqlAlchemyEvidenceAuditLog in app/evidence_ledger/audit_log.py
_EVIDENCE_EVENT_TYPES = frozenset({"created", "superseded"})

# api_key_audit_events class: API-key auth events written by
# SqlAlchemyApiKeyAuthAuditLog in app/api/auth_audit.py
_API_KEY_EVENT_TYPES = frozenset({"api_key_auth"})

# Union of all in-scope event types
IN_SCOPE_EVENT_TYPES: frozenset[str] = _EVIDENCE_EVENT_TYPES | _API_KEY_EVENT_TYPES


# ---------------------------------------------------------------------------
# DB connection helpers — follow db_smoke_check.py conventions
# ---------------------------------------------------------------------------

def _resolve_db_url() -> str:
    """Return the sync Postgres URL from the environment, with fallback."""
    # The application uses DATABASE_URL (psycopg async driver prefix) for
    # runtime, but db_smoke_check.py reads DATABASE_URL_SYNC for sync psycopg.
    # This script reads the same env var hierarchy.
    url = os.environ.get(
        "DATABASE_URL_SYNC",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://land:land@localhost:5432/land_diligence",
        ),
    )
    # Strip async driver prefix so psycopg3 (sync) / psycopg2 can accept it
    url = url.replace("postgresql+psycopg://", "postgresql://")
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _event_type_tuple(event_types: frozenset[str]) -> tuple[str, ...]:
    return tuple(sorted(event_types))


def run_purge(
    *,
    db_url: str,
    retention_days: int,
    apply: bool,
) -> None:
    """Execute dry-run or apply purge against audit.events."""
    try:
        import psycopg  # type: ignore[import-untyped]
    except ImportError:
        print(
            "psycopg is not installed. "
            "Run: cd backend && python -m pip install -e '.[dev]'",
            file=sys.stderr,
        )
        raise SystemExit(1)

    cutoff: datetime = datetime.now(UTC) - timedelta(days=retention_days)
    event_types = _event_type_tuple(IN_SCOPE_EVENT_TYPES)

    # Build a parameterised IN-list placeholder compatible with psycopg3
    placeholders = ", ".join("%s" for _ in event_types)

    count_sql = f"""
        SELECT event_type, count(*) AS n
        FROM audit.events
        WHERE event_type IN ({placeholders})
          AND occurred_at < %s
        GROUP BY event_type
        ORDER BY event_type
    """

    delete_sql = f"""
        DELETE FROM audit.events
        WHERE event_type IN ({placeholders})
          AND occurred_at < %s
    """

    mode = "APPLY" if apply else "DRY-RUN"
    print(
        f"purge_audit_events: {mode}  "
        f"retention_days={retention_days}  "
        f"cutoff={cutoff.date().isoformat()}"
    )
    print(f"  in-scope event types: {sorted(IN_SCOPE_EVENT_TYPES)}")

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(count_sql, (*event_types, cutoff))
            rows = cur.fetchall()

        total = 0
        if rows:
            print("  rows eligible for deletion:")
            for event_type, n in rows:
                print(f"    {event_type}: {n}")
                total += n
        else:
            print("  no eligible rows found")

        print(f"  total eligible: {total}")

        if apply and total > 0:
            with conn.cursor() as cur:
                cur.execute(delete_sql, (*event_types, cutoff))
                deleted = cur.rowcount
            conn.commit()
            print(f"  deleted: {deleted} rows")
        elif apply and total == 0:
            print("  nothing to delete")
        else:
            print("  dry-run: no rows deleted (pass --apply to delete)")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Purge old in-scope audit events from audit.events. "
            "Dry-run by default; pass --apply to delete."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Delete rows (default: dry-run only, no writes).",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=_DEFAULT_RETENTION_DAYS,
        help=(
            f"Delete events older than this many days "
            f"(default: {_DEFAULT_RETENTION_DAYS}, from config/data_retention.yaml)."
        ),
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help=(
            "Postgres connection URL. Defaults to DATABASE_URL_SYNC / DATABASE_URL "
            "env vars, then local-dev default."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    db_url = args.db_url or _resolve_db_url()
    if args.retention_days < 1:
        print("--retention-days must be >= 1", file=sys.stderr)
        raise SystemExit(1)
    run_purge(
        db_url=db_url,
        retention_days=args.retention_days,
        apply=args.apply,
    )


if __name__ == "__main__":
    main()
