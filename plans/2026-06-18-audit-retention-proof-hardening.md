# Audit-Retention Proof Hardening

## Goal

Prove that repo-local audit-event retention tooling can be exercised safely against an
isolated database in dry-run and explicit-apply modes, without provisioning hosted log
retention, hosted scheduler automation, SIEM export, or user-bound identity audit.

## Non-goals

- No hosted scheduler, hosted log-retention/export/SIEM, pager route, or production
  retention automation.
- No destructive default validation. Dry-run remains the default wrapper behavior.
- No broad audit schema changes, user-account tables, OAuth/OIDC, or full RBAC.
- No expansion of purge scope beyond cataloged audit-event retention classes.
- No deletion or mutation of local developer data outside an isolated test database.

## Current state

- `config/data_retention.yaml` defines retention classes and a repo-local audit purge
  schedule contract.
- `scripts/data_retention_check.py` validates the catalog, runbook, purge script, and
  wrappers.
- `scripts/purge_audit_events.py` supports dry-run by default and explicit `--apply`
  against `audit.events`.
- `backend/tests/scripts/test_purge_audit_events.py` contains DB-gated integration
  tests for purge behavior, but the next pass should re-audit whether dry-run/apply
  proof is composed clearly enough for release-candidate handoff.
- `state/LEVEL_9_10_GATE_MATRIX.md` keeps `L10-SEC-006` partial and `L10-SEC-007`
  validate-only because hosted log retention and production automation remain external
  authority. This plan preserves the Level 9/10 authority context: repo-local audit
  retention proof can be strengthened here, while hosted log retention, SIEM export,
  scheduler automation, and user-bound audit authority remain external.

## Proposed design

Use an isolated DB proof pass:

1. Audit `config/data_retention.yaml`, `scripts/data_retention_check.py`,
   `scripts/purge_audit_events.py`, wrappers, runbook text, and DB-gated tests.
2. Add the smallest validator/test hardening needed so dry-run default, explicit apply,
   in-scope event types, out-of-scope preservation, and hosted blockers are fail-closed.
3. If needed, add a local proof wrapper or documented command that exercises an isolated
   DB only when the caller has explicitly enabled DB smoke prerequisites.
4. Preserve `L10-SEC-006` and `L10-SEC-007` boundaries: repo-local purge proof is not
   hosted log retention, SIEM export, user-bound audit, or production automation.

Rejected alternatives:

- Provisioning hosted retention or scheduler infrastructure requires external platform
  authority.
- Making purge apply run by default would violate the dry-run-first safety boundary.
- Expanding purge scope beyond cataloged event types would risk deleting audit evidence
  that has no approved retention rule.

## Bottom-up sequence

1. Audit the retention catalog, purge script, wrappers, runbook, release-readiness
   composition, and DB-gated purge tests.
2. Tighten static checks around purge scope, dry-run defaults, explicit apply, and
   hosted blockers.
3. Add or refine DB-gated tests only if they can run against isolated state.
4. Run data-retention, release-readiness, readiness-matrix, focused tests, ruff, mypy,
   and full verification.
5. Update state logs without claiming hosted retention, hosted scheduler, SIEM export,
   or production audit completion.

## Files likely to change

| File | Expected change |
|---|---|
| `config/data_retention.yaml` | Clarify purge proof expectations only if audit finds gaps. |
| `scripts/data_retention_check.py` | Add static fail-closed checks for retention proof coverage if needed. |
| `scripts/purge_audit_events.py` | Tighten dry-run/apply behavior only if audit finds a concrete gap. |
| `docs/runbooks/data_retention.md` | Clarify isolated proof and hosted blockers if needed. |
| `backend/tests/test_data_retention_artifacts.py` | Add artifact tests for validator/runbook hardening. |
| `backend/tests/scripts/test_purge_audit_events.py` | Add DB-gated behavior tests if needed. |
| `state/PROJECT_STATE.md` | Record active audit-retention hardening scope and validation. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and residual risk. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\data_retention_check.py
.\scripts\run_data_retention_check.ps1
.\scripts\run_purge_audit_events.ps1
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
cd backend; python -m pytest -q .\tests\test_data_retention_artifacts.py .\tests\scripts\test_purge_audit_events.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

DB-gated purge tests should remain skipped unless the caller explicitly provides the
required DB smoke environment.

## Risks and blockers

- Repo-local purge proof does not prove hosted log retention, SIEM export, scheduler
  operation, or production audit completeness.
- Applying purge against the wrong database would be destructive; any apply proof must
  use isolated runtime state and explicit operator intent.
- Future audit event types must remain preserved until they are deliberately cataloged
  with a retention class.

## Decision log

- 2026-06-18: Selected after `R-020` because route-scope/RBAC handoff coverage tightens
  protected operator/reviewer boundaries, and the next repo-local security candidate is
  audit-retention proof hardening without hosted scheduler or log-retention authority.

## Progress log

- 2026-06-18: Plan opened as the next active repo-local lane after R-020.
