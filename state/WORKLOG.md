# Worklog

Append concise entries. Do not rely on chat history.

## 2026-06-04 (Session 2 D-004 Level 8 ownership and fixture acceptance)

- Completed Lane D D-004 from root `main` after Session 1 landed Lane B TB-100 at `cf9897e`.
- Mapped Level 8 connector gates L8-001 through L8-010 to lane owners and supporting owners before connector runtime code.
- Defined the first fixture-only connector acceptance path as a static local flood fixture: no live network, no browser/download step, no vendor credential, and no paid/live API dependency.
- Recorded pre-code decisions for future `backend/app/connectors/` ownership, connector run lifecycle authority, idempotency identity, success evidence shape, failure taxonomy, and geometry fixture needs.
- Preserved D-003 schema-contract boundaries: no shared schemas, migrations, connector runtime code, or Lane A/B/C implementation files were edited.
- Set D-005 as the next safe step: resolve connector module ownership and run lifecycle authority before any fixture connector implementation.

## 2026-06-04 (Session 1 Lane B TB-100 coordinate validation hardening)

- Created isolated worktree `worktrees/session1-lane-b` on branch `lane-b/session1-geometry-hardening` from root `main` at `04d0a8f` to avoid Session 2's active Lane D D-001 checkout edits.
- Implemented a Lane B-only validator hardening slice: non-finite longitude/latitude values and out-of-range EPSG:4326 longitude/latitude positions now fail `validate_geojson`.
- Added one invalid coordinate fixture plus inline non-finite coordinate regression coverage in `backend/tests/area_geometry/test_area_service.py`.
- Verified focused service/validator checks, DB-enabled Lane B tests, targeted Lane B lint/type checks, and full PowerShell verification with DB smoke enabled. Pre-merge result: 253 tests pass; lint clean; mypy clean (89 source files); DB smoke passes.
- Merged root `main` at D-001 into the Lane B worktree, resolving conflicts only in shared state files by preserving both Session 2 D-001 state and Session 1 TB-100 state.
- Verified post-merge focused Lane B/report/API checks and full PowerShell verification with DB smoke enabled. Result: 254 tests pass; lint clean; mypy clean (90 source files); DB smoke passes.
- Merged root `main` at D-002 into the Lane B worktree after `main` advanced again; conflicts were again limited to shared state files and resolved by preserving D-002 as current repo-wide authority and TB-100 as the isolated Lane B contribution.
- Verified post-D-002 focused Lane B/report/API checks and full PowerShell verification with DB smoke enabled. Result: 255 tests pass; lint clean; mypy clean (91 source files); DB smoke passes.
- Merged root `main` at D-003 into the Lane B worktree after coordination; conflicts were again limited to shared state files and resolved by preserving D-003 as current repo-wide authority and TB-100 as the isolated Lane B contribution.
- Verified post-D-003 full PowerShell verification with DB smoke enabled. Result: 255 tests pass; lint clean; mypy clean (91 source files); DB smoke passes.
- Squash-merged the verified Lane B TB-100 branch onto root `main` so coordinate hardening is now mainline without carrying temporary cross-session merge commits.
- Verified root `main` after squash merge: Lane B targeted tests pass with DB smoke enabled; targeted Lane B ruff/mypy pass; full PowerShell verification with DB smoke enabled passes with 255 tests, lint clean, mypy clean (91 source files), migrations/seeds, and DB smoke.
- Coordination note sent to Session 2 without changing its reasoning level; no action requested.

## 2026-06-04 (Session 2 D-000 report surfacing)

- Completed Lane D D-000 by updating `ReportRunService` to create stored unsupported-category SOURCE_FAILURE evidence for missing not-evaluated domains before rule evaluation.
- Preserved Lane C ownership: no Lane C implementation or state files were modified. The report service uses Lane C's not-evaluated helper, then normalizes the helper payload to the evidence ledger's controlled source-failure payload shape before storage.
- Updated report service, API scaffold, and DB-backed report repository tests so unsupported soil/septic, environmental hazards, resource context, and market context appear in report/API `unknowns`, source manifests, caveats, and cost metrics.
- Verified Lane D targeted checks: report/API tests pass with DB smoke enabled; targeted ruff and mypy pass.
- Verified full gate: `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1` passes with 250 backend tests, lint clean, mypy clean (89 source files), migrations/seeds, and DB smoke.
- Updated Lane D plan/state, project state, deferred task plan, and task queue. D-000 is done; D-001 DB-backed API workflow wiring is now the next Lane D task.

## 2026-06-04 (Session 2 merged C-002 handoff)

- Merged Session 1's clean `codex/session1-lane-c` C-002 branch into root `main` after confirming the unsupported-category ruleset metadata now uses `severity_on_fail: unknown`.
- Resolved merge conflicts only in append-only state logs; no Lane C implementation logic was changed during conflict resolution.
- Verified the merged tree with targeted C-002/report/API tests, targeted ruff and mypy, full DB-gated PowerShell verification, and full test collection. Result: 250 tests collected and full DB-gated verification passes with lint clean and mypy clean (89 source files).
- Updated Lane D state and plan: C-002 is canonical, D-000 is the next Lane D task, and D-001 remains blocked until D-000 completes.

