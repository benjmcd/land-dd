# EQ Phase 2 — Operationalize the Empirical-Qualification Control Plane

> **Self-contained delegated handoff.** Execute against `origin/main` without further steering.
> Read this whole file + the canonical sources before starting. If anything here conflicts
> with live `origin/main`, **live `origin/main` wins** — reconcile first.

## FIRST ACTION — set the session goal

Set your session goal (use your goal function / `/goal`) to:

> **Operationalize the empirical-qualification control plane: make qualification status
> executable and drift-proof (derived from the crosswalk + real checker results), make
> change-impact invalidation executable, and collect repo-local evidence for the
> auto-verifiable P0 invariants — all while remaining honestly `P0 = BLOCKED`, with no gate
> moved to PASS and no owner-decision unfrozen.**

Mid-to-long-term milestone, 4 bottom-up lanes (EQP2-1 … EQP2-4), one PR each.

---

## Why this milestone (grounding)

Phase 1 (EQ-1…EQ-5, merged through `origin/main@8dadfbf`) landed a **static, self-validating
spine**: `validate_qualification.py` (17 checks), `selftest_qualification_validator.py`
(12 fail-closed mutations), the catalog (392 criteria), the readiness crosswalk
(surface→criterion mapping with `evidence_role`), the change-impact matrix, and a
hand-authored `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` at honest `P0 = BLOCKED`.

But the control plane is **declared, not executed**:
- The crosswalk *documents* surface→criterion mappings; nothing *derives* status from real
  checker results, so status is hand-maintained and can silently drift.
- The change-impact matrix *lists* invalidation; nothing *applies* it to an actual diff.
- The auto-verifiable P0 invariants (test-suppression ban, evidence-linkage) are declared
  BLOCKED but no repo-local evidence is *collected* for them.

Phase 2 turns the paperwork into enforcement — without crossing the P0-freeze line.

---

## Handoff contract

- **Objective:** Qualification status is **derived and drift-proof** (computed from the
  crosswalk + real checker exit results, asserted equal to the committed status file);
  change-impact invalidation is **executable** against a diff; repo-local evidence is
  **collected** for the auto-verifiable P0 invariants — with the gate honestly staying
  `BLOCKED` throughout.
- **Scope fence:** Only lanes EQP2-1…EQP2-4 below, all within the qualification subsystem
  plus extending the existing readiness/authority checkers to *report into* qualification
  (per ADR 0004). New checker scripts + wrappers; extensions to `validate_qualification.py`
  / `selftest_qualification_validator.py`; status/backlog updates; verify wiring; tests.
- **Non-goals (do NOT do):**
  - Do **not** move any gate/overlay/criterion to `PASS`. Status values stay in
    `{BLOCKED, NOT_RUN}`. P0 stays `BLOCKED` (the validator's P0-freeze rule must keep
    holding — do not weaken it).
  - Do **not** unfreeze or fill any owner-decision (targets/profiles/rubrics/reviewers/
    candidate identity). `candidate.*` stays null; `source_profile_ids` stays empty;
    domain profiles stay template-only; target registry stays DRAFT.
  - Do **not** land Q3A/B/C or AI/CG/FIN/E rubrics/targets. Catalog entries only.
  - Do **not** change DB schema, public API, auth boundaries, or report semantics.
  - Do **not** auto-load `EMPIRICAL_QUALIFICATION_FRAMEWORK.md` into agent context.
  - Do **not** delete files (archive to `archive/<YYYY-MM-DD>_<reason>/`).
  - Do **not** add a new *runtime/product* dependency. `jsonschema`/`PyYAML` already adopted.
