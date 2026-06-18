# Jurisdiction/Rulepack Checklist Dry Run

## Goal

Dry-run the existing jurisdiction and rulepack readiness checklists against the next
candidate expansion shape without selecting a new geography, approving a rulepack,
starting live connector work, or claiming hosted production readiness. The pass should
show whether the current checklists are executable and fail-closed enough for future
Level 9/10 expansion decisions.

## Non-goals

- No new state, county, jurisdiction, rulepack, source, connector, or vendor selection.
- No DS-017 implementation or entitlement decision.
- No hosted deployment, hosted alerting, full IdP/RBAC, billing, secret-manager, or
  registry image work.
- No legal, fair-housing, zoning, lending, insurance, appraisal, investment, or
  residential recommendation conclusion.
- No production readiness or Level 10 completion claim.

## Current state

- `state/POST_RC_AUTHORITY_SPLIT.md` lists jurisdiction/rulepack checklist dry run as a
  repo-local candidate.
- `state/LEVEL_9_10_GATE_MATRIX.md` preserves the Level 9/10 distinction: MVP scope
  boundaries and red-flag regression suites are private-MVP proven, while hosted
  deployment, external review, DS-017, identity/RBAC, and production workload claims
  remain blocked or partial.
- `docs/checklists/jurisdiction_readiness.md` and
  `docs/checklists/rulepack_readiness.md` are already release-readiness artifacts, but
  this lane has not yet rehearsed them against a concrete future expansion packet.

## Proposed design

Use a dry-run only workflow:

1. Determine whether the checklists are intended to be exhaustive or intentionally
   scoped.
2. Pick a hypothetical candidate expansion shape from existing docs/state only; do not
   select or approve it.
3. Walk both checklists and record which items can be satisfied from current repo-local
   evidence and which fail closed on missing external authority.
4. Add the smallest validator or documentation hardening only if the dry run exposes a
   concrete checklist ambiguity or silent-pass risk.
5. Preserve all product, source, legal, hosted, and identity blockers.

Rejected alternatives:

- Selecting a new county or rulepack would exceed current authority.
- Implementing a new connector would bypass the readiness checklist purpose.
- Treating a checklist dry run as approval would collapse the Level 9/10 boundary.

## Bottom-up sequence

1. Audit the two checklist files and their release-readiness references.
2. Identify the smallest existing candidate expansion packet or placeholder that can
   exercise the checklist without new source/geography decisions.
3. Produce a dry-run result or guard that distinguishes repo-confirmed evidence,
   missing evidence, and external blockers.
4. Run release-readiness, private-MVP, readiness-matrix, and focused checklist tests.
5. Update state logs without promoting any new geography/rulepack/source.

## Files likely to change

| File | Expected change |
|---|---|
| `docs/checklists/jurisdiction_readiness.md` | Clarify checklist semantics only if ambiguity is found. |
| `docs/checklists/rulepack_readiness.md` | Clarify checklist semantics only if ambiguity is found. |
| `docs/runbooks/release_readiness.md` | Update only if checklist dry-run proof becomes a release artifact. |
| `scripts/*` | Add a small validator only if needed to prevent checklist drift. |
| `backend/tests/*` | Add focused artifact tests only for changed checklist/validator behavior. |
| `state/PROJECT_STATE.md` | Record active dry-run scope and validation. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and residual risk. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Update routing without promoting Level 10 or expansion readiness. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\private_mvp_readiness_check.py
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
cd backend; python -m pytest -q .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

Narrow checks may be refined after the audit identifies the actual affected files.

## Risks and blockers

- A dry run can prove checklist executability, but it cannot approve a new
  jurisdiction, rulepack, connector, source, or residential expansion.
- Checklist ambiguity can create false confidence if missing legal/source/geography
  evidence is not recorded as a blocker.
- Future expansions can weaken protected-class/proxy, overclaim, source-rights, or
  evidence-lineage boundaries unless they are routed back through the existing guards.

## Decision log

- 2026-06-18: Selected after `R-018` because threat/proxy audit hardening completed and
  `state/POST_RC_AUTHORITY_SPLIT.md` lists jurisdiction/rulepack checklist dry run as
  the next unblocked repo-local candidate. This keeps Level 9/10 expansion readiness
  separate from hosted production, legal review, DS-017, and new geography approval.

## Progress log

- 2026-06-18: Plan opened after R-018 added threat/proxy audit guardrails and kept
  external security/legal/hosted/identity/source blockers intact.
