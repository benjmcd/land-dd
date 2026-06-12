# Source Readiness Closure Plan

## Purpose

Close source-readiness gaps without overclaiming production readiness. This plan now starts from the current audited state: DS-001, DS-002, DS-003, DS-004, DS-010, DS-011, and DS-023 are Must-priority connector-ready; DS-017 remains the only Must-priority blocker. Across all priorities, the current source-readiness check reports 16/25 connector-ready, including DS-007 BLM MLRS for bounded active federal mining-claim context only, DS-008 USGS MRDS for bounded historical mineral-occurrence screening only, DS-015 NC Geological Survey for bounded 1985 geologic map-unit context only, and DS-022 Census TIGER/ACS for bounded TIGERweb tract/block-group geography context only.

## Current facts

- Must-priority source readiness is `sources=8 ready=7 blocked=1`; DS-017 Commercial parcel vendor remains blocked by vendor/license selection and is not required for the private MVP unless product scope changes.
- All-priority source readiness is `sources=25 ready=16 blocked=9`; DS-007 BLM MLRS is connector-ready only for bounded active federal mining-claim context. It does not determine private mineral rights, claim-boundary precision, title status, mine hazards, resource value, extraction feasibility, environmental liability, buildability, appraisal, lending suitability, insurance, or investment suitability.
- DS-008 USGS MRDS is connector-ready only for bounded historical mineral-occurrence context. It does not determine mineral rights, mine hazards, resource value, extraction feasibility, environmental liability, buildability, appraisal, lending suitability, insurance, or investment suitability.
- DS-015 NC Geological Survey is connector-ready only for bounded NCGS 1985 statewide geologic map-unit context. It does not determine landslide/sinkhole/radon hazards, mineral resources or rights, engineering/geotechnical suitability, buildability, appraisal, lending suitability, insurance, or investment suitability.
- DS-022 Census TIGER/ACS is connector-ready only for administrative TIGERweb geography context. ACS demographic variables, protected-class analytics, neighborhood desirability, market/investment/lending suitability, and residential steering remain excluded.
- DS-011 County assessor is connector-ready only as an explicit `AssessorNotEvaluatedConnector`: it records ASSESSOR_NOT_EVALUATED source-failure evidence for every area. It does not query live assessor portals or expose owner/value/sale-history fields.
- DS-023 Local zoning ordinance PDFs is connector-ready through recorded-fixture zoning district connectors for reviewed county UDO tables. It does not claim live PDF retrieval, autonomous amendment tracking, final legal zoning interpretation, or raw PDF redistribution.
- DS-020 NOAA NWS climate/weather is connector-ready through the bounded point/zone API connector. It provides administrative forecast-zone context only, not climate normals, frost dates, growing-season length, or agricultural risk conclusions.
- DB-enabled verification passed on Docker PostGIS against fresh verification database `land_diligence_verify_20260611091900` with `RUN_DB_SMOKE=1`, `DATABASE_URL_SYNC`, and `DATABASE_URL` set to the same runtime. The DB smoke check now validates all 25 canonical source-registry IDs are present exactly once; the full-suite final smoke saw 25 seeded registry rows and 26 total source rows after DB tests created the unsupported-screening test source.

## Immediate pass

1. Land interrupted tail fixes.
   - Keep OSM road-access evidence as `SPATIAL_INTERSECTION`.
   - Ensure no-road OSM evidence is ledger-valid by omitting unknown `road_distance_m` while preserving `no_public_road_adjacency=true` and `road_count=0`.
   - Include NOAA and OSM API tests in the tracked test surface.

2. Reconcile release-readiness proof with current source readiness.
   - Update release-readiness scripts and runbook from Must `ready=6 blocked=2` to `ready=7 blocked=1`.
   - Ensure DS-017 is the only current Must blocker.
   - Run the release-readiness proof script and focused tests.

3. Clean state drift.
   - Update `state/PROJECT_STATE.md` so active plan, current counts, DS-011/DS-017/DS-020/DS-022 status, and next task match live repo output.
   - Update `state/VALIDATION_LOG.md` with fresh commands, results, and residual risks.
   - Keep older historical log entries as history, but make the top/current state unambiguous.

