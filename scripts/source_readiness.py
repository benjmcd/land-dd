from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
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
    source_connector_inventory_entry,
)
from app.source_registry.usage_rights import (  # noqa: E402
    source_production_use_blocking_fields,
)


@dataclass(frozen=True)
class SourceReadinessRecord:
    source_registry_id: str
    name: str
    organization: str | None
    domain: str
    mvp_priority: str
    source_type: str | None
    review_status: str
    license_status: str
    production_use_allowed: bool
    connector_implemented: bool
    connector_surfaces: tuple[str, ...]
    connector_ready: bool
    blocked_fields: tuple[str, ...]


def build_readiness_records(
    sources: list[SourceContract],
) -> list[SourceReadinessRecord]:
    return [_source_to_readiness(source) for source in sources]


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
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero when no connector-ready source is present.",
    )
    args = parser.parse_args()

    sources = load_registry_sources(args.register, priority=args.priority)
    records = build_readiness_records(sources)
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


def _source_to_readiness(source: SourceContract) -> SourceReadinessRecord:
    source_registry_id = str(source.metadata["source_registry_id"])
    usage_blocked_fields = source_production_use_blocking_fields(source)
    connector_inventory = source_connector_inventory_entry(source_registry_id)
    connector_surfaces = (
        () if connector_inventory is None else connector_inventory.surfaces
    )
    connector_implemented = connector_inventory is not None
    blocked_fields = (
        usage_blocked_fields
        if connector_implemented
        else (*usage_blocked_fields, "connector_implemented")
    )
    return SourceReadinessRecord(
        source_registry_id=source_registry_id,
        name=source.name,
        organization=source.organization,
        domain=source.domain,
        mvp_priority=str(source.metadata["mvp_priority"]),
        source_type=source.source_type,
        review_status=source.review_status,
        license_status=source.license_status,
        production_use_allowed=usage_blocked_fields == (),
        connector_implemented=connector_implemented,
        connector_surfaces=connector_surfaces,
        connector_ready=blocked_fields == (),
        blocked_fields=blocked_fields,
    )


if __name__ == "__main__":
    raise SystemExit(main())
