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
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _REPO_ROOT / "config" / "data_retention.yaml"
_REQUIRED_RETENTION_CLASSES = ("audit_events", "api_key_audit_events")
_RETENTION_PERIOD_PATTERN = re.compile(r"([1-9][0-9]*)_days_target")


class RetentionCatalogError(ValueError):
    """Raised when the retention catalog cannot safely drive purge defaults."""


def _load_retention_catalog(config_path: Path | None = None) -> dict[str, Any]:
    catalog_path = config_path or _CONFIG_PATH
    try:
        yaml = importlib.import_module("yaml")
    except ImportError as exc:
        raise RetentionCatalogError(
            "data_retention.yaml cannot be validated because PyYAML is not installed"
        ) from exc

    try:
        catalog_text = catalog_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RetentionCatalogError(
            f"data_retention.yaml unable to read: {catalog_path}"
        ) from exc

    try:
        catalog = yaml.safe_load(catalog_text)
    except Exception as exc:
        raise RetentionCatalogError("data_retention.yaml malformed") from exc

    if not isinstance(catalog, dict):
        raise RetentionCatalogError("data_retention.yaml must be a mapping")
    return cast(dict[str, Any], catalog)


def _retention_classes_by_id(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    classes = catalog.get("retention_classes")
    if not isinstance(classes, list):
        raise RetentionCatalogError("data_retention.yaml retention_classes must be a list")

    classes_by_id: dict[str, dict[str, Any]] = {}
    for item in classes:
        if not isinstance(item, dict):
            raise RetentionCatalogError("data_retention.yaml retention classes must be mappings")
        item = cast(dict[str, Any], item)
        class_id = item.get("id")
        if not isinstance(class_id, str) or not class_id:
            raise RetentionCatalogError("data_retention.yaml retention class id invalid")
        if class_id in classes_by_id:
            raise RetentionCatalogError(
                f"data_retention.yaml duplicate retention class: {class_id}"
            )
        classes_by_id[class_id] = item
    return classes_by_id


def _parse_retention_period_days(class_id: str, period: Any) -> int:
    if not isinstance(period, str):
        raise RetentionCatalogError(
            f"{class_id} has unsupported retention_period: {period!r}"
        )
    match = _RETENTION_PERIOD_PATTERN.fullmatch(period)
    if match is None:
        raise RetentionCatalogError(
            f"{class_id} has unsupported retention_period: {period!r}"
        )
    return int(match.group(1))


def _resolve_default_retention_days(config_path: Path | None = None) -> int:
    catalog = _load_retention_catalog(config_path)
    if catalog.get("schema_version") != "data_retention_v1":
        raise RetentionCatalogError("data_retention.yaml unexpected schema_version")

    classes_by_id = _retention_classes_by_id(catalog)
    resolved_days: set[int] = set()
    for class_id in _REQUIRED_RETENTION_CLASSES:
        retention_class = classes_by_id.get(class_id)
        if retention_class is None:
            raise RetentionCatalogError(
                f"data_retention.yaml missing retention class: {class_id}"
            )
        period = retention_class.get("retention_period")
        resolved_days.add(_parse_retention_period_days(class_id, period))

    if len(resolved_days) != 1:
        raise RetentionCatalogError(
            "data_retention.yaml audit purge retention classes must share one retention window"
        )
    return resolved_days.pop()

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
        import psycopg
    except ImportError as exc:
        print(
            "psycopg is not installed. "
            "Run: cd backend && python -m pip install -e '.[dev]'",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

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
        default=None,
        help=(
            "Delete events older than this many days "
            "(default: read from config/data_retention.yaml; fails closed if invalid)."
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
    explicit_retention_days = args.retention_days
    if explicit_retention_days is not None and explicit_retention_days < 1:
        print("--retention-days must be >= 1", file=sys.stderr)
        raise SystemExit(1)

    try:
        catalog_retention_days = _resolve_default_retention_days()
    except RetentionCatalogError as exc:
        print(f"purge_audit_events: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    retention_days = (
        explicit_retention_days
        if explicit_retention_days is not None
        else catalog_retention_days
    )
    run_purge(
        db_url=db_url,
        retention_days=retention_days,
        apply=args.apply,
    )


if __name__ == "__main__":
    main()