## 2026-06-04 (Session 1 C-002 not-evaluated rule categories)

- Implemented the Lane C-owned C-002 slice: added `backend/app/claims_engine/not_evaluated.py`, four unsupported-domain hard gates in `config/ruleset_homestead_mvp.yaml`, and rule-engine emission of deterministic `SeverityBand.UNKNOWN` claims from source-failure evidence for soil/septic, environmental hazard, resource context, and market context.
- Preserved the evidence-before-claim invariant: not-evaluated claims are generated only from source-failure evidence IDs; non-failure records for unsupported domains do not produce claims.
- Added `backend/tests/claims_engine/test_not_evaluated_claims.py` for ruleset declarations, helper-generated source-failure evidence, evidence-linked unknown claims, deterministic ordering, non-failure ignore behavior, and market-context safe language.
- Updated Lane C plan/state, project state, and task queue. C-002 is complete for Lane C claim/rule scope; Session 2/Lane D should wire report-run auto-creation/registration of unsupported-domain source-failure evidence in D-000 before D-001 completion.
- Verified before final rebase: Lane C claims tests pass with DB smoke enabled; report/API tests pass; full DB-gated backend pytest passes; direct DB smoke passes; targeted ruff/mypy pass; default PowerShell verification passes.

## 2026-06-04 (Session 2 C-002 handoff risk check)

- Rechecked root `main`, Session 1's worktree, and the Session 1 log before advancing Lane D. Root `main` remained clean and did not contain C-002 at the time of the check.
- Found Session 1's C-002 worktree still in a detached rebase state with unresolved conflict markers in `state/VALIDATION_LOG.md`.
- Read-only validation of the draft C-002 branch found the emitted not-evaluated claims were UNKNOWN, but the four unsupported-category ruleset entries and unit test still declared `severity_on_fail: informational`.
- Sent Session 1 a coordination note because D-000 depends on a canonical C-002 handoff whose claim behavior and ruleset metadata both use UNKNOWN for unsupported categories.
- Non-mutating merge simulation showed the C-002 branch conflicted with root `main` only in state files; no report/API code conflicts were identified.

## 2026-06-04 (Session 2 API unknown surfacing regression)

- Added a Lane D API regression proving `POST /report-runs` surfaces `SeverityBand.UNKNOWN` claims generated from stored source-failure evidence in the response `unknowns` list and cost metrics.
- This does not implement D-000 unsupported-category injection before C-002; it hardens the existing report/API behavior D-000 will rely on after Lane C emits unsupported-category unknown claims.
- Verified focused API checks: 8 API tests pass; targeted ruff and mypy pass.
- Verified Lane D checks: 18 report/API tests pass with DB smoke enabled.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 244 tests; lint clean; mypy clean (87 source files); migrations/seeds and DB smoke pass.

## 2026-06-04 (Session 2 Lane D boundary split + DB session pre-work)

- Resolved the C-002 report-surfacing ownership conflict in planning/coordination docs: Lane C owns unsupported-category claim/rule behavior; Lane D owns report/API surfacing as D-000 after C-002.
- Corrected the C-002 spec so unsupported-category rules use `unknown` severity, not `informational`, preserving report unknowns and the source-failure pattern.
- Added `backend/app/db/session.py` with `get_db_session()` delegating to the shared `get_session()` engine/session factory path.
- Added `backend/tests/api/test_db_session.py` to verify `get_db_session()` delegates without creating a new engine or requiring a live DB.
- Verified Lane D targeted checks: 17 report/API tests pass with DB smoke enabled; targeted ruff and mypy pass.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 243 tests; lint clean; mypy clean (87 source files); migrations/seeds and DB smoke pass.
- Re-audit note: D-001 pre-work is partially complete, but full DB-backed API wiring remains blocked until Lane C C-002 and Lane D D-000 are complete.

## 2026-06-04 (Session 1 C-001 ORM stabilization)

- Re-verified the C-001 handoff from the external session export against live repo state and found the full DB-smoke gate failed in the four DB-backed claim repository tests.
- Root cause: `ClaimModel` and dependent claim models declared ORM `ForeignKey(...)` constraints to cross-schema tables that were not all present in the active SQLAlchemy metadata, then claim/evidence links could flush before the parent claim row.
- Fixed `backend/app/claims_engine/models.py` so cross-schema DB FKs remain database-migration authority while the Lane C ORM maps those references as scalar UUID columns; internal `claims.claims` FKs remain for claim-local dependencies.
- Fixed `SqlAlchemyClaimRepository.add()` to flush the parent claim before adding claim/evidence links and verification tasks.
- Verified: failing claim DB test file passes (4 tests); Lane C evidence/claims tests pass (137 tests with DB smoke enabled); targeted ruff and mypy pass; Lane C import-isolation scan returns 0 matches; full collection reports 242 tests; `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1` passes with lint clean, mypy clean (85 source files), migrations/seeds, and DB smoke.
- Re-audit note: C-001 is now live-verified after repair; Level 6 remains partial until C-002 not-evaluated categories are implemented by Lane C and surfaced through Lane D without violating ownership boundaries.

