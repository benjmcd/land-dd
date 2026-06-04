# Deferred Codex Tasks — 2026-06-03

These tasks were deferred from the pre-Codex hardening session (ralplan A-minus plan).
Each task is scoped, has acceptance criteria, and builds on the structural fixes already made.
Assign one task per Codex lane agent session. Do not start a higher-numbered task
until the prior one is complete and verified.

**Completed pre-conditions (do NOT redo):**
- `backend/app/db/base.py` — single shared `AppBase(DeclarativeBase)` with MetaData naming_convention
- `backend/app/db/types.py` — canonical ENUM instances for `authority_level_enum`, `confidence_band_enum`,
  `job_status_enum`, **and `severity_band_enum`** (all pre-done; use these, never re-declare in model files)
- `backend/app/domain/enums.py` — `IntentCode(StrEnum)` with 9 validated values
- All legacy `.query()` calls in `provenance_repo.py` upgraded to SQLAlchemy 2.x `select()`

---

## Task C-001: Claims ORM models (Phase 3)

**Priority:** HIGH
**Prerequisite:** `backend/app/db/base.py` and `backend/app/db/types.py` must exist (DONE — commit 99cde91).
`severity_band_enum` is already in `db/types.py` (pre-done) — do NOT redeclare it.

**Context:**
`SqlAlchemyClaimRepository` (in `backend/app/claims_engine/claim_repo.py`) uses raw SQL
`text()` for all operations against `claims.claims`, `claims.claim_evidence`, and
`claims.verification_tasks`. This bypasses type safety. All other SQLAlchemy repositories
in this project use ORM models.

**Work:**

1. Create `backend/app/claims_engine/models.py` with ORM models inheriting from `AppBase`.
   Import `AppBase` from `app.db.base`.
   Import `confidence_band_enum` and `severity_band_enum` from `app.db.types` (already exist — do not redeclare).

   The **actual** `claims.claims` table (from `db/migrations/0001_initial_spine.sql`):
   ```sql
   CREATE TABLE IF NOT EXISTS claims.claims (
       claim_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
       area_id uuid NOT NULL REFERENCES core.areas(area_id),
       rule_execution_run_id uuid REFERENCES rules.rule_execution_runs(rule_execution_run_id),
       intent_id uuid REFERENCES core.intents(intent_id),
       claim_code text NOT NULL,
       domain text NOT NULL,
       assertion text NOT NULL,
       severity claims.severity_band NOT NULL DEFAULT 'unknown',
       confidence evidence.confidence_band NOT NULL DEFAULT 'unknown',
       user_safe_language text NOT NULL,
       verification_required boolean NOT NULL DEFAULT false,
       verification_task text,
       created_at timestamptz NOT NULL DEFAULT now(),
       metadata jsonb NOT NULL DEFAULT '{}'::jsonb
   );
   ```
   NOTE: There are NO `is_negative`, `is_unknown`, or `needs_review` columns.
   NOTE: There ARE `rule_execution_run_id` and `intent_id` columns (nullable FKs — map as `UUID | None`).

   The **actual** `claims.claim_evidence` table:
   ```sql
   CREATE TABLE IF NOT EXISTS claims.claim_evidence (
       claim_id uuid NOT NULL REFERENCES claims.claims(claim_id) ON DELETE CASCADE,
       evidence_id uuid NOT NULL REFERENCES evidence.observations(evidence_id),
       support_role text NOT NULL DEFAULT 'supports',
       PRIMARY KEY (claim_id, evidence_id)
   );
   ```
   NOTE: The column is `support_role text`, NOT `evidence_order int`. The existing `claim_repo.py`
   already inserts `support_role='supports'` — the ORM model must map this column exactly.

   The **actual** `claims.verification_tasks` table:
   ```sql
   CREATE TABLE IF NOT EXISTS claims.verification_tasks (
       verification_task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
       area_id uuid NOT NULL REFERENCES core.areas(area_id),
       claim_id uuid REFERENCES claims.claims(claim_id),
       task_code text NOT NULL,
       task_text text NOT NULL,
       responsible_party text,
       priority claims.severity_band NOT NULL DEFAULT 'medium',
       status text NOT NULL DEFAULT 'open',
       due_at timestamptz,
       completed_at timestamptz,
       completion_note text,
       created_at timestamptz NOT NULL DEFAULT now()
   );
   ```
   NOTE: `claim_id` is nullable here. The existing `claim_repo.py` inserts `task_code`, `task_text`,
   `priority`, `status`, and `area_id` — the ORM model must map all of these.

