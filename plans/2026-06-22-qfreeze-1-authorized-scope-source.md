# QFREEZE-1 Authorized Scope Source And Windows Freeze

## Goal
Apply the first owner-authorized qualification parameterization freeze slice after HCV:
record the owner decision, freeze the explicitly authorized scope/version/source fields,
bind DS-002 as the first approved source profile, and freeze only the W-003/W-011 target
bindings that the owner directive explicitly resolves. The lane must keep `P0 =
BLOCKED`, every non-P0 status `NOT_RUN`, and all remaining domain/profile/contract/
rubric/threshold blockers visible.

## Non-goals
- Do not set the top-level `qualification_targets.status` to `FROZEN` while unrelated
  active target bindings remain DRAFT.
- Do not freeze domain profiles, criterion contracts, judgment rubrics, Q1/Q2/DQ/M
  thresholds, AI/CG/FIN/E profiles, Bologna AOI/source authority, source approvals
  beyond DS-002, DS-017, hosted authority, DB/API/UI/report semantics, or any
  qualification `PASS`.
- Do not touch `backend/app/**` or `schemas/report_run_schema.json`; only reference the
  already-existing report contract value.
- Do not create a report result, candidate artifact, corpus, fixture, DB seed, connector,
  source registry promotion, or runtime proof.

## Current state
- HCV-2, HCV-3, and HCV-4 are merged. Live `origin/main` is
  `6f49c7abc9bec4f8d2d17734609e6960cc869bc8`.
- Fresh worktree `worktrees/qfreeze1` on `codex/qfreeze-cascade-1` starts from that
  live main.
- This active follow-on remains subordinate to `state/LEVEL_9_10_GATE_MATRIX.md`; the
  Level 9/10 gate matrix is still blocked by the same external source/AOI/hosted and
  qualification evidence boundaries.
- Baseline checks passed before edits:
  - `py -3.12 scripts\qualification_status_check.py --root .` derives
    `BLOCKED=1 NOT_RUN=20`.
  - `py -3.12 scripts\validate_qualification.py --root . --now 2026-06-22T12:00:00Z`
    passes with blocked-readiness warnings for template-only domain profiles, empty
    source bindings, unresolved scope/version fields, unresolved `ruleset_versions`,
    draft targets, draft criterion contracts, and draft judgment rubrics.
  - Focused backend qualification/routing tests passed (`15 passed`).
- Owner authorization is preserved in `state/owner-decisions.md` and covers only:
  product scope `BOUNDED_USER_VALIDATED`, deployment `LOCAL_SINGLE_USER`,
  `windows_native_required=true`, W-003 long-path policy and paths-with-spaces smoke
  evidence, W-011 version matrix and upgrade-policy note, scope/version fields, and
  source binding `DS-002`.
- At QFREEZE-1 baseline, `qualification_targets.yaml` already had product/deployment/
  windows values but recorded no controlled disposition, kept `source_profile_ids: []`,
  left `ruleset_versions` and six scope/version fields unresolved, left
  `windows_native.long_path_policy` and W-003/W-011 target bindings DRAFT, and kept the
  target registry globally `DRAFT`.
- Canonical current values found in repo:
  - Report contract: `report_run_contract_v1` in `schemas/report_run_schema.json` and
    report contract tests.
  - API contract: `api/openapi_stub.yaml` version `0.1.0`.
  - Ruleset: `config/ruleset_homestead_mvp.yaml` id `homestead_mvp_v0_1`, version
    `0.1`, matching report tests.
  - DS-002 profile: `config/qualification/source_profiles/source_quality_profile.ds-002.yaml`
    is `APPROVED` and uses `HASHED_RETRIEVAL_MANIFEST`.

## Proposed design
Record a controlled owner disposition in `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md`
for each authorized field. Use `owner=benjmcd`, `authority=owner directive
2026-06-22`, `authority_file=state/owner-decisions.md`, rationale `conservative
defaults matching operational reality`, and reversal `requires a new owner decision +
full requalification`, as required by the handoff and preserved in the branch-local
decision ledger.

Update `config/qualification/qualification_targets.yaml` narrowly:
- Keep top-level `status: DRAFT`.
- Bind `scope.source_profile_ids: [DS-002]`.
- Freeze scope/version values:
  `report_contract_version: report_run_contract_v1`, `api_contract_version: 0.1.0`,
  `ruleset_versions.homestead_mvp_v0_1: "0.1"`,
  `normalization_schema_version: 0.1.0-alpha`,
  `geometry_pipeline_version: 0.1.0-alpha`,
  `source_snapshot_policy: HASHED_RETRIEVAL_MANIFEST_PER_SOURCE`, and
  `data_as_of_policy: SOURCE_DATA_AS_OF_AND_RETRIEVAL_TIMESTAMP_WITH_FRESHNESS_CAVEATS`.
