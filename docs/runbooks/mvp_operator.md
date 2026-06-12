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
| `DATABASE_URL` | _(none)_ | Postgres connection string; omit for in-memory mode |
| `USE_DB_SERVICES` | `false` | Use Postgres-backed services instead of in-memory stores |
| `OBJECT_STORE_ROOT` | `./object_store` | Directory for report artifact files |
| `REVIEWER_ACCOUNTS` | local fixture reviewer | Reviewer service account ids and tokens |
| `REVIEWER_ACCOUNT_SCOPES` | local fixture scopes | Explicit reviewer scopes such as `connector:run`, `connector:review`, `operations:read`, `report:approve`, `report:retry`, and `report:run` |
| `ENABLE_LIVE_CONNECTORS` | `false` | Enables request-time DS-001, DS-002, DS-004, then DS-003 connector gating |

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
{"report_run_id": "<uuid>", "area_id": "<uuid>", "status": "queued"}
```

**Step 2 — Poll until complete:**

```bash
curl -s http://localhost:8000/report-runs/<report_run_id>
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
  -d '{"area_id": "<uuid>", "intent_code": "rural_land_purchase"}'
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
report. The signed-token path still returns `201 Created` with a full
`ReportRunContract` on the first request and `200 OK` with the same contract on replay.
The unauthenticated operator path returns `202 Accepted` on first queueing and `200 OK`
with the same queued job on replay.

### Approve a report run

The final Markdown dossier (`GET /report-runs/{id}/dossier`) and the machine-readable
artifact (`GET /report-runs/{id}/artifact`) are both gated on approval status. A report
that has not been approved returns `409 Conflict`.

**Via the web UI:** navigate to the report page (`/ui/report-runs/{id}`). When the report
has succeeded but is not yet approved, an approval form is shown. Enter the reviewer ID
and token (scope: `report:approve`) and submit. The authenticated reviewer identity is
recorded in the immutable `review_actions` audit log — credentials are required and
validated on every submission.

**Via the API:** approve using reviewer headers on a reviewer account that holds the
`report:approve` scope:

```bash
curl -s -X POST http://localhost:8000/report-runs/<report_run_id>/approve \
  -H 'Content-Type: application/json' \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123' \
  -d '{"reason": "Screened and verified — approved for delivery"}'
```

The `reason` field is optional. The response returns the updated `ReportRunContract` with
`"review_status": "approved"` and the approval action recorded in `review_actions`. Once
approved, `GET /report-runs/{id}/dossier` returns the full Markdown dossier.

Approval is idempotent: a second `POST /approve` on an already-approved report returns
the current contract unchanged.

### Retry a failed report job

Report retry routes require reviewer headers:

```bash
X-Reviewer-Id: fixture-reviewer
X-Reviewer-Token: fixture-token-123
```

If `GET /report-runs/<report_run_id>` returns `status="failed"`, create a new report job
from the failed job's stored area and intent:

```bash
curl -s -X POST http://localhost:8000/report-runs/<report_run_id>/retry \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123'
```

The failed job is preserved. The response returns a new `report_run_id` plus
`retry_of_report_run_id` pointing at the failed job.

### Reviewed live connector queue scheduling

Connector scheduling routes require reviewer headers:

```bash
X-Reviewer-Id: fixture-reviewer
X-Reviewer-Token: fixture-token-123
```

To enqueue the current reviewed live-source sequence for an already registered area:

```bash
curl -s -X POST http://localhost:8000/connector-runs/live-sequence/schedule-bbox \
  -H 'Content-Type: application/json' \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123' \
  -d '{
    "area_id": "<uuid>",
    "bbox": {"xmin": -77.10, "ymin": 38.80, "xmax": -77.00, "ymax": 38.90},
    "max_sample_points": 2,
    "max_features": 1,
    "max_rows": 1
  }'
```

