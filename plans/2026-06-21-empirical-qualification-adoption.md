# Empirical-Qualification Framework Adoption + Readiness-Governance Consolidation

> **This is a delegated, self-contained handoff.** It is written so the receiving session
> can execute every lane against `origin/main` without further steering. Read this whole
> file plus the canonical sources listed below before starting. If a fact here ever
> conflicts with live `origin/main`, **live `origin/main` wins** — reconcile first.

## FIRST ACTION — set the session goal

Before any other work, set your session goal (use your goal function / `/goal`) to:

> **Adopt the empirical-qualification framework as the canonical empirical-validity
> control plane for land-dd, and consolidate the repo's ad-hoc readiness/authority
> governance under it — landing the self-validating spine on `origin/main`, reporting an
> honest `P0 = BLOCKED`, without attempting any qualification PASS or unfreezing any
> owner-decision.**

This is a mid-to-long-term milestone (multiple PRs, bottom-up). The lanes below (EQ-1 …
EQ-5, plus parallel Lane R) decompose it. Keep this goal set until all non-deferred
done-criteria are met.

---

## Handoff contract (fill-every-field schema)

- **Objective:** The land-dd repo carries a *single, self-validating* empirical-validity
  control plane (vocabulary → criterion catalog → profiles → status), wired into CI and
  `verify`, reporting `P0 = BLOCKED` honestly; and the existing ad-hoc readiness/authority
  checkers are explicitly subordinated to it (one source of truth, not three).
- **Scope fence:** Only the lanes EQ-1…EQ-5 and Lane R below. Copying/adapting the spine
  subset of the framework package; writing one ADR; updating `AGENTS.md`/`MANIFEST.md`;
  wiring one CI gate + one `verify` step; authoring the status file at honest values;
  collapsing the 8 domain stubs to one template; a consolidation crosswalk; a
  parameterization-backlog tracking doc; and correcting one false claim in
  `state/residual-reconciliation.md`.
- **Non-goals (do NOT touch / do NOT do):**
  - Do **not** land the framework's expansion lanes `Q3A/Q3B/Q3C` (cross-state /
    restricted-source / non-US) docs, targets, or governance. Keep catalog entries only.
  - Do **not** land the conditional overlays `AI / CG / FIN / E` rubrics or targets (all
    are disabled features). Catalog entries only.
  - Do **not** attempt to move any gate to `PASS`. Do **not** unfreeze any owner-decision
    (deployment profile, source approvals, thresholds, personas, RPO/RTO, rubrics).
  - Do **not** auto-load the 1,514-line `EMPIRICAL_QUALIFICATION_FRAMEWORK.md` from agent
    context; land it as a referenced appendix only (its own `G-022` forbids auto-load).
  - Do **not** copy the 8 byte-identical domain-profile stubs (they are one template
    instantiated 8×, with flood references wrongly pasted into non-flood domains).
  - Do **not** introduce new *runtime/product* dependencies. `jsonschema`/`PyYAML` are
    validation tooling (dev), handled per EQ-2; flag if anything else is needed and STOP.
  - Do **not** change DB schema, public API, auth boundaries, or report semantics.
  - Do **not** delete files. Archive superseded artifacts to `archive/<YYYY-MM-DD>_<reason>/`.
- **Boundaries & safety:** Work only inside the land-dd repo. The framework source package
  at `C:\Users\benny\Downloads\land-dd_empirical_qualification` is **READ-ONLY input** —
  copy from it, never write to it. Create worktrees only under `<repo>/worktrees/<short>`
  off `origin/main`. One worktree+branch per lane. Ask before acting outside the repo.
- **Canonical sources of truth (read first, in order):**
  1. `origin/main` HEAD (`git rev-parse origin/main`) — the only product authority.
  2. `AGENTS.md` (non-negotiables, bottom-up build order, planning threshold).
  3. `state/PROJECT_STATE.md`, `MANIFEST.md`, `.agent/PLANS.md` (on `origin/main`).
  4. This plan file.
  5. The framework package (read-only) — especially `README.md`,
     `PROJECT_PARAMETERIZATION_BLOCKERS.md`, `VALIDATION_REPORT.md`,
     `ADVERSARIAL_REVIEW_FINDINGS.md`, `ARTIFACT_MANIFEST.json`.
  Distinguish authority (`origin/main`) from the local dirty root and from the package.
