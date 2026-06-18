# Source-Rights Export Guard

## Goal

Add repo-local fail-closed proof that source-rights metadata controls whether
source-derived records, report artifacts, and exported outputs may expose restricted or
vendor-derived fields. This follows `state/LEVEL_9_10_GATE_MATRIX.md` and the
Level 9/10 authority context in `state/PRODUCTION_AUTHORITY_PACKET.md` without approving
DS-017 or any hosted production lane.

## Non-goals

- No DS-017 vendor selection, source review approval, connector implementation, or paid
  vendor ingestion.
- No hosted deployment, registry publication, secret-manager, billing, alerting, IdP, or
  full RBAC implementation.
- No public API, DB schema, report-semantics, geography, or rulepack expansion unless a
  focused audit proves the guard cannot be implemented without it.
- No generated evidence artifacts, secrets, vendor data, screenshots, or DB dumps.

## Current state

- `state/PRODUCTION_AUTHORITY_PACKET.md` now records that DS-017 requires field-level
  allow/deny policy, entitlement, export, cache, raw-data, AI-use, and cost authority
  before implementation.
- `scripts/source_readiness.py --priority Must --json` still reports
  `sources=8 ready=7 blocked=1`; DS-017 is blocked.
- Current source-rights fields live in `registers/data_source_registry.csv`, mirrored in
  `db/seeds/002_seed_source_registry.sql`, and interpreted through source-readiness and
  usage-rights helpers.
- Existing reports must continue to preserve evidence, caveats, and reproducibility
  without leaking restricted or unapproved source fields.

## Proposed design

Trace current export/report/source-use paths from the registry rights fields to the
places where source-derived data leaves the system. Add the narrowest guard or test
surface that proves blocked, unknown, or restricted source rights fail closed for export
and report exposure unless an explicit approved scope says otherwise.

## Bottom-up sequence

1. Audit existing usage-rights helpers, source-readiness output, report artifact
   generation, JSON/Markdown export, and connector evidence paths.
2. Identify whether an existing helper should own export permission decisions or whether
   a small source-rights export helper is needed.
3. Add focused tests for blocked/unknown DS-017-like rights and at least one approved
   restricted public-source case.
4. Implement the smallest guard that preserves current selected-county outputs while
   rejecting unapproved vendor/raw-field export.
5. Update runbooks/state only where the guard changes operator expectations.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/source_registry/*` | Source-rights/export helper or guard, if no suitable helper exists. |
| `backend/app/reports/*` | Only if report/export paths need a direct guard hook. |
| `backend/tests/source_registry/*` | Rights/export guard coverage. |
| `backend/tests/reports/*` | Regression coverage for report/export fail-closed behavior if affected. |
| `docs/runbooks/*` | Minimal operator note if behavior changes. |
| `state/PROJECT_STATE.md` | Record scope and validation. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and result. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\source_readiness.py --priority Must --json
python .\scripts\readiness_matrix_check.py
cd backend; $env:PYTHONPATH='.'; python -m pytest -q .\tests\source_registry .\tests\reports
cd backend; python -m ruff check <touched files>
cd backend; python -m mypy <touched files>
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers

- `restricted` may currently mean production-allowed in source-readiness, but export
  exposure still needs an explicit enforcement path for each restriction.
- The guard must not remove evidence required for report reproducibility; it should
  suppress or block unapproved exposed fields while preserving caveats and source-failure
  records.
- DS-017 remains blocked unless product/vendor authority changes or the source is
  explicitly removed/deferred from full-release Must scope.

## Decision log

- 2026-06-18: Selected as the next repo-local follow-on after the production authority
  packet because it reduces the highest DS-017-adjacent leakage risk without requiring a
  vendor, hosted platform, or external authority.

## Progress log

- 2026-06-18: Plan opened after `R-011` production authority packet.
