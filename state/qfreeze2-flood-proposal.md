# QFREEZE-2 Flood-Only Proposal Packet

Generated: 2026-07-06

Status: review-only proposal. This packet freezes nothing, records no owner authority,
does not update `state/owner-decisions.md`, does not change qualification config, and
does not change `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`. `P0` remains `BLOCKED`.

## Authority Boundary

This packet is a proposed owner-ratifiable freeze design for a future follow-up slice.
The future slice would still need a cited owner decision before it can change any
`DRAFT` status to `FROZEN`, approve anything beyond already-approved `DS-002`, or
write any owner-decision/status/config record.

Current evidence anchors:

| Fact | Evidence |
|---|---|
| Current target registry is `DRAFT`. | `config/qualification/qualification_targets.yaml:2` |
| Current qualified domains are eight domains including `flood`. | `config/qualification/qualification_targets.yaml:18` |
| Current selected source profile is `DS-002`. | `config/qualification/qualification_targets.yaml:56` |
| `DS-002` is already `APPROVED` and covers `flood`. | `config/qualification/source_profiles/source_quality_profile.ds-002.yaml:2`, `config/qualification/source_profiles/source_quality_profile.ds-002.yaml:4`, `config/qualification/source_profiles/source_quality_profile.ds-002.yaml:31` |
| Current rubric registry is `DRAFT`. | `config/qualification/judgment_rubrics.yaml:2` |
| Current status keeps `p0` `BLOCKED`. | `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` |
| QFREEZE-1 froze only selected scope/version/source fields and W-003/W-011 bindings. | `state/owner-decisions.md` |

## Proposed Frozen Scope

Proposed future target change:

```yaml
scope.qualified_domains:
- flood
```

The seven currently listed non-flood domains would be excluded from the qualified
scope, not passed:

| Domain | Proposed disposition | Consequence |
|---|---|---|
| `wetlands` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | No wetland jurisdiction, NWI, delineation, or buildability qualification claim. |
| `slope_terrain` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | No terrain/buildability/stability qualification claim. |
| `soils_septic_proxy` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | No septic suitability or soil interpretation qualification claim. |
| `physical_road_access_proxy` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | No legal/physical access qualification claim. |
| `zoning_context` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | No zoning entitlement or permitted-use qualification claim. |
| `environmental_context` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | No broad environmental hazard qualification claim. |
| `source_availability_and_conflict` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | Flood source coverage/conflict remains handled inside the flood profile only. |

This aligns source coverage with `DS-002`, whose approved profile covers `flood` and
not the other domains.

## P0 Predicate Map

`scripts/qualification_status_check.py` derives P0 as `BLOCKED` when any of six
parameterization predicates is unresolved.

| Predicate | Checker anchor | Current state | Proposal effect if later applied |
|---|---|---|---|
| Target registry and candidate identity resolved. | `scripts/qualification_status_check.py:324`, `scripts/qualification_status_check.py:404` | Targets are `DRAFT`; candidate fields are null. | Requires future `targets.status=FROZEN` and mechanical candidate fields: `commit`, `artifact_digest`, `protocol_version`, `targets_version`, `vocabulary_version`, `criteria_catalog_digest`. Without candidate identity, P0 stays `BLOCKED`. |
| Required domain and source profiles resolved. | `scripts/qualification_status_check.py:331` | Eight domain profiles are represented by template only; `DS-002` is approved. | One frozen `flood` domain profile plus selected `DS-002` would satisfy flood-only source/domain coverage. |
| Scope/version fields resolved. | `scripts/qualification_status_check.py:357` | QFREEZE-1 already resolved report/API/ruleset/normalization/geometry/source snapshot/data-as-of fields. | Keep existing values; narrow `qualified_domains` to `[flood]`. |
| Target bindings frozen and references non-empty. | `scripts/qualification_status_check.py:364` | 82 bindings are `DRAFT`; W-003/W-011 bindings are already `FROZEN`. | Freeze every referenced binding with resolved values or evidenced N/A values. |
| Non-DIAGNOSTIC catalog contracts frozen. | `scripts/qualification_status_check.py:380` | 96 non-DIAGNOSTIC contracts are still `DRAFT`; this predicate is catalog-wide, not active-gate-only. | Freeze or formally disposition all 96. If the future slice does not change all 96 or make a reviewed framework change, P0 remains `BLOCKED`. |
| Judgment rubric registry and entries frozen. | `scripts/qualification_status_check.py:391` | Registry plus 19 entries are `DRAFT`; 16 are active for the current profile. | Freeze the registry and all 19 entries, with 16 applicable flood/current-profile rubrics in full and 3 disabled-profile rubrics as evidenced N/A. |

