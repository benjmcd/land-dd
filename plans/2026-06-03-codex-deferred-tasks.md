# Deferred Codex Tasks — 2026-06-03

These are the tasks deferred from the pre-Codex hardening session (ralplan A-minus plan).
Each task is scoped, has acceptance criteria, and builds on the structural fixes already made.
Assign one task per Codex lane agent session. Do not start a higher-numbered task
until the prior one is complete and verified.

---

## Task C-001: Claims ORM models (Phase 3)

**Priority:** HIGH  
**Prerequisite:** `backend/app/db/base.py` and `backend/app/db/types.py` must exist (DONE — commit 99cde91)

**Context:**  
`SqlAlchemyClaimRepository` (in `backend/app/claims_engine/claim_repo.py`) uses raw SQL
`text()` for all operations against `claims.claims`, `claims.claim_evidence`, and
`claims.verification_tasks`. This bypasses type safety. All other SQLAlchemy repositories
in this project use ORM models.

**Work:**

1. Create `backend/app/claims_engine/models.py` with ORM models inheriting from `AppBase`:
   - `ClaimModel` mapping `claims.claims`
   - `ClaimEvidenceLinkModel` mapping `claims.claim_evidence`
   - `VerificationTaskModel` mapping `claims.verification_tasks`

   Import `AppBase` from `app.db.base`. Import `confidence_band_enum` and add a new
   `severity_band_enum` to `app/db/types.py` (matching `claims.severity_band` in SQL).
   Use `create_type=False` for all ENUM instances (DDL is managed by migrations).

   The `claims.claims` table columns (from `db/migrations/0001_initial_spine.sql`):
   ```sql
   claim_id uuid PRIMARY KEY
   area_id uuid NOT NULL REFERENCES core.areas(area_id)
   claim_code text NOT NULL
   domain text NOT NULL
   assertion text NOT NULL
   severity claims.severity_band NOT NULL
   confidence evidence.confidence_band NOT NULL
   is_negative boolean NOT NULL DEFAULT false
   is_unknown boolean NOT NULL DEFAULT false
   needs_review boolean NOT NULL DEFAULT false
   user_safe_language text
   verification_required boolean NOT NULL DEFAULT false
   verification_task text
   created_at timestamptz NOT NULL DEFAULT now()
   metadata jsonb NOT NULL DEFAULT '{}'
   ```

   `claims.claim_evidence`:
   ```sql
   claim_id uuid NOT NULL REFERENCES claims.claims(claim_id)
   evidence_id uuid NOT NULL REFERENCES evidence.observations(evidence_id)
   evidence_order int NOT NULL DEFAULT 0
   PRIMARY KEY (claim_id, evidence_id)
   ```

   `claims.verification_tasks`:
   ```sql
   verification_task_id uuid PRIMARY KEY DEFAULT gen_random_uuid()
   claim_id uuid NOT NULL REFERENCES claims.claims(claim_id)
   task_description text NOT NULL
   ```

2. Refactor `SqlAlchemyClaimRepository` to use the new ORM models:
   - `add()`: use `session.add(ClaimModel(...))` + `session.add_all([ClaimEvidenceLinkModel(...)])` + flush
   - `get()`: use `session.get(ClaimModel, claim_id)` + query `ClaimEvidenceLinkModel`
   - `list_by_area()`: use `select(ClaimModel).where(...)`
   - `list_all()`: use `select(ClaimModel)`
   - All queries must use SQLAlchemy 2.x `select()` style (not `.query()`)

3. Add targeted type annotations and ensure `mypy` passes.

**Acceptance criteria:**
- `grep -rn "\.query(" backend/app/` returns 0 matches
- `grep -rn "class.*DeclarativeBase" backend/app/` returns exactly 1 match (in `db/base.py`)
- `grep -rn "severity_band_enum\s*=" backend/app/` returns exactly 1 match (in `db/types.py`)
- Existing 4 `test_sqlalchemy_claim_repo.py` DB tests still pass
- `ruff check app/claims_engine/` passes
- `mypy app/claims_engine/` passes
- Full `RUN_DB_SMOKE=1 py -3.12 -m pytest` passes (≥235 tests)

---

## Task C-002: Level 6 completion — not-evaluated rule categories (Phase 6)

**Priority:** HIGH  
**Prerequisite:** Task C-001 complete (so any new claim types use ORM models)

**Context:**  
`rule_engine.py` implements 6 rule domains: flood, access, zoning, water, wetlands, slope.
Four more categories are listed in MILESTONE_MAP as required for Level 6 PASS:
soil/septic, environmental hazards, market context, resource context.

Per project non-negotiables: no report may assert final buildability, water rights, or
market value. These categories cannot be implemented without real data. The correct
approach is explicit `NOT_EVALUATED` claim generation so reports accurately disclose scope.

**Work:**

1. Define 4 new constants in `rule_engine.py`:
   ```python
   SOIL_SEPTIC_CONDITION = "soil_septic_unsupported"
   ENV_HAZARD_CONDITION = "env_hazard_unsupported"
   RESOURCE_CONTEXT_CONDITION = "resource_context_unsupported"
   MARKET_CONTEXT_CONDITION = "market_context_out_of_scope"
   ```

