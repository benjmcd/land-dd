# Owner Decisions

This file records explicit owner decisions that affect qualification state. It is a
repo-local authority ledger, not an agent inference log.

## 2026-06-22 QFREEZE-1 Qualification Freeze

owner=benjmcd
authority=owner directive 2026-06-22
rationale=conservative defaults matching operational reality
reversal=requires a new owner decision + full requalification

Provenance: owner authorization was delivered to the workspace handoff for this
QFREEZE-1 lane on 2026-06-22. This record preserves the decision inside the branch so
the freeze does not depend on a dirty-root or stale worktree inbox file.

Authorized fields:

| Field path | Authorized value | Disposition |
|---|---|---|
| `scope.product_scope_profile` | `BOUNDED_USER_VALIDATED` | FROZEN_TARGET |
| `scope.deployment_profile` | `LOCAL_SINGLE_USER` | FROZEN_TARGET |
| `scope.windows_native_required` | `true` | FROZEN_TARGET |
| `scope.source_profile_ids` | [`DS-002`] | APPROVED_SOURCE_PROFILE |
| `scope.report_contract_version` | `report_run_contract_v1` | FROZEN_TARGET |
| `scope.api_contract_version` | `0.1.0` | FROZEN_TARGET |
| `scope.ruleset_versions.homestead_mvp_v0_1` | `0.1` | FROZEN_TARGET |
| `scope.normalization_schema_version` | `0.1.0-alpha` | FROZEN_TARGET |
| `scope.geometry_pipeline_version` | `0.1.0-alpha` | FROZEN_TARGET |
| `scope.source_snapshot_policy` | `HASHED_RETRIEVAL_MANIFEST_PER_SOURCE` | FROZEN_TARGET |
| `scope.data_as_of_policy` | `SOURCE_DATA_AS_OF_AND_RETRIEVAL_TIMESTAMP_WITH_FRESHNESS_CAVEATS` | FROZEN_TARGET |
| `windows_native.long_path_policy` | `ENABLED` | FROZEN_TARGET |
| `windows_native.supported_windows_versions` | `["Windows 11 (>=22H2)"]` | FROZEN_TARGET |
| `windows_native.supported_powershell_versions` | `["5.1", "7.x"]` | FROZEN_TARGET |
| `windows_native.supported_python_versions` | `["3.12"]` | FROZEN_TARGET |
| `windows_native.supported_docker_desktop_versions` | `["4.x"]` | FROZEN_TARGET |
| `criterion_bindings.W-003` | frozen | FROZEN_TARGET |
| `criterion_bindings.W-011` | frozen | FROZEN_TARGET |

Explicit exclusions:
- no P0 `PASS`;
- no domain-profile rubric freeze;
- no DQ/Q1/Q2/M threshold freeze;
- no criterion-contract pass-rule freeze;
- no judgment-rubric freeze;
- no source approvals beyond DS-002;
- no DS-017 approval;
- no Bologna AOI/source authority;
- no fixture capture;
- no DB seed;
- no report/API/UI/runtime proof;
- no hosted authority.

## 2026-07-06 QFREEZE-2 Flood-Only Qualification Freeze

owner=benjmcd
authority=owner directive 2026-07-06 (interactive session): authorized the flood-only QFREEZE-2 proposal in state/qfreeze2-flood-proposal.md AS-IS, ratifying all EXISTING and NEW proposed values, flood-only qualified scope.
rationale=conservative defaults matching operational reality
reversal=requires a new owner decision + full requalification