2. Refactor `SqlAlchemyClaimRepository` to use the new ORM models:
   - `add()`: use `session.add(ClaimModel(...))` + `session.add_all([ClaimEvidenceLinkModel(...)])` + flush
   - `get()`: use `session.get(ClaimModel, claim_id)` + query `ClaimEvidenceLinkModel`
   - `list_by_area()`: use `select(ClaimModel).where(...)`
   - `list_all()`: use `select(ClaimModel)`
   - All queries must use SQLAlchemy 2.x `select()` style (not `.query()`)
   - The `_claim_params` and `_row_to_claim` helper functions should be removed
     or converted to ORM-based equivalents; keep the `_claim_metadata` / `_metadata_evidence_ids`
     logic since evidence_id ordering is stored in `metadata` JSONB

3. Add targeted type annotations and ensure `mypy` passes.

**Acceptance criteria:**
- `grep -rn "\.query(" backend/app/` returns 0 matches
- `grep -rn "class.*DeclarativeBase" backend/app/` returns exactly 1 match (in `db/base.py`)
- `grep -rn "severity_band_enum\s*=" backend/app/` returns exactly 1 match (in `db/types.py`)
- `grep -rn "rule_execution_run_id" backend/app/claims_engine/models.py` returns ≥1 match
- `grep -rn "support_role" backend/app/claims_engine/models.py` returns ≥1 match
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
soil/septic, environmental hazards, resource context, market context.

Per project non-negotiables:
- No report may assert final buildability, water rights, or market value.
- "Every interpreted claim must cite stored evidence. No evidence, no claim."
- Source failures are first-class evidence, not silent results.
- Market context claims MUST NOT assert valuation, pricing, or investment advice.

**Design decision — sentinel source failure approach:**
These 4 categories cannot produce real screening results in the current tool version because
no data connectors exist for them. The correct pattern mirrors the existing "source unavailable"
pattern already in the rule engine: create SOURCE_FAILURE evidence records citing a registered
sentinel source, then let the rule engine emit "unknown due to source failure" claims from them.

This preserves the evidence-before-claim invariant fully: every claim will cite a stored
SOURCE_FAILURE evidence record, and that evidence record cites a registered source.

**Work:**

### Step 1 — Register the sentinel source

In `backend/app/claims_engine/not_evaluated.py` (new file), define:
```python
NOT_EVALUATED_SOURCE_NAME = "Land Diligence MVP — Unsupported Screening Categories"
NOT_EVALUATED_SOURCE_ORG = "internal"
NOT_EVALUATED_DOMAINS = ("soil_septic", "env_hazard", "resource_context", "market_context")

NOT_EVALUATED_CAVEATS = {
    "soil_septic": (
        "Soil and septic feasibility data sources are not supported in this screening "
        "tool version. A soil perc test, county health department consultation, and "
        "septic engineer assessment are required before any building or septic system "
        "determination can be made."
    ),
    "env_hazard": (
        "Environmental hazard data sources (Superfund, brownfield, LUST, etc.) are "
        "not supported in this screening tool version. Consult EPA ECHO, state DEQ "
        "databases, and a Phase I ESA professional for environmental due diligence."
    ),
    "resource_context": (
        "Mineral rights, timber, water rights, and resource context data sources are "
        "not supported in this screening tool version. Consult a title company, "
        "state geological survey, and water rights attorney for resource due diligence."
    ),
    "market_context": (
        "Market context was not evaluated. No valuation, pricing, comparable sales, "
        "neighborhood desirability assessment, or investment guidance is provided by "
        "this screening tool. Consult a licensed appraiser and real estate professional."
    ),
}
```

### Step 2 — Add 4 new conditions and YAML ruleset entries

Add to `rule_engine.py`:
```python
SOIL_SEPTIC_CONDITION = "soil_septic_unsupported"
ENV_HAZARD_CONDITION = "env_hazard_unsupported"
RESOURCE_CONTEXT_CONDITION = "resource_context_unsupported"
MARKET_CONTEXT_CONDITION = "market_context_out_of_scope"
```

Add 4 new `hard_gates` entries to `config/ruleset_homestead_mvp.yaml`:
- `claim_code`: `SOIL_NOT_EVALUATED`, `ENV_HAZ_NOT_EVALUATED`, `RESOURCE_NOT_EVALUATED`, `MARKET_OUT_OF_SCOPE`
- `severity_on_fail`: `informational` for all four
- `condition`: the condition constants above
- `verification_task`: what the user should do manually (derive from caveats above)

### Step 3 — Service-layer sentinel source creation

In `backend/app/reports/service.py`, update `create_report_run()`:

1. Before calling `_rule_engine.evaluate(evidence)`, look up or create the sentinel source:
   ```python
   sentinel_source = self._ensure_sentinel_source()
   ```

