# Incident Response and Rollback Runbook

## Purpose

Use this runbook when the deployed land-diligence service is unavailable, producing
unsafe or misleading reports, failing connector review gates, losing job progress, or
showing evidence of data/security compromise.

The runbook is operational only. It must not be used to weaken the evidence-before-claim
contract, bypass source-rights review, or assert legal/buildability/title/water/wetland
jurisdiction conclusions.

## Severity Levels

| Severity | Trigger | User impact | Target response |
|---|---|---|---|
| SEV0 | Confirmed data exposure, credential leak, evidence/claim corruption, or report output that could materially mislead users at scale | Critical safety, privacy, or trust impact | Start immediately; freeze deploys and live connectors |
| SEV1 | Production API unavailable, DB unavailable, migrations failed, report workflow cannot complete, or backup/restore proof fails during an incident | Core workflow down or unreliable | Start within 30 minutes |
| SEV2 | Queue backlog, elevated report failures, connector source outage, stale source-readiness blockers, or degraded metrics with contained user impact | Workflow degraded but controllable | Start within 1 business day |
| SEV3 | Documentation drift, non-critical smoke failure, isolated fixture issue, or operator tooling defect with no current user impact | Operational follow-up | Track and schedule |

## Ownership

The incident owner is the operations on-call role for the deployment environment. Until a
named production rotation exists, the repo owner or current deployment operator is the
incident owner for local/preview environments.

Required roles:

| Role | Responsibility |
|---|---|
| Incident commander | Own severity, timeline, decisions, and closure |
| Backend operator | Run deployment, DB, queue, and report checks |
| Source/review operator | Validate connector source rights and review-gated evidence state |
| Communications owner | Record user/operator-facing status and post-incident notes |

For SEV0 and SEV1, the incident commander must not be the sole verifier of recovery. A
second operator or reviewer must verify the recovery evidence when available.

## Escalation

Escalate immediately when any of these are true:

- Credentials, private data, or paid/vendor data may be exposed.
- Reports may contain unsupported legal, buildability, title, water, wetland jurisdiction,
  appraisal, lending, or investment claims.
- Evidence records, claim links, or report artifacts may be corrupted.
- Migrations, backup/restore, or DB smoke checks fail.
- Source-rights authority is unclear for a live connector.
- A rollback or containment action could lose evidence or report audit history.

Escalation path:

1. Incident commander classifies severity and freezes deploys for SEV0/SEV1.
2. Backend operator captures current state using the checks below.
3. Source/review operator confirms whether source-derived evidence remains review-gated.
4. Communications owner records affected workflow, start time, status, and next update.
5. If recovery requires secrets, paid vendors, hosted infrastructure access, or data
   deletion, stop and escalate to the deployment owner before acting.

## First 15 Minutes

Run these from the repository root on Windows unless a production platform provides a
more authoritative equivalent:

```powershell
git status --short
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
.\scripts\run_deployment_smoke.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
docker compose ps
docker compose logs backend --tail 120
```

If the failure involves restore confidence, run:

```powershell
.\scripts\run_backup_restore_check.ps1
```

Record:

- incident ID or timestamp;
- severity;
- incident owner;
- affected API endpoints or workflows;
- current commit or deployed image tag;
- DB URL/environment name, not credentials;
- command results;
- whether live connectors were enabled;
- whether any connector evidence had not yet been approved for QA.

## Rollback and Mitigation

### Deployment Rollback

Use when the latest backend image, config, or Compose/runtime change fails smoke or breaks
the core workflow.

1. Freeze new deploys and pause nonessential worker execution.
2. Capture the current failing evidence:

   ```powershell
   .\scripts\run_deployment_smoke.ps1
   docker compose logs backend --tail 120
   docker compose ps
   ```

3. Revert to the last known-good image or commit through the deployment platform. In
   local Compose, rebuild from the known-good checkout and restart the backend.
4. Re-run deployment smoke:

   ```powershell
   .\scripts\run_deployment_smoke.ps1
   ```

5. Keep `ENABLE_LIVE_CONNECTORS=false` until the deployed API, DB smoke, queue health,
   and report workflow are stable.

### Database Rollback or Migration Mitigation

This repo does not currently provide automatic down migrations. Treat database rollback
as a restore-or-forward-fix decision.

1. Stop writers before changing DB state:

   ```powershell
   docker compose stop backend live-connector-worker
   ```

2. Run backup/restore proof if restore confidence is part of the decision:

   ```powershell
   .\scripts\run_backup_restore_check.ps1
   ```

3. Prefer a forward migration fix when evidence/report history is intact and the failure
   is localized.
4. Restore to a new database from the latest verified backup only when the incident owner
   has confirmed the target backup, target environment, and data-loss window.
5. After recovery, run:

   ```powershell
   $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
   .\scripts\run_deployment_smoke.ps1
   ```

### Connector or Source Outage

Use when DS-001, DS-002, DS-003, or DS-004 live source behavior is unavailable,
malformed, transfer-limited, or source rights are unclear.

1. Disable request-time live connectors:

   ```powershell
   $env:ENABLE_LIVE_CONNECTORS='false'
   ```

2. Do not approve connector evidence until source-failure evidence and retrieval
   provenance have been reviewed.
3. Confirm source readiness:

   ```powershell
   py -3.12 .\scripts\source_readiness.py --priority Must --json
   ```

4. Use `/operations/queue-health` and `GET /connector-runs/live-jobs/{job_id}` to inspect
   queued or failed work without leasing jobs.

### Queue or Report Failure

Use when report jobs accumulate, fail repeatedly, or do not reach `succeeded`.

1. Inspect queue state:

   ```powershell
   curl http://localhost:8000/operations/queue-health `
     -H "X-Reviewer-Id: fixture-reviewer" `
     -H "X-Reviewer-Token: fixture-token-123"
   ```

2. Inspect a specific report:

   ```powershell
   curl http://localhost:8000/report-runs/<report_run_id>
   ```

3. Retry only failed report jobs, and preserve lineage:

   ```powershell
   curl -X POST http://localhost:8000/report-runs/<report_run_id>/retry `
     -H "X-Reviewer-Id: fixture-reviewer" `
     -H "X-Reviewer-Token: fixture-token-123"
   ```

4. If retry fails repeatedly, classify as at least SEV2 and inspect DB/job/log evidence
   before further retries.

## Recovery Criteria

Do not close the incident until all applicable checks pass:

```powershell
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
.\scripts\run_deployment_smoke.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
.\scripts\run_incident_rollback_check.ps1
```

The Windows and POSIX wrappers delegate to `scripts/incident_rollback_check.py` so
local and CI validation use the same validate-only logic.

For connector incidents, also confirm:

- source-failure evidence exists for failed source calls;
- unapproved connector evidence is excluded from reports;
- source readiness still reports reviewed sources only as ready.

## Closure Record

Record the closure in the incident tracker or validation log with:

- severity and owner;
- start/end time;
- root cause;
- affected workflows;
- rollback or mitigation used;
- checks run and results;
- any data-loss window, or explicit "no data loss found";
- follow-up work and owner.

## Known Limits

- This runbook defines repo-local and Compose-local recovery proof. Hosted deployment
  rollback depends on the production platform.
- No production on-call schedule, pager, or named human escalation list is stored in the
  repo.
- No automated down migrations exist; DB rollback is restore-or-forward-fix.
- Repo-local alert rules exist in `config/ops_alert_rules.yaml`, but hosted dashboards,
  alert routing, and pager integration are not yet implemented.
