# Lane D ADR 0001: Report Persistence

## Status

Accepted

## Context

Level 7 requires report runs to be reproducible after creation. The repository already has a `reports.report_runs` table, and `backend/app/core/config.py` already exposes `OBJECT_STORE_ROOT` for local artifact storage.

The report slice needs two things:

1. durable metadata in Postgres for the report run itself;
2. a machine-readable artifact that preserves the full report contract, including evidence, claims, unknowns, caveats, and verification tasks.

## Decision

Lane D persists report runs through a repository abstraction:

- `InMemoryReportRunRepository` keeps the existing fixture-only API scaffold working.
- `SqlAlchemyReportRunRepository` writes a machine-readable JSON artifact under `OBJECT_STORE_ROOT` using the report-run ID as the filename.
- The repository stores the report-run metadata row in `reports.report_runs` and records the artifact path in `output_uri` and `machine_json_uri`.
- The report contract remains the API-facing surface; persistence enriches it with repository-managed metadata instead of changing the workflow contract.

## Consequences

- Report retrieval depends on both the DB row and the artifact file.
- Missing artifact files fail closed instead of silently returning an incomplete report.
- The API scaffold can stay in-memory by default while a DB-backed harness exercises the durable path.
- Future work can wire the same repository into broader API flows once area persistence exists.
