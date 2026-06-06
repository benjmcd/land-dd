# Plan: Private MVP Utility Proof

**Status:** approved  
**Created:** 2026-06-06  
**Revised:** 2026-06-06 (iteration 2 — Architect + Critic iteration 2 feedback incorporated)  
**Supersedes:** `plans/2026-06-05-l10-production-hardening.md` (production hardening continues as separate lane; this plan is the new active lane)

---

## RALPLAN-DR Summary

### Principles

1. Evidence before claim — every report assertion must cite stored evidence or explicitly record an unknown.
2. Private MVP readiness is orthogonal to hosted-production readiness — production blockers must not gate private MVP utility proof.
3. Source-linked claims or explicit unknowns — source failures are first-class evidence, not silent "no issue found."
4. Cautious report language — no legal access, buildability, title, water rights, appraisal, investment certainty.
5. Reproducible validation — milestone completion requires repo evidence and passing commands, not narrative claims.

### Decision Drivers

1. **High-ROI gap is utility proof, not more generic hardening.** The repo is materially hardened at Level 10 (partial). The primary unfulfilled gap is proving representative AOIs flow through the full pipeline to approved Markdown dossiers.
2. **DS-017 (commercial parcel vendor) must not block private MVP.** Public/official/county sources and fixture-backed stubs are sufficient for the first geography proof.
3. **Hosted-production blockers must not gate private MVP.** OAuth/OIDC, full RBAC, billing, registry publication, and hosted alerting are explicitly out of scope for this lane.

### Viable Options

**Option A — Sequential full implementation (recommended default)**
- Pros: Clear dependency order, minimal coordination overhead, lowest risk of state-file conflicts, respects bottom-up build order.
- Cons: Cannot parallelize truly independent work packages (geography manifests, readiness profile, fixtures) without coordination.

**Option B — Parallel fan-out on independent packages**
- Pros: Faster wall-clock completion of manifests + fixtures + readiness profile in parallel.
- Cons: Requires careful assignment of file ownership; risk of merge conflicts in shared state files; overhead of coordinating across concurrent agents.

**Option C — Planning only (no implementation this session)**
- Pros: Safest; no risk of regressions.
- Cons: Fails to deliver on the handoff objective — the primary goal is proving MVP utility, not just planning it.

**Recommendation:** Option A with selective parallelism where file ownership is non-overlapping (county manifests can run in parallel; state files must remain sequential).

---

## Objective

Prove a private MVP rural-land dossier workflow for a bounded geography. When this lane is done, the repo can honestly demonstrate:

```
AOI intake → source/evidence collection or explicit source-unavailable state
→ cautious claim generation → review/approval gate
→ approved Markdown rural-land dossier delivery
→ regression assertions for evidence linkage, caveats, unknowns, and forbidden overclaims
```

## Recommended Geography

**North Carolina — Buncombe County, Chatham County, Brunswick County**

Accepted as the default for private MVP pending brief source-discovery confirmation per county. If discovery shows a county has unusable public data, stale services, or hostile terms, record the issue and propose a replacement.

| County | MVP role | Source notes |
|---|---|---|
| Buncombe | Mountain/slope/elevation stress | Explicit GIS portal; parcels, street centerlines, surface water, elevations/contours, slope tool; users-must-verify posture aligns with caveated reports |
| Chatham | Piedmont rural/exurban zoning, parcel/tax | CAMA parcel service, JSON/geoJSON/PBF query, enriched tax attributes |
| Brunswick | Coastal/flood/wetlands/zoning complexity | GIS data download, viewer, interactive maps; compiled from recorded deeds and plats |

## Source Decisions

| Source | Private MVP stance |
|---|---|
| DS-010 county GIS parcels | Relevant for selected NC counties; explicit unknown/unavailable allowed per AOI |
| DS-011 county assessor/tax | Relevant as minimal parcel/tax context; no appraisals, value conclusions, or investment language |
| DS-023 local zoning ordinance PDFs | Relevant as mapped/fixture-backed zoning context; report: "mapped zoning/source indicates…, requires confirmation by…" |
| DS-017 commercial parcel vendor | Demoted/deferred from private MVP; not a blocker unless public/county sources prove insufficient |

## Non-Goals for This Lane

