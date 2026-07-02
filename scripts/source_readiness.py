from __future__ import annotations


import argparse
import json
import sys
from dataclasses import asdict
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

from app.source_registry.readiness import (  # noqa: E402
    STALE_AFTER_DAYS,
    build_readiness_records,
)

__all__ = ["STALE_AFTER_DAYS", "build_readiness_records", "main"]


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


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
