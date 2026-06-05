# Project State

## Current Branch State

- `main` is expected to track `origin/main`.
- Exact baseline hashes and verification evidence are recorded in
  `state/VALIDATION_LOG.md`.
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
- Report run review actions support approval, rejection, and supersession with
  reviewer identity, reason, transition, and timestamp history.
- Approved report runs can be served as a Markdown rural-land dossier through a
  delivery endpoint; unapproved, rejected, or superseded runs are blocked from
  served dossier delivery.
- Report creation accepts optional workspace/requester metadata and
  workspace-scoped idempotency keys. `POST /report-runs/jobs` queues
  idempotent report job requests, and `POST /report-runs/jobs/execute-next`
  leases one queued job and turns it into a persisted report run.
- `GET /report-runs` list endpoint is wired with area_id, intent_code, limit,
  and offset filters for both in-memory and Postgres backends.
- Source-failure and unsupported-category unknowns are surfaced rather than
  silently treated as safe.
- Fixture source UUID is registered in `registers/data_source_registry.csv`
  as DS-FIXTURE-001.
- DS-002 FEMA NFHL has an approved source-governance review for the
  federal-first flood path.
- Generated FastAPI OpenAPI is the runtime API authority; the curated stub is
  checked for path/method drift.
- Local orchestration folders such as `.omc/` and `.omx/` are workflow state,
  not source-of-truth project artifacts.

## What Is Not Yet Ready

- MVP state/counties are not selected.
- Live connectors are not enabled and should remain blocked.
- Most source registry rows other than DS-002 still have unresolved
  production-use status.
- Public API contract still lacks authenticated workspace/user enforcement.
- Report jobs can be executed through the explicit worker endpoint, but no
  autonomous scheduler/daemon runs them yet.
- Broader dossier product surfaces such as PDF, web pages, dashboards, or
  operator UI are not yet implemented.
- Report generation is synchronous in the current API route.
- Workspace/user access control is represented in schema but not enforced as a
  public API contract.
- The rural land dossier template is compiled into the approved Markdown
  delivery endpoint, but not yet into PDF or web dashboard output.

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