- Hosted deployment, OAuth/OIDC, full RBAC, external secret manager, automatic key rotation
- LLM summaries, paid geocoding, paid map tiles, paid parcel vendor (DS-017)
- Full browser/dashboard polish before Markdown report contract is stable
- Nationwide source abstraction or coverage beyond NC/Buncombe/Chatham/Brunswick
- Hosted billing integration, registry image publication as a product blocker

## Work Packages

### WP-1: State and plan alignment

**Files affected:** `tasks/task_queue.yaml`, `plans/README.md`, `state/PROJECT_STATE.md`, `state/OPEN_QUESTIONS.md`

**What:** Fix the planning-source drift. `tasks/task_queue.yaml` currently points `active_plan` at `plans/2026-06-03-foundation-vertical-slice.md`; update it to point to this plan. Update `plans/README.md` to index this as the active plan. Move the MVP geography question from Critical open to decided in `state/OPEN_QUESTIONS.md`.

**Acceptance:**
- `tasks/task_queue.yaml` `active_plan` → `plans/2026-06-06-private-mvp-utility-proof.md`
- `state/OPEN_QUESTIONS.md` geography question moved to Decided section
- `state/PROJECT_STATE.md` reflects active lane as Private MVP Utility Proof

### WP-2: County source manifests

**Files affected:** `docs/geographies/nc/buncombe/source_manifest.md`, `docs/geographies/nc/chatham/source_manifest.md`, `docs/geographies/nc/brunswick/source_manifest.md`

**What:** For each county, record the official GIS/data portal, parcel/cadastral stance, assessor/tax stance, zoning stance, known caveats, machine-queryable/fixture-backed/deferred classification, source authority level, permitted MVP usage, and report caveat text.

**Invariants:**
- No claim of legal boundary, legal access, zoning entitlement, septic suitability, wetland jurisdiction, or buildability
- Caveat text must reflect "mapped data indicates…" / "requires confirmation by…" posture

**Acceptance:**
- Three manifest files exist, one per county
- Each file covers all required fields: portal source, parcel stance, assessor stance, zoning stance, caveats, queryability class, authority level, caveat text
- No forbidden language

### WP-3: Private MVP readiness profile

**Files affected:** `config/private_mvp_beta_readiness.yaml`, `backend/tests/test_private_mvp_readiness.py`

**What:** Create a readiness profile that distinguishes `private_mvp_beta` gates from `hosted_production` gates. The profile checks for evidence of: geography selected, county manifests present, golden AOI fixture manifest, DB-backed regression path, DS-010/011/023 selected-county behavior, DS-017 not required, Markdown dossier delivery, overclaim checks, evidence-lineage checks, unknowns visible in reports, operator runbook current.

**What it does NOT block on:**
- Hosted deployment attestation, registry publication, hosted billing, full RBAC, OAuth/OIDC, external secret manager, Docker Scout credentials, paid geocoding/tiles/vendors

**Acceptance:**
- Config file exists with `private_mvp_beta` and `hosted_production` top-level sections, each listing named gates with `status` and `required_evidence` fields
- `backend/tests/test_private_mvp_readiness.py` passes: it must load `config/private_mvp_beta_readiness.yaml`, assert all expected `private_mvp_beta` gate names are present, assert `hosted_production` section exists, and assert no `private_mvp_beta` gate blocks on any of the listed production-only items above
- `cd backend; py -3.12 -m pytest -q tests/test_private_mvp_readiness.py` passes
- Hosted production gates remain unaffected
- `.\scripts\verify.ps1` passes after adding the config file

### WP-4: Source-readiness profile resolution

**Files affected:** `registers/data_source_registry.csv` (stance/review_status columns for DS-010, DS-011, DS-023), or equivalent private-MVP source stance document

**What:** Update the source registry to reflect that DS-010, DS-011, and DS-023 have a defined private-MVP stance for the selected NC counties (not just `unreviewed/pending`). DS-017 remains `blocked` but is explicitly noted as not a private-MVP blocker.

**Key constraint:** Do not claim full license/terms review is complete for DS-010/011/023; record that they are `selected-county: private-mvp-stance-accepted` with explicit fixture-backed/unavailable-allowed posture.

**Acceptance:**
- DS-010, DS-011, DS-023 have `private_mvp_stance` or equivalent field reflecting accepted private-MVP usage with explicit caveats
- DS-017 remains `blocked` but is annotated as not a private-MVP blocker
- `py -3.12 scripts/source_readiness.py --priority Must` output reflects updated stance

### WP-5: Golden AOI fixtures