- Freeze Windows values:
  `windows_native.long_path_policy: ENABLED`,
  supported Windows versions `["Windows 11 (>=22H2)"]`,
  PowerShell versions `["5.1", "7.x"]`, Python versions `["3.12"]`, Docker Desktop
  versions `["4.x"]`.
- Mark only `criterion_bindings.W-003` and `criterion_bindings.W-011` as `FROZEN`, with
  rationales citing the owner directive and local evidence notes.

Add a compact repo-local evidence note under `docs/qualification/` for W-003/W-011 that
records the expected paths-with-spaces smoke evidence and upgrade-policy boundary without
claiming W gate `PASS`.

Alternatives rejected:
- Freezing the whole target registry now: invalid because many unrelated target bindings,
  contracts, and rubrics remain DRAFT.
- Freezing DQ/Q1/Q2/M bindings from existing numeric values: those are threshold/pass-rule
  decisions and the handoff explicitly excludes domain-profile rubric thresholds and
  criterion-contract pass-rules.
- Treating DS-002 binding as source-domain coverage resolution for all domains: DS-002
  only covers flood; other domain profiles/source approvals remain blocked.

## Bottom-up sequence
1. Add red tests for the owner decision record, authorized target values, DS-002 binding,
   W-003/W-011 frozen bindings, and P0/non-P0 status cap.
2. Apply the narrow target/backlog/evidence/routing edits.
3. Run focused tests and validators after the slice.
4. If validators reveal additional mechanically resolvable target bindings, freeze only
   those with a source-backed rationale; otherwise leave them blocked and record why.
5. Run ruff/mypy, diff hygiene/no-deletion checks, full `.\scripts\verify.ps1`, separate
   review, GitHub checks, merge, detached post-merge proof, and worktree cleanup.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-22-qfreeze-1-authorized-scope-source.md` | Executable plan for first cascade slice. |
| `config/qualification/qualification_targets.yaml` | Authorized scope/version/source and W target values. |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | Controlled owner-disposition record and updated blocker counts. |
| `docs/qualification/windows-freeze-evidence.md` | W-003/W-011 evidence and upgrade-policy note. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Owner-disposition/backlog assertions. |
| `backend/tests/test_qualification_status_check.py` | Status cap remains `BLOCKED`/`NOT_RUN` after partial freeze. |
| `backend/tests/test_readiness_core_artifacts.py` | Active plan/routing assertions if this slice becomes active. |
| `tasks/task_queue.yaml` | Route HCV-4 done and QFREEZE-1 active. |
| `state/PROJECT_STATE.md` | Current checkpoint for first freeze slice. |
| `state/WORKLOG.md` | Execution notes. |
| `state/VALIDATION_LOG.md` | Validation evidence. |
| `plans/README.md` | Current/latest plan routing. |

## Tests / verification
- `py -3.12 -m pytest -q tests\test_qualification_status_check.py tests\test_qualification_parameterization_backlog_artifacts.py tests\test_readiness_core_artifacts.py` from `backend\`.
- `py -3.12 scripts\qualification_status_check.py --root .`
- `py -3.12 scripts\validate_qualification.py --root . --now 2026-06-22T12:00:00Z`
- `py -3.12 scripts\selftest_qualification_validator.py`
- `py -3.12 scripts\readiness_matrix_check.py`
- Focused `ruff`/`mypy` on touched scripts/tests if code/tests change.
- `git diff --check`
- `git diff --name-only --diff-filter=D`
- `.\scripts\verify.ps1`

## Risks and blockers
- The owner directive authorizes specific values but not P0 PASS, domain thresholds,
  source approvals beyond DS-002, or criterion/rubric pass-rules.
- Binding DS-002 reduces one source blocker but does not cover all qualified domains.
- W-003/W-011 target bindings can be frozen, but W gate status must remain `NOT_RUN`
  until a future qualification result is produced from controlled evidence.
- The top-level target registry must stay `DRAFT` until all active target bindings are
  frozen.

## Decision log
- 2026-06-22: First cascade slice will freeze only owner-authorized scope/version/source
  and W-003/W-011 target values; P0 remains `BLOCKED`.

## Progress log
- 2026-06-22: Created `worktrees/qfreeze1` from live `origin/main@6f49c7a`, read startup
  routing and qualification artifacts, verified baseline status/validator/focused tests,
  and drafted this executable plan.
