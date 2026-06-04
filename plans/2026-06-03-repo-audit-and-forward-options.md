# Repo Audit + Forward Options (2026-06-03)

Status: REVIEWED (ralplan consensus — Planner + Architect + Critic passes complete; factual corrections from both folded in and re-verified against ground truth)
Author: Claude (ralplan)
Scope: Full-repo state assessment since last check + Codex session direction + prioritized forward options.

> **Important — this is a snapshot of a moving target.** The Codex session was **actively running during this audit**: `git status` changed mid-review (the source-provenance sub-feature `provenance_repo.py`/`provenance_service.py` + tests appeared, and `PROJECT_STATE.md`/`VALIDATION_LOG.md`/`WORKLOG.md` flipped from "Level 1 / Docker not running" to "Level 2 PASS / DB smoke passes") between the first and second `git status`. Some early reads in this audit caught stale/older file versions. All load-bearing claims below were re-verified against ground truth after the Critic pass. See F13.

---

## 1. What was verified (evidence, not assertion)

- `verify.sh` (Git Bash, default): **PASS** — 173 collected, 172 run + **1 skipped** (the DB-gated `test_report_repository.py`); ruff clean; mypy strict clean (72 source files). The default gate does **not** set `RUN_DB_SMOKE`, so it skips DB smoke.
- **DB smoke HAS passed** (corrects an earlier draft claim of "never run"): `state/VALIDATION_LOG.md` records a `RUN_DB_SMOKE=1` run with Docker up — migrations apply, seeds apply, smoke passes, 173 tests. I independently confirmed Docker is running now (`docker info` → `29.2.1`). So L2's gates have passed **once, locally, with logged evidence**.
- **But the DB path is NOT CI-enforced**: `.github/workflows/ci.yml` runs `./scripts/verify.sh` with **no Postgres service container and no `RUN_DB_SMOKE`** — so a fresh CI checkout never exercises migrations, seeds, the ORM, or DB smoke. L2 PASS therefore rests on one developer manually having Docker up, not a reproducible gate.
- Git: 26 commits on `main` (`13b75a9` → `7527ba5 Add report protocol adapters`). No push (`origin/main` at `13b75a9`). Substantial **uncommitted** work in flight (Lane A provenance + Lane D persistence + all state docs).
- Uncommitted work in flight (as of latest `git status`, spanning two lanes):
  - Lane D persistence (TD-040): new `reports/models.py`, `reports/report_repo.py`, `tests/reports/test_report_repository.py`, `docs/adr/lane-d-0001-report-persistence.md`; modified `reports/service.py` + report/api tests.
  - Lane A provenance: new `source_registry/provenance_repo.py`, `provenance_service.py`, `tests/source_registry/test_source_provenance*.py`; modified `source_contracts.py`, `source_registry/models.py`.
  - Shared state docs modified: `PROJECT_STATE.md`, `VALIDATION_LOG.md`, `WORKLOG.md`, `lane-a-state.md`, `lane-d-state.md`. Root scratch files untracked: `findings.md`, `progress.md`, `task_plan.md`.
- Branches `codex/roi-plan-20260603` and `001-audit` are **stale** (no commits ahead of `main`).

## 2. Codex session direction (from artifacts + session file)

Codex executed lane tasks methodically in dependency order (TA→TB→TC→TD), largely **in-memory**, brought Docker up and ran DB smoke (flipping L2 to PASS during this very audit), and is mid-flight on DB-backed slices: persisted report runs (TD-040, Lane D) **and** a source-provenance sub-feature (Lane A `provenance_repo.py`/`provenance_service.py`, landed mid-audit). Its scratch notes (`task_plan.md`, `findings.md`) confirm it (a) reused `reports.report_runs` + `OBJECT_STORE_ROOT`, (b) noticed `ReportRunContract` lacked `machine_json_uri`/`cost_metrics`, and (c) flagged that **Lane B area persistence does not exist**, so the report test hand-seeds a `core.areas` row in raw SQL. The session file mentions Docker/RUN_DB_SMOKE heavily — the DB dimension is front-of-mind. "Alembic" appears only as echoed AGENTS.md text — never actually adopted.

**Net direction:** filling persistence **top-down** (reports + provenance first) and adding rule breadth, while the lower persistence layers (area/evidence/claim) remain in-memory — i.e., a single Codex session working across Lanes A and D at once, in one tree.

## 3. Strengths (credit where due — this is high-quality work)