**Files affected:**
- `tests/fixtures/golden_aois/` (new directory)
- `tests/fixtures/golden_aois/manifest.yaml`
- 9 GeoJSON AOI geometry files (`bun_slope.geojson`, etc.)
- Connector evidence JSON blobs in `tests/fixtures/connectors/` for domains covered by existing connectors (flood, terrain, wetlands, access, zoning) — one blob per domain per case where a non-NOT_EVALUATED result is expected
- `backend/tests/test_golden_aoi_manifest.py` — manifest schema validation test

**Two artifact types — distinction is critical:**

WP-5 produces two distinct artifact families. This resolves the ambiguity identified by the Architect:

1. **AOI geometry fixtures** (`tests/fixtures/golden_aois/*.geojson`): Valid WGS84 GeoJSON Polygons used as the `area_geojson` input to `POST /intake`. Coarse bounding polygons are acceptable. Exact parcel matching is deferred.

2. **Connector evidence fixture JSON blobs** (`tests/fixtures/connectors/nc_<county>_<case>_<domain>.json`): Required for domains exercised via `FixtureConnectorIngestWorkflow` (Path B — the existing connector review workflow path, not direct ledger injection). Follows the existing schema established by `tests/fixtures/connectors/flood_*.json` and `tests/fixtures/connectors/zoning_*.json` (`retrieval_run` + `evidence` fields per `SourceRetrievalRunContract`). Required for: flood (DS-002), terrain (DS-001), wetlands (DS-004), access (existing `StaticAccessFixtureConnector`), zoning (existing `StaticZoningFixtureConnector` / DS-023 fixture-backed path).

**Parcel/assessor domain handling (Decision: Option X):**

DS-010 (county GIS parcels) and DS-011 (county assessor) will be handled via the `NOT_EVALUATED` sentinel path, not via new connector classes. This means:
- WP-5 must add `parcels` and `assessor` to `NOT_EVALUATED_DOMAINS` in `backend/app/claims_engine/not_evaluated.py`.
- This causes the report service to inject a `NOT_EVALUATED` source-failure sentinel for those domains, which appears explicitly in the report's source manifest and unknowns list as "not determined — requires confirmation."
- This is consistent with the product spec: "source failures are first-class evidence" and "DS-010/011: explicit unknown/unavailable allowed per AOI."
- No `StaticParcelFixtureConnector` or `StaticAssessorFixtureConnector` is required for private MVP.

**NOT_EVALUATED extension — all required file changes (implementer must update ALL of these):**

Adding `parcels` and `assessor` to `NOT_EVALUATED_DOMAINS` is necessary but not sufficient. The implementer MUST update these locations in parallel or tests will fail with `KeyError` at rule evaluation:

| File | Location | Change |
|---|---|---|
| `backend/app/claims_engine/not_evaluated.py` | `NOT_EVALUATED_DOMAINS` tuple | Add `"parcels"`, `"assessor"` |
| `backend/app/claims_engine/not_evaluated.py` | `NOT_EVALUATED_CLAIM_CODES` dict | Add `"parcels": "PARCEL_NOT_EVALUATED"`, `"assessor": "ASSESSOR_NOT_EVALUATED"` (or appropriate codes) |
| `backend/app/claims_engine/not_evaluated.py` | `NOT_EVALUATED_CAVEATS` dict | Add `"parcels"` and `"assessor"` keys with caveat text (e.g., "County parcel data not evaluated — requires confirmation by county GIS") |
| `backend/app/claims_engine/rule_engine.py` | `NOT_EVALUATED_CONDITIONS_BY_DOMAIN` dict | Add `"parcels"` and `"assessor"` keys with condition strings (e.g., `"parcel_data_unsupported"`, `"assessor_data_unsupported"`) |
| `config/ruleset_homestead_mvp.yaml` | hard-gate rules section | Add entries for the new condition strings (`parcel_data_unsupported`, `assessor_data_unsupported`) matching the existing pattern for `soil_septic_unsupported`, etc. |

`NOT_EVALUATED_METHOD_CODES` derives automatically from `NOT_EVALUATED_DOMAINS` — no separate update required for that dict.

**Terrain and wetlands domain handling for fixture-backed regression:**

