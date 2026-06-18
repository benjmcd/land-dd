from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))

from db.seeds.source_registry_seeds import (  # type: ignore[import-not-found]  # noqa: E402
    DEFAULT_REGISTER_PATH,
    load_registry_sources,
)

from app.domain.source_contracts import SourceContract  # noqa: E402
from app.source_registry.connector_inventory import (  # noqa: E402
    source_connector_inventory_entries,
)
from app.source_registry.usage_rights import (  # noqa: E402
    source_production_use_blocking_fields,
)

STALE_AFTER_DAYS = 90


@dataclass(frozen=True)
class SourceReadinessRecord:
    source_registry_id: str
    name: str
    organization: str | None
    domain: str
    mvp_priority: str
    source_type: str | None
    review_status: str
    freshness_class: str
    last_checked_at: str | None
    last_checked_age_days: int | None
    stale_after_days: int
    review_owner: str | None
    review_freshness_allowed: bool
    review_freshness_blocked_fields: tuple[str, ...]
    license_status: str
    production_use_allowed: bool
    connector_implemented: bool
    connector_surfaces: tuple[str, ...]
    connector_names: tuple[str, ...]
    connector_scope_notes: tuple[str, ...]
    connector_ready: bool
    blocked_fields: tuple[str, ...]


def build_readiness_records(
    sources: list[SourceContract],
    *,
    as_of: date | None = None,
) -> list[SourceReadinessRecord]:
    effective_as_of = as_of if as_of is not None else date.today()
    return [_source_to_readiness(source, as_of=effective_as_of) for source in sources]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report source registry readiness for production connector use."
    )
    parser.add_argument(
        "--register",
        type=Path,
        default=DEFAULT_REGISTER_PATH,
        help="Path to data_source_registry.csv.",
    )
    parser.add_argument(
        "--priority",
        default=None,
        help="Optional MVP priority filter, for example Must or Should.",
    )
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="As-of date for review freshness checks in YYYY-MM-DD form.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero when no connector-ready source is present.",
    )
    args = parser.parse_args()

    sources = load_registry_sources(args.register, priority=args.priority)
    records = build_readiness_records(sources, as_of=args.as_of)
    ready_count = sum(1 for record in records if record.connector_ready)
    blocked_count = len(records) - ready_count

    if args.json:
        print(
            json.dumps(
                {
                    "schema_version": "source_readiness_v1",
                    "priority": args.priority,
                    "source_count": len(records),
                    "ready_count": ready_count,
                    "blocked_count": blocked_count,
                    "sources": [asdict(record) for record in records],
                },
                indent=2,
            )
        )
    else:
        priority_label = args.priority if args.priority is not None else "all"
        print(
            "source readiness: "
            f"priority={priority_label} sources={len(records)} "
            f"ready={ready_count} blocked={blocked_count}"
        )
        for record in records:
            if record.connector_ready:
                print(f"- {record.source_registry_id}: ready {record.name}")
                continue
            print(
                f"- {record.source_registry_id}: blocked {record.name} "
                f"fields={','.join(record.blocked_fields)}"
            )

    if args.require_ready and ready_count == 0:
        return 2
    return 0


def _source_to_readiness(
    source: SourceContract,
    *,
    as_of: date,
) -> SourceReadinessRecord:
    source_registry_id = str(source.metadata["source_registry_id"])
    mvp_priority = str(source.metadata["mvp_priority"])
    usage_blocked_fields = source_production_use_blocking_fields(source)
    connector_inventory_entries = source_connector_inventory_entries(source_registry_id)
    connector_surfaces = _dedupe_ordered(
        surface
        for connector_inventory in connector_inventory_entries
        for surface in connector_inventory.surfaces
    )
    connector_names = tuple(
        connector_inventory.connector_name
        for connector_inventory in connector_inventory_entries
    )
    connector_scope_notes = tuple(
        connector_inventory.scope_note
        for connector_inventory in connector_inventory_entries
        if connector_inventory.scope_note
    )
    connector_implemented = bool(connector_inventory_entries)
    review_freshness = _review_freshness_blocking_fields(
        source,
        mvp_priority=mvp_priority,
        production_use_allowed=usage_blocked_fields == (),
        connector_implemented=connector_implemented,
        as_of=as_of,
    )
    review_freshness_blocked_fields = review_freshness.blocked_fields
    blocked_fields = (
        (*usage_blocked_fields, *review_freshness_blocked_fields)
        if connector_implemented
        else (*usage_blocked_fields, "connector_implemented", *review_freshness_blocked_fields)
    )
    return SourceReadinessRecord(
        source_registry_id=source_registry_id,
        name=source.name,
        organization=source.organization,
        domain=source.domain,
        mvp_priority=mvp_priority,
        source_type=source.source_type,
        review_status=source.review_status,
        freshness_class=source.freshness_class,
        last_checked_at=source.last_checked_at,
        last_checked_age_days=review_freshness.last_checked_age_days,
        stale_after_days=STALE_AFTER_DAYS,
        review_owner=source.review_owner,
        review_freshness_allowed=review_freshness_blocked_fields == (),
        review_freshness_blocked_fields=review_freshness_blocked_fields,
        license_status=source.license_status,
        production_use_allowed=usage_blocked_fields == (),
        connector_implemented=connector_implemented,
        connector_surfaces=connector_surfaces,
        connector_names=connector_names,
        connector_scope_notes=connector_scope_notes,
        connector_ready=blocked_fields == (),
        blocked_fields=blocked_fields,
    )


@dataclass(frozen=True)
class ReviewFreshnessResult:
    blocked_fields: tuple[str, ...]
    last_checked_age_days: int | None


def _review_freshness_blocking_fields(
    source: SourceContract,
    *,
    mvp_priority: str,
    production_use_allowed: bool,
    connector_implemented: bool,
    as_of: date,
) -> ReviewFreshnessResult:
    if mvp_priority != "Must":
        return ReviewFreshnessResult((), None)

    freshness_class = source.freshness_class.strip().lower()
    candidate_ready_without_freshness = production_use_allowed and connector_implemented
    blocked_fields: list[str] = []
    last_checked_age_days: int | None = None

    if freshness_class == "current-effective":
        parsed_last_checked = _parse_last_checked_at(source.last_checked_at)
        if parsed_last_checked is None:
            blocked_fields.append("last_checked_at")
        elif parsed_last_checked > as_of:
            blocked_fields.append("last_checked_at")
        else:
            last_checked_age_days = (as_of - parsed_last_checked).days
            if last_checked_age_days > STALE_AFTER_DAYS:
                blocked_fields.append("last_checked_at")

        if not _has_real_review_owner(source.review_owner):
            blocked_fields.append("review_owner")
    elif candidate_ready_without_freshness:
        blocked_fields.append("freshness_class")

    return ReviewFreshnessResult(tuple(blocked_fields), last_checked_age_days)


def _parse_last_checked_at(last_checked_at: str | None) -> date | None:
    if last_checked_at is None or not last_checked_at.strip():
        return None
    try:
        return date.fromisoformat(last_checked_at)
    except ValueError:
        return None


def _has_real_review_owner(review_owner: str | None) -> bool:
    if review_owner is None:
        return False
    normalized = review_owner.strip().lower()
    return bool(normalized) and normalized != "unassigned"


def _dedupe_ordered(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


if __name__ == "__main__":
    raise SystemExit(main())
