# Error-State / No-Leak Hardening

## Goal

Strengthen repo-local proof that current API/UI error and recovery surfaces do not leak
stack traces, secrets, raw connector payloads, or internal implementation details, while
preserving first-class source-failure evidence and without claiming hosted error/log
review.

## Non-goals

- No hosted error/log review, hosted SIEM/log-retention, pager route, or production
  observability claim.
- No broad API, UI, report-semantics, auth, or database schema redesign.
- No suppression of source-failure evidence; connector/source failures must remain
  explicit evidence rather than silent success.
- No legal, security-review, hosted IdP/RBAC, DS-017 entitlement, or production launch
  claim.

## Current state

- `state/LEVEL_9_10_GATE_MATRIX.md` keeps `L10-SEC-009` at `PARTIAL`: route error
  tests, auth failure pages, and threat/proxy audit error-leakage guards exist, but
  hosted error/log review is still blocked.
- This plan preserves the Level 9/10 authority context: repo-local error-state proof
  can be strengthened here, while hosted error/log review, hosted log-retention/SIEM,
  alerting, and production security review remain external authority.
- `config/threat_proxy_audit.yaml`, `docs/runbooks/threat_proxy_audit.md`, and
  `scripts/threat_proxy_audit_check.py` already model `production_error_leakage` and
  `production_error_log_review`.
- Current UI/API tests cover several safe error pages, auth failures, recovery preview,
  and report failure paths, but the next pass should audit whether raw exception text,
  tracebacks, secret-like values, local paths, or connector payload details can surface
  through common operator/reviewer workflows.

## Proposed design

Use a repo-local fail-closed proof pass:

1. Audit current API/UI error and recovery surfaces using the smallest relevant files,
   especially `backend/app/api/ui*.py`, `backend/app/api/reports.py`,
   `backend/app/api/connectors.py`, `backend/app/api/operations.py`,
   `backend/app/operations/recovery_preview.py`, existing UI/API tests, and the
   threat/proxy audit checker.
2. Add targeted regressions for the highest-risk error surfaces found: invalid route
   inputs, failed report/connector operations, recovery-preview failures, auth errors,
   and UI error pages.
3. Harden the threat/proxy audit checker or runbook only where it can enforce concrete
   repo-local evidence, while preserving the hosted error/log review blocker.
4. Keep source failures first-class: user-facing summaries should be safe, but evidence
   records may still carry source-failure metadata needed for auditability.

Rejected alternatives:

- Hosted error/log review requires external hosted logging and production authority.
- Broad exception-handler rewrites or report-semantics changes are unnecessary unless
  the audit finds a repo-confirmed leak path.
- Hiding all connector failures would violate the evidence-led source-failure contract.

## Bottom-up sequence

1. Audit existing error-safety controls and tests before editing.
2. Add targeted tests for any confirmed leak path or missing guard.
3. Implement the narrowest runtime/checker/runbook changes needed.
4. Run threat/proxy audit, access-control where affected, release-readiness,
   readiness-matrix, focused UI/API tests, ruff, mypy, diff hygiene, and full
   verification.
5. Update state logs without claiming hosted error/log review or production launch
   readiness.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/api/ui*.py` | Harden safe error rendering only if audit finds a concrete gap. |
| `backend/app/api/reports.py` | Harden failed-report or caveat error exposure only if needed. |
| `backend/app/api/connectors.py` | Harden connector error response exposure only if needed. |
| `backend/app/api/operations.py` | Harden recovery/operations error exposure only if needed. |
| `scripts/threat_proxy_audit_check.py` | Add concrete error-leakage guard checks if needed. |
| `backend/tests/api/*` | Add focused UI/API error-state regressions. |
| `backend/tests/test_threat_proxy_audit_artifacts.py` | Add artifact coverage if checker/runbook changes. |
| `docs/runbooks/threat_proxy_audit.md` | Clarify boundaries only if checker/test changes require it. |
| `state/PROJECT_STATE.md` | Record active error-state/no-leak hardening scope. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and residual risk. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\threat_proxy_audit_check.py
.\scripts\run_threat_proxy_audit_check.ps1
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
cd backend; python -m pytest -q .\tests\test_threat_proxy_audit_artifacts.py .\tests\api\test_ui_routes.py .\tests\api\test_ui_operations_routes.py .\tests\api\test_operations.py .\tests\api\test_report_run_list.py .\tests\api\test_connector_ingest_api.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers

- Repo-local error-state regressions do not replace hosted error/log review, SIEM/log
  retention, alert routing, or external security review.
- Connector/source failures must remain visible as source-failure evidence; the goal is
  safe presentation, not error suppression.
- Future hosted observability may expose different logs or middleware paths and must be
  reviewed separately.

## Decision log

- 2026-06-18: Selected after `R-021` because audit-retention proof hardening closed the
  next repo-local security/audit slice, and the remaining repo-local candidate in
  `state/POST_RC_AUTHORITY_SPLIT.md` is error-state/no-leak hardening.

## Progress log

- 2026-06-18: Plan opened as the next active repo-local lane after R-021.
