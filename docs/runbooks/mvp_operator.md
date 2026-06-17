# MVP Operator Runbook

## Overview

Land Diligence is a fixture-backed land due-diligence screening compiler for US rural land.
It evaluates flood, soil, and environmental data against a submitted area of interest and
returns a structured report of claims, unknowns, and verification tasks.

**Scope:** Default MVP operation is fixture-backed and single-process. Reviewed public
live-source connectors are available through explicit reviewer/operator flows and the
default-off live connector request-time flag, but their output remains screening-only and
review-gated. Supported intents: `rural_land_purchase`, `homestead_feasibility`.

---

## Prerequisites

- Python 3.12+
- pip (backend dependencies)
- Docker + Docker Compose (optional, for Postgres-backed mode)
- No API keys or credentials required for MVP fixture mode

---

## Startup

### Development (in-memory, no database)

Use in-memory mode only for local fixture/demo work. Non-local `APP_ENV` values
fail startup unless `USE_DB_SERVICES=true`, because queued jobs, connector
review, reports, and audit state must survive process restarts.

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### With PostgreSQL (Docker)

```bash
docker compose up -d db
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql://user:pass@localhost:5432/landdd \
USE_DB_SERVICES=true \
  PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Apply migrations before first run:

```bash
./scripts/db_apply_migrations.sh
# or on Windows:
.\scripts\db_apply_migrations.ps1
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `land-diligence` | Application name (appears in /health) |
| `APP_ENV` | `development` | Environment label |
| `DATABASE_URL` | _(none)_ | Postgres connection string; required when `USE_DB_SERVICES=true` |
| `USE_DB_SERVICES` | `false` | Use Postgres-backed services instead of in-memory stores; required outside local/dev/development/test `APP_ENV` values |
| `OBJECT_STORE_ROOT` | `./object_store` | Directory for report artifact files |
| `REVIEWER_ACCOUNTS` | local fixture reviewer | Reviewer service account ids and tokens |
| `REVIEWER_ACCOUNT_SCOPES` | local fixture scopes | Explicit reviewer scopes such as `connector:run`, `connector:review`, `operations:read`, `report:approve`, `report:retry`, `report:run`, and `source:manage` |
| `ENABLE_LIVE_CONNECTORS` | `false` | Enables request-time DS-001, DS-002, DS-004, then DS-003 connector gating |

Local/dev/development/test app environments may use raw `API_KEYS`, raw
`API_KEY_SPECS` secrets, and the default fixture reviewer account for private-MVP work.
Non-local `APP_ENV` values with `REQUIRE_API_KEY=true` reject `API_KEYS` and require
`API_KEY_SPECS` entries with `sha256:<64-hex>` secrets. Non-local `APP_ENV` values also
reject the fixture reviewer account and raw reviewer tokens; configure explicit
`REVIEWER_ACCOUNTS` entries as `id:sha256:<64-hex>` and give every reviewer id explicit
`REVIEWER_ACCOUNT_SCOPES`.

---

## API Workflow

### One-shot intake (recommended for UI and scripting)

**Step 1 — Submit area + intent:**

```bash
curl -s -X POST http://localhost:8000/intake \
  -H 'Content-Type: application/json' \
  -d '{
    "area_geojson": {"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]},
    "intent_code": "rural_land_purchase"
  }'
```

Response (202 Accepted):

```json
{"report_run_id": "{report_run_id}", "area_id": "{area_id}", "status": "queued"}
```

**Step 2 — Poll until complete:**

```bash
curl -s http://localhost:8000/report-runs/{report_run_id}
```

Poll until `"status": "succeeded"`. The full `ReportRunContract` is returned at that point.

Status values: `queued` → `running` → `succeeded` (or `failed`).

### Two-step API (area pre-registration)

```bash
# Register area
curl -s -X POST http://localhost:8000/areas \
  -H 'Content-Type: application/json' \
  -d '{"geom_geojson": {...}, "geom_source": "user supplied"}'

# Create report run with returned area_id
curl -s -X POST http://localhost:8000/report-runs \
  -H 'Content-Type: application/json' \
  -d '{"area_id": "{area_id}", "intent_code": "rural_land_purchase"}'
```

The two-step report creation response is `202 Accepted` with `report_run_id` and
`status="queued"`.

### Idempotent report creation

`POST /report-runs` accepts an optional `Idempotency-Key` header. Reusing the same
non-blank key with the same area and intent returns the original report run instead of
creating a duplicate. Reusing the same key with a different area or intent returns
`409 Conflict`.

Signed-token report creation scopes the key to the authenticated workspace and user, so
two different principals can reuse the same raw key without replaying each other's
report. Both signed-token and unauthenticated operator paths return `202 Accepted` on
first queueing and `200 OK` with the same job on replay.

### Identifier glossary

Use these placeholders consistently in curl examples:

| Placeholder | Meaning | Where it comes from |
|---|---|---|
| `{area_id}` | Area of interest ID | Returned by `POST /areas` or `POST /intake`; pass this to generic `POST /report-runs` |
| `{report_run_id}` | Report/job ID | Returned by `POST /report-runs`, `POST /intake`, or `/operator-cases/{case_id}/report`; use it for poll/approve/dossier/artifact routes |
| `{case_id}` | Packaged selected-county fixture case slug (not an AOI UUID) | Returned by `GET /operator-cases`; only `/operator-cases/{case_id}/report` accepts it |
| `{ingest_run_id}` | Connector evidence/review run ID | Returned by connector-run routes and connector review queue payloads; use it for evidence lineage and review, not dossier delivery |

Mnemonic: `{case_id}` selects the packaged selected-county corpus, `{area_id}`
identifies the stored AOI record, `{report_run_id}` identifies the report job created
from either input, and `{ingest_run_id}` identifies connector evidence.

### Approve a report run

The final Markdown dossier (`GET /report-runs/{report_run_id}/dossier`) and the machine-readable
artifact (`GET /report-runs/{report_run_id}/artifact`) are both gated on approval status. A report
that has not been approved returns `409 Conflict`.

**Via the web UI:** navigate to the report page (`/ui/report-runs/{report_run_id}`). When the report
has succeeded but is not yet approved, an approval form is shown. Enter the reviewer ID
and token (scope: `report:approve`) and submit. The authenticated reviewer identity is
recorded in the immutable `review_actions` audit log — credentials are required and
validated on every submission.

**Via the API:** approve using reviewer headers on a reviewer account that holds the
`report:approve` scope:

```bash
curl -s -X POST http://localhost:8000/report-runs/{report_run_id}/approve \
  -H 'Content-Type: application/json' \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123' \
  -d '{"reason": "Screened and verified — approved for delivery"}'
```

The `reason` field is optional. The response returns the updated `ReportRunContract` with
`"review_status": "approved"` and the approval action recorded in `review_actions`. Once
approved, `GET /report-runs/{report_run_id}/dossier` returns the full Markdown dossier.

Approval is idempotent: a second `POST /approve` on an already-approved report returns
the current contract unchanged.

