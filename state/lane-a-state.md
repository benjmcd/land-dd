# Lane A State — Source Registry + DB Infrastructure

```text
Current milestone: Level 1 — Governed Repo Scaffold (Lane A scaffold complete)
Target milestone: Level 2 (DB spine) → Level 3 (source registry)
Milestone status: PARTIAL
Last verified: 2026-06-03
Verification command(s):
- pytest backend/tests/source_registry/ -v
- mypy backend/app/source_registry backend/app/domain/source_contracts.py
- ./scripts/verify.sh
Verification result:
- 11 Lane A tests passing; lint clean; mypy clean (40 source files)
Failed or blocked gates:
- L2-001: Docker Desktop not running — DB cannot start
- L2-002: PostGIS extension not verified (Docker blocked)
- L2-003: Migrations not tested from zero (Docker blocked)
- L2-004: DB cannot be reset without Docker
- All L2 gates: BLOCKED (Docker)
Completion evidence:
- plans/lane-a-2026-06-03-source-registry.md
- backend/tests/source_registry/ (11 tests passing)
Next lowest-dependency task:
- TA-010: Clean up backward-compat shims in app/repositories/ and app/services/
Do not work on yet:
- SQLAlchemy ORM model (needs DB schema confirmed — proceed with in-memory first)
- Paid/commercial source connectors
- Any Lane B/C/D files
```

## Known blockers

| Item | Status | Impact |
|---|---|---|
| Docker Desktop not running | Blocked | All L2 DB-requiring gates blocked |
| MVP state/county | Undecided | Do not hard-code jurisdiction-specific logic |

## Active plan

`plans/lane-a-2026-06-03-source-registry.md`

## Lane-specific verification commands

```bash
# Lane A unit tests only:
cd backend && PYTHONPATH=. pytest tests/source_registry/ -v

# Lane A type check only:
cd backend && mypy app/source_registry app/domain/source_contracts.py

# Full workspace gate:
./scripts/verify.sh

# DB smoke (when Docker is running):
docker compose up -d db
RUN_DB_SMOKE=1 ./scripts/verify.sh
```
