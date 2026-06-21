# Framework Adequacy Gates

## Purpose

This file tests the qualification framework itself. It prevents the framework from becoming an impressive but unexecutable policy document.

Statuses:

```text
PASS
FAIL
BLOCKED
N/A
```

A framework release is structurally adequate only when every `FRAMEWORK` gate passes. A project qualification run remains blocked until every applicable `INSTANTIATION` gate passes.

## Framework gates

| ID | Type | PASS condition | FAIL condition | v3 result |
|---|---|---|---|---|
| `FA-001` | FRAMEWORK | Implementation maturity, empirical validity, deployment quality, and expansion readiness are separate axes. | One axis is used as a proxy for another. | PASS |
| `FA-002` | FRAMEWORK | Product-scope and deployment profiles explicitly determine applicable gates. | Applicability depends on ad hoc interpretation. | PASS |
| `FA-003` | FRAMEWORK | Bounded production does not require unrelated international expansion proof. | Non-US testing blocks an otherwise bounded production claim. | PASS |
| `FA-004` | FRAMEWORK | International architecture probes cannot imply jurisdictional operational qualification. | One probe is treated as worldwide coverage. | PASS |
| `FA-005` | FRAMEWORK | Every criterion has a unique machine-readable ID and contract. | Criteria exist only in prose or duplicate IDs exist. | PASS |
| `FA-006` | FRAMEWORK | PASS/FAIL/BLOCKED/N/A semantics are schema-checked. | Illegal PASS states validate. | PASS |
| `FA-007` | FRAMEWORK | Invariants, profile-required, targeted, judgment-rubric, and diagnostic requirements are distinct. | Every desirable practice is treated as equally non-waivable. | PASS |
| `FA-008` | FRAMEWORK | Undefined qualitative terms are prohibited and controlled vocabulary exists. | “Material,” “appropriate,” or similar terms are evaluator-defined after results. | PASS |
| `FA-009` | FRAMEWORK | Numeric targets and rubrics freeze before unsealing. | Targets may be chosen after results. | PASS |
| `FA-010` | FRAMEWORK | Aggregate metrics cannot hide critical subgroup failures. | Pooled success can qualify a failed geography/domain/persona. | PASS |
| `FA-011` | FRAMEWORK | Sample, power/precision, denominator, exclusion, missing-data, and uncertainty rules are preregistered. | Convenient case selection or denominator changes are allowed. | PASS |
| `FA-012` | FRAMEWORK | Acceptance contamination, reviewer independence, competency, blinding, and adjudication are controlled. | Implementers can certify their own tuned holdout. | PASS |
| `FA-013` | FRAMEWORK | AOI/address/APN/geocode/parcel-version identity has explicit qualification. | A report about the wrong place can still pass. | PASS |
| `FA-014` | FRAMEWORK | Geospatial data quality follows explicit completeness, consistency, positional, temporal, thematic, and lineage measures. | Source return is treated as proof of quality. | PASS |
| `FA-015` | FRAMEWORK | PostgreSQL/PostGIS integrity, transactionality, migration, query, concurrency, backup, and PITR are independently gated. | Database non-fragility is assumed from unit tests. | PASS |
| `FA-016` | FRAMEWORK | Source rights, retention, export, AI use, preservation, retirement, and terms changes are gated. | Publicly accessible data is treated as unrestricted. | PASS |
| `FA-017` | FRAMEWORK | Security, privacy, misuse, sensitive geospatial data, and isolation are profile-aware. | Security scope is generic or multi-tenancy is assumed. | PASS |
| `FA-018` | FRAMEWORK | Accessibility includes web tasks, maps, exports, keyboard, assistive technology, and uncertainty presentation. | Conformance relies only on automated scans. | PASS |
| `FA-019` | FRAMEWORK | Human utility tests first-use, persona strata, comparator honesty, trust, unknown recognition, and correction. | Faster task time alone qualifies utility. | PASS |
| `FA-020` | FRAMEWORK | Modularity is tested through dependency direction, substitution, removal, registration, and regression—not LOC alone. | A gameable code-location ratio is the primary architecture gate. | PASS |
| `FA-021` | FRAMEWORK | Hosted operations include real deployment, load, soak, outage, alert, recovery, recall, and restore drills. | Static runbooks/configuration count as operations proof. | PASS |
| `FA-022` | FRAMEWORK | Economic gates are conditional on commercial claims and include total cost and measured user value. | Economics unnecessarily blocks a noncommercial release or ignores vendor/labor cost. | PASS |
| `FA-023` | FRAMEWORK | Regulatory/professional-scope applicability is explicit and jurisdiction/profile based. | Generic disclaimers are treated as compliance. | PASS |
| `FA-024` | FRAMEWORK | AI controls activate only when probabilistic output affects the released scope. | AI criteria are either omitted when needed or rigidly required when unused. | PASS |
| `FA-025` | FRAMEWORK | Post-release field surveillance can invalidate prior qualification. | Pre-release PASS remains permanent after drift/incidents. | PASS |
| `FA-026` | FRAMEWORK | Change classes map to affected gates and silence defaults to invalidation. | Gate validity is decided informally. | PASS |
| `FA-027` | FRAMEWORK | Evidence-preservation modes reconcile reproducibility with source-license restrictions. | Qualification requires prohibited data retention or accepts unauditable evidence. | PASS |
| `FA-028` | FRAMEWORK | Small teams may combine accountable roles while independence-sensitive review remains independent. | The process either demands an enterprise headcount or permits total self-certification. | PASS |
| `FA-029` | FRAMEWORK | Detailed evidence is routed and excluded from always-loaded agent context. | Governance itself causes context bloat. | PASS |
| `FA-030` | FRAMEWORK | The framework states residual limits and never claims metaphysical completeness. | Unknown unknowns are implicitly treated as passed. | PASS |
| `FA-031` | FRAMEWORK | Windows-native operation is qualified across PowerShell, paths, case behavior, line endings, Docker Desktop, OneDrive/sync boundaries, file locks, CI, versions, and credentials. | Windows support is documentation-only. | PASS |
| `FA-032` | FRAMEWORK | Automatic candidate generation/ranking has separate universe, recall, false-exclusion, stability, provenance, anti-steering, alert, and performance gates. | Analysis accuracy is used as proof of search/ranking quality. | PASS |
| `FA-033` | FRAMEWORK | Financial/valuation/investment behavior has conditional leakage, uncertainty, drift, fairness, decision-loss, review, applicability, and correction gates. | Generic diligence qualification is used to authorize financial advice or AVM-like output. | PASS |
| `FA-034` | FRAMEWORK | Document/OCR/table/figure extraction retains resolvable anchors and routes low-confidence output to review/unknown. | Parsed text is accepted as evidence without extraction qualification. | PASS |
| `FA-035` | FRAMEWORK | Every claimed domain and active source has a frozen/approved profile bound to P0. | Generic architecture/source registry substitutes for exact domain/source readiness. | PASS |
| `FA-036` | FRAMEWORK | Report, API, normalization, geometry, ruleset, source snapshot, and data-as-of semantics are frozen independently of the code commit. | Candidate identity is underspecified. | PASS |
| `FA-037` | FRAMEWORK | Validator behavior has adversarial executable self-tests for classification outrun, conditional mismatch, catalog drift, and false P0. | The control plane self-certifies from schema appearance. | PASS |
| `FA-038` | FRAMEWORK | Conditional gates do not block disabled capabilities, while enabled capabilities cannot escape their gates. | The framework is either unnecessarily rigid or permits capability bypass. | PASS |
| `FA-039` | FRAMEWORK | Non-US representation includes locally relevant tenure, authority, rights, locale, CRS, and planning concepts without forcing a US parcel model. | Q3C tests only translated US concepts. | PASS |
| `FA-040` | FRAMEWORK | Source operations are checked against commercial/cache/retain/export/display/AI rights and approved preservation mode. | A source profile is “approved” despite an operational rights conflict. | PASS |

