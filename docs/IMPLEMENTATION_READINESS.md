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
- The DB-backed report path is proven end-to-end: a `RUN_DB_SMOKE=1` regression
  ingests a committed domain fixture, asserts the persisted `claims.claim_evidence`
  row cites the ingested evidence, and the DB-loaded dossier renders the domain finding
  plus caveats; a companion test asserts byte-identical cross-run report reproducibility
  (PR #188). The default CI gate stays the fast non-DB job.
- Private MVP geography is selected: North Carolina, with Buncombe, Chatham,
  and Brunswick as the selected NC counties.
- The selected-county operator path is routed through
  `/operator-cases/{case_id}/report`; `docs/runbooks/mvp_operator.md` is the
  current operator authority and includes the Operator Path Proof Matrix.
- DS-002 FEMA NFHL has a reviewed federal source row. DS-010 selected-county
  parcel connectors and DS-023 Chatham/Brunswick recorded-fixture zoning are
  scoped for private MVP; DS-011 assessor remains an explicit NOT_EVALUATED
  sentinel. Selected-county source-provenance expectations for DS-010,
  DS-011, and DS-023 are governed by
  `config/private_mvp_beta_readiness.yaml`.
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
- Fixture connector runs require request identity, preflight fixture area IDs
  against the authenticated workspace before durable provenance/evidence/queue
  writes, and create connector review queue rows scoped to that workspace.
- Connector review queue list/read/action routes require request identity,
  return only authenticated-workspace rows, and require review actions to use
  the authenticated user as `reviewer_id`.

## Do Not Start Impact-Heavy Work Until

| Gate | Required decision | Reason |
|---|---|---|
| Source-management/live connector tenancy | Decide whether source-management routes are admin-only or workspace-scoped, and define non-fixture live connector run identifiers/payload tenancy before live multi-user ingestion. | Fixture connector run/review queue routes are workspace-scoped, while source registry routes remain governance/admin scaffolding and fixture connectors use deterministic packaged IDs. |
| Report job scheduling | Decide whether bounded operator/API execution is enough or an autonomous scheduler/daemon is needed. | The worker endpoint and bounded operator script exist, but automatic processing is not yet part of the runtime. |
| Dossier surface expansion | Decide whether beta needs PDF, dashboard, richer web delivery, or a broader operator UI beyond approved Markdown and current operator-case routes. | Served Markdown delivery is review-gated; broader user-facing surfaces remain product decisions. |
| Legacy/null ownership | Decide whether any pre-existing `core.areas.workspace_id IS NULL` rows need a one-time backfill. | Authenticated public APIs intentionally fail closed for null-owned areas rather than exposing them across workspaces. |
| Hosted-production blockers | Decide which hosted-production blockers matter only after private MVP utility is proven. | Hosted deployment, OAuth/OIDC, registry publication, billing, and external secret-manager work are documented blockers, but they should not obscure private MVP utility proof. |

## Recommended Next Passes

Immediate next passes are source-management/live connector tenancy, report job
scheduling, dossier surface expansion, legacy/null ownership, and
hosted-production blockers after private MVP utility.

1. **Authority pass**
   - Keep `MILESTONE_MAP.md`, `LANE_OWNERSHIP.md`, and `state/*.md` current.
   - Reconcile any ADR links to missing or historical planning artifacts.
   - Keep `scripts/render_project_status.py` runnable.

2. **Source-management/live connector tenancy decision**
   - Treat North Carolina Buncombe, Chatham, and Brunswick as the selected NC
     counties; do not reopen geography selection without a new authority pass.
   - Keep selected-county scope aligned with
     `config/private_mvp_beta_readiness.yaml`, the county manifests, and the
     operator-case bridge in `docs/runbooks/mvp_operator.md`.
   - Keep raw-data/source-provenance UI assumptions aligned with the
     `selected_county_source_provenance_scope` catalog before expanding
     selected-county source coverage.
   - Decide whether source-management routes are admin-only or workspace-scoped
     before exposing live source governance or live ingestion beyond
     fixture/operator use.

3. **API contract pass**
   - Use generated FastAPI OpenAPI as runtime authority.
   - Keep `api/openapi_stub.yaml` as a curated path/method-checked companion.
   - Keep trusted-header workspace/user enforcement around report routes.
   - Keep area/evidence reads and report creation bound to authenticated
     workspace-owned areas.
   - Use `REPORT_AUTH_MODE=signed_token` before exposed beta deployment unless a
     stronger external IdP/session integration replaces it.
   - Keep fixture connector run/review queue routes behind request identity.
   - Use the bounded report worker script for operator-driven job execution.
   - Keep explicit false/unknown/missing/source-failed response semantics visible.

4. **Report job scheduling decision**
   - Decide whether bounded operator/API execution is enough for private MVP or
     whether a scheduler/daemon is needed.
   - Keep validate-only checks fail-closed; validation must not seed, mutate, or
     generate runtime artifacts.

5. **Dossier surface expansion decision**
   - Keep `templates/report_template_rural_land_dossier.md` aligned with the
     approved Markdown dossier endpoint.
   - Keep safe-language lint around generated report text.
   - Keep served/beta dossier delivery gated on the report review workflow.
   - Use the Operator Path Proof Matrix before adding PDF, dashboard, richer web
     delivery, or broader operator UI surfaces.

6. **Legacy/null ownership decision**
   - Decide whether null-owned historical areas need a one-time backfill or
     should stay inaccessible through authenticated public APIs.
   - Keep workspace isolation as the public API default.

7. **Hosted-production blockers after private MVP utility**
   - Keep hosted deployment, OAuth/OIDC, registry publication, billing, and
     external secret-manager work out of the private MVP gate unless utility
     proof requires them.
   - Promote only blockers that have a repo-confirmed path from private MVP
     utility to hosted-production need.

## Stop Rules

Stop and re-enter audit mode if a proposed implementation:

- requires live credentials or live vendor/county access;
- changes source production-use behavior without license review;
- makes legal, title, water-rights, appraisal, insurance, or investment claims;
- exposes user/report data without workspace scoping;
- broadens MVP geography without updating source authority and caveats.