- Evidence-before-claim enforced in `ClaimContract` validator; source-failure-as-evidence implemented; unknowns generated from source failures.
- Safety/liability invariants honored: user-safe language, `forbidden_language` list, per-claim verification tasks, screening-only framing (G-III).
- Severity vs confidence kept separate (G-II-004); caveats propagate into claims (L6-005).
- Deterministic claim IDs via `uuid5` (L6-003 reproducibility/idempotency).
- Lane isolation actually held: import invariants respected; Lane C uses injected `protocols`, not Lane A/B imports.
- Fail-closed source production-use check (G-IV-005). verify gate green across 173 tests, strict mypy, ruff.
- Lane A L3 provenance modeling is more complete than a first pass suggests: source + dataset + dataset-version + ingest-run contracts and ORM models, a clean `SourceRetrievalStatus`↔`job_status` enum translation, and in-memory + SQLAlchemy provenance repositories (covers much of L3-003/004/008 design-wise).

## 4. Findings — weaknesses / brittleness / fragility (severity-rated)

### CRITICAL

- **F1. The persistence foundation passed once manually but is not continuously/CI-proven, and most of the ORM surface is still unexercised.** DB smoke passed locally once (VALIDATION_LOG, Docker up) — so this is *not* "never run" — but CI never runs it (see §1), and only **one** DB-gated test exists (`test_report_repository.py`). The other SQLAlchemy adapters are tested only against a hand-rolled `_FakeSession` (`tests/source_registry/test_sqlalchemy_source_repo.py`), so they have **not** been round-tripped against Postgres even in the manual run: Lane A ships **4 ORM models** (`SourceModel`, `SourceDatasetModel`, `SourceDatasetVersionModel`, `SourceIngestRunModel`) + **two** SQLAlchemy repos (`SqlAlchemySourceRepository` + `SqlAlchemySourceProvenanceRepository`, the latter using the legacy `.query()` API), plus Lane D's `ReportRunModel`/`SqlAlchemyReportRunRepository`. `0001` uses PostGIS generated columns (`centroid`, `bbox` as `GENERATED ALWAYS AS … STORED`) + cross-schema enums; the migration self-labels "executable draft." Net: L2 PASS is **claimed with logged evidence (legitimate per the map's evidence rule) but fragile** — it depends on a developer having Docker up, isn't reproducible from a clean CI checkout, and exercises only one of three ORM adapters. The maturity *claim* (Level 2 PASS) is defensible; its *durability* is not.

- **F2. Inverted persistence order.** L3–L7 domain logic was built in-memory, and the *current* slice (persist report runs — top of the stack) was built before the layers beneath it persist at all (see F3): areas, evidence, and claims have no DB-backed store. So even though the L2 schema now applies and smoke passes, the persistence layers are being filled top-down (reports first) rather than bottom-up (area→evidence→claim→report). Defensible as ports/adapters sequencing, but report persistence currently bridges to nothing underneath it.

### MAJOR

- **F3. Lanes B & C have zero persistence; the evidence/claim graph is memory-only.** No `models.py` in `area_geometry/`, `evidence_ledger/`, or `claims_engine/`. `claims.claims` / `claims.claim_evidence` / `evidence.observations` are never written. When `SqlAlchemyReportRunRepository` persists, it writes only the `report_runs` row + a JSON artifact embedding claims. So the durable system-of-record does **not** hold the evidence→claim graph, and source→evidence→claim→report **lineage is not queryable** (breaks the intent behind G-I/G-II and L10-DATA-007). Report persistence is a bridge with no far bank yet.

- **F4. Cross-lane FK seam handled by raw SQL in a test.** `test_report_repository.py::_seed_area_row` hand-inserts `core.areas` via raw `ST_GeomFromGeoJSON` SQL because Lane B has no area persistence. The vertical-domain lane split does not cleanly map to the relational integration (everything FKs to `core.areas`); there is no defined mechanism for cross-lane persisted fixtures except raw SQL.

- **F5. Tri-modal entity definition drift (Contract / SQL / ORM), already diverged — with a latent correctness bug.** Each entity is defined three times by hand. Confirmed drift on report runs: `ReportRunContract.intent_code: str` vs `reports.report_runs.intent_id uuid FK` vs `ReportRunModel.intent_id` (nullable, **never populated** by `_contract_to_model`). Result: persisted rows have `intent_id`, `intent_version_id`, `rule_version_id`, `workspace_id` = NULL; intent + rule version survive only inside the JSON artifact → weakens reproducibility metadata (L7-002 / G-II-006). Deeper: there is **no `IntentCode` enum** in `domain/enums.py` at all — `intent_code` is an unconstrained free string validated against a 9-value SQL `core.intent_code` enum only at FK-resolution time, which currently never happens. No test verifies contract↔ORM↔schema agreement.

