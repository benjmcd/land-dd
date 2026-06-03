from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))

from db.seeds.source_registry_seeds import DEFAULT_PRIORITY, load_seed_sources  # noqa: E402
from app.domain.source_contracts import SourceContract  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or apply source registry seeds.")
    parser.add_argument("--priority", default=DEFAULT_PRIORITY)
    parser.add_argument("--json", action="store_true", help="Print seed summary as JSON.")
    parser.add_argument("--apply", action="store_true", help="Apply seeds to the configured DB.")
    args = parser.parse_args()

    seeds = load_seed_sources(priority=args.priority)
    if args.apply:
        return _apply_seeds(seeds)

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "name": source.name,
                        "organization": source.organization,
                        "source_registry_id": source.metadata["source_registry_id"],
                    }
                    for source in seeds
                ],
                indent=2,
            )
        )
    else:
        print(f"validated source seeds: {len(seeds)} priority={args.priority}")
        for source in seeds:
            print(f"- {source.metadata['source_registry_id']}: {source.name}")
    return 0


def _apply_seeds(seeds: list[SourceContract]) -> int:
    from sqlalchemy.orm import Session

    from app.db.engine import build_engine
    from app.source_registry.service import SourceService
    from app.source_registry.source_repo import SqlAlchemySourceRepository

    engine = build_engine()
    registered = 0
    skipped = 0
    with Session(engine) as session:
        repo = SqlAlchemySourceRepository(session)
        service = SourceService(repo)
        for source in seeds:
            if repo.exists_by_name_org(source.name, source.organization):
                skipped += 1
                continue
            service.register(source)
            registered += 1
        session.commit()
    print(f"source seeds applied: registered={registered} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