2. Add `_ensure_sentinel_source()` to `ReportRunService`:
   - Calls `source_service.list_all()` to find an existing source with
     `name == NOT_EVALUATED_SOURCE_NAME`
   - If not found, registers a new `SourceContract` for it with
     `license_status="approved"`, `commercial_use_status="approved"`, etc.
   - Returns the `SourceContract`

3. For each domain in `NOT_EVALUATED_DOMAINS`, if no evidence records already exist
   for that domain in `evidence`, create a SOURCE_FAILURE evidence record:
   ```python
   for domain in NOT_EVALUATED_DOMAINS:
       if not any(e.domain == domain for e in evidence):
           not_eval_ev = self._evidence_service.create_source_failure(
               area_id=area_id,
               source_id=sentinel_source.source_id,
               method_code=f"{domain}_not_evaluated",
               caveat=NOT_EVALUATED_CAVEATS[domain],
               domain=domain,
           )
           evidence = [*evidence, not_eval_ev]
   ```

4. The updated `evidence` list is then passed to `_rule_engine.evaluate(evidence)`.
   The rule engine's new 4 domain handlers (Step 4) will emit claims from these
   source failure records.

### Step 4 — Rule engine handlers for the 4 new domains

Add 4 new `_xxx_source_failure_check()` predicates and 4 new claim-emitting methods to
`RuleEngine.evaluate()`, following the exact same pattern as the existing 6 domains:
- `_is_soil_septic_source_failure(evidence) -> bool`
- `_is_env_hazard_source_failure(evidence) -> bool`
- `_is_resource_context_source_failure(evidence) -> bool`
- `_is_market_context_source_failure(evidence) -> bool`
- `_soil_septic_not_evaluated_claim(area_id, rule, evidence_records) -> ClaimContract`
- `_env_hazard_not_evaluated_claim(area_id, rule, evidence_records) -> ClaimContract`
- `_resource_context_not_evaluated_claim(area_id, rule, evidence_records) -> ClaimContract`
- `_market_context_not_evaluated_claim(area_id, rule, evidence_records) -> ClaimContract`

Each `_xxx_not_evaluated_claim` method should:
- Set `severity = SeverityBand.INFORMATIONAL`
- Set `confidence = ConfidenceBand.UNKNOWN`
- Set user_safe_language from `NOT_EVALUATED_CAVEATS[domain]`
- Set `verification_required = True` with an appropriate verification_task

Note: Because `severity == SeverityBand.INFORMATIONAL` (NOT UNKNOWN), these claims will
NOT appear in `ReportRunContract.unknowns` (which filters `severity == UNKNOWN`).
They WILL correctly represent "the tool disclosed a gap" without being falsely flagged as risks.
If you want them in `unknowns`, use `severity = SeverityBand.UNKNOWN` instead.
Choose based on the desired UX: INFORMATIONAL = disclosure note; UNKNOWN = gap warning.

### Step 5 — Tests

Add unit tests in `backend/tests/claims_engine/test_not_evaluated_claims.py`:
- Verify that when `RuleEngine.evaluate()` receives a SOURCE_FAILURE record for each
  of the 4 not-evaluated domains, it emits the corresponding not-evaluated claim
- Verify `user_safe_language` does NOT contain words like "value", "price", "invest",
  "neighborhood", "desirable" for market_context claims
- Verify `is_source_failure=True` on the sentinel evidence records

**Acceptance criteria:**
- Level 6 gates L6-001 through L6-010 must now all be PASS (not PARTIAL) in `state/lane-c-state.md`
- `RuleEngine.evaluate()` emits claims for all 4 not-evaluated domains when provided with
  the corresponding SOURCE_FAILURE evidence records
- No assertion about property value, neighborhood desirability, or investment
  appears in any claim language (grep for "value", "price", "invest", "neighborhood")
- `RUN_DB_SMOKE=1 py -3.12 -m pytest tests/claims_engine/` passes
- `RUN_DB_SMOKE=1 py -3.12 -m pytest` passes (≥235+N tests where N = new tests added)
- `ruff check app/claims_engine/ app/reports/` passes
- `mypy app/claims_engine/ app/reports/` passes

---

## Task D-001: Level 7 DB wiring — full report-run pipeline through DB (Phase 7)

**Priority:** MEDIUM
**Prerequisite:** Tasks C-001 + C-002 complete (claims ORM models must exist; Level 6 must pass)

**Context:**
The API `POST /report-runs` endpoint currently uses in-memory repositories injected from
`api/dependencies.py`. The `SqlAlchemyReportRunRepository`, `SqlAlchemyAreaRepository`,
`SqlAlchemyEvidenceRepository`, and `SqlAlchemyClaimRepository` all exist and are tested.

