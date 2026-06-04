# ADR Lane A 0001: Source provenance and license gates

## Status
Accepted

## Context

The product is evidence-led and Postgres/PostGIS-first. A source is not truth by itself; it is an input that needs authority, licensing, freshness, coverage, caveats, retrieval metadata, and production-use constraints before downstream evidence or claims can rely on it.

The MVP source registry currently seeds registry rows from `registers/data_source_registry.csv` into `SourceContract` objects. DB application and retrieval-run behavior remain blocked until Docker/PostGIS smoke can run, so this ADR defines the governance model that source code and future DB behavior must preserve.

## Decision

Use the source registry as the mandatory authority for any non-human-note evidence source.

Every production source must have:

- a registered source identity and authority level;
- explicit commercial-use, cache, export, raw-data, and AI-use statuses;
- license summary and review status, including `unknown` or `blocked` when unresolved;
- attribution requirement and reportable attribution text when required;
- geographic scope, update cadence or freshness class, and source caveats;
- source version or source-date metadata when available;
- retrieval metadata and failure status for connector/runtime attempts;
- fixture coverage before any live connector is enabled.

Repository field mapping:

- `jurisdiction` is represented as `geographic_scope`;
- `source_url_or_reference` is represented as `homepage_url` plus metadata `raw_url`;
- `ai_use_status` is represented as `ai_use_allowed`;
- `source_type`, `license_status`, `redistribution_status`, `freshness_class`, `last_checked_at`, `review_owner`, and `review_status` are preserved in source metadata until a later migration promotes them to first-class columns.

Unknown or incompatible rights fail closed. A source with unknown, blocked, or incompatible terms may be used for fixture-only development and review, but must not feed production reports, user exports, or live connector output until a license review records an allowed/restricted decision.

`templates/data_source_license_review.md` is the canonical human review worksheet for TA-050. Lane A intentionally does not create a second near-duplicate license template; future references to `source_license_review` should use this root template unless the plan is explicitly revised.

Connector retrieval attempts may hand Lane A a complete `SourceRetrievalRunContract` when the connector owns deterministic attempt identity. The public `SourceProvenanceService.record_retrieval_run_contract(...)` method records that supplied contract after validating the referenced dataset version and preserving the supplied `ingest_run_id`. Connector code must call this through the public service surface and must not import Lane A repositories directly.

## Consequences

- Evidence creation must reject unregistered source IDs except controlled human-note evidence types.
- Future `SourceExistsProtocol.source_production_use_allowed` behavior must check review status and usage constraints, not only row existence.
- Source-failure and blocked-source outcomes must create explicit evidence or run-state records; missing data must never become "no issue found."
- Fixture connector workflows can preserve deterministic retrieval-run identity through the public provenance service before evidence ingestion.
- Live connectors remain blocked until the source registry row, license review, fixture tests, failure behavior, and output caveats are all present.
- DB smoke remains a separate prerequisite for claiming Level 2 or durable Level 3 completion.

## Links

- `MILESTONE_MAP.md` Level 3
- `docs/DATA_SOURCE_STRATEGY.md`
- `registers/data_source_registry.csv`
- `schemas/source_schema.json`
- `templates/data_source_license_review.md`