2. Add 4 new `hard_gates` entries to `config/ruleset_homestead_mvp.yaml` with:
   - `claim_code`: e.g. `SOIL_NOT_EVALUATED`, `ENV_HAZ_NOT_EVALUATED`, `RESOURCE_NOT_EVALUATED`, `MARKET_OUT_OF_SCOPE`
   - `severity_on_fail: "informational"` for soil/env/resource; market context is `"informational"` with explicit caveat
   - `condition`: the constant names above
   - `verification_task`: what the user should do manually

3. Add evaluation methods to `RuleEngine.evaluate()` for these 4 categories. Each should
   unconditionally emit a claim with `is_unknown=True` (or a new `is_not_evaluated=True`
   if you add that flag to the claim contract) with user-safe language that explicitly
   states: "This category was not evaluated in this screening run."

   **Critical constraint (AGENTS.md):** market context claims MUST NOT assert valuation,
   pricing, neighborhood desirability, or investment advice. Use language like:
   "Market context was not evaluated. No valuation, pricing, or investment guidance
   is provided by this screening tool."

4. Add in-memory fixture tests for all 4 new not-evaluated claim outputs:
   - Deterministic claim IDs
   - `is_unknown=True` / `is_not_evaluated=True`
   - User-safe language validation
   - Source-manifest correctly excludes market context

**Acceptance criteria:**
- Level 6 gates L6-001 through L6-010 must now all be PASS (not PARTIAL) in `state/lane-c-state.md`
- New not-evaluated claims appear in `ReportRunContract.unknowns` list
- No assertion about property value, neighborhood, or investment appears in claim language
- `RUN_DB_SMOKE=1 py -3.12 -m pytest tests/claims_engine/` passes
- Full verification passes: ≥235+N tests (N = new tests added)

---

## Task D-001: Level 7 DB wiring — full report-run pipeline through DB (Phase 7)

**Priority:** MEDIUM  
**Prerequisite:** Tasks C-001 + C-002 complete (claims ORM models must exist; Level 6 must pass)

**Context:**  
The API `POST /report-runs` endpoint currently uses in-memory repositories injected from
`api/dependencies.py`. The `SqlAlchemyReportRunRepository`, `SqlAlchemyAreaRepository`,
`SqlAlchemyEvidenceRepository`, and `SqlAlchemyClaimRepository` all exist and are tested.
The `get_session()` generator exists in `app/db/engine.py`. The wiring just needs to connect them.

**Work:**

1. Add a `backend/app/db/session.py` with `get_db_session()` FastAPI dependency:
   ```python
   from sqlalchemy.orm import Session
   from fastapi import Depends
   from app.db.engine import build_engine

   def get_db_session() -> Iterator[Session]:
       with Session(build_engine()) as session:
           yield session
   ```

2. Update `api/dependencies.py`:
   - Add a `create_db_services(session: Session, settings: Settings) -> ApiServices` path
   - When `DATABASE_URL` is set to a non-default value OR `RUN_DB_SMOKE == "1"`, inject:
     - `SqlAlchemyAreaRepository(session)` as the area repo
     - `SqlAlchemyEvidenceRepository(session)` as the evidence repo
     - `SqlAlchemyClaimRepository(session)` as the claim repo
     - `SqlAlchemyReportRunRepository(session, settings.object_store_root)` as the report repo
   - Keep the in-memory fallback for local dev / unit tests

3. Wire the `POST /report-runs` router to use the DB session when available.

4. Add a DB-backed API integration test that:
   - Seeds a `core.areas` row
   - Posts to `POST /report-runs` with a valid `area_id` + `intent_code`
   - Verifies 201 response
   - Verifies the `reports.report_runs` row exists in DB with `intent_id` populated
   - Cleans up after itself

**Acceptance criteria:**
- `POST /report-runs` uses DB repos when `RUN_DB_SMOKE=1`
- The DB-backed API test passes
- Level 7 gates L7-001 through L7-010 all PASS in `state/lane-d-state.md`
- Full verification: `RUN_DB_SMOKE=1 py -3.12 -m pytest` passes (≥235+N tests)
- `ruff check app/api/ app/reports/` and `mypy app/api/ app/reports/` both pass

---

## General constraints for Codex agents executing these tasks

1. Run `ruff check` and `mypy` on modified files after each sub-step. Fix before continuing.
2. Run `RUN_DB_SMOKE=1 py -3.12 -m pytest` (from `backend/`) at the end of each task.
3. All new SQLAlchemy models MUST inherit from `AppBase` (from `app.db.base`), not from `DeclarativeBase`.
4. All new ENUM type instances (e.g. `severity_band_enum`) MUST go in `app/db/types.py`, not in model files.
5. Do not delete any file. Archive superseded code to `archive/<date>_<reason>/`.
6. Do not touch files owned by other lanes (see `LANE_OWNERSHIP.md`).
7. Update `state/WORKLOG.md`, `state/VALIDATION_LOG.md`, and the relevant lane state file after each task.
8. Each task must be a separate commit (or logical group of commits). Do not squash across tasks.
