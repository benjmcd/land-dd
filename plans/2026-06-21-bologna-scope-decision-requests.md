# Bologna Scope Decision Requests

## Goal
Make the blocked Bologna pilot-scope authority gate actionable by adding structured
decision-request entries for every required scope decision. The request entries should
tell a future operator exactly what evidence must be supplied while preserving the
current blocked, uncited, validate-only boundary.

## Non-goals
- Do not select a Bologna AOI, approve Italy/EU/local sources, change source rights,
  promote source registry rows, capture fixtures, run connectors, seed the database, or
  create report/runtime artifacts.
- Do not approve DS-017, provision hosted services, implement hosted identity/RBAC,
  publish images, add billing, or claim Level 10 authority.
- Do not edit per-source rights rows or recorded-source corpus rows as if authority
  exists.

## Current state
Live `origin/main` is `df96c21f9445fc5cb915d2b06ec0b2eb6c731f2f`, which merged PR
#121 (`BPS-001`). The root checkout remains dirty preservation state, so this slice is
isolated in `worktrees/bol-req`.

This plan preserves the Level 9/10 authority boundary documented in
`state/LEVEL_9_10_GATE_MATRIX.md`; it does not move any Level 9/10 external gate from
blocked to approved.

`config/bologna_pilot_scope_authority.yaml` records the required scope-decision IDs,
but the evidence expectations still live mostly as prose. That creates a narrow
handoff gap: a future operator knows which slots are missing, but not the minimum
reference shape each slot must provide.

## Proposed design
Add `scope_decision_requests` to `config/bologna_pilot_scope_authority.yaml`. Each entry
will have:

- `id` matching one required scope decision;
- `status: missing_authority`;
- `expected_reference` text;
- non-empty `minimum_evidence`;
- `downstream_use` text;
- empty `authority_references`;
- `decision_updates_allowed: false`.

The pilot-scope checker will require request IDs to exactly match
`required_scope_decisions`, and production-authority intake will cross-check its
`bologna_pilot_scope` stream against both lists. The runbook will name the structured
request table so the machine-readable packet is the source of truth.

Rejected alternative: create a separate request YAML. That would add another authority
surface when the existing pilot-scope packet can carry the request shape directly.

Rejected alternative: start editing source-authority intake. That still requires cited
product/AOI/source-review authority and would overstep the current blocker.

## Bottom-up sequence
1. Add structured decision-request rows to the existing pilot-scope authority catalog.
2. Update the pilot-scope checker and focused tests to require exact coverage and
   fail-closed request state.
3. Update production-authority intake validation so release-level required evidence
   cannot drift from the request rows.
4. Update runbook/state/routing surfaces to make `BPS-REQ-001` the current validate-only
   follow-up.
5. Run focused validators/tests, no-deletion checks, workspace validation, and full
   verification before publication.

## Files likely to change

| File | Expected change |
|---|---|
| `config/bologna_pilot_scope_authority.yaml` | Add structured scope decision requests |
| `scripts/bologna_pilot_scope_authority_check.py` | Validate request coverage/state |
| `scripts/production_authority_intake_check.py` | Cross-check intake against request IDs |
| `backend/tests/test_bologna_pilot_scope_authority_artifacts.py` | Add request coverage/fail-closed tests |
| `backend/tests/test_production_authority_intake_artifacts.py` | Prove intake/request alignment |
| `docs/runbooks/bologna_pilot_scope_authority.md` | Document the structured request boundary |
| `plans/README.md` | Route the current plan |
| `state/PROJECT_STATE.md` | Record checkpoint and next pursuit |
| `tasks/task_queue.yaml` | Add `BPS-REQ-001` |
| `state/WORKLOG.md` | Add worklog entry |
| `state/VALIDATION_LOG.md` | Record validation |

## Tests / verification
```powershell
py -3.12 .\scripts\bologna_pilot_scope_authority_check.py
py -3.12 .\scripts\production_authority_intake_check.py
py -3.12 .\scripts\bologna_preflight_check.py
py -3.12 .\scripts\release_readiness_check.py
cd backend; py -3.12 -m pytest tests\test_bologna_pilot_scope_authority_artifacts.py tests\test_production_authority_intake_artifacts.py tests\test_readiness_core_artifacts.py -q
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signal: all checks pass; `DS-017` remains the only blocked Must source; no
Bologna authority is approved.

## Risks and blockers
The main risk is creating wording that looks like an approval workflow. The structured
requests must remain missing, uncited, and update-disallowed until external evidence
exists.

## Decision log
- 2026-06-21: Selected structured request rows inside the existing pilot-scope packet
  because it advances authority collection without creating a second source of truth.

## Progress log
- 2026-06-21: Created `worktrees/bol-req` from live `origin/main` at
  `df96c21f9445fc5cb915d2b06ec0b2eb6c731f2f`.
