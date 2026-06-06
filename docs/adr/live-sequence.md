# ADR: Live Connector Sequence Scheduler

Date: 2026-06-05

## Status

Accepted

## Context

The API already exposes one reviewer-authenticated scheduler route per reviewed live
connector: DS-001 USGS TNM EPQS, DS-002 FEMA NFHL, DS-004 NWI, and DS-003 SSURGO. Each
route enqueues bounded `live_connector_run` jobs without fetching the live source,
persisting evidence, approving connector review, or creating reports.

For production operation, a reviewer/operator should not need to make four separate
schedule calls when the intended policy is the current default-off request-time sequence:
DS-001, then DS-002, then DS-004, then DS-003. The durable worker and connector review
gate already provide the execution and approval boundaries.

## Decision

Add a reviewer-authenticated batch scheduler route:
`POST /connector-runs/live-sequence/schedule-bbox`.

The route validates a registered area and one bounded EPSG:4326 bbox, then enqueues the
current reviewed live-source sequence as separate durable jobs in this order:

1. DS-001 USGS TNM EPQS
2. DS-002 FEMA NFHL
3. DS-004 NWI
4. DS-003 SSURGO

The response returns the policy id and the ordered live job records. The route reuses the
existing per-source enqueue methods and idempotency keys. It does not fetch any live
source, persist evidence, approve review queue items, schedule reports, or bypass
`approve_for_connector_qa`.

## Consequences

- Operators can schedule the full reviewed live-source queue for an area with one API
  call while retaining one review gate per connector run.
- The worker remains the execution boundary and continues dispatching by
  `source_registry_id`.
- Report creation remains separate and review-gated.
- This does not decide future source-specific cadence, retries, requeue policy, or county
  source-rights blockers.

## Verification

- API tests cover auth, area validation, ordered DS-001/DS-002/DS-004/DS-003 job
  creation, idempotency, and no live-fetch/evidence/report side effects at schedule time.
- OpenAPI parity remains generated from `create_app().openapi()`.