## 2026-06-04 (C-001 Claims ORM models + coordination infra)

- Implemented C-001: created `backend/app/claims_engine/models.py` with `ClaimModel`, `ClaimEvidenceLinkModel`, and `VerificationTaskModel` (all inheriting `AppBase`). All three ORM models verified against `db/migrations/0001_initial_spine.sql`. `ClaimModel.claim_metadata` is mapped with Python attribute name to avoid `DeclarativeBase.metadata` collision (actual DB column name is `metadata`). `rule_execution_run_id` and `intent_id` nullable FKs are mapped but not yet populated by the current rule engine path.
- Refactored `SqlAlchemyClaimRepository` in `claim_repo.py` from raw `text()` SQL to SQLAlchemy 2.x ORM (`session.add()`, `session.get()`, `select()`). All raw SQL and `_row_to_claim()`/`_claim_params()`/`_select_claim_statement()` helpers replaced by ORM equivalents. `_claim_metadata()`, `_metadata_evidence_ids()`, `_validate_claim_for_persistence()`, and `_verification_priority()` preserved unchanged.
- Updated `state/lane-c-state.md` and `state/lane-d-state.md` with C-001/C-002/D-001 as explicit next tasks.
- Created `CODEX_PARALLEL.md` — parallel session coordination protocol with file ownership map, pre-condition checks, and safe parallel execution rules.
- Updated `PROMPT_LANE_*.md` files to reflect current done/pending state for all four lanes.
- Updated `tasks/task_queue.yaml` — all T000-T060 now `done`; C-001 `pending`, C-002/D-001 `blocked`.
- Updated `LANE_OWNERSHIP.md` — added `db/base.py`, `db/types.py`, `validate_workspace.ps1`, `verify.ps1`, and `CODEX_PARALLEL.md` to the Shared Interface Zone.
- Verified: 201 tests pass; structural invariants ok; lint clean; mypy clean (85 source files).

## 2026-06-03 (non-fragility audit + invariant enforcement)

- Found and fixed critical non-negotiable violation: `forbidden_language` block in `ruleset_homestead_mvp.yaml` was silently discarded by the hand-rolled YAML parser (section != "hard_gates" guard). Fixed: parser now loads the 6 forbidden phrases into `RuleSet.forbidden_language`; `RuleEngine._check_forbidden_language()` raises `ValueError` if any generated claim contains a forbidden phrase. 7 tests added in `test_forbidden_language.py`.
- Fixed fragile `_unknown_claims` filter in `service.py`: replaced `"UNKNOWN" in claim.claim_code` substring scan with `claim.severity == SeverityBand.UNKNOWN` (the correct and complete signal).
- Added `intent_code_enum` to `db/types.py` — closes the gap for future ORM models against `core.intents` or `reports.report_runs`. Added explanatory comment for `area_type_enum` (the one known exception, pending coordinated migration).
- Added AGENTS.md non-negotiable: no agent name, model name, or AI attribution in any file or commit message.
- Removed `Author: Claude (ralplan)` tag from `plans/2026-06-03-repo-audit-and-forward-options.md`.
- Rewrote all session commit messages to remove `Co-Authored-By:` trailers (17 local commits; no remote push affected).
- Added 3 structural invariant checks to `scripts/validate_workspace.ps1` (runs as part of `verify.ps1`):
  1. Exactly 1 `DeclarativeBase` subclass in `backend/app/` (prevents ORM base fragmentation)
  2. Zero `.query(` calls in `backend/app/` (prevents SQLAlchemy 1.x API regression)
  3. No `noreply@anthropic` in tracked `.py` or `.sql` files (prevents agent attribution leakage)
- Verified: 201 tests pass (non-DB); 84 source files mypy-clean; ruff clean; structural invariants pass.

## 2026-06-03 (pre-Codex structural hardening — ralplan A-minus + deep re-audit)

**Initial hardening (commit group 99cde91–3d5a9fd):**
- Committed all 49 uncommitted files in 9 logical groups (CI scripts, Lane A provenance, Lane B area models, Lane C evidence/claim models, Lane D report persistence, ADRs, agent docs, state/plans, archive cleanup).
- Created `backend/app/db/base.py` with single `AppBase(DeclarativeBase)` + MetaData naming_convention for Alembic readiness.
- Created `backend/app/db/types.py` with canonical `authority_level_enum`, `confidence_band_enum`, `job_status_enum` (one definition each, `create_type=False`).
- Updated all 4 ORM model modules (source_registry, area_geometry, evidence_ledger, reports) to inherit from `AppBase`; removed duplicate enum declarations; backward-compat aliases preserved.
- Fixed 3 legacy `.query()` sites in `source_registry/provenance_repo.py` → SQLAlchemy 2.x `select()` style.
- Added `IntentCode(StrEnum)` to `domain/enums.py` with 9 values matching `core.intent_code` SQL enum exactly.
- Constrained `ReportRunContract.intent_code` to `IntentCode`; updated API and service signatures.
- Fixed `SqlAlchemyReportRunRepository._contract_to_model()` which was silently dropping `intent_id` (setting it NULL); added `_resolve_intent_id()` that looks up `core.intents` by `intent_code`.
- Added DB assertion to `test_report_repository.py` verifying `intent_id` is NOT NULL after round-trip.

