# Source Freshness Review-Drift Guard

## Goal

Add repo-local fail-closed proof that Must-source registry freshness and review
metadata cannot silently drift stale while still being treated as production-ready.
This follows `state/LEVEL_9_10_GATE_MATRIX.md` and the Level 9/10 authority context in
`state/PRODUCTION_AUTHORITY_PACKET.md` without creating hosted alerts or changing any
source approval decision.

## Non-goals

- No DS-017 vendor selection, approval, connector implementation, or paid-source use.
- No hosted monitor, alert manager, dashboard, pager route, scheduler, or log-retention
  implementation.
- No source status, geography, rulepack, API, DB schema, report semantics, or connector
  expansion unless audit proves a narrow guard cannot work without it.
- No live vendor/network checks, generated evidence artifacts, secrets, screenshots, or
  DB dumps.

## Current state

- `R-012` added source-rights report exposure guarding, but Level 10 data-governance
  source freshness remains `PARTIAL`.
- `scripts/source_readiness.py --priority Must --json` reports source-use and connector
  readiness, but it does not yet fail closed on stale `Last Checked At` or review drift.
- `config/ops_alert_rules.yaml` contains a source-registry stale-review alert contract,
  but that is still validate-only and not a local freshness guard.
- `registers/data_source_registry.csv` and `db/seeds/source_registry_seeds.py` are the
  source-review metadata authority surfaces for this pass.

## Proposed design

Audit how `Freshness Class`, `Last Checked At`, review status, MVP priority, and source
readiness are parsed and seeded. Add the narrowest repo-local checker or source-readiness
extension that fails closed when Must current-effective sources have missing, malformed,
or stale review metadata, while preserving explicitly unreviewed/blocked DS-017 as a
known blocker rather than pretending it is ready.

## Bottom-up sequence

1. Audit registry CSV, seed mapping, source-readiness output, alert-rule catalog, and
   tests that pin source metadata.
2. Determine whether the guard belongs inside `scripts/source_readiness.py` or as a
   separate validate-only freshness checker composed by source-readiness tests.
3. Add focused tests for stale, missing, malformed, unreviewed, and current-effective
   Must-source review metadata.
4. Implement the smallest fail-closed guard that preserves the current selected-county
   source baseline and DS-017 blocked status.
5. Update state and validation logs without promoting hosted source monitoring or
   alert-routing readiness.

## Files likely to change

| File | Expected change |
|---|---|
| `scripts/source_readiness.py` | Freshness/review-drift guard or routing to a new focused checker. |
| `scripts/*source*freshness*` | Only if a separate validate-only checker is cleaner. |
| `backend/tests/*source*` | Artifact/unit tests for stale and current review metadata. |
| `config/ops_alert_rules.yaml` | Only if audit finds the stale-review alert contract inconsistent. |
| `state/PROJECT_STATE.md` | Record scope and validation. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and result. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\source_readiness.py --priority Must --json
python .\scripts\readiness_matrix_check.py
python .\scripts\alert_rules_check.py
cd backend; $env:PYTHONPATH='.'; python -m pytest -q .\tests\source_registry
cd backend; python -m ruff check <touched files>
cd backend; python -m mypy <touched files>
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers

- A date-based freshness guard can become noisy if it is not explicit about the review
  horizon and intentionally unreviewed blocked sources.
- DS-017 must remain blocked unless external source/vendor authority changes or a
  product decision removes it from Must scope.
- Hosted source freshness alerting remains blocked until alert manager, dashboard, and
  owner evidence exist.

## Decision log

- 2026-06-18: Selected as the next repo-local follow-on after the source-rights export
  guard because it addresses the adjacent data-governance drift risk without requiring
  hosted alerting or source/vendor authority.
- 2026-06-18: Placed the guard in `scripts/source_readiness.py` rather than a detached
  checker so stale Must current-effective source metadata changes the readiness result
  that release and private-MVP validators already consume.
- 2026-06-18: Kept the stale horizon at 90 days to match
  `config/ops_alert_rules.yaml`; the alerting artifact test pins the readiness and
  alert-rule constants to that machine-readable contract.

## Progress log

- 2026-06-18: Plan opened after `R-012` source-rights export guard.
- 2026-06-18: Added review-freshness fields and readiness blocking for Must
  current-effective sources with missing, malformed, future-dated, or older-than-90-day
  `Last Checked At` values, blank/unassigned review owners, or otherwise-ready
  non-current freshness classes. DS-017 remains blocked by existing review/rights/
  connector fields and is not treated as ready.
- 2026-06-18: Added source-readiness and alerting regressions for current, exactly
  90-day, stale, missing, malformed, future-dated, blank-owner, unassigned-owner,
  approved-but-unreviewed, and DS-017 blocked cases.
