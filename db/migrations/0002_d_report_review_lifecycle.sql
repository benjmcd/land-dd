-- Add report review lifecycle fields.
-- Safe to re-run.
ALTER TABLE reports.report_runs
    ADD COLUMN IF NOT EXISTS review_status text NOT NULL DEFAULT 'needs_review',
    ADD COLUMN IF NOT EXISTS reviewed_by text,
    ADD COLUMN IF NOT EXISTS reviewed_at timestamptz,
    ADD COLUMN IF NOT EXISTS review_actions jsonb NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE reports.report_runs
    DROP CONSTRAINT IF EXISTS report_runs_review_status_check;

ALTER TABLE reports.report_runs
    ADD CONSTRAINT report_runs_review_status_check CHECK (
        review_status IN (
            'draft',
            'needs_review',
            'approved',
            'rejected',
            'superseded'
        )
    );