- **F6. No Alembic; no drift detection.** Despite "SQLAlchemy 2/Alembic-ready", migrations are raw SQL applied by shell, ORM models are hand-mirrored, and `db_smoke_check.py` validates only PostGIS version + schema presence + `source.sources` row count — it does **not** exercise the ORM or check ORM-vs-schema agreement. Drift can pass smoke undetected.

- **F11. The `ruleset_body` reproducibility guarantee is hollow (stated invariant unmet).** The schema models `rules.rule_versions.ruleset_body jsonb` + `rules.rule_execution_runs` precisely so a report can be reproduced from a *stored, versioned ruleset*. But evaluation logic lives in `rule_engine.py` Python while the YAML carries only gate metadata (see F8) — so persisting/replaying a `ruleset_body` cannot reproduce a verdict; behavior is pinned to a git SHA, not the stored body. L7 is "report-run reproducibility" and AGENTS.md names schema changes that threaten report reproducibility as a stop-and-record condition. The system therefore *claims* (in schema) a reproducibility property its engine cannot honor. (Surfaced by Architect review.)

### MODERATE (scalability / modularity / non-fragility — the stated lens)

- **F7. Fragmented ORM `DeclarativeBase` (with a concrete conflict already present).** Lane A `SourceRegistryBase` and Lane D `ReportBase` are independent bases with no shared metadata registry. Worse, `job_status_enum` (`name="job_status", schema="jobs"`) is declared **twice** — `source_registry/models.py:26` and `reports/models.py:19` — so any unified `metadata.create_all()` path would have two bases each trying to manage the same type. Blocks unified test-DB setup, cross-table ORM relationships, and consistency; will fragment further as Lanes B/C add models. Direct artifact of lane isolation with no shared-Base decision.

- **F8. Rule engine does not scale by design.** `rule_engine.py` is ~1,750 lines for 6 hard gates: the YAML supplies only gate *metadata*, while evaluation logic + claim construction are hand-coded per domain with near-identical 4-method blocks (`_x_unknown/_needs_review/_stale/...`). Adding the remaining MILESTONE_MAP rule categories (soil_septic, environmental_hazard, market_context, resource_context) ≈ +250 lines of copy-paste each. `evaluate()` hard-codes the six conditions by name, so a new YAML gate without new Python is inert. Logic *quality* is good; the *structure* is the opposite of the "modular/scalable" goal.

- **F9. Bespoke YAML parser; orphaned dependency.** `_parse_ruleset_yaml` is a hand-rolled, indentation-sensitive parser (breaks on valid YAML variants: flow style, anchors, multi-line scalars, comments mid-structure). PyYAML is **not** a runtime dependency; `types-PyYAML` (stubs only) sits in dev deps with nothing importing `yaml`. Fragile and inconsistent.

### MINOR

- **F10. Governance hygiene.** Root scratch files (`findings.md`, `progress.md`, `task_plan.md`) are untracked at repo root (belong in `.agent/` or `.gitignore`). Stale branches `codex/roi-plan-20260603`, `001-audit` are cleanup/prune candidates. TD-040 slice is uncommitted.

- **F12. DB tooling conflates schema with seed presence (corrected).** Earlier draft claimed a seed-ordering trap; corrected: `scripts/db_apply_migrations.sh` (lines 11-19) applies migrations **and** seeds together, so the documented path is fine. Residual minor concern: there is no migrations-only path (e.g. for schema-only CI validation), and `db_smoke_check.py` asserts `source.sources > 0`, conflating "schema correct" with "seeds loaded" — a schema-only validation can't be expressed. (Corrected per Critic review.)

