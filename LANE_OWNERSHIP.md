# LANE_OWNERSHIP.md

This file is the authoritative file-ownership map for the 4 isolated agent lanes.
A fresh agent must read this file before touching any code outside its assigned lane.

**Critical rule**: An agent MUST NOT modify a file owned by another lane.
If a cross-lane change is required, stop and record a blocker. The human coordinator resolves it.

**Archive rule**: Agents NEVER delete files. When code is superseded, retired, or replaced, move it to the `archive/` directory at the repo root. Do not use `rm`, `del`, or any destructive file removal command.

---

## Archive convention

```
archive/
  <YYYY-MM-DD>_<reason>/
    <original-relative-path>
```

Example: a retired backward-compat shim archived on 2026-06-10:

```
archive/
  2026-06-10_source-registry-lane-migration/
    backend/
      app/
        repositories/
          __init__.py
          source_repo.py
```

This preserves history, allows rollback without git, and keeps the active tree clean.
Always verify tests still pass after any archival move.

---

## Shared Interface Zone (READ-ONLY for all lane agents)

These files are shared by all lanes. No single lane owns them.
Changes require cross-lane review and an ADR update.

| File | Purpose |
|---|---|
| `backend/app/domain/enums.py` | Shared enums: AuthorityLevel, ConfidenceBand, SeverityBand, EvidenceType, AreaType, JobStatus |
| `backend/app/domain/protocols.py` | Service protocol interfaces for cross-lane validation (SourceExistsProtocol, AreaExistsProtocol) |
| `backend/app/db/engine.py` | SQLAlchemy engine factory — must stay lazily initialized |
| `backend/app/db/base.py` | Single `AppBase(DeclarativeBase)` — all ORM models must inherit this; never add a second DeclarativeBase |
| `backend/app/db/types.py` | Canonical SQLAlchemy ENUM instances — import from here; never redeclare in model files |
| `backend/app/core/config.py` | Application settings |
| `backend/app/core/__init__.py` | Package marker |
| `backend/app/db/__init__.py` | Package marker |
| `backend/app/domain/__init__.py` | Package marker |
| `backend/app/__init__.py` | Package marker |
| `backend/app/main.py` | FastAPI app factory — extend only via lane routers registered here |
| `backend/app/api/health.py` | Health/version endpoints — do not modify |
| `AGENTS.md` | Root operating contract |
| `CLAUDE.md` | Claude Code adapter |
| `CODEX_PARALLEL.md` | Parallel session coordination — human coordinator updates only |
| `README.md` | Human overview |
| `MANIFEST.md` | Routing map |
| `MILESTONE_MAP.md` | Maturity gate definitions |
| `LANE_OWNERSHIP.md` | This file — human coordinator updates only |
| `scripts/verify.sh` | Canonical verification gate (Linux/macOS) |
| `scripts/verify.ps1` | Canonical verification gate (Windows) — includes structural invariant checks |
| `scripts/validate_workspace.ps1` | Workspace structure + structural invariant checks |
| `scripts/agent-context-check.sh` | Context check |
| `schemas/*.json` | JSON schema contracts between lanes |
| `.github/`, `.agent/`, `.codex/` | CI and agent config |

**Backward-compat shims (schedule for archiving by Lane A):**

When a shim is no longer needed, **move it to `archive/`** — never delete outright.
Archive convention: `archive/<YYYY-MM-DD>_<reason>/<original-relative-path>`.
Example: `archive/2026-06-10_source-registry-lane-migration/backend/app/repositories/source_repo.py`.

| File | Note |
|---|---|
| `backend/app/repositories/source_repo.py` | Re-exports from Lane A's module. Lane A archives this. |
| `backend/app/repositories/__init__.py` | Lane A archives when shim is no longer imported anywhere. |
| `backend/app/services/source_service.py` | Re-exports from Lane A's module. Lane A archives this. |
| `backend/app/services/__init__.py` | Lane A archives when shim is no longer imported anywhere. |
| `backend/app/domain/contracts.py` | Re-exports from per-lane contract files. Lane D archives when all lanes have migrated to per-lane imports. |

---

## Connector Integration Zone

Connector work is a coordinator-owned integration zone. It is not Lane A, B, C, or D by default.

Connector implementation passes may read public lane service APIs and domain contracts, but they must not modify lane-owned implementation files unless the owning lane explicitly accepts that follow-up. Cross-lane changes still follow the cross-lane change process below.

| Path | Purpose |
|---|---|
| `backend/app/connectors/` | Fixture-first connector interfaces, adapters, and orchestration for assigned connector passes |
| `backend/tests/connectors/` | Connector contract and fixture behavior tests |
| `tests/fixtures/connectors/` | Connector-specific local fixture inputs and expected normalized outputs |
| `plans/connector-*.md` | Connector implementation plans when connector work becomes more than a one-pass handoff |
| `state/connector-state.md` | Connector integration-zone state when connector work becomes more than a one-pass handoff |

Connector run lifecycle authority:

- Source retrieval runs are the provenance authority for connector attempts.
- `source.ingest_runs` stores connector name, dataset version, status, timing, row/error/warning counts, log URI, and metrics.
- `jobs.job_queue` is reserved for future async orchestration and must reference source retrieval provenance rather than replacing it.

First assigned implementation pass:

1. Build a fixture-only flood connector pass in the connector integration zone.
2. Use local fixture JSON only; no live network, vendor credential, browser/download step, or paid API.
3. Write connector output as evidence/source-failure inputs before claims or reports.
4. Stop if the pass requires Lane A/B/C/D implementation changes not explicitly coordinated with the owning lane.

---

## Lane A — Source Registry + DB Infrastructure

**Milestone gates**: MILESTONE_MAP.md L2-*, L3-001 to L3-010

**Owned files** (Lane A agent reads and writes these):

| Path | Purpose |
|---|---|
| `backend/app/source_registry/` | All source registry module code |
| `backend/app/domain/source_contracts.py` | SourceContract and related Pydantic models |
| `backend/tests/source_registry/` | Lane A tests |
| `db/migrations/` | ALL migration files — Lane A stewards the MIGRATION_REGISTRY.md |
| `db/migrations/MIGRATION_REGISTRY.md` | Migration number allocation log |
| `db/seeds/source_*.py` | Source registry seed data |
| `docker-compose.yml` | Local DB setup (Lane A owns; Lane D reads) |
| `scripts/db_apply_migrations.sh` | Migration application script |
| `scripts/db_smoke_check.py` | DB smoke test |
| `plans/lane-a-*.md` | Lane A implementation plans |
| `state/lane-a-state.md` | Lane A current state |
| `docs/adr/lane-a-*.md` | Lane A architecture decisions |

**Readable (not modifiable)**:
- `backend/app/domain/enums.py`, `protocols.py`
- `backend/app/db/engine.py`, `backend/app/core/config.py`

**Forbidden** (do not touch):
- `backend/app/area_geometry/`
- `backend/app/evidence_ledger/`
- `backend/app/claims_engine/`
- `backend/app/reports/`
- `backend/app/api/` (except registering own router in `main.py` via plan)
- `backend/app/domain/area_contracts.py`, `evidence_contracts.py`, `claim_contracts.py`, `report_contracts.py`
- Any other lane's plans, state, tests, or ADR files

**Import invariant**: May import from `app.domain.*`, `app.db.*`, `app.core.*`, `app.source_registry.*` only.

**First-session tasks** (see `plans/lane-a-2026-06-03-source-registry.md`):
1. Archive shim directories (`repositories/`, `services/`) — move them to `archive/<date>_source-registry-lane-migration/backend/app/` once no code imports from them.
2. Add SQLAlchemy ORM model for `source.sources` table.
3. Add SQLAlchemy-backed SourceRepository.
4. Seed 3-5 sources from `registers/data_source_registry.csv`.
5. Confirm `RUN_DB_SMOKE=1 ./scripts/verify.sh` passes (once Docker is running).

---

## Lane B — Area + Geometry Domain

**Milestone gates**: MILESTONE_MAP.md L4-001 to L4-010

**Owned files**:

| Path | Purpose |
|---|---|
| `backend/app/area_geometry/` | Area and geometry module code |
| `backend/app/domain/area_contracts.py` | AreaContract Pydantic model |
| `backend/tests/area_geometry/` | Lane B tests |
| `db/seeds/area_*.py` | Area fixture seed data |
| `tests/fixtures/geometries/` | GeoJSON fixture files |
| `plans/lane-b-*.md` | Lane B implementation plans |
| `state/lane-b-state.md` | Lane B current state |
| `docs/adr/lane-b-*.md` | Lane B architecture decisions |

**Readable (not modifiable)**:
- `backend/app/domain/enums.py`, `protocols.py`
- `backend/app/db/engine.py`, `backend/app/core/config.py`
- `docker-compose.yml` (read only — changes go through Lane A)

**Forbidden**:
- `backend/app/source_registry/`
- `backend/app/evidence_ledger/`
- `backend/app/claims_engine/`
- `backend/app/reports/`
- Any Lane A/C/D plans, state, or ADR files

**Import invariant**: May import from `app.domain.*`, `app.db.*`, `app.core.*`, `app.area_geometry.*` only. NEVER imports from `app.source_registry`, `app.evidence_ledger`, `app.claims_engine`, or `app.reports`.

**First-session tasks** (see `plans/lane-b-2026-06-03-area-geometry.md`):
1. Implement `AreaService` and `InMemoryAreaRepository`.
2. Add GeoJSON polygon validation (basic: type check + coordinates present).
3. Add fixture GeoJSON geometries (valid polygon, multipolygon, invalid, empty).
4. Write tests covering all geometry fixture cases.

---

## Lane C — Evidence Ledger + Claims Engine

**Milestone gates**: MILESTONE_MAP.md L5-001 to L5-010, L6-001 to L6-010

**Owned files**:

