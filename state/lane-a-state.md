# Lane A State — Source Registry + DB Infrastructure

```text
Current milestone: Level 1 — Governed Repo Scaffold (Lane A scaffold complete)
Target milestone: Level 2 (DB spine) → Level 3 (source registry)
Milestone status: PARTIAL
Last verified: 2026-06-03
Verification command(s):
- pytest backend/tests/source_registry/ -v
- mypy backend/app/source_registry backend/app/domain/source_contracts.py
- python scripts/seed_sources.py
- python scripts/seed_sources.py --json
- ./scripts/verify.sh
Verification result:
- 23 Lane A tests passing
- Source seed dry-run validates 8 `Must` registry rows
- Full verification passes: 49 tests; lint clean; mypy clean (48 source files)
Failed or blocked gates:
- L2-001: Docker Desktop not running — DB cannot start
- L2-002: PostGIS extension not verified (Docker blocked)
- L2-003: Migrations not tested from zero (Docker blocked)
- L2-004: DB cannot be reset without Docker
- All L2 gates: BLOCKED (Docker)
- L3-003/L3-004: Source version and retrieval-run behavior not yet exercised beyond schema
- L3-007/L3-010: License review workflow/template still pending (TA-050)
Completion evidence:
- plans/lane-a-2026-06-03-source-registry.md
- backend/tests/source_registry/ (23 tests passing)
- archive/2026-06-03_source-registry-lane-migration/backend/app/repositories/
- archive/2026-06-03_source-registry-lane-migration/backend/app/services/
- backend/app/source_registry/models.py (SourceModel for source.sources)
- backend/tests/source_registry/test_source_models.py (4 model contract tests)
- backend/app/source_registry/source_repo.py (SqlAlchemySourceRepository)
- backend/tests/source_registry/test_sqlalchemy_source_repo.py (4 repository tests)
- db/seeds/source_registry_seeds.py (registry-backed source seed loader)
- scripts/seed_sources.py (dry-run/JSON/apply runner; apply unverified until DB is available)
- backend/tests/source_registry/test_source_seeds.py (4 seed tests)
Next lowest-dependency task:
- TA-050: License review template and provenance ADR
Do not work on yet:
- DB smoke (needs Docker/PostGIS verification)
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