**Deep re-audit (commits 4f4c0ca, 714a07b):**
- Discovered that the global `mypy` used by `verify.ps1` catches errors that `python -m mypy` misses. Fixed 6 pre-existing type errors in report test files (string literals passed where `IntentCode` is required).
- Audited the Codex task spec (`plans/2026-06-03-codex-deferred-tasks.md`) against the actual migration SQL and found 3 blocking schema errors:
  - `claims.claims`: spec listed `is_negative`/`is_unknown`/`needs_review` (not in DB); omitted `rule_execution_run_id` and `intent_id` (are in DB).
  - `claims.claim_evidence`: spec had `evidence_order int` (not in DB); actual column is `support_role text`.
  - `claims.verification_tasks`: spec showed 3-column stub; actual table has 12 columns.
- Added `severity_band_enum` to `backend/app/db/types.py` (pre-completes the structural prerequisite for C-001 ORM models; all 4 canonical DB ENUMs are now in `db/types.py`).
- Corrected C-002 design: the `evidence_ids` non-empty invariant blocks naive not-evaluated claims; updated spec to use sentinel source failure evidence approach (creates SOURCE_FAILURE evidence records for each missing domain, then the rule engine emits UNKNOWN claims from them — preserves evidence-before-claim invariant).
- Corrected D-001 design: removed `build_engine()`-per-request anti-pattern (destroys connection pooling); delegated to existing `get_session()` singleton from `engine.py`. Added `main.py` to required change list.
- Made C-002 severity choice definitive: not-evaluated claims use `SeverityBand.UNKNOWN` (consistent with all other "source not available" claims; ensures they appear in `ReportRunContract.unknowns`).
- Verified: 235 tests pass; `ruff check` clean; global `mypy` clean (83 source files including tests).

## 2026-06-04 (Lane C DB-backed claim persistence)

- Completed Lane C TC-150 by adding `SqlAlchemyClaimRepository` for `claims.claims`, DB-backed claim/evidence links in `claims.claim_evidence`, and verification-task persistence in `claims.verification_tasks`.
- Preserved rule metadata and evidence ordering in `claims.claims.metadata` until a coordinated schema migration promotes those fields.
- Added DB-gated tests for durable claim round-trip, evidence-link rows, verification-task rows, unknown/source-failure claim persistence, duplicate claim rejection, and rollback behavior.
- Added `docs/adr/lane-c-rules.md` to document deterministic rules, claim persistence, evidence links, rule version metadata, verification tasks, hard gates before scoring, and deferred suitability scoring.
- Verified Lane C targeted checks: 130 tests pass with `RUN_DB_SMOKE=1`; targeted ruff and mypy pass; cross-lane import scan returns 0 matches.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 235 tests; lint clean; mypy clean (81 source files); DB smoke passes.
- Re-audit note: Level 6 remains partial until missing rule categories are implemented or explicitly labeled as not evaluated.

## 2026-06-04 (Lane C evidence geometry/spatial precision + automation guardrails)

- Removed the remaining live automatic-execution reference from `CLAUDE.md`; active automation sweeps now return 0 matches, the Claude/Codex automatic config paths are absent, and `local_artifacts/psql.cmd` remains present.
- Updated `AGENTS.md` and repo-local Claude debug/validation skills so Windows verification points to PowerShell wrappers instead of `.sh` commands.
- Completed Lane C TC-140 by adding optional GeoJSON/SRID/spatial precision fields to `EvidenceContract`, mapping geometry to `evidence.observations.geometry`, and preserving spatial precision in evidence metadata.
- Added `docs/adr/lane-c-evidence.md` to document evidence persistence, immutability, supersession/amendment, audit events, geometry mapping, and source-failure treatment.
- Verified Lane C targeted checks: 126 tests pass with `RUN_DB_SMOKE=1`; targeted ruff and mypy pass; cross-lane import scan returns 0 matches.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 231 tests; lint clean; mypy clean (80 source files); DB smoke passes.
- Re-audit note: Level 5 now passes for the fixture-backed DB evidence-ledger path; next dependency is Level 6 durable claim/claim-evidence persistence.

## 2026-06-04 (Lane C DB-backed evidence repository and audit log)

- Completed Lane C TC-130 by adding `SqlAlchemyEvidenceRepository` for `evidence.observations` and `SqlAlchemyEvidenceAuditLog` for evidence events in `audit.events`.
- Preserved contract-only evidence fields in observation metadata: `source_id`, `evidence_code`, `observed_at`, and `superseded_by`.
- Added DB-gated tests for source observation, source failure, spatial intersection, derived metric, document extract, human verification, invalid payload rejection, supersession, retrieval by area/source/type, rollback behavior, and durable audit events.
- Verified Lane C targeted checks: 122 tests pass with `RUN_DB_SMOKE=1`; targeted ruff and mypy pass; cross-lane import scan returns 0 matches.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 227 tests collected; lint clean; mypy clean (80 source files); DB smoke passes.
- Re-audit note: Level 5 remains partial until `EvidenceContract` exposes geometry/SRID/spatial-precision fields and maps them into `evidence.observations.geometry`.