| Path | Purpose |
|---|---|
| `backend/app/evidence_ledger/` | Evidence module code |
| `backend/app/claims_engine/` | Claims and rules engine code |
| `backend/app/domain/evidence_contracts.py` | EvidenceContract Pydantic model |
| `backend/app/domain/claim_contracts.py` | ClaimContract Pydantic model |
| `backend/tests/evidence_ledger/` | Evidence tests |
| `backend/tests/claims_engine/` | Claims/rules tests |
| `config/ruleset_homestead_mvp.yaml` | YAML ruleset definitions |
| `plans/lane-c-*.md` | Lane C implementation plans |
| `state/lane-c-state.md` | Lane C current state |
| `docs/adr/lane-c-*.md` | Lane C architecture decisions |

**Readable (not modifiable)**:
- `backend/app/domain/enums.py`, `protocols.py`
- `backend/app/db/engine.py`, `backend/app/core/config.py`

**Forbidden**:
- `backend/app/source_registry/`
- `backend/app/area_geometry/`
- `backend/app/reports/`
- Any Lane A/B/D plans, state, or ADR files

**Import invariant**: May import from `app.domain.*`, `app.db.*`, `app.core.*`, `app.evidence_ledger.*`, `app.claims_engine.*` only. NEVER imports from `app.source_registry` or `app.area_geometry`. Cross-lane validation uses `app.domain.protocols.SourceExistsProtocol` and `AreaExistsProtocol` (injected, not imported from Lane A/B).

**ORM invariant**: All new ORM models must inherit `AppBase` from `app.db.base`. All SQLAlchemy ENUM instances must be imported from `app.db.types` — never redeclared in model files.

**Current tasks** (see `plans/2026-06-03-codex-deferred-tasks.md`):
1. C-001: DONE. `claims_engine/models.py` exists and `SqlAlchemyClaimRepository` is ORM-backed.
2. C-002: Add 4 not-evaluated rule categories using sentinel SOURCE_FAILURE evidence approach. Lane C emits evidence-linked UNKNOWN claims but must not modify Lane D report files.

---

## Lane D — Reports + API + Platform Infrastructure

**Milestone gates**: MILESTONE_MAP.md L7-001 to L7-010 (setup for L8-L10)

**Owned files**:

| Path | Purpose |
|---|---|
| `backend/app/reports/` | Report service code |
| `backend/app/api/` | FastAPI routers (beyond health.py) |
| `backend/tests/reports/` | Report tests |
| `backend/tests/api/` | API contract tests |
| `Makefile` | Build/run shortcuts |
| `plans/lane-d-*.md` | Lane D implementation plans |
| `state/lane-d-state.md` | Lane D current state |
| `docs/adr/lane-d-*.md` | Lane D architecture decisions |

**Readable (not modifiable)**:
- `backend/app/domain/enums.py`, `protocols.py`
- `backend/app/db/engine.py`, `backend/app/core/config.py`
- `docker-compose.yml` (read only — changes go through Lane A)
- `backend/app/source_registry/service.py` (read Lane A's service interface)
- `backend/app/area_geometry/` (read Lane B's service interface)
- `backend/app/evidence_ledger/` (read Lane C's service interface)
- `backend/app/claims_engine/` (read Lane C's service interface)

**Forbidden** (do not modify):
- `backend/app/source_registry/`
- `backend/app/area_geometry/`
- `backend/app/evidence_ledger/`
- `backend/app/claims_engine/`
- `backend/app/domain/source_contracts.py`, `area_contracts.py`, `evidence_contracts.py`, `claim_contracts.py`
- Any Lane A/B/C plans, state, or ADR files

**Import invariant**: May import from all modules' PUBLIC service APIs, but NEVER modifies other lanes' files. Implements `SourceExistsProtocol` and `AreaExistsProtocol` using real services and injects them into Lane C's evidence service.

**Current tasks** (see `plans/2026-06-03-codex-deferred-tasks.md`):
1. D-000: Surface C-002 unsupported-category source-failure claims in report/API output after Lane C completes C-002.
2. D-001: Create `db/session.py` with `get_db_session()`; update `api/dependencies.py` and `main.py` for DB-backed services; add DB-backed API integration test. `db/session.py` may be prepared after C-001; full DB service wiring remains blocked until C-002 and D-000 complete.

---

## Cross-lane change process

If a change requires modifying a shared interface zone file (e.g., `protocols.py`, `enums.py`):
1. Stop and record a blocker in your lane's state file.
2. Describe the needed change in your lane's plan file.
3. The human coordinator decides which lane makes the change, or makes it directly.
4. Record the decision in the relevant ADR.

If `db/migrations/` needs a new migration:
1. Read `db/migrations/MIGRATION_REGISTRY.md`.
2. Claim the next available number by appending a row to the registry.
3. Name the migration file: `NNNN_<lane_prefix>_<description>.sql` (e.g., `0003_b_area_geometry.sql`).
4. Commit both the registry update and the migration file in the same change.

---

## Git branch convention

Lane branches should use the prefix: `lane-a/`, `lane-b/`, `lane-c/`, `lane-d/`.

Examples:
- `lane-a/source-orm-model`
- `lane-b/geojson-validation`
- `lane-c/evidence-service`
- `lane-d/report-run-service`

Integration to `main` happens at milestone boundaries or when a lane completes a stable slice.