### Retry a failed report job

Report retry routes require reviewer headers:

```bash
X-Reviewer-Id: fixture-reviewer
X-Reviewer-Token: fixture-token-123
```

If `GET /report-runs/{report_run_id}` returns `status="failed"`, create a new report job
from the failed job's stored area and intent:

```bash
curl -s -X POST http://localhost:8000/report-runs/{report_run_id}/retry \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123'
```

The failed job is preserved. The response returns a new `report_run_id` plus
`retry_of_report_run_id` pointing at the failed job.

### Reviewed live connector queue scheduling

Connector scheduling routes require reviewer headers plus the request workspace/user
headers for the registered area:

```bash
X-Reviewer-Id: fixture-reviewer
X-Reviewer-Token: fixture-token-123
X-Workspace-Id: {workspace_id}
X-User-Id: {user_id}
```

To enqueue the current reviewed live-source sequence for an already registered area:

```bash
curl -s -X POST http://localhost:8000/connector-runs/live-sequence/schedule-bbox \
  -H 'Content-Type: application/json' \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123' \
  -H 'X-Workspace-Id: {workspace_id}' \
  -H 'X-User-Id: {user_id}' \
  -d '{
    "area_id": "{area_id}",
    "bbox": {"xmin": -77.10, "ymin": 38.80, "xmax": -77.00, "ymax": 38.90},
    "max_sample_points": 2,
    "max_features": 1,
    "max_rows": 1
  }'
```

The response returns `policy_id="reviewed_live_sequence_ds001_ds002_ds004_ds003_v1"` and
four durable live connector jobs in order: DS-001, DS-002, DS-004, DS-003, scoped to
the authenticated workspace. Scheduling does not call live sources, persist evidence,
approve review, or create reports. Run `py -3.12 .\scripts\live_connector_worker.py
--max-jobs 1 --json` to process queued jobs one at a time; report creation remains
separate and requires connector review approval.

### Queue health

Queue health requires reviewer headers and is read-only:

```bash
curl -s http://localhost:8000/operations/queue-health \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123'
```

The response reports status counts and oldest queued age for report jobs and live
connector jobs. It does not lease work, retry jobs, call live sources, persist evidence,
or create reports.

To inspect failed and stale-running recovery candidates without mutating queue state:

```bash
curl -s http://localhost:8000/operations/recovery-preview \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123'
```

The recovery preview response returns up to the response's
`candidate_limit_per_state` failed report jobs, stale-running report jobs, failed live
connector jobs, and stale-running live connector jobs with detail API/UI paths and
recommended inspection steps. Per-queue truncation booleans show when additional failed
or stale-running jobs exist beyond the candidate sample. It does not retry reports,
requeue live connector jobs, lease work, call live sources, persist evidence, or create
reports.

---

## Selected-County Operator Cases (server, no Docker required)

The selected-county private-MVP fixture cases are available through the app surface.
Use this server path when an operator wants an evidence-rich selected-county fixture
dossier through HTTP/UI instead of the no-server CLI. It packages the nine
Buncombe/Chatham/Brunswick cases under
`backend/app/operator_cases`, ingests the local fixture connectors for the selected case,
approves eligible connector-QA handoffs, creates an approved report, and returns the
existing report UI/download links.

List cases:

```bash
curl -s http://localhost:8000/operator-cases
```

Create an approved fixture report for one case:

```bash
curl -s -X POST http://localhost:8000/operator-cases/CHA-rural-use/report
```

The response includes:

- `links.ui`: open the report in `/ui/report-runs/{report_run_id}`
- `links.dossier_download`: approved Markdown dossier download
- `links.artifact`: approved machine-readable report JSON

In the web UI, open `http://localhost:8000/ui/` and use the
**Selected-County Private MVP Fixture Cases** table. The custom GeoJSON intake form remains
available on the same page for manual AOIs; it posts to `/ui/intake` without requiring
JavaScript and redirects to the created report or connector-review queue.

Report status/detail pages are also usable without JavaScript. Queued/running, failed,
missing, pending-approval, and approved report states render the current status first,
then the next available operator action: wait/list navigation for generating reports,
retry for failed reports, approve for pending reports, and export/download/lineage links
for approved reports. Queued/running pages auto-refresh every 3 seconds by default but
include no-JavaScript 3/10/30/60-second interval controls plus pause, manual refresh,
and resume links. Print/export attempts for missing or unapproved reports use the same
status/action shell and never expose dossier content before approval. Connector review,
operations, and evidence-lineage pages include the same mobile viewport contract while
retaining their no-JavaScript forms and return links.

This route remains fixture-only utility coverage. It does not use live-source production
coverage, does not unblock DS-017, and does not assert legal zoning, surveyed boundary,
wetland jurisdiction, buildability, legal access, appraisal, lending, insurance, or
investment conclusions.

Do not confuse this route with the generic `POST /report-runs` path. In default fixture
mode, generic report creation does not load the packaged selected-county connector
fixtures; use `/operator-cases/{case_id}/report` for the packaged selected-county
HTTP/UI path, or use `scripts/generate_dossier.py --connector all --approve` when no
server is running.

## Operator Path Proof Matrix

Use this matrix to pick the right path and avoid treating one proof as another.

| Path | Intended use | Proves | Does not prove |
|---|---|---|---|
| `scripts/generate_dossier.py --connector all --approve --artifact` | Fast no-server selected-county dossier and JSON artifact | County golden fixture evidence, approved-report state, source/caveat/unknown rendering, API-compatible in-memory artifact contract shape | HTTP routing, DB persistence, UI usability, live-source coverage |
| `POST /operator-cases/{case_id}/report` | Server/API selected-county fixture dossier | App-owned packaged selected-county corpus, local fixture ingestion, connector-QA approval handoff, approved report download/artifact links | Live county coverage, DS-017 readiness, generic `/report-runs` fixture ingestion |
| `/ui/` selected-county launcher | Browser operator flow for packaged cases | No-JavaScript UI launch into the same `/operator-cases` path and existing approved report pages | Full dashboard polish, user accounts/RBAC, live-source production operation |
| Generic `POST /report-runs` | Custom AOI report run from an existing `area_id` plus already-ingested state | Report job lifecycle, approval gate, artifact/dossier route contracts | Selected-county fixture ingestion in default mode; use `/operator-cases` for packaged cases |
| DB-backed verification with `RUN_DB_SMOKE=1` | Persistence proof | Migrations/seeds, DB service wiring, persisted report/artifact behavior for the generic full reviewed dossier path, representative selected-county operator cases, and the selected-county UI launcher | No-server CLI behavior, hosted deployment, live-source production coverage, external identity/secrets |
| Live connector queue paths | Reviewed live-source screening workflows | Bounded source-specific fetch/schedule/review behavior for implemented connectors | Recorded fixture parity, paid vendor coverage, legal/buildability/title/value conclusions |