## 2026-06-04 (Lane B supported domain area-type mapping)

- Completed Lane B TB-090 by preserving exact domain area type in `core.areas.metadata.domain_area_type`.
- Mapped `multi_polygon` to DB bucket `polygon` and `buffer` to DB bucket `generated_candidate`, while keeping reads fail-closed if metadata conflicts with stored DB area type.
- Added DB-gated tests for all six Level 4 domain area types and conflicting metadata rejection.
- Verified Lane B targeted checks: 46 tests pass with `RUN_DB_SMOKE=1`; `ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes; `mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 216 tests collected; lint clean; mypy clean (78 source files); DB smoke passes.
- Re-audit note: Level 4 now passes for the current fixture-backed DB repository path; next dependency is Lane C durable evidence-ledger/audit persistence.

## 2026-06-04 (Lane B DB-backed area versioning)

- Completed Lane B TB-080 for the current repository path by adding `AreaVersionContract`, `AreaVersionModel`, `SqlAlchemyAreaRepository.replace_geometry`, and `SqlAlchemyAreaRepository.list_versions`.
- Added DB-gated tests for immutable prior-geometry storage in `core.area_versions`, version number sequencing, missing-area no-op behavior, invalid replacement rejection, and rollback behavior.
- Verified Lane B targeted checks: 41 tests pass with `RUN_DB_SMOKE=1`; `ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes; `mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 211 tests collected; lint clean; mypy clean (78 source files); DB smoke passes.
- Re-audit note: superseded by TB-090, which resolves the `multi_polygon`/`buffer` domain-to-DB area-type alignment for the current repository path.

## 2026-06-04 (Lane B DB-backed spatial relation helper)

- Completed Lane B TB-070 by adding `AreaSpatialRelationContract` and `SqlAlchemyAreaRepository.get_spatial_relation`.
- Added DB-gated tests for contained, disjoint, missing-area, wrong-SRID, empty-geometry, and unsupported-geometry-type comparison behavior.
- Verified Lane B targeted checks: 35 tests pass with `RUN_DB_SMOKE=1`; `ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes; `mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 205 tests collected; lint clean; mypy clean (78 source files); DB smoke passes.

## 2026-06-04 (Lane B DB-backed area metrics)

- Completed Lane B TB-060 by adding `AreaMetricsContract` and `SqlAlchemyAreaRepository.get_metrics`.
- Added DB-gated tests for PostGIS-derived geodesic area, centroid, bbox, SRID, and measurement caveats for Polygon and MultiPolygon fixtures.
- Verified Lane B targeted checks: 27 tests pass with `RUN_DB_SMOKE=1`; `ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes; `mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 197 tests collected; lint clean; mypy clean (78 source files); DB smoke passes.

## 2026-06-04 (Lane B DB-backed area repository)

- Completed Lane B TB-050 by adding `AreaModel` for `core.areas` and `SqlAlchemyAreaRepository` for PostGIS-backed area persistence.
- Added DB-gated tests for Polygon and MultiPolygon round-trips, service integration, existence/list behavior, SRID 4326 persistence, source/confidence/validated field round-trips, and fail-closed domain/DB area-type mismatches.
- Verified Lane B targeted checks: 22 tests pass with `RUN_DB_SMOKE=1`; `ruff check app/area_geometry tests/area_geometry` passes; `mypy app/area_geometry tests/area_geometry` passes.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 192 tests collected; lint clean; mypy clean (78 source files); DB smoke passes.

## 2026-06-04 (source governance and DB verification hardening)

- Hardened `SourceService.source_production_use_allowed` so production evidence requires reviewed license, commercial, redistribution, cache, export, raw-data, and AI-use rights.
- Added regression tests for blocked/unknown source usage-right dimensions and updated report/provenance fixtures to model fully reviewed sources.
- Strengthened `db_smoke_check.py` from schema/source-count checks to schema, table, column, enum, foreign-key, source seed, and intent seed assertions.
- Added a PostGIS-backed GitHub Actions `db-verify` job and Python 3.12 selection/version checks for verification scripts.
- Corrected Windows DB-smoke command snippets and demoted Lane D state wording to a partial report-run harness rather than full Level 7 PASS.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: Python 3.12.10 selected; 186 tests pass; ruff clean; mypy clean; migrations/seeds and stronger DB smoke pass.

## 2026-06-04 (Session 2 D-001 DB-backed API workflow)

- Completed Lane D D-001 from clean root `main` without touching Session 1's Lane A or Lane B worktrees.
- Added explicit DB API mode through `create_app(use_db_services=True)`, preserving default in-memory API services for fast fixture tests.
- Wired request-scoped SQLAlchemy-backed source, area, evidence, claim, and report services in `backend/app/api/dependencies.py`; successful DB requests commit and failed requests roll back.
- Added DB-backed API integration coverage for `POST /areas`, `POST /report-runs`, `GET /report-runs/{id}`, persisted `reports.report_runs` row, non-null seeded `intent_id`, unsupported-category UNKNOWN claims, and report artifact path.
- Hardened Lane D's internal unsupported-category sentinel lookup to use a stable source UUID instead of scanning all source rows. This avoids coupling report generation to Lane A source-row URL normalization while keeping the change inside Lane D-owned report code.
- Verified targeted Lane D/API checks with DB smoke enabled before full workspace verification.