- **Isolation:** One branch+worktree per lane: `eq/<lane>` under
  `worktrees/eq-<lane>` off `origin/main`. Confirm no other active session owns the branch
  (`git worktree list`, recent `codex/*` activity, `state/agent-inbox/`) before starting a
  lane. Remove the worktree after the lane's PR merges.
- **Done-criteria:** Per-lane below. Milestone done = EQ-1…EQ-4 merged to `origin/main`,
  `verify` green, the qualification selftest green in CI, status file reports honest
  `P0 = BLOCKED`, and the consolidation boundary is documented and enforced. EQ-5 and
  Lane R are tracked but may complete in parallel.
- **Verification:** Each lane's PR is reviewed by a **separate** review lane (not the
  authoring lane self-approving). Use the repo's read-only reviewers
  (`code-reviewer` / `data-governance-reviewer` / `security-reviewer` as fits the lane).
  CI (`verify`, `db-verify`, plus the new `qualification-selftest` gate) must be green
  before merge. Post-merge: confirm on a detached `origin/main` checkout, then remove the
  worktree.
- **Constraints:** Smallest correct change per slice; bottom-up. No file deletion
  (archive instead). **No AI/agent/model authorship attribution** in any file or commit
  message — no `Co-Authored-By:`, no `Generated by:`, no agent/model names in files,
  commits, or branch names. Each lane: author a `plans/2026-06-21-eq-<lane>-<slug>.md`
  in the `.agent/PLANS.md` format before implementing, and update
  `state/PROJECT_STATE.md` / `state/WORKLOG.md` / `state/VALIDATION_LOG.md`. Current phase
  per lane starts at **plan**, then **implement** only after the lane plan exists.

---

## Background & grounding (verified, do not re-derive)

Two independent read-only audits produced this handoff. Their conclusions are evidence,
not assumptions:

**Audit A — dirty-root reconciliation (vs `origin/main` `cc54776`).** The local dirty root
(branch `codex/r026-raw-readiness-ui`, pinned at `c3364ea` = R-022, now ~71 commits behind
main) was classified file-by-file (120 files) and adversarially verified.
- The claim **`state/residual-reconciliation.md: "STILL_DIVERGENT: none"` is FALSE.**
  ~11 files are genuinely un-landed real product (adversarially confirmed, conf ≥0.98),
  all marked `DEFER` on main but **decaying** against a heavily-changed `main`
  (`backend/app/api/ui.py` route set diverged; readiness parsers reworked):
  `backend/app/dossier_readiness.py` (+test), `backend/app/product_correctness.py`
  (+test), `backend/app/production_authority.py` (+test), the UI tests
  `test_ui_expansion_readiness.py` / `test_ui_selected_geography_coverage.py`, and the
  local-deployment profile unit (`config/local_deployment.yaml`,
  `scripts/local_deployment_check.py`, `scripts/run_local_deployment_check.ps1/.sh`,
  `backend/tests/test_local_deployment_artifacts.py`).
- `expansion_readiness` and `selected_geography_coverage` **logic** already landed on main
  (recast as `checklist_dry_run` checker / `source_provenance`); only their app-module +
  UI surface is deferred. → Lane R addresses this falsehood.