Dry-run conclusion: in-memory checker simulation shows the proposal still leaves P0
blocked unless candidate identity is also supplied. With future owner-ratified target,
catalog, rubric, flood-profile, source-profile, and candidate identity values applied,
the parameterization predicate becomes false and derived `p0` can become `NOT_RUN`.
That is not `PASS`; `PASS` still requires a separate sealed evidence run, result file,
and the never-auto invariants such as P0-004, P0-005, P0-021, and P0-023.

## Proposed Target Values

Values marked `NEW` have no resolved in-repo draft value today and are the highest
owner-review burden. Values marked `EXISTING` reuse the current draft value from
`config/qualification/qualification_targets.yaml`. Values marked `N/A` are proposed
only to clear catalog-wide parameterization for disabled capabilities.

| Parameter family | File anchor | Current | Proposed value | Disposition | Rationale |
|---|---|---|---|---|---|
| `protocol.confidence_level` | `config/qualification/qualification_targets.yaml:71` | `0.95` | `0.95` | `FROZEN_TARGET` | EXISTING conservative confidence level. |
| `protocol.pre_adjudication_reliability_minimum` / P0-014 | `config/qualification/qualification_targets.yaml:72`, `config/qualification/criterion_catalog.yaml:537` | `0.7`, binding `DRAFT` | `0.7`, binding `FROZEN` | `FROZEN_TARGET` | EXISTING reviewer/source reliability floor. |
| Protocol statistical methods | `config/qualification/qualification_targets.yaml:79` | null methods | `primary_analysis_method=stratified pre-registered acceptance analysis using exact or Wilson intervals`; `cluster_handling_method=AOI-level clustered denominators`; `multiple_comparison_method=Holm-Bonferroni for secondary families`; `missing_data_method=fail-closed unknown, no imputation`; `practical_effect_thresholds=zero critical false clearances plus material-effect floors` | `FROZEN_TARGET` | NEW; required before unsealing so methods are not result-chosen. |
| Q1 recall/false-positive/linkage floors | `config/qualification/qualification_targets.yaml:93` | existing numeric floors | Keep `critical_issue_recall=1.0`, material recall `0.9` point/`0.8` lower CI, severe false positive `0.1` point/`0.2` upper CI, verification coverage `1.0`, per-geography/intent/domain floors `1.0` | `FROZEN_TARGET` | EXISTING strict screening-safety floors. |
| Q1 calibration/runtime values | `config/qualification/qualification_targets.yaml:101` | partial/null | Keep high-confidence correctness `0.95`; NEW `confidence_expected_calibration_error_maximum=0.10`, `severity_weighted_agreement_minimum=0.85`, `p95_report_runtime_seconds=60`, `p95_report_memory_mb=2048` | `FROZEN_TARGET` | NEW values bound confidence and local single-user runtime without implying production scale. |
| Q2 user-utility floors | `config/qualification/qualification_targets.yaml:112` | existing/null mix | Keep participants `24`/`8`, completion `0.9`, critical exclusion recognition `0.95`, material issue improvement `15`, median time reduction `30`, decision concordance `0.8`, unknown recognition/evidence/verification floors `0.9`, usefulness median `4`, critical workflow median `3`, persona floor `0.9`; NEW trust calibration `0.15`, error recovery `0.9`, accessibility completion `0.9`, median support helps `1`, workload score `50` | `FROZEN_TARGET` | Existing values define the utility test; NEW values close nulls conservatively. |
| Q3 inactive non-regression/cost | `config/qualification/qualification_targets.yaml:136` | partial/null | Keep performance regression `0.1`, runtime multiplier `2.0`; NEW cost multiplier `1.25` only as profile-inactive N/A/deferred disposition | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | Q3 expansion is not part of flood-only P0. |
| DB local evidence spine targets | `config/qualification/qualification_targets.yaml:148` | null/empty | NEW `postgresql_versions=[16.x]`, `postgis_versions=[3.x]`, `proj_gdal_version_policy=repo-locked runtime`, `p95_core_query_latency_ms=500`, `max_connection_budget=20`, volume multiplier `3`, `rpo_minutes=1440`, `rto_minutes=240`, `pitr_required=true`, migration downtime `60`, capacity headroom `0.30` | `FROZEN_TARGET` | Conservative local/DB-smoke scope, not hosted production. |
| Security quota profile / S-009 | `config/qualification/qualification_targets.yaml:160`, `config/qualification/criterion_catalog.yaml:9290` | null profile | NEW local single-user API-key quota profile: bounded connector/report jobs, per-request AOI limits, no uncontrolled retries, zero critical/high unresolved applicable vulnerabilities retained | `FROZEN_TARGET` | Bounds misuse/cost for local review scope. |
| Accessibility matrix | `config/qualification/qualification_targets.yaml:168` | partial/null | Keep WCAG 2.2 AA and one manual assistive reviewer; NEW matrix: Windows 11 current Chrome/Edge/Firefox plus responsive mobile viewport smoke; persona comprehension target requires correct caveat/unknown interpretation | `FROZEN_TARGET` | Matches user-facing local workflow without broad browser certification. |
| Maintainability targets | `config/qualification/qualification_targets.yaml:175` | partial/null | Keep mutation floor `0.8`, flaky rate `0.01`; NEW complexity/size thresholds: no critical module over approved threshold without plan/tests; startup context remains thin via manifest routing | `FROZEN_TARGET` | Preserves maintainability proof without LOC gaming. |
| Regulatory/professional scope / R-008 | `config/qualification/qualification_targets.yaml:284`, `config/qualification/criterion_catalog.yaml:7290` | null cadence | NEW `change_monitoring_frequency_days=90`; external review required for new high-risk claim class remains `true` | `FROZEN_TARGET` | Flood-only screening still needs term/regulatory drift monitoring. |
| Data-quality flood thresholds | `config/qualification/qualification_targets.yaml:277` | empty maps/null | NEW flood/DS-002 maps: completeness must record coverage/modernized-FIRM caveats; positional tolerance uses source geometry plus a conservative 30m boundary-near caution band; staleness threshold requires retrieval/effective date and review before live enablement; thematic accuracy is screening-only; cross-source agreement is N/A unless another approved flood source is added; low-confidence extraction threshold N/A for DS-002 structured layer | `FROZEN_TARGET` | Converts empty maps into flood-specific quality gates while preserving no-final-determination caveats. |
| Field surveillance | `config/qualification/qualification_targets.yaml:194` | nulls | NEW periodic review sample `20` or all incidents per 180 days; source drift check `90` days; qualification review `180` days; calibration drift max `0.10`; unknown-rate change max `0.15`; critical containment `60` minutes | `FROZEN_TARGET` | Needed for the flood profile's surveillance plan, even if F overlay result remains `NOT_RUN` until evidence exists. |
| Operations hosted profile | `config/qualification/qualification_targets.yaml:180` | nulls | `N/A_LOCAL_SINGLE_USER_NO_HOSTED_SLO` for availability/error budget/staging/soak/alert delivery; no hosted claim | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | Deployment profile is `LOCAL_SINGLE_USER`, not hosted production. |
| Unit economics | `config/qualification/qualification_targets.yaml:201` | nulls | `N/A_NONCOMMERCIAL_NO_ECONOMICS_CLAIM` for cost/margin/value metrics | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | `commercial_profile_enabled=false`; no valuation/investment/economics claim. |
| Candidate generation | `config/qualification/qualification_targets.yaml:232` | disabled with nulls | `enabled=false`; N/A evidence for recall/ranking/search/cost fields; keep protected/proxy features disallowed | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | Candidate search/ranking is disabled. |
| Financial modeling | `config/qualification/qualification_targets.yaml:250` | disabled with nulls | `enabled=false`; N/A evidence for model error, interval, drift, review, and loss fields | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | No appraisal, valuation, lending, insurance, or investment output. |
| AI/LLM | `config/qualification/qualification_targets.yaml:287` | disabled with nulls | `enabled=false`; keep critical unsupported statements `0`; N/A for latency/cost/variability/case-strata because decision-relevant AI is disabled | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` | No decision-relevant AI output in qualified scope. |
| W-003/W-011 | `config/qualification/qualification_targets.yaml:662`, `config/qualification/qualification_targets.yaml:669` | bindings already `FROZEN`, catalog contracts still `DRAFT` | Keep QFREEZE-1 values; update only catalog parameterization in future freeze | `FROZEN_TARGET` | Reconciles frozen target bindings with catalog-wide predicate 5. |

## Catalog-Wide Disposition Index

The future freeze must disposition all 96 DRAFT non-DIAGNOSTIC catalog contracts. The
60 active/current-profile contracts are active for flood-only P0 unless noted. The 36
inactive contracts must still be dispositioned because `catalog_parameterization_unresolved`
is catalog-wide. The catalog has no flood-specific criterion ID family; flood-only
qualification is therefore controlled by frozen target scope, the flood domain profile,
and DS-002 source coverage rather than by dropping catalog contracts whose text is
not flood-specific.

| Gate | Count | Contract IDs and catalog anchors | Proposed disposition |
|---|---:|---|---|
| P0 | 3 | `P0-014@537`, `P0-017@658`, `P0-025@976` | `FROZEN_TARGET` for P0-014/P0-017; `FROZEN_RUBRIC` for P0-025. |
| Q1 | 9 | `Q1-006@1448`, `Q1-007@1495`, `Q1-008@1540`, `Q1-016@1894`, `Q1-017@1941`, `Q1-019@2035`, `Q1-020@2083`, `Q1-029@2482`, `Q1-034@2709` | `FROZEN_TARGET`, with `Q1-020` also `FROZEN_RUBRIC`. |
| Q2 | 18 | `Q2-001@2937`, `Q2-005@3113`, `Q2-006@3157`, `Q2-007@3203`, `Q2-008@3247`, `Q2-009@3291`, `Q2-010@3337`, `Q2-011@3380`, `Q2-012@3424`, `Q2-014@3516`, `Q2-016@3603`, `Q2-018@3690`, `Q2-021@3820`, `Q2-022@3866`, `Q2-023@3912`, `Q2-027@4087`, `Q2-029@4179`, `Q2-030@4227` | `FROZEN_TARGET` for target-bound rows; `FROZEN_RUBRIC` for human-judgment rows. |
| DB | 5 | `DB-007@6448`, `DB-009@6527`, `DB-013@6684`, `DB-015@6763`, `DB-020@6965` | `FROZEN_TARGET`. |
| R | 2 | `R-008@7290`, `R-009@7330` | `FROZEN_TARGET` and `FROZEN_RUBRIC`. |
| F | 4 | `F-003@7507`, `F-005@7594`, `F-006@7638`, `F-009@7775` | `FROZEN_TARGET` as flood surveillance policy, not a passed F overlay. |
| DQ | 9 | `DQ-002@7997`, `DQ-004@8084`, `DQ-005@8128`, `DQ-006@8174`, `DQ-012@8433`, `DQ-015@8565`, `DQ-019@8740`, `DQ-020@8786`, `DQ-022@8832` | `FROZEN_TARGET` for flood/DS-002 quality maps; `FROZEN_RUBRIC` for DQ-020. |
| S | 1 | `S-009@9290` | `FROZEN_TARGET`. |
| A | 5 | `A-008@10263`, `A-009@10307`, `A-010@10349`, `A-012@10431`, `A-013@10473` | `FROZEN_TARGET` plus `FROZEN_RUBRIC` for judgment rows. |
| M | 5 | `M-004@10672`, `M-005@10717`, `M-007@10798`, `M-009@10879`, `M-015@11120` | `FROZEN_TARGET` plus `FROZEN_RUBRIC` for M-004/M-015. |
| O | 7 | `O-005@11524`, `O-007@11603`, `O-008@11643`, `O-009@11683`, `O-013@11846`, `O-017@12005`, `O-024@12285` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` for local single-user/no-hosted scope. |
| E | 6 | `E-001@12364`, `E-003@12447`, `E-005@12526`, `E-007@12605`, `E-011@12764`, `E-012@12806` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA`; E-012 rubric frozen as disabled-profile N/A. |
| G | 1 | `G-007@13087` | `FROZEN_TARGET` using existing validity days. |
| W | 2 | `W-003@13810`, `W-011@14131` | `FROZEN_TARGET`; QFREEZE-1 bindings already frozen. |
| CG | 6 | `CG-005@14388`, `CG-006@14432`, `CG-007@14476`, `CG-014@14788`, `CG-016@14877`, `CG-017@14921` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` because candidate generation is disabled. |
| FIN | 7 | `FIN-004@15144`, `FIN-005@15188`, `FIN-009@15366`, `FIN-010@15414`, `FIN-011@15458`, `FIN-016@15689`, `FIN-018@15778` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` because financial modeling is disabled and prohibited from scope. |
| AI | 4 | `AI-006@16024`, `AI-010@16187`, `AI-014@16350`, `AI-018@16513` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` because decision-relevant AI is disabled. |
| Q3 | 2 | `Q3-022@5157`, `Q3-023@5201` | `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` for non-expansion P0; owner decision required before Q3 expansion. |