DB-backed verification includes the generic full reviewed dossier path in
`backend/tests/api/test_report_runs_db.py` plus representative selected-county operator DB smoke cases `BUN-slope`, `CHA-zoning-edge`, and `BRU-coastal-flood`
in `backend/tests/api/test_operator_cases_db.py`. The same DB smoke file also covers
the `/ui/operator-cases/report` launcher for one representative selected-county case,
including redirect to the approved report page, approved UI delivery links, and persisted
JSON artifact delivery.
It does not prove full hosted production, live-source production coverage, or counties
outside the selected private-MVP set.

### Operator path execution qualifiers

| Path | Evidence richness | Approval gate | DB required | Live network required | Main limitation |
|---|---|---|---|---|---|
| `scripts/generate_dossier.py --connector all --approve --artifact` | High selected-county fixture evidence plus final dossier/artifact shape | `--approve` calls the same approval service method as the HTTP path; no reviewer HTTP hop | No | No | No HTTP routing, UI, or DB persistence proof |
| `POST /operator-cases/{case_id}/report` | High selected-county fixture evidence through the app-owned packaged corpus | Yes; use returned dossier/artifact links as the routed app proof | No for default local/in-memory smoke; add `RUN_DB_SMOKE=1` separately for persistence proof | No | Fixture-only packaged cases, not live county fetches |
| `/ui/` selected-county launcher | High selected-county fixture evidence plus no-JavaScript operator UX | Yes; same approved-report and dossier gates as `/operator-cases` | No for default local/in-memory smoke; add `RUN_DB_SMOKE=1` separately for persistence proof | No | UI usability for packaged cases only; not full accounts/RBAC |
| Generic `POST /report-runs` | Low by default; strongest as a code-level integration pattern over an existing `{area_id}` plus whatever evidence is already ingested/reviewed | Yes | No for default local/in-memory smoke; add `RUN_DB_SMOKE=1` separately for persistence proof | Only when you intentionally enable live connector ingestion; otherwise no | This is not the packaged selected-county corpus path and does not auto-load selected-county fixtures in default mode |
| DB-backed verification with `RUN_DB_SMOKE=1` | Same evidence as the exercised path plus persisted artifact metadata | Same as the exercised path | Yes | No by itself | Persistence proof only for the exercised generic dossier path, representative selected-county operator DB smoke cases, and one selected-county UI launcher DB smoke |
| Live connector queue paths | Connector-dependent live evidence | Connector review queue applies where implemented | Optional, depending on runtime | Yes | Only implemented live connectors; no packaged selected-county parity |

---

## Local Dossier Generation (no server required)

Generate a Markdown dossier directly from a GeoJSON AOI file using fixture connectors.
No database or API server is required. Basic preview commands can omit approval; final
operator delivery should use `--approve` plus `--artifact` so the Markdown dossier and
JSON artifact carry approved-report state.

```bash
# Single connector (flood only)
py -3.12 scripts/generate_dossier.py \
  --aoi tests/fixtures/golden_aois/cha_rural_use.geojson \
  --intent homestead_feasibility

# All available connectors (flood + access + zoning where fixtures exist)
py -3.12 scripts/generate_dossier.py \
  --aoi tests/fixtures/golden_aois/cha_rural_use.geojson \
  --intent homestead_feasibility \
  --connector all

# Write to file instead of stdout
py -3.12 scripts/generate_dossier.py \
  --aoi tests/fixtures/golden_aois/bru_wetlands_soils.geojson \
  --intent rural_land_purchase \
  --connector all \
  --output /tmp/bru_dossier.md
```

`--connector all` runs parcels, flood, access, zoning, buildability, soils, terrain,
and wetlands in sequence. Missing fixtures for a given AOI are warned and skipped —
the dossier is still produced from whichever connectors succeeded. Evidence from each
connector is auto-approved for connector QA when the quality profile is
`READY_FOR_CONNECTOR_QA`.

Available AOI fixtures (9 cases): `tests/fixtures/golden_aois/*.geojson`.
Available connector fixtures: `tests/fixtures/connectors/*.json`.

### Operator Quickstart — approved dossier + artifact (no server, no Docker)

```powershell
py -3.12 scripts/generate_dossier.py `
  --aoi tests/fixtures/golden_aois/cha_rural_use.geojson `
  --intent homestead_feasibility `
  --connector all `
  --approve `
  --artifact local_artifacts/cha_rural_use_report.json `
  --output local_artifacts/cha_rural_use_dossier.md
```

This is the no-Docker, no-network operator path that produces an APPROVED selected-county dossier (Markdown) plus the machine-readable JSON artifact.
`--approve` calls the same `approve_report_run` service method the HTTP approve endpoint uses and emits the same in-memory report artifact contract shape. It does not prove the HTTP `POST /report-runs` surface, `/operator-cases/{case_id}/report`, or DB artifact persistence. It does not exercise HTTP routing, access gates, or DB artifact persistence; the API tests and DB-smoke tests cover those separately.
`local_artifacts/` is a gitignored on-demand output location.

---

## Token Generation

Generate a short-lived report identity bearer token for authenticated API calls:

```bash
REPORT_IDENTITY_TOKEN_SECRET=<your-32+-char-secret> \
py -3.12 scripts/mint_report_token.py \
  --workspace-id <workspace-uuid> \
  --user-id <user-uuid> \
  --expires-minutes 480

# JSON output with full token metadata
REPORT_IDENTITY_TOKEN_SECRET=<secret> \
py -3.12 scripts/mint_report_token.py \
  --workspace-id <workspace-uuid> \
  --user-id <user-uuid> \
  --json
```

Use the printed token as `Authorization: Bearer <token>` with `X-Workspace-Id` and
`X-User-Id` headers on API calls. Requires `REPORT_AUTH_MODE=signed_token` in the
server environment (default is `trusted_headers` for local development).

---

## Web Interface

### Deployment posture and API-key locking

When `REQUIRE_API_KEY=true` is set, JSON/API routes require `X-API-Key`. The
operator web UI supports a private-beta browser bridge: `/ui/auth` is public,
accepts the same configured API key, and sets a signed expiring HttpOnly SameSite
cookie scoped to `/ui` without storing the submitted API key. Set
`UI_AUTH_COOKIE_SECRET` to a high-entropy value in shared environments. With
`REQUIRE_API_KEY=true`, non-local `APP_ENV` values fail startup if it is blank and also
reject `API_KEYS` plus raw `API_KEY_SPECS` secrets. Only local/dev/development/test
config uses a per-process signing secret and may keep raw fixture API-key values.
Non-local `APP_ENV` values set the cookie `Secure` flag automatically;
`UI_AUTH_COOKIE_SECURE=true` can force it in any environment. Cookie-authenticated UI
mutation forms include a signed CSRF token derived from the HttpOnly UI cookie; refresh
stale forms before retrying an action. Sign-out is a CSRF-protected POST from
`/ui/auth/logout`. That cookie is accepted only by `/ui/*` routes; `/areas` and other
JSON/API paths still require `X-API-Key`. `/health` and `/version` remain public for
smoke checks.

