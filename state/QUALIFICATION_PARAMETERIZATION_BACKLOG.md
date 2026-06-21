# Qualification Parameterization Backlog

Status: `P0 = BLOCKED`

This file is a visibility register for the empirical-qualification adoption path. It
does not land the qualification validator, catalog, status schema, source profiles, or
CI selftest. It does not approve Bologna, DS-017, hosted authority, source rights, or
any owner decision.

Every row below is `BLOCKED (external/owner authority)` until a cited decision record,
review artifact, or approved source profile exists.

No AOI selection, source approval, fixture capture, runtime/report use, or source registry promotion is authorized by this backlog.

## Sources

- Read-only framework input:
  `C:\Users\benny\Downloads\land-dd_empirical_qualification\PROJECT_PARAMETERIZATION_BLOCKERS.md`.
- Empirical-qualification boundary: `docs/adr/0004-empirical-qualification-control-plane.md`.
- Bologna first-gate authority: `config/bologna_pilot_scope_authority.yaml`.
- Bologna source-rights matrix: `config/bologna_source_rights.yaml`.
- Bologna source-authority intake: `config/bologna_source_authority_intake.yaml`.
- Bologna recorded-source corpus: `config/bologna_recorded_source_corpus.yaml`.

## Selected Scope

| Field | Value | Status |
|---|---|---|
| `product_scope_profile` | `BOUNDED_USER_VALIDATED` | BLOCKED (external/owner authority) |
| `deployment_profile` | `LOCAL_SINGLE_USER` | BLOCKED (external/owner authority) |
| `windows_native_required` | `true` | BLOCKED (external/owner authority) |
| `candidate_generation_enabled` | `false` | profile disabled unless owner activates |
| `financial_modeling_enabled` | `false` | profile disabled unless owner activates |
| `ai_llm_enabled_for_decision_relevant_output` | `false` | profile disabled unless owner activates |
| `commercial_profile_enabled` | `false` | profile disabled unless owner activates |

## Readiness Summary

| Blocker class | Count/status | Gate effect |
|---|---:|---|
| Active gates | 12 | BLOCKED (external/owner authority) |
| Active DRAFT criterion contracts | 60 | BLOCKED (external/owner authority) |
| Active DRAFT/unresolved target bindings | 51 | BLOCKED (external/owner authority) |
| Active DRAFT judgment rubrics | 16 | BLOCKED (external/owner authority) |
| Qualified-domain profiles still DRAFT | 8 | BLOCKED (external/owner authority) |
| Approved source profiles selected | 0 | BLOCKED (external/owner authority) |
| Unresolved scope/version fields | 6 plus `ruleset_versions` | BLOCKED (external/owner authority) |
| Inactive/conditional DRAFT contracts | 36 | excluded unless owner activates profile |

## P0 Repo-Local Auto-Evidence

These rows have repo-local evidence collected in
`docs/qualification/P0_AUTO_EVIDENCE.yaml`. They remain blocked because no external
target, vault, source, rubric, reviewer, candidate, or controlled storage authority has
been frozen.

| Criterion | Evidence status | Effective status | Still-blocked reason |
|---|---|---|---|
| `P0-004` | auto-evidenced; still target-blocked | BLOCKED | External vault/access-control records and sealed-case hashes are not approved. |
| `P0-005` | auto-evidenced; still target-blocked | BLOCKED | Sealed acceptance case identity and case provenance register are not approved. |
| `P0-021` | auto-evidenced; still target-blocked | BLOCKED | Controlled storage, archive manifests, and evidence hashes are not approved. |
| `P0-023` | auto-evidenced; still target-blocked | BLOCKED | Frozen thresholds, candidate artifact, and sealed run/version records are absent. |

## Active Gates

All active gates require frozen targets, contracts, rubrics where applicable, reviewer
authority, and empirical evidence before any `PASS` claim:

`A`, `DB`, `DQ`, `G`, `IR`, `M`, `P0`, `Q1`, `Q2`, `R`, `S`, `W`.

## Active Criterion Contracts Requiring Freeze

Every listed criterion is `BLOCKED (external/owner authority)`.

- `A`: `A-008`, `A-009`, `A-010`, `A-012`, `A-013`.
- `DB`: `DB-007`, `DB-009`, `DB-013`, `DB-015`, `DB-020`.
- `DQ`: `DQ-002`, `DQ-004`, `DQ-005`, `DQ-006`, `DQ-012`, `DQ-015`, `DQ-019`, `DQ-020`, `DQ-022`.
- `G`: `G-007`.
- `M`: `M-004`, `M-005`, `M-007`, `M-009`, `M-015`.
- `P0`: `P0-014`, `P0-017`, `P0-025`.
- `Q1`: `Q1-006`, `Q1-007`, `Q1-008`, `Q1-016`, `Q1-017`, `Q1-019`, `Q1-020`, `Q1-029`, `Q1-034`.
- `Q2`: `Q2-001`, `Q2-005`, `Q2-006`, `Q2-007`, `Q2-008`, `Q2-009`, `Q2-010`, `Q2-011`, `Q2-012`, `Q2-014`, `Q2-016`, `Q2-018`, `Q2-021`, `Q2-022`, `Q2-023`, `Q2-027`, `Q2-029`, `Q2-030`.
- `R`: `R-008`, `R-009`.
- `S`: `S-009`.
- `W`: `W-003`, `W-011`.

## Target Binding Blockers

Every target binding below must become frozen with resolved values before P0 can pass.

