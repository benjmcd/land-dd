# Plan: Extended-domain fixture ingestion — minerals end-to-end (US MVP)

Date: 2026-06-29
Branch: `claude/us-mvp-minerals-fixture` (off origin/main @ 66846f27)
Owner-independent US-MVP advancement. Parallel Codex lane (qualification/Bologna) is isolated.

## Objective
Close the verified end-to-end seam: the "extended public" connectors (minerals/geology/water/
env-hazard/broadband) are built (live + per-connector API + unit tests) and the dossier renders
their sections (via *synthetic* evidence in `test_dossier_enrichment.py`), but **none is exercised
through the fixture-ingestion → evidence → claim → dossier pipeline on a real NC AOI**. The 8 core
domains have that proof (`backend/tests/private_mvp/test_utility_closure.py`); the extended domains
do not. This slice establishes the fixture-ingestion path for the first extended domain — **minerals**
— for both the success and source-failure paths.

## Why minerals first
Homestead-relevant (federal mining claims / split-estate affect surface use + access), mountain-
Buncombe fit, and it has both a positive gate (`MINERALS_ACTIVE_CLAIMS_001`, condition
`blm_active_mining_claims_present`) and a source-unavailable gate (`MINERALS_SOURCE_UNAVAILABLE`,
condition `minerals_source_unavailable`) in `config/ruleset_homestead_mvp.yaml:119-130`. The
source-failure path also exercises the "source failures are first-class evidence, not silent
no-issue" non-negotiable end-to-end.

## Scope (verified against code, not assumed)
Gap confirmed: `app/connectors/__init__.py` exports `Static*FixtureConnector` + `evaluate_*_fixture_
quality` only for the 8 core domains; extended domains exist only as live connectors. `build_fixture_
workflow_with_public_services` needs a `FixtureConnectorProtocol` connector (zero-arg, `.load_fixture`).
So this requires a small production connector, NOT just tests/fixtures.

Rule-engine logic (`backend/app/claims_engine/rule_engine.py:340-347, 621-625, 2830-2834`):
- `_is_minerals_active_evidence`: `domain=="minerals"`, non-failure, `observed_value["blm_active_mining_claim_count"] > 0` → `MINERALS_ACTIVE_CLAIMS_001`.
- `_is_minerals_source_failure` + no active → `MINERALS_SOURCE_UNAVAILABLE`.

## Changes (smallest slice; mirrors flood_fixture exactly)
1. NEW `backend/app/connectors/minerals_fixture.py` — `StaticMineralsFixtureConnector`
   (`connector_name="fixture_minerals_static"`, `domain="minerals"`) + `MineralsFixtureConnectorResult`,
   structurally identical to `flood_fixture.py` (load JSON `{retrieval_run, evidence}`, validate
   connector_name/domain/status↔evidence-type).
2. `backend/app/connectors/__init__.py` — export the two new symbols.
3. NEW fixtures (reusing existing `tests/fixtures/golden_aois/bun_slope.geojson` AOI):
   - `tests/fixtures/connectors/nc_buncombe_bun_minerals_active.json` (succeeded; spatial evidence;
     `blm_active_mining_claim_count > 0`).
   - `tests/fixtures/connectors/nc_buncombe_bun_minerals_unavailable.json` (blocked; source-failure evidence).
4. NEW `backend/tests/private_mvp/test_extended_domain_minerals.py` — two end-to-end tests mirroring
   `test_utility_closure.py`: active-claims → `MINERALS_ACTIVE_CLAIMS_001`; source-unavailable →
   `MINERALS_SOURCE_UNAVAILABLE` unknown + dossier caveat. Both assert no forbidden overclaim phrases.

## Correction discovered while building (verify-as-you-go)
- The quality evaluator is NOT optional: the workflow falls back to the flood evaluator, so minerals
  needs its own `evaluate_minerals_fixture_quality` (thin wrapper over the generic `_evaluate_fixture_quality`).
- Minerals active evidence is a `SOURCE_OBSERVATION` (not `SPATIAL_INTERSECTION`): `blm_active_mining_claim_count`
  is in `SOURCE_OBSERVATION_ALLOWED_KEYS`. So the connector mirrors `zoning_fixture` (non-spatial),
  the evaluator uses `require_spatial_geometry=False`, and the source-failure fixture follows the gate's
  controlled-failure contract (`metrics.failure_reason`; `observed_value` keys failure_reason/error_message/
  retryable; `confidence: unknown`; no geometry).

## Out of scope (deliberate, minimal slice)
- The other 4 extended domains (geology/water/env/broadband) — trivial follow-ups once this pattern lands.
- The golden-AOI `manifest.yaml` — descriptive only; the test is self-contained. Not touched.
- No live network, no new source approval (DS-008 USGS MRDS / DS-007 BLM already approved-with-restrictions, US-wide, public).

## Isolation fence (parallel Codex lane)
CLAUDE touches ONLY: `backend/app/connectors/minerals_fixture.py`, `backend/app/connectors/__init__.py`,
`backend/tests/private_mvp/test_extended_domain_minerals.py`, the 2 new fixtures, and this plan.
No `scripts/`, `config/`, `schemas/`, or canonical state files. Disjoint from Codex's qualification/Bologna set.

## Acceptance criteria
- New connector + 2 fixtures + 2 end-to-end tests; both tests pass via `py -3.12` from `backend/`.
- ruff + mypy clean. `.\scripts\verify.ps1` green. P0 unaffected (this is US-MVP, not qualification).
- Independent reviewer pass clean. No report-semantics/schema/auth change. No overclaim phrases in dossier.
- `gh pr checks` green before merge.
