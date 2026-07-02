# EQP2-3 P0 Auto Evidence

## Goal
Collect repo-local evidence for the four auto-verifiable P0 invariants `P0-004`, `P0-005`, `P0-021`, and `P0-023`, link that evidence from the blocked P0 status, and mark each as `auto-evidenced; still target-blocked` in the parameterization backlog while keeping effective P0 status `BLOCKED`.

## Non-goals
- Do not move P0, any qualification, overlay, conditional overlay, or criterion to `PASS`.
- Do not create a formal P0 result artifact or claim a qualification run occurred.
- Do not unfreeze owner decisions, target bindings, source profiles, candidate identity, domain profiles, rubrics, source rights, AOI scope, or target status.
- Do not create sealed acceptance cases, fixtures, source records, DB seeds, connectors, rulepacks, reports, APIs, UI surfaces, or runtime proof.
- Do not implement EQP2-4 checker criterion-advertisement parity.

## Current state
- Live `origin/main@71c6a74eae08811d4e178b0c11365ff1e247772d` includes PR #136 jsonschema mypy stub fix, PR #134 report-run rights optionality, PR #133 report-run contract ADR, and PR #132 error-safety hardening, on top of EQP2-1 status derivation and EQP2-2 advisory change-impact reporting.
- `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` keeps `qualifications.p0.status: BLOCKED`, `result_path: null`, and unresolved candidate fields. Its schema allows additional blocked evidence links only through `blocker_references`; it does not allow arbitrary per-criterion evidence fields.
- `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` lists P0 target blockers but does not yet mark the four repo-local invariant evidence rows as auto-evidenced/still target-blocked.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context for routing. EQP2-3 cannot reinterpret Level 9/10 readiness or convert repo-local P0 evidence into hosted/runtime authority.
- Live catalog names differ from the handoff examples: `P0-021` is **Evidence integrity** and `P0-023` is **Threshold immutability**. This lane follows live catalog authority while still collecting the requested repo-local evidence classes.
- Existing qualification validators already preserve no-PASS behavior and P0 freeze rules. EQP2-3 should add an evidence checker rather than weaken status derivation.

## Proposed design
Add a committed evidence artifact at `docs/qualification/P0_AUTO_EVIDENCE.yaml` with one row per requested criterion. Each row records:
- live catalog statement;
- repo-local evidence status `auto_evidenced_still_target_blocked`;
- effective status `BLOCKED`;
- evidence records that point to existing repo files and explain the repo-local signal;
- caveats that explain what remains unproven until owner/freeze authority exists.

Add `scripts/qualification_p0_evidence_check.py` with wrappers. The checker will validate that:
- the four criterion IDs exist in the catalog and are invariant P0 criteria;
- the evidence artifact has exactly those rows, existing evidence paths, blocked effective status, and the expected evidence status;
- `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` still has P0 `BLOCKED`, `result_path: null`, and references the evidence artifact in `blocker_references`;
- `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` marks each criterion as `auto-evidenced; still target-blocked`;
- basic repo-local scans support the evidence claims, including no `continue-on-error` in CI, no pytest `xfail`, qualification status/change-impact checkers present, and known fixture corpora remaining explicitly fixture-only rather than sealed acceptance evidence.

Rejected alternatives:
- Put per-criterion evidence directly into `EMPIRICAL_QUALIFICATION_STATUS.yaml`: the status schema does not allow it, and adding schema surface for blocked evidence is unnecessary.
- Set `qualifications.p0.result_path`: that would imply a P0 run/result artifact, which is explicitly out of scope while targets and candidate identity remain unresolved.
- Treat repo-local evidence as criterion PASS: the evidence is partial and target-blocked; P0 remains blocked by unresolved profile/target/rubric/source decisions.

