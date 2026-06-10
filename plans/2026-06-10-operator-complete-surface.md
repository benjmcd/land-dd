# Plan: Operator-Complete Production Surface

**Status:** approved (revised after adversarial review, iteration 2)
**Created:** 2026-06-10
**Relationship:** Builds on `plans/2026-06-06-private-mvp-utility-proof.md` (complete).
Advances Level 9/10 product-correctness and security gates from the top down: the
operator-facing surface.

## Problem statement

The platform layers (source registry → geometry → evidence → claims → reports → jobs) are
hardened and verified (871 tests, full DB-enabled verify green). The remaining gap between
"materially hardened backend" and "production-grade tool usable in full" is the operator
surface:

1. **Security + audit-integrity hole (P0):** `POST /ui/report-runs/{id}/approve`
   (`ui.py:241-272`) approves with **zero credential check** AND records the **first
   configured reviewer account** as `reviewed_by` in the immutable `review_actions`
   audit log (`report_repo.py:62-77,127-140`) — falsified attribution. The API route
   (`reports.py:288-295`) requires a scoped principal (`report:approve`). Violates
   L10-SEC-002 and the provenance non-negotiable.
2. **Silent connector-review dead-end:** when intake hits live-connector review, it returns
   `status="pending_connector_review"` + `connector_ingest_run_id` with `report_run_id=None`
   and **no report job** (`intake.py:54-65`, `reports.py:255-265`). The UI renders the raw
   JSON and the operator has no page to see or action the queue.
3. **L9-004 gap — evidence behind claims is not inspectable in the product surface:** the
   dossier shows evidence *counts* (`dossier.py:186`), and the complete lineage API
   (`GET /report-runs/{id}/lineage`, claim→evidence→source→ingest-run) has no UI.
4. **No artifact export:** no download of the dossier (.md) or machine-readable report
   artifact (.json) preserving run identity + evidence links (L10-PROD-003, L9-006).
5. **No failure recovery in UI:** retry exists only as a reviewer-scoped API route.
6. **No operations visibility in UI:** `/operations/queue-health` (scope `operations:read`)
   has no page.
7. **List scalability:** UI report list hardcodes 30 recent; no programmatic
   `GET /report-runs` list endpoint exists at all; `list_recent(limit)` (protocol +
   both stores, `job_store.py:51,103,207`) has no offset/status.

## Recorded posture decisions (from adversarial review)

- **REQUIRE_API_KEY=true locks the UI too — by design.** `PUBLIC_PATHS` stays
  `{/health,/version}`; we do NOT exempt `/ui` or export routes (that would leak dossier
  content in locked deployments). The operator UI targets the default private
  trusted-network posture; documented in the runbook (S8).
- **UI reviewer auth = stateless per-action form fields** (`reviewer_id` + `reviewer_token`)
  validated via `services.reviewer_auth(reviewer_id=..., reviewer_token=...)` (the
  `__call__` at `reviewer_auth.py:35-83`; there is no `.authenticate()`), then
  `require_reviewer_scope(...)`. No sessions/cookies. CSRF is mitigated incidentally but
  effectively: a cross-site form post cannot succeed without the secret token in the body.
- **Connector-review UI binds to the reviewer-scope model** (`connector:review` =
  `REVIEWER_SCOPE_CONNECTOR_REVIEW`), NOT the workspace-header compat model
  (`connectors.py:495-609`) — browsers cannot supply `X-Workspace-Id`. UI list uses the
  repository directly (`list_connector_runs(workspace_id=None, status=..., limit=...,
  offset=...)`, `review_queue.py:56-64`); UI actions delegate to the same queue methods the
  canonical reviewer-scoped routes use (`connectors.py:1316-1445`).
- **Compare stays count-level and ungated** (matches existing API; exposes only summary
  counts of unapproved reports, content stays approved-gated). Recorded as deliberate.
