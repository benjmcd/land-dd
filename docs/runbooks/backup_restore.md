# Backup and Restore Runbook

## Purpose

Use this runbook to prove that a Postgres/PostGIS database backup can be restored into a
separate database and still satisfies the repository's DB smoke invariants.

This is a Level 10 production-hardening check. It is not a substitute for a production
backup policy, retention schedule, encryption policy, or offsite recovery plan.

## Safety Boundary

The automated restore check only recreates a database whose name starts with
`land_diligence_restore_check` and contains only letters, digits, or underscores. Do not
point it at the source production database.

The default dump file is written under ignored local artifacts:

```text
local_artifacts/backup_restore/restore-check.sql
```

Treat dump files as sensitive operational artifacts. Store production backups only in an
approved encrypted location with access controls.

## Windows PowerShell

Start or select the source database, then apply current migrations and seeds:

```powershell
docker compose up -d db
.\scripts\db_apply_migrations.ps1
```

Run the restore check:

```powershell
.\scripts\run_backup_restore_check.ps1
```

If `pg_dump` is not installed locally but Docker is available, the script uses the
`postgis/postgis:16-3.4` image as a PostgreSQL client and maps localhost database URLs to
`host.docker.internal`.

Useful environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL_SYNC` | `postgresql://land:land@localhost:5432/land_diligence` | Source DB to dump |
| `DATABASE_ADMIN_URL_SYNC` | source URL with database `postgres` | Admin DB used to create/drop the restore DB |
| `RESTORE_CHECK_DB_NAME` | `land_diligence_restore_check` | Dedicated restore DB name |
| `RESTORE_DATABASE_URL_SYNC` | source URL with restore DB name | Restore DB URL |
| `RESTORE_CHECK_DUMP_PATH` | `local_artifacts/backup_restore/restore-check.sql` | Local dump path |
| `RESTORE_CHECK_KEEP_DB` | unset | Set to `1` to keep the restore DB for inspection |

Expected result:

```text
backup/restore check: ok
```

The script drops the restore database after a successful or failed run unless
`RESTORE_CHECK_KEEP_DB=1`.

## POSIX Shell

Use the shell equivalent on Linux/macOS or CI runners:

```bash
./scripts/db_apply_migrations.sh
./scripts/run_backup_restore_check.sh
```

The shell script has the same Docker client fallback when local `pg_dump` is absent.

## Evidence to Record

Record these in `state/VALIDATION_LOG.md` after a successful check:

- command used;
- source and restore database names, without secrets;
- `db_smoke_check.py` result against the restored DB;
- whether the restore database was dropped or preserved for inspection.

## Failure Handling

If restore fails:

- keep the failed command output;
- do not treat backup coverage as proven;
- inspect whether the failure is from missing PostgreSQL client tools, source DB
  connectivity, dump failure, restore failure, missing PostGIS extension, or smoke-check
  invariant drift;
- rerun only after the underlying cause is fixed.
