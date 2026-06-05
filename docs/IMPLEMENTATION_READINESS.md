# Implementation Readiness

This document is the first stop before impact-heavy implementation. It turns
the current repo state into concrete gates and next passes so future work can
start without re-litigating basic authority.

## Current Working Baseline

- Fast local verification passes through `scripts/verify.*`.
- The in-memory API demo runs the fixture-to-report workflow through public
  endpoints.
- CI runs both the fast verification job and the PostGIS-backed DB verification
  job on `main`.
- Current connector runtime is fixture-only for access, flood, and zoning.
- DS-002 FEMA NFHL has a reviewed federal source row; local/county source rows
  still fail closed until reviewed.
- FastAPI's generated OpenAPI schema is the runtime API authority;
  `api/openapi_stub.yaml` is a curated companion checked for path/method drift.
- Report runs return a machine-readable JSON contract; approved report runs can
  also be delivered as a Markdown rural-land dossier.
- Served Markdown dossier text is checked against the active ruleset's
  forbidden-language list before delivery.
- Report runs now have a human-review lifecycle: `needs_review`, `approved`,
  `rejected`, and `superseded` transitions with reviewer, reason, and timestamp
  audit history.
- Report creation accepts optional workspace/requester metadata and
  workspace-scoped idempotency keys; queued report jobs require an idempotency
  key and can be explicitly leased/executed into persisted report runs.
- `scripts/run_report_worker.py` can execute a bounded number of queued report
  jobs through the authenticated public API for operator-driven processing.
- Report API routes require trusted `X-Workspace-Id` and `X-User-Id` headers
  and reject body/query/reviewer identity mismatches.
- Report API routes can run in `REPORT_AUTH_MODE=signed_token`, where a signed
  bearer report identity token supplies the workspace/user authority and
  mismatched identity headers fail closed.
- `scripts/mint_report_token.py` can mint short-lived operator tokens for
  `REPORT_AUTH_MODE=signed_token` from `REPORT_IDENTITY_TOKEN_SECRET`.
- Area API routes now require the same request identity boundary, bind
  `core.areas.workspace_id` and `created_by` on creation, and list only areas in
  the authenticated workspace.
- Evidence API reads require request identity and return records only when the
  requested `area_id` belongs to the authenticated workspace.
- Report creation and report-job submission reject area IDs outside the
  authenticated workspace at both the API route and report-service boundary.
  Evidence writes also accept an optional workspace scope for callers that have
  workspace authority.

## Do Not Start Impact-Heavy Work Until

| Gate | Required decision | Reason |
|---|---|---|
| MVP geography | Select one U.S. state and 3-5 target counties. | County parcels, zoning, assessor, recorder, wells, and caveats are jurisdiction-specific. |
| Source licensing | Complete license review for any source used beyond fixtures. | Unknown or blocked source rights fail closed for production reports and exports. |
| External identity integration | Decide whether beta needs an external IdP/session issuer beyond signed report identity tokens. | The backend now has a signed beta token boundary, but a public multi-user deployment may still need a product IdP/session layer. |
| Connector/source API scoping | Decide workspace payload and reviewer authority for connector runs, connector review queue items, and any future source-management API. | Area/evidence/report routes are now workspace-scoped; connector queue and source surfaces still need a deliberate tenancy contract. |
| Legacy/null area ownership | Decide whether any pre-existing `core.areas.workspace_id IS NULL` rows need a one-time backfill. | Authenticated public APIs intentionally fail closed for null-owned areas rather than exposing them across workspaces. |
| Report job scheduling | Decide whether bounded operator/API execution is enough or an autonomous scheduler/daemon is needed. | The worker endpoint and bounded operator script exist, but automatic processing is not yet part of the runtime. |
| Dossier surface expansion | Decide whether beta needs PDF, web page, dashboard, or operator UI beyond the approved Markdown endpoint. | Served Markdown delivery is review-gated; broader user-facing surfaces remain product decisions. |
| Golden parcels | Define regression parcels for the selected counties. | Geo/source changes need known fixtures to detect false confidence. |

## Recommended Next Passes

1. **Authority pass**
   - Keep `MILESTONE_MAP.md`, `LANE_OWNERSHIP.md`, and `state/*.md` current.
   - Reconcile any ADR links to missing or historical planning artifacts.
   - Keep `scripts/render_project_status.py` runnable.

2. **MVP geography and source pass**
   - Pick the state/counties.
   - Update `registers/data_source_registry.csv` with county-specific rows or
     narrowed source records.
   - Complete source reviews under `registers/license-reviews/` for the first
     source candidates.
   - Define source caveats and source-failure behavior before runtime work.

3. **API contract pass**
   - Use generated FastAPI OpenAPI as runtime authority.
   - Keep `api/openapi_stub.yaml` as a curated path/method-checked companion.
   - Keep trusted-header workspace/user enforcement around report routes.
   - Keep area/evidence reads and report creation bound to authenticated
     workspace-owned areas.
   - Use `REPORT_AUTH_MODE=signed_token` before exposed beta deployment unless a
     stronger external IdP/session integration replaces it.
   - Design connector/source workspace authority before exposing those routes
     beyond fixture/operator use.
   - Use the bounded report worker script for operator-driven job execution.
   - Decide and implement automatic report-job scheduling only if beta needs it.
   - Keep explicit false/unknown/missing/source-failed response semantics visible.

4. **First high-ROI implementation pass**
   - Choose one vertical slice, preferably one selected-county fixture-backed
     source adapter that produces evidence and report-visible unknowns/caveats.
   - Keep live network disabled until the connector gate passes.
   - Add regression fixtures before widening data coverage.

5. **Report productization pass**
   - Keep `templates/report_template_rural_land_dossier.md` aligned with the
     approved Markdown dossier endpoint.
   - Keep safe-language lint around generated report text.
   - Keep served/beta dossier delivery gated on the report review workflow.

## Stop Rules

Stop and re-enter audit mode if a proposed implementation:

- requires live credentials or live vendor/county access;
- changes source production-use behavior without license review;
- makes legal, title, water-rights, appraisal, insurance, or investment claims;
- exposes user/report data without workspace scoping;
- broadens MVP geography without updating source authority and caveats.
