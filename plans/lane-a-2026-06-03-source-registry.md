# Lane A — Source Registry + DB Infrastructure

## Goal

Complete MILESTONE_MAP.md Levels 2-3:
- Postgres/PostGIS migrations apply cleanly from scratch.
- Source registry is seeded, with license/provenance metadata, and backed by tests.
- DB smoke passes when Docker is available.

## Non-goals

- No area, evidence, claim, or report work.
- No live connector integration.
- No paid/commercial data.
- No global coverage or jurisdiction decisions.

## Current state

- DB migration `db/migrations/0001_initial_spine.sql` exists with all core tables.
- `SourceContract` Pydantic model in `backend/app/domain/source_contracts.py`.
- `InMemorySourceRepository` + `SourceService` in `backend/app/source_registry/`.
- 28 passing tests in `backend/tests/source_registry/`.
- Backward-compat shims in `app/repositories/` and `app/services/` were archived under `archive/2026-06-03_source-registry-lane-migration/` (TA-010 complete).
- `SourceModel` in `backend/app/source_registry/models.py` maps the `source.sources` table (TA-020 complete).
- `SqlAlchemySourceRepository` in `backend/app/source_registry/source_repo.py` implements the source repository protocol for SQLAlchemy sessions (TA-030 complete).
- `db/seeds/source_registry_seeds.py` parses `registers/data_source_registry.csv` and validates the 8 `Must` MVP source rows as `SourceContract` objects (TA-040 complete).
- `scripts/seed_sources.py` supports dry-run and JSON seed review; DB apply and smoke are verified via the Windows PowerShell wrapper (TA-040 complete).
- `docs/adr/lane-a-0001-provenance-model.md` defines fail-closed source provenance and license gates (TA-050 complete).
- `templates/data_source_license_review.md` is the canonical source license review template; it was strengthened instead of creating a near-duplicate `source_license_review.md` (TA-050 complete).
- `registers/data_source_registry.csv`, `schemas/source_schema.json`, and the seed loader now carry explicit license/review/freshness fields (TA-050 complete).
- `SourceService` implements source existence and fail-closed production-use checks for `SourceExistsProtocol` wiring (TA-050 complete).
- DB smoke now passes via the Windows PowerShell verification wrapper.

## Proposed design

Build bottom-up: archive shims → SQLAlchemy ORM model → SQLAlchemy-backed repository → source seeds → DB smoke.

## Bottom-up sequence

### TA-010: Archive backward-compat shims
1. Confirm no file outside `app/repositories/` imports from `app.repositories.source_repo` or `app.services.source_service` (run a grep).
2. Move `backend/app/repositories/` to `archive/<today>_source-registry-lane-migration/backend/app/repositories/`.
3. Move `backend/app/services/` to `archive/<today>_source-registry-lane-migration/backend/app/services/`.
4. Confirm `pytest backend/tests/source_registry/ -v` still passes.
5. Confirm `.\scripts\verify.ps1` still passes.

### TA-020: SQLAlchemy ORM model for source.sources
1. Create `backend/app/source_registry/models.py` with `SourceModel` (SQLAlchemy Base + mapped_column).
2. Match `source.sources` table columns from `db/migrations/0001_initial_spine.sql`.
3. Import test: confirm `from app.source_registry.models import SourceModel` does not crash.
4. Mypy: clean.

### TA-030: SQLAlchemy-backed SourceRepository
1. Add `SqlAlchemySourceRepository` to `backend/app/source_registry/source_repo.py`.
2. Implement `add`, `get`, `list_all`, `exists_by_name_org` using SQLAlchemy Session.
3. Keep `InMemorySourceRepository` for fixture tests.
4. Write tests using the in-memory repository (no live DB needed for unit tests).

### TA-040: Source seeds
1. Parse `registers/data_source_registry.csv` rows marked `MVP Priority = Must`.
2. Create `db/seeds/source_registry_seeds.py` that inserts 5+ sources.
3. Add a `scripts/seed_sources.py` runner.
4. Write a test that instantiates seed sources as `SourceContract` objects (no DB required).

### TA-050: License review template
1. Create `docs/adr/lane-a-0001-provenance-model.md` (ADR for source/provenance decisions).
2. Strengthen the existing canonical `templates/data_source_license_review.md` with required license review fields instead of creating a duplicate template.
3. Add explicit governance fields to the source register/schema/seed path: license status, redistribution status, freshness class, last checked, review owner, review status, and fail-closed usage statuses.

