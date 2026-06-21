# Project Parameterization Blockers

**Framework version:** 3.0

This register distinguishes framework completeness from project-specific readiness.
The framework is structurally valid, but P0 must remain blocked until every active item below is frozen.

## Current selected scope

```yaml
product_scope_profile: BOUNDED_USER_VALIDATED
deployment_profile: LOCAL_SINGLE_USER
windows_native_required: true
candidate_generation_enabled: false
financial_modeling_enabled: false
ai_llm_enabled_for_decision_relevant_output: false
commercial_profile_enabled: false
```

## Readiness summary

| Blocker class | Count/status | P0 effect |
|---|---:|---|
| Active gates | 12 | Must be fully parameterized |
| Active DRAFT criterion contracts | 60 | BLOCKED |
| Active DRAFT/unresolved target bindings | 51 | BLOCKED |
| Active DRAFT judgment rubrics | 16 | BLOCKED |
| Qualified-domain profiles still DRAFT | 8 | BLOCKED |
| Approved source profiles selected | 0 | BLOCKED |
| Unresolved scope/version fields | 6 plus ruleset versions | BLOCKED |
| Inactive/conditional DRAFT contracts | 36 | Do not block current profile |

## Active gates

```text
A
DB
DQ
G
IR
M
P0
Q1
Q2
R
S
W
```

## Active criterion contracts requiring freeze

### A — 5

```text
A-008
A-009
A-010
A-012
A-013
```

### DB — 5

```text
DB-007
DB-009
DB-013
DB-015
DB-020
```

### DQ — 9

```text
DQ-002
DQ-004
DQ-005
DQ-006
DQ-012
DQ-015
DQ-019
DQ-020
DQ-022
```

### G — 1

```text
G-007
```

### M — 5

```text
M-004
M-005
M-007
M-009
M-015
```

### P0 — 3

```text
P0-014
P0-017
P0-025
```

### Q1 — 9

```text
Q1-006
Q1-007
Q1-008
Q1-016
Q1-017
Q1-019
Q1-020
Q1-029
Q1-034
```

### Q2 — 18

```text
Q2-001
Q2-005
Q2-006
Q2-007
Q2-008
Q2-009
Q2-010
Q2-011
Q2-012
Q2-014
Q2-016
Q2-018
Q2-021
Q2-022
Q2-023
Q2-027
Q2-029
Q2-030
```

### R — 2

```text
R-008
R-009
```

### S — 1

```text
S-009
```

### W — 2

```text
W-003
W-011
```

## Active target bindings

Each row must change to `FROZEN`, and every referenced value must be resolved.

| Criterion | Binding status | Unresolved references |
|---|---|---|
| `P0-014` | `DRAFT` | none |
| `P0-017` | `DRAFT` | `protocol.practical_effect_thresholds` |
| `Q1-006` | `DRAFT` | none |
| `Q1-007` | `DRAFT` | none |
| `Q1-008` | `DRAFT` | none |
| `Q1-016` | `DRAFT` | `q1.confidence_expected_calibration_error_maximum` |
| `Q1-017` | `DRAFT` | `q1.severity_weighted_agreement_minimum` |
| `Q1-019` | `DRAFT` | none |
| `Q1-020` | `DRAFT` | none |
| `Q1-029` | `DRAFT` | `q1.p95_report_runtime_seconds`, `q1.p95_report_memory_mb` |
| `Q1-034` | `DRAFT` | none |
| `Q2-001` | `DRAFT` | none |
| `Q2-005` | `DRAFT` | none |
| `Q2-006` | `DRAFT` | none |
| `Q2-007` | `DRAFT` | none |
| `Q2-008` | `DRAFT` | none |
| `Q2-009` | `DRAFT` | none |
| `Q2-010` | `DRAFT` | none |
| `Q2-011` | `DRAFT` | none |
| `Q2-012` | `DRAFT` | none |
| `Q2-014` | `DRAFT` | `q2.trust_calibration_error_maximum` |
| `Q2-016` | `DRAFT` | `q2.error_recovery_success_minimum` |
| `Q2-018` | `DRAFT` | `q2.accessibility_task_completion_minimum` |
| `Q2-021` | `DRAFT` | `q2.support_help_requests_median_maximum` |
| `Q2-022` | `DRAFT` | none |
| `Q2-027` | `DRAFT` | none |
| `Q2-029` | `DRAFT` | `q2.maximum_workload_score` |
| `DQ-002` | `DRAFT` | `data_quality.completeness_thresholds_by_source_domain` |
| `DQ-004` | `DRAFT` | `data_quality.positional_accuracy_tolerances_by_source_domain` |
| `DQ-005` | `DRAFT` | `data_quality.staleness_thresholds_by_source_domain` |
| `DQ-006` | `DRAFT` | `data_quality.thematic_accuracy_thresholds_by_source_domain` |
| `DQ-012` | `DRAFT` | `data_quality.cross_source_agreement_thresholds_by_domain` |
| `DQ-015` | `DRAFT` | `data_quality` |
| `DQ-019` | `DRAFT` | `data_quality` |
| `DQ-022` | `DRAFT` | `data_quality.low_confidence_extraction_review_threshold` |
| `DB-007` | `DRAFT` | `database.p95_core_query_latency_ms` |
| `DB-009` | `DRAFT` | `database.max_connection_budget` |
| `DB-013` | `DRAFT` | `database.rpo_minutes`, `database.rto_minutes` |
| `DB-015` | `DRAFT` | `database.representative_data_volume_multiplier`, `database.large_migration_lock_or_downtime_budget_seconds` |
| `DB-020` | `DRAFT` | `database.capacity_headroom_minimum` |
| `S-009` | `DRAFT` | `security_privacy.rate_limit_and_quota_profile` |
| `A-008` | `DRAFT` | `accessibility.supported_browser_os_matrix` |
| `A-009` | `DRAFT` | none |
| `A-012` | `DRAFT` | `accessibility.reading_level_or_comprehension_targets_by_persona` |
| `M-005` | `DRAFT` | none |
| `M-007` | `DRAFT` | none |
| `M-009` | `DRAFT` | `maintainability.maximum_approved_complexity_or_size_thresholds` |
| `G-007` | `DRAFT` | none |
| `R-008` | `DRAFT` | `regulatory_professional_scope.change_monitoring_frequency_days` |
| `W-003` | `DRAFT` | `windows_native.long_path_policy` |
| `W-011` | `DRAFT` | `windows_native.supported_windows_versions`, `windows_native.supported_powershell_versions`, `windows_native.supported_python_versions`, `windows_native.supported_docker_desktop_versions` |