4. Close 2026-06-12 source-authority drift.
   - Align DS-010 registry, SQL seed, source review, and operator runbook text with the current Buncombe/Chatham/Brunswick selected-county connector-ready state.
   - Align DS-023 registry, SQL seed, source review, and operator runbook text with the current Chatham/Brunswick recorded-fixture zoning scope while keeping Buncombe zoning and live PDF ingestion out of scope.
   - Add focused regression checks that reject stale Must-readiness and selected-county claims in the canonical registry/review/runbook artifacts.

5. Add aggregate connector-scope readiness metadata.
   - Preserve the current source-level ready/blocked counts and existing `connector_implemented`, `connector_surfaces`, and `connector_ready` semantics.
   - Add source-readiness output fields that list every implemented connector and every explicit scope note for a source, so DS-010 and DS-023 no longer depend on a single primary connector entry to explain selected-county readiness.
   - Keep this slice read-only with respect to database schema, public API routes, report semantics, connector execution, and source-review/license decisions.

6. Promote aggregate scope metadata into the private-MVP gate.
   - Extend `scripts/private_mvp_readiness_check.py` so the selected-county private-MVP validator requires DS-010 and DS-023 aggregate connector names and scope notes in Must source-readiness JSON.
   - Keep this validate-only: it must not seed data, write artifacts, execute connectors, or weaken DS-017/full-release blockers.

7. Close private-MVP readiness catalog drift.
   - Align `config/private_mvp_beta_readiness.yaml` with the current selected-county regression and utility-closure proof surfaces.
   - Require current DS-010/DS-011/DS-023 selected-county scope phrases and reject stale catalog phrases in the private-MVP validator and tests.
   - Preserve the separation between fixture regression, selected-county connector utility, DB smoke, DS-017, and hosted-production blockers.

8. Promote selected-county scope from prose to structured catalog data.
   - Add a structured `selected_county_source_scope` section to `config/private_mvp_beta_readiness.yaml` for DS-010, DS-011, and DS-023.
   - Validate connector names, required source-readiness surfaces, and scope-note fragments from the structured catalog instead of hardcoding the selected-county scope only in the validator.
   - Keep stale-prose deny-list checks as a guardrail, but do not use exact current prose as the primary proof of source-scope truth.

9. Align selected-county source manifests with structured scope.
   - Update Buncombe/Chatham/Brunswick source manifests so DS-010, DS-011, and DS-023 language matches the structured private-MVP source scope and current source-readiness output.
   - Add private-MVP validator/test coverage that rejects stale manifest phrases such as no machine-queryable parcel/assessor path and “not available through the data pipeline” where current selected-county scope is more precise.
   - Keep this docs/validation-only: no source-readiness count changes, connector execution changes, API changes, report semantics changes, DB schema changes, or DS-017/hosted-production changes.

10. Promote selected-county manifest expectations into structured catalog data.
   - Add a structured `selected_county_manifest_scope` section to `config/private_mvp_beta_readiness.yaml` for Buncombe, Chatham, and Brunswick manifest paths, required DS-010/DS-011/DS-023 fragments, and shared stale-fragment denials.
   - Change `scripts/private_mvp_readiness_check.py` so county source-manifest validation is driven by that catalog data rather than hardcoded Python phrase maps.
   - Keep this validate-only and docs/catalog-only: no source-readiness count changes, connector execution changes, API changes, report semantics changes, DB schema changes, or DS-017/hosted-production changes.

## Mid-term pass

1. Select the next non-Must source-readiness candidate from live registry evidence.
   - DS-007 BLM MLRS is complete for active federal mining-claim geospatial context only.
   - DS-008 USGS MRDS is complete for historical mineral-occurrence screening only.
   - DS-022 Census TIGER/ACS is complete for TIGERweb geography context only.
   - DS-015 NC Geological Survey is complete for NCGS 1985 geologic map-unit context only.
   - Re-select the next non-Must source from current registry evidence; do not assume DS-014, DS-024, or DS-025 is unblocked without a fresh source review and connector proof.
   - Prioritize remaining public/government sources only after source authority, field policy, cache/export behavior, attribution, caveats, connector inventory, and connector/API tests are scoped.
   - Do not promote source readiness from source-review prose alone; require connector proof and source-readiness test updates.

