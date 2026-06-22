# Harden the Empirical-Qualification Control Plane (resolve bot-flagged defects)

> Self-contained delegated handoff. Execute against `origin/main` without further steering.
> If anything here conflicts with live `origin/main`, **live `origin/main` wins** — reconcile
> first. Every finding below is from the chatgpt-codex-connector review bot; **re-confirm each
> against current main before fixing** (the EQP2 validator rework may have already fixed some —
> if so, mark that review thread resolved with a one-line note and move on).

## FIRST ACTION — set the session goal

Set your session goal (use your goal function / `/goal`) to:

> **Harden the empirical-qualification control plane: resolve the verified review-bot
> correctness/security defects in the qualification validators, checkers, crosswalk, and
> status derivation — re-confirming each against current main, fixing the still-valid ones
> with tests, and keeping the framework honestly `P0 = BLOCKED`. STOP adding new
> Bologna/authority scaffolding: it is externally blocked and adds no actionable value until
> an external owner decision exists.**

Mid-to-long-term milestone, bottom-up lanes HCV-1 … HCV-4, one PR each.

## Why this milestone (and why NOT more Bologna)

EQP2 (operationalize) is complete and sound: status derivation is hard-capped to
`{BLOCKED, NOT_RUN}`, validator + selftest pass, P0 honestly BLOCKED. Good. But the review bot
left **~26 still-open correctness/security findings on the control plane itself** — real
defects in `validate_qualification.py`, the readiness/authority checkers, the crosswalk, and
status derivation. These were deferred while EQP2 was active; that lane is now done, so they
are safe to fix.

