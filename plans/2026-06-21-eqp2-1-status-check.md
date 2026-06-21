# EQP2-1 Derived Qualification Status Check

## Goal
Make the empirical qualification status file executable and drift-proof by deriving
the allowed gate/overlay statuses from the committed control plane and mapped checker
results, then failing when `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` disagrees.

## Non-goals
- Do not move any gate, overlay, or criterion to `PASS`.
- Do not unfreeze owner decisions, candidate identity, targets, rubrics, source
  profiles, domain profiles, Bologna authority, DB/API/auth/report semantics, or
  runtime artifacts.
- Do not change existing readiness/authority checker behavior in this lane.
- Do not add runtime/product dependencies.

## Current state
- `docs/adr/0004-empirical-qualification-control-plane.md` makes the qualification
  catalog/status the canonical empirical-validity authority, while existing
  readiness/authority checks report into it.
- `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` is hand-authored: `p0` is `BLOCKED`,
  all other qualifications, overlays, and conditional overlays are `NOT_RUN`,
  `candidate.*` is null, and `highest_valid_classification` is `L9-R`.
- `config/qualification/readiness_crosswalk.yaml` maps active readiness/authority
  surfaces to criterion IDs and evidence roles, but does not provide checker command
  metadata.
- `scripts/validate_qualification.py` validates schema/catalog/crosswalk structure and
  prevents false `PASS`, but it does not run mapped checkers or require P0 to remain
  `BLOCKED` while targets are DRAFT.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains a downstream readiness/maturity surface;
  this lane does not change Level 9/10 readiness semantics and only makes the
  qualification status check consume mapped readiness surfaces as non-passing inputs.
- A live audit of the mapped checker paths found that all default invocations pass
  except two unstarted-runtime cases: `scripts/package_manifest_check.py` needs a
  built manifest argument and `scripts/spatial_query_plan_runtime_check.py` needs a
  DB URL.

## Proposed design
Add `scripts/qualification_status_check.py` and shell/PowerShell wrappers. The checker
will load the catalog, targets, crosswalk, and committed status file, run each unique
mapped checker path with the selected Python, and derive a conservative status view:

- `p0` is `BLOCKED` while qualification targets are not `FROZEN` or candidate identity
  is incomplete.
- Every other gate/overlay starts as `NOT_RUN`.
- A checker exit code of `0` does not advance status; the mapped gate/overlay remains
  `NOT_RUN` because readiness checks are evidence inputs, not qualification passes.
- The two measured unstarted-runtime checkers remain `NOT_RUN` when they emit their
  known missing-input diagnostics.
- Any other nonzero mapped checker result marks the mapped catalog gates/overlays
  `BLOCKED`, which makes the committed status mismatch and fails closed.
- Any committed status outside `{BLOCKED, NOT_RUN}` fails, even if the structural
  validator would otherwise accept it.

Rejected alternatives:

- Treat every nonzero checker as immediately `BLOCKED`: this would turn missing DB URL
  or missing release manifest into a false qualification blocker even though no
  qualification run has started.
- Treat passing readiness checks as `PASS`: this contradicts ADR 0004 and the Phase 2
  non-goal that no gate may pass from repo-local inference.
- Add crosswalk command metadata now: useful later, but it broadens EQP2-1. EQP2-4 is
  the correct lane for checker advertisement and parity.

## Bottom-up sequence
1. Add failing tests for the new status checker, including P0 drift and an unexpected
   checker failure case.
2. Implement the status checker and wrappers.
3. Extend the qualification selftest with a committed-status drift mutation.
4. Wire the status check into `verify.ps1`, `verify.sh`, and the CI
   `qualification-selftest` job through the wrapper.
5. Update routing/state logs to make EQP2-1 the active completed slice.
6. Run focused tests, direct status/validator/selftest checks, and full verification.

## Files likely to change
| File | Expected change |
|---|---|
| `scripts/qualification_status_check.py` | New derived status checker. |
| `scripts/run_qualification_status_check.sh` | New POSIX wrapper. |
| `scripts/qualification_status_check.ps1` | New PowerShell wrapper. |
| `scripts/selftest_qualification_validator.py` | Add status-drift selftest case. |
| `scripts/verify.ps1` | Add qualification status step after validator. |
| `scripts/verify.sh` | Add qualification status step after validator. |
| `.github/workflows/ci.yml` | Run the status wrapper in the qualification job. |
| `backend/tests/test_qualification_status_check.py` | Focused behavior tests. |
| `backend/tests/test_qualification_spine.py` | Assert new artifacts/wiring. |
| `state/PROJECT_STATE.md` | Route current checkpoint to EQP2-1. |
| `state/WORKLOG.md` | Record implementation summary. |
| `state/VALIDATION_LOG.md` | Record checks and outcomes. |

## Tests / verification
- `py -3.12 -m pytest backend/tests/test_qualification_status_check.py -q`
- `py -3.12 -m pytest backend/tests/test_qualification_status_check.py backend/tests/test_qualification_spine.py -q`
- `py -3.12 scripts/qualification_status_check.py --root .`
- `py -3.12 scripts/validate_qualification.py --root . --layout repo`
- `py -3.12 scripts/selftest_qualification_validator.py`
- `.\scripts\verify.ps1`

## Risks and blockers
- If a new mapped checker begins requiring runtime input without being declared in the
  status checker, EQP2-1 should fail closed. EQP2-4 is expected to replace the small
  local missing-runtime table with checker-advertised metadata.
- Unexpected checker failures currently cannot be committed as non-P0 `BLOCKED` without
  result artifacts because the structural validator requires `result_path` for those
  statuses. That is acceptable: the check should fail and force a deliberate follow-up
  instead of silently rewriting status.
- Full DB-backed checks remain optional and must not be seeded or generated by this
  lane.

## Decision log
- 2026-06-21: Use `origin/main@b88d608aec21a988bc4127f167ee0972f6da06f2` as live
  authority and work only in `worktrees/eqp2-1` on branch `eqp2/1-status-check`.
- 2026-06-21: Recent Git history proves PR #129 is the Phase 2 handoff on top of
  EQ-4; no separate visible EQ-5 implementation commit is treated as current
  authority.
- 2026-06-21: Derive only `BLOCKED`/`NOT_RUN`; never derive `PASS`.
- 2026-06-21: Treat only `package_manifest_check.py` and
  `spatial_query_plan_runtime_check.py` as known unstarted-runtime `NOT_RUN` cases for
  EQP2-1.

## Progress log
- 2026-06-21: Reconciled handoff against live worktree list and live `origin/main`;
  audited status, ADR 0004, crosswalk, change-impact matrix, validator, selftest,
  verification wrappers, CI, and existing qualification tests.
- 2026-06-21: Added focused red tests, implemented the derived status checker and
  wrappers, extended the adversarial selftest with a P0 drift case, and wired the
  checker into verify plus the dedicated qualification CI job.
- 2026-06-21: Focused status tests, direct status check, adversarial selftest,
  combined status/spine tests, and the PowerShell status wrapper passed before broader
  verification.
- 2026-06-21: Final `.\scripts\verify.ps1` passed after updating stale routing
  assertions; `git diff --check` passed and no tracked deletions were reported.
- 2026-06-21: Draft PR CI exposed that `db-verify` ambient DB URLs caused the status
  selftest to run spatial DB runtime before migrations. The checker now suppresses
  runtime env for known runtime-required checks by default, with an explicit
  `--allow-runtime-checkers` opt-in.
- 2026-06-21: Independent read-only code review found no blocking issues and one minor
  timeout-output normalization edge case; fixed that edge case and reran full
  `.\scripts\verify.ps1` successfully.