DS-001 (terrain/elevation) and DS-004 (NWI/wetlands) have existing bounded live connectors. They do NOT have fixture connector classes (`StaticTerrainFixtureConnector` and `StaticWetlandFixtureConnector` do not exist). For the fixture-only MVP regression (WP-6), these domains are NOT listed in `expected_connector_workflow_domains`. The regression exercises them in the following way:
- Terrain and wetlands are in the scope of the live connectors (DS-001, DS-004) which are enabled in production. In the fixture-only regression, no terrain or wetlands evidence is injected via Path B.
- The BUN-slope case is designed to test slope/terrain stress conceptually, but the fixture-only regression covers flood evidence (via `StaticFloodFixtureConnector`) for that case; terrain data is acknowledged as "live-connector-only" in the runbook.
- Do not add terrain/wetlands to `NOT_EVALUATED_DOMAINS` — those domains are supported by live connectors and will evaluate normally in production. Their absence from the fixture regression is a fixture-scope limitation, not a domain-unsupported condition.

**Fixture schema per case (in manifest.yaml):**

`expected_connector_workflow_domains` is restricted to domains with **existing fixture connector classes**: `flood` (`StaticFloodFixtureConnector`), `access` (`StaticAccessFixtureConnector`), `zoning` (`StaticZoningFixtureConnector`). Terrain and wetlands are live-connector-only and are not listed here.

```yaml
case_id: BUN-slope
county: buncombe
state: nc
intent: rural_land_purchase
geometry_file: bun_slope.geojson
connector_fixture_files:
  flood: nc_buncombe_bun_slope_flood.json
  access: nc_buncombe_bun_slope_access.json
expected_source_domains: [flood, access, parcels, assessor]
expected_connector_workflow_domains: [flood, access]
expected_not_evaluated_domains: [parcels, assessor]
expected_red_flag_categories: [slope_constraint]
expected_caveats: [gis_slope_not_survey_grade]
expected_unknowns: [parcels_not_evaluated, assessor_not_evaluated]
forbidden_claims:
  - "You can build here"
  - "legal access"
  - "water rights"
  - "good investment"
  - "This property is worth"
  - "This land is safe"
```

**Available fixture connector classes (do not invent new domains for Path B):**
- `fixture_flood_static` → `StaticFloodFixtureConnector` + `evaluate_flood_fixture_quality`
- `fixture_access_static` → `StaticAccessFixtureConnector` + `evaluate_access_fixture_quality`
- `fixture_zoning_static` → `StaticZoningFixtureConnector` + `evaluate_zoning_fixture_quality`

Use only these three in `expected_connector_workflow_domains`. Connector blobs must match the connector's domain exactly. WP-6 must wire the correct quality evaluator per connector using the existing `_QUALITY_EVALUATORS` routing dict in `backend/app/api/connectors.py` — do not hardcode or default to the flood evaluator.

**Acceptance:**
- 9 GeoJSON AOI geometry files exist with valid WGS84 Polygons
- `manifest.yaml` exists, is YAML-parseable, and contains all required fields for each case
- Connector evidence JSON blobs exist for all `expected_connector_workflow_domains` entries
- `parcels` and `assessor` are added to `NOT_EVALUATED_DOMAINS` in `backend/app/claims_engine/not_evaluated.py`
- `backend/tests/test_golden_aoi_manifest.py` passes: loads `manifest.yaml`, validates each case has `case_id`, `county`, `state`, `intent`, `geometry_file`, `forbidden_claims`, `expected_not_evaluated_domains`; validates each `geometry_file` is a valid GeoJSON Polygon; validates each `connector_fixture_file` path exists
- `cd backend; py -3.12 -m pytest -q tests/test_golden_aoi_manifest.py` passes
- `.\scripts\verify.ps1` passes (existing NOT_EVALUATED tests still pass with added domains)
- No live network calls required to use fixtures

### WP-6: DB-backed MVP regression proof

**Files affected:** `scripts/run_mvp_regression.ps1` (and `.sh`), `backend/tests/private_mvp/test_mvp_regression.py`

**Evidence path used:** Path B (`FixtureConnectorIngestWorkflow`), not direct ledger injection. Fixture-domain evidence enters the ledger via the existing connector workflow, records a `source_ingest_run_id`, and is gated behind the connector review/approval step (using the scoped reviewer service-account auth already implemented). This ensures the regression exercises the real production code path. The `parcels` and `assessor` domains are handled via the `NOT_EVALUATED` sentinel extended in WP-5 — these do not go through the connector workflow but produce explicit source-failure evidence records with status `NOT_EVALUATED`.

