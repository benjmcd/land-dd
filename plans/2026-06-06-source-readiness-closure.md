# Source Readiness Closure Plan

## Purpose

Close source-readiness gaps without overclaiming production readiness. This plan now starts from the current audited state: DS-001, DS-002, DS-003, DS-004, DS-010, DS-011, and DS-023 are Must-priority connector-ready; DS-017 remains the only Must-priority blocker. Across all priorities, the current source-readiness check reports 13/25 connector-ready, including DS-022 Census TIGER/ACS for bounded TIGERweb tract/block-group geography context only.

## Current facts

- Must-priority source readiness is `sources=8 ready=7 blocked=1`; DS-017 Commercial parcel vendor remains blocked by vendor/license selection and is not required for the private MVP unless product scope changes.
- All-priority source readiness is `sources=25 ready=13 blocked=12`; DS-022 Census TIGER/ACS is connector-ready only for administrative TIGERweb geography context. ACS demographic variables, protected-class analytics, neighborhood desirability, market/investment/lending suitability, and residential steering remain excluded.
- DS-011 County assessor is connector-ready only as an explicit `AssessorNotEvaluatedConnector`: it records ASSESSOR_NOT_EVALUATED source-failure evidence for every area. It does not query live assessor portals or expose owner/value/sale-history fields.
- DS-023 Local zoning ordinance PDFs is connector-ready through recorded-fixture zoning district connectors for reviewed county UDO tables. It does not claim live PDF retrieval, autonomous amendment tracking, final legal zoning interpretation, or raw PDF redistribution.
- DS-020 NOAA NWS climate/weather is connector-ready through the bounded point/zone API connector. It provides administrative forecast-zone context only, not climate normals, frost dates, growing-season length, or agricultural risk conclusions.
- DB-enabled verification should be re-run when local PostgreSQL/PostGIS prerequisites are available; default verification does not prove DB smoke unless `RUN_DB_SMOKE=1` is set and prerequisites exist.

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

## Mid-term pass

1. Select the next non-Must source-readiness candidate from live registry evidence.
   - DS-022 Census TIGER/ACS is complete for TIGERweb geography context only.
   - Prioritize remaining public/government sources only after source authority, field policy, cache/export behavior, attribution, caveats, connector inventory, and connector/API tests are scoped.
   - Do not promote source readiness from source-review prose alone; require connector proof and source-readiness test updates.

2. Re-run DB-backed verification where prerequisites exist.
   - Start PostgreSQL/PostGIS or use an equivalent configured DB runtime.
   - Run `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`.
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
- Release-readiness scripts, runbook, source-readiness tests, and source-readiness CLI agree on Must `sources=8 ready=7 blocked=1`.
- `state/PROJECT_STATE.md` and `state/VALIDATION_LOG.md` clearly identify DS-017 as the only Must blocker, DS-022 as connector-ready for TIGERweb geography context only, and DB smoke as skipped unless `RUN_DB_SMOKE=1` prerequisites are present.
- Focused connector/API/source-readiness/release-readiness checks pass.
- `git diff --check` passes.
- Default `.\scripts\verify.ps1` passes, or any failure is recorded with a specific blocker.
