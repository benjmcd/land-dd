# Data Retention Runbook

## Policy summary

The MVP retains all operational data (report runs, evidence, job queue records, source
ingest runs) indefinitely. Audit events (access logs, API-key auth events in
`audit.events`) have a target retention period of **90 days**, but no automated purge
procedure exists yet. All data deletion is a manual operator action in MVP scope.

---

## Retention classes

Retention classes are catalogued in `config/data_retention.yaml`. Each class specifies:

| Field | Meaning |
|---|---|
| `id` | Stable identifier for the retention class |
| `description` | Which table/queue the class covers |
| `retention_period` | Target period (`indefinite_mvp` or `90_days_target`) |
| `deletion_approach` | How deletion is handled (`manual_operator` or `not_yet_automated`) |
| `data_sensitivity` | Sensitivity label for the class |
| `blocker` | Why automated deletion is not yet in place |

To review the full catalog:

```powershell
Get-Content config\data_retention.yaml
```

or:

```bash
cat config/data_retention.yaml
```

---

## MVP scope limitation

No automated deletion procedures are implemented. All data deletion is a manual operator
action. The current blockers are:

- **automated_deletion** — No automated deletion procedure implemented in MVP; all
  deletion is manual.
- **hosted_log_retention** — Hosted log retention system not yet provisioned.

Do not delete `reports.report_runs`, `evidence.observations`, `jobs.job_queue`, or
`source.ingest_runs` rows without explicit operator sign-off. Deleting evidence breaks
report reproducibility.

---

## How to purge audit events

Audit events targeted for 90-day retention live in `audit.events`. The in-scope
event types are:

| Retention class       | event_type values           |
|-----------------------|-----------------------------|
| `audit_events`        | `created`, `superseded`     |
| `api_key_audit_events`| `api_key_auth`              |

A purge script exists at `scripts/purge_audit_events.py`. It deletes **only** the
in-scope event types listed above; any future event type with a different policy is
excluded by the explicit allowlist in the script.

### Step 1 — Dry run (always run first)

```powershell
.\scripts\run_purge_audit_events.ps1
```

or directly:

```powershell
py -3.12 scripts/purge_audit_events.py
```

The dry run prints the count of rows eligible for deletion per event type and the
cutoff date. No rows are written or deleted.

### Step 2 — Review output and confirm with security reviewer

Before applying:

1. Confirm the retention decision with the security reviewer.
2. Back up or export the rows if required for compliance.
3. Record the planned deletion in `state/WORKLOG.md` with date, expected row count,
   and approver name.

### Step 3 — Apply (manual operator action)

```powershell
py -3.12 scripts/purge_audit_events.py --apply
```

Custom retention window (override the 90-day default):

```powershell
py -3.12 scripts/purge_audit_events.py --apply --retention-days 90
```

The script prints the number of rows actually deleted and exits 0 on success.

### Notes

- There is no automated (scheduled) job for this procedure. It must be triggered
  manually by an operator.
- Pass `--db-url` to target a non-default database, or set the `DATABASE_URL_SYNC`
  environment variable.
- The script reads the default retention window from `config/data_retention.yaml`
  and falls back to 90 days if the YAML is unreadable.

---

## Future work

- Schedule the purge script (`scripts/purge_audit_events.py --apply`) as a cron job
  or operator runbook step once the operational process is agreed.
- Provision hosted log retention / SIEM export for `audit.events`.
- Assess GDPR/CCPA scope when user-identifying data is introduced.
- Add retention policy enforcement tests to CI once automated deletion exists.
- Revisit `indefinite_mvp` classes when operational data volume requires archival.

---

## Validation

Validate this runbook and the retention catalog with:

```powershell
.\scripts\run_data_retention_check.ps1
```

---

## Contact

Contact: operator / security reviewer.
