# HCV-2 Checker Robustness And Security Hardening

## Goal
Harden the HCV-2 readiness/checker surfaces against the live review-bot findings:
checklist dry-run path/assertion parsing, release package manifest ZIP/secret
validation, private-MVP county/provenance bindings, and the Bologna pilot-scope
PowerShell wrapper exit-code handling. The empirical qualification framework must
remain honestly `P0 = BLOCKED` with every non-P0 qualification `NOT_RUN`.

## Non-goals
- No Bologna authority, source-rights, corpus, fixture, runtime, report, or DB seed
  scaffolding.
- No qualification `PASS`, owner-decision unfreeze, source approval, AOI selection,
  DS-017 approval, hosted authority, or Level 10 claim.
- No DB schema, public API, UI, report semantic, auth, or connector runtime change.
- No edits to the parallel product lane files:
  `backend/app/security_guardrails.py`, `backend/app/operations_guardrails.py`,
  `backend/app/source_provenance.py`, or their backend/API tests.
- No file deletion.

## Current state
- Live lane authority is `origin/main@79bd89cf0dc441606429ca6ca5d23ba6d7ad32a4`,
  the PR #144 HCV-1 merge. The root checkout is dirty scratch and is not used for
  implementation.
- Focused baseline tests pass for the HCV-2 surfaces:
  `py -3.12 -m pytest -q backend\tests\test_checklist_dry_run_artifacts.py backend\tests\test_package_manifest_check.py backend\tests\test_private_mvp_readiness.py backend\tests\test_bologna_pilot_scope_authority_artifacts.py`.
- `scripts/checklist_dry_run_check.py` currently joins referenced paths to `ROOT`
  without resolved root confinement, accepts empty `contains` / `regex` assertions,
  and only recognizes `- [ ]` / `- [x]` checklist markers.
- `scripts/package_manifest_check.py` currently detects only `.env*` plus a few local
  state path parts as forbidden secrets/state, and compares ZIP contents through a
  set of names, which collapses duplicate entries.
- `scripts/private_mvp_readiness_check.py` already validates the selected-county
  provenance section shape and aggregate connector names, but the live code still
  allows a connector to be assigned to the wrong selected county if the aggregate
  source-level set remains correct, and it accepts valid-but-wrong provenance
  expectation classes for a source.
- `scripts/run_bologna_pilot_scope_authority_check.ps1` delegates to the Python
  checker and prints success without explicitly checking `$LASTEXITCODE`.
- As the active follow-on plan, this plan must keep citing
  `state/LEVEL_9_10_GATE_MATRIX.md` so the readiness-matrix checker can preserve the
  Level 9/10 release-gate routing context while HCV-2 remains fix-only.

## Proposed design
Use fail-closed validation in the existing checkers and focused artifact tests:
- Add a root-confined path resolver for checklist artifacts and route all checklist
  file existence/read calls through it. Reject absolute paths and any path that
  resolves outside the repository root.
- Reject empty assertion bodies after trimming whitespace. Keep exactly-one-of
  `contains` / `regex` semantics.
- Extend checklist parsing to recognize unordered `-`, `*`, `+` checkbox markers
  and ordered checkbox markers such as `1. [ ]`, while still rejecting malformed
  checkbox-looking lines.
- Detect duplicate ZIP file entries from `ZipInfo` names before comparing names to
  the manifest.
- Expand forbidden package paths to common secret and production-config patterns:
  `.env*` except `.env.example`, `*.pem`, `*.key`, and `config/prod.*`, plus the
  existing local state exclusions.
- Add county/source expected provenance bindings for the selected NC counties, using
  the existing intentionally-scoped selected-county readiness catalog as authority.
  This is validation only; it does not expand source coverage.
- Make the Bologna PowerShell wrapper fail explicitly when the Python validator exits
  nonzero.

## Bottom-up sequence
1. Add red tests for the four HCV-2 findings and confirm they fail for the expected
   reason.
2. Patch the checker scripts minimally to satisfy those tests.
3. Re-run the focused HCV-2 pytest set and direct validators/wrappers.
4. Run qualification/status invariants proving `P0` remains `BLOCKED` and non-P0
   remains `NOT_RUN`.
