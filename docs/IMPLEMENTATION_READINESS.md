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
- Report runs return a machine-readable JSON contract; the dossier template is
  not yet the served report product.
- Report runs now have a human-review lifecycle: `needs_review`, `approved`,
  `rejected`, and `superseded` transitions with reviewer, reason, and timestamp
  audit history.
- Report creation accepts optional workspace/requester metadata and
  workspace-scoped idempotency keys; queued report jobs require an idempotency
  key and remain queued until a worker runtime is added.

## Do Not Start Impact-Heavy Work Until

| Gate | Required decision | Reason |
|---|---|---|
| MVP geography | Select one U.S. state and 3-5 target counties. | County parcels, zoning, assessor, recorder, wells, and caveats are jurisdiction-specific. |
| Source licensing | Complete license review for any source used beyond fixtures. | Unknown or blocked source rights fail closed for production reports and exports. |
| API enforcement | Decide authentication/authorization for workspace and user identity. | Explicit workspace/requester fields exist, but they are not yet enforced by an auth boundary. |
| Report job runtime | Add worker lease/execute/retry behavior for queued report jobs. | The queued API contract exists, but queued jobs are not yet executed asynchronously. |
| Report lifecycle delivery gate | Decide how approved review status gates served dossier delivery and any human/operator UI. | The backend lifecycle exists, but product delivery still needs an explicit approval gate. |
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
   - Add authentication/enforcement around workspace and requester metadata.
   - Add worker execution for queued report jobs.
   - Keep explicit false/unknown/missing/source-failed response semantics visible.

4. **First high-ROI implementation pass**
   - Choose one vertical slice, preferably one selected-county fixture-backed
     source adapter that produces evidence and report-visible unknowns/caveats.
   - Keep live network disabled until the connector gate passes.
   - Add regression fixtures before widening data coverage.

5. **Report productization pass**
   - Compile `templates/report_template_rural_land_dossier.md` from the report
     contract.
   - Add safe-language lint around generated report text.
   - Gate served/beta dossier delivery on the report review workflow.

## Stop Rules

Stop and re-enter audit mode if a proposed implementation:

- requires live credentials or live vendor/county access;
- changes source production-use behavior without license review;
- makes legal, title, water-rights, appraisal, insurance, or investment claims;
- exposes user/report data without workspace scoping;
- broadens MVP geography without updating source authority and caveats.
