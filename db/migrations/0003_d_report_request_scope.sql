-- Add report request scoping and idempotency fields.
-- Safe to re-run.
ALTER TABLE reports.report_runs
    ADD COLUMN IF NOT EXISTS idempotency_key text;

DROP INDEX IF EXISTS report_runs_idempotency_key_uidx;

CREATE UNIQUE INDEX IF NOT EXISTS report_runs_workspace_idempotency_key_uidx
    ON reports.report_runs ((COALESCE(workspace_id::text, '')), idempotency_key)
    WHERE idempotency_key IS NOT NULL;