## Proposed Flood Domain Profile

This is a proposed future `config/qualification/domain_profiles/flood.yaml` payload.
It is not created by this packet.

```yaml
schema_version: domain_qualification_profile_v3
domain_id: flood
version: 0.1.0-qfreeze2-proposal
status: FROZEN
scope:
  intents: [rural_land_purchase, homestead_feasibility]
  geographies: [US-NC-Buncombe, US-NC-Chatham, US-NC-Brunswick]
  input_modalities: [parcel_id, address, coordinates, drawn_or_uploaded_geometry, multi_parcel_aoi]
  output_channels: [api_json, web_ui, exported_report]
reference_hierarchy:
- rank: 1
  source_id: DS-002
  name: FEMA National Flood Hazard Layer effective data
  use: primary public-official flood hazard screening reference
  limitations: screening only; no FEMA endorsement; no final floodplain, insurance, lending, survey, engineering, or NFIP determination
issue_taxonomy:
- id: FLOOD_SFHA_INTERSECTION
  criticality: critical
  definition: AOI intersects a FEMA effective special flood hazard area or regulatory floodway feature.
- id: FLOOD_BOUNDARY_NEAR
  criticality: material
  definition: AOI touches or falls within the conservative boundary caution band around a mapped flood feature.
- id: FLOOD_OUTSIDE_MODERNIZED_COVERAGE
  criticality: material_unknown
  definition: FEMA effective digital flood layer is missing, non-modernized, or outside coverage.
- id: FLOOD_SOURCE_FAILURE
  criticality: material_unknown
  definition: DS-002 retrieval, parsing, or lineage proof fails.
severity_rubric:
- level: critical
  rule: SFHA or floodway intersection, source failure masking flood status, or wrong-AOI flood evidence.
- level: material
  rule: boundary-near condition, stale/partial DS-002 metadata, or mapped low/moderate risk needing caveat.
- level: informational
  rule: no mapped effective NFHL feature, with source/date/coverage caveat retained.
confidence_rubric:
- band: high
  rule: DS-002 retrieval succeeded, AOI geometry is unambiguous, and intersection is not boundary-near.
- band: medium
  rule: AOI is boundary-near, source metadata is partial, or geometry normalization needed manual review.
- band: low
  rule: DS-002 coverage is absent/stale/conflicting or source failure is recorded.
source_requirements:
- source_id: DS-002
  required_state: APPROVED
  required_fields: [retrieved_at, source_url, dataset_label, source_version_or_effective_date_when_available, checksum_or_retrieval_manifest, FEMA attribution, no-endorsement caveat]
spatial_temporal_tolerances:
  boundary_caution_band_meters: 30
  no_clearance_if_source_failed: true
  temporal_policy: retrieval timestamp plus FEMA effective date when available; review before live connector enablement or material FEMA terms/service change
unknown_states: [SOURCE_FAILED, OUTSIDE_COVERAGE, STALE, CONFLICTING, UNKNOWN]
metrics:
- id: flood_critical_issue_recall
  threshold: 1.0
- id: flood_material_issue_recall_point_minimum
  threshold: 0.9
- id: flood_source_failure_false_clear_maximum
  threshold: 0
- id: flood_evidence_linkage
  threshold: 1.0
known_exclusions:
- No final legal access, title, survey, buildability, insurance, lending, NFIP, engineering, appraisal, valuation, or investment conclusion.
- No wetland jurisdiction, septic approval, water rights, mineral rights, local flood ordinance, storm-surge, climate projection, or private/local source qualification.
- Preliminary, pending, logo/trademark, private basemap, and third-party FEMA-adjacent layers are excluded unless separately approved.
owner: benjmcd
reviewers: [qualification-reviewer, flood-domain-reviewer]
expires_at: '2027-07-06T00:00:00Z'
frozen_at: '<owner-authorized-freeze-timestamp>'
approved_by: [benjmcd]
invalidation_triggers:
- FEMA terms, service access, dataset label, source rights, preservation, data quality, coverage, or caveat requirements materially change.
- The profile is used outside flood-only DS-002 effective-data screening.
- A source failure, wrong-AOI event, critical false-clearance, or report overclaim is found.
field_surveillance_plan: Review at least 20 flood reports or all critical incidents per 180 days; re-run DS-002 source drift review every 90 days; immediately invalidate on critical false-clearance or source-rights breach.
```