## Bottom-up sequence
1. Add failing tests for the evidence artifact, status/backlog links, and checker behavior.
2. Add `docs/qualification/P0_AUTO_EVIDENCE.yaml`.
3. Implement `scripts/qualification_p0_evidence_check.py` and wrappers.
4. Wire the checker into `scripts/verify.ps1`, `scripts/verify.sh`, and the `qualification-selftest` CI job.
5. Update `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`, `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md`, routing/state docs, and tests.
6. Run focused checks, full verify, separate review, PR, CI, post-merge proof, and worktree cleanup.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-21-eqp2-3-p0-auto-evidence.md` | Lane plan and progress log. |
| `docs/qualification/P0_AUTO_EVIDENCE.yaml` | New repo-local blocked evidence artifact. |
| `scripts/qualification_p0_evidence_check.py` | New artifact/status/backlog evidence checker. |
| `scripts/qualification_p0_evidence_check.ps1` | Windows wrapper. |
| `scripts/run_qualification_p0_evidence_check.sh` | POSIX/CI wrapper. |
| `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` | Add evidence artifact to P0 blocker references; keep P0 blocked and result_path null. |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | Mark four requested invariant IDs as auto-evidenced/still target-blocked. |
| `.github/workflows/ci.yml`, `scripts/verify.ps1`, `scripts/verify.sh` | Wire checker into local and CI verification. |
| `scripts/selftest_qualification_validator.py` | Add a fail-closed evidence-link mutation if useful after implementation. |
| `backend/tests/test_qualification_p0_auto_evidence.py`, `backend/tests/test_qualification_spine.py`, routing tests | Focused artifact/checker/routing coverage. |
| `MANIFEST.md`, `plans/README.md`, `state/PROJECT_STATE.md`, `state/WORKLOG.md`, `state/VALIDATION_LOG.md`, `tasks/task_queue.yaml` | State/routing updates after implementation. |

## Tests / verification
- Red first: `py -3.12 -m pytest backend/tests/test_qualification_p0_auto_evidence.py backend/tests/test_qualification_spine.py -q`
- Focused green: same pytest command after implementation.
- Direct checker: `py -3.12 scripts/qualification_p0_evidence_check.py --root .`
- Existing gates: `py -3.12 scripts/selftest_qualification_validator.py`, `py -3.12 scripts/validate_qualification.py --root . --layout repo`, `py -3.12 scripts/qualification_status_check.py --root .`, and `py -3.12 scripts/qualification_change_impact_check.py --root .`
- Lint/type narrow surface: `ruff check scripts/qualification_p0_evidence_check.py backend/tests/test_qualification_p0_auto_evidence.py backend/tests/test_qualification_spine.py`; targeted mypy if environment supports it.
- Full gate before PR: `.\scripts\verify.ps1`.
- CI before merge: GitHub `verify`, `db-verify`, and `qualification-selftest` green.
- Post-merge proof: detached `origin/main` `.\scripts\verify.ps1`.

## Risks and blockers
- Repo-local evidence is not the same as qualification evidence. The artifact must keep caveats explicit and effective status blocked.
- Test-suppression scanning can be noisy because conditional skips are legitimate for DB-gated tests. The checker should reject `xfail` and CI `continue-on-error`, while recording skip evidence as repo-local audit context instead of treating all skips as failures.
- P0-004/P0-005 cannot be satisfied from repo-local files because sealed acceptance cases and anti-contamination records require external/vaulted authority. This lane can only prove current repo-local controls and blocked state.

## Decision log
- 2026-06-21: Live catalog authority wins over stale handoff labels for P0-021/P0-023. Evidence collection will cite live catalog statements and keep all four rows blocked.

## Progress log
- 2026-06-21: Lane worktree `worktrees/eqp2-3` created from `origin/main@0f0f592` after EQP2-2 merge and detached proof passed.
- 2026-06-21: Added `docs/qualification/P0_AUTO_EVIDENCE.yaml`, status/backlog links, P0 evidence checker/wrappers, verify/CI wiring, focused tests, and routing/state updates while preserving P0 `BLOCKED` and `result_path: null`.
- 2026-06-21: Separate read-only review found live `origin/main` had advanced to PR #132. Rebased onto `origin/main@be2f504`, preserved `backend/app/core/error_safety.py` and `backend/tests/test_error_safety.py`, and confirmed `git diff --name-only --diff-filter=D origin/main` is empty.
- 2026-06-21: Post-rebase `.\scripts\verify.ps1` passed; DB smoke skipped because `RUN_DB_SMOKE` was not set.
- 2026-06-21: Live `origin/main` advanced again to PR #133. Rebased onto `origin/main@8822a14`, preserved `docs/adr/lane-d-0021-report-run-contract-backward-compat.md`, and reconfirmed no tracked deletions against `origin/main`.
- 2026-06-21: Post-PR #133 rebase `.\scripts\verify.ps1` passed; DB smoke skipped because `RUN_DB_SMOKE` was not set.
- 2026-06-21: Live `origin/main` advanced again to PR #134. Rebased onto `origin/main@af6dd94`, preserved report-run rights optionality changes, and reconfirmed no tracked deletions against `origin/main`.
- 2026-06-21: Post-PR #134 rebase `.\scripts\verify.ps1` passed; DB smoke skipped because `RUN_DB_SMOKE` was not set.
- 2026-06-21: Live `origin/main` advanced again to PR #136. Rebased onto `origin/main@71c6a74`, preserved the jsonschema mypy stub fix, and reconfirmed no tracked deletions against `origin/main`.
- 2026-06-21: Post-PR #136 rebase `.\scripts\verify.ps1` passed; DB smoke skipped because `RUN_DB_SMOKE` was not set.
