# Lane A State - Source Registry + DB Infrastructure

```text
Current milestone: Level 3 - Source Registry + Provenance Core
Target milestone: Level 3 (Source Registry + Provenance Core)
Milestone status: PASS
Last verified: 2026-06-04
Verification command(s):
- py -3.12 -m pytest -q tests/source_registry/test_source_schema_contract.py
- py -3.12 -m pytest -q tests/source_registry/test_source_provenance_schema_contract.py
- py -3.12 -m pytest -q tests/source_registry
- ruff check app/source_registry app/domain/source_contracts.py tests/source_registry
- mypy app/source_registry app/domain/source_contracts.py tests/source_registry
- pytest backend/tests/source_registry/ -v
- mypy backend/app/source_registry backend/app/domain/source_contracts.py
- python scripts/seed_sources.py
- python scripts/seed_sources.py --json
- .\scripts\verify.ps1
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Verification result:
- Source schema-contract parity test: 4 passed
- Source provenance-family schema-contract parity test: 6 passed
- Lane A source-registry collection: 54 tests; default local run has one DB-gated skip
- Source seed dry-run validates 8 `Must` registry rows
- Full DB-enabled verification passes after TA-080: 350 backend tests pass; lint clean; mypy clean (121 source files); migrations/seeds apply; DB smoke passes
- Source provenance layer records source datasets, dataset versions, and retrieval runs in the existing source schema
- Public source provenance service can preserve supplied connector retrieval-run identity through `record_retrieval_run_contract(...)`
- Canonical `schemas/source_schema.json` is aligned to serialized `SourceContract` and explicitly excludes dataset/version/retrieval-run family fields pending separate schema-family work
- `schemas/source_provenance_schema.json` is aligned to serialized `SourceDatasetContract`, `SourceDatasetVersionContract`, and `SourceRetrievalRunContract`; it tracks retrieval status enum values and non-negative retrieval counts without adding runtime validation or connector behavior
- Source freshness, authority, and license/review/usage-right metadata are visible in downstream report source manifests and review exports
Failed or blocked gates:
- None for Level 3; Level 4 area geometry DB work is next
Completion evidence:
- plans/lane-a-2026-06-03-source-registry.md
- backend/tests/source_registry/ (48 tests collected)
- backend/app/source_registry/models.py
- backend/app/source_registry/source_repo.py
- backend/app/source_registry/provenance_repo.py
- backend/app/source_registry/provenance_service.py
- backend/tests/source_registry/test_source_models.py
- backend/tests/source_registry/test_sqlalchemy_source_repo.py
- backend/tests/source_registry/test_source_seeds.py
- backend/tests/source_registry/test_source_provenance.py
- backend/tests/source_registry/test_source_provenance_models.py
- backend/tests/source_registry/test_source_schema_contract.py
- backend/tests/source_registry/test_source_provenance_schema_contract.py
- backend/app/connectors/public_wiring.py (connector public-service adapter uses Lane A public service without repository imports)
- db/seeds/source_registry_seeds.py
- scripts/seed_sources.py
- docs/adr/lane-a-0001-provenance-model.md
- templates/data_source_license_review.md
- registers/data_source_registry.csv
- schemas/source_schema.json
- schemas/source_provenance_schema.json
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
| Connector retrieval-run identity | Public service supported | `record_retrieval_run_contract(...)` preserves supplied `ingest_run_id` |
| Source provenance family schemas | Resolved for serialized contracts | `schemas/source_provenance_schema.json` covers dataset/version/retrieval-run contracts; runtime validation and downstream linkage remain separate future work |

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