- **Errors:** UI auth failures return real 401/403 status codes with generic messages
  (mirror `reviewer_auth.py:67-83`), no field-level leaks. Unconfigured reviewer accounts
  surface the existing 503 semantics.

## Slices (implementation order)

### S1 (P0) — UI reviewer authentication for approve
**Files:** `backend/app/api/ui.py`, `backend/tests/api/test_ui_routes.py`
- Approve form gains `reviewer_id` + `reviewer_token` (password) inputs.
- Handler authenticates via `services.reviewer_auth(...)`, enforces
  `REVIEWER_SCOPE_REPORT_APPROVE`, approves as the **authenticated** reviewer.
  Remove the first-account fallback entirely.
- HTTPException from auth → render error page with the same status code (401/403/503).
- Tests: no creds → 401; bad token → 401; valid-unscoped → 403; valid+scoped → approved
  AND `reviewed_by`/`review_actions` record the authenticated id (audit integrity);
  update `test_ui_approve_report_run_redirects_on_success` (currently encodes the
  insecure contract).

### S2 — Report export/download + OpenAPI stub regeneration tooling
**Files:** `backend/app/api/reports.py`, `backend/app/api/ui.py`, new
`scripts/export_openapi_stub.py`, `docs/planning_pack/api/openapi_stub.yaml`, tests
- `GET /report-runs/{id}/dossier?download=1` → existing gating (`409` unapproved, `404`
  missing, `202` running — `reports.py:487-522`), adds
  `Content-Disposition: attachment; filename="dossier_<id>.md"`. Body byte-identical to
  `build_rural_land_dossier`.
- `GET /report-runs/{id}/artifact` → machine-readable report JSON with attachment
  disposition; approved-only gating mirroring dossier. In DB mode serve the persisted
  artifact (authoritative; `report_repo.py:86-108`); in-memory mode serialize the contract.
- UI report page: download links (.md / .json) next to Print.
- New `scripts/export_openapi_stub.py`: dumps `create_app().openapi()` as YAML to
  `docs/planning_pack/api/openapi_stub.yaml` (the parity test deep-compares,
  `test_planning_pack_schema_copies.py:34-40`). Run it in THIS and EVERY route-adding
  slice.
- Tests: gating, content-type, disposition; artifact preserves `report_run_id` +
  evidence links + caveats; **forbidden-phrase assertion on the JSON artifact body**;
  DB-gated test exercising the persisted-artifact path.

### S3 — Connector review queue UI + intake pending-path surfacing
**Files:** new `backend/app/api/ui_review.py`, `backend/app/main.py`,
`backend/app/api/ui.py` (index-page JS only), tests
- `GET /ui/connector-review-queue`: table (ingest_run_id, connector, status, attempts,
  created) + status filter + limit/offset pagination via
  `list_connector_runs(workspace_id=None, ...)`.
- `GET /ui/connector-review-queue/{ingest_run_id}`: payload summary, quality issues,
  attempts/lock/timing metadata, last error; action forms (approve/reject/requeue/cancel)
  with reviewer_id+token+reason, enforcing `REVIEWER_SCOPE_CONNECTOR_REVIEW`, delegating
  to the same queue/service methods as the canonical reviewer-scoped routes.
- Index page: when `/intake` responds `pending_connector_review`, render a human result
  with a link to `/ui/connector-review-queue/{connector_ingest_run_id}` (no report job
  exists in this path — link is from the intake response, not a report page).
- After approval, surface the resume affordance (link/form to the existing post-approval
  report resume path keyed on ingest_run_id).
- Tests: list/filter/pagination render; detail renders quality issues; all four actions
  require auth + scope; approve transitions; index pending-path link rendering.

### S4 — Failure recovery + operations dashboard UI
**Files:** new `backend/app/api/ui_operations.py`, `backend/app/api/ui.py` (failed-page
section), `backend/app/main.py`, tests
- Failed-report page: Retry form (reviewer_id+token) → `REVIEWER_SCOPE_REPORT_RETRY` +
  failed-only check (mirror `reports.py:316-353`), redirect to `/ui/report-runs/{new_id}`.