Separately: the last four merges (#138–#141, ~1,900 lines) added more Bologna authority-record
scaffolding. It stayed blocked-sound (no line crossed), but it is **over-governance creep** —
it extends already-existing Bologna packets and advances nothing actionable, because Bologna
needs an external AOI + source-rights decision that no checker can produce. **Do not continue
that direction.** Hardening the validators (which actually run and gate) is higher-value than
more blocked-authority YAML.

## Handoff contract

- **Objective:** the qualification validators/checkers/crosswalk/status-derivation are free of
  the bot-flagged correctness/security defects (or each is confirmed already-fixed/stale and
  its thread resolved), with regression tests, and the framework still reports honest
  `P0 = BLOCKED`.
- **Scope fence:** only the findings in "Lanes" below, all within the qualification + readiness
  checker subsystem you own. Re-verify currency, fix still-valid, add tests, resolve stale
  threads.
- **Non-goals (do NOT do):**
  - Do **not** add any new Bologna/authority scaffolding, packet, or checker. (Hard stop on
    that direction.)
  - Do **not** move any gate/criterion to `PASS`; do **not** unfreeze owner decisions
    (`candidate.* null`, `source_profile_ids` empty, targets DRAFT, domain profiles
    template-only must all hold). Tightening validators must only ever make BLOCKED *more*
    correct, never enable a PASS.
  - Do **not** touch `backend/app/api/ui.py`, `backend/app/api/connectors.py`,
    `backend/app/main.py`, or any `defer/*` / `fix/*` branch — **a parallel lane owns those
    product files.**
  - Do **not** change DB schema, public API, or report semantics; no file deletion (archive
    instead); no AI/agent/model attribution anywhere.
- **Boundaries & ISOLATION (a parallel lane runs concurrently):**
  - You OWN: `scripts/validate_qualification.py`, `scripts/selftest_qualification_validator.py`,
    `scripts/qualification_status_check.py`, `scripts/qualification_change_impact_check.py`,
    `config/qualification/**`, `schemas/qualification/**`, the readiness/authority checker
    scripts (`scripts/*_readiness_check.py`, `scripts/*authority*_check.py`,
    `scripts/checklist_dry_run_check.py`, `scripts/package_manifest_check.py`,
    `scripts/private_mvp_readiness_check.py`, `scripts/bologna_*` *for fixes only, not new
    scaffolding*), plus ALL shared state/control files (`state/**`, `tasks/task_queue.yaml`,
    `MANIFEST.md`, `plans/**`).
  - The parallel lane is fixing **product bugs in `backend/app/api/ui.py`,
    `backend/app/api/connectors.py`, `backend/app/main.py` only** — it will not edit your
    subsystem or shared state files.
  - Worktrees only under `worktrees/hcv-*` off `origin/main`.
- **Canonical sources:** `origin/main` HEAD; `AGENTS.md`; `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`;
  `config/qualification/criterion_catalog.yaml`; `scripts/validate_qualification.py`; this plan.
- **Isolation:** one branch+worktree per lane: `hcv/<lane>` under `worktrees/hcv-<lane>`.
- **Done-criteria:** each lane below; milestone done = HCV-1…HCV-4 merged (or findings
  confirmed stale + threads resolved), `verify` green (validator+selftest incl. the
  qualification-selftest CI job), P0 still BLOCKED, every fix covered by a selftest/regression
  case.
- **Verification:** each lane PR reviewed by a **separate** lane (not self-approval). CI
  `verify`+`db-verify`+`qualification-selftest` green before merge; **confirm ALL checks green
  via `gh pr checks` (not just a `--watch` exit) immediately before merging**, and run the full
  `verify` gate (incl. mypy, py-3.12) locally before merge — do not merge on partial signal.
  Post-merge detached proof; remove the worktree.
- **Constraints:** smallest correct change per slice; bottom-up; author
  `plans/2026-06-21-hcv-<lane>-<slug>.md` first; update `state/PROJECT_STATE.md`/`WORKLOG.md`/
  `VALIDATION_LOG.md`. Each new validator rule gets a selftest fail-closed case.

## Lanes (re-verify each finding against current main first)

### HCV-1 — `validate_qualification.py` correctness gaps (highest value)
Findings (PR #126/#127). For each, confirm still-present, then fix + add a selftest case:
- Expired gates: a `PASS` result must be rejected when `expires_at` is in the past (no
  time-based expiry check today). *(Time input must be injectable for tests — pass a clock/now
  param; do not call a live clock in a way that breaks determinism.)*
- Result `gate_id` must match the status gate it is filed under (mismatched gates accepted).
- Result scope/version identity must match candidate scope/version (different profile versions
  accepted as evidence).
- Per-criterion evidence references must resolve (broken links accepted in PASS).
- `FROZEN` domain profiles with unresolved `TBD` fields must be rejected (owner decisions
  silently treated as frozen).
- Frozen domain-profile modality/channel coverage must be validated (narrower scope accepted).
- Source-profile coverage must be validated against targets (out-of-scope sources accepted).
- `CONDITIONAL` source rights must require an enforcement-control proof (accepted without
  proof).
- P0 `BLOCKED`: validate the `blocked_record` (reason + references) **regardless of whether a
  `result_path` is present** (currently skipped when result_path set).
- `RAW_EXPORT` validation must require the export right too, not just `raw_data` (#127).
- `schemas/qualification/qualification_result.schema.json`: `PASS` results must require
  reviewer / independent-reproduction metadata (currently omittable).
**Done:** each gap fixed + a selftest mutation proving it fails closed; P0 still BLOCKED.

### HCV-2 — Checker robustness & security
- `scripts/checklist_dry_run_check.py` (#82): reject empty `contains: ""` / `regex: ""`
  assertions (they match anything); recognize checklist markers beyond `- [ ]`
  (`* [ ]`, `+ [ ]`, ordered); **confine path resolution to the repo root** — absolute paths or
  `../` in evidence/blocker_authority fields must not read outside the repo (path-traversal).
- `scripts/package_manifest_check.py` (#88): explicitly reject duplicate ZIP entries (currently
  collapsed by `set()`); broaden secret-path detection beyond `.env*` to common patterns
  (`*.pem`, `*.key`, `config/prod.*`, etc.).
- `scripts/private_mvp_readiness_check.py` (#92): validate county-specific connector
  assignments per county; bind provenance-expectation classes to each source.
- `scripts/run_bologna_pilot_scope_authority_check.ps1` (#121): check `$LASTEXITCODE` after the
  Python validator (missing check → false success). (Fix-only; no new Bologna scaffolding.)
**Done:** each fixed + a focused test; the path-traversal fix has an explicit escape-attempt
test.

### HCV-3 — Crosswalk completeness (orphaned CI gates)
`config/qualification/readiness_crosswalk.yaml` (#128): the CI gates `run_provenance_check.sh`,
`run_security_scan.sh`, and `run_backup_restore_check.ps1` are not mapped in the crosswalk
inventory → orphaned gates. Add them (mapped to the appropriate criterion IDs, `evidence_role`),
and extend the validator's inventory-coverage check so a future unmapped CI gate fails closed.
**Done:** no orphaned CI gate; validator enforces inventory coverage; selftest case.

### HCV-4 — Status-derivation + config consistency
- `scripts/qualification_status_check.py` (#130): the P0 "parameterization unresolved" blocker
  set is narrower than the validator's full set (only targets/candidate, not contracts/rubrics/
  profiles) → derived vs validator drift. Align the two so the derived BLOCKED reason matches
  the validator.
- `config/qualification/source_profiles/source_quality_profile.ds-002.yaml` (#127): the
  `CONDITIONAL` rights vocabulary is incompatible with production `usage_rights.py`
  (`restricted`/`approved-with-restrictions`); reconcile the profile vocabulary with the
  production registry fields.
- `tasks/task_queue.yaml` / routing (#86, #121): remove stale "active" routing entries for work
  already marked done (BPS-001, REC-001). (Low priority; coordination-only.)
**Done:** derived status reason matches validator; DS-002 vocab reconciled; routing consistent.

## Explicitly out of scope / already addressed (do not redo)
- Plan-doc findings on `plans/2026-06-21-eq-phase2-operationalize.md` and
  `plans/2026-06-21-empirical-qualification-adoption.md` (#129/#123): these are historical
  decision records; the issues they cite (baseline wording, the "no separate selftest job"
  claim) were already corrected or superseded. Just resolve those threads, do not rewrite the
  plans.

## Decision log
- 2026-06-21: Redirect off Bologna scaffolding (creep, externally blocked) to hardening the
  control-plane validators against ~26 verified bot findings. Strict no-PASS / no-unfreeze /
  no-new-Bologna. Parallel lane owns backend/app/api/{ui,connectors}.py + main.py product bugs.

## Progress log
- 2026-06-21: Handoff authored off `origin/main@9490a7d`. Awaiting session to set goal + begin HCV-1.
