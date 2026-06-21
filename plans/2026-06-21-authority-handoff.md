# Production Authority Handoff Hardening

## Goal
Make the external authority intake runbook directly usable as an evidence-collection
handoff for DS-017, hosted platform, secrets, identity/RBAC, image publication, billing,
hosted observability, and Bologna recorded-source authority.

## Non-goals
- Do not approve sources, select vendors, provision hosted infrastructure, publish
  images, write secrets, create billing integration, select a Bologna AOI, capture
  fixtures, create runtime artifacts, mutate the database, or claim Level 10 authority.
- Do not change source readiness, release-readiness semantics, API/UI behavior, report
  behavior, schemas, connectors, or fixture corpora.
- Do not start Bologna implementation or multi-geography framework implementation.

## Current state
Live `origin/main` is `c58d22450044cf055f719af3feeb27c9c7d37e1f`, which merged PR
#117 (`PR116-SYNC`). The root checkout remains the dirty preserved
`codex/r026-raw-readiness-ui` lane, so this work is isolated in
`worktrees/auth-handoff`.

`config/production_authority_intake.yaml` is already the machine-readable authority
stream map and cross-checks against the lower-level catalogs. The runbook currently
names those catalogs and boundaries, but it does not enumerate each stream's required
evidence fields. That makes it weaker as a handoff checklist and easier for future
changes to drift from the catalog.

`state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context. This slice
may improve external evidence collection clarity, but it must keep every authority
stream blocked until cited external evidence exists.

## Proposed design
Keep `config/production_authority_intake.yaml` as the source of truth and harden the
handoff surface around it:

- expand `docs/runbooks/production_authority_intake.md` with an evidence checklist for
  every configured authority stream;
- tighten `scripts/production_authority_intake_check.py` so the runbook must cite every
  stream id, source catalog, required evidence field, and stream-specific role,
  attestation, or blocked-category field;
- update artifact tests to prove the same runbook/catalog parity;
- refresh routing/state to point at this authority-handoff hardening slice instead of
  the completed PR116 sync.

Rejected alternative: start DS-017, hosted, or Bologna implementation. The authority
streams still have empty `authority_references`, `evidence_status: missing`, and
`decision_updates_allowed: false`, so implementation would be an inference rather than
an evidence-led step.

## Bottom-up sequence
1. Reconfirm live `origin/main`, worktree placement, and baseline authority validators.
2. Harden the runbook and checker/test parity against the existing intake catalog.
3. Refresh plan/state/task/log routing and the Level 9/10 next-pass prose.
4. Run focused validators, source-readiness proof, no-deletion checks, workspace
   validation, and full verification.
5. Publish and merge only if CI passes; after merge, revalidate detached live main and
   remove the worktree.

## Files likely to change

| File | Expected change |
|---|---|
| `plans/2026-06-21-authority-handoff.md` | New execution plan |
| `docs/runbooks/production_authority_intake.md` | Add external evidence checklist |
| `scripts/production_authority_intake_check.py` | Validate runbook/catalog parity |
| `backend/tests/test_production_authority_intake_artifacts.py` | Prove runbook parity |
| `plans/README.md` | Route current plan |
| `state/PROJECT_STATE.md` | Record current checkpoint and boundaries |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Refresh next-pass prose without promotion |
| `tasks/task_queue.yaml` | Add `AUTH-HANDOFF` |
| `state/WORKLOG.md` | Add worklog entry |
| `state/VALIDATION_LOG.md` | Record validation |

## Tests / verification
```powershell
py -3.12 .\scripts\production_authority_intake_check.py
py -3.12 .\scripts\source_entitlement_check.py
py -3.12 .\scripts\bologna_recorded_source_corpus_check.py
py -3.12 .\scripts\bologna_preflight_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
py -3.12 .\scripts\source_readiness.py --priority Must --json
cd backend; py -3.12 -m pytest tests\test_production_authority_intake_artifacts.py tests\test_source_entitlement_artifacts.py tests\test_bologna_recorded_source_corpus_artifacts.py -q
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signal: all checks pass, no deleted files are present, and Must-source readiness
remains `sources=8 ready=7 blocked=1` with `DS-017` still blocked.

## Risks and blockers
The main risk is accidentally making a checklist sound like approval. This slice must
preserve blocked states, empty authority references, missing evidence status, and
Level 9/10 boundaries. The actual DS-017, hosted, identity, observability, artifact, and
Bologna implementation lanes remain blocked on external authority.

## Decision log
- 2026-06-21: Selected handoff hardening instead of another pure post-merge sync because
  it advances the next real blocker: collecting cited external authority evidence.

## Progress log
- 2026-06-21: Created `worktrees/auth-handoff` from live `origin/main` at
  `c58d22450044cf055f719af3feeb27c9c7d37e1f`.
- 2026-06-21: Baseline authority, Bologna, release, and readiness validators passed
  before edits.
- 2026-06-21: Expanded the production-authority intake runbook and tightened the
  checker/test parity against `config/production_authority_intake.yaml`.
- 2026-06-21: First full verification failed on a line-length lint issue in the focused
  test; wrapped the tuple and reran focused authority tests successfully.
- 2026-06-21: Final full `.\scripts\verify.ps1` passed.