2. Re-run DB-backed verification where prerequisites exist.
   - Completed on 2026-06-11 against Docker PostGIS on port 55432 using fresh database `land_diligence_verify_20260611091900`.
   - Keep this as a repeatable handoff gate after future DB/schema/seed changes; do not treat default verification with skipped DB smoke as equivalent proof.
   - Record pass/fail evidence without treating skipped DB smoke as a pass.

3. Preserve current source caveats through report surfaces.
   - Ensure every new connector evidence row has provenance, source version/date when available, retrieval metadata, caveats, and confidence.
   - Keep legal access, buildability, title, water rights, wetlands jurisdiction, appraisal, lending, insurance, and investment conclusions out of reports.

## Long-term path

1. Source expansion.
   - Promote additional counties and sources only after county/source-specific review, connector proof, and source-readiness test updates.
   - Revisit DS-017 only after vendor, license, cost model, field policy, and product need are selected.

2. Production hardening.
   - Close hosted production gates separately from private-MVP proof: hosted auth/RBAC, secret-manager integration, key rotation, hosted log retention, billing reconciliation, published image attestation, deployment proof, hosted alerting, and operational recovery drills.
   - Use `scripts/run_private_mvp_readiness_check.ps1` for the selected NC county private-MVP beta boundary; it must keep DS-017 blocked for full release readiness while confirming DS-017 and hosted-production gates do not block the private-MVP utility proof.
   - Every validate-only action must fail closed on missing runtime and must not seed or generate artifacts.

3. Product completeness.
   - Keep the backend evidence-ledger-first and Postgres/PostGIS-first.
   - Add UI, batch workflows, and summaries only after evidence, claims, report reproducibility, API, and operator review surfaces remain stable under verification.

## Non-goals

- Do not expose owner/value/sale-history data from assessor portals without a reviewed field policy.
- Do not treat DS-011 `AssessorNotEvaluatedConnector` as live assessor data.
- Do not treat DS-023 recorded-fixture zoning as live PDF retrieval or legal zoning advice.
- Do not mark DS-017 ready without explicit vendor/license approval.
- Do not claim hosted-production or DB-backed readiness from default local verification.

## Acceptance criteria

- OSM and NOAA connector/API tests pass and are part of the repo test surface.
- Release-readiness scripts, runbook, source-readiness tests, and source-readiness CLI agree on Must `sources=8 ready=7 blocked=1`, and release-readiness proof requires CI `db-verify` to set both `DATABASE_URL_SYNC` and `DATABASE_URL` when DB smoke is enabled.
- `state/PROJECT_STATE.md` and `state/VALIDATION_LOG.md` clearly identify DS-017 as the only Must blocker, DS-007 as connector-ready for active federal mining-claim context only, DS-015 as connector-ready for NCGS 1985 geologic map-unit context only, DS-008 as connector-ready for historical mineral-occurrence context only, DS-022 as connector-ready for TIGERweb geography context only, and DB smoke as skipped unless `RUN_DB_SMOKE=1` prerequisites are present.
- Focused connector/API/source-readiness/release-readiness checks pass.
- `git diff --check` passes.
- Default `.\scripts\verify.ps1` passes, or any failure is recorded with a specific blocker.

## Decision log