Reviewer tokens for UI operations are separate from API keys. Configure them via
`REVIEWER_ACCOUNTS` and `REVIEWER_ACCOUNT_SCOPES` (see the Configuration table above and
`.env.example`). Non-local `APP_ENV` values require explicit reviewer accounts using
`id:sha256:<64-hex>` token specs and explicit scopes; the default fixture reviewer is
local-only.

### Home page and intake

Open `http://localhost:8000/ui/` in a browser. Submit a GeoJSON polygon and select an
intent. The page submits to `/intake` and then either:

- Redirects to the report status page (`/ui/report-runs/{report_run_id}`), which auto-refreshes
  while the report is generating, can be slowed with `?refresh_seconds=30`, and can be
  paused with `?auto_refresh=false`; or
- Shows a yellow banner with a link to the **Connector Review Queue** if the intake
  response returns `status=pending_connector_review` (no report job exists yet at that
  point — the link goes directly to the queue item).

The home navigation also links directly to the connector review queue so operators can
recover review-gated work after leaving an intake result or returning to the console
later.

### Report list (`/ui/report-runs`)

The report list shows up to 30 runs per page with a status filter dropdown and
previous/next pagination links. The status filter accepts: `queued`, `running`,
`succeeded`, `failed`; unknown status values return a safe HTML error instead of
falling back to an unfiltered list. Each row has an **Action** column: queued/running
rows link to the status page, failed rows link to the detail page where retry credentials
can be entered, succeeded-but-unapproved rows link to the approval detail page, and
approved rows expose view, dossier download, JSON artifact download, and lineage links.
Each succeeded row displays its review badge (`approved` in green or `pending` in
amber). The wide table is wrapped for horizontal scrolling on narrow screens. The page
navigation links back to the home console, operations dashboard, and connector review
queue.

A **Compare** affordance lets operators select 2–4 report runs using the checkboxes and
open a side-by-side summary at `/ui/compare?ids=<uuid>,<uuid>[,...]`. The compare view
shows report/review/delivery status, claim/unknown/red-flag/verification-task counts,
high-severity claim code/domain summaries, and gated next-action links. Approved
reports expose existing dossier, artifact, print, and lineage links; unapproved reports
link only to the report detail/approval page. When exactly two compared reports share
the same `area_id`, the page also renders a **Change Review** section using the same
diff semantics as `GET /report-runs/{report_run_id}/diff?base_id=<uuid>`: ruleset changed,
added/removed claim codes, added/removed sources, and evidence-count delta. Report
content is still gated on approval status.

The compare control is a native `GET /ui/compare` form and works without JavaScript.
With JavaScript disabled, selected rows submit as repeated query parameters
(`/ui/compare?ids=<uuid>&ids=<uuid>`). The compare route also preserves the existing
comma-separated URL format.

Programmatic access: `GET /report-runs?status=<value>&limit=<n>&offset=<n>` (max limit
100) returns a JSON list of report run summaries.

### Report page (`/ui/report-runs/{report_run_id}`)

- **Queued or running:** the page auto-refreshes every 3 seconds by default. Use the
  **Refresh interval** selector to apply 3, 10, 30, or 60 seconds without JavaScript.
  Use **Pause auto-refresh** to reopen it with `?auto_refresh=false`; the paused page
  removes the refresh meta tag and shows **Refresh now** plus **Resume auto-refresh**
  links while preserving a non-default `refresh_seconds` value.
- **Failed:** shows the error message and a retry form (see below).
- **Succeeded, not yet approved:** shows the approval form (see below).
- **Approved:** shows the rendered dossier with nav links:
  - **Download dossier (.md):** `GET /report-runs/{report_run_id}/dossier?download=1` — serves the
    Markdown dossier as an attachment; approved-only (returns `409` if not approved,
    `202` if still running, `404` if not found).
  - **Download report (.json):** `GET /report-runs/{report_run_id}/artifact` — serves the
    machine-readable report JSON as an attachment; approved-only with identical gating.
    In DB-backed mode the persisted artifact file is served; in-memory mode the contract
    is serialised at request time.
  - **Print / Export PDF:** `/ui/report-runs/{report_run_id}/print` — print-optimised HTML page;
    approved-only.
  - **View evidence lineage:** see below.

### Approving a report run via the UI

The report page for a succeeded-but-unapproved run shows an approval form. Without a
reviewer UI session, the form requires **Reviewer ID** and **Reviewer token** fields
(scope: `report:approve`) and accepts an optional approval reason. Blank approval
reasons are stored as omitted audit notes; non-empty reasons are trimmed and recorded on
the report review action. A successful credential submission can establish the UI-only
reviewer session described below; JSON/API reviewer routes still require reviewer
headers and do not use the UI cookie.
On success the page redirects back to the report view. On credential failure the
response carries the real HTTP status (401/403/503) and a generic error message — no
field-level detail is leaked.

The default fixture account (`fixture-reviewer` / `fixture-token-123`) in
`.env.example` includes the private-MVP operator scopes. If a local environment overrides
`REVIEWER_ACCOUNT_SCOPES`, keep `report:approve` before using the UI approval form in
development:

```
REVIEWER_ACCOUNT_SCOPES=fixture-reviewer:connector:run|connector:review|operations:read|report:approve|report:retry|report:run|source:manage
```

API-based approval (unchanged) sends credentials as headers:

```bash
curl -s -X POST http://localhost:8000/report-runs/{report_run_id}/approve \
  -H 'Content-Type: application/json' \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123' \
  -d '{"reason": "Screened and verified — approved for delivery"}'
```

### Retrying a failed report run via the UI

The report page for a failed run shows a retry form. The form requires **Reviewer ID**
and **Reviewer token** (scope: `report:retry`). On success a new report run is created
and the page redirects to it. The original failed job is preserved.

### Connector review queue (`/ui/connector-review-queue`)

When an intake request returns `status=pending_connector_review`, no report job exists
yet. The operator must action the connector review item before a report can be generated.

**Queue list** (`/ui/connector-review-queue`): table of connector ingest runs with status
filter and limit/offset pagination (default 25 per page). Columns: ingest run ID,
connector, status, attempts, compact triage summary, next action, and created. The
triage column summarizes existing review payload fields: disposition, signal codes,
first human-review task, blocking issue count, evidence counts, and source-failure
counts. The next-action link always opens the detail page; it labels the expected
operator path for the current queue status without duplicating credentialed mutation
forms on the list. Unknown status filter values return a safe HTML error instead of
falling back to an unfiltered queue. Wide queue tables are contained in a horizontal
scroll wrapper on narrow screens.

**Item detail** (`/ui/connector-review-queue/{ingest_run_id}`): starts with a
**Decision Context** panel before mutation forms. It shows the connector handoff title
and summary, retrieval status/counts/log URI/metrics, review signals, human-review
tasks, evidence/source-failure counts, and compact evidence cards with evidence code,
observation, caveat, and evidence ID. The page still shows quality issues (blocking
issues highlighted in red) plus attempts/lock/timing metadata, but it does not dump raw
queue payload fields or secret-looking metric keys.

