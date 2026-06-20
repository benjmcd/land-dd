# Post-SE001 Roadmap And Bologna Preflight

## Goal

Restore live routing after the merged `SE-001` source-entitlement packet and add a
validate-only Bologna recorded-source preflight so the next long-range milestone is
specific without being overclaimed.

The overarching target remains a repeatable, evidence-led land/locality due-diligence
compiler. The immediate system-visible outcome is an active plan/task lane that says
SE-001 is complete, DS-017 remains blocked, hosted authority remains external, and a
Bologna pilot cannot start until source, jurisdiction, rulepack, recorded-corpus, and
runtime proof prerequisites are explicitly satisfied.

## Non-goals

- No Bologna implementation, source selection, source registry promotion, connector,
  recorded-source fixture, DB seed, report behavior, API/UI behavior, or schema change.
- No DS-017 approval, vendor selection, paid-source metering, entitlement enforcement,
  owner/value/title exposure, or source-readiness promotion.
- No hosted deployment, hosted identity/RBAC, hosted observability/log retention,
  hosted object-store proof, billing, image publication, production workload proof, or
  Level 10 completion claim.
- No multi-geography framework implementation, new rulepack, legal interpretation, or
  reuse of the US homestead rulepack for Italy/EU scope.

## Current state

- Live `origin/main` is at merged PR #106
  `a508cd207c95fb79736340295c7eaaee908cc2bf`.
- `SE-001` added `config/source_entitlements.yaml`,
  `scripts/source_entitlement_check.py`, runbook/wrappers/tests, and release-readiness
  composition for DS-017. The packet is validate-only and keeps DS-017 blocked.
- Current validators pass: Must source readiness reports `sources=8 ready=7 blocked=1`
  with only `DS-017` blocked; source-entitlement, checklist dry-run, release-readiness,
  and Level 9/10 matrix checks pass.
- Routing is stale: `state/PROJECT_STATE.md`, `plans/README.md`, and
  `tasks/task_queue.yaml` still describe `SE-001` as active even though it has merged.
- Existing `config/checklist_dry_run.yaml` rehearses US jurisdiction/rulepack expansion
  against a hypothetical county-like candidate. It is not Bologna, Italy/EU, or
  recorded-source authority.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 gate authority and keeps
  hosted, DS-017, source, jurisdiction, rulepack, and production authority boundaries
  separate.

## Proposed design

Add `config/bologna_preflight.yaml` plus a validate-only checker/runbook. The preflight
is a machine-readable decision packet for what must be true before a Bologna
recorded-source pilot can start. It pins approval flags to false, requires missing or
blocked prerequisites to stay visible, and cross-checks the production authority packet
so the catalog cannot be mistaken for implementation approval.

Talmudic debate / coherence check:

- Position A: start hosted authority next. Rejected because platform, DNS/TLS, hosted
  DB, secret-manager, identity/RBAC, billing, alerting, object-store, and production
  workload authority are still external blockers.
- Position B: continue DS-017 engineering next. Rejected because SE-001 made the blocker
  decision-ready; the remaining action is a product/source/vendor authority decision,
  not local connector work.
- Position C: start Bologna implementation next. Rejected because no Bologna candidate
  authority, Italy/EU source-rights packet, rulepack scope, recorded-source corpus, CRS
  policy, or DB-backed report proof exists.
- Position D: add only a state/routing update. Rejected as insufficient because it would
  answer immediate staleness but not prevent the next long-term milestone from being
  interpreted too broadly.
- Position E: update routing and add a validate-only Bologna preflight. Accepted because
  it is the narrowest repo-local step that advances the long-term objective while
  preserving all external-authority blockers.

## Bottom-up sequence

1. Add failing/pinning tests for the Bologna preflight catalog, checker, runbook, and
   production-authority boundary.
2. Add `config/bologna_preflight.yaml`, `scripts/bologna_preflight_check.py`, and
   Windows/POSIX wrappers.
3. Add `docs/runbooks/bologna_preflight.md` and update
   `state/PRODUCTION_AUTHORITY_PACKET.md` with the Bologna pilot authority section.
4. Update manifest, plan index, task queue, project state, worklog, validation log, and
   Level 9/10 next-pass text so `BP-001` is active and `SE-001` is done.
5. Run focused tests/checkers, source/release/readiness validators, workspace
   validation, diff/no-deletion checks, and default `.\scripts\verify.ps1`.

## Files likely to change

| File | Expected change |
|---|---|
| `config/bologna_preflight.yaml` | New validate-only Bologna recorded-source preflight catalog. |
| `scripts/bologna_preflight_check.py` | New static checker for the catalog/runbook/authority packet. |
| `scripts/run_bologna_preflight_check.ps1` | Windows wrapper. |
| `scripts/run_bologna_preflight_check.sh` | POSIX wrapper. |
| `backend/tests/test_bologna_preflight_artifacts.py` | New artifact and fail-closed tests. |
| `docs/runbooks/bologna_preflight.md` | Operator interpretation and limits. |
| `state/PRODUCTION_AUTHORITY_PACKET.md` | Bologna pilot authority boundary. |
| `MANIFEST.md` | Route the new preflight authority surface. |
| `plans/README.md` | Mark SE-001 complete and route BP-001 active. |
| `tasks/task_queue.yaml` | Mark SE-001 done and add active BP-001. |
| `state/PROJECT_STATE.md` | New current checkpoint and future milestone sequence. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Next-pass text update only. |
| `state/WORKLOG.md` | Worklog entry. |
| `state/VALIDATION_LOG.md` | Validation entry. |

## Tests / verification

```powershell
py -3.12 -m pytest backend\tests\test_bologna_preflight_artifacts.py -q
py -3.12 .\scripts\bologna_preflight_check.py
.\scripts\run_bologna_preflight_check.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\source_entitlement_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signal: only active task is `BP-001`; Bologna preflight passes while keeping all
approval flags false; DS-017 remains the only blocked Must source; release and
readiness-matrix validators pass; no tracked deletions are present; default verify
passes. DB smoke remains default-off unless explicitly requested.

## Risks and blockers

- A Bologna preflight can be mistaken for Bologna approval. The catalog, checker,
  runbook, and authority packet must all say it is validate-only and not started.
- The existing US checklist cannot be treated as Italy/EU readiness. The preflight must
  name it as a useful pattern only.
- DS-017 is separate from Bologna recorded-source work but still affects the broader
  release boundary. The preflight should require an explicit DS-017 path without
  implying a vendor approval.
- Hosted authority remains external. Local recorded-source proof cannot become hosted
  production proof by wording.

## Decision log

- 2026-06-20: Chose a validate-only Bologna preflight plus routing update after live
  validation showed SE-001 merged, DS-017 still blocked, hosted authority still external,
  and no Bologna authority surface in the current repo.

## Progress log

- 2026-06-20: Opened clean `worktrees/authority-next` on `codex/authority-next` from
  live `origin/main` at `a508cd207c95fb79736340295c7eaaee908cc2bf`. Baseline source
  readiness, source-entitlement, checklist dry-run, release-readiness, and
  readiness-matrix validators passed before edits.