**Quality evaluator wiring — critical implementer note:** When constructing `FixtureConnectorIngestWorkflow` in the regression, pass the correct domain-specific quality evaluator per connector. Use the `_QUALITY_EVALUATORS` routing dict already in `backend/app/api/connectors.py`: `fixture_flood_static` → `evaluate_flood_fixture_quality`, `fixture_access_static` → `evaluate_access_fixture_quality`, `fixture_zoning_static` → `evaluate_zoning_fixture_quality`. Do NOT use the default `evaluate_flood_fixture_quality` for non-flood connectors — the flood evaluator checks for `connector_name == "fixture_flood_static"` and will produce a blocking quality issue for any other connector.

**What:** One reproducible DB-backed private MVP verification path. Requires Postgres-backed services (`RUN_DB_SMOKE=1`). Exercises:

1. Apply migrations/seeds (if not already applied)
2. Register a representative AOI from the golden fixture set (at least one per county: BUN-*, CHA-*, BRU-*)
3. Create a report request via `POST /report-runs`
4. Run fixture connector workflow for each `expected_connector_workflow_domain` per case — restricted to existing fixture connectors: `flood` (`StaticFloodFixtureConnector`), `access` (`StaticAccessFixtureConnector`), `zoning` (`StaticZoningFixtureConnector`)
5. Exercise connector review/approval gate for each run (uses scoped reviewer service-account auth)
6. Create the approved report
7. Retrieve approved Markdown dossier via `GET /report-runs/{id}/dossier` (or equivalent approved-report endpoint)
8. Assert: `source_manifest` is non-empty and includes at least one connector-workflow domain per case
9. Assert: `unknowns` list contains `parcels`-domain and `assessor`-domain NOT_EVALUATED entries (produced by WP-5 NOT_EVALUATED_DOMAINS extension)
10. Assert: `caveats` are non-empty
11. Assert: `verification_tasks` are non-empty
12. Assert: report Markdown content does not contain any forbidden claim phrase from the golden fixture manifest
13. Emit deterministic summary with pass/fail per assertion

**Minimum evidence requirements (distinguishing utility proof from pipeline exercise):**

At minimum, the regression must verify that at least one case per county:
- Has connector-workflow evidence (flood or terrain) in the source manifest with `retrieval_status: succeeded`
- Has explicit `parcels` and `assessor` NOT_EVALUATED entries in the report unknowns
- Has no forbidden overclaim phrase in the Markdown dossier output

This is achievable with the WP-5 fixture artifacts and the existing connector infrastructure — it does not require new live-source connectors.

**Acceptance:**
- `backend/tests/private_mvp/test_mvp_regression.py` exists with DB-smoke-gated tests
- At least one test per county (3 tests minimum) passes the evidence, unknown, caveat, and overclaim assertions above
- `cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/private_mvp/test_mvp_regression.py` passes
- Forbidden-phrase check uses the `forbidden_claims` list from `tests/fixtures/golden_aois/manifest.yaml`
- `parcels` and `assessor` NOT_EVALUATED entries appear in the report unknowns for all tested cases
- `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1` continues to pass

### WP-7: Report-language and evidence-lineage checks

**Files affected:** `backend/tests/reports/test_report_overclaim.py`

**Relationship to existing tests:** `backend/tests/claims_engine/test_forbidden_language*.py` (if present) covers the claim-engine layer contract. `backend/tests/reports/test_report_regression.py` covers fixture report artifact semantics (structure, field presence). WP-7's `test_report_overclaim.py` is specifically targeted at Markdown dossier output (via `build_rural_land_dossier` or the `GET /report-runs/{id}/dossier` response body) to catch overclaims that might survive the claims contract but appear in rendered prose. Do not duplicate existing claim-contract coverage.

**What:** Tests that fail if Markdown dossier output contains forbidden overclaim phrases (tested at the Markdown string level, not the claim contract level):
- "You can build here"
- "This parcel has legal access" / "legal access"
- "This property has water rights" / "water rights"
- "This is a good investment" / "good investment"
- "This land is safe"
- "This property is worth"

Also assert at the Markdown dossier level:
- At least one caveat sentence is present in the dossier output
- Unknowns/source-failures are visible (not silently absent) — test that NOT_EVALUATED domains appear as "not determined" or equivalent in dossier prose
- Source linkage (at least one source citation) is present

