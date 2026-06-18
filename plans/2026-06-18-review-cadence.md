# Source Review Cadence Consistency

## Goal

Make source-review cadence prose and runbook guidance consistent with the repo-local
90-day Must-source freshness horizon enforced by `scripts/source_readiness.py` and
`scripts/alert_rules_check.py`. This follows the Level 9/10 authority context in
`state/LEVEL_9_10_GATE_MATRIX.md` and keeps `L10-DATA-003` partial until hosted alert
delivery evidence exists.

## Non-goals

- No live source terms refresh, URL crawl, vendor negotiation, or source approval.
- No DS-017 vendor selection, approval, connector implementation, or paid-source use.
- No hosted monitor, alert manager, dashboard, pager route, or scheduled job.
- No change to current `Last Checked At` values, source statuses, geographies,
  connectors, DB schema, API contracts, or report semantics.

## Current state

- `R-013` added a repo-local readiness guard: Must current-effective sources stop
  counting as connector-ready when review freshness metadata is missing, malformed,
  future-dated, older than 90 days, or lacks a real review owner.
- `config/ops_alert_rules.yaml` is the stale-source alert contract authority for the
  90-day horizon, and `backend/tests/test_alerting_artifacts.py` now pins that horizon
  against the source-readiness guard constant.
- Read-only review found possible drift between machine-enforced 90-day freshness and
  human-facing source-review cadence language. That should be audited before more
  source-governance work is built on top of the new guard.

## Proposed design

Audit source-review documents and runbooks that mention next review dates, review
cadence, or freshness expectations. Add the narrowest static guard or wording update so
the machine-enforced 90-day Must-source horizon cannot be contradicted by prose while
still allowing source-specific update cadence caveats and explicitly blocked/unreviewed
sources.

## Bottom-up sequence

1. Audit source-review docs, alerting/release/operator runbooks, and source registry
   wording for `next review`, `review cadence`, `90 days`, and stale freshness claims.
2. Identify canonical wording for the machine-enforced review horizon versus
   source-specific upstream update cadence.
3. Add or extend a validate-only checker/test only if current prose can drift without a
   failing guard.
4. Update affected docs with narrow language that preserves DS-017 and hosted-alert
   blockers.
5. Run focused artifact/readiness checks and full verification before handoff.

## Files likely to change

| File | Expected change |
|---|---|
| `docs/source-reviews/*.md` | Only if cadence prose contradicts the 90-day guard. |
| `docs/runbooks/alerting.md` | Clarify machine-enforced freshness horizon if needed. |
| `docs/runbooks/release_readiness.md` | Clarify release-readiness boundary if needed. |
| `backend/tests/*alert*` or `scripts/*check*.py` | Static guard only if audit finds drift risk. |
| `state/PROJECT_STATE.md` | Record scope and validation. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and result. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\check_source_registry.py
python .\scripts\source_readiness.py --priority Must --json
python .\scripts\alert_rules_check.py
python .\scripts\readiness_matrix_check.py
cd backend; python -m pytest -q .\tests\test_alerting_artifacts.py .\tests\source_registry
cd backend; python -m ruff check <touched files>
cd backend; python -m mypy <touched files>
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers

- A prose guard must not force live source re-review or imply hosted monitoring exists.
- Upstream update cadence and local review cadence are different concepts; do not
  collapse them into one field.
- DS-017 remains blocked unless external source/vendor authority changes or a product
  decision removes it from Must scope.

## Decision log

- 2026-06-18: Selected as the next repo-local follow-on after `R-013` because the new
  source-readiness freshness guard is strongest when source-review prose cannot
  contradict its 90-day horizon.

## Progress log

- 2026-06-18: Plan opened after `R-013` source freshness review-drift guard.