**Audit B — empirical-qualification framework assessment.** Verdict: **ADAPT** (not adopt-
whole, not shelf). Grounds:
- It **self-validates**: `scripts/selftest_qualification_validator.py` passes 8/8
  adversarial mutations; the validator enforces real invariants (framework↔catalog ID
  parity, SHA-256 freshness, profile-cycle detection, controlled-term parity, the
  "PASS cannot contain FAIL rows / cannot omit applicable criteria / cannot N/A an
  applicable invariant" rules, and the P0-freeze invariant).
- Its **self-critique is honest** (ships `ADVERSARIAL_REVIEW_FINDINGS.md` 27 findings,
  caps itself at `L9-R`, lists every unfrozen decision in
  `PROJECT_PARAMETERIZATION_BLOCKERS.md`).
- `requirement_class` enum is consistent (schema = catalog =
  `INVARIANT/PROFILE_REQUIRED/TARGETED/JUDGMENT_RUBRIC/DIAGNOSTIC`; catalog uses
  210/89/81/11/1 = 392 contracts). **No schema↔catalog drift** (verified).
- **Top risk = governance multiplication.** The repo already runs *two* gate systems
  (`*_readiness.yaml` + `*_readiness_check.py`, and `state/LEVEL_9_10_GATE_MATRIX.md`),
  and recent history added many validate-only authority packets (Bologna ×7, DS-017, PAI).
  Adopting this as a *third* parallel truth would worsen the very confusion it prevents.
  → Adoption is only justified if it **consolidates** (EQ-1 + EQ-4): make the catalog the
  one canonical empirical-validity authority and subordinate the ad-hoc checkers to it.
- **Over-build to defer:** 8 identical domain stubs → one template; Q3 lanes + conditional
  overlays → catalog entries only.
- **Env reality:** the validator needs `jsonschema`+`PyYAML`. Locally **`py -3.11` has
  them; `py -3.12` does NOT** — wire EQ-2 so this cannot cause a false CI/verify failure.

---

## Repo wiring facts (embedded so you needn't re-derive)

- **ADR:** `docs/adr/NNNN-slug.md`. Existing run to `0003-*`; next number = **`0004`**.
- **Schemas:** live flat at `schemas/*_schema.json`. Put the framework's JSON schemas under
  a grouped subdir `schemas/qualification/<name>.schema.json` to avoid crowding the flat
  dir; reference them by relative path from the validator.
- **Config:** readiness/authority YAML live in `config/`. Put qualification YAML under
  `config/qualification/`.
- **CI** (`.github/workflows/ci.yml`): each gate is a job on `ubuntu-latest`,
  `permissions: {contents: read}`, `actions/checkout@v6`, `actions/setup-python@v6` with
  `python-version: '3.12'`, then `python -m pip install PyYAML` and
  `python -m pip install -e "backend[dev]"`, then runs a **`.sh` wrapper**
  (e.g. `./scripts/run_release_readiness_check.sh`). New gate must follow this shape and
  **must ensure `jsonschema` is importable** under the CI interpreter (add it to
  `backend[dev]` if not already present — dev/validation dep, note in the ADR/plan).
- **verify** (`scripts/verify.ps1` / `verify.sh`): `verify.ps1` selects interpreter via
  `Select-Python` (tries `py -3.12`, falls back to `python`) — **this is the source of the
  local false-fail**; for qualification, the wrapper must select an interpreter that has
  `jsonschema` (honor `PYTHON_BIN`/`LAND_DD_PYTHON_EXECUTABLE`; document `py -3.11` for
  local runs). `verify.sh` uses `PYTHON_BIN="${PYTHON_BIN:-python}"`. Register the new
  selftest as a sequenced step mirroring existing checker invocations.
- **Wrappers:** the package ships `.ps1`/`.cmd` only. You must ADD `.sh` wrappers for CI
  (mirror `scripts/run_release_readiness_check.sh`), keep `.ps1` for local Windows.
- **Checker tests:** mirror `backend/tests/test_release_readiness_artifacts.py` — load the
  validator via `importlib.util.spec_from_file_location(...)`, assert selftest exit 0 and
  that examples conform.
- **Source rights model:** `backend/app/source_registry/usage_rights.py`
  (`PRODUCTION_USAGE_FIELDS` = license_status, commercial_use_status,
  redistribution_status, cache_allowed, export_allowed, raw_data_allowed, ai_use_allowed)
  + `registers/data_source_registry.csv` (1:1 columns). Map the framework's
  `source_quality_profile` onto these fields — do not invent a parallel rights vocabulary.
- **Plan format:** `.agent/PLANS.md` (Goal / Non-goals / Current state / Proposed design /
  Bottom-up sequence / Files likely to change / Tests-verification / Risks-blockers /
  Decision log / Progress log). Plans live at `plans/YYYY-MM-DD-slug.md`, referenced from
  `state/PROJECT_STATE.md`.
- **PR/merge:** branch off `origin/main`; one PR per lane; watch CI to green; merge
  `--no-ff`; post-merge detached proof; remove worktree. Commit messages: plain, no
  attribution trailers.

---

## Lanes

> Sequence: **EQ-1 → EQ-2 → EQ-3 → EQ-4 → EQ-5.** Lane R is independent and may run in
> parallel. Each lane: author its own `plans/2026-06-21-eq-<lane>-<slug>.md` first, then a
> single PR. EQ-1 is a hard gate — no spine code lands before the boundary decision is ADR'd.

### EQ-1 — Boundary & consolidation ADR (GATE; do first)
**Why:** prevents a third competing readiness truth. This is the precondition for value.
**Do:**
- Write `docs/adr/0004-empirical-qualification-control-plane.md`: decide and record that
  the qualification **catalog is the canonical empirical-validity authority**, and the
  existing `config/*_readiness.yaml` + `scripts/*_readiness_check.py` +
  `state/LEVEL_9_10_GATE_MATRIX.md` are a **CI/deployment gate layer that reports INTO**
  qualification (not parallel truth). State that `jsonschema` is adopted as a
  dev/validation dependency. State the deferrals (Q3, conditional overlays, no PASS).
- Update `AGENTS.md` (one concise paragraph under the relevant section) and `MANIFEST.md`
  (route entry) with the boundary, so future agents have one source of truth.
- Add the EQ-1…EQ-5 + Lane R lanes to `tasks/task_queue.yaml` as queued items.
  **Caution:** `tasks/task_queue.yaml` has had a PyYAML parse sensitivity — validate it
  parses (`py -3.11 -c "import yaml,sys; yaml.safe_load(open('tasks/task_queue.yaml'))"`)
  before committing.
**Done:** ADR merged; AGENTS.md/MANIFEST.md carry the boundary; task_queue parses and lists
the lanes. No product code in this lane.

### EQ-2 — Land the self-validating spine + CI gate
**Why:** the part that pays for itself immediately and cannot be gamed.
**Copy from package → repo** (adapt paths/imports; package dir is read-only):
- `qualification_vocabulary.yaml` → `config/qualification/`
- `criterion_catalog.yaml` → `config/qualification/`
- `qualification_profiles.yaml` → `config/qualification/`
- schemas → `schemas/qualification/`: `qualification_vocabulary.schema.json`,
  `criterion_contract.schema.json`, `criterion_catalog.schema.json`,
  `qualification_profiles.schema.json`
- `scripts/validate_qualification.py`, `scripts/selftest_qualification_validator.py` →
  `scripts/` (fix any internal relative paths to the new repo layout)
- keep `scripts/validate_qualification.ps1` / `.cmd`; **ADD** `.sh` wrappers
  `scripts/run_qualification_validate.sh` and `scripts/run_qualification_selftest.sh`
  (mirror `scripts/run_release_readiness_check.sh`); add matching `.ps1` named to repo
  convention if helpful.
**Wire:**
- Ensure `jsonschema` is importable under CI's `python` (add to `backend[dev]` if absent).
- Add CI job `qualification-selftest` to `.github/workflows/ci.yml` following the embedded
  pattern; it runs `./scripts/run_qualification_selftest.sh` then
  `./scripts/run_qualification_validate.sh` (validate the catalog).
- Register the selftest as a sequenced step in `verify.ps1`/`verify.sh`, honoring
  `PYTHON_BIN` so it uses an interpreter with `jsonschema` (document `py -3.11` locally).
- Add `backend/tests/test_qualification_spine.py` mirroring
  `test_release_readiness_artifacts.py`: load the validator via importlib, assert selftest
  exit 0, assert `criterion_catalog.yaml` validates and framework↔catalog ID parity holds.
**Done:** selftest green in CI and locally (`py -3.11` or `PYTHON_BIN`); catalog validates;
new test passes; `verify` green.

### EQ-3 — Honest status + minimal parameterization surface
**Why:** make the framework report the *correct* current state.
**Do:**
- Create `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` from
  `empirical_qualification_status.example.yaml`, set to honest values:
  `highest_valid_classification` = the repo's actually-proven level (treat as **`L9-R`**
  unless `state/LEVEL_9_10_GATE_MATRIX.md` proves higher), **`P0 = BLOCKED`** with a
  rationale citing `PROJECT_PARAMETERIZATION_BLOCKERS.md`. Validate it.
