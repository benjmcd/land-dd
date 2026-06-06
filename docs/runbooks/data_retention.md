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
- **hosted_log_retention** — Out of scope for local-only operation; hosted log
  retention or SIEM export is only relevant after an explicit hosting scope change.

Do not delete `reports.report_runs`, `evidence.observations`, `jobs.job_queue`, or
`source.ingest_runs` rows without explicit operator sign-off. Deleting evidence breaks
report reproducibility.

---

## How to manually purge audit events

Audit events targeted for 90-day retention live in `audit.events`. To purge events older
than 90 days, connect to the Postgres database and run:

```sql
-- Preview rows that would be deleted (dry run)
SELECT count(*)
FROM audit.events
WHERE recorded_at < now() - interval '90 days';

-- Delete rows older than 90 days
DELETE FROM audit.events
WHERE recorded_at < now() - interval '90 days';
```

Before running the DELETE:

1. Confirm the retention decision with the security reviewer.
2. Back up or export the rows if required for compliance.
3. Record the deletion in `state/WORKLOG.md` with date, row count, and approver.

There is no automated job for this procedure. It must be triggered manually.

---

## Future work

- Implement automated purge job for `audit.events` rows older than 90 days.
- Keep hosted log retention / SIEM export deferred unless hosting scope is explicitly
  approved.
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