Action forms require **Reviewer ID** and **Reviewer token** with scope
`connector:review`, and the detail page only shows actions that are valid for the
queue item's current status:

| Action | When to use | Reason field |
|---|---|---|
| **Approve for QA** | Open item in `needs_review`, `queued`, or `running` status | Optional |
| **Request Fix (Reject)** | Open item in `needs_review`, `queued`, or `running` status | Required |
| **Requeue After Fix** | Failed item has been corrected and retry attempts remain | Required |
| **Cancel** | Non-terminal item should stop processing | Required |

After a queue item reaches `succeeded` status (approved), a **Resume Report Run** form
appears. This form uses the current reviewer session when it has `report:run` scope;
otherwise enter **Reviewer ID** and **Reviewer token** with `report:run` scope plus
an intent selection. Submitting it creates a new report run for the
area associated with the approved connector run and redirects to the report page.
Terminal queue items with no valid mutation action render an explicit no-actions message
instead of invalid action forms.

### Operations dashboard (`/ui/operations`)

Navigate to `/ui/operations`. When the current reviewer session has `operations:read`
scope, the dashboard renders directly on `GET /ui/operations`; otherwise the page shows
the credential form. Submitting valid **Reviewer ID** and **Reviewer token** credentials
with `operations:read` scope also creates the reviewer UI session before rendering the
dashboard. The page renders queue-health tables for report jobs and live connector jobs
(total, queued, running, succeeded, failed, cancelled, needs review, oldest queued age).
The dashboard is read-only; it does not lease work, retry jobs, or call live sources.
Count cells link to the corresponding report list or connector review queue filter so
operators can drill into affected work without leaving the UI. Wide queue-health tables
are contained in horizontal scroll wrappers on narrow screens.

The dashboard links to `/ui/operations/recovery-preview`, which renders the same
read-only failed/stale-running recovery candidate view in the browser. Candidate rows link
only to existing report or live connector job detail pages; the page labels the per-state
candidate cap and shows a truncation note if more failed or stale-running jobs exist. The
preview page does not perform retries, requeues, leases, or source calls.

Equivalent API call:

```bash
curl -s http://localhost:8000/operations/queue-health \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123'
```

### Evidence lineage (`/ui/report-runs/{report_run_id}/lineage`)

Linked from approved report pages as **View evidence lineage**. Renders three tables:

- **Sources → Ingest Runs** — each data source and the ingest run chain that produced
  its evidence.
- **Claims → Evidence** — each claim and the evidence record IDs that support it.
- **Evidence → Claims** — each evidence record, its source, and the claims that cite it.
  `UNKNOWN` evidence (no data) is highlighted amber; `SOURCE_FAILURE` evidence is
  highlighted red.

The operator UI lineage page follows the approved-report delivery boundary:
direct visits for succeeded-but-unapproved reports return an **Approval Required**
page and link back to the report review page. The JSON lineage API
(`GET /report-runs/{report_run_id}/lineage`) remains available for service consumers under
the normal API access policy. Wide lineage tables are contained in horizontal
scroll regions on narrow screens.

---

## Health Check

```bash
curl http://localhost:8000/health
# {"status": "ok", "app": "land-diligence", "environment": "development"}

curl http://localhost:8000/version
# {"version": "0.1.0"}
```

---

## Backup and Restore Check

Run the restore proof before claiming backup coverage:

```powershell
.\scripts\run_backup_restore_check.ps1
```

The check dumps the configured source DB, restores it into a dedicated
`land_diligence_restore_check*` database, runs `scripts/db_smoke_check.py` against the
restored DB, and drops the restore DB unless `RESTORE_CHECK_KEEP_DB=1`.

See `docs/runbooks/backup_restore.md` for safety boundaries and environment variables.

---

## Deployment Smoke

Run deployment smoke after Compose/runtime changes and before claiming deploy readiness:

```powershell
.\scripts\run_deployment_smoke.ps1
```

The smoke check uses an isolated Compose project named `land-diligence-smoke` by default,
builds the backend image, starts DB-backed Compose services, applies migrations/seeds,
checks `/health`, `/version`, `/metrics`, and `/operations/queue-health`, then creates an
area and report run through the deployed HTTP API. It stops the Compose services on exit
unless `DEPLOYMENT_SMOKE_KEEP_SERVICES=1`.

Optional environment variables:

| Variable | Default | Description |
|---|---|---|
| `DEPLOYMENT_SMOKE_PROJECT` | `land-diligence-smoke` | Compose project name |
| `DEPLOYMENT_SMOKE_BACKEND_PORT` | `18080` | Host port for backend |
| `DEPLOYMENT_SMOKE_DB_PORT` | `55432` | Host port for Postgres |
| `DEPLOYMENT_SMOKE_KEEP_SERVICES` | unset | Set to `1` to preserve services for debugging |

---

## UI Browser Smoke

After starting a local, private-beta, or hosted candidate runtime, run the UI smoke
checks before claiming browser usability:

```powershell
$env:LAND_DD_UI_SMOKE_BASE_URL = 'http://127.0.0.1:8000'
.\scripts\run_ui_browser_smoke.ps1
python .\scripts\ui_runtime_smoke.py --base-url $env:LAND_DD_UI_SMOKE_BASE_URL
```

The browser smoke launches Chrome with temporary profiles, checks the core `/ui/*`
surfaces at desktop (`1366x900`) and mobile (`390x844`) viewports, fails closed on
missing DOM contracts or page-level horizontal overflow, and removes its temporary
Chrome profiles. It does not create areas, report runs, connector-review items, review
actions, screenshots, or JSON output by default.

To opt in to an operator-case runtime delivery check after the default route checks,
pass a selected-county case id to the urllib-based runtime smoke:

```powershell
python .\scripts\ui_runtime_smoke.py --base-url $env:LAND_DD_UI_SMOKE_BASE_URL --operator-case-id BUN-slope
```

This posts the existing UI form field to `/ui/operator-cases/report`, follows the
redirect to the approved report UI page, and checks the final page for the executive
summary, Markdown dossier download, JSON report download, and evidence-lineage link.
It creates an in-memory approved report in the target runtime when that runtime uses
the default in-memory services; use it only when mutating fixture state is intentional.
For a DB-backed runtime, add an artifact persistence assertion:

```powershell
python .\scripts\ui_runtime_smoke.py --base-url $env:LAND_DD_UI_SMOKE_BASE_URL --operator-case-id BUN-slope --expect-artifact-persistence postgres+object_store
```

That DB-backed invocation follows the same UI path and then fetches the linked JSON
artifact, requiring `artifact_metadata.persistence` to equal `postgres+object_store`.

Set these optional environment variables only when the target runtime requires them or
when collecting explicit visual evidence:

| Variable | Default | Description |
|---|---|---|
| `LAND_DD_UI_SMOKE_BASE_URL` | `http://127.0.0.1:8000` | Running app base URL |
| `LAND_DD_CHROME_PATH` | auto-detect | Chrome/Chromium executable path |
| `LAND_DD_UI_SMOKE_MODE` | `headless` | `headless`, `headed`, or `both` |
| `LAND_DD_UI_SMOKE_API_KEY` | unset | Optional UI API key for API-key-locked runtimes |
| `LAND_DD_UI_SMOKE_REVIEWER_ID` | unset | Optional reviewer id for reviewer-session checks |
| `LAND_DD_UI_SMOKE_REVIEWER_TOKEN` | unset | Optional reviewer token for reviewer-session checks |
| `LAND_DD_UI_SMOKE_SCREENSHOT_DIR` | unset | Opt-in screenshot output directory, usually under `local_artifacts/` |

Use headed mode or screenshot output only for deliberate visual review. Screenshots can
contain private operator/report data and must remain in ignored local artifact paths.

---

## Incident Response

Use `docs/runbooks/incident_response.md` for severity, ownership, escalation, rollback,
and recovery criteria. Validate the runbook and referenced proof scripts with:

```powershell
.\scripts\run_incident_rollback_check.ps1
```

---

## Alerting Rules

Use `config/ops_alert_rules.yaml` as the repo-local alert catalog for high-severity
failures, queue health, deployment/DB/backup checks, source-readiness drift, and stale
source metadata. Validate the catalog with:

```powershell
.\scripts\run_alert_rules_check.ps1
```

See `docs/runbooks/alerting.md` for rule sources, operator workflow, escalation, and known
limits. The catalog does not create hosted dashboards, alert routing, or pager delivery.

---

## Supply Chain Checks

The CI workflow includes a `supply-chain` job that validates the backend production
dependency lock/SBOM, installs the backend dependency environment, and runs
`pip-audit --local`. It also includes a `container-image-scan` job that builds the
backend image from `backend/Dockerfile` and, when Docker Scout credentials are configured,
scans the local image with Docker Scout for
critical/high CVEs. Dependabot is configured for GitHub Actions and backend Python
dependency metadata.

Validate the repo-local supply-chain configuration with:

```powershell
.\scripts\run_supply_chain_check.ps1
```

See `docs/runbooks/supply_chain.md` for operator workflow and limits. The CI workflow
publishes GitHub artifact attestations for the repo-local production lock and SBOM, but
does not publish a release package or registry image with attached attestations. The
backend Dockerfile pins the `python:3.12-slim` base image by OCI index digest; see
`docs/runbooks/container_image_scan.md` for the Docker image scan boundary,
`docs/runbooks/image_publication.md` for the registry publication boundary, and
`docs/runbooks/hosted_deployment.md` for the hosted deployment boundary.

---

## Cost Monitoring

Use `config/ops_cost_monitoring.yaml` as the repo-local cost monitoring catalog for
compute, storage, LLM-if-used, maps, geocoding, and data-vendor guardrails. Validate the
catalog with:

```powershell
.\scripts\run_cost_monitoring_check.ps1
```

The current app records report-shape `artifact_metadata.cost_metrics` counts plus
zero-dollar attribution fields for local-only paths, and keeps LLM, geocoding,
map/tile, and paid data-vendor paths disabled or blocked until metered.
See `docs/runbooks/cost_monitoring.md` for workflow and limits.

---

## Access Control

Use `config/access_control.yaml` as the repo-local access-control posture catalog.
Validate it with:

```powershell
.\scripts\run_access_control_check.ps1
```

The access-control proof is validate-only and static. It checks the current default-off
API-key middleware, private-beta UI API-key cookie bridge, local scoped reviewer
service-account auth, reviewer-authenticated and scoped operator routes, intentionally
public `/health` and `/version` routes, CI proof wiring, configured static API-key
lifecycle support, structured API-key auth runtime logs/audit rows including
`/ui/auth` login attempts, the repo-local `identity_rbac_contract` design handoff,
and explicit production auth blockers. The identity/RBAC handoff maps future roles
to current route scopes and names required identity/audit claims, but it does not add
user accounts, OAuth/OIDC, full user RBAC, automatic key rotation, hosted
identity-provider integration, or user-bound audit semantics.
It does not add user accounts, OAuth/OIDC, full user RBAC.

---

## Release Readiness

Use `config/release_readiness.yaml` as the repo-local release gate catalog. Validate it
with:

```powershell
.\scripts\run_release_readiness_check.ps1
```

The release-readiness proof is validate-only. It gathers the repo's existing verification,
DB, deployment smoke, supply-chain, image scan, backup/restore, incident, alerting, cost,
access-control, release-package, image-publication, hosted-deployment, and
source-readiness proofs into one boundary. It does not push a registry image, create a
hosted deployment, or attach published registry-image attestations.

---

## Release Package

Use `config/release_package.yaml` as the local package boundary. Validate it with:

```powershell
.\scripts\run_release_package_check.ps1
```

After the release gates pass, create a local source/runtime/operator ZIP and manifest
with:

```powershell
.\scripts\build_release_package.ps1 -Version <version>
```

The package is written under `local_artifacts/releases`. The builder fails if outputs
already exist and does not delete, overwrite, push, deploy, or publish anything.

---

## Image Publication

Use `config/image_publication.yaml` as the validate-only registry image publication
boundary. Validate it with:

```powershell
.\scripts\run_image_publication_check.ps1
```

The proof checks the backend image source, required release/deployment/scan gates,
required post-publish evidence, and publication blockers. It does not push a registry
image, create a hosted deployment, sign an image SBOM, or publish registry attestations.

---

## Hosted Deployment

Use `config/hosted_deployment.yaml` as the validate-only hosted runtime deployment
boundary. Validate it with:

```powershell
.\scripts\run_hosted_deployment_check.ps1
```

The proof checks required pre-deploy gates, runtime inputs, runtime evidence, and hosted
platform/DNS/TLS/secrets/database/billing/alerting blockers. It does not create hosted
infrastructure, write secrets, open a public endpoint, or deploy a registry image.

---

## Data retention

Use `config/data_retention.yaml` as the repo-local data retention policy catalog.
Validate it with:

```powershell
.\scripts\run_data_retention_check.ps1
```

The MVP retains all operational data (report runs, evidence, job queue, source ingest
runs) indefinitely. Audit events (`audit.events`) have a target retention period of
90 days, but no automated purge exists yet. All deletion is a manual operator action.

See `docs/runbooks/data_retention.md` for retention classes, manual purge SQL, and
future work items.

---

## Known Limitations

