# MVP Operator Runbook

## Overview

Land Diligence is a fixture-backed land due-diligence screening compiler for US rural land.
It evaluates flood, soil, and environmental data against a submitted area of interest and
returns a structured report of claims, unknowns, and verification tasks.

**Scope:** MVP is fixture-only. No live external data APIs are called. Single-process mode.
Supported intents: `rural_land_purchase`, `homestead_feasibility`.

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
| `OBJECT_STORE_ROOT` | `./object_store` | Directory for report artifact files |

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

## Known Limitations

| Limitation | Impact |
|---|---|
| In-memory job store | Job status is lost on server restart; pending jobs cannot be recovered |
| Fixture-only connectors | No live flood, soil, or parcel data; all evidence comes from static fixtures |
| Single-process | `AsyncReportJobStore` is not shared across multiple workers or processes |
| No authentication | All endpoints are unauthenticated; do not expose publicly without a proxy |
| No persistence by default | In-memory repositories reset on restart; use DATABASE_URL for persistence |

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