- **Boundaries & safety / ISOLATION (critical — a parallel Claude lane is running):**
  - **You OWN and may edit:** `config/qualification/**`, `schemas/qualification/**`,
    `scripts/validate_qualification.py`, `scripts/selftest_qualification_validator.py`,
    any new `scripts/qualification_*` scripts + their wrappers,
    `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`,
    `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md`, `docs/qualification/**`, and — for
    EQP2-4 only — `scripts/release_readiness_check.py`, `scripts/readiness_matrix_check.py`
    and sibling authority/readiness checkers (to make them *report* their criterion IDs).
  - **You OWN all shared state/control files:** `state/PROJECT_STATE.md`,
    `state/WORKLOG.md`, `state/VALIDATION_LOG.md`, `tasks/task_queue.yaml`, `MANIFEST.md`,
    `plans/README.md`, `state/LEVEL_9_10_GATE_MATRIX.md`,
    `state/residual-reconciliation.md`. The parallel lane will NOT touch these.
  - **Do NOT touch (parallel Claude lane / out of scope):** `backend/app/api/ui.py`; the
    DEFER product modules `backend/app/{dossier_readiness,product_correctness,production_authority,expansion_readiness,selected_geography_coverage}.py`
    and their tests; any `defer/*` branch; and **do not create, remove, or prune git
    worktrees other than your own `worktrees/eqp2-*`** — a parallel lane is cleaning stale
    worktrees and will avoid yours.
  - Do **not** revive or add ad-hoc product/guardrail modules. The goal is to *subordinate*
    existing checks to the catalog, not to add new parallel guardrails (that would
    contradict ADR 0004's consolidation).
  - Create worktrees only under `worktrees/eqp2-<short>` off `origin/main`. Ask before
    acting outside the repo.
- **Canonical sources of truth (read first):** `origin/main` HEAD; `AGENTS.md`;
  `docs/adr/0004-empirical-qualification-control-plane.md`;
  `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`; `config/qualification/readiness_crosswalk.yaml`;
  `config/qualification/change_impact_matrix.yaml`; `config/qualification/criterion_catalog.yaml`;
  `scripts/validate_qualification.py`; this plan.
- **Isolation:** one branch+worktree per lane: `eqp2/<lane>` under `worktrees/eqp2-<lane>`
  off `origin/main`. Confirm no other session owns the branch before starting.
- **Done-criteria:** per lane below. Milestone done = EQP2-1…EQP2-4 merged; `verify`
  green (selftest+validator run inside it); status remains honest `P0 = BLOCKED`; status is
  now derived+asserted; invalidation is executable; auto-verifiable invariants carry
  collected repo-local evidence while still BLOCKED.
- **Verification:** each lane PR reviewed by a **separate** lane (not self-approval); use
  the read-only reviewers (`code-reviewer`/`data-governance-reviewer`). CI `verify`+
  `db-verify` green before merge; post-merge detached `verify` proof; remove the worktree.
- **Constraints:** smallest correct change per slice; bottom-up; no file deletion; **no
  AI/agent/model attribution in files, commits, or branch names**; author
  `plans/2026-06-21-eqp2-<lane>-<slug>.md` (`.agent/PLANS.md` format) before implementing;
  update `state/PROJECT_STATE.md`/`WORKLOG.md`/`VALIDATION_LOG.md`.

---

## Embedded facts (from the landed spine — do not re-derive)

- **Validator** `scripts/validate_qualification.py` already runs 17 checks incl.
  `validate_catalog` (framework↔catalog SHA + ID parity), `validate_readiness_crosswalk`
  (crosswalk IDs + required globs + inventory parity), `validate_change_impact_matrix`
  (`invalidate_by_default` IDs are catalog criteria), `validate_result`/`validate_result_records`
  (PASS cannot omit/contain-FAIL; P0-freeze: "P0 cannot PASS while qualification targets are
  not FROZEN"), `validate_active_parameterization` (no null/TBD in frozen fields). CLI:
  `--root --layout {auto,bundle,repo} --targets --status --rubrics`.
- **Selftest** proves 12 mutations fail closed (incl. drift, bad change-impact/crosswalk IDs,
  N/A of an applicable INVARIANT, PASS omitting criteria, P0 PASS with DRAFT targets).
- **Crosswalk** `readiness_crosswalk.yaml`: `entries[]` each
  `{surface_id, surface_type, config_paths[], checker_paths[], criterion_ids[], evidence_role, notes}`;
  `evidence_role` ∈ {`feeds_status`, `deployment_gate`, …}. `inventory.{config_globs,checker_globs,intentional_exclusions}`.
- **Status** `EMPIRICAL_QUALIFICATION_STATUS.yaml` (`empirical_qualification_status_v3`):
  `qualifications.{p0,q1,q2,q3a,q3b,q3c}.{status,prerequisites,result_path,expires_at,blocked_reason,blocker_references}`;
  `overlays.*` and `conditional_overlays.*.{status,applicable,…}`; `candidate.*` all null;
  `highest_valid_classification: L9-R`; P0 `status: BLOCKED`.
- **Change-impact** `change_impact_matrix.yaml` (`qualification_change_impact_v3`):
  `change_classes.<CLASS>.{review[], invalidate_by_default[], conditional[], examples[]}`.
- **P0 auto-verifiable invariants** (repo-local, no owner judgment): **P0-021** test-suppression
  prohibition, **P0-023** evidence-linkage requirement, **P0-004** sealed-acceptance isolation,
  **P0-005** anti-contamination. (PROFILE_REQUIRED P0-001/002/003/006/007/008 need owner freeze.)
- **CI wiring:** selftest + validator are invoked inside `verify.ps1`/`verify.sh`
  (`== qualification selftest ==` then `== qualification validation ==`), which run in the
  `verify` + `db-verify` CI jobs. **There is no separate `qualification-selftest` CI job** —
  keep this pattern (add new checks as verify steps), and correct any prior wording that
  implied a standalone job.
- **Env:** `jsonschema` imports under `py -3.11` and CI's `backend[dev]` 3.12, not bare local
  `py -3.12`. Honor `PYTHON_BIN`/`LAND_DD_PYTHON_EXECUTABLE`.

---

## Lanes

### EQP2-1 — Derived, drift-proof status
**Goal:** status is computed, not hand-typed.
**Do:** add `scripts/qualification_status_check.py` (+ `.ps1`/`.sh` wrappers mirroring the
qualification validator wiring) that derives each gate/overlay's `status` from (a) the
catalog, (b) the crosswalk `evidence_role` mappings, and (c) the **exit results of the
mapped existing checkers** — then asserts the committed `EMPIRICAL_QUALIFICATION_STATUS.yaml`
matches the derived view (fail-closed on drift). Derivation must only ever produce
`BLOCKED`/`NOT_RUN` (never PASS); P0 stays BLOCKED. Wire as a `== qualification status ==`
step in `verify.ps1`/`verify.sh` after the validator. Extend the selftest with a drift case
(committed status ≠ derived → FAIL). 
**Done:** status check green in `verify`/CI; mutating the status file off the derived view
fails the selftest; P0 still BLOCKED.

### EQP2-2 — Executable change-impact invalidation
**Goal:** a change to a mapped path surfaces the criteria needing re-validation.
**Do:** add `scripts/qualification_change_impact_check.py` (+ wrappers) that takes a changed
-path set (default: `git diff --name-only origin/main...HEAD`) and reports, from
`change_impact_matrix.yaml` + `readiness_crosswalk.yaml`, which `change_classes` and
`criterion_ids` are implicated (review vs invalidate_by_default). Make it advisory
(prints + non-zero only on an internal inconsistency, not on "criteria affected"). Wire as
an informational step in `verify` and/or a CI step that comments the impacted criteria.
Extend the selftest: a known mapped-path change yields the expected criterion set.
**Done:** running it on a sample diff prints the correct implicated criteria; selftest proves
the mapping; no false gate.

### EQP2-3 — Repo-local evidence collection for auto-verifiable P0 invariants
**Goal:** collect (not claim) evidence for P0-021/P0-023/P0-004/P0-005.
**Do:** add evidence-collection for the four repo-local invariants — e.g. P0-021 scans for
skipped/xfail/disabled tests and CI suppressions; P0-023 verifies the evidence-linkage
manifest/harness exists; P0-004/P0-005 verify sealed-case/anti-contamination handling
records exist. Record gathered evidence pointers in a result/evidence artifact under
`state/` or `docs/qualification/` (your subsystem) referenced from the status file, but keep
each criterion's effective gate status **BLOCKED** (the P0 gate cannot pass until the
owner-frozen PROFILE_REQUIRED criteria are also satisfied). Update
`QUALIFICATION_PARAMETERIZATION_BACKLOG.md` to mark these four as "auto-evidenced;
still target-blocked." 
**Done:** evidence is collected + linked; the four invariants show gathered evidence yet
remain BLOCKED; validator/selftest still green; NO criterion is PASS.

### EQP2-4 — Subordinate the existing checkers (executable consolidation)
**Goal:** make ADR 0004's "readiness checks report INTO qualification" executable.
**Do:** have `release_readiness_check.py`, `readiness_matrix_check.py`, and the relevant
authority/readiness checkers emit/record their mapped `criterion_id`(s) (from the crosswalk)
in a machine-readable form, and have the EQP2-1 status check consume those as the
`feeds_status`/`deployment_gate` evidence inputs. No change to what those checks gate or
their pass/fail behavior — additive reporting only. Add a validator check that every
crosswalk `checker_paths` entry actually emits its declared criterion IDs (catch silent
drift between crosswalk and checkers). 
**Done:** each mapped checker advertises its criterion IDs; status derivation consumes them;
validator proves crosswalk↔checker advertisement parity; no gate behavior changed.

---

## Decision log
- 2026-06-21: Phase 2 = operationalize (derive status, executable invalidation, collect
  repo-local invariant evidence, subordinate checkers) without crossing P0-freeze. Lanes
  EQP2-1→EQP2-4. Strict no-PASS / no-unfreeze. Isolation fence vs the parallel Claude
  QA + worktree-cleanup lane and the DEFER product modules.

## Progress log
- 2026-06-21: Handoff authored off `origin/main@8dadfbf`. Awaiting session to set goal and
  begin EQP2-1.