## Applicable Flood Judgment Rubrics

Common frozen rubric structure proposed for every applicable entry:

```yaml
reviewer_independence_required: true
rating_scale: {1: fail, 2: weak, 3: acceptable, 4: strong}
pass_rule: all critical dimensions score 4 and all other dimensions score at least 3; no unresolved critical objection
adjudication_rule: two reviewers; disagreement on any critical dimension goes to independent adjudicator; lower score controls until resolved
calibration_cases:
- id: flood_boundary_near_with_source_caveat
  expected_result: reviewer preserves caution band, unknown/source caveats, and no final determination language
evidence_record_schema: qualification_rubric_review_v1 with criterion_id, reviewer_id, independence_attestation, dimensions, rating, rationale, evidence_refs, adjudication_notes
```

| Criterion | File anchor | Purpose | Reviewer competency | Required dimensions |
|---|---|---|---|---|
| `P0-025` | `config/qualification/judgment_rubrics.yaml:104` | Reviewer competency | Qualification lead plus domain/source-rights familiarity. | competence, independence, conflict disclosure, evidence handling. |
| `Q1-020` | `config/qualification/judgment_rubrics.yaml:113` | Verification-action quality | Flood due-diligence reviewer familiar with DS-002 caveats. | action specificity, owner usability, caveat preservation, no overclaim. |
| `Q2-009` | `config/qualification/judgment_rubrics.yaml:122` | Decision concordance | User-study reviewer independent of implementation. | scenario framing, decision agreement, uncertainty handling, no steering. |
| `Q2-012` | `config/qualification/judgment_rubrics.yaml:131` | Verification-action quality | Same as Q1-020 plus user workflow review. | follow-up clarity, evidence link, caveat retention, comprehension. |
| `Q2-014` | `config/qualification/judgment_rubrics.yaml:140` | Trust calibration | Human-factors reviewer. | confidence alignment, unknown recognition, no false reassurance, no alarmism. |
| `Q2-022` | `config/qualification/judgment_rubrics.yaml:149` | Usability floor | Human-factors/user-study reviewer. | task completion, caveat comprehension, report/API consistency, help burden. |
| `Q2-023` | `config/qualification/judgment_rubrics.yaml:158` | Qualitative defect saturation | User-study lead independent from feature implementation. | defect taxonomy, saturation evidence, critical defect handling, persona coverage. |
| `Q2-029` | `config/qualification/judgment_rubrics.yaml:167` | Cognitive-load control | Human-factors reviewer. | workload score interpretation, caveat density, map/report clarity, escalation clarity. |
| `Q2-030` | `config/qualification/judgment_rubrics.yaml:176` | Comparator honesty | Reviewer familiar with baseline workflow and product non-goals. | comparator fairness, no cherry-picking, time/quality tradeoff, limitations. |
| `R-009` | `config/qualification/judgment_rubrics.yaml:185` | External high-risk review | Qualified external professional or domain expert for new high-risk claims. | scope, independence, authority, conclusions, recorded limitations. |
| `DQ-020` | `config/qualification/judgment_rubrics.yaml:32` | Bias/blind spots | Data-quality reviewer familiar with geospatial source quality. | coverage gaps, measurement bias, source limitations, mitigation/caveats. |
| `A-010` | `config/qualification/judgment_rubrics.yaml:5` | Human-factors anti-dark-pattern review | Accessibility/human-factors reviewer. | no dark patterns, no hidden uncertainty, no deceptive ranking, caveat visibility. |
| `A-012` | `config/qualification/judgment_rubrics.yaml:14` | Reading/comprehension | Accessibility/content reviewer. | persona comprehension, terminology, precision retained, uncertainty understood. |
| `A-013` | `config/qualification/judgment_rubrics.yaml:23` | Map/legend honesty | Map UX/geospatial reviewer. | scale, symbol clarity, overlap handling, source-coverage legend. |
| `M-004` | `config/qualification/judgment_rubrics.yaml:68` | Test coverage adequacy | Senior engineer independent of touched implementation. | unit/integration/DB/regression/negative paths, evidence preservation, risk fit. |
| `M-015` | `config/qualification/judgment_rubrics.yaml:77` | Fresh-agent maintainability | Maintainer not relying on chat history. | discoverability, context routing, invariant preservation, bounded change success. |