- `GET /ui/operations`: token form → POST renders queue-health (same service as
  `/operations/queue-health`, scope `operations:read`).
- Tests: retry auth/failed-only/redirect; dashboard auth + renders counts.

### S5 — Report list: pagination, filtering, list API
**Files:** `backend/app/reports/job_store.py` (protocol + both impls),
`backend/app/api/reports.py`, `backend/app/api/ui.py` (list page), tests, openapi stub
- `list_recent(limit, offset=0, status=None)` in protocol + in-memory + SQLAlchemy stores
  (grep all `list_recent` callers first). DB-gated test for the SQL path.
- `GET /report-runs?status=&limit=&offset=` (bounded `le=100`) returning job summaries
  (id, intent, status, created_at, review_status where available — N+1 bounded by page).
- UI list: status filter + prev/next; failed rows link to report page (retry lives there).
- Tests: API pagination/filter/bounds; UI controls; both store impls.

### S6 — Evidence/lineage explorer UI (closes L9-004 product-surface gap)
**Files:** new page in `backend/app/api/ui_review.py` (or `ui_lineage.py`),
`backend/app/api/ui.py` (link from report page), tests
- `GET /ui/report-runs/{id}/lineage`: renders the existing lineage response — per-claim
  evidence ids (with type/source), per-evidence claim links, source → ingest-run chain.
  Same gating posture as the lineage API.
- Report page links "View evidence lineage".
- Tests: lineage page renders claim→evidence mapping; gating consistent with API.

### S7 — Compare UI (usability; L9-008 already satisfied by API)
**Files:** `backend/app/api/reports.py` (extract shared summary helper),
`backend/app/api/ui.py` or `ui_review.py`, tests, openapi stub (no route change to API)
- Extract the inline summary construction (`reports.py:418-443`) into a helper used by
  both API route and UI page (keeps handlers thin; no API behavior change).
- `GET /ui/compare?ids=a,b[,c,d]`: side-by-side table; enforce 2..4 ids + UUID validation
  (mirror API semantics incl. malformed/oversize cases in tests).
- Report list page: simple compare affordance.

### S8 — Docs, state, full verification
- Runbook (`docs/runbooks/mvp_operator.md`): credentialed UI approve, connector review
  flow, retry, export, operations, lineage, compare; **REQUIRE_API_KEY posture note**
  (locked deployments lock the UI by design).
- `state/PROJECT_STATE.md`: fix stale active-plan pointer at the "Active plan (overall)"
  section (task_queue.yaml is already correct), record this plan + results.
- `state/WORKLOG.md`, `state/VALIDATION_LOG.md`.
- Regenerate openapi stub (final), `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`,
  adversarial code review pass.

## Non-goals

- OAuth/OIDC, sessions, cookies, full RBAC (hosted-production lane).
- Changes to API auth posture, `PUBLIC_PATHS`, report semantics, schema, or connectors.
- SPA frameworks, new dependencies, server-side PDF rendering.
- New intents/geographies (2 seeded intents stay; no geography selector).

## Risks

| Risk | Mitigation |
|---|---|
| OpenAPI parity test breaks per route-adding slice | `scripts/export_openapi_stub.py` created in S2; run in every route-adding slice |
| Existing UI tests encode insecure approve | Updated in S1; intentional contract change recorded here |
| Reviewer token in form body | Same trust model/channel as header tokens; trusted-network posture documented; secret-in-body defeats CSRF forgery |
| ui.py contention across slices | Slices land sequentially; one slice owns ui.py edits at a time |
| In-memory vs DB store drift (pagination, artifact) | Tests for both implementations; DB-gated tests for SQL paths |
| Compare exposes unapproved counts | Recorded posture decision; content remains approved-gated |