## 2026-06-04 (Session 2 D-002 report artifact regression)

- Created `plans/2026-06-04-l7-closeout-l8-entry.md` to sequence Level 7 closeout and Level 8 entry without prematurely editing shared schemas or Lane A/B/C implementation files.
- Added `backend/tests/reports/test_report_regression.py`, a normalized fixture report regression that asserts stable generated report semantics while ignoring dynamic UUID, timestamp, and path fields.
- Kept Session 2 work away from Session 1's active Lane B coordinate-validation branch and away from Lane A/C implementation surfaces.
- Set the next Session 2 task to a schema-contract alignment note before any `schemas/*.json` changes or Level 8 connector implementation.

## 2026-06-04 (Session 2 D-003 schema-contract alignment)

- Audited active shared schemas against current source, evidence, claim, and report domain contracts without editing schema files.
- Recorded schema gaps and future lane owners in `plans/2026-06-04-l7-closeout-l8-entry.md`.
- Identified that `schemas/evidence_schema.json` still reflects older geometry/timestamp fields, `schemas/claim_schema.json` requires fields not in the current claim contract and omits ruleset metadata, and no active report-run schema exists yet.
- Preserved shared-schema ownership boundaries: Lane A for source schema, Lane C for evidence/claim schemas, Lane D for report schema proposal, and coordinator review for cross-lane composition.
- Set the next task to Level 8 ownership and fixture-only connector acceptance planning before connector runtime code.

## 2026-06-03 (Windows PowerShell verification wrapper)

- Added PowerShell-native wrappers for verification, workspace validation, DB migration application, and bootstrap so Windows users can avoid launching Git Bash.
- Updated README, AGENTS, testing docs, prompt template, and current state blocks to point Windows usage at `.\scripts\verify.ps1`.
- Verified `.\scripts\verify.ps1` with `RUN_DB_SMOKE=1`: 179 tests pass; ruff clean; mypy clean (76 source files); DB smoke passes through the local `psql` shim.

## 2026-06-03 (Lane D persisted report runs)

- Completed Lane D TD-040 by adding the `reports.report_runs` ORM model, the SQLAlchemy report-run repository, a machine-readable artifact round-trip, and a DB-backed persistence test.
- `verify.sh` now passes with DB smoke enabled: 173 tests pass; ruff clean; mypy clean (72 source files).
- Updated Lane D plan/state/validation docs and recorded the persistence decision in `docs/adr/lane-d-0001-report-persistence.md`.

## 2026-06-03 (scaffold validation alignment)

