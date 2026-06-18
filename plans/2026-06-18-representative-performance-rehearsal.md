# Representative Performance Rehearsal

## Goal

Run and, where needed, harden the existing local release-candidate performance evidence
path so selected-county workflow load and spatial query-plan proof can be repeated from a
local candidate runtime without claiming hosted production capacity, formal SLOs, or
Level 10 completion.

## Non-goals

- No hosted load test, public endpoint, production SLO, autoscaling, dashboard, alert
  route, or capacity claim.
- No DS-017 vendor/source approval, paid-source use, entitlement implementation, or
  source-scope decision.
- No default live-load or DB runtime gate in release-readiness validation.
- No DB schema, API contract, report-semantics, source-status, geography, or rulepack
  change unless a repo-confirmed blocker is found.
- No committed measured runtime artifacts. Candidate evidence stays under ignored
  `local_artifacts/`.

## Current state

- `state/POST_RC_AUTHORITY_SPLIT.md` says local work may continue in the
  release-candidate package/performance rehearsal lane while hosted/source/vendor
  authority remains blocked.
- The Level 9/10 gate matrix in `state/LEVEL_9_10_GATE_MATRIX.md` keeps hosted
  deployment, hosted workload, DS-017, IdP/RBAC, billing, alerting, and external
  secret-manager proof out of repo-local claims.
- `config/performance_baseline.yaml`, `scripts/load_test_runner.py`, and the load-test
  wrappers already support valid area-create to report-run workflow traffic plus
  optional `load_test_result_v1` JSON evidence.
- `config/spatial_query_plan.yaml` and the spatial runtime checker already support
  read-only opt-in `EXPLAIN ANALYZE` evidence against an operator-supplied database and
  `area_id`.
- `R-015` made the local package boundary carry startup, plan, state, task, test, and
  selected-county fixture authority for handoff.

## Proposed design

Use the existing performance and spatial harnesses as the authority chain before adding
new implementation. First run validate-only checks to prove contracts and docs still
agree. Then run a local candidate runtime proof only if the runtime can be prepared
without seeding in validate-only actions or writing committed artifacts. If the rehearsal
finds a reproducibility gap, make the narrowest guard or runbook/test change needed to
fail closed the next time.

Rejected alternatives:

- Hosted load/staging proof is blocked until hosted platform and workload authority
  exists.
- Committing measured local artifacts would make the repo carry stale machine-specific
  evidence.
- Adding a new performance framework before exercising the existing standard-library
  runner and spatial checker would increase surface area without a proven need.

## Bottom-up sequence

1. Revalidate performance baseline, load-test validate-only, spatial static contract,
   release-readiness, and readiness-matrix checks.
2. Prepare a local candidate runtime/DB only if it can be isolated and kept out of git.
3. Run workflow-valid load proof with JSON output under `local_artifacts/`.
4. Run read-only spatial runtime plan proof with an explicit area ID and JSON output
   under `local_artifacts/`.
5. Patch only discovered reproducibility gaps in scripts/tests/runbooks; otherwise record
   the rehearsal as evidence-only local proof.
6. Update state logs while keeping `L10-PERF-*` hosted gates blocked, partial, or
   validate-only as appropriate.

## Files likely to change

| File | Expected change |
|---|---|
| `docs/runbooks/performance.md` | Clarify local rehearsal workflow only if the current instructions are incomplete. |
| `docs/runbooks/load_testing.md` | Clarify result capture only if rehearsal exposes an ambiguity. |
| `state/PROJECT_STATE.md` | Record active rehearsal scope and validation. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and local proof results. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Update next-pass routing without promoting hosted readiness. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\performance_baseline_check.py
.\scripts\run_performance_baseline_check.ps1
.\scripts\run_load_test.ps1 -ValidateOnly
python .\scripts\spatial_query_plan_check.py
.\scripts\run_spatial_query_plan_check.ps1
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
```

Optional runtime proof, only after an isolated candidate runtime and DB are prepared:

```powershell
.\scripts\run_load_test.ps1 -BaseUrl http://127.0.0.1:<port> -ResultDir .\local_artifacts\performance-baseline\<release-id>
.\scripts\run_spatial_query_plan_runtime_check.ps1 --area-id <prepared-area-id> --output-json .\local_artifacts\spatial-query-plan\<release-id>.json
```

Full handoff gate:

```powershell
.\scripts\verify.ps1
```

## Risks and blockers

- Local latency and query-plan evidence is machine- and fixture-dependent. It must be
  labeled as release-candidate rehearsal evidence, not a hosted SLO or capacity claim.
- Runtime proof must not be added to default release-readiness until a controlled
  representative runtime target exists.
- Spatial runtime proof is meaningful only when the supplied DB and `area_id` are
  representative enough for the intended selected-county workload.
- Hosted deployment, DS-017, IdP/RBAC, secret-manager, billing, alerting, and registry
  image publication remain external-authority blockers.

## Decision log

- 2026-06-18: Selected after `R-015` because `state/POST_RC_AUTHORITY_SPLIT.md`
  explicitly prefers the local package/performance rehearsal lane when external hosted
  and source/vendor decisions remain blocked.

## Progress log

- 2026-06-18: Plan opened after release-candidate package rehearsal proved the local
  source/runtime/operator handoff package boundary.
- 2026-06-18: Static performance/spatial/release validators passed. Isolated local
  runtime rehearsal first exposed a real background-job race: concurrent report jobs
  could both see the fixed internal not-evaluated sentinel source as absent, then one
  failed on duplicate `source_id` insert even though HTTP load-test requests were
  accepted.
- 2026-06-18: Fixed the race with a separate fixed-ID source `get_or_add` path using
  PostgreSQL `ON CONFLICT (source_id) DO NOTHING`; kept normal source registration
  strict for name/organization duplicates.
- 2026-06-18: Added focused source-service/source-repository coverage and a DB-gated
  concurrent background report regression that forces both sessions to observe the
  sentinel as missing, then asserts both jobs and report rows succeed and exactly one
  sentinel source row exists.
- 2026-06-18: Re-ran the patched local runtime rehearsal against an isolated DB on
  port `55461`: spatial runtime proof observed the configured target GIST indexes,
  workflow load passed `20/20` sequential and `40/40` concurrent requests, no report
  job errors were logged, and durable DB state showed `12` succeeded report jobs with
  one sentinel source row.
