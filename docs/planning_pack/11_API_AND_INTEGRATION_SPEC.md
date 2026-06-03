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

## 3. Endpoint groups

### Areas

- `POST /areas`
- `GET /areas/{area_id}`
- `GET /areas/{area_id}/features`
- `GET /areas/{area_id}/evidence`
- `GET /areas/{area_id}/claims`
- `GET /areas/{area_id}/reports`

### Sources

- `GET /sources`
- `POST /sources`
- `GET /sources/{source_id}`
- `GET /datasets/{dataset_id}/versions`
- `POST /ingest-runs`

### Reports

- `POST /reports`
- `GET /reports/{report_run_id}`
- `GET /reports/{report_run_id}/status`
- `GET /reports/{report_run_id}/sections`
- `GET /reports/{report_run_id}/assets`
- `GET /reports/{report_run_id}/machine-json`

### Review

- `POST /claims/{claim_id}/review-notes`
- `POST /verification-tasks/{id}/complete`
- `POST /reports/{report_run_id}/approve`
- `POST /reports/{report_run_id}/reject`

### Batch screening

- `POST /screening-jobs`
- `GET /screening-jobs/{job_id}`
- `GET /screening-jobs/{job_id}/results`

## 4. API requirements

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

## 5. Integration boundaries

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

## 6. OpenAPI draft

See `api/openapi_stub.yaml`.