The response returns `policy_id="reviewed_live_sequence_ds001_ds002_ds004_ds003_v1"` and
four durable live connector jobs in order: DS-001, DS-002, DS-004, DS-003. Scheduling does
not call live sources, persist evidence, approve review, or create reports. Run
`py -3.12 .\scripts\live_connector_worker.py --max-jobs 1 --json` to process queued jobs
one at a time; report creation remains separate and requires connector review approval.

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

---

## Local Dossier Generation (no server required)

Generate a Markdown dossier directly from a GeoJSON AOI file using fixture connectors.
No database, no API server, and no approval step required.

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

When `REQUIRE_API_KEY=true` is set, the API-key middleware applies to **every route**,
including all `/ui/*` pages and file-download endpoints. The only public exceptions are
`/health` and `/version`. This is intentional fail-closed behaviour: setting
`REQUIRE_API_KEY=true` without a valid `X-API-Key` header will lock the entire operator
UI, not just the JSON API. The operator web UI targets the default private trusted-network
posture (`REQUIRE_API_KEY=false`). Do not set `REQUIRE_API_KEY=true` in environments
where operators need browser access unless the deployment provides header injection or a
reverse-proxy that adds the key for trusted internal clients.

Reviewer tokens for UI operations are separate from API keys. Configure them via
`REVIEWER_ACCOUNTS` and `REVIEWER_ACCOUNT_SCOPES` (see the Configuration table above and
`.env.example`).

### Home page and intake

Open `http://localhost:8000/ui/` in a browser. Submit a GeoJSON polygon and select an
intent. The page submits to `/intake` and then either:

- Redirects to the report status page (`/ui/report-runs/{id}`), which auto-refreshes
  while the report is generating; or
- Shows a yellow banner with a link to the **Connector Review Queue** if the intake
  response returns `status=pending_connector_review` (no report job exists yet at that
  point — the link goes directly to the queue item).

### Report list (`/ui/report-runs`)

The report list shows up to 30 runs per page with a status filter dropdown and
previous/next pagination links. The status filter accepts: `queued`, `running`,
`succeeded`, `failed`. Each succeeded row displays its review badge (`approved` in green
or `pending` in amber). Failed rows link to the individual report page where a retry form
is available.

A **Compare** affordance lets operators select 2–4 report runs using the checkboxes and
open a side-by-side summary at `/ui/compare?ids=<uuid>,<uuid>[,...]`. The compare view
shows summary counts only (claims, unknowns, red flags, verification tasks). Report
content is gated on approval status.

Programmatic access: `GET /report-runs?status=<value>&limit=<n>&offset=<n>` (max limit
100) returns a JSON list of report run summaries.

### Report page (`/ui/report-runs/{id}`)

- **Queued or running:** the page auto-refreshes every 3 seconds.
- **Failed:** shows the error message and a retry form (see below).
- **Succeeded, not yet approved:** shows the approval form (see below).
- **Approved:** shows the rendered dossier with nav links:
  - **Download dossier (.md):** `GET /report-runs/{id}/dossier?download=1` — serves the
    Markdown dossier as an attachment; approved-only (returns `409` if not approved,
    `202` if still running, `404` if not found).
  - **Download report (.json):** `GET /report-runs/{id}/artifact` — serves the
    machine-readable report JSON as an attachment; approved-only with identical gating.
    In DB-backed mode the persisted artifact file is served; in-memory mode the contract
    is serialised at request time.
  - **Print / Export PDF:** `/ui/report-runs/{id}/print` — print-optimised HTML page;
    approved-only.
  - **View evidence lineage:** see below.

### Approving a report run via the UI

The report page for a succeeded-but-unapproved run shows an approval form. The form
requires **Reviewer ID** and **Reviewer token** fields (scope: `report:approve`). There
is no session or cookie: credentials are validated per-action from the form body.
On success the page redirects back to the report view. On credential failure the
response carries the real HTTP status (401/403/503) and a generic error message — no
field-level detail is leaked.

The default fixture account (`fixture-reviewer` / `fixture-token-123`) does **not** hold
`report:approve` scope in `.env.example`. Grant it explicitly via
`REVIEWER_ACCOUNT_SCOPES` before using the UI approval form in development:

```
REVIEWER_ACCOUNT_SCOPES=fixture-reviewer:connector:run|connector:review|operations:read|report:approve|report:retry|report:run
```

API-based approval (unchanged) sends credentials as headers:

```bash
curl -s -X POST http://localhost:8000/report-runs/<report_run_id>/approve \
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
connector, status, attempts, created.

**Item detail** (`/ui/connector-review-queue/{ingest_run_id}`): shows payload summary,
quality issues (blocking issues highlighted in red), and attempts/lock/timing metadata.

Action forms — all require **Reviewer ID** and **Reviewer token** with scope
`connector:review`:

| Action | When to use | Reason field |
|---|---|---|
| **Approve for QA** | Data quality passes review | Optional |
| **Request Fix (Reject)** | Data quality blocks use | Required |
| **Requeue After Fix** | Underlying fixture/data has been corrected | Required |
| **Cancel** | No further action needed | Required |

After a queue item reaches `succeeded` status (approved), a **Resume Report Run** form
appears. This form requires **Reviewer ID** and **Reviewer token** with scope
`report:run`, and an intent selection. Submitting it creates a new report run for the
area associated with the approved connector run and redirects to the report page.

### Operations dashboard (`/ui/operations`)

Navigate to `/ui/operations`. Enter **Reviewer ID** and **Reviewer token** (scope:
`operations:read`) and submit the form. The page renders queue-health tables for report
jobs and live connector jobs (total, queued, running, succeeded, failed, cancelled, needs
review, oldest queued age). The dashboard is read-only; it does not lease work, retry
jobs, or call live sources.

Equivalent API call:

```bash
curl -s http://localhost:8000/operations/queue-health \
  -H 'X-Reviewer-Id: fixture-reviewer' \
  -H 'X-Reviewer-Token: fixture-token-123'