## Active judgment rubrics

```text
A-010
A-012
A-013
DQ-020
M-004
M-015
P0-025
Q1-020
Q2-009
Q2-012
Q2-014
Q2-022
Q2-023
Q2-029
Q2-030
R-009
```

Every rubric must define reviewer competence, dimensions, scale, pass rule, adjudication, calibration cases, and evidence schema.

## Domain profiles

- `flood`: `DRAFT`; freeze source hierarchy, issue taxonomy, critical/material definitions, severity/confidence rubrics, tolerances, exclusions, metrics, reviewers, and surveillance plan.
- `wetlands`: `DRAFT`; freeze source hierarchy, issue taxonomy, critical/material definitions, severity/confidence rubrics, tolerances, exclusions, metrics, reviewers, and surveillance plan.
- `slope_terrain`: `DRAFT`; freeze source hierarchy, issue taxonomy, critical/material definitions, severity/confidence rubrics, tolerances, exclusions, metrics, reviewers, and surveillance plan.
- `soils_septic_proxy`: `DRAFT`; freeze source hierarchy, issue taxonomy, critical/material definitions, severity/confidence rubrics, tolerances, exclusions, metrics, reviewers, and surveillance plan.
- `physical_road_access_proxy`: `DRAFT`; freeze source hierarchy, issue taxonomy, critical/material definitions, severity/confidence rubrics, tolerances, exclusions, metrics, reviewers, and surveillance plan.
- `zoning_context`: `DRAFT`; freeze source hierarchy, issue taxonomy, critical/material definitions, severity/confidence rubrics, tolerances, exclusions, metrics, reviewers, and surveillance plan.
- `environmental_context`: `DRAFT`; freeze source hierarchy, issue taxonomy, critical/material definitions, severity/confidence rubrics, tolerances, exclusions, metrics, reviewers, and surveillance plan.
- `source_availability_and_conflict`: `DRAFT`; freeze source hierarchy, issue taxonomy, critical/material definitions, severity/confidence rubrics, tolerances, exclusions, metrics, reviewers, and surveillance plan.

## Source profiles

`scope.source_profile_ids` is empty. Before P0:

1. Select the exact source set.
2. Create one source-quality profile per source.
3. Resolve authority, rights, commercial/cache/retain/export/AI permissions, preservation mode, coverage, freshness, quality, normalization, failure behavior, retirement, enabled operations, and enforcement controls.
4. Set each selected profile to `APPROVED`.

## Scope/version blockers

```text
report_contract_version
api_contract_version
normalization_schema_version
geometry_pipeline_version
source_snapshot_policy
data_as_of_policy
ruleset_versions
```

## Conditional work that does not block the current profile

- `CG` remains blocked but inapplicable while candidate generation/ranking is disabled.
- `FIN` remains blocked but inapplicable while financial/valuation/investment output is disabled.
- `AI` remains blocked but inapplicable while decision-relevant AI is disabled.
- `E` remains blocked but inapplicable while no commercial/economic-viability claim is made.
- `Q3A/Q3B/Q3C`, `O`, and `F` do not block the current bounded user-validation profile.

## Allowed dispositions

Every blocker must receive exactly one controlled disposition:

```text
FROZEN_TARGET
FROZEN_RUBRIC
FROZEN_DOMAIN_PROFILE
APPROVED_SOURCE_PROFILE
PROFILE_EXCLUDED_WITH_EVIDENCED_NA
BLOCKED_WITH_OWNER_AND_DECISION
REMOVED_THROUGH_REVIEWED_FRAMEWORK_CHANGE
```

Silent deletion, post-result threshold changes, or broadening/narrowing scope after unsealing invalidate the run.