- Add schemas → `schemas/qualification/`: `empirical_qualification_status.schema.json`,
  `source_quality_profile.schema.json`, `domain_qualification_profile.schema.json`,
  `qualification_targets.schema.json`, `qualification_result.schema.json`,
  `judgment_rubrics.schema.json`.
- **Collapse the 8 domain stubs to ONE** `config/qualification/domain_profile.template.yaml`
  (+ its schema). Do not land 8 clones.
- Add ONE real `config/qualification/source_quality_profile.<source>.yaml` for an
  already-approved source, mapping fields onto `usage_rights.py` `PRODUCTION_USAGE_FIELDS`
  (no parallel rights vocabulary).
- Extend `test_qualification_spine.py` (or a sibling) to assert the status file validates
  and reports `P0 = BLOCKED`, and the template/source profile validate.
**Done:** status validates at honest `P0 = BLOCKED`; schemas + one template + one source
profile land; tests green; `verify` green.

### EQ-4 — Consolidation crosswalk (subordinate the ad-hoc checkers)
**Why:** deliver the consolidation the ADR promised; reduce net governance systems.
**Do:**
- **Self-derive** the live list (do not trust any hardcoded inventory): enumerate
  `config/*readiness*.yaml`/authority configs and `scripts/*_readiness_check.py` /
  authority checkers on `origin/main`.