### TA-060: DB smoke (COMPLETE)
1. Run `docker compose up -d db`.
2. Run `.\scripts\db_apply_migrations.ps1`.
3. Run `python scripts/db_smoke_check.py`.
4. Record result in `state/VALIDATION_LOG.md`.
5. If passes: update `state/lane-a-state.md` milestone to L2/L3 candidate.
Status: COMPLETE. DB smoke passes locally, and the PowerShell verification wrapper now owns the local `psql` shim PATH prepend.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/source_registry/models.py` | New: SQLAlchemy ORM model |
| `backend/app/source_registry/source_repo.py` | Add SQLAlchemy-backed repository |
| `db/seeds/source_registry_seeds.py` | New: seed data |
| `scripts/seed_sources.py` | New: seed runner |
| `docs/adr/lane-a-0001-provenance-model.md` | New: ADR |
| `templates/data_source_license_review.md` | Strengthen canonical license review template |
| `registers/data_source_registry.csv` | Add explicit governance fields |
| `schemas/source_schema.json` | Add source-governance fields |
| `state/lane-a-state.md` | Update after each task |
| `state/VALIDATION_LOG.md` | DB smoke results |

## Tests / verification

```bash
pytest backend/tests/source_registry/ -v
mypy backend/app/source_registry backend/app/domain/source_contracts.py
.\scripts\verify.ps1
# When Docker available:
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

## Risks and blockers

| Blocker | Status | Impact |
|---|---|---|
| Docker Desktop | Available | TA-060 complete; DB smoke verified |
| MVP state/county not decided | Undecided | Do not hard-code jurisdiction logic |
| psycopg[binary] | Installed | Should connect once Docker is running |

## Decision log

- 2026-06-03: Lane A owns source registry and DB infrastructure.
- 2026-06-03: `SourceContract` expanded to 17 fields matching DB schema + L3 requirements.
- 2026-06-03: Backward-compat shims in `repositories/` and `services/` are Lane A's to archive (not delete) once no code imports from them.
- 2026-06-03: `docker-compose.yml` assigned to Lane A ownership.

## Progress log

- 2026-06-03: Lane scaffold created. `InMemorySourceRepository` + `SourceService` in `source_registry/`. 11 tests passing.
- 2026-06-03: TA-010 complete. Archived `backend/app/repositories/` and `backend/app/services/` to `archive/2026-06-03_source-registry-lane-migration/backend/app/` after confirming no active imports.
- 2026-06-03: TA-020 complete. Added `SourceModel` for `source.sources` with 4 model contract tests. Full verification: 26 tests, ruff clean, mypy clean (42 source files); DB smoke skipped.
- 2026-06-03: TA-030 complete. Added `SqlAlchemySourceRepository` with non-DB session-bound tests for add/get/list/exists behavior. Full verification: 30 tests, ruff clean, mypy clean (43 source files); DB smoke skipped.
- 2026-06-03: TA-040 complete. Added registry-backed source seed loader, seed runner, seed tests, and source metadata mapping. Lane A tests: 23 passing. Full verification: 49 tests, ruff clean, mypy clean (48 source files); DB smoke skipped.
- 2026-06-03: TA-050 complete. Added source provenance/license ADR, strengthened the canonical data-source license review template, wired explicit governance fields through the register/schema/seed path, and added fail-closed SourceService production-use checks. Lane A tests: 28 passing. Full verification at TA-050: 64 tests, ruff clean, mypy clean (51 source files); DB smoke skipped.
- 2026-06-03: TA-060 complete. DB smoke passes locally using the PowerShell verification wrapper, which prepends `local_artifacts` so the `psql` shim is available on Windows. Full verification: 179 tests, ruff clean, mypy clean (76 source files); DB smoke passes.
- 2026-06-04: Source production-use gating now checks review, license, commercial, redistribution, cache, export, raw-data, and AI-use rights. Full verification: 186 tests, ruff clean, mypy clean (76 source files); strengthened DB smoke passes.
- 2026-06-04: CON-007 coordinated Lane A public provenance follow-up complete. `SourceProvenanceService.record_retrieval_run_contract(...)` preserves supplied `SourceRetrievalRunContract.ingest_run_id`, `retrieval_run_exists(...)` exposes public duplicate checks, and DB-enabled source provenance tests verify round-trip identity preservation. Full DB-enabled PowerShell verification: 289 tests, lint clean, mypy clean (104 source files), migrations/seeds apply, DB smoke passes.