- **F13. Concurrent live mutation of a shared, OneDrive-synced working tree (coordination hazard) — CRITICAL for process.** The Codex agent was **editing this working tree while the audit ran**: `git status` gained `provenance_repo.py`/`provenance_service.py` + provenance tests and flipped `PROJECT_STATE.md` L1→L2 between two checks minutes apart; an early Read returned a stale 94-line `source_registry/models.py` vs the true 224-line file. Two compounding causes: (a) a single Codex session is working **across Lanes A and D simultaneously in one tree** (uncommitted edits span `source_*`, `reports/*`, and shared `state/*`), and (b) the tree is under `OneDrive\Desktop\...`, adding sync races, stale reads, and `.pyc` churn. The 4-lane "isolation" model assumes lane agents can't collide, but with no git-worktree isolation and a synced path, concurrent agents *can* stomp each other and any audit/plan is immediately stale. Mitigation: give each concurrent agent its own git worktree/branch (the `lane-*/` convention already exists), move the tree off OneDrive (or pause sync during agent runs), and commit-or-stash before launching a second agent.

## 5. Planning-doc alignment

- `state/PROJECT_STATE.md` (current) claims **"Level 2 — Postgres/PostGIS Storage Spine: PASS"** with logged DB-smoke evidence. That claim is *defensible* per the map's evidence rule, but **fragile**: CI doesn't run DB smoke (so it's not reproducible from a clean checkout), only one of three ORM adapters is round-tripped, and the migration is a draft. The doc should re-state L2 as "PASS (manual, not CI-enforced)" and make "**lock L2 into CI**" the explicit next gate rather than presenting it as settled.
- `LANE_OWNERSHIP.md` has no contract for cross-lane *persisted* fixtures (the F4 seam) nor a shared-`DeclarativeBase` owner (F7).
- No ADR records the deliberate in-memory-first adaptation to the Docker blocker.

---

## 6. Forward options (each independently scoped; dependencies noted)

### Option A — Lock the Postgres/PostGIS spine into CI (make L2 PASS durable). Effort: S
Docker is already available locally and DB smoke passed once; the gap is **enforcement**. Add a GitHub Actions `postgis/postgis:16-3.4` service job that applies migrations + seeds, runs `db_smoke_check.py` with `RUN_DB_SMOKE=1`, and adds an **ORM round-trip test per adapter** (the 4 source models + provenance repo + report repo — today only the report repo is real-DB-tested; the rest use `_FakeSession`). 
- **Pros:** Converts L2 from "passed once on a dev laptop" to "proven on every push"; exercises the 2 currently-unproven SQLAlchemy adapters; catches the generated-column / duplicate-`job_status_enum` / FK-ordering issues automatically instead of on someone's first `psql`. Foundation for everything else.
- **Cons:** CI runtime/config; will likely surface a fix batch on first real run; no user-visible feature.
- **Depends on:** nothing (Docker is up). **Highest leverage, smallest effort.**

### Option B — Build persistence bottom-up: area → evidence → claim → rule-execution → report. Effort: L (multi-session, multi-lane)
Add ORM models + DB-backed repos + DB-gated round-trip tests for areas (Lane B), evidence + claim + `claim_evidence` (Lane C), **and the rules schema (`rule_sets`/`rule_versions`/`rule_execution_runs`)** so claims persist with a non-NULL `rule_execution_run_id` and a stored ruleset body (without rule-execution persistence, claims repeat the F5 NULL-lineage pattern one layer down). Then wire `ReportRunService` to persist real evidence/claim/rule-execution rows so lineage is queryable and TD-040 integrates correctly.
- **Pros:** Realizes evidence-before-claim durably (not just in memory); enables source→evidence→claim→report lineage (L10-DATA-007); resolves the hollow-reproducibility risk (F11) by giving the engine a real stored ruleset body; corrects build order; makes report persistence meaningful.
- **Cons:** Largest, multi-lane effort; rules-schema persistence adds a step often forgotten.
- **Depends on:** Option A **and Option C item (1)** (a single shared `DeclarativeBase` + a shared persisted-area seed helper are prerequisites here, not parallel — otherwise each lane re-invents raw-SQL area seeding and adds another independent Base).

### Option C — Pay down structural/scalability debt (modularity & non-fragility). Effort: M
(1) Unify a single shared `DeclarativeBase` in the shared zone (F7). (2) Add a contract↔ORM↔schema alignment/drift test; resolve `intent_code↔intent_id` + persist rule version (F5/F6). (3) Replace the bespoke parser with PyYAML as a justified runtime dep, or drop the orphaned stub (F9). (4) Refactor the rule engine to be table-driven so a new gate is YAML + a small adapter, not 250 lines (F8).
- **Pros:** Directly serves the modularity/scalability/non-fragility lens; makes new rule categories + jurisdictions cheap; removes parser fragility; prevents silent drift.
- **Cons:** Refactor risk on green code; unified Base touches the shared zone (cross-lane coordination).
- **Depends on / sequencing:** Item (1) (unified Base) is a **prerequisite of Option B**, not parallel. Item (3) PyYAML decision is start-now. Item (2) drift test is most valuable once A is green. Item (4) rule-engine refactor should be **down-ranked and gated behind A+B** (so it has a DB round-trip safety net) and scoped as "add the next/6th-style gate via YAML-only to prove the table-driven abstraction," not a big-bang rewrite.

### Option D — Stay the course (finish TD-040 + add rule breadth), defer DB hardening. Effort: n/a — baseline for comparison, not recommended
- **Pros:** Preserves momentum; more visible breadth; no Docker dependency.
- **Cons:** Compounds the central risk (more code on an unproven foundation); widens tri-modal drift; defers the only gate that raises maturity. Breadth without depth.
- **Depends on:** nothing — but **not recommended as the primary path.**

### Option E — Planning-doc & governance realignment. Effort: S
Set "lock L2 into CI" as the explicit next gate in `PROJECT_STATE.md`; ADR for the in-memory-first adaptation + shared-Base decision; add a cross-lane persisted-fixture contract + shared-Base owner to `LANE_OWNERSHIP.md`; relocate/gitignore root scratch files; prune stale branches; commit (or explicitly hold) TD-040.
- **Pros:** Keeps the governance/enforcement layer honest; low effort.
- **Cons:** Documentation, not capability.
- **Depends on:** informed by A–C decisions.

## 6b. Decisions only you can make (surface these first)

1. **Concurrency / isolation (most urgent).** A Codex session appears to still be running on *this* working tree (it mutated files mid-audit, F13). Before more work: decide whether concurrent agents each get an isolated **git worktree + lane branch** (the `lane-*/` convention already exists) vs. sharing one tree. Sharing one tree = collisions, stale reads, and audits that go stale in minutes. Recommend: isolate, and **commit or stash the in-flight Codex work** before launching anything else.
2. **CI-enforce the DB path?** Docker is available and smoke passed once; the choice is whether to invest ~S effort to run migrations+seeds+smoke+ORM round-trips in CI (Option A) so L2 stays proven, vs. relying on a developer manually having Docker up. Recommend: CI-enforce.
3. **TD-040 disposition.** The uncommitted persisted-report slice is green and correctly gated. Commit it now (with a tracked follow-up to rewire it through real evidence/claim/rule-exec rows once Option B lands), or hold it until B? Recommend: **commit-but-condition.**
4. **Move the repo off OneDrive?** (F13) Recommend yes, or pause sync during agent runs.

## 7. Recommended sequence (short / mid / long term)

**Corrected dependency graph (from Architect review):**
`A (prove spine) → [C1 unified Base + shared area-seed helper] → B (area→evidence→claim→rule-exec→report adapters) → C2 (contract↔ORM↔schema drift test) → F8 rule-engine refactor`. The two genuinely start-now, A-independent items are the **PyYAML decision (F9)** and the **drift test design**.

- **Short term (now):** Option A (lock L2 into CI-Postgres so it stays proven) + Option E doc realignment + the F9 PyYAML decision. Decide TD-040: **commit-but-condition** (it's green and correctly gated) and add an issue to re-wire it through real evidence/claim/rule-exec rows once B lands; do not build more report-persistence breadth on it yet.
- **Mid term:** Option C item (1) (unified `DeclarativeBase` + shared area-seed helper) → Option B (area→evidence→claim→rule-execution→report) → Option C drift test + intent/rule-version persistence (closes F5/F11).
- **Long term:** Prove **one real MVP jurisdiction end-to-end** (even with fixture data) to validate that the contracts and gates model reality — this, not "more rule domains in the abstract," is the right next breadth, and it forces the still-undecided product calls (MVP county, parcel vendor) that AGENTS.md flags as stop-conditions. Then resume up-stack breadth (remaining rule domains via the now-table-driven engine, soft scoring, L8 connectors) and apply JR-*/RP-* readiness gates before new jurisdictions/intents.

**One-line thesis:** The work is high-quality but stacked on an unproven base; the highest-leverage next move is to *prove the Postgres/PostGIS spine in CI and build persistence bottom-up (area→evidence→claim→rule-exec→report)*, before adding more in-memory breadth — and the unit after that is one real jurisdiction end-to-end, not more abstract rules.