- Added `.gitignore` entry for the nested `001-audit/` audit worktree so root status no longer presents it as a candidate repo artifact.
- Added minimal scaffold tests for Lane B area contract defaults, Lane D report contract defaults, and API health scaffold.
- Corrected Lane B and Lane D state evidence so documented lane-specific verification commands now match runnable tests.
- `verify.sh` passes via Git Bash: 22 tests pass; ruff clean; mypy clean (44 source files); DB smoke skipped.
- Anchored local `main` to `origin/main` and created local baseline commit `ffb73e1` (`Establish governed scaffold baseline`); no push performed.
- Completed Lane A TA-010 by archiving backward-compat shims from `backend/app/repositories/` and `backend/app/services/` into `archive/2026-06-03_source-registry-lane-migration/backend/app/`.
- `verify.sh` passes after TA-010: 22 tests pass; ruff clean; mypy clean (40 active source files); DB smoke skipped.
- Completed Lane A TA-020 by adding `SourceModel` for `source.sources` plus model contract tests. `verify.sh` passes: 26 tests pass; ruff clean; mypy clean (42 source files); DB smoke skipped.
- Completed Lane A TA-030 by adding `SqlAlchemySourceRepository` plus non-DB repository tests. `verify.sh` passes: 30 tests pass; ruff clean; mypy clean (43 source files); DB smoke skipped.
- Completed Lane A TA-040 by adding registry-backed source seed loading, a seed runner, seed tests, and metadata persistence mapping. Lane A tests pass: 23 tests; seed dry-run validates 8 `Must` rows.
- Completed Lane B TB-010 through TB-040 for the in-memory fixture slice: AreaService, InMemoryAreaRepository, GeoJSON/SRID validator, geometry fixtures, and service/validator tests. Lane B tests pass: 16 tests.
- `verify.sh` passes via Git Bash after TA-040 and Lane B fixture slice: 49 tests pass; ruff clean; mypy clean (48 source files); DB smoke skipped.
- Completed Lane C TC-010 for the in-memory evidence slice: EvidenceService, InMemoryEvidenceRepository, source/area protocol validation, source-failure evidence, typed human notes, area/source/type retrieval, and duplicate evidence protection. Lane C tests pass: 16 tests.
- `verify.sh` passes via Git Bash after TC-010: 59 tests pass; ruff clean; mypy clean (51 source files); DB smoke skipped.
- Completed Lane A TA-050 by adding the source provenance/license ADR, strengthening the canonical data-source license review template, wiring explicit governance fields through the source register/schema/seed path, and adding fail-closed SourceService production-use checks. Lane A tests pass: 28 tests.
- `verify.sh` passes via Git Bash after TA-050: 64 collected tests; ruff clean; mypy clean (51 source files); DB smoke skipped.
- Completed Lane C TC-020 for the in-memory evidence slice: `superseded_by`, repository supersession marking, and service safeguards for same-area replacement, new evidence IDs, already-superseded originals, pre-superseded new records, and source-failure replacement. Lane C tests pass: 23 tests.
- `verify.sh` passes via Git Bash after TC-020: 71 collected tests; ruff clean; mypy clean (51 source files); DB smoke skipped.
- Completed Lane C TC-030 for the in-memory claim-service slice: `ClaimRepository`, `InMemoryClaimRepository`, and `ClaimService` with stored evidence-link validation, same-area enforcement, unknown claim generation from source-failure evidence, user-safe-language enforcement, and verification-task enforcement. Lane C tests pass: 35 tests.
- `verify.sh` passes via Git Bash after TC-030: 83 tests pass; ruff clean; mypy clean (54 source files); DB smoke skipped.
- Completed Lane C TC-040 for the first deterministic rule-engine slice: rule metadata on claims, constrained current-ruleset loading, deterministic flood hard-gate claims, source-failure unknown claims, low-risk no-claim output, empty input, multi-area grouping, simultaneous positive/failure output, input-order determinism, invalid severity rejection, and superseded-evidence exclusion. Lane C tests pass: 45 tests.
- `verify.sh` passes via Git Bash after TC-040: 93 tests pass; ruff clean; mypy clean (56 source files); DB smoke skipped.
- Completed Lane C TC-050 for the in-memory evidence payload-validation slice: type-specific `observed_value` validation for source observations, spatial intersections, derived metrics, document extracts, source failures, and human-note guardrails. Spatial validation accepts `flood_zone_code` results and bounds `intersection_ratio` to `0..1`. Lane C tests pass: 59 tests.
- `verify.sh` passes via Git Bash after TC-050: 107 tests pass; ruff clean; mypy clean (59 source files); DB smoke skipped.
- Completed Lane C TC-060 for the in-memory evidence audit-event slice: optional `EvidenceAuditLog` injection, `EvidenceAuditEvent`, `InMemoryEvidenceAuditLog`, and create/source-failure/human-note/supersede event tests. Lane C tests pass: 63 tests.
- `verify.sh` passes via Git Bash after TC-060: 111 tests pass; ruff clean; mypy clean (60 source files); DB smoke skipped.
- Completed Lane C TC-070 for the in-memory flood contradiction/stale rule slice: deterministic needs-review claims for conflicting active evidence and positive-plus-source-failure evidence, explicit `source_stale` fixture handling, superseded-evidence exclusion, and deterministic review-output ordering. Lane C tests pass: 69 tests.
- `verify.sh` passes via Git Bash after TC-070: 117 tests pass; ruff clean; mypy clean (60 source files); DB smoke skipped.
- Completed Lane D TD-020 for the in-memory API scaffold: per-app in-memory service wiring, source/area/evidence/report-run routers, router registration, and API tests for happy paths and representative 422 cases. Lane D tests pass: 7 tests.
- `verify.sh` passes via Git Bash after TD-020: 122 tests pass; ruff clean; mypy clean (65 source files); DB smoke skipped.
- Completed Lane D TD-030 for the in-memory report-run service: ReportRunService validates registered areas, gathers area evidence, runs the deterministic rule engine, stores evidence-linked claims through ClaimService, and returns report evidence, claims, unknowns, red flags, caveats, verification tasks, source manifest, and artifact metadata. Lane D tests pass: 11 tests.
- `verify.sh` passes via explicit Git Bash after TD-030: 126 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane C TC-080 for the access hard-gate fixture slice: deterministic `ACCESS_001`, access source-unavailable unknown, access needs-review, stale access review, safe legal-access language, and access adjacency payload validation. Lane C tests pass: 76 tests.
- `verify.sh` passes via explicit Git Bash after TC-080: 131 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane C TC-090 for the wetlands hard-gate fixture slice: deterministic `WETLAND_001`, wetland source-unavailable unknown, wetland needs-review, stale wetland review, screening-only/no-delineation language, and wetland fixture payload validation. Lane C tests pass: 83 tests.
- `verify.sh` passes via explicit Git Bash after TC-090: 138 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane C TC-100 for the slope/buildability hard-gate fixture slice: deterministic `SLOPE_001`, slope source-unavailable unknown, slope needs-review, stale slope review, screening-only/no-final-buildability language, and slope derived-metric payload validation. Lane C tests pass: 90 tests.
- `verify.sh` passes via explicit Git Bash after TC-100: 145 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane C TC-110 for the zoning/use hard-gate fixture slice: deterministic `ZONING_001`, zoning source-unavailable unknown, zoning needs-review for incomplete/mixed evidence, stale zoning review, screening-only/no-final-legal-use language, and zoning source-observation payload validation. Lane C tests pass: 100 tests.
- `verify.sh` passes via explicit Git Bash after TC-110: 157 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane C TC-120 for the water-context hard-gate fixture slice: deterministic `WATER_001`, water source-unavailable unknown, water needs-review for incomplete/mixed evidence including internally contradictory fixture records, stale water review, screening-only/no-water-rights/no-well-viability language, and water source-observation payload validation. Lane C tests pass: 111 tests.
- `verify.sh` passes via explicit Git Bash after TC-120: 168 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane D TD-050 for the in-memory protocol adapter wiring: added `SourceServiceProtocolAdapter` and `AreaServiceProtocolAdapter`, wired them into `EvidenceService` construction in the report pipeline, and added adapter-focused delegation/guardrail tests. Lane D tests pass: 15 tests.
- `verify.sh` passes via explicit Git Bash after TD-050: 172 tests pass; ruff clean; mypy clean (69 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.

## 2026-06-03 (repo bootstrap + local index)

- Ran `npx codesight --index`; local index written to `.codesight/`.
- Created `plans/2026-06-03-repo-bootstrap.md` for local-only GitHub bootstrap work.
- Aligned README and `manifest.json` with target repo `benjmcd/land-dd`.
- Corrected `tasks/task_queue.yaml` against canonical state: T010 blocked on Docker, T020 done, lane plans listed for implementation routing.
- Initialized local Git on `main` and set `origin` to `https://github.com/benjmcd/land-dd.git`; no commit or push performed.
- `verify.sh` passes via Git Bash: 19 tests pass; ruff clean; mypy clean (40 source files); DB smoke skipped.
- Added `.codesight/` to `.gitignore` and `MANIFEST.md` generated-artifact policy.
- Added `PROMPT_FOR_ISOLATED_LANE_AGENT.md` for parallel lane agents, with local-only, no-shared-checkout, lane-ownership, and stop-condition rules.
- Strengthened isolated-lane prompt with no-baseline-commit isolation guidance, Windows/Git Bash command notes, test-first work protocol, tech-debt controls, shared-log conflict handling, and stricter definition of done.

## 2026-06-03 (session 3 — lane scaffold)

- Installed `psycopg[binary]`, `pytest-cov`, `types-PyYAML` (from pyproject.toml dev deps).
- Fixed `engine.py` to use deferred/lazy initialization (prevents module-import DB connection).
- Split `backend/app/domain/contracts.py` into per-lane contract files:
  - `source_contracts.py` (Lane A), `area_contracts.py` (Lane B),
    `evidence_contracts.py` (Lane C), `claim_contracts.py` (Lane C), `report_contracts.py` (Lane D)
- Added `protocols.py` (shared: SourceExistsProtocol, AreaExistsProtocol).
- Extended `enums.py`: added EvidenceType, AreaType, JobStatus.
- Migrated source_repo + source_service into `backend/app/source_registry/`.
  Old `repositories/` and `services/` are now backward-compat shims (Lane A archives to `archive/` once no imports remain).
- Split `test_domain_contracts.py` and `test_source_service.py` into per-lane test directories.
- Created lane module directories: source_registry/, area_geometry/, evidence_ledger/, claims_engine/, reports/.
- Created lane test directories: tests/source_registry/, tests/area_geometry/, tests/evidence_ledger/, tests/claims_engine/, tests/reports/.
- Created per-lane operating contracts: lanes/lane-{a,b,c,d}/AGENTS.md + CLAUDE.md.
- Created per-lane plans: plans/lane-{a,b,c,d}-2026-06-03-*.md.
- Created per-lane state files: state/lane-{a,b,c,d}-state.md.
- Created LANE_OWNERSHIP.md (canonical isolation map).
- Created db/migrations/MIGRATION_REGISTRY.md.
- Updated MANIFEST.md, state/PROJECT_STATE.md (MILESTONE_MAP status block added).
- verify.sh: 19 tests pass; lint clean; mypy clean (40 source files).

## 2026-06-03 (session 2)

- Fixed 3 baseline lint errors (`config.py` E501, `contracts.py` UP017/UP037).
- Installed mypy in Python 3.11 environment; `verify.sh` typecheck step now executes.
- T010 (DB smoke) blocked: Docker Desktop not running. Recorded blocker in VALIDATION_LOG.
- T020 completed: added source registry repository/service layer.
  - `backend/app/repositories/source_repo.py`: `SourceRepository` Protocol + `InMemorySourceRepository`.
  - `backend/app/services/source_service.py`: `SourceService` with dedup enforcement.
  - `backend/tests/test_source_service.py`: 8 fixture-backed tests, all passing.
- `verify.sh` passes: 14 tests, lint clean, mypy clean.

## 2026-06-03 (initial)

- Created dual-agent workspace structure for Codex and Claude Code.
- Added thin `AGENTS.md`, `CLAUDE.md` importer, `MANIFEST.md`, plans, skills, subagents, CI, and validation scripts.
- Preserved comprehensive planning pack under `docs/planning_pack/` as reference, not startup context.
