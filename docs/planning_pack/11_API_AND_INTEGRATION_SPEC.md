# 11 API and Integration Spec

Generated: 2026-05-28

## 1. API principle

The API should expose stored resources and report runs. It should not allow clients to create untraceable claims or recompute authoritative logic outside the evidence/rules system.

## 2. Resource model

Primary resources:
- workspace
- user
- source
- dataset
- dataset_version
- area
- evidence
- claim
- verification_task
- rule_set
- report_run
- job

## 3. Current implemented endpoint groups

The current local API authority is the FastAPI app in `backend/app/main.py`.
`api/openapi_stub.yaml` is generated from `create_app().openapi()` and is
guarded by `backend/tests/test_planning_pack_schema_copies.py`.

### Areas

- `POST /areas`
- `GET /areas`

### Sources

- `GET /sources`
- `POST /sources`

### Evidence

- `GET /evidence`

### Reports

- `POST /report-runs`
- `GET /report-runs/{report_run_id}`

### Connector review status

- `GET /connector-runs/{ingest_run_id}/review-status`
- `GET /connector-runs/{ingest_run_id}/review-queue`

Both review-read routes require `X-Workspace-Id` and `X-User-Id`. They resolve the
review queue row inside the caller workspace and return 404 for unknown or
cross-workspace ingest runs.

### Health/version

- `GET /health`
- `GET /version`

## 4. Future endpoint groups not yet implemented

These groups remain product/API roadmap items, not active API claims:

- area features, area evidence-by-path, area claims-by-path, and area report lists;
- source detail, dataset versions, and ingest-run creation;
- report status, sections, assets, machine JSON, approve, and reject routes;
- claim review-note and verification-task mutation routes;
- batch screening jobs and result retrieval.

## 5. API requirements

1. All mutating calls require workspace context.
2. All report calls return source/run metadata.
3. All exported data passes entitlement checks.
4. API responses distinguish missing, unknown, failed, and false.
5. Geometry inputs must be validated server-side.
6. Report creation is async.
7. Idempotency keys required for report creation and batch jobs.
8. Pagination required for evidence/claims lists.
9. API returns stable IDs for all evidence and claims.
10. API has explicit versioning.

## 6. Integration boundaries

External systems:
- parcel vendors
- public data portals
- geocoders
- map/tile services
- LLM/document extraction providers
- billing
- email/notification
- CRM/support
- data warehouse later

Internal events:
- `source.version_published`
- `area.created`
- `feature_extraction.completed`
- `evidence.created`
- `rules.completed`
- `report.completed`
- `report.needs_review`
- `report.approved`
- `source.failure_recorded`

## 7. OpenAPI draft

See `api/openapi_stub.yaml`. It is a generated current-reference file for the
local FastAPI app, not a broader product-roadmap contract.
