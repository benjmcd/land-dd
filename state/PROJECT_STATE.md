# Project State

## Current Branch State

- `main` is expected to track `origin/main`.
- Last confirmed baseline: commit `53efb49` (matches `origin/main` as of
  2026-06-05).
- The working baseline is a fixture-backed backend MVP scaffold, not a live
  production diligence product.

## What Works

- Source, area, evidence, claim, connector, and report services are wired for
  in-memory API use.
- Postgres-backed repositories and DB smoke are covered by CI.
- Static access, flood, and zoning connector fixtures can produce evidence via
  `POST /connector-runs`.
- Connector review queue supports enqueue, list, get, approve, reject, requeue,
  and cancel with reviewer identity recorded in the payload action history.
- Report runs expose source manifest, assumptions, caveats, evidence, claims,
  unknowns, red flags, verification tasks, and machine JSON metadata.
- `GET /report-runs` list endpoint is wired with area_id, intent_code, limit,
  and offset filters for both in-memory and Postgres backends.
- Source-failure and unsupported-category unknowns are surfaced rather than
  silently treated as safe.
- Fixture source UUID is registered in `registers/data_source_registry.csv`
  as DS-FIXTURE-001.
- Local orchestration folders such as `.omc/` and `.omx/` are workflow state,
  not source-of-truth project artifacts.

## What Is Not Yet Ready

- MVP state/counties are not selected.
- Live connectors are not enabled and should remain blocked.
- Most source registry rows still have unresolved production-use status.
- Public API contract is still a compact draft.
- Report generation is synchronous in the current API route.
- Workspace/user access control is represented in schema but not enforced as a
  public API contract.
- The rural land dossier template is not yet compiled as a served report.

## Current Source Of Truth

- Product scope: `docs/PRODUCT_SPEC.md`
- Architecture: `docs/ARCHITECTURE.md`
- Storage: `docs/POSTGRES_FIRST_STORAGE.md`
- Data/source policy: `docs/DATA_SOURCE_STRATEGY.md`
- Milestones: `MILESTONE_MAP.md`
- Ownership: `LANE_OWNERSHIP.md`
- Next implementation gates: `docs/IMPLEMENTATION_READINESS.md`
- Open questions: `state/OPEN_QUESTIONS.md`
- Validation evidence: `state/VALIDATION_LOG.md`