Provenance: owner authorization delivered to the workspace handoff for this QFREEZE-2 lane on 2026-07-06; ratified content = state/qfreeze2-flood-proposal.md (merged as PR #190, origin/main 2447349a). Preserve the authorization in-branch so the freeze does not depend on a transient inbox.

Validator-compatibility correction: frozen flood unknown_states = [SOURCE_FAILED, OUTSIDE_COVERAGE, STALE, CONFLICTING]. The ratified packet catch-all UNKNOWN was removed under the same owner directive 2026-07-06 as a validator-compatibility correction; benjmcd authorized the flood profile with fail-closed unknown handling, and this preserves that intent while changing no threshold, scope, or safety posture.

Authorized fields:

| Field path | Authorized value | Disposition |
|---|---|---|
| `qualification_targets.status` | `FROZEN` | FROZEN_TARGET |
| `qualification_targets.frozen_at` | `2026-07-06T20:26:43Z` | FROZEN_TARGET |
| `qualification_targets.approved_by` | [`benjmcd`] | FROZEN_TARGET |
| `scope.qualified_domains` | [`flood`] | FROZEN_TARGET |
| `scope.explicitly_unqualified_domains` | prior exclusions plus `wetlands, slope_terrain, soils_septic_proxy, physical_road_access_proxy, zoning_context, environmental_context, source_availability_and_conflict` | PROFILE_EXCLUDED_WITH_EVIDENCED_NA |
| `protocol.confidence_level` | `0.95` | FROZEN_TARGET |
| `protocol.pre_adjudication_reliability_minimum` | `0.7` | FROZEN_TARGET |
| `protocol.primary_analysis_method` | `stratified pre-registered acceptance analysis using exact or Wilson intervals` | FROZEN_TARGET |
| `protocol.cluster_handling_method` | `AOI-level clustered denominators` | FROZEN_TARGET |
| `protocol.multiple_comparison_method` | `Holm-Bonferroni for secondary families` | FROZEN_TARGET |
| `protocol.missing_data_method` | `fail-closed unknown, no imputation` | FROZEN_TARGET |
| `protocol.practical_effect_thresholds` | `zero critical false clearances plus material-effect floors` | FROZEN_TARGET |
| `q1.*` | existing recall/linkage floors plus calibration/runtime values from QFREEZE-2 packet | FROZEN_TARGET |
| `q2.*` | existing user-utility floors plus trust/error/accessibility/help/workload values from QFREEZE-2 packet | FROZEN_TARGET |
| `q3.lane_incremental_cost_multiplier_maximum` | `1.25` for inactive non-expansion disposition | PROFILE_EXCLUDED_WITH_EVIDENCED_NA |
| `database.*` | PostgreSQL 16.x, PostGIS 3.x, repo-locked runtime, latency/connection/volume/RPO/RTO/PITR/migration/headroom values from QFREEZE-2 packet | FROZEN_TARGET |
| `security_privacy.rate_limit_and_quota_profile` | local single-user API-key quota profile with bounded connector/report jobs, AOI limits, no uncontrolled retries, zero unresolved applicable critical/high vulnerabilities | FROZEN_TARGET |
| `accessibility.supported_browser_os_matrix` | Windows 11 current Chrome/Edge/Firefox plus responsive mobile viewport smoke | FROZEN_TARGET |
| `accessibility.reading_level_or_comprehension_targets_by_persona` | correct caveat/unknown interpretation required | FROZEN_TARGET |
| `maintainability.*` | mutation/flaky floors plus approved complexity/size and thin startup-context targets from QFREEZE-2 packet | FROZEN_TARGET |
| `operations.*` | `N/A_LOCAL_SINGLE_USER_NO_HOSTED_SLO` | PROFILE_EXCLUDED_WITH_EVIDENCED_NA |
| `field_surveillance.*` | sample 20/all incidents per 180 days, source drift 90 days, qualification review 180 days, calibration drift 0.10, unknown-rate change 0.15, containment 60 minutes | FROZEN_TARGET |
| `unit_economics.*` | `N/A_NONCOMMERCIAL_NO_ECONOMICS_CLAIM` | PROFILE_EXCLUDED_WITH_EVIDENCED_NA |
| `candidate_generation.*` | disabled; N/A evidence for recall/ranking/search/cost fields; protected/proxy features disallowed | PROFILE_EXCLUDED_WITH_EVIDENCED_NA |
| `financial_modeling.*` | disabled; N/A evidence for model error, interval, drift, review, and loss fields | PROFILE_EXCLUDED_WITH_EVIDENCED_NA |
| `data_quality.*` | flood/DS-002 quality maps for coverage caveats, 30m caution band, retrieval/effective-date review, screening-only thematic accuracy, cross-source N/A, structured-layer low-confidence N/A | FROZEN_TARGET |
| `regulatory_professional_scope.change_monitoring_frequency_days` | `90` | FROZEN_TARGET |
| `ai_llm.*` | disabled; critical unsupported statements `0`; N/A latency/cost/variability/case-strata | PROFILE_EXCLUDED_WITH_EVIDENCED_NA |
| `criterion_bindings.*` | `84` bindings frozen: P0-014, P0-017, Q1-006, Q1-007, Q1-008, Q1-016, Q1-017, Q1-019, Q1-020, Q1-029, Q1-034, Q2-001, Q2-005, Q2-006, Q2-007, Q2-008, Q2-009, Q2-010, Q2-011, Q2-012, Q2-014, Q2-016, Q2-018, Q2-021, Q2-022, Q2-027, Q2-029, Q3-022, Q3-023, DQ-002, DQ-004, DQ-005, DQ-006, DQ-012, DQ-015, DQ-019, DQ-022, DB-007, DB-009, DB-013, DB-015, DB-020, S-009, A-008, A-009, A-012, M-005, M-007, M-009, O-005, O-007, O-008, O-009, O-013, O-017, O-024, E-001, E-003, E-005, E-007, E-011, G-007, R-008, F-003, F-005, F-006, F-009, CG-005, CG-006, CG-007, CG-014, CG-016, CG-017, FIN-004, FIN-009, FIN-010, FIN-011, FIN-016, AI-006, AI-010, AI-014, AI-018, W-003, W-011 | FROZEN_TARGET_OR_EVIDENCED_NA |
| `domain_profiles.flood` | frozen flood-only DS-002 profile with corrected four-state unknown_states list | FROZEN_DOMAIN_PROFILE |
| `criterion_catalog.parameterization_status` | all `391` non-DIAGNOSTIC contracts frozen | FROZEN_TARGET_OR_RUBRIC_OR_EVIDENCED_NA |
| `judgment_rubrics.status` | `FROZEN` | FROZEN_RUBRIC |
| `judgment_rubrics.criteria` | all `19` entries frozen: A-010, A-012, A-013, DQ-020, E-012, FIN-005, FIN-018, M-004, M-015, P0-025, Q1-020, Q2-009, Q2-012, Q2-014, Q2-022, Q2-023, Q2-029, Q2-030, R-009 | FROZEN_RUBRIC_OR_PROFILE_EXCLUDED_WITH_EVIDENCED_NA |
| `state.EMPIRICAL_QUALIFICATION_STATUS.candidate` | commit `2447349aa06d11ccb9e0d4ab01433c7c2c0a4b0c`, artifact digest `sha256:457412c1d29543f89be7c5d2c9d521bd999ae1395df5885ddd902865057bb978`, protocol `qualification_protocol_v3`, targets `0.1.0-draft`, vocabulary `qualification_vocabulary_v3`, catalog digest `sha256:a6490c75627a7d5bd05e6ed055de7f5a3e84408957a6e00a4dfa00fd4ebb0f55` | CANDIDATE_IDENTITY |
| `state.EMPIRICAL_QUALIFICATION_STATUS.qualifications.p0.status` | `NOT_RUN` only if derived by checker; never `PASS` | STATUS_DERIVED_NOT_PASS |

Explicit exclusions:
- no P0 `PASS`;
- no source approval beyond `DS-002`;
- no non-flood domain qualification;
- no DS-017 approval;
- no hosted-production, Level 10, or Bologna authority;
- no final legal access, title, survey, buildability, insurance, lending, NFIP, engineering, appraisal, valuation, or investment conclusion;
- no wetland jurisdiction, septic approval, water rights, mineral rights, local flood ordinance, storm-surge, climate projection, or private/local source qualification;
- no candidate-generation, financial modeling, decision-relevant AI, commercial economics, valuation, lending, insurance, investment, protected-class, demographic, neighborhood desirability, or residential steering feature qualification;
- P0 remains not-PASS until a separate sealed evidence run and result file satisfy the empirical qualification protocol.