| Limitation | Impact |
|---|---|
| In-memory job store | Local/dev/test-only mode. Job status is lost on server restart; pending jobs cannot be recovered |
| Live connectors are bounded and review-gated | Reviewed Must-priority paths now include DS-001, DS-002, DS-003, and DS-004 public-source connectors, DS-010 selected-county parcel connectors, the DS-011 assessor NOT_EVALUATED sentinel, and DS-023 Chatham/Brunswick recorded-fixture zoning. Outputs remain screening-only and cannot assert legal/buildability/title/water/wetland jurisdiction conclusions. |
| County/vendor coverage is intentionally scoped | DS-010 parcel connectors are limited to Buncombe/Chatham/Brunswick selected-county operator flows; DS-011 assessor remains explicit NOT_EVALUATED evidence, not live assessor data; DS-017 commercial parcel vendor remains blocked; DS-023 covers Chatham/Brunswick recorded-fixture zoning only. Buncombe zoning and all other counties remain NOT_EVALUATED. |
| Single-process local default | In-memory stores are not shared across multiple workers or processes; non-local runtime must use DB-backed services |
| No full user auth/RBAC | API-key and scoped reviewer service-account gates exist, `API_KEY_SPECS` supports configured active/retired static key lifecycle entries, and API-key decisions emit structured runtime logs plus DB-backed `audit.events` rows in DB-service mode. The repo-local `identity_rbac_contract` maps future roles to current route scopes for design handoff only; there are no user accounts, OAuth/OIDC, full user RBAC, hosted identity provider, automatic key rotation, hosted log retention, or user-bound audit semantics |
| Private-beta UI API-key bridge only | When `REQUIRE_API_KEY=true` is set, `/ui/auth` can set a signed expiring HttpOnly SameSite cookie scoped to `/ui` after the submitted API key passes the same verifier as `X-API-Key`; the cookie does not store the submitted API key, is signed with `UI_AUTH_COOKIE_SECRET`, and fails startup outside local/dev/development/test app envs when that setting is blank. Local/dev/development/test app envs may use a per-process fallback. The cookie is `Secure` automatically outside local app envs. Cookie-authenticated UI mutation forms require signed CSRF tokens and sign-out uses POST. JSON/API paths still require `X-API-Key`; this is not full user auth/RBAC, OAuth/OIDC, user-account persistence, automatic key rotation, or hosted secret management. |
| UI reviewer auth is private-beta session auth | Browser operators can start a signed expiring HttpOnly reviewer session at `/ui/auth/reviewer` or by submitting reviewer credentials on the first UI action. The cookie is scoped to `/ui`, stores reviewer id/scopes/expiry plus a non-secret HMAC binding to the configured token spec, is invalidated by reviewer-token rotation or scope removal, and never authenticates JSON/API routes. API clients must still send `X-Reviewer-Id` and `X-Reviewer-Token`. This is not full user auth/RBAC. |
| Local fixture mode has no persistence | In-memory repositories reset on restart; production-like runtime must set `USE_DB_SERVICES=true` with `DATABASE_URL` |
| Repo-local alert rules only | Alert rules are validated as artifacts, but no hosted alert manager, dashboard, pager, or named on-call rotation exists |
| Supply-chain scan limits | CI runs Python dependency vulnerability scanning, validates and attests the repo-local production lock/SBOM, pins the backend base image by OCI index digest, scans the locally built backend image for critical/high CVEs, and validates the image-publication and hosted-deployment boundaries, but there is no hosted deployment or published-registry image attestation |
| Cost monitoring is local and zero-dollar attributed | Report cost metrics include local-only USD-cent attribution, but no hosted billing reconciliation or approved nonzero unit-cost thresholds exist yet |
| Release package is local | Local ZIP package creation exists under `local_artifacts/releases`, but there is no pushed registry image, hosted deployment, signed image SBOM, or published registry-image attestation yet |

---

## Troubleshooting

**422 on POST /intake**
- GeoJSON is malformed or the geometry type is unsupported (must be Polygon or MultiPolygon).
- `intent_code` must be exactly `rural_land_purchase` or `homestead_feasibility`.

**404 on GET /report-runs/{report_run_id}**
- The ID is unknown. If the server restarted after the job was created, the job record was lost.
  Submit a new intake request.

**Report stuck in `queued`**
- The server was restarted after the POST /intake but before the background task ran.
  The in-memory job store is gone. Submit a new intake request.

**`status: failed` in report response**
- Check `caveats` field in the response for the error message.
- Common causes: area not registered (should not occur via /intake), rule engine misconfiguration.

**UI approval form returns 401 or 403**
- Reviewer credentials are missing or wrong, the reviewer session is expired/invalid, or the reviewer account does not hold `report:approve` scope.
- Start or refresh a reviewer session at `/ui/auth/reviewer`, or enter reviewer credentials directly in the action form.
- Check `REVIEWER_ACCOUNTS` and `REVIEWER_ACCOUNT_SCOPES` in the server environment.
  If the environment overrides the `.env.example` default fixture scopes, keep
  `report:approve` before testing UI approval in development.
- 503 means reviewer accounts are not configured at all.

**UI returns 401/403 on every page (locked out)**
- `REQUIRE_API_KEY=true` is set and the browser has no valid `/ui` auth cookie.
  Visit `/ui/auth`, submit the configured API key, and retry the UI route.
- JSON/API callers must continue sending `X-API-Key`; the `/ui/auth` cookie is
  a signed expiring token and is not accepted outside `/ui/*`.
- If the app restarted in local/dev/development/test with `UI_AUTH_COOKIE_SECRET`
  blank, sign in again. Set a stable high-entropy `UI_AUTH_COOKIE_SECRET` before
  running API-key-locked shared or production-like environments.
- A 403 security-check page on a UI form usually means the form's CSRF token is stale
  or missing. Refresh the page and submit again.

**Intake response shows `pending_connector_review` but no report link**
- This is expected when a live connector run requires review before a report can be
  generated. The home page renders a banner with a link to
  `/ui/connector-review-queue/{connector_ingest_run_id}`. Action the item in the queue,
  then use the **Resume Report Run** form on the approved queue detail page.

**Connector review action returns 409**
- The queue item is not in a state that allows the requested action (e.g. trying to
  approve an item that is already cancelled, or resuming a report from a non-succeeded
  item). Navigate back to the queue detail page to check the current status.

**Download link returns 409**
- `GET /report-runs/{report_run_id}/dossier?download=1` or `GET /report-runs/{report_run_id}/artifact` returns
  `409 Conflict` when the report has not been approved. Approve the report first via the
  UI approval form or the API.

**Verification:**

```bash
cd backend && py -3.12 -m pytest -q
# or on Windows:
.\scripts\verify.ps1
```

---

## Private MVP Utility Proof (fixture-backed, no paid vendors)

This path proves the end-to-end pipeline for North Carolina private MVP counties
(Buncombe, Chatham, Brunswick) using only official/public or fixture-backed sources.
No API keys, paid vendors, or live DB are required.

Validate the private-MVP gate catalog before handing off a private beta build:

```powershell
.\scripts\run_private_mvp_readiness_check.ps1
```

This proof is validate-only. It keeps DS-017 Commercial parcel vendor and hosted
production work blocked for full release readiness while confirming those blockers do
not gate the selected NC county private-MVP utility proof.

### Geography and scope

