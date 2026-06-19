# Data Retention Runbook

## Policy summary

The MVP retains all operational data (report runs, evidence, job queue records, source
ingest runs) indefinitely. Audit events (access logs, API-key auth events in
`audit.events`) have a target retention period of **90 days**. A repo-local audit
retention schedule contract now records the dry-run-first purge command, target event
types, weekly cadence, and manual apply gates; the hosted scheduler is not provisioned
yet. Any applied data deletion remains a manual operator action in MVP scope.

---

## Retention classes

Retention classes are catalogued in `config/data_retention.yaml`. Each class specifies:

| Field | Meaning |
|---|---|
| `id` | Stable identifier for the retention class |
| `description` | Which table/queue the class covers |
| `retention_period` | Target period (`indefinite_mvp` or `90_days_target`) |
| `deletion_approach` | How deletion is handled (`manual_operator` or `automated_script_dry_run_default`) |
| `data_sensitivity` | Sensitivity label for the class |
| `blocker` | Current hosted-production blocker or retention limit |

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

Repo-local audit purge tooling and the repo-local audit retention schedule contract are
implemented as validate-only artifacts. The current blockers are:

- **automated_deletion** - Repo-local audit purge command and schedule contract exist;
  hosted scheduler and automatic approval workflow are not provisioned.
- **hosted_log_retention** - Hosted log retention system not yet provisioned.

Do not delete `reports.report_runs`, `evidence.observations`, `jobs.job_queue`, or
`source.ingest_runs` rows without explicit operator sign-off. Deleting evidence breaks
report reproducibility.

The schedule contract is intentionally not a hosted scheduler. It keeps the command and
approval boundary explicit until platform scheduling, alerting, and log-retention
authority exist.

| Field | Current value |
|---|---|
| Runner | `scripts/purge_audit_events.py` |
| Dry-run wrappers | `scripts/run_purge_audit_events.ps1`, `scripts/run_purge_audit_events.sh` |
| Cadence | Weekly |
| Default mode | Dry run; no rows deleted |
| Target retention classes | `audit_events`, `api_key_audit_events` |
| Target event types | `created`, `superseded`, `api_key_auth` |
| Apply gates | `--apply`, security reviewer approval, backup/export, `state/WORKLOG.md` entry |
| Hosted scheduler | Blocked |

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

### Step 1 - Dry run (always run first)

```powershell
.\scripts\run_purge_audit_events.ps1
```

or directly:

```powershell
py -3.12 scripts/purge_audit_events.py
```

The dry run prints the count of rows eligible for deletion per event type and the
cutoff date. No rows are written or deleted.

### Step 2 - Review output and confirm with security reviewer

Before applying:

1. Confirm the retention decision with the security reviewer.
2. Back up or export the rows if required for compliance.
3. Record the planned deletion in `state/WORKLOG.md` with date, expected row count,
   and approver name.

### Step 3 - Apply (manual operator action)

```powershell
py -3.12 scripts/purge_audit_events.py --apply
```

Custom retention window (explicit operator override):

```powershell
py -3.12 scripts/purge_audit_events.py --apply --retention-days 90
```

The script prints the number of rows actually deleted and exits 0 on success.

### Notes

- There is no hosted scheduled job for this procedure. It must be triggered manually by
  an operator until the hosted scheduler is provisioned and wired to the same gates.
- Pass `--db-url` to target a non-default database, or set the `DATABASE_URL_SYNC`
  environment variable.
- Every purge validates `config/data_retention.yaml`. The default retention window is
  read from that catalog, and the purge path fails closed when the catalog is
  unreadable or invalid instead of using a silent hard-coded fallback.
- `--retention-days` is an explicit operator override for a reviewed one-off purge
  window after the catalog has validated; it does not replace the catalog as the
  retention authority.

---

## Future work

- Provision the hosted scheduler for the repo-local weekly purge contract once platform
  scheduling, alerting, backup/export, and approval evidence are available.
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

The Windows and POSIX wrappers delegate to `scripts/data_retention_check.py` so local
and CI validation use the same validate-only logic.

---

## Contact

Contact: operator / security reviewer.