- 2026-06-12: Treat `registers/data_source_registry.csv` as the canonical usage-rights metadata authority, with `db/seeds/002_seed_source_registry.sql` as the seed mirror and source-review/runbook prose as derived operator-facing documentation. This pass is limited to source-authority alignment and tests; it does not change schema, API contracts, connector behavior, source-readiness semantics, report semantics, or production-readiness claims.
- 2026-06-12: Source-readiness remains source-level for pass/fail counts, but connector inventory must now expose aggregate connector names and scope notes for multi-county sources. This is the narrowest next step toward non-fragile county/source alignment without creating a new registry schema or changing connector runtime behavior.
- 2026-06-12: The private-MVP readiness gate should enforce aggregate DS-010/DS-023 connector scope metadata because that is the operator-facing proof boundary for selected-county truthfulness. Pytest-only coverage is useful but too indirect for handoff/validation workflows.
- 2026-06-12: The private-MVP readiness catalog is an operator-facing authority surface, not just a passive manifest. It must be guarded against stale DS-010/DS-011/DS-023 scope prose the same way runbook and source-registry prose are guarded, while still avoiding a broad schema change.
- 2026-06-12: The selected-county source boundary should be declared as structured catalog data before introducing a broader per-county readiness schema. This is the narrowest non-fragility step: it keeps current source-level readiness semantics while making the private-MVP gate less dependent on exact prose.
- 2026-06-12: County source manifests are operator-facing authority surfaces. They must track the structured selected-county scope and current source-readiness output rather than preserving older fixture-only/no-connector language.
- 2026-06-12: County source-manifest expectations should live in the private-MVP readiness catalog, not only in validator code. This keeps the manifest guard validate-only while making selected-county expansion and source-boundary edits reviewable as catalog data.

## Progress log

