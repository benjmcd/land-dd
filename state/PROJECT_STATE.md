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
- Served report dossier text is checked against the active ruleset's forbidden
  language before delivery.
- Report creation accepts optional workspace/requester metadata and
  workspace-scoped idempotency keys. `POST /report-runs/jobs` queues
  idempotent report job requests, and `POST /report-runs/jobs/execute-next`
  leases one queued job and turns it into a persisted report run.
- `scripts/run_report_worker.py` can execute a bounded number of queued report
  jobs through the authenticated public API for operator-driven processing.
- Report API creation, listing, retrieval, review, job access, job execution,
  and dossier delivery require `X-Workspace-Id` and `X-User-Id` request headers;
  body/query workspace and reviewer fields must match the request identity.
- Report routes can alternatively run with `REPORT_AUTH_MODE=signed_token`,
  requiring signed bearer report identity tokens whose workspace/user claims
  become the request authority.
- `scripts/mint_report_token.py` can mint short-lived operator tokens for
  signed-token report API mode from `REPORT_IDENTITY_TOKEN_SECRET`.
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
- The report API has signed-token beta identity enforcement, but no external
  identity-provider or session-management integration yet.
- Report jobs can be executed through the explicit worker endpoint or bounded
  operator script, but no autonomous scheduler/daemon runs them yet.
- Broader dossier product surfaces such as PDF, web pages, dashboards, or
  operator UI are not yet implemented.
- Report generation is synchronous in the current API route.
- Non-report resources are not yet fully workspace-scoped at the API boundary.
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