- **Counties:** Buncombe, Chatham, Brunswick (NC)
- **Intent:** `homestead_feasibility` / `rural_land_purchase`
- **Connector domains:** fixture regression exercises `flood`, `access`, `zoning`,
  `parcels`, `terrain`, `wetlands`, `soils`, and `buildability` as declared per
  case in `tests/fixtures/golden_aois/manifest.yaml`.
- **NOT_EVALUATED domains:** case-specific per manifest. Assessor remains
  NOT_EVALUATED in all fixture regression cases. Parcel fixtures are now
  present for all 9 golden AOIs, so parcel identity populates in every
  dossier. Selected-county DS-010 live connectors are reviewed separately
  and still exclude owner/value/title fields.

### 1. DB startup (optional — in-memory is sufficient for fixture regression)

For full DB-backed mode, start Postgres and apply migrations:

```powershell
docker compose up -d db
.\scripts\db_apply_migrations.ps1
```

The migration scripts can use a Dockerized `psql` client when no local PostgreSQL
client is installed. If Postgres is mapped to a non-default host port, set both
`DATABASE_URL_SYNC` and `DATABASE_URL` before running DB-backed tests or
`.\scripts\verify.ps1`.

For the fixture regression suite, in-memory services are used and no DB is required.

### 2. Fixture-backed AOI intake

Register an area of interest using a golden fixture geometry:

```bash
curl -s -X POST http://localhost:8000/areas \
  -H 'Content-Type: application/json' \
  -d '{
    "geom_geojson": {"type":"Polygon","coordinates":[[[-82.340,35.615],[-82.320,35.615],[-82.320,35.625],[-82.340,35.625],[-82.340,35.615]]]},
    "label": "bun-slope-test",
    "geom_source": "golden-aoi-fixture"
  }'
```

Alternatively, load a GeoJSON file from `tests/fixtures/golden_aois/` and POST its
`geometry` field.

### 3. Run fixture connector workflow (Path B)

**Quickest path (no server required):** use `scripts/generate_dossier.py --connector all`
(see [Local Dossier Generation](#local-dossier-generation-no-server-required)). Steps
3–5 below describe the equivalent code-level flow for integration testing.

Fixture connectors are invoked via `FixtureConnectorIngestWorkflow` with the
domain-appropriate quality evaluator. From Python:

```python
from app.connectors import (
    StaticFloodFixtureConnector,
    evaluate_flood_fixture_quality,
    build_fixture_workflow_with_public_services,
)

workflow = build_fixture_workflow_with_public_services(
    retrieval_provenance_port=retrieval_port,
    evidence_service=evidence_service,
    connector=StaticFloodFixtureConnector(),
    quality_evaluator=evaluate_flood_fixture_quality,
)
result = workflow.ingest_fixture("tests/fixtures/connectors/nc_buncombe_bun_slope_flood.json")
```

Repeat for each manifest-declared fixture domain by pairing the matching
`Static*FixtureConnector` with its `evaluate_*_fixture_quality` function as
applicable per the case manifest in `tests/fixtures/golden_aois/manifest.yaml`.

### 4. Report creation and review/approval gate

Create a report run after connector evidence is ingested. Evidence with
`source_ingest_run_id = None` (all fixture connector blobs) is auto-approved.
For explicit review, wire a `ConnectorReviewQueue` that returns an approved decision:

```bash
curl -s -X POST http://localhost:8000/report-runs \
  -H 'Content-Type: application/json' \
  -d '{"area_id": "{area_id}", "intent_code": "homestead_feasibility"}'
```

Poll `GET /report-runs/{report_run_id}` until `"status": "succeeded"`.

> Note: this generic `POST /report-runs` example is a code-level integration pattern
> over an existing `{area_id}` plus whatever evidence is already ingested/reviewed.
> In default fixture mode it does not ingest the packaged selected-county corpus, so
> this generic curl path yields an evidence-poor dossier unless
> `ENABLE_LIVE_CONNECTORS=true` (network) or a DB-backed connector-run pre-ingests
> evidence. For the evidence-rich selected-county packaged path through the app
> surface, use `/operator-cases/{case_id}/report`; for no-server selected-county
> delivery, use the Operator Quickstart above.

### 4a. Approve the report run (required before dossier delivery)

The dossier endpoint enforces an approval gate. A reviewer with `report:approve` scope
must approve the completed report before `GET /report-runs/{report_run_id}/dossier` will serve it:

```bash
curl -s -X POST http://localhost:8000/report-runs/{report_run_id}/approve \
  -H 'Content-Type: application/json' \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123' \
  -d '{"reason": "fixture regression — approved for dossier delivery"}'
```

The response returns `"review_status": "approved"`. Without this step, step 5 returns
`409 Conflict`.

### 5. Retrieve Markdown dossier

```python
from app.reports.dossier import build_rural_land_dossier
dossier = build_rural_land_dossier(report_run)
print(dossier)
```

The dossier always begins with a screening disclaimer and surfaces all unknowns,
verification tasks, and source citations. It never asserts legal access, buildability,
title status, or investment suitability.

### 6. Run fixture regression suite

```powershell
.\scripts\run_mvp_regression.ps1 -Force
# or:
$env:RUN_DB_SMOKE = '1'
cd backend
PYTHONPATH=. python -m pytest tests/private_mvp/test_mvp_regression.py -v
```

All three county tests (Buncombe, Chatham, Brunswick) must pass.

### Known limitations for fixture regression

| Domain | Status | Reason |
|---|---|---|
| `flood` | fixture-backed | StaticFloodFixtureConnector; confirm with county flood-plain manager |
| `access` | fixture-backed | StaticAccessFixtureConnector; road presence does not prove legal access |
| `zoning` | fixture-backed / recorded-fixture source path | StaticZoningFixtureConnector in regression; DS-023 Chatham/Brunswick recorded-fixture connectors are reviewed separately and still require county Planning confirmation |
| `parcels` | fixture-backed across all 9 AOIs / selected-county live path | StaticParcelFixtureConnector in all regression cases; parcel PIN, county, acreage, and zoning designation populate in the dossier where the fixture carries those fields. DS-010 live connectors are limited to selected-county operator flows and exclude owner/value/title fields |
| `assessor` | NOT_EVALUATED sentinel | No live assessor connector; DS-011 records explicit ASSESSOR_NOT_EVALUATED evidence and no owner/value/sale-history data is asserted |
| `terrain/slope` | fixture-backed / live source path | StaticTerrainFixtureConnector in Buncombe regression cases; DS-001 USGS TNM remains screening-only |
| `wetlands` | fixture-backed / live source path | StaticWetlandsFixtureConnector in Brunswick regression cases; DS-004 NWI remains screening-only and is not a jurisdictional determination |
| `soils` | fixture-backed | StaticSoilsFixtureConnector in Brunswick regression cases; not septic suitability |
| `buildability` | fixture-backed | StaticBuildabilityFixtureConnector records screening constraints only; not a buildability conclusion |
| Appraisal/value | never | Not provided — outside scope; use licensed appraiser |
| Legal access | never | Not asserted — road proximity only; confirm with title/surveyor |
