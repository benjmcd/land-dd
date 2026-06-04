# ADR: Connector Source-Failure Evidence ID Adoption

Status: accepted

Date: 2026-06-04

## Context

Lane C TC-180 added public service support for preserving caller-supplied source-failure evidence IDs through `EvidenceService.create_source_failure(...)`. Before this connector pass, the connector evidence-ingestion adapter still treated source-failure evidence contracts as templates: it created source-failure records through the public Lane C method, but did not pass the connector-supplied `evidence_id`.

Connector fixture output is deterministic and already carries source-failure evidence IDs. Preserving those IDs at the connector adapter boundary makes fixture-backed source failures reproducible across the connector workflow and DB-backed public service wiring.

## Decision

Adopt Lane C's public source-failure ID preservation from the connector side:

- extend the connector evidence-ingestion port protocol to accept optional `evidence_id`;
- pass `EvidenceContract.evidence_id` into `create_source_failure(...)` for source-failure connector evidence;
- check existing stored source-failure fingerprints before deterministic-ID duplicate fallback, so idempotent source failures return stored authority when the failure was already persisted;
- update connector/API fake evidence ports and DB-backed public-wiring tests to preserve supplied source-failure IDs.

This slice does not edit Lane C service code, shared schemas, database migrations, live connector behavior, claim/rule logic, report semantics, API mutation routes, queue behavior, or durable `ingest_run_id` evidence-row linkage.

## Consequences

- Fixture-backed source-failure evidence now round-trips with deterministic evidence IDs through connector workflow and DB-backed public Lane C service wiring.
- Repeated source-failure fixture runs still prefer stored fingerprint authority before deterministic-ID fallback.
- The remaining durable lineage gap is explicit: evidence records still do not carry a durable `ingest_run_id` link, so source retrieval runs remain provenance/lifecycle authority and evidence linkage remains a future coordinated schema/service pass.
