# ADR: Approved Connector Evidence Report Gate

Date: 2026-06-05

## Status

Accepted

## Context

The DS-002 FEMA NFHL connector persists spatial and source-failure evidence through the
evidence ledger, and reviewers can close connector review queue items with
`approve_for_connector_qa` or fix/cancel decisions. Before this decision, report
generation consumed all area evidence uniformly. Live connector evidence could therefore
influence report claims after persistence without durable proof that the connector run had
passed human review.

Postgres remains the system of record for evidence observations and connector review
queue state. Source retrieval runs remain connector provenance authority. The report layer
must not create a parallel connector approval store or infer approval from source registry
review alone.

## Decision

Add optional `source_ingest_run_id` lineage to `EvidenceContract` and persist it in the
existing evidence metadata JSON. Connector-produced evidence, including source-failure
evidence, must set this value to the connector run's `ingest_run_id`.

Report generation will include connector-lineage evidence only when the connector review
queue has a matching item whose status is `SUCCEEDED` and whose latest
`review_decision.action` is `approve_for_connector_qa`. Evidence without connector
lineage continues to behave as before.

No DB migration is added for this slice because the evidence table already stores
contract metadata as JSON and the report layer only needs a UUID lookup key. A future
dedicated evidence-to-retrieval-run foreign key can replace or supplement this metadata
field if connector evidence volume or query patterns require it.

## Consequences

- Live connector evidence is fail-closed for reports until explicit review approval is
  present.
- Source-failure evidence from a connector run is also gated by the same approval rule,
  preventing unreviewed live-source failures from silently becoming report unknowns.
- Existing fixture/manual evidence without `source_ingest_run_id` remains report-eligible.
- The connector review queue is the current approval authority for report eligibility, but
  it is still not a durable reviewer action-history ledger.
- The generated OpenAPI planning-pack stub and evidence schema include
  `source_ingest_run_id`.

## Verification

- Focused report tests cover exclusion of unapproved connector evidence and inclusion of
  approved connector evidence.
- FEMA connector tests cover lineage stamping for successful spatial evidence and
  source-failure evidence.
- Evidence repository tests cover metadata round-trip of `source_ingest_run_id`.
