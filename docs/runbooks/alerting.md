# Alerting Runbook

## Purpose

Use `config/ops_alert_rules.yaml` as the repo-local alert-rule catalog for Level 10
production hardening. The catalog maps existing health, metrics, queue, deployment,
backup/restore, and source-readiness signals to severity, ownership, escalation, and
validation evidence.

These rules do not weaken the evidence-before-claim contract, bypass connector review, or
assert legal, buildability, title, water, wetland jurisdiction, appraisal, lending, or
investment conclusions.

## Rule Sources

| Signal | Source of truth | Notes |
|---|---|---|
| API health | `/health` | Public liveness and environment status |
| Runtime metrics | `/metrics` | In-memory `runtime_metrics_v1` request counters and durations |
| Queue health | `/operations/queue-health` | Reviewer-authenticated report/live connector queue counts, queued age, running age, and stale-running count |
| Deployment smoke | `scripts/run_deployment_smoke.ps1` | Compose-backed health, metrics, queue health, and report workflow |
| DB smoke | `scripts/verify.ps1`, `scripts/db_smoke_check.py` | Migrations, seeds, and DB schema proof when `RUN_DB_SMOKE=1` |
| Backup/restore | `scripts/run_backup_restore_check.ps1` | Dump, restore, DB smoke, and restore DB cleanup proof |
| Source readiness | `scripts/source_readiness.py --priority Must --json` | Reviewed source-rights readiness for Must sources |
| Source freshness | `registers/data_source_registry.csv` | `Freshness Class` and `Last Checked At` for reviewed source rows |
| Cost monitoring | `scripts/run_cost_monitoring_check.ps1` | Cost categories, report count metrics, and paid-source guardrails |

## Validate Rules

Run from the repository root:

```powershell
.\scripts\run_alert_rules_check.ps1
```

The Windows and POSIX wrappers delegate to `scripts/alert_rules_check.py` so local
and CI validation use the same validate-only logic.

The check is validate-only. It verifies that the alert catalog and runbook exist, required
high-severity and stale-data rules are present, referenced proof artifacts exist,
`docker compose config --quiet` passes when Docker is available, source-readiness JSON has
the expected shape, and Must source rows carry parseable freshness metadata.

## Operator Workflow

1. Classify the firing rule by `severity` in `config/ops_alert_rules.yaml`.
2. Open `docs/runbooks/incident_response.md` for SEV0 or SEV1, and for any SEV2 that
   threatens report correctness, source authority, queue recovery, or user trust.
3. Capture the current signal payload or command output before mitigation.
4. For queue alerts, inspect `/operations/queue-health`, then use the linked
   `/ui/report-runs?status=running` or `/ui/live-connector-jobs?status=running&stale=true`
   drilldown before remediation. Treat `stale_running` as a worker-progress signal and
   avoid retry loops until the running job, failed job lineage, and source-review state
   are understood.
5. For source-readiness or stale-source alerts, do not approve new connector evidence until
   the source/review operator confirms rights, freshness, and caveats.
6. Close the alert only after the corresponding validation proof passes.

## Escalation Notes

- `safety_contract_check_failed` is SEV0 because unsupported report semantics can mislead
  users even if infrastructure is healthy.
- Health, deployment, DB, and backup/restore failures are SEV1 because they affect core
  workflow availability or recovery confidence.
- Queue backlog, stale running jobs, connector failures, metrics loss, and
  source-readiness/freshness drift are SEV2 unless they also indicate unsafe output, data
  exposure, or evidence corruption.
- Cost-monitoring check failure is SEV2 because unmetered growth can make batch/report
  operation unsafe to expand even when user-facing APIs are healthy.

## Known Limits

- This catalog is repo-local. It does not create hosted alert routing, dashboards, a pager,
  or a named production on-call rotation.
- Runtime metrics are in-memory and reset on process restart.
- `/operations/queue-health` is reviewer-authenticated and must be queried with reviewer
  service-account headers in deployed environments.
- Source freshness rules validate registry metadata and operator review cadence; they do
  not independently verify every upstream vendor dataset in real time.