Disabled-profile rubric entries `E-012`, `FIN-005`, and `FIN-018` should be frozen only
as `PROFILE_EXCLUDED_WITH_EVIDENCED_NA` unless economics/financial modeling is later
activated by owner decision.

## Deferred Or Blocked Items

These remain blocked or out of scope under the proposal:

- The seven non-flood domain profiles listed above.
- Any source approval beyond `DS-002`.
- Any DS-017, hosted production, Level 10, Bologna, international, candidate-generation,
  financial modeling, decision-relevant AI, valuation, lending, insurance, investment,
  title, survey, water-rights, wetland-jurisdiction, septic, or buildability claim.
- Any P0 `PASS`, because no sealed qualification execution evidence or result file is
  created by this packet.
- Candidate identity if the future freeze does not set the six required candidate
  fields. In that case derived P0 remains `BLOCKED`, even if targets/catalog/rubrics
  are frozen.

## Honest P0 Outcome Statement

This proposal can support a future move from derived `P0 = BLOCKED` to derived
`P0 = NOT_RUN` only if the future owner-authorized freeze also:

1. Sets `qualification_targets.status` to `FROZEN`.
2. Narrows `scope.qualified_domains` to `[flood]`.
3. Adds a complete frozen flood domain profile.
4. Keeps `source_profile_ids: [DS-002]` and does not approve other sources.
5. Freezes every target binding with resolved or evidenced N/A values.
6. Freezes or formally N/A-dispositions all 96 catalog-wide DRAFT non-DIAGNOSTIC
   contracts.
7. Freezes the judgment-rubric registry and all 19 entries, with 16 applicable rubrics
   in full and 3 disabled-profile N/A rubrics.
8. Records candidate identity fields mechanically from the exact candidate artifact and
   catalog/vocabulary/target versions.
9. Leaves committed qualification results as `NOT_RUN` until a separate sealed
   empirical run exists.

If any of those are missing, at least one of the six checker predicates remains true
and P0 remains `BLOCKED`. Even if all are present, the output is `NOT_RUN`, not `PASS`.
