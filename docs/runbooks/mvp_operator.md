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

### Approve a report run

The final Markdown dossier (`GET /report-runs/{id}/dossier`) is gated on approval status.
A report that has not been approved returns `409 Conflict`. Approve a completed report run
using a reviewer account that holds the `report:approve` scope:

```bash
X-Reviewer-Id: fixture-reviewer
X-Reviewer-Token: fixture-token-123
```

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

`--connector all` runs flood, access, and zoning in sequence. Missing fixtures for a
given AOI are warned and skipped — the dossier is still produced from whichever
connectors succeeded. Evidence from each connector is auto-approved for connector QA
when the quality profile is `READY_FOR_CONNECTOR_QA`.

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

Open `http://localhost:8000/ui/` in a browser. Submit a GeoJSON polygon and select an intent.
The page links to the report status page, which auto-refreshes while the report is generating.

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
| Live connectors are bounded and review-gated | Reviewed DS-001, DS-002, DS-003, and DS-004 public-source connectors are available, but outputs remain screening-only and cannot assert legal/buildability/title/water/wetland jurisdiction conclusions |
| County/vendor sources not ready | Parcel, assessor, commercial parcel, and local zoning sources still require jurisdiction/vendor/license decisions before production connector use |
| Single-process default | In-memory stores are not shared across multiple workers or processes |
| No full user auth/RBAC | API-key and scoped reviewer service-account gates exist, `API_KEY_SPECS` supports configured active/retired static key lifecycle entries, and API-key decisions emit structured runtime logs plus DB-backed `audit.events` rows in DB-service mode, but there are no user accounts, OAuth/OIDC, full user RBAC, hosted identity provider, automatic key rotation, hosted log retention, or user-bound audit semantics |
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

### Geography and scope

- **Counties:** Buncombe, Chatham, Brunswick (NC)
- **Intent:** `homestead_feasibility` / `rural_land_purchase`
- **Connector domains:** `flood` (StaticFloodFixtureConnector), `access`
  (StaticAccessFixtureConnector), `zoning` (StaticZoningFixtureConnector)
- **NOT_EVALUATED domains:** `parcels`, `assessor` — recorded as explicit unknowns;
  no cadastral or tax data is asserted

### 1. DB startup (optional — in-memory is sufficient for fixture regression)

For full DB-backed mode, start Postgres and apply migrations:

```powershell
docker compose up -d db
.\scripts\db_apply_migrations.ps1
```

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

Repeat for access (`StaticAccessFixtureConnector` + `evaluate_access_fixture_quality`)
and zoning (`StaticZoningFixtureConnector` + `evaluate_zoning_fixture_quality`) as
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
| `access` | fixture-backed | StaticAccessFixtureConnector; road presence ≠ legal access |
| `zoning` | fixture-backed | StaticZoningFixtureConnector; requires county planning confirmation |
| `parcels` | NOT_EVALUATED | No machine-queryable county parcel connector; recorded as unknown |
| `assessor` | NOT_EVALUATED | No machine-queryable assessor connector; recorded as unknown |
| `terrain/slope` | live-connector only | DS-001 USGS TNM; not included in fixture regression |
| `wetlands` | live-connector only | DS-004 NWI; not included in fixture regression |
| Appraisal/value | never | Not provided — outside scope; use licensed appraiser |
| Legal access | never | Not asserted — road proximity only; confirm with title/surveyor |
