# Connector Review Workspace Scope

## Goal
Close the workspace-isolation gap on legacy connector review-action routes and the
approved-connector report-run route. A reviewer authenticated in one workspace must
not be able to approve, reject, requeue, cancel, or create a report job for a
connector review item owned by another workspace.

## Non-goals
- No schema changes.
- No connector execution changes.
- No source-readiness or source-review status changes.
- No UI redesign or new browser workflow.
- No hosted auth/RBAC redesign.
- No report artifact path hardening in this slice.

## Current state
- `GET /connector-runs/{ingest_run_id}/review-status` and
  `GET /connector-runs/{ingest_run_id}/review-queue` already use scoped queue
  lookup through `AuthDep`.
- Legacy review-action routes under
  `/connector-runs/{ingest_run_id}/review-actions/*` use reviewer credentials but
  do not require request workspace identity.
- `POST /connector-runs/{ingest_run_id}/report-runs` also uses reviewer
  credentials but does not propagate workspace/requester identity onto the queued
  report job.
- `POST /intake` creates areas before live connector orchestration. When request
  identity is present, that route must copy the same workspace/requester identity
  onto the created area so request-time live connector queue items inherit the
  correct scope.
- Authenticated `POST /report-runs` is the continuation surface after an authenticated
  intake-created connector review item is approved, so it must not bypass request-time
  live connector orchestration while unauthenticated local report creation still runs it.
- `ConnectorReviewQueueRepository.get_by_ingest_run_id()` already accepts a
  `workspace_id` filter, so the narrow fix can reuse existing repository
  behavior.

## Proposed design
Use the existing workspace auth dependency and scoped queue helper for every
legacy connector review mutation. The queue item should be looked up using the
authenticated workspace before any state transition. The connector-to-report path
should also require workspace identity, verify the area belongs to that workspace,
and create the queued report job with `workspace_id` and `requested_by`.
For intake-created live connector work, preserve the existing unauthenticated
local path but resolve request identity when supplied and propagate it through
area creation, idempotency, report job creation, and background report execution.
Authenticated report creation should keep principal-scoped idempotency, but still check
request-time live connectors before queueing the report job.

Rejected alternatives:
- Removing the legacy routes is broader than necessary and risks breaking
  documented operator flows.
- Adding new repository methods is unnecessary because scoped lookup already
  exists.
- Relying only on reviewer credentials is insufficient because reviewer identity
  is not a workspace boundary.

## Bottom-up sequence
1. Add focused failing tests proving cross-workspace requests to the legacy
   review-action routes return 404 and do not mutate the item.
2. Add focused failing tests proving the connector-to-report route requires
   workspace identity, hides other-workspace queue items, and creates report jobs
   with workspace/requester identity.
3. Update the legacy routes in `backend/app/api/connectors.py` to require
   `AuthDep`, use scoped queue lookup, and propagate report job identity.
4. Update authenticated intake to preserve workspace/requester identity for
   request-time live connector queue items and queued report jobs.
5. Update authenticated report creation to run request-time live connector orchestration
   before queueing the final report job.
6. Run focused connector action/API tests, then the default verification gate.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/api/connectors.py` | Scope legacy review mutations and connector report job creation by workspace |
| `backend/app/api/intake.py` | Propagate request identity into intake-created areas and report jobs when present |
| `backend/app/api/reports.py` | Preserve live connector orchestration on authenticated report creation |
| `backend/app/evidence_ledger/evidence_repo.py` | Persist evidence dataset/run lineage into existing relational columns after DB-gated verification exposed the gap |
| `backend/tests/api/test_connector_review_actions.py` | Add identity and cross-workspace regression coverage |
| `backend/tests/api/test_fema_nfhl_connector_api.py` | Adjust connector-to-report assertions if needed |
| `backend/tests/evidence_ledger/test_sqlalchemy_evidence_repo.py` | Pin SQLAlchemy evidence lineage column persistence |
| `api/openapi_stub.yaml` | Regenerated if route header contracts change |
| `docs/planning_pack/api/openapi_stub.yaml` | Regenerated schema copy if route header contracts change |
| `state/VALIDATION_LOG.md` | Record verification evidence |
| `state/WORKLOG.md` | Record implementation note |
| `state/PROJECT_STATE.md` | Add current checkpoint if behavior changes land |

## Tests / verification
Focused:
```powershell
cd backend
python -m pytest -q .\tests\api\test_connector_review_actions.py
python -m pytest -q .\tests\api\test_fema_nfhl_connector_api.py -k "review-actions or report-runs or approved or intake"
python -m ruff check .\app\api\connectors.py .\app\api\intake.py .\app\api\reports.py .\tests\api\test_connector_review_actions.py .\tests\api\test_fema_nfhl_connector_api.py
python -m mypy .\app\api\connectors.py .\app\api\intake.py .\app\api\reports.py .\tests\api\test_connector_review_actions.py .\tests\api\test_fema_nfhl_connector_api.py
```

Handoff:
```powershell
.\scripts\verify.ps1
```

## Risks and blockers
- Tests that mount only the connector router may need to provide request identity
  headers after `AuthDep` is added.
- The route should hide cross-workspace items as not found, not leak existence
  through authorization or conflict errors.
- Report job identity should be explicit so later worker/list/detail routes can
  enforce workspace filtering consistently.
- Intake must not become auth-required for legacy local callers unless the
  existing signed-token mode or supplied identity headers make auth mandatory.
- Authenticated report creation must not skip request-time live connectors for
  authenticated intake continuation flows.

## Decision log
- 2026-06-18: Treat workspace isolation as higher priority than stale routing
  cleanup because it affects mutation boundaries.
- 2026-06-18: Keep the fix route-local and reuse existing queue repository scope
  filtering.
- 2026-06-18: Include intake identity propagation because request-time live
  connector review items derive their scope from the area created by `/intake`.
- 2026-06-18: Include authenticated report creation because it is the normal
  continuation surface after authenticated intake-created connector review.

## Progress log
- 2026-06-18: Live `origin/main` fast-forwarded to `3aff431`; remote CI green;
  default local `.\scripts\verify.ps1` passed with DB smoke skipped. Read-only
  security review identified unscoped legacy connector review-action routes and
  connector-to-report job creation.
- 2026-06-18: Implemented scoped legacy review mutations, scoped connector-to-report
  resume, authenticated intake identity propagation, and regenerated OpenAPI stubs.
- 2026-06-18: Re-audit found authenticated report creation bypassed request-time live
  connector orchestration; added it to this slice before handoff.
- 2026-06-18: Focused connector review action, intake/idempotency, report-auth, live
  connector intake/report continuation, OpenAPI parity, ruff, and mypy checks passed.
  Final `.\scripts\verify.ps1` passed on Python 3.12.10 with DB smoke skipped because
  `RUN_DB_SMOKE=1` was not set.
- 2026-06-18: DB-gated verification on isolated Postgres exposed that
  `SqlAlchemyEvidenceRepository` wrote `source_ingest_run_id` only into evidence
  metadata while leaving the existing `evidence.observations.ingest_run_id` column
  empty. Fixed the repository mapper to persist and read `dataset_version_id` and
  `ingest_run_id`, retaining metadata fallback for legacy rows.
- 2026-06-18: Focused DB-gated selected-county, evidence repository, claim
  repository, and public connector wiring tests passed on isolated Postgres port
  `55448`. Final `RUN_DB_SMOKE=1 .\scripts\verify.ps1` passed on Python 3.12.10,
  including migrations/seeds, backend tests, ruff, mypy, and DB smoke.