| Gate group | Blocked target bindings |
|---|---|
| `P0` | `P0-014`, `P0-017`, `P0-025` |
| `Q1` | `Q1-006`, `Q1-007`, `Q1-008`, `Q1-016`, `Q1-017`, `Q1-019`, `Q1-020`, `Q1-029`, `Q1-034` |
| `Q2` | `Q2-001`, `Q2-005`, `Q2-006`, `Q2-007`, `Q2-008`, `Q2-009`, `Q2-010`, `Q2-011`, `Q2-012`, `Q2-014`, `Q2-016`, `Q2-018`, `Q2-021`, `Q2-022`, `Q2-027`, `Q2-029` |
| `DQ` | `DQ-002`, `DQ-004`, `DQ-005`, `DQ-006`, `DQ-012`, `DQ-015`, `DQ-019`, `DQ-022` |
| `DB` | `DB-007`, `DB-009`, `DB-013`, `DB-015`, `DB-020` |
| `S` | `S-009` |
| `A` | `A-008`, `A-009`, `A-012` |
| `M` | `M-005`, `M-007`, `M-009` |
| `G` | `G-007` |
| `R` | `R-008` |
| `W` | `W-003`, `W-011` |

Unresolved reference families include practical-effect thresholds, Q1/Q2 calibration
targets, runtime and memory budgets, data-quality thresholds, database latency and
capacity budgets, security quota profile, accessibility supported matrix, regulatory
change-monitoring frequency, Windows tool matrix, and `ruleset_versions`.

## Judgment Rubric Blockers

Every rubric must define reviewer competence, dimensions, scale, pass rule,
adjudication, calibration cases, and evidence schema before it can unblock its gate:

`A-010`, `A-012`, `A-013`, `DQ-020`, `M-004`, `M-015`, `P0-025`, `Q1-020`, `Q2-009`,
`Q2-012`, `Q2-014`, `Q2-022`, `Q2-023`, `Q2-029`, `Q2-030`, `R-009`.

## Domain Profile Blockers

Every domain profile remains `DRAFT` and must freeze source hierarchy, issue taxonomy,
critical/material definitions, severity/confidence rubrics, tolerances, exclusions,
metrics, reviewers, and surveillance plan:

`flood`, `wetlands`, `slope_terrain`, `soils_septic_proxy`,
`physical_road_access_proxy`, `zoning_context`, `environmental_context`,
`source_availability_and_conflict`.

## Source Profile Blockers

Approved selected source profiles: `0`.

Before P0 can pass, the exact source set must be selected and each selected source must
have an approved source-quality profile covering authority, rights, commercial/cache/
retain/export/AI permissions, preservation mode, coverage, freshness, quality,
normalization, failure behavior, retirement, enabled operations, and enforcement
controls.

## Scope And Version Blockers

These fields remain unresolved and block P0 until frozen:

`report_contract_version`, `api_contract_version`, `normalization_schema_version`,
`geometry_pipeline_version`, `source_snapshot_policy`, `data_as_of_policy`,
`ruleset_versions`.

## Bologna Priority Blockers

The Bologna path remains the prioritized product pursuit, but all steps below are
blocked by external/owner authority. This backlog only makes the sequence explicit.

### Bologna pilot-scope authority

Gate unblocked if completed: decide whether any Bologna pilot preparation may proceed
beyond blocked catalogs.

Blocked decisions:

`product_authorizes_bologna_pilot_reference`, `one_aoi_geometry_or_named_boundary`,
`intended_operator_and_use_case`, `pilot_non_goals_and_exclusions`,
`stop_conditions_and_reversion_plan`, `jurisdiction_boundary_review`,
`evidence_only_or_rulepack_scope`, `ds017_treatment_for_pilot`,
`candidate_source_selection_policy`, `fixture_capture_boundary`,
`report_runtime_boundary`, `no_overclaim_review_owner`.

### Bologna source-rights matrix

Gate unblocked if completed: allow exact candidate source rows to move from pending
review to reviewed source authority. This still does not create fixtures or runtime
use by itself.

Every candidate remains pending until source-schema, license, cache, export, AI-use,
raw-data, attribution, fixture-use, runtime-use, report-use, caveat, and source-version
evidence is cited.

### Bologna recorded-source corpus

Gate unblocked if completed: allow one approved recorded-source corpus manifest after
scope and per-source rights authority are cited.

Blocked corpus decisions:

`one_aoi_scope`, `exact_source_selection`, `completed_per_source_rights_review`,
`source_contract_fields_complete`, `source_registry_row_review`,
`recorded_fixture_scope`, `retrieval_metadata_policy`, `source_version_policy`,
`attribution_policy`, `crs_precision_policy`, `field_allowlist`, `field_denylist`,
`no_data_policy`, `source_failure_policy`, `caveat_policy`, `report_use_policy`,
`raw_data_export_policy`, `review_owner`, `no_overclaim_review`.

### DB-backed Bologna report proof

Gate unblocked if completed: prove one local DB-backed Bologna report with claims,
evidence, unknowns, caveats, artifacts, and lineage after pilot scope, source rights,
recorded corpus, report-use policy, and no-overclaim review are approved.

Blocked output: no report/API/UI/runtime proof, no source-registry promotion, no DB
seed, no connector, no rulepack, no hosted proof, no Level 10 claim.

## Controlled Dispositions

Each blocker must eventually receive exactly one controlled disposition:

`FROZEN_TARGET`, `FROZEN_RUBRIC`, `FROZEN_DOMAIN_PROFILE`,
`APPROVED_SOURCE_PROFILE`, `PROFILE_EXCLUDED_WITH_EVIDENCED_NA`,
`BLOCKED_WITH_OWNER_AND_DECISION`, or `REMOVED_THROUGH_REVIEWED_FRAMEWORK_CHANGE`.

Silent deletion, post-result threshold changes, or scope changes after unsealing
invalidate the qualification run.