## Project-instantiation gates

These are expected to be blocked until the project owner freezes them.

| ID | PASS condition | FAIL/BLOCKED condition | Current example status |
|---|---|---|---|
| `FI-001` | Product-scope and deployment profiles are selected and approved. | No exact profile. | PASS in example, subject to owner approval |
| `FI-002` | Every applicable TARGETED criterion has a frozen target. | Any required target is null/TBD. | BLOCKED |
| `FI-003` | Every applicable JUDGMENT_RUBRIC criterion has a frozen rubric and reviewer role. | Generic judgment only. | BLOCKED |
| `FI-004` | Domain qualification profiles are frozen for every claimed domain. | Domain-level reference/severity/confidence remains draft. | BLOCKED |
| `FI-005` | Source-quality/rights/preservation profiles are approved for every production source. | Any required source is unknown/unapproved. | BLOCKED |
| `FI-006` | Protocol, cohort, reviewers, statistical plan, and evidence location are frozen. | Acceptance design remains draft. | BLOCKED |
| `FI-007` | Production SLO/RTO/RPO/capacity/security/accessibility targets are frozen for a production claim. | Production targets remain null. | BLOCKED |
| `FI-008` | Criterion catalog entries applicable to P0 are `FROZEN`. | Any applicable non-diagnostic contract remains `DRAFT`. | BLOCKED |
| `FI-009` | Candidate commit/tag/digest is fixed. | Candidate changes during execution. | BLOCKED until execution |
| `FI-010` | Independent execution and evidence archive are provisioned. | Qualification depends on ordinary dev access or chat history. | BLOCKED until execution |
| `FI-011` | Exact report/API/normalization/geometry/ruleset/source-snapshot/data-as-of versions are frozen. | Candidate semantics remain null or implicit. | BLOCKED |
| `FI-012` | Windows support/version/long-path/line-ending/credential targets are frozen and proven in Windows CI. | Windows-native requirements remain partially null or unexecuted. | BLOCKED |
| `FI-013` | Document-extraction types, languages, confidence/review thresholds, and anchors are frozen for enabled extraction. | Parsed zoning/legal evidence lacks an acceptance profile. | BLOCKED |
| `FI-014` | Conditional CG/FIN/AI/E applicability matches actual enabled product behavior. | A capability is hidden from its gate or a disabled capability blocks release. | PASS for current disabled CG/FIN/AI/E flags; continuously enforced |
| `FI-015` | Every source-profile operation is compatible with approved rights and has an admissible evidence-preservation mode. | Any selected source/operation remains unknown or conflicting. | BLOCKED |

## Overall adversarial result

```text
Framework structural adequacy: PASS
Project-specific qualification readiness: BLOCKED
Reason: 60 active criterion contracts, 51 active target bindings, 16 active judgment rubrics,
8 domain profiles, the exact source set, scope/version fields, Windows targets, candidate identity,
and empirical execution evidence are intentionally not yet frozen.
```

That is the correct result. A document can be structurally adequate while an actual product qualification remains blocked.