**Acceptance:**
- `test_report_overclaim.py` tests the Markdown dossier string, not the `ReportRunContract` fields
- Tests fail deterministically if any forbidden phrase appears in the Markdown output
- Caveat, unknown, and source-citation assertions pass for the fixture-backed test dossier
- `cd backend; py -3.12 -m pytest -q tests/reports/test_report_overclaim.py` passes
- `.\scripts\verify.ps1` passes after adding the tests

### WP-8: Operator runbook and state update

**Files affected:** `docs/runbooks/mvp_operator.md`, `state/PROJECT_STATE.md`, `state/WORKLOG.md`, `state/VALIDATION_LOG.md`

**What:** Update the operator runbook so an operator can follow the private MVP path without reading implementation code. Record in state files: what changed, what was validated, which commands passed, which parts remain fixture/manual/deferred, which production blockers remain outside this lane.

**Acceptance:**
- Runbook covers: DB startup, fixture-backed AOI intake, report creation, review/approval, Markdown dossier retrieval, known limitations
- Validation log records commands run and residual risks
- Worklog reflects this session's changes

---

## Verification Expectations

**Minimum passing gates for lane completion:**

```
- active plan/task pointers consistent
- MVP geography recorded as accepted-for-private-MVP
- county source manifests exist for all 3 counties
- private_mvp_beta readiness profile exists
- DS-017 is not a private-MVP blocker (annotated in registry)
- DS-010/011/023 have selected-county stance
- golden AOI manifest exists with 9+ cases
- DB-backed MVP regression path exists and exits 0
- approved Markdown dossier is retrievable in regression
- report-language overclaim checks pass
- source/evidence/caveat/unknown assertions covered by tests
- validation log records commands and residual risks
- .\scripts\verify.ps1 passes (all existing tests continue to pass)
```

## Residual Risks

| Risk | Mitigation |
|---|---|
| DS-010/DS-011/DS-023 may have no machine-queryable public API for NC counties within private MVP timeline | Use fixture-backed stubs with explicit `source_unavailable` evidence; this is explicitly allowed by the handoff |
| Existing report service may not generate Markdown dossier for arbitrary county AOIs without a registered county connector | Scope regression to fixture-backed connectors; record Markdown dossier path as fixture-exercise proof, not live-data proof |
| DB regression script may require Docker to be running | Gate with `RUN_DB_SMOKE` env var as already established; document clearly in runbook |
| state files are large and drift frequently | Update only materially affected sections; do not rewrite entire files |

## ADR Decisions Required

| Decision | Where |
|---|---|
| Private MVP readiness is orthogonal to hosted-production readiness | `docs/adr/mvp-0001-private-mvp-readiness-separation.md` |
| NC/Buncombe/Chatham/Brunswick as accepted MVP geography | Record in `state/OPEN_QUESTIONS.md` Decided section; no ADR required unless architecture is impacted |
| DS-017 demoted from private MVP Must to optional/deferred | Record in `registers/data_source_registry.csv` and `config/private_mvp_beta_readiness.yaml` |

**ADR mvp-0001 must explicitly record:**
1. Fixture-backed evidence for existing connector domains (flood, terrain, wetlands, access, zoning) traverses Path B — `FixtureConnectorIngestWorkflow` — recording a `source_ingest_run_id` and going through the connector review/approval gate. Evidence is NOT injected directly into the ledger, bypassing the approval gate.
2. DS-010 (parcels) and DS-011 (assessor) are handled via `NOT_EVALUATED_DOMAINS` extension in `not_evaluated.py` for private MVP. They produce explicit `NOT_EVALUATED` source-failure sentinels in the evidence ledger, which appear as unknowns in reports and dossiers. No `StaticParcelFixtureConnector` or `StaticAssessorFixtureConnector` is required for private MVP.
3. This is a private MVP decision only. A future live-connector pass for DS-010/DS-011 will require proper connector classes and a source-rights review.

## Implementation Order

1. WP-1 (state alignment) — unblock all other packages
2. WP-2 + WP-3 + WP-4 (county manifests, readiness profile, source stance) — independent; can run in parallel
3. WP-5 (golden AOI fixtures) — independent of WP-2/3/4; can run concurrently
4. WP-6 (DB regression proof) — depends on WP-5 fixtures
5. WP-7 (overclaim/lineage checks) — depends on WP-6 regression infrastructure
6. WP-8 (runbook + state update) — after WP-6/7 pass
