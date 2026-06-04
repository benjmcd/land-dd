# Lane D ADR 0002: Connector Entry Ownership

## Status

Proposed

## Context

Level 8 introduces fixture-first connectors. Connector work crosses existing lane boundaries:

- Lane A owns source registry, source datasets, dataset versions, retrieval runs, source licensing, and DB migrations.
- Lane B owns geometry validation and geometry fixtures.
- Lane C owns evidence payload validation, source-failure evidence, and claims.
- Lane D owns report/API surfacing.

`LANE_OWNERSHIP.md` does not currently assign `backend/app/connectors/`. It also states that `LANE_OWNERSHIP.md` updates are made by the human coordinator. Therefore this ADR is a decision packet for coordinator review, not a runtime implementation.

Current repo authority favors source retrieval runs for connector provenance:

- `SourceRetrievalRunContract` captures connector name, dataset version, status, timing, row/error/warning counts, log URI, and metrics.
- `source.ingest_runs` persists those fields and links evidence rows through `evidence.observations.ingest_run_id`.
- `jobs.job_queue` exists for async orchestration and retry scheduling, but is not source provenance.

## Decision

Before any Level 8 connector runtime code, create a coordinator-owned connector integration zone in `LANE_OWNERSHIP.md`.

Recommended ownership:

- `backend/app/connectors/`: coordinator-owned connector integration zone; write access only for a specifically assigned connector implementation pass.
- `backend/tests/connectors/`: same connector integration zone.
- `tests/fixtures/connectors/`: same connector integration zone for connector-specific fixture inputs and expected normalized outputs.
- `plans/connector-*.md` and `state/connector-state.md`: same connector integration zone if connector work becomes more than a one-pass handoff.

The connector integration zone may read public lane APIs and domain contracts but must not modify Lane A/B/C/D-owned implementation files. Cross-lane changes still stop and go through the owning lane.

Use source retrieval runs as the connector attempt lifecycle authority:

- First fixture connector tests should record or assert `SourceRetrievalRunContract` behavior.
- `source.ingest_runs` is the durable provenance table for connector attempts.
- `jobs.job_queue` is reserved for future asynchronous scheduling. If later introduced, a job record should reference the retrieval run or source dataset/version; it must not replace source retrieval provenance.

The first implementation slice should be assigned to a dedicated connector implementation pass after the ownership map is updated. It should use a static local flood fixture, no live network, and no vendor credentials.

## Alternatives Considered

Assign connectors to Lane A:

- Strong fit for source registry and retrieval-run persistence.
- Rejected as the general owner because connector output must align with Lane C evidence contracts and would pressure Lane A to own evidence ingestion semantics.

Assign connectors to Lane C:

- Strong fit for evidence output and source-failure behavior.
- Rejected as the general owner because source licensing, dataset versions, and retrieval-run persistence are Lane A-owned.

Assign connectors to Lane D:

- Strong fit for proving report/API surfacing.
- Rejected as the general owner because connectors sit before evidence and claims, and report/API ownership should not expand into source ingestion.

Use `jobs.job_queue` as connector lifecycle authority:

- Useful later for async scheduling and retries.
- Rejected for first Level 8 fixture work because source provenance already has a retrieval-run model/table and evidence rows link to source ingest runs.

## Consequences

- D-005 cannot be fully complete until `LANE_OWNERSHIP.md` is updated by the coordinator.
- First connector runtime code remains blocked until ownership and run lifecycle authority are canonical.
- The next connector pass can be isolated from Session 1 Lane A/C work and Session 2 Lane D work.
- Level 8 can prove fixture connector behavior without live network use, credentials, schema edits, or report/API broadening.
