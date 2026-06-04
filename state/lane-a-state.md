# Lane A State - Source Registry + DB Infrastructure

```text
Current milestone: Level 3 - Source Registry + Provenance Core
Target milestone: Level 3 (Source Registry + Provenance Core)
Milestone status: PASS
Last verified: 2026-06-04
Verification command(s):
- pytest backend/tests/source_registry/ -v
- mypy backend/app/source_registry backend/app/domain/source_contracts.py
- python scripts/seed_sources.py
- python scripts/seed_sources.py --json
- .\scripts\verify.ps1
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Verification result:
- 41 Lane A tests passing
- Source seed dry-run validates 8 `Must` registry rows
- Full verification passes: 186 tests; lint clean; mypy clean (76 source files)
- Source provenance layer records source datasets, dataset versions, and retrieval runs in the existing source schema
- Source freshness, authority, and license/review/usage-right metadata are visible in downstream report source manifests and review exports
Failed or blocked gates:
- None for Level 3; Level 4 area geometry DB work is next
Completion evidence:
- plans/lane-a-2026-06-03-source-registry.md
- backend/tests/source_registry/ (41 tests passing)
- backend/app/source_registry/models.py
- backend/app/source_registry/source_repo.py
- backend/app/source_registry/provenance_repo.py
- backend/app/source_registry/provenance_service.py
- backend/tests/source_registry/test_source_models.py
- backend/tests/source_registry/test_sqlalchemy_source_repo.py
- backend/tests/source_registry/test_source_seeds.py
- backend/tests/source_registry/test_source_provenance.py
- backend/tests/source_registry/test_source_provenance_models.py
- db/seeds/source_registry_seeds.py
- scripts/seed_sources.py
- docs/adr/lane-a-0001-provenance-model.md
- templates/data_source_license_review.md
- registers/data_source_registry.csv
- schemas/source_schema.json
- backend/app/reports/service.py (downstream freshness/authority visibility in report source manifests)
Next lowest-dependency task:
- TB-050: SQLAlchemy/PostGIS area model and repository
Do not work on yet:
- Live connectors
- New jurisdictions or intents
- Any Lane B/C/D files
```

## Known blockers

| Item | Status | Impact |
|---|---|---|
| MVP state/county | Undecided | Do not hard-code jurisdiction-specific logic |
| Live connector credentials | Unavailable | No live API/vendor integrations |
| Docker availability | Available | DB smoke now passes locally |

## Active plan

`plans/lane-a-2026-06-03-source-registry.md`

## Lane-specific verification commands

```bash
# Lane A unit tests only:
cd backend && PYTHONPATH=. pytest tests/source_registry/ -v

# Lane A type check only:
cd backend && mypy app/source_registry app/domain/source_contracts.py

# Full workspace gate:
.\scripts\verify.ps1

# DB smoke (when Docker is running):
docker compose up -d db
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```