`get_session()` is already defined in `app/db/engine.py` as a properly implemented singleton-backed
generator factory. **Do NOT use `build_engine()` in FastAPI dependencies** — `build_engine()` creates
a new engine per call, destroying connection pooling. Use `get_session()` from `engine.py`.

`app.state.services` is initialized in `backend/app/main.py` at line 21:
`app.state.services = create_api_services()`
**D-001 must update `main.py`** to conditionally inject DB-backed services alongside the
`api/dependencies.py` update. Both files need to change.

**Work:**

1. Add `backend/app/db/session.py` with a FastAPI-compatible `get_db_session()` dependency
   that wraps the existing `get_session()` generator from `engine.py`:
   ```python
   from __future__ import annotations
   from collections.abc import Iterator
   from sqlalchemy.orm import Session
   from app.db.engine import get_session

   def get_db_session() -> Iterator[Session]:
       """FastAPI dependency — yields a SQLAlchemy session from the shared engine pool."""
       yield from get_session()
   ```
   This delegates entirely to `get_session()` which already uses the module-level singleton
   `_engine` and `_session_factory`. No new engine creation.

2. Update `api/dependencies.py`:
   - Add `create_db_services(session: Session, settings: Settings) -> ApiServices`
   - When `settings.database_url` is a real postgres URL (not default/test)
     OR `os.getenv("RUN_DB_SMOKE") == "1"`, inject:
     - `SqlAlchemyAreaRepository(session)` as the area repo
     - `SqlAlchemyEvidenceRepository(session)` as the evidence repo
     - `SqlAlchemyClaimRepository(session)` as the claim repo
     - `SqlAlchemyReportRunRepository(session, settings.object_store_root)` as the report repo
   - Keep `create_api_services()` as the in-memory fallback for local dev / unit tests

3. Update `backend/app/main.py` to conditionally use DB-backed services:
   - Replace `app.state.services = create_api_services()` with logic that:
     - Reads `settings = get_settings()`
     - If `RUN_DB_SMOKE == "1"` or `settings.database_url` points to postgres:
       does NOT set `app.state.services` at startup
       instead adds a `lifespan` context manager or `startup` event that creates
       a DB-session-scoped service set per request
     - Otherwise: keeps `app.state.services = create_api_services()` (in-memory)
   - Wire the `POST /report-runs` router to use `get_db_session` when available

4. Add a DB-backed API integration test in `backend/tests/api/test_report_runs_db.py`:
   - Seeds a `core.areas` row and a `core.intents` row
   - Posts to `POST /report-runs` with a valid `area_id` + `intent_code`
   - Verifies 201 response
   - Verifies the `reports.report_runs` row exists in DB with `intent_id` populated
   - Cleans up after itself

**Acceptance criteria:**
- `POST /report-runs` uses DB repos when `RUN_DB_SMOKE=1`
- `get_db_session()` in `session.py` delegates to `get_session()` from `engine.py`
  (does NOT call `build_engine()` directly)
- The DB-backed API test passes
- Level 7 gates L7-001 through L7-010 all PASS in `state/lane-d-state.md`
- Full verification: `RUN_DB_SMOKE=1 py -3.12 -m pytest` passes (≥235+N tests)
- `ruff check app/api/ app/reports/ app/db/` and `mypy app/api/ app/reports/ app/db/` both pass

---

## General constraints for Codex agents executing these tasks

1. Run `ruff check` and `mypy` on modified files after each sub-step. Fix before continuing.
2. Run `RUN_DB_SMOKE=1 py -3.12 -m pytest` (from `backend/`) at the end of each task.
3. All new SQLAlchemy models MUST inherit from `AppBase` (from `app.db.base`), not from `DeclarativeBase`.
4. All ENUM type instances MUST be imported from `app/db/types.py`, never re-declared in model files.
   `severity_band_enum` is already in `db/types.py` — use it.
5. Do not delete any file. Archive superseded code to `archive/<date>_<reason>/`.
6. Do not touch files owned by other lanes (see `LANE_OWNERSHIP.md`).
   `backend/app/domain/claim_contracts.py` is Lane C's file.
   `backend/app/domain/enums.py` is in the Shared Interface Zone — changes require ADR.
7. Update `state/WORKLOG.md`, `state/VALIDATION_LOG.md`, and the relevant lane state file after each task.
8. Each task must be a separate commit (or logical group of commits). Do not squash across tasks.
9. The DB schemas in this plan file have been verified against `db/migrations/0001_initial_spine.sql`.
   If in doubt, read the migration SQL directly — it is authoritative.