```

### Evidence lineage (`/ui/report-runs/{id}/lineage`)

Linked from approved report pages as **View evidence lineage**. Renders three tables:

- **Sources → Ingest Runs** — each data source and the ingest run chain that produced
  its evidence.
- **Claims → Evidence** — each claim and the evidence record IDs that support it.
- **Evidence → Claims** — each evidence record, its source, and the claims that cite it.
  `UNKNOWN` evidence (no data) is highlighted amber; `SOURCE_FAILURE` evidence is
  highlighted red.

The lineage page applies the same access gating as the lineage API
(`GET /report-runs/{id}/lineage`).

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

The access-control proof is validate-only. It checks the current default-off API-key
middleware, local scoped reviewer service-account auth, reviewer-authenticated and
scoped operator routes, intentionally public `/health` and `/version` routes, CI proof
wiring, configured static API-key lifecycle support, structured API-key auth runtime
logs, and explicit production auth blockers. It does not add user accounts, OAuth/OIDC,
full user RBAC, automatic key rotation, or hosted identity-provider integration.

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
| In-memory job store | Job status is lost on server restart; pending jobs cannot be recovered |
| Live connectors are bounded and review-gated | Reviewed Must-priority paths now include DS-001, DS-002, DS-003, and DS-004 public-source connectors, DS-010 selected-county parcel connectors, the DS-011 assessor NOT_EVALUATED sentinel, and DS-023 Chatham/Brunswick recorded-fixture zoning. Outputs remain screening-only and cannot assert legal/buildability/title/water/wetland jurisdiction conclusions. |
| County/vendor coverage is intentionally scoped | DS-010 parcel connectors are limited to Buncombe/Chatham/Brunswick selected-county operator flows; DS-011 assessor remains explicit NOT_EVALUATED evidence, not live assessor data; DS-017 commercial parcel vendor remains blocked; DS-023 covers Chatham/Brunswick recorded-fixture zoning only. Buncombe zoning and all other counties remain NOT_EVALUATED. |
| Single-process default | In-memory stores are not shared across multiple workers or processes |
| No full user auth/RBAC | API-key and scoped reviewer service-account gates exist, `API_KEY_SPECS` supports configured active/retired static key lifecycle entries, and API-key decisions emit structured runtime logs plus DB-backed `audit.events` rows in DB-service mode, but there are no user accounts, OAuth/OIDC, full user RBAC, hosted identity provider, automatic key rotation, hosted log retention, or user-bound audit semantics |
| `REQUIRE_API_KEY=true` locks the operator UI | When `REQUIRE_API_KEY=true` is set, the API-key middleware applies to every route including all `/ui/*` pages; only `/health` and `/version` remain public. The UI targets the default private trusted-network posture (`REQUIRE_API_KEY=false`). |
| UI reviewer auth is stateless per-action | The UI approval, retry, connector-review, and operations forms submit `reviewer_id` + `reviewer_token` in the form body on every action. There are no sessions or cookies. Tokens are validated via the same reviewer-auth service as API header tokens. |
| No persistence by default | In-memory repositories reset on restart; use DATABASE_URL for persistence |
| Repo-local alert rules only | Alert rules are validated as artifacts, but no hosted alert manager, dashboard, pager, or named on-call rotation exists |
| Supply-chain scan limits | CI runs Python dependency vulnerability scanning, validates and attests the repo-local production lock/SBOM, pins the backend base image by OCI index digest, scans the locally built backend image for critical/high CVEs, and validates the image-publication and hosted-deployment boundaries, but there is no hosted deployment or published-registry image attestation |
| Cost monitoring is local and zero-dollar attributed | Report cost metrics include local-only USD-cent attribution, but no hosted billing reconciliation or approved nonzero unit-cost thresholds exist yet |
| Release package is local | Local ZIP package creation exists under `local_artifacts/releases`, but there is no pushed registry image, hosted deployment, signed image SBOM, or published registry-image attestation yet |

---

## Troubleshooting

**422 on POST /intake**
- GeoJSON is malformed or the geometry type is unsupported (must be Polygon or MultiPolygon).
- `intent_code` must be exactly `rural_land_purchase` or `homestead_feasibility`.

**404 on GET /report-runs/{id}**
- The ID is unknown. If the server restarted after the job was created, the job record was lost.
  Submit a new intake request.

**Report stuck in `queued`**
- The server was restarted after the POST /intake but before the background task ran.
  The in-memory job store is gone. Submit a new intake request.

**`status: failed` in report response**
- Check `caveats` field in the response for the error message.
- Common causes: area not registered (should not occur via /intake), rule engine misconfiguration.

**UI approval form returns 401 or 403**
- Credentials are missing, wrong, or the reviewer account does not hold `report:approve` scope.
- Check `REVIEWER_ACCOUNTS` and `REVIEWER_ACCOUNT_SCOPES` in the server environment.
  The default fixture account in `.env.example` does not include `report:approve`; add it
  explicitly before testing UI approval in development.
- 503 means reviewer accounts are not configured at all.

**UI returns 401/403 on every page (locked out)**
- `REQUIRE_API_KEY=true` is set. The API-key middleware blocks all routes except `/health`
  and `/version`, including all `/ui/*` pages. Either disable `REQUIRE_API_KEY` for
  private-network operator use, or configure the reverse proxy to inject the
  `X-API-Key` header for trusted operator clients.

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
- `GET /report-runs/{id}/dossier?download=1` or `GET /report-runs/{id}/artifact` returns
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
  -d '{"area_id": "<uuid>", "intent_code": "homestead_feasibility"}'
```

Poll `GET /report-runs/<report_run_id>` until `"status": "succeeded"`.

### 4a. Approve the report run (required before dossier delivery)

The dossier endpoint enforces an approval gate. A reviewer with `report:approve` scope
must approve the completed report before `GET /report-runs/{id}/dossier` will serve it:

```bash
curl -s -X POST http://localhost:8000/report-runs/<report_run_id>/approve \
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