5. Update state/worklog/validation log with exact commands and residual risk.
6. Run `git diff --check`, no-deletion check, and full `.\scripts\verify.ps1`.
7. Push HCV-2 as one PR, wait for green checks with `gh pr checks --watch --interval
   60`, confirm final `gh pr checks`, merge, run detached post-merge proof, and remove
   the worktree.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-21-hcv-2-checker-hardening.md` | Executable HCV-2 plan. |
| `backend/tests/test_checklist_dry_run_artifacts.py` | Red/green tests for empty assertions, path traversal, and marker parsing. |
| `backend/tests/test_package_manifest_check.py` | Red/green tests for duplicate ZIP entries and secret path patterns. |
| `backend/tests/test_private_mvp_readiness.py` | Red/green tests for county-specific connector and provenance-class binding. |
| `backend/tests/test_bologna_pilot_scope_authority_artifacts.py` | Red/green test for PowerShell wrapper exit-code handling. |
| `config/checklist_dry_run.yaml` | Replace the lone directory evidence citation with a concrete file citation. |
| `scripts/checklist_dry_run_check.py` | Root-confined paths, empty assertion rejection, broader marker parsing. |
| `scripts/package_manifest_check.py` | Duplicate ZIP detection and broader secret-path detection. |
| `scripts/private_mvp_readiness_check.py` | County/source-specific connector and provenance expectation validation. |
| `scripts/run_bologna_pilot_scope_authority_check.ps1` | Explicit `$LASTEXITCODE` failure propagation. |
| `plans/README.md` | Route current plan to HCV-2. |
| `tasks/task_queue.yaml` | Mark HCV-2 active and point to this plan. |
| `state/PROJECT_STATE.md` | Record HCV-2 as current lane and preserve boundaries. |
| `state/WORKLOG.md` | Append HCV-2 execution notes. |
| `state/VALIDATION_LOG.md` | Append focused/full validation results. |

## Tests / verification
- `py -3.12 -m pytest -q backend\tests\test_checklist_dry_run_artifacts.py backend\tests\test_package_manifest_check.py backend\tests\test_private_mvp_readiness.py backend\tests\test_bologna_pilot_scope_authority_artifacts.py`
- `py -3.12 scripts\checklist_dry_run_check.py`
- `py -3.12 scripts\private_mvp_readiness_check.py`
- `py -3.12 scripts\bologna_pilot_scope_authority_check.py`
- `.\scripts\run_bologna_pilot_scope_authority_check.ps1`
- `py -3.12 scripts\validate_qualification.py --root . --now 2026-06-21T12:00:00Z`
- `py -3.12 scripts\qualification_status_check.py --root .`
- `py -3.12 scripts\selftest_qualification_validator.py`
- Focused `ruff`/`mypy` on touched scripts/tests.
- `git diff --check`
- `git diff --name-only --diff-filter=D`
- `.\scripts\verify.ps1`

## Risks and blockers
- Checklist path confinement must not break legitimate repo-relative references in
  `config/checklist_dry_run.yaml`.
- Secret-path detection must reject packaged secrets without treating allowed docs or
  `.env.example` as forbidden.
- County/provenance bindings are intentionally scoped to the selected private-MVP NC
  counties; do not generalize them into a new multi-geography framework.
- The Bologna wrapper change must only propagate validator failure; it must not create
  authority, files, or scaffolding.

## Decision log
- 2026-06-21: HCV-2 proceeds after HCV-1 merged through PR #144. Keep the lane at
  checker hardening only, with no new Bologna or qualification-pass authority.

## Progress log
- 2026-06-21: Created clean `worktrees/hcv2` branch
  `codex/hcv2-checker-hardening` from `origin/main@79bd89c`; read routing,
  architecture, ADR 0004, HCV plan, and focused checker/test files; baseline focused
  HCV-2 tests passed before red tests were added.
- 2026-06-21: Added red tests for every HCV-2 finding and confirmed they failed for
  the expected missing behavior; patched the four checker/wrapper surfaces; focused
  HCV-2 tests, changed wrappers/checkers, structural qualification validation,
  status derivation, readiness-matrix check, qualification selftest, focused ruff, and
  focused mypy now pass.
- 2026-06-21: First full `.\scripts\verify.ps1` failed only on two stale routing tests
  that still expected HCV-1 as active. Updated those assertions for HCV-2; focused
  routing tests passed, and final full `.\scripts\verify.ps1` passed. DB smoke was
  skipped because `RUN_DB_SMOKE=1` was not set.
- 2026-06-21: After PR #146 advanced `origin/main` to
  `b5f6727bd5ab6b9264812e9943a24924eec54b29`, rebased HCV-2 cleanly. Focused HCV-2
  tests and changed wrapper/status/selftest/readiness checks passed again with
  `BLOCKED=1 NOT_RUN=20`; final full verification is being rerun on the rebased head.
- 2026-06-21: Separate review found that checklist evidence/blocker paths still
  accepted empty strings and directories. Hardened `require_existing()` to require
  non-empty repo-local files, replaced the lone directory evidence citation with a
  concrete file, and added catalog-level regression tests for empty evidence and
  directory blocker-authority paths. Focused HCV-2 checks, focused ruff/mypy, diff
  hygiene, no-deletion check, and final full `.\scripts\verify.ps1` passed on the
  review-response head; DB smoke was skipped because `RUN_DB_SMOKE=1` was not set.