- 2026-06-12: Live repo, CI, source-readiness scripts, private-MVP/release-readiness checks, focused tests, and default verification were audited. Remaining actionable drift is stale DS-010/DS-023 registry/review/runbook prose and missing tests for those exact stale claims.
- 2026-06-12: DS-010/DS-023 registry, SQL seed, source reviews, and operator runbook were aligned to current selected-county source truth. Added stale-phrase guards in source-registry/private-MVP tests and the private-MVP readiness validator. Source-registry check, private-MVP readiness check, Must/all-priority source-readiness JSON, focused tests, focused ruff/mypy, release-readiness check, source-registry test suite, `git diff --check`, and default `.\scripts\verify.ps1` passed; DB smoke remains a separate `RUN_DB_SMOKE=1` gate.
- 2026-06-12: Began aggregate connector-scope readiness slice after confirming `source_readiness.py` only used one primary connector entry per source ID while DS-010 and DS-023 have multiple county-specific inventory entries.
- 2026-06-12: Aggregate connector-scope readiness metadata landed. `source_readiness.py --json` now emits `connector_names` and `connector_scope_notes`; DS-010 exposes Chatham/Buncombe/Brunswick parcel connectors and DS-023 exposes Chatham/Brunswick recorded-zoning connectors without changing source-level ready/blocked counts. Focused tests, ruff/mypy, private-MVP and release-readiness validators, combined source/private-MVP tests, `git diff --check`, and default `.\scripts\verify.ps1` passed; DB smoke remains a separate `RUN_DB_SMOKE=1` gate.
- 2026-06-12: Began private-MVP validator hardening so aggregate DS-010/DS-023 connector scope metadata is enforced by `scripts/run_private_mvp_readiness_check.ps1`, not only by tests.
- 2026-06-12: Private-MVP validator hardening landed. `scripts/private_mvp_readiness_check.py` now requires DS-010 and DS-023 aggregate connector names and scope-note fragments from Must source-readiness JSON; a negative-path test proves the validator rejects a missing selected-county DS-010 connector. Private-MVP tests, private-MVP readiness validator, focused ruff/mypy, release-readiness validator, combined source/private-MVP tests, Must source-readiness JSON, `git diff --check`, and default `.\scripts\verify.ps1` passed; DB smoke remains a separate `RUN_DB_SMOKE=1` gate.
- 2026-06-12: Private-MVP readiness catalog drift was closed. `config/private_mvp_beta_readiness.yaml` now cites both `test_mvp_regression.py` and `test_utility_closure.py`, describes DS-010 as selected-county parcel connector-ready, DS-011 as an assessor NOT_EVALUATED sentinel, and DS-023 as Chatham/Brunswick recorded-fixture UDO lookup only. The private-MVP validator and tests now require these current phrases, reject stale catalog phrases, and treat selected-county connector-name order as non-authoritative while still failing on missing, unexpected, or duplicate names. Focused private-MVP tests, private-MVP readiness validator, focused ruff/mypy, combined source/private-MVP tests, release-readiness validator, Must source-readiness JSON, and stale-phrase re-audit passed; DB smoke remains a separate `RUN_DB_SMOKE=1` gate.
- 2026-06-12: Pre-push validation repeated after the order-insensitive connector-name guard. Focused private-MVP tests, combined source/private-MVP tests, private-MVP and release-readiness validators, focused ruff/mypy, Must source-readiness JSON, stale-phrase re-audit, `git diff --check`, and default `.\scripts\verify.ps1` passed. DB-enabled smoke was not run because Docker Desktop's Linux engine was unavailable; do not treat this as DB proof.
- 2026-06-12: Began structured selected-county source-scope catalog slice. Current target is `config/private_mvp_beta_readiness.yaml`, `scripts/private_mvp_readiness_check.py`, and private-MVP tests only; schema, connector runtime, source-readiness counts, public API, report semantics, DS-017, and hosted-production gates stay unchanged.
- 2026-06-12: Structured selected-county source-scope catalog slice landed locally. `config/private_mvp_beta_readiness.yaml` now declares DS-010, DS-011, and DS-023 connector names, required source-readiness surfaces, scope-note fragments, and out-of-scope boundaries; `scripts/private_mvp_readiness_check.py` consumes that structured catalog for the selected-county gate. Focused private-MVP tests, private-MVP readiness validator, focused ruff/mypy, combined source/private-MVP tests, release-readiness validator, Must source-readiness JSON, stale-phrase re-audit, `git diff --check`, and default `.\scripts\verify.ps1` passed; DB smoke remains a separate `RUN_DB_SMOKE=1` gate.
- 2026-06-12: Began selected-county source-manifest alignment slice after finding Buncombe/Chatham/Brunswick manifests still described DS-010 and DS-011 as no machine-queryable connection / not available through the data pipeline. Scope is limited to manifest prose and private-MVP validation guards.
- 2026-06-12: Selected-county source-manifest alignment slice landed locally. Buncombe/Chatham/Brunswick manifests now track the structured DS-010/DS-011/DS-023 private-MVP boundary, including Buncombe DS-023 out-of-scope status, Chatham/Brunswick recorded-fixture zoning readiness, selected-county parcel connector readiness, and assessor NOT_EVALUATED sentinel behavior. The private-MVP validator now fails closed on stale manifest no-connector / unavailable-pipeline language. Focused private-MVP tests, private-MVP readiness validator, focused ruff/mypy, targeted and broader source-readiness/private-MVP tests, stale manifest phrase audit, `git diff --check`, and default `.\scripts\verify.ps1` passed; `git diff --check` emitted only CRLF-to-LF normalization warnings for touched Markdown files, and DB smoke remains a separate `RUN_DB_SMOKE=1` gate.
- 2026-06-12: Began selected-county manifest-scope catalog slice. Current target is `config/private_mvp_beta_readiness.yaml`, `scripts/private_mvp_readiness_check.py`, and private-MVP tests only; manifest prose, source-readiness counts, connector runtime, API behavior, report semantics, DB schema, DS-017, and hosted-production gates stay unchanged.
- 2026-06-12: Selected-county manifest-scope catalog slice landed locally. `config/private_mvp_beta_readiness.yaml` now declares Buncombe/Chatham/Brunswick manifest paths, DS-010/DS-011/DS-023 required source fragments, and shared stale-fragment denials; `scripts/private_mvp_readiness_check.py` consumes that structured catalog for manifest validation. Focused private-MVP tests, private-MVP readiness validator, focused ruff/mypy, targeted and broader source-readiness/private-MVP tests, Must source-readiness JSON, release-readiness validator, docs-only stale phrase audit, `git diff --check`, and default `.\scripts\verify.ps1` passed; local DB smoke remains a separate `RUN_DB_SMOKE=1` gate.