- Produce `docs/qualification/readiness-crosswalk.md`: map each existing readiness/authority
  check → the `criterion_id`(s) in `criterion_catalog.yaml` it satisfies or feeds. Flag any
  check with no catalog home (candidate to retire/fold) and any catalog gate with no
  existing check (genuine empirical gap).
- Land `config/qualification/change_impact_matrix.yaml` (+ schema) and validate its
  `invalidate_by_default[]` criterion IDs against the catalog (the package leaves these
  unvalidated — add that check to the validator or the test).
- Where cheap and non-breaking, annotate existing readiness checks with the criterion ID
  they map to (comment/metadata only; no behavior change). Archive nothing yet.
**Done:** crosswalk doc merged; change-impact-matrix validates against the catalog; gaps
and orphans are explicitly listed; no existing gate behavior changed.

### EQ-5 — Parameterization-backlog tracking (non-coding; visibility)
**Why:** make the "weeks-to-months of owner decisions" honest and gated.
**Do:**
- Add `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` enumerating, from
  `PROJECT_PARAMETERIZATION_BLOCKERS.md`: the 21 frozen-decision placeholders, the
  **0-approved-sources** fact, the unfrozen domain profiles / judgment rubrics / target
  bindings — each as a `BLOCKED (external/owner authority)` item with the gate it unblocks.
- Add corresponding `BLOCKED` entries to `tasks/task_queue.yaml` (validate parse).
**Done:** backlog doc lists every owner-decision blocker with its gate; task_queue parses
and reflects them. No attempt to resolve them.

### Lane R — Correct the residual-reconciliation falsehood (parallel, independent)
**Why:** `state/residual-reconciliation.md` asserts `STILL_DIVERGENT: none`, which is
false, and the ~11 stranded DEFER'd files are decaying 71 commits behind main.
**Do (choose, and record the choice in the file):**
- **Preferred:** extract the ~11 genuinely-stranded files (listed in Background, Audit A)
  onto a branch `defer/guardrail-readiness-ui` off **current** `origin/main`, rebasing
  their substrate (note `ui.py` route set and readiness parsers changed) so they stop
  decaying; then the dirty root `codex/r026-raw-readiness-ui` can be discarded. Do **not**
  land them as PASS — they remain DEFER product slices.
- **Minimum:** if extraction is out of appetite now, correct
  `state/residual-reconciliation.md` to replace `STILL_DIVERGENT: none` with the honest
  count + the explicit file list + gate IDs + a decay warning, so the next agent does not
  discard real work.
**Done:** the false claim is corrected; stranded files are either extracted to a fresh
branch off main or explicitly re-recorded as decaying DEFER work with their gates.

---

## Decision log
- 2026-06-21: User elevated the Bologna recorded-source path above broad EQ-2/EQ-3/EQ-4
  work. `EQ-BOL` is a pulled-forward visibility slice after EQ-1: it creates the
  blocked parameterization backlog now, while EQ-5 later reconciles or graduates that
  backlog after the self-validating spine, status file, and crosswalk exist.
- 2026-06-21: Milestone scoped as ADAPT (land spine, consolidate, defer expansion) per
  Audit B; sequenced EQ-1 (gate) → EQ-5 + parallel Lane R. Q3/conditional overlays and any
  gate PASS explicitly deferred. `jsonschema` adopted as dev/validation dep (EQ-2/ADR).

## Progress log
- 2026-06-21: EQ-1 merged through PR #124. `EQ-BOL` branch started from
  `origin/main@6d671875aee1c0a7fcba1d6124c2ffbb05841457` to record the blocked
  Bologna-first parameterization backlog without landing qualification spine code.
- 2026-06-21: Handoff authored off `origin/main@cc54776`. Awaiting receiving session to set
  goal and begin EQ-1.
