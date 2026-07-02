# Readiness Crosswalk

This document is the human-readable companion to `config/qualification/readiness_crosswalk.yaml`. It maps existing readiness, authority, release, source, security, operations, and spatial gate surfaces to empirical qualification criteria. A mapped readiness surface does not satisfy or pass the mapped criteria; it only identifies which criteria the surface can inform, block, or route into the qualification control plane.

## Mapped Surfaces

| Surface | Role | Criteria | Meaning |
|---|---|---|---|
| `level_9_10_matrix` | feeds_status | `G-011`, `G-016`, `G-017`, `M-014` | Routes Level 9/10 status into the qualification framework. |
| `release_readiness` | deployment_gate | `G-002`, `G-016`, `O-020`, `M-014` | Blocks publication when release governance is incomplete. |
| `private_mvp_readiness` | feeds_status | `Q1-002`, `Q1-003`, `Q1-018`, `Q2-020` | Feeds private MVP claim/evidence/caveat readiness. |
| `source_readiness` | feeds_status | `Q1-012`, `DQ-001`, `DQ-018`, `S-016` | Feeds source registry and source-rights readiness. |
| `source_entitlements` | authority_blocker | `Q1-012`, `S-016`, `R-005`, `DQ-018` | Blocks restricted source use without entitlement evidence. |
| `production_authority_intake` | authority_blocker | `G-021`, `O-020`, `S-005`, `R-005` | Records owner production authority decisions. |
| `authority_evidence_intake` | authority_blocker | `P0-001`, `G-021`, `O-020`, `S-005`, `R-005` | Composes active routing, production authority streams, Bologna ODP gates, empty authority records, and P0 blocked status without recording authority. |
| `authority_follow_on_sequence` | authority_blocker | `P0-001`, `G-021`, `O-020`, `S-005`, `R-005` | Maps first repo-local actions after cited authority while keeping every mapped lane blocked. |
| `bologna_preflight` | authority_blocker | `R-001`, `R-002`, `Q3-027`, `Q3-028` | Blocks Bologna work before non-US scope boundaries are explicit. |
| `bologna_pilot_scope_authority` | authority_blocker | `P0-001`, `R-001`, `R-002`, `G-011` | Blocks pilot work until Bologna product scope is approved. |
| `bologna_source_candidates` | authority_blocker | `DQ-013`, `DQ-017`, `Q3-006`, `R-005` | Blocks corpus work until candidate sources have a governed path. |
| `bologna_source_rights` | authority_blocker | `Q1-012`, `S-016`, `R-005`, `Q3-029` | Blocks source use until source rights are recorded. |
| `bologna_source_authority_intake` | authority_blocker | `P0-001`, `Q3-006`, `S-016`, `R-005` | Records owner approval for Bologna source authority. |
| `bologna_recorded_source_corpus` | authority_blocker | `Q1-003`, `Q1-033`, `DQ-018`, `Q3-020` | Records corpus metadata needed for later report lineage. |
| `bologna_owner_answer_intake` | authority_blocker | `P0-001`, `G-021`, `R-005`, `Q3-029` | Maps owner-answer questions to Bologna authority packets without recording authority. |
| `bologna_odp1_owner_answer_packet` | authority_blocker | `P0-001`, `G-021`, `R-005`, `Q3-029` | Gives the owner a checkable ODP-BOL-001 product/AOI/scope response packet without recording authority. |
| `bologna_odp1_owner_response_gate` | authority_blocker | `P0-001`, `G-021`, `R-005`, `Q3-029` | Checks ODP-BOL-001 owner-response completeness without recording authority. |
| `bol_scope_auth` | authority_blocker | `P0-001`, `G-021`, `R-005`, `Q3-029` | Checks that the current review-only ODP-BOL-001 answer cannot record authority and keeps future authority recording separate from source, corpus, and report work. |
| `bologna_odp2_source_rights_response_gate` | authority_blocker | `P0-001`, `Q1-012`, `Q3-006`, `S-016`, `R-005`, `Q3-029` | Checks ODP-BOL-002 source-authority/source-rights response completeness while preserving the missing ODP-BOL-001 prerequisite. |
| `bologna_odp2_owner_answer_packet` | authority_blocker | `P0-001`, `Q1-012`, `Q3-006`, `S-016`, `R-005`, `Q3-029` | Gives the owner a checkable ODP-BOL-002 source-authority/source-rights response packet without recording authority or unlocking source/corpus/report work. |
| `bologna_odp3_corpus_response_gate` | authority_blocker | `P0-001`, `Q1-003`, `Q1-033`, `DQ-018`, `Q3-020`, `R-005`, `Q3-029` | Checks ODP-BOL-003 recorded-source corpus response completeness while preserving missing ODP-BOL-001/002 prerequisites and all corpus/runtime/report blockers. |
| `bologna_odp4_db_report_proof_response_gate` | authority_blocker | `P0-001`, `Q1-003`, `Q1-033`, `DQ-018`, `Q3-020`, `R-005`, `Q3-029` | Checks ODP-BOL-004 DB report proof response completeness while preserving missing ODP-BOL-001/002/003 prerequisites and all DB/report/API blockers. |
| `qualification_parameterization_backlog` | authority_blocker | `P0-001`, `P0-014`, `P0-017`, `P0-025`, `G-021` | Checks owner-decision and parameterization blocker consistency without resolving those blockers. |
| `checklist_dry_run` | static_guardrail | `Q3-011`, `Q3-015`, `R-001`, `R-009` | Guards jurisdiction terminology and rulepack isolation. |
| `access_control` | static_guardrail | `S-003`, `S-004`, `S-010`, `S-011` | Guards auth, tenancy, and data-boundary assumptions. |
| `threat_proxy_audit` | static_guardrail | `S-015`, `S-024`, `R-003`, `Q2-017` | Guards against proxy or ranking surfaces becoming steering signals. |
| `data_retention` | static_guardrail | `DB-016`, `S-011`, `S-014`, `G-014` | Guards retention and privacy lifecycle boundaries. |
| `deployment_smoke` | deployment_gate | `O-001`, `O-002`, `O-019` | Exercises release-runtime health without claiming hosted authority. |
| `hosted_deployment` | deployment_gate | `O-001`, `O-002`, `O-003`, `O-019`, `S-013` | Blocks hosted deployment until operational prerequisites are present. |
| `image_publication` | deployment_gate | `O-001`, `S-006`, `G-020` | Guards image-publication and container provenance. |
| `release_package` | deployment_gate | `O-001`, `G-010`, `G-016`, `M-014` | Guards release artifacts and package manifests. |
| `observability_readiness` | deployment_gate | `O-012`, `O-013`, `O-014`, `F-001` | Guards observability prerequisites for hosted operations. |
| `alert_rules` | deployment_gate | `O-013`, `O-014`, `S-017`, `F-006` | Guards operational and security alert escalation rules. |
| `cost_monitoring` | static_guardrail | `E-001`, `E-004`, `E-009`, `Q3-023` | Guards economic and quota-monitoring expectations. |
| `performance_baseline` | static_guardrail | `O-008`, `Q1-029`, `Q3-022`, `E-001` | Guards runtime and performance baselines. |
| `spatial_query_plan` | static_guardrail | `DB-006`, `DB-007`, `Q1-013`, `Q3-013` | Guards geometry, CRS, and spatial-query assumptions. |
| `container_scan` | deployment_gate | `S-006`, `O-001` | Feeds container supply-chain deployment checks. |
| `supply_chain` | deployment_gate | `S-006`, `S-023`, `G-020` | Guards dependency and artifact provenance. |
| `security_scan` | deployment_gate | `S-006`, `S-023` | Routes static security-scan CI results into dependency and vulnerability criteria. |
| `backup_restore` | deployment_gate | `DB-012`, `DB-019`, `O-005` | Records backup/restore release proof as recovery gate evidence. |
| `incident_rollback` | static_guardrail | `O-014`, `O-015`, `S-017`, `F-007` | Guards incident-response and rollback readiness. |

## Gaps

The crosswalk records the main criterion groups that have no existing readiness surface capable of satisfying them:

| Gap | Criteria | Reason |
|---|---|---|
| `empirical_acceptance_cases` | `Q1-006`, `Q1-007`, `Q1-008`, `Q1-009`, `Q2-001`, `Q2-005` | Existing readiness gates do not provide sealed empirical acceptance cases or user outcome evidence. |
| `live_field_surveillance` | `F-001`, `F-003`, `F-012` | Readiness configs describe intended monitoring posture but do not create production field surveillance evidence. |
| `disabled_decision_capabilities` | `AI-001`, `CG-001`, `FIN-001` | AI, candidate generation, and financial modeling remain disabled overlays and have no pass-capable readiness surface. |
| `hosted_runtime_evidence` | `O-007`, `O-013`, `O-018` | Hosted-operation criteria need runtime evidence that static readiness configs cannot provide. |

## Orphans

There are no known active readiness, authority, release, source, security, operations, or spatial gate surfaces without a mapped qualification home. The validator derives the expected inventory from the globs and CI/release gate paths in `readiness_crosswalk.yaml` and fails closed if a newly added surface or CI gate wrapper is not mapped or intentionally excluded.
