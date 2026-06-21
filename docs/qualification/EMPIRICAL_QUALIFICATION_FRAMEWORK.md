# Empirical Qualification Framework

**Version:** 3.0  
**Status:** Canonical adversarially revised qualification framework  
**Recommended repo path:** `docs/qualification/EMPIRICAL_QUALIFICATION_FRAMEWORK.md`

## 1. Purpose

This document defines the release barriers needed to determine whether the land-diligence platform is:

- functionally correct for its declared scope;
- safe against materially misleading land-screening output;
- useful to intended users;
- modular and extensible across sources and jurisdictions;
- resilient to missing, stale, malformed, restricted, or conflicting data;
- reproducible, testable, maintainable, secure, private, accessible, scalable, and economically operable;
- ready for a bounded private MVP, expansion, release candidate, or production-grade claim.

It supplements the repository milestone map. The milestone map measures implementation maturity. This framework measures whether implemented behavior survives empirical and operational qualification.

A large test count, passing fixtures, a working UI, or a completed implementation plan is not enough. A qualification claim is valid only when every required criterion passes against the exact candidate artifact and a complete evidence package exists.

---

## 2. Non-certainty statement

No static document can guarantee that every future hazard, jurisdictional rule, data failure, user behavior, attack, or operational condition has been anticipated. Therefore this framework does not claim metaphysical completeness.

It is intended to be **exhaustive for the currently declared product scope and known risk classes**. It addresses unknown unknowns by requiring:

- independent review;
- sealed acceptance cohorts;
- adversarial and fault-injection testing;
- residual-risk registration;
- incident and discrepancy feedback loops;
- qualification expiry and invalidation;
- periodic requalification;
- explicit scope and claim boundaries.

Any untested or unresolved material dimension is `BLOCKED`, not implicitly passed.

---

## 3. Qualification architecture

The complete framework has four layers.

```text
P0   Protocol integrity and admissibility
     -> must pass before empirical results support a claim

Q1   Blind real-parcel accuracy and safety
Q2   Comparative user decision utility
     -> bounded empirical validity

Q3A  Cross-state integration
Q3B  Restricted/unavailable-source degradation
Q3C  Non-US representation probe
     -> optional expansion-readiness evidence, not a bounded-production prerequisite

DQ   Geospatial and source-data quality
IR   Input resolution, cadastral identity, and AOI integrity
DB   PostgreSQL/PostGIS integrity and operability
S    Security, privacy, rights, compliance, and misuse resistance
A    Accessibility and human factors
M    Maintainability, modularity, and test effectiveness
O    Operations, reliability, recovery, and scalability
R    Regulatory and professional-scope applicability
F    Field surveillance, drift, correction, and recall
W    Windows-native development/operator environment
G    Governance, release, evidence, expiry, and invalidation
     -> cross-cutting overlays selected by the exact product/deployment profile

E    Economic/resource viability
CG   Candidate generation, search, filtering, ranking, and alerts
FIN  Valuation, return, liquidity, and investment/financial outputs
AI   AI/LLM-assisted behavior
     -> conditional overlays activated only when the corresponding capability or claim is enabled

Bounded production classification
     -> P0 + Q1 + Q2 when user utility is claimed
        + every applicable cross-cutting/conditional overlay PASS
        + no requirement to pass Q3 unless an expansion claim is made
```

The empirical cases test distinct claims:

1. **Q1:** Is the bounded screening output materially correct and safe?
2. **Q2:** Does it improve the intended users' bounded decisions?
3. **Q3A/B/C:** Can the architecture expand or degrade safely without rewriting or weakening the core?

The overlays prevent empirical, operational, expansion, and commercial claims from being conflated.

---


## 3A. Orthogonal qualification axes

Qualification is evaluated on separate axes. Passing one axis cannot compensate for failure on another.

```text
Implementation maturity
  measured by MILESTONE_MAP.md

Bounded empirical validity
  P0 + Q1 + Q2 for an exact geography, intent, domain set, input mode, source set,
  report version, and user population

Deployment quality
  DQ + IR + DB + S + A + M + O + R + F + W, with E, CG, FIN, and AI when applicable

Expansion readiness
  Q3A cross-state integration
  Q3B restricted/unavailable-source degradation
  Q3C non-US architecture probe
```

A bounded production release does **not** require a non-US probe. Conversely, a successful non-US architecture probe does not establish production readiness.

## 3B. Qualification profiles

Before testing, select one product-scope profile and one deployment profile. The selection determines which gates are required and which criteria may be `N/A`.

### Product-scope profiles

| Profile | Permitted claim | Required empirical gates |
|---|---|---|
| `REPO_PROVEN` | The implementation passes its governed fixture/regression suite. | Milestone map only |
| `BOUNDED_SCREENING_VALIDATED` | The frozen bounded land-screening scope demonstrated materially safe and accurate behavior. | P0 + Q1 |
| `BOUNDED_USER_VALIDATED` | Intended users demonstrated improved bounded screening utility. | P0 + Q1 + Q2 |
| `BOUNDED_PRODUCTION_LOCAL` | The frozen bounded product is production-grade for its supported local/single-user environment. | Bounded user validation + applicable production overlays |
| `BOUNDED_PRODUCTION_SINGLE_TENANT` | The frozen bounded product is production-grade for one hosted organization/controlled beta. | Bounded user validation + applicable hosted production overlays |
| `BOUNDED_PRODUCTION_MULTI_TENANT` | The frozen bounded product is production-grade for public multi-tenant operation. | Single-tenant production + multi-tenant isolation/authorization controls |
| `US_EXPANSION_READY` | The architecture demonstrated cross-state extension and restricted-source degradation. | P0 + Q1 + Q2 + Q3A + Q3B |
| `GLOBAL_ARCHITECTURE_PROBED` | The architecture also survived a non-US representation probe. | P0 + Q1 + Q2 + Q3A + Q3B + Q3C |
| `JURISDICTION_OPERATIONALLY_QUALIFIED` | One named jurisdiction/domain/intent package passed its own bounded empirical, data, rights, and operational gates. | Per-jurisdiction profile; cannot be inferred from another jurisdiction |

### Deployment profiles

| Profile | Intended environment | Mandatory overlay implications |
|---|---|---|
| `LOCAL_SINGLE_USER` | Local/private evaluation; no external service claim. | DQ/IR/DB/S/A/M/R/W/G as applicable; O/F limited to local recoverability and field correction |
| `PRIVATE_SINGLE_TENANT_HOSTED` | One organization or controlled beta environment. | DQ/IR/DB/S/A/M/O/R/F/G plus W when Windows is supported; tenant-isolation criteria may be N/A with evidence |
| `PUBLIC_MULTI_TENANT_SAAS` | Internet-facing, multiple users/workspaces. | All applicable DQ/IR/DB/S/A/M/O/R/F/G; multi-tenant isolation mandatory; W required only when Windows is supported |
| `ENTERPRISE_API_OR_ON_PREM` | API or customer-operated deployment. | Profile-specific auth, isolation, upgrade, support, and deployment criteria |

Commercial operation is a modifier layered onto a deployment profile; it activates E and commercial claim controls. `Q3C`, internationalization, data-residency, and cross-border transfer criteria become mandatory only for a global architecture or international operational claim. `CG` applies only to automatic candidate generation/ranking. `FIN` applies only to financial/valuation/investment outputs. `W` applies to the canonical Windows development/operator environment.

## 3C. Requirement classes

Every criterion must declare one requirement class.

| Class | Meaning | Waiver behavior |
|---|---|---|
| `INVARIANT` | Fundamental safety, evidence, rights, or isolation rule. | Cannot be waived. |
| `PROFILE_REQUIRED` | Required for one or more selected profiles. | May become `N/A` only by narrowing and refreezing scope. |
| `TARGETED` | Requires a predeclared numeric or ordinal target. | Target may change only before unsealing; post-hoc change invalidates the run. |
| `JUDGMENT_RUBRIC` | Requires structured expert/user judgment. | Binary result still required; rubric, reviewers, and adjudication are mandatory. |
| `DIAGNOSTIC` | Collected for improvement but does not independently block release. | Cannot be represented as proof of qualification. |

The framework deliberately avoids treating every desirable practice as an invariant. This prevents unnecessary rigidity while preserving non-waivable safety boundaries.

## 3D. Criterion contract

A release-blocking criterion is not operationally valid until its machine-readable contract contains:

```text
criterion_id
gate_id
requirement_class
applicable_profiles
statement
unit_of_analysis
population_or_input_scope
pass_logic
fail_logic
blocked_logic
n_a_logic
metric_definition
numerator
denominator
threshold
uncertainty_method
stratification_requirements
evidence_types
verification_method
reviewer_or_owner_role
automation_level
execution_frequency
expiry
invalidation_triggers
```

If a required field is unresolved, the criterion result is `BLOCKED`. Qualitative terms such as “material,” “appropriate,” “representative,” “critical,” or “independent” must point to a controlled definition or rubric.

## 3E. Controlled vocabulary

The following terms must be defined in `config/qualification_vocabulary.yaml` before P0 can pass:

- `critical_issue`;
- `material_issue`;
- `severe_blocker`;
- `screenable_positive`;
- `screenable_negative`;
- `critical_false_reassurance`;
- `source_failure`;
- `source_gap`;
- `stale_source`;
- `conflicting_evidence`;
- `degraded_report`;
- `correct_claim`;
- `high_confidence`;
- `representative_workload`;
- `independent_reviewer`;
- `fresh_operator`;
- `semantic_equivalence`;
- `material_change`;
- `supported_environment`;
- `production_grade`.

Definitions must be bounded by product scope. For example, “severe blocker” is a screening classification, not a final legal determination.

## 3F. Stratification rule

Aggregate success cannot hide a failed critical subgroup.

For every safety- or validity-relevant metric, results must be reported where applicable by:

```text
geography
intent
domain
source state
input modality
severity
confidence band
user persona
output channel
deployment profile
```

A configured subgroup floor may be lower-powered than the aggregate result, but:

- zero critical false reassurance remains invariant;
- no primary persona may fail safety comprehension;
- no qualified domain may have zero positive acceptance examples;
- no qualified geography/intent may be supported only by pooled results from another scope.

## 3G. Evidence-preservation modes

Source licenses can conflict with reproducibility. Every source must use one approved evidence mode:

| Mode | Use |
|---|---|
| `FULL_SNAPSHOT` | Raw versioned source content may be retained and replayed. |
| `CONTROLLED_SNAPSHOT` | Raw content retained in restricted storage with access controls. |
| `HASHED_RETRIEVAL_MANIFEST` | Content cannot be retained; store request, response metadata, hashes, version IDs, and permitted derived observations. |
| `PROVIDER_REPLAY` | Reproduction uses an authorized provider snapshot/version endpoint. |
| `SYNTHETIC_CONTRACT_FIXTURE` | Used only for connector-contract behavior; cannot prove real-source empirical accuracy. |

A source without an approved preservation mode is blocked from qualification claims requiring historical reproducibility.


## 4. Status and result vocabulary

### 4.1 Qualification status

Every qualification object must use exactly one status.

| Status | Meaning |
|---|---|
| `NOT_RUN` | No admissible execution has begun. |
| `RUNNING` | Execution is in progress; no completion claim is allowed. |
| `BLOCKED` | A required dependency, decision, authority, sample, reviewer, environment, or target is unavailable. |
| `FAIL` | One or more hard criteria failed. |
| `PASS` | Every applicable hard criterion passed and all required evidence exists. |
| `INVALIDATED` | A prior pass is no longer valid because a material change or discovered defect affects it. |
| `EXPIRED` | The qualification exceeded its approved validity period and must be rerun or renewed. |

There is no `PARTIAL_PASS`.

### 4.2 Criterion result

| Result | Meaning |
|---|---|
| `PASS` | Criterion satisfied with admissible evidence. |
| `FAIL` | Criterion not satisfied. |
| `BLOCKED` | Criterion is required but cannot presently be evaluated. |
| `N/A` | Demonstrably inapplicable to the frozen scope, with rationale, approver, and expiry. |

`N/A` is prohibited for release-blocking safety, evidence-lineage, source-rights, reproducibility, tenant-isolation, backup/restore, or critical-false-reassurance criteria when the associated feature exists.

### 4.3 Criterion severity

| Severity | Meaning |
|---|---|
| `RELEASE_BLOCKING` | Any `FAIL` or `BLOCKED` prevents the associated qualification claim. |
| `REQUIRED` | Must pass for full qualification; may be deferred only by narrowing the product scope before execution. |
| `DIAGNOSTIC` | Recorded for improvement but does not independently control the gate. |

---

## 5. Automatic failure conditions

Any of the following automatically fails the applicable gate and prevents a production-grade claim:

1. An interpreted claim has no stored evidence link.
2. A required source failure, restriction, staleness state, or unknown is silently represented as “clear,” “none,” or low risk.
3. The system makes an unsupported final legal, title, survey, access, zoning, wetland, septic, appraisal, insurance, lending, water-rights, mineral-rights, or investment determination.
4. A predesignated critical issue is missed or materially understated.
5. Restricted or unapproved source data is ingested, persisted, exposed, exported, trained on, or used in a claim.
6. Protected-class data or a proxy is used to rank or steer residential location choices.
7. A cross-user or cross-tenant data leak occurs.
8. A report cannot be reproduced from the recorded commit, rules, migrations, source versions, and artifacts.
9. A sealed acceptance cohort was visible to implementers or coding agents before release-candidate execution.
10. Thresholds, denominators, exclusion rules, or primary endpoints were changed after results were inspected without invalidating the run.
11. Test failures, source failures, or qualification discrepancies were removed, suppressed, or reclassified without recorded evidence and approval.
12. Production backup restoration fails or has never been exercised for a production-grade claim.
13. A deployment or migration causes silent evidence, claim, audit, or report-lineage loss.
14. A security assessment finds an unresolved critical or high-severity vulnerability in the released scope.
15. User-facing exported artifacts lose material caveats, unknowns, source restrictions, or lineage.
16. The exact artifact tested is not the artifact released.
17. A qualification is claimed from local hidden state, chat history, manual database edits, or undocumented steps.
18. Required reviewers have undisclosed conflicts of interest or the reference standard is created after viewing system output.
19. The wrong parcel/AOI, ambiguous address, duplicate parcel identifier, or superseded geometry is used without explicit disambiguation.
20. A user-facing citation or evidence reference cannot be resolved to the recorded source/version or approved preservation record.
21. A release-blocking criterion is declared passed without a complete criterion contract, denominator, evidence, and verifier.
22. Aggregate metrics are used to conceal a failed safety-critical geography, intent, domain, persona, or output channel.
23. Protected qualification code, thresholds, sealed-case hashes, or evidence manifests are modified without invalidating the run.
24. A released system continues to assert a previously qualified claim after detected source drift, rights revocation, or field evidence invalidates it.

---

## 6. Canonical target registry

Every numeric threshold and scope boundary must be frozen in `config/qualification_targets.yaml` before qualification begins.

The registry must identify:

```text
product claim
product-scope profile
deployment profile
intent(s)
geography/geographies
enabled domains
enabled connectors
enabled input modalities
enabled output channels
enabled AI/LLM behavior
qualified-domain profiles
source preservation modes
reference-standard hierarchy
sample-size floors
power-analysis result
accuracy thresholds
user-utility thresholds
performance targets
cost targets
RTO/RPO/SLO targets
security verification profile
Postgres/PostGIS qualification targets
regulatory applicability profile
accessibility conformance target
qualification validity period
```

A missing target required by a criterion results in `BLOCKED`. Targets cannot be backfilled after results are known.

Recommended minimum floors are included in the companion example file. A power analysis or risk assessment may require larger samples or stricter thresholds; it may not justify weaker safety-critical thresholds.

---

# P0 — Protocol Integrity and Admissibility Gate

## 7. Qualification claim

Passing P0 permits only this claim:

> The empirical protocol is sufficiently controlled, predeclared, independent, and reproducible for Q1–Q3 results to be considered admissible.

P0 does not qualify product behavior.

## 8. P0 hard criteria

| ID | Requirement | PASS | FAIL | Required evidence |
|---|---|---|---|---|
| `P0-001` | Frozen qualification claim | Exact product, geography, intent, domains, users, sources, outputs, and prohibited claims are frozen before execution. | Scope is vague or changes after results are viewed. | Signed protocol and target registry. |
| `P0-002` | Exact candidate identity | Commit, tag, container digest, migration set, ruleset versions, configuration, and source manifests identify the tested candidate. | Candidate cannot be uniquely reconstructed. | Candidate manifest. |
| `P0-003` | Protocol preregistration | Protocol, primary endpoints, metrics, thresholds, denominators, analysis, exclusions, and stopping rules are committed and timestamped before unsealing. | Any primary rule is chosen post hoc. | Preregistered protocol hash. |
| `P0-004` | Sealed acceptance isolation | Acceptance cases and expected outcomes are held outside the ordinary developer/agent-visible repo; only hashes and metadata are visible. | Implementers or agents can inspect acceptance answers before execution. | Vault/access-control record and hashes. |
| `P0-005` | Anti-contamination rule | Cases previously used for development, debugging, prompting, or tuning are excluded from sealed acceptance. | A known fixture is counted as independent acceptance evidence. | Case provenance register. |
| `P0-006` | Sampling frame | The eligible population, selection method, strata, inclusion/exclusion rules, and replacement rules are explicit. | Cases are hand-picked without a documented frame. | Sampling plan. |
| `P0-007` | Coverage matrix | Required combinations of geography, domain, source state, severity, geometry type, and control type have minimum counts. | Material strata have zero or unknown coverage. | Coverage matrix. |
| `P0-008` | Sample-size justification | Sample count is the larger of the configured floor or the preregistered power/precision requirement. | Count is based only on convenience. | Power/precision calculation. |
| `P0-009` | Metric definitions | Every metric has exact numerator, denominator, unit of analysis, aggregation rule, and treatment of ties/unknowns. | Metrics can be calculated multiple ways. | Metrics specification. |
| `P0-010` | Missing-data policy | Missing participant, source, reviewer, or run data has a preregistered treatment; silent case deletion is prohibited. | Missing results are excluded opportunistically. | Missing-data plan. |
| `P0-011` | Exclusion policy | Case/participant exclusion conditions are defined before execution and every exclusion is logged. | Outliers or failures are removed post hoc. | Exclusion log. |
| `P0-012` | Reviewer independence | Reference reviewers are independent of the implementation under test or their role/conflict is explicitly controlled. | Implementers self-certify material correctness. | Reviewer roster and disclosures. |
| `P0-013` | Blinding | Reference reviewers do not see system output before recording initial judgments; output raters do not see implementation intent where avoidable. | Reference judgments are influenced by product output. | Blinding procedure and attestations. |
| `P0-014` | Reference reliability | Pre-adjudication inter-rater reliability meets the configured threshold, or the domain is marked reference-unstable and cannot support a pass claim. | Reference disagreement is high and hidden by adjudication. | Reliability metrics and raw ratings. |
| `P0-015` | Adjudication integrity | Disagreements are preserved, adjudicated by a third qualified reviewer, and reasons are recorded. | Final reference silently overwrites disagreement. | Adjudication register. |
| `P0-016` | Statistical analysis | Point estimates, uncertainty intervals, paired/crossover structure, and multiple-comparison treatment are preregistered. | Only favorable point estimates are reported. | Analysis plan and code. |
| `P0-017` | Practical-effect threshold | Statistical significance alone cannot pass a utility criterion; configured practical-effect thresholds also apply. | A trivial effect is called useful because p < threshold. | Target registry. |
| `P0-018` | Retest rule | Failed gates may be rerun only after a recorded remediation; the previous run remains archived. | Failed runs are overwritten or repeatedly rerun until passing without disclosure. | Retest history. |
| `P0-019` | Change freeze | Material code/rule/source/config changes after qualification begins invalidate the run unless explicitly classified as non-semantic. | Candidate changes during testing without restart. | Change log and diff classification. |
| `P0-020` | Human-subject protection | Consent, privacy, compensation, withdrawal, retention, and de-identification procedures exist for participant studies. | Participant data is collected without adequate handling rules. | Study protocol and privacy record. |
| `P0-021` | Evidence integrity | Raw inputs, outputs, reviewer records, analysis code, and hashes are retained in immutable or controlled storage. | Evidence can be edited without trace. | Archive manifest and hashes. |
| `P0-022` | Independent reproduction | A second operator can execute the protocol from documented materials without chat history or maintainer intervention. | Results depend on hidden knowledge. | Reproduction report. |
| `P0-023` | Threshold immutability | Threshold changes after unsealing automatically invalidate the run and require a new version. | Thresholds are softened after failure. | Git history and status record. |
| `P0-024` | Publication completeness | All prespecified results, including failures and adverse findings, are reported. | Unfavorable metrics are omitted. | Final qualification report. |

| `P0-025` | Reviewer competency | Each reference/adjudication role has frozen competency requirements, training/calibration evidence, and domain limits. | Unqualified reviewers establish decision-critical truth. | Reviewer qualification records. |
| `P0-026` | Clustered/stratified analysis | Repeated domains within AOIs, repeated tasks within participants, and county/persona strata are handled by the preregistered analysis. | Non-independent observations are treated as independent or subgroup failure is hidden. | Analysis specification. |
| `P0-027` | Qualification implementation integrity | Analysis code, criteria catalog, target registry, sealed hashes, and schemas are protected by review and content hashes. | Acceptance machinery can be silently altered during execution. | Integrity manifest. |
| `P0-028` | External-validity boundary | The protocol states the population, contexts, dates, source conditions, and claims to which results do and do not generalize. | A balanced challenge cohort is represented as real-world prevalence or universal validity. | External-validity statement. |
| `P0-029` | Reference hierarchy | Every domain defines acceptable authoritative, professional, independent-calculation, and fallback reference levels plus conflict handling. | Reviewers choose convenient references post hoc. | Domain reference profiles. |
| `P0-030` | Safety stop rule | A preregistered rule pauses execution and blocks release when critical false reassurance, rights breach, privacy breach, or cross-user leakage is observed. | Testing continues and results are pooled after a critical safety breach without containment. | Stop-rule and incident record. |

P0 passes only when every applicable criterion passes.

---

# Q1 — Blind Real-Parcel Accuracy, Safety, and Data-Quality Benchmark

## 9. Qualification claim

Passing Q1 permits this bounded claim:

> For the frozen MVP geography, intent, domains, sources, and report version, the system demonstrated materially accurate, evidence-linked, fail-closed screening behavior on an unseen real-parcel cohort.

It does not establish professional, legal, engineering, environmental, appraisal, insurance, lending, or investment-grade determination.

## 10. Cohort construction

Recommended minimum floor:

```text
60 real AOIs total
20 per selected North Carolina county
```

The actual count is the larger of this floor or the P0 power/precision requirement.

Per county, include at minimum:

- six material-positive AOIs;
- four critical or multi-hazard AOIs;
- four ambiguity/conflict/source-gap AOIs;
- four ordinary negative/control AOIs;
- two geometry or boundary edge cases.

Across the cohort, require at least:

- 30 critical issue instances;
- five screenable positive instances for every core domain claimed as qualified;
- five explicit source-unavailable/stale/restricted instances;
- five contradictory-source instances;
- five boundary-touch/sliver/multipolygon geometry cases;
- five input-identity ambiguity cases covering address/APN/geocode/parcel-version uncertainty;
- at least one parcel split, merge, supersession, or cross-jurisdiction identity case where available.

An AOI may satisfy multiple strata, but every stratum count must be reported.

## 11. Reference standard

Each domain/case is classified before system output is viewed:

```text
SCREENABLE_POSITIVE
SCREENABLE_NEGATIVE
UNKNOWN_DUE_TO_SOURCE
CONFLICTING_EVIDENCE
OUTSIDE_SCREENING_SCOPE
NOT_APPLICABLE
```

The reference must distinguish:

- authoritative observation;
- professional or agency determination;
- independent geospatial calculation;
- source limitation;
- reviewer inference.

The reference should use information independent of the system’s derived output where reasonably possible. The same upstream source may verify raw facts, but system-generated claims cannot serve as their own reference.

## 12. Q1 hard criteria

| ID | Requirement | PASS | FAIL | Required evidence |
|---|---|---|---|---|
| `Q1-001` | Terminal run behavior | Every AOI reaches a persisted terminal state: complete, degraded, blocked, or failed with explicit reason. | Any run disappears, hangs indefinitely, or fails silently. | Run manifest. |
| `Q1-002` | Claim-evidence linkage | 100% of interpreted claims link to stored evidence and source/version metadata. | Any interpreted claim is unlinked. | Automated lineage report. |
| `Q1-003` | Provenance completeness | 100% of source-derived evidence contains source, retrieval, version/date, geography, method, confidence, caveat, and rights status required by schema. | Any required field is absent or fabricated. | Provenance audit. |
| `Q1-004` | Unsupported certainty | Zero forbidden final/professional determinations or materially equivalent language. | Any forbidden certainty appears in API, UI, export, or report. | Language scan plus human review. |
| `Q1-005` | Critical false reassurance | Zero cases state or materially imply clear/no issue/low risk for a critical positive, critical unknown, restricted source, or failed source. | Any critical false reassurance occurs. | Case discrepancy register. |
| `Q1-006` | Critical issue recall | 100% of predesignated critical screenable issue instances are surfaced as red flag, blocker, contradiction, or explicit unknown at the correct minimum severity. | Any critical issue is missed or materially understated. | Confusion matrix. |
| `Q1-007` | Material issue recall | Point recall meets configured threshold, recommended >=90%, and the configured lower confidence bound is met, recommended >=80%. | Either point or uncertainty threshold fails. | Metrics with intervals. |
| `Q1-008` | Severe false-positive control | Severe-blocker false-positive rate meets configured ceiling, recommended <=10%, with configured upper confidence bound, recommended <=20%. | Either ceiling fails. | Metrics with intervals. |
| `Q1-009` | Unknown fidelity | 100% of reference unknown/source-gap cases remain visibly unknown, unavailable, stale, restricted, conflicting, or requiring verification. | Any unknown becomes an implicit negative/clear result. | Unknown-state matrix. |
| `Q1-010` | Contradiction fidelity | 100% of material source conflicts are retained and surfaced; no arbitrary winner is silently selected. | Conflict is hidden or collapsed without policy/evidence. | Conflict report. |
| `Q1-011` | Source freshness truth | 100% of stale, unknown-date, failed, or superseded sources are labeled correctly. | Any source is represented as fresher or more authoritative than recorded. | Freshness audit. |
| `Q1-012` | Source-rights truth | 100% of restricted or unapproved data is blocked from prohibited use and represented accurately in report coverage. | Rights boundary is crossed or hidden. | Entitlement audit. |
| `Q1-013` | Spatial calculation accuracy | Independent calculations for intersections, distances, areas, buffers, slopes, bounds, and centroids are within source-specific tolerances frozen in targets. | Any material calculation exceeds tolerance. | Spatial comparison report. |
| `Q1-014` | Boundary semantics | Touching, sliver overlap, holes, multipolygons, invalid geometry, and CRS transformation cases follow documented deterministic rules. | Boundary behavior is inconsistent or undocumented. | Edge-case suite. |
| `Q1-015` | Geospatial data-quality declaration | Every production source/domain has measured or declared completeness, logical consistency, positional accuracy, temporal quality, thematic accuracy, and usability/lineage limits. | A source is used without a data-quality profile. | DQ profiles. |
| `Q1-016` | Confidence calibration | High-confidence claims meet configured correctness threshold, recommended >=95%, and no critical high-confidence false claim occurs; confidence bands are monotonic. | High-confidence errors exceed target or lower bands outperform higher bands materially. | Calibration report. |
| `Q1-017` | Severity calibration | Critical/severe labels correspond to preregistered materiality rules; no severe label is generated solely from low-confidence weak evidence unless explicitly marked precautionary. | Severity is opaque, inconsistent, or misleading. | Severity audit. |
| `Q1-018` | Caveat preservation | 100% of material claims preserve required source/domain caveats through database, API, UI, and export. | Any output channel drops a material caveat. | Cross-channel comparison. |
| `Q1-019` | Verification-action coverage | Every critical positive, critical unknown, and conflict has at least one appropriate next verification action. | Any critical case lacks an actionable next step. | Reviewer rating. |
| `Q1-020` | Verification-action quality | At least configured proportion, recommended >=90%, of generated actions are appropriate, feasible, nonduplicative, and non-misleading. | Threshold fails. | Reviewer scores. |
| `Q1-021` | Normalized reproducibility | Repeated pinned runs produce identical canonical semantic output after excluding only preregistered nondeterministic fields. | Unexplained semantic drift occurs. | Canonical hashes and diff. |
| `Q1-022` | Versioned change explanation | Current-source reruns identify source/rule/version changes and explain report deltas. | Output changes without attributable lineage. | Report-diff artifact. |
| `Q1-023` | Impact traceability | Given a defective source version or rule, the system can identify all affected evidence, claims, reports, and exports. | Affected outputs cannot be enumerated. | Impact-query transcript. |
| `Q1-024` | Correction path | A material defect can trigger correction, invalidation, regeneration, and user/operator notification records without overwriting history. | Incorrect output cannot be safely corrected or recalled. | Correction drill. |
| `Q1-025` | Export integrity | JSON, HTML/PDF, and shared views preserve material source, caveat, unknown, restriction, version, and lineage information. | Any export loses decision-critical context. | Artifact comparison. |
| `Q1-026` | PII minimization | Reports, logs, fixtures, and qualification artifacts contain no unnecessary owner/person data or user-sensitive search history. | Unnecessary PII is exposed or retained. | PII scan and inventory. |
| `Q1-027` | Fault behavior | Timeout, malformed payload, empty response, HTTP error, rate limit, stale cache, schema drift, and partial-source failure all fail closed. | Any injected failure yields false-clear output or corrupted state. | Fault-injection report. |
| `Q1-028` | Regression safety | Protected NC golden, DB, migration, report, lineage, source-rights, overclaim, and connector suites pass unchanged. | Tests are weakened, skipped, or fail. | CI report. |
| `Q1-029` | Runtime bound | p95 report runtime and resource usage meet the frozen qualification target in pinned and current-source modes. | Target fails or measurement is absent. | Performance report. |
| `Q1-030` | Independent reproduction | A second operator reproduces the exact benchmark from the candidate tag and controlled inputs. | Reproduction fails or needs hidden intervention. | Reproduction report. |

| `Q1-031` | AOI/input identity | The resolved AOI/parcel/locality matches the intended input or requires explicit user/operator disambiguation before decision-relevant processing. | The system analyzes the wrong or ambiguously resolved place without blocking. | Input-resolution audit. |
| `Q1-032` | Parcel/locality lineage | Parcel identifiers, geometry versions, splits, merges, aliases, and jurisdiction changes are preserved or explicitly unresolved. | Historical/current records are silently conflated. | Identity-lineage report. |
| `Q1-033` | Citation resolvability | Every material citation resolves to the recorded source/version, permitted snapshot, provider replay, or hashed retrieval manifest. | A user/operator cannot verify the cited evidence. | Citation-resolution audit. |
| `Q1-034` | Domain/intent/geography floors | Every qualified domain, intent, and geography meets its configured critical and material floors independently; aggregate pooling cannot rescue a failed scope. | A declared sub-scope fails while the aggregate passes. | Stratified metrics. |
| `Q1-035` | Input-modality equivalence | Address, parcel ID, coordinates, uploaded/drawn geometry, and multi-parcel inputs produce equivalent AOI identity where they refer to the same place, within declared tolerances. | Input mode materially changes the analyzed place without warning. | Cross-input comparison. |
| `Q1-036` | Negative capability | Domains outside coverage or evidence strength are explicitly `NOT_EVALUATED`/unknown and never inferred from adjacent layers. | The report implies comprehensive diligence from partial domain coverage. | Coverage-language audit. |
| `Q1-037` | Domain qualification profile | Every domain has a frozen reference method, issue taxonomy, severity rubric, confidence rubric, source hierarchy, tolerances, and known exclusions. | A domain is called qualified without domain-specific criteria. | Domain profile registry. |
| `Q1-038` | Benchmark-prevalence distinction | Challenge-set metrics and any prevalence-weighted estimates are reported separately. | Balanced benchmark performance is presented as field prevalence performance. | Metrics report. |

## 13. Q1 required evidence package

```text
qualification/q1/<qualification-version>/
  protocol_ref.yaml
  candidate_manifest.yaml
  cohort_hash_manifest.json
  coverage_matrix.csv
  reference_schema.json
  raw_blinded_ratings/
  inter_rater_reliability.json
  adjudication_register.csv
  source_version_manifest.json
  source_rights_snapshot.csv
  geospatial_tolerance_profile.yaml
  raw_outputs/
  normalized_outputs/
  canonical_hashes.json
  metrics.json
  confidence_intervals.json
  calibration_report.json
  fault_injection_results.json
  discrepancy_register.csv
  independent_reproduction.md
  PASS_OR_FAIL.md
```

---

# Q2 — Comparative User Decision-Utility and Human-Factors Trial

## 14. Qualification claim

Passing Q2 permits this bounded claim:

> For the frozen user personas and rural-land screening workflow, system-assisted participants recognized material issues and unknowns more effectively and completed the task more efficiently than under the defined manual baseline, without acquiring unsafe certainty.

It does not establish that the product chooses the best property, guarantees a good purchase, or replaces professional diligence.

## 15. Trial design

Use three realistic briefs aligned to the selected counties:

1. mountain/rural residence screen;
2. rural residence plus small-agriculture screen;
3. coastal residence screen.

Each brief contains at least six real candidate AOIs:

- one clear mandatory exclusion;
- one ambiguity/source-gap candidate;
- two plausible candidates;
- one ordinary control;
- one multi-factor tradeoff candidate.

Minimum participant floor:

```text
24 participants
8 land professionals or experienced analysts
8 experienced rural buyers/investors
8 realistic less-experienced target users
```

Use the larger of this floor or the preregistered power requirement. Project implementers cannot count as target-user participants.

Use a randomized, counterbalanced crossover or an equivalently powered design. Training, task instructions, time limits, available baseline materials, and assistance must be standardized.

## 16. Required tasks

Each participant must:

1. identify mandatory exclusions;
2. produce a defensible shortlist;
3. identify material risks and supporting evidence;
4. identify material unknowns and source gaps;
5. state next verification actions;
6. explain confidence and uncertainty;
7. complete critical safety-comprehension questions;
8. export or hand off the result.

## 17. Q2 hard criteria

| ID | Requirement | PASS | FAIL | Required evidence |
|---|---|---|---|---|
| `Q2-001` | Representative participants | Every declared primary persona meets its minimum count; implementers are excluded from target-user counts. | Any primary persona is absent or materially underrepresented. | Participant matrix. |
| `Q2-002` | Standardized baseline | Manual-condition information, time, tools, and training are fixed and reproducible. | Baseline is artificially weak, inconsistent, or undocumented. | Baseline package. |
| `Q2-003` | Randomization/counterbalancing | Assignment and ordering follow the preregistered design; deviations are recorded. | Convenience ordering creates uncontrolled learning bias. | Randomization manifest. |
| `Q2-004` | Carryover control | Learning/order effects are tested and remain below configured tolerance or are adjusted according to plan. | Material carryover invalidates comparison. | Analysis output. |
| `Q2-005` | Workflow completion | At least configured rate, recommended >=90%, completes intake, report, evidence, comparison, decision, and export without developer intervention. | Threshold fails or hidden manual intervention is required. | Session logs. |
| `Q2-006` | Critical exclusion recognition | System-assisted participants identify at least configured rate, recommended >=95%, of expert-designated critical exclusions and are not worse than baseline in any critical category. | Threshold fails or any critical category degrades materially. | Paired result matrix. |
| `Q2-007` | Material issue improvement | System-assisted recognition improves by configured practical threshold, recommended >=15 percentage points, and the preregistered uncertainty interval excludes no improvement. | Practical or uncertainty threshold fails. | Statistical report. |
| `Q2-008` | Time efficiency | Median system-assisted completion time improves by configured threshold, recommended >=30%, and uncertainty supports a real improvement. | Threshold fails. | Task timing analysis. |
| `Q2-009` | Decision concordance | At least configured rate, recommended >=80%, of shortlist/reject decisions fall within the independent panel’s defensible decision set. | Threshold fails. | Decision matrix. |
| `Q2-010` | Unknown recognition | At least configured rate, recommended >=90%, of material unknowns are identified in the assisted condition. | Threshold fails. | Unknown-recognition matrix. |
| `Q2-011` | Evidence traceability | At least configured rate, recommended >=90%, of material participant reasons are traceable to evidence without developer help. | Threshold fails. | Observational scoring. |
| `Q2-012` | Verification-action quality | At least configured rate, recommended >=90%, of proposed next actions are appropriate; every critical case has an appropriate action. | Threshold fails or any critical case lacks an action. | Expert ratings. |
| `Q2-013` | Safety comprehension | Zero participants submit a final decision while retaining a prohibited certainty interpretation. Initial misunderstandings are permitted only if the product detects/corrects them and comprehension is then demonstrated. | Any participant completes while retaining a prohibited certainty interpretation, or correction depends on developer intervention. | Pre/post comprehension results and correction logs. |
| `Q2-014` | Trust calibration | Assisted confidence tracks task accuracy and does not show configured material overconfidence relative to the manual condition. | Product materially increases confidence without corresponding accuracy. | Calibration analysis. |
| `Q2-015` | Source-failure visibility | Zero observed participant errors are caused by a hidden source failure, stale source, restricted source, or unknown represented as clear. | Any such error occurs. | Root-cause register. |
| `Q2-016` | Error recovery | At least configured rate, recommended >=90%, can locate the reason for a warning/conflict and revise a decision after corrected evidence is introduced. | Users cannot recover from or understand correction. | Recovery task scores. |
| `Q2-017` | No steering/proxy behavior | No task, feature, recommendation, or participant rationale is driven by protected classes or residential desirability proxies supplied by the system. | Any protected-class steering behavior occurs. | Feature/data audit and session review. |
| `Q2-018` | Accessibility task completion | Participants using keyboard-only and at least one screen-reader/low-vision workflow can complete all critical tasks; no critical accessibility blocker exists. | A critical task is inaccessible. | Accessibility session report. |
| `Q2-019` | Cross-channel consistency | UI, API, and export present materially equivalent claims, unknowns, caveats, and evidence links. | Users receive contradictory semantics by channel. | Cross-channel audit. |
| `Q2-020` | Artifact handoff | 100% of exported/shared trial artifacts preserve run version, sources, caveats, unknowns, restrictions, and lineage. | Any handoff loses required context. | Artifact audit. |
| `Q2-021` | Support burden | Median help requests and intervention time remain within frozen target; no critical workflow requires maintainer knowledge. | Target fails. | Session support logs. |
| `Q2-022` | Usability floor | Median usefulness-for-next-investigation rating meets configured floor, recommended >=4/5, and no critical workflow median is below 3/5. | Threshold fails. | Survey results. |
| `Q2-023` | Qualitative defect saturation | All recurring critical/major themes are coded, owned, and resolved or scope-blocking; no unowned repeated critical theme remains. | Repeated critical problem is dismissed as anecdotal. | Thematic analysis. |
| `Q2-024` | Participant privacy | Study data is de-identified, access-controlled, retained/deleted per protocol, and not mixed into product data. | Privacy protocol is violated. | Data-handling audit. |
| `Q2-025` | Independent analysis | A second analyst reproduces primary calculations from de-identified raw data and analysis code. | Primary results cannot be reproduced. | Reanalysis report. |
| `Q2-026` | Regression preservation | Product changes made for the trial do not weaken Q1, safety language, source rights, or existing protected tests. | Q1 or protected regression is degraded. | CI and Q1 smoke report. |

| `Q2-027` | Persona-specific safety floor | Every primary persona independently meets critical exclusion, unknown-recognition, and safety-comprehension floors. | Aggregate success hides a failed primary persona. | Stratified persona report. |
| `Q2-028` | First-use versus trained-use | Results separately report first-use performance and trained/repeated-use performance; required product claims use the appropriate context. | Learning-dependent performance is presented as first-use usability. | Session-order analysis. |
| `Q2-029` | Cognitive-load control | Workload/frustration and information-overload measures remain within frozen limits; improvements are not achieved by hiding evidence or caveats. | Users are faster only because decision-critical context is suppressed or overload is unacceptable. | Workload and content audit. |
| `Q2-030` | Comparator honesty | If an incumbent/tool-assisted comparator is used, its configuration, data access, training, and time budget are equivalent and reproducible. Manual baseline remains separately reported. | A deliberately weak or misconfigured comparator is used to manufacture advantage. | Comparator package. |

## 18. Q2 required evidence package

```text
qualification/q2/<qualification-version>/
  protocol_ref.yaml
  participant_protocol.md
  consent_privacy_retention.md
  persona_and_power_matrix.csv
  trial_briefs/
  baseline_materials/
  candidate_hash_manifest.json
  expert_reference.json
  randomization_manifest.json
  anonymized_session_data/
  task_times.csv
  task_scores.csv
  comprehension_results.csv
  accessibility_results.md
  trust_calibration.json
  qualitative_codebook.md
  discrepancy_register.csv
  analysis_code/
  independent_reanalysis.md
  metrics.json
  PASS_OR_FAIL.md
```

---

# Q3 — Cross-Jurisdiction Portability, Source Substitution, and Degraded-Source Resilience Trial

## 19. Qualification claim

Passing Q3 permits this bounded claim:

> The platform demonstrated modular expansion across materially different source and jurisdiction conditions, including a non-US architecture probe, without forking or weakening the core area/evidence/claim/report model and while failing closed under restricted or unavailable data.

Q3 does not establish worldwide legal-grade coverage.

## 20. Required lanes

Q3 is represented as three independently passable sub-gates: `Q3A`, `Q3B`, and `Q3C`. A US expansion-readiness claim requires Q3A and Q3B. A global-architecture-probe claim additionally requires Q3C. A bounded production claim for the existing NC scope does not require any Q3 lane.

### Lane A — Approved cross-state integration

Use one US jurisdiction outside North Carolina with:

- materially different hazards or land-use conditions;
- approved parcel/zoning or equivalent source rights;
- at least two reusable domains and two genuinely new domain/jurisdiction concerns;
- at least eight real AOIs, including ordinary, positive, unknown, and boundary cases.

A county such as Larimer County, Colorado may be considered after source-rights review, but the jurisdiction is not locked by this framework.

### Lane B — Restricted/unavailable-source path

Use one jurisdiction/source where a material local source is unavailable, restricted, unlicensed, or operationally blocked.

At least four real AOIs must prove that:

- prohibited data is not used;
- the report still reaches a truthful degraded terminal state using approved sources;
- missing local domains remain explicit;
- no scraping or silent substitute occurs.

### Lane C — Non-US architecture probe

Use one non-US locality with materially different:

- administrative hierarchy;
- cadastral/land-administration concepts;
- source authorities and terms;
- language or terminology;
- units/date/number/address conventions;
- CRS or map-service conventions;
- planning or land-use document structure;
- freehold, leasehold, strata/vertical, communal/customary, concession, public-land, or other locally relevant tenure concepts without forcing US parcel ownership semantics.

Bologna may be used if authoritative AOI/source decisions and usage rights are approved. Lane C requires at least six independently reviewable cases spanning administrative hierarchy, cadastral identity, locale, CRS, source rights, and planning-document representation. Cases may be AOIs or architecture/contract scenarios, but each must have explicit inputs, expected representation, and pass/fail output.

Lane C is an architecture probe, not a claim of purchase-grade international diligence.

## 21. Q3 hard criteria

| ID | Requirement | PASS | FAIL | Required evidence |
|---|---|---|---|---|
| `Q3-001` | Core-model preservation | No jurisdiction-specific fork of area, geometry, source, evidence, claim, report, audit, rights, or review semantics. | Core domain models are copied or forked. | Architecture diff. |
| `Q3-002` | Schema generality | No schema change is needed, or every change has an ADR proving general cross-jurisdiction value and backward compatibility. | Ad hoc jurisdiction columns/tables are introduced. | Migration/ADR review. |
| `Q3-003` | Change dispersion (`DIAGNOSTIC`) | Change concentration across core versus extension modules is measured and reviewed; any core change is justified as reusable through ADR and protected tests. | This metric alone cannot pass or fail Q3; failure occurs through Q3-001/002/004/005 when core coupling is demonstrated. | Change-dispersion analysis. |
| `Q3-004` | Dependency direction | Core modules do not import jurisdiction implementations; adapters depend inward on stable interfaces. | Circular or outward core dependency appears. | Dependency graph. |
| `Q3-005` | Registration mechanism | New source, jurisdiction, and rulepack can be registered without central conditional chains or editing unrelated handlers. | Expansion requires pervasive `if jurisdiction == ...` logic. | Registration test. |
| `Q3-006` | Source-governance precondition | Every new source has authority, license/terms, allowed uses, caveats, freshness, coverage, and contact/retirement metadata before activation. | Connector activates first and governance is added later. | Source registry snapshot. |
| `Q3-007` | Restricted-source enforcement | Lane B restricted/unapproved data is never ingested, persisted, cached, rendered, exported, trained on, or used in claims. | Any prohibited use occurs. | Entitlement audit. |
| `Q3-008` | Degraded completion | Every Lane B case reaches an explicit partial/blocked terminal state with domain coverage and next actions. | Run crashes, hangs, or represents blocked domains as clear. | Run results. |
| `Q3-009` | Source substitution | At least one domain is switched between two conforming source adapters without changing core evidence/claim/report code; differences remain attributable. | Vendor/source replacement requires core rewrite or loses lineage. | Substitution trial. |
| `Q3-010` | Source retirement | A source can be disabled/retired without deleting history, breaking old reports, or silently changing new coverage. | Retirement corrupts reproducibility or causes hidden fallback. | Retirement drill. |
| `Q3-011` | Jurisdiction terminology isolation | No NC-specific authority, terminology, caveat, rule, or contact instruction leaks into other lanes. | Semantic leakage occurs. | Language audit. |
| `Q3-012` | International representation | Lane C correctly represents administrative hierarchy, locale, units, dates, addresses, and source authorities without US-only coercion. | Non-US concepts are forced into misleading US semantics. | International model review. |
| `Q3-013` | CRS and geometry portability | All lane geometries transform, validate, measure, and query within configured tolerance across relevant CRSs. | Spatial errors or hidden CRS assumptions occur. | Spatial portability report. |
| `Q3-014` | Locale-safe output | Numbers, units, dates, names, and translated/local terms are rendered consistently and remain machine-readable. | Output is ambiguous, mistranslated, or lossy. | Locale tests. |
| `Q3-015` | Rulepack isolation | Jurisdiction/intent rules are versioned, independently testable, and cannot mutate unrelated rule behavior. | Rule additions alter existing outputs unexpectedly. | Rule regression report. |
| `Q3-016` | Fault injection | Timeout, 429, 5xx, malformed payload, empty result, partial response, stale version, schema drift, duplicate records, and corrupt geometry all fail closed. | Any injected failure creates false-clear or corrupt state. | Fault matrix. |
| `Q3-017` | Retry/idempotency | Retrying connector and report jobs creates no duplicate durable evidence, claims, artifacts, or audit events beyond documented attempt records. | Duplicate/conflicting business records appear. | Idempotency report. |
| `Q3-018` | Concurrency safety | Concurrent runs for same/different AOIs remain isolated, deterministic where expected, and free of lost updates. | Race condition, cross-run contamination, or duplicate completion occurs. | Concurrency test. |
| `Q3-019` | Existing-scope regression | All protected NC behavior, golden outputs, source-rights, safety language, and migrations pass unchanged unless an intentional versioned semantic change is approved. | Existing behavior regresses or tests are weakened. | CI report. |
| `Q3-020` | Backward report reproducibility | Old reports remain readable and attributable after adding new lanes/rules/sources. | Expansion breaks historical reports. | Historical replay. |
| `Q3-021` | Adapter removal | A new lane can be disabled/removed without breaking core startup, migrations, or existing jurisdictions. | Adapter becomes an undeletable core dependency. | Removal drill. |
| `Q3-022` | Performance non-regression | New lanes meet frozen p95 runtime/resource target and existing NC p95 regresses by no more than configured tolerance, recommended 10%. | Target fails. | Comparative load report. |
| `Q3-023` | Cost containment | Per-report connector/compute/storage costs remain within configured target for each lane; restricted-source degradation does not trigger uncontrolled fallback cost. | Cost target fails or is unmeasured. | Cost report. |
| `Q3-024` | Observability isolation | Logs, metrics, alerts, and run IDs identify source/jurisdiction failures without leaking another user/tenant’s data. | Failures are indistinguishable or data leaks across context. | Observability audit. |
| `Q3-025` | Documentation sufficiency | A fresh agent/developer can add a fixture, run a lane, diagnose failure, and understand source rights using repo docs only. | Chat history or maintainer memory is required. | Fresh-agent transcript. |
| `Q3-026` | Independent reproduction | A second operator reproduces all lanes from clean checkout/tag and controlled sources. | Reproduction fails. | Reproduction report. |
| `Q3-027` | No scope overclaim | Product/docs state exact lane/domain/source coverage and do not claim state-, nation-, or world-complete diligence. | Coverage is overstated. | Claim-language audit. |
| `Q3-028` | Non-US claim boundary | Lane C output explicitly distinguishes architecture portability from authoritative international diligence. | Architecture probe is marketed as validated international due diligence. | Report/doc audit. |
| `Q3-029` | Data export rights | Every lane’s export behavior follows source-specific redistribution constraints. | Export exceeds rights. | Export entitlement tests. |
| `Q3-030` | Migration/rollback compatibility | Expansion migrations apply from prior supported release with representative data and have rollback/forward-repair proof. | Upgrade loses data or cannot be repaired. | Migration drill. |


## 21A. Q3 sub-gate applicability

The Q3 criteria are shared contracts with explicit lane applicability.

| Sub-gate | Required criterion IDs |
|---|---|
| `Q3A` cross-state integration | Q3-001–006, Q3-009–011, Q3-013, Q3-015–027, Q3-029–030; Q3-003 is diagnostic |
| `Q3B` restricted/unavailable source | Q3-001–002, Q3-004–010, Q3-016–027, Q3-029–030; Q3-003 is diagnostic |
| `Q3C` non-US architecture probe | Q3-001–006, Q3-009–030 except Q3-007–008; Q3-003 is diagnostic |

A criterion may be satisfied with lane-specific evidence, but one lane's result cannot automatically satisfy another lane. Each result file uses gate ID `Q3A`, `Q3B`, or `Q3C` and includes the required shared criterion IDs.


## 22. Q3 required evidence package

```text
qualification/q3/<qualification-version>/
  protocol_ref.yaml
  lane_selection_and_scope.md
  jurisdiction_decisions/
  architecture_before_after.md
  dependency_graphs/
  source_rights_reviews/
  source_registry_snapshot.csv
  lane_case_hashes.json
  international_representation_review.md
  failure_injection_manifest.yaml
  source_substitution_results.md
  source_retirement_results.md
  idempotency_concurrency_results.json
  performance_baseline.json
  performance_results.json
  cost_results.json
  normalized_outputs/
  regression_results/
  independent_reproduction.md
  discrepancy_register.csv
  PASS_OR_FAIL.md
```

---


# IR — Input Resolution, Cadastral Identity, and AOI Integrity Overlay

## Applicability

IR applies whenever users identify a place through an address, parcel/APN, coordinates, map click, uploaded geometry, named locality, multi-parcel assemblage, or generated candidate region.

## IR hard criteria

| ID | PASS | FAIL |
|---|---|---|
| `IR-001` | Every input retains its original representation and a versioned resolution record. | Resolution overwrites the user input or cannot be audited. |
| `IR-002` | Ambiguous addresses, parcel IDs, locality names, or geocodes block decision-relevant processing until disambiguated. | The system silently selects one candidate. |
| `IR-003` | Geocoder/provider, match type, score/precision, timestamp, and normalization steps are recorded. | A location result has no resolution provenance. |
| `IR-004` | Parcel/APN uniqueness is scoped by jurisdiction and time; duplicate or reused identifiers are handled. | APNs are treated as globally or permanently unique. |
| `IR-005` | Parcel split, merge, retirement, supersession, and geometry-version relationships are represented where available. | Historical and current parcels are silently conflated. |
| `IR-006` | Cross-jurisdiction, enclave, boundary, and overlapping-authority cases identify every applicable authority or remain explicitly unresolved. | One jurisdiction is assumed from centroid alone. |
| `IR-007` | Multi-parcel and multipart AOIs preserve component identity and aggregation rules. | Assemblages collapse into an unauditable polygon. |
| `IR-008` | User-drawn/uploaded geometry is validated, repaired only under explicit policy, and retains original plus normalized versions. | Repair silently changes intent. |
| `IR-009` | Generated candidate regions record algorithm, constraints, source versions, and exclusion logic. | Automatically designed regions cannot be reproduced. |
| `IR-010` | Physical road proximity is never represented as legal access without authoritative evidence. | Spatial adjacency becomes a legal-access claim. |
| `IR-011` | Input-resolution tests include wrong-result traps, near-boundary addresses, duplicate street names, rural routes, and missing parcel matches. | Only easy exact matches are tested. |
| `IR-012` | AOI identity is preserved through evidence, claims, report runs, exports, corrections, and reruns. | Output can no longer be tied to the exact analyzed geometry/version. |
| `IR-013` | Unsupported input modes fail explicitly and preserve recoverable state. | Unsupported input is coerced into a misleading AOI. |
| `IR-014` | Resolution confidence is separate from land-diligence suitability/confidence. | Location uncertainty is hidden inside a general score. |
| `IR-015` | A wrong-AOI incident can identify affected reports and trigger invalidation/notification. | Wrong-place analysis cannot be recalled. |

---

# DB — PostgreSQL/PostGIS Integrity and Operability Overlay

## Applicability

DB applies to every milestone or release that uses PostgreSQL/PostGIS as the canonical system of record.

## DB hard criteria

| ID | PASS | FAIL |
|---|---|---|
| `DB-001` | Supported PostgreSQL, PostGIS, PROJ/GDAL-related versions and upgrade policy are frozen and tested. | Runtime versions are implicit or unsupported. |
| `DB-002` | Migrations apply from empty DB and every supported prior release using representative data. | Only greenfield migration is proven. |
| `DB-003` | Required PK/FK/unique/check/not-null/exclusion constraints enforce domain invariants at the database boundary where appropriate. | Invalid core state can be persisted through another code path. |
| `DB-004` | Evidence/claim/report/audit writes are transactionally atomic according to documented boundaries. | Partial commits create unsupported claims or broken lineage. |
| `DB-005` | Concurrency/isolation tests cover duplicate job claims, lost updates, write skew, deadlocks, retries, and idempotency. | Concurrent work corrupts or duplicates durable state. |
| `DB-006` | Geometry columns have explicit SRID/type rules and appropriate GiST/SP-GiST/BRIN or justified index strategy. | Spatial storage/query behavior is accidental. |
| `DB-007` | Representative spatial and lineage queries have reviewed plans and meet frozen latency/resource targets. | Sequential scans or pathological plans violate targets without mitigation. |
| `DB-008` | Statistics, autovacuum, analyze, bloat, long transaction, and index-maintenance policies are monitored. | DB health degradation is unmanaged. |
| `DB-009` | Connection pooling, statement/lock/idle timeouts, retry policy, and max-connection budgets are configured and load-tested. | Connection exhaustion or indefinite locks can disable the system. |
| `DB-010` | Database roles follow least privilege; application, migration, read-only, backup, and operator capabilities are separated. | The normal app runs as owner/superuser. |
| `DB-011` | Multi-tenant deployments prove tenant isolation at query, ORM/repository, job, export, and optionally RLS layers. | Any cross-tenant row/artifact access occurs. |
| `DB-012` | Backup plus WAL/PITR or approved equivalent is configured, monitored, and restored into a clean environment. | Backup success is asserted without restore proof. |
| `DB-013` | RPO/RTO drills include DB, object artifacts, source manifests, and encryption keys/config required for recovery. | Restored DB cannot reproduce reports or access artifacts. |
| `DB-014` | Migration failure has tested rollback or forward-repair, with data-loss boundaries declared. | A failed migration strands the deployment. |
| `DB-015` | Large-table migration and backfill behavior is tested at representative volume and within maintenance/availability policy. | Migration causes unbounded lock or outage. |
| `DB-016` | Retention/deletion/archival preserves legal, license, privacy, audit, and reproducibility requirements. | Purge either destroys required history or retains prohibited data. |
| `DB-017` | Schema, seed, reference, and ruleset data are versioned; manual production edits are prohibited or audited through controlled tooling. | Hidden DB state changes behavior. |
| `DB-018` | Replicas/failover, if used, have lag, read-consistency, promotion, and stale-read policy tested. | Reports use stale/inconsistent replicas without disclosure. |
| `DB-019` | Corruption/integrity checks and restore validation include critical lineage counts, hashes, and referential checks. | Restore is syntactically successful but semantically incomplete. |
| `DB-020` | Capacity forecasts include rows, indexes, geometry size, WAL, backups, audit events, and report/source history. | Storage growth threatens correctness or recovery unobserved. |

---

# R — Regulatory, Professional-Scope, and Claim-Applicability Overlay

## Applicability

R is profile- and jurisdiction-dependent. It does not encode legal advice; it requires documented applicability decisions and qualified review where risk warrants it.

## R hard criteria

| ID | PASS | FAIL |
|---|---|---|
| `R-001` | A versioned applicability register maps product features, users, geographies, data, and deployment to potentially relevant legal/regulatory/professional regimes. | Compliance is assumed from generic disclaimers. |
| `R-002` | Product scope explicitly distinguishes screening from licensed legal, surveying, engineering, appraisal, brokerage, environmental, insurance, and lending activity. | Features cross a professional boundary without review. |
| `R-003` | Residential discovery/recommendation behavior has documented fair-housing/anti-steering review. | Residential location ranking uses protected classes or proxies. |
| `R-004` | Valuation, AVM, collateral, lending, insurance, tenant/employment, or consumer-reporting uses remain disabled until a dedicated applicability and control profile passes. | High-stakes regulated use is enabled by implication. |
| `R-005` | Public-record, owner-data, privacy, marketing, terms-of-use, and source-license obligations are tracked per jurisdiction/source. | “Public” is treated as unrestricted. |
| `R-006` | International operation records data-residency, cross-border transfer, language, local representative, and local professional-scope obligations where applicable. | Non-US deployment reuses US assumptions. |
| `R-007` | Product terms, disclaimers, user confirmations, and support language match actual capability and do not waive non-waivable duties. | Disclaimers contradict behavior or create false reassurance. |
| `R-008` | Material regulatory/source-terms changes have monitoring, owner, review cadence, and kill-switch/invalidation path. | A changed rule or revoked right remains active unnoticed. |
| `R-009` | Qualified external review is obtained before enabling a materially new high-risk claim class or jurisdiction; reviewer scope and conclusions are recorded. | Coding agents or developers make final applicability decisions alone. |
| `R-010` | Marketing, sales, report labels, and API documentation claim only passed scope and name unqualified domains/geographies. | Commercial language outruns qualification evidence. |

---

# F — Field Surveillance, Drift, and Post-Release Learning Overlay

## Applicability

F applies to beta and production use. Pre-release benchmarks cannot establish continuing validity after sources, rules, users, or field conditions change.

## F hard criteria

| ID | PASS | FAIL |
|---|---|---|
| `F-001` | Production discrepancies, complaints, professional corrections, source notices, and near misses enter a governed intake. | Field failures remain informal or lost in support channels. |
| `F-002` | Each material field discrepancy is classified, linked to affected scope, and assigned an owner/severity/deadline. | Failures cannot drive remediation. |
| `F-003` | A representative production sample is periodically reviewed against available later truth or professional follow-up. | Benchmark performance is assumed to persist indefinitely. |
| `F-004` | Source schema, coverage, cadence, rights, and statistical/distribution drift are monitored. | Upstream drift silently changes behavior. |
| `F-005` | Confidence/severity calibration and unknown rates are monitored by geography/domain/source state. | Calibration degradation is hidden in aggregate metrics. |
| `F-006` | Critical false reassurance, rights breach, wrong-AOI, or cross-user leak triggers immediate containment and gate invalidation. | Serious incidents wait for routine release cadence. |
| `F-007` | Affected reports/users can be identified, notified where appropriate, invalidated, and regenerated. | Known-bad outputs remain active. |
| `F-008` | Field findings update regression cases, risk taxonomy, domain profiles, and sealed-case strategy without contaminating the future pool. | Incidents do not strengthen future qualification. |
| `F-009` | Requalification cadence is risk- and source-volatility-based, not only calendar-based. | Fast-changing sources retain stale qualification. |
| `F-010` | User behavior/misuse signals are reviewed, including detached screenshots, caveat stripping, and prohibited downstream use. | Predictable misuse is ignored. |
| `F-011` | Post-release metrics distinguish product defects, source limitations, reviewer disagreement, and out-of-scope requests. | All problems are attributed to “bad data” or users. |
| `F-012` | A periodic field-surveillance report records adverse findings, corrective actions, residual risk, and current claim boundaries. | Only favorable usage metrics are published internally. |

---

# DQ — Geospatial and General Data-Quality Overlay

## 23. Applicability

DQ applies to every source and derived dataset used in Q1–Q3 or production. It operationalizes the principal geospatial data-quality dimensions: completeness, logical consistency, positional accuracy, temporal quality, thematic accuracy, and usability/lineage.

## 24. DQ hard criteria

| ID | PASS | FAIL |
|---|---|---|
| `DQ-001` | Every active source has a versioned data-product/profile record. | Source quality is known only informally. |
| `DQ-002` | Completeness omission and commission are measured or explicitly bounded for each claimed domain/geography. | Coverage is assumed because a source returned data. |
| `DQ-003` | Logical/topological consistency checks pass or defects are quarantined. | Invalid relationships enter evidence silently. |
| `DQ-004` | Positional accuracy/tolerance is declared and propagated into spatial claims. | Spatial precision is overstated. |
| `DQ-005` | Temporal validity, update cadence, staleness threshold, and observation date are known or explicitly unknown. | Old data is treated as current. |
| `DQ-006` | Thematic/classification accuracy is measured or caveated for categorical layers. | Categories are treated as authoritative without validation. |
| `DQ-007` | Units, null semantics, sentinel values, and code lists are normalized and tested. | Source-specific null/code behavior corrupts meaning. |
| `DQ-008` | Duplicate, overlap, gap, and geometry-repair policies are deterministic and auditable. | Automatic repair changes meaning silently. |
| `DQ-009` | Source-to-normalized-field mappings are versioned and contract-tested. | Schema drift silently remaps fields. |
| `DQ-010` | Derived calculations record method, parameters, input versions, and uncertainty/tolerance. | Derived evidence cannot be reproduced. |
| `DQ-011` | Data-quality failures create quarantined/failed states, not normal evidence. | Bad records flow into claims. |
| `DQ-012` | Cross-source agreement/disagreement is measured for overlapping critical domains. | Conflicts are undiscovered or hidden. |
| `DQ-013` | Coverage maps expose where a source/domain is not evaluated. | Users infer coverage from absence. |
| `DQ-014` | Data-retirement/supersession preserves historical reproducibility. | New data overwrites history. |
| `DQ-015` | Every quality metric has an owner, threshold, review date, and evidence path. | Quality profiles are stale or ownerless. |
| `DQ-016` | Qualification outputs disclose material source-quality limits. | Internal quality caveats disappear in user output. |
| `DQ-017` | Source record identity and crosswalks are stable/versioned across vendors and refreshes. | The same real-world feature is duplicated or conflated silently. |
| `DQ-018` | Citation anchors, content hashes, retrieval metadata, and preservation mode remain resolvable for the qualification validity period. | Evidence references rot or cannot be audited. |
| `DQ-019` | Data-quality metrics are reported per qualified geography/domain, not only globally. | Good coverage elsewhere masks a local failure. |
| `DQ-020` | Sampling/measurement bias and known blind spots are documented for every derived or modeled layer. | Model-derived coverage is treated as uniform observation. |
| `DQ-021` | Parsed zoning/legal/source documents retain page/section/table/figure anchors, content hashes, extraction method, and extraction confidence. | Extracted text cannot be traced to the source location. |
| `DQ-022` | OCR/table/figure extraction errors and low-confidence regions are flagged and routed to review or unknown state. | Garbled extraction becomes normal evidence. |
| `DQ-023` | Visual map/tiles used only for presentation are not treated as analytical source data unless separately approved and profiled. | Rendered pixels or consumer map tiles silently become authoritative evidence. |

---

# S — Security, Privacy, Compliance, and Misuse Overlay

## 25. S hard criteria

| ID | PASS | FAIL |
|---|---|---|
| `S-001` | A current threat model covers users, APIs, Postgres/PostGIS, object storage, connectors, jobs, exports, admin/review flows, and AI components if enabled. | Material attack surfaces are unmodeled. |
| `S-002` | A frozen OWASP ASVS or equivalent verification profile is selected; all applicable release-blocking requirements pass. | Security target is undefined or selectively applied. |
| `S-003` | Authentication, session handling, and credential recovery are tested in deployed context. | Auth controls exist only as local stubs. |
| `S-004` | Authorization and tenant/workspace isolation tests prove deny-by-default behavior across API, UI, jobs, DB queries, exports, and artifacts. | Any horizontal/vertical privilege leak occurs. |
| `S-005` | Secrets are externalized, rotated, scanned, and absent from repo/logs/artifacts. | Secret exposure occurs. |
| `S-006` | Dependency lock, SBOM, provenance/attestation, vulnerability scan, and update policy exist. | Released dependencies are untracked or critically vulnerable. |
| `S-007` | SAST, DAST/API security testing, injection tests, and manual security review pass for released scope. | Critical/high finding remains. |
| `S-008` | GeoJSON/geometry bombs, oversized polygons, decompression bombs, malicious documents, SSRF, path traversal, XSS, SQL injection, and resource-exhaustion inputs fail safely. | Any input crosses a security/resource boundary. |
| `S-009` | Rate limits, quotas, job bounds, and cost-abuse controls are enforced. | A user can cause unbounded compute/vendor cost. |
| `S-010` | Audit logs are tamper-evident enough for decision-impacting and security actions, with actor/time/object correlation. | Sensitive actions are unattributable. |
| `S-011` | Personal-data inventory, purpose, legal/contractual basis, minimization, retention, deletion, and access rules are documented and tested. | Personal data is collected or retained without control. |
| `S-012` | Owner names, addresses, search history, notes, and exports are exposed only where purpose and rights permit. | Unnecessary personal/property data is broadly exposed. |
| `S-013` | Encryption in transit and at rest is active for production systems and backups. | Sensitive production data is unencrypted. |
| `S-014` | Privacy deletion/export requests can be executed without destroying required audit/provenance records improperly. | Privacy rights and audit integrity cannot coexist. |
| `S-015` | Fair-housing/anti-steering tests prove protected-class data and proxies are absent from residential recommendation logic. | Steering/proxy behavior exists. |
| `S-016` | Source-license, attribution, redistribution, caching, retention, and AI-use restrictions are enforced by code/config where applicable. | Compliance relies only on developer memory. |
| `S-017` | Security/privacy incidents have runbooks, notification logic, affected-record queries, and exercised drills. | Incident response is untested. |
| `S-018` | Independent security review or penetration test has no unresolved critical/high findings before production-grade claim. | Review absent or serious findings open. |
| `S-019` | Qualification and production data are separated; sealed acceptance data cannot leak into training, logs, demos, or ordinary dev access. | Acceptance confidentiality is breached. |
| `S-020` | Every accepted medium residual risk has owner, rationale, mitigation, expiry, and review date. | Residual security/privacy risk is unowned. |
| `S-021` | Sensitive geospatial information and high-risk locations have classification, access, export, and logging rules. | Exact location data creates unmanaged safety/security exposure. |
| `S-022` | Logs, traces, analytics, screenshots, and support artifacts are tested for secrets, owner data, precise-location data, and participant data leakage. | Observability becomes a secondary data leak. |
| `S-023` | Vulnerability findings are triaged for applicability/reachability with evidence; `NOT_AFFECTED` is distinct from risk acceptance. | High-severity scanner output is ignored or accepted without proof. |
| `S-024` | Abuse cases cover stalking/doxxing, discriminatory steering, bulk owner harvesting, sensitive-site discovery, report tampering, and cost/resource abuse. | Predictable harmful use is untested. |
| `S-025` | Data residency and cross-border processing controls are enforced when the selected profile requires them. | International/user data crosses an unapproved boundary. |

---

# A — Accessibility and Human-Factors Overlay

## 26. A hard criteria

| ID | PASS | FAIL |
|---|---|---|
| `A-001` | All applicable WCAG 2.2 Level A and AA success criteria pass for released web content/workflows. | Any applicable A/AA criterion fails. |
| `A-002` | Automated accessibility scanning is supplemented by manual keyboard, focus, screen-reader, zoom/reflow, contrast, error, and dynamic-update testing. | Conformance relies only on an automated score. |
| `A-003` | Every critical workflow is operable without a pointer device. | A critical task is keyboard-inaccessible. |
| `A-004` | Maps and spatial findings have nonvisual textual equivalents sufficient for the decision task. | Essential information exists only visually. |
| `A-005` | Color is not the sole carrier of severity/status; legends and text remain understandable. | Risk meaning depends only on color. |
| `A-006` | Critical caveats, unknowns, and source failures are prominent, plain-language, and not hidden behind optional interaction. | Safety information is obscure. |
| `A-007` | Error messages identify what failed, what was preserved, and what the user can do next. | Errors imply success or provide no recovery. |
| `A-008` | Desktop/mobile and Windows browser matrix meets configured support targets for critical workflows. | A supported environment cannot complete the workflow. |
| `A-009` | User testing includes at least one participant or specialist evaluation for keyboard and screen-reader/low-vision use. | Accessibility is only theoretically asserted. |
| `A-010` | Human factors review finds no dark pattern, forced overconfidence, hidden uncertainty, or deceptive ranking presentation. | UI nudges users toward unsupported certainty. |
| `A-011` | Exported HTML/PDF and shared artifacts meet the configured accessibility profile or clearly provide an equivalent accessible representation. | Accessibility ends at the web UI. |
| `A-012` | Reading level, terminology, abbreviations, and uncertainty language are validated for each target persona without removing precision. | Reports are technically correct but practically incomprehensible. |
| `A-013` | Map scale, symbology, overlap, uncertainty, and source-coverage legends do not imply precision beyond the data. | Visualization creates false spatial certainty. |
| `A-014` | Critical tasks remain usable under zoom, high contrast, reduced motion, slow network, and recoverable session interruption. | Supported accessibility/environment conditions break the workflow. |

---

# M — Maintainability, Modularity, and Test-Effectiveness Overlay

## 27. M hard criteria

| ID | PASS | FAIL |
|---|---|---|
| `M-001` | Dependency-boundary tests enforce domain layering and prevent core-to-adapter imports. | Architecture depends on convention only. |
| `M-002` | New sources, jurisdictions, intents, report sections, and renderers use documented extension interfaces. | Ordinary extension requires core rewrites. |
| `M-003` | No circular dependency exists across core domain modules. | Circular dependency is present. |
| `M-004` | Critical rule, evidence, geometry, rights, and report logic has unit, integration, DB, regression, and negative-path coverage appropriate to risk. | A critical path has only happy-path tests. |
| `M-005` | Mutation score for configured critical modules meets target, recommended >=80%, with surviving critical mutants reviewed. | Tests pass while important logic mutations survive unchecked. |
| `M-006` | Property-based/fuzz tests cover geometry, serialization, idempotency, and malformed-source invariants. | Edge behavior relies only on hand-picked examples. |
| `M-007` | Flaky-test rate remains below configured ceiling, recommended <1%; quarantine cannot satisfy a pass claim. | Reliability depends on reruns or broad skips. |
| `M-008` | Test categories are reported separately: domain, DB/PostGIS, connector, report, UI, security, governance, and artifact/static checks. | A large total obscures weak behavioral coverage. |
| `M-009` | Complexity/size thresholds are configured; modules exceeding them require decomposition plan or approved rationale with tests. | Central modules grow without control. |
| `M-010` | Public/domain contracts are versioned and backward compatibility is tested. | Breaking changes occur silently. |
| `M-011` | Representative prior-release migration, upgrade, and replay tests pass. | Only empty-database migration is tested. |
| `M-012` | Clean Windows bootstrap and canonical PowerShell verification pass from a path containing spaces. | Windows-native workflow is unproven. |
| `M-013` | CI independently proves supported non-Windows production/runtime environment if different. | Local and deployed behavior diverge untested. |
| `M-014` | Documentation routing remains concise; active state, manifest, plan, and milestone records agree. | Agents receive stale/conflicting control state. |
| `M-015` | A fresh agent completes a bounded maintenance/change task without chat history and without violating invariants. | Repo governance is not operationally usable. |
| `M-016` | Deleting/disabling an optional adapter or feature does not break unrelated core behavior. | Optional modules are entangled. |
| `M-017` | Toolchain, dependency lock, Python/runtime, PostgreSQL/PostGIS, locale, and timezone needed for reproduction are pinned or bounded and recorded. | Results depend on an unknown environment. |
| `M-018` | Critical code/config/data has an accountable owner and maintenance/deprecation path; single-maintainer risk is recorded. | Essential behavior is ownerless. |
| `M-019` | Skips, xfails, quarantines, and disabled gates are machine-reported with owner, reason, expiry, and no release-blocking coverage loss. | Test suppression hides failure. |
| `M-020` | Dead adapters, stale rules, unused dependencies, and obsolete compatibility code are periodically identified and removed through protected tests. | Extension surface grows without control. |

---

# O — Hosted Operations, Reliability, Recovery, and Scalability Overlay

## 28. O hard criteria

| ID | PASS | FAIL |
|---|---|---|
| `O-001` | The exact tested tag/digest is deployed through documented CI/CD with provenance. | Production differs from tested artifact. |
| `O-002` | Environment configuration and secrets are externalized; startup validates required settings. | Hidden local configuration is required. |
| `O-003` | Production Postgres/PostGIS and artifact storage persist across restart/redeploy. | State is ephemeral or manually reconstructed. |
| `O-004` | Upgrade from the prior supported release with representative data passes and preserves lineage/audit semantics. | Upgrade loses or corrupts data. |
| `O-005` | Backup completes and restore into a clean environment meets frozen RPO/RTO targets. | Restore is untested or misses target. |
| `O-006` | Rollback or forward-repair for application and migration failure is exercised. | Failed release cannot be recovered safely. |
| `O-007` | Availability/error-budget/SLO targets are defined and met during staging/beta observation window. | Targets absent or missed. |
| `O-008` | p50/p95/p99 API and report-job latency meet configured targets under representative workload. | Performance target fails. |
| `O-009` | Concurrent and batch workload target completes without lost, duplicate, cross-contaminated, or indefinitely stuck jobs. | Correctness fails under load. |
| `O-010` | Queue retry, lease, cancellation, timeout, dead-letter, and idempotency behavior is tested. | Jobs duplicate or disappear. |
| `O-011` | Upstream source outage/degradation triggers truthful partial reports, metrics, and alerts. | Outage creates false-clear output or silent failure. |
| `O-012` | Structured logs, traces/correlation IDs, metrics, and dashboards cover report, connector, DB, auth, export, and job lifecycle. | Operators cannot diagnose failures. |
| `O-013` | Release-blocking alerts reach a real monitored destination within configured detection/notification target. | Alerts exist only as config files or are not delivered. |
| `O-014` | On-call/incident runbooks are exercised for source outage, DB issue, bad release, rights revocation, data defect, and security event. | Runbooks are static and untested. |
| `O-015` | Data correction/recall drill identifies affected reports and records notification/regeneration outcome. | Known bad data cannot be operationally contained. |
| `O-016` | Retention, archival, deletion, and legal/license expiration jobs execute correctly. | Data remains indefinitely or disappears improperly. |
| `O-017` | Capacity model covers DB growth, geometry indexes, artifacts, logs, source snapshots, and qualification evidence. | Storage/capacity failure is unmanaged. |
| `O-018` | Disaster-recovery dependency inventory and single-point-of-failure review are complete. | Critical unmitigated dependency is unknown. |
| `O-019` | Deployment smoke tests exercise authenticated intake-to-report-to-export path. | Deployment is considered healthy from process startup alone. |
| `O-020` | Accountable engineering, security/privacy, data-governance, product, and operations roles sign off. One person may hold multiple roles in a small project, but security/data-risk review requiring independence must be performed independently. | Responsibility is absent or independence-sensitive review is self-certified. |
| `O-021` | Clock, timezone, locale, and source-observation timestamps are synchronized and monitored. | Freshness, expiry, or ordering depends on drifting clocks. |
| `O-022` | Maintenance-mode and partial-dependency behavior preserve truthful status and recoverable work. | Planned maintenance creates false success or data loss. |
| `O-023` | Third-party service/vendor dependency inventory includes exit, substitution, outage, quota, and terms-change plans. | One provider failure or termination strands the product. |
| `O-024` | Representative soak/endurance testing detects resource leaks, queue accumulation, DB bloat, and long-run degradation. | Short load tests hide operational decay. |
| `O-025` | Post-incident review produces tracked corrective actions, regression tests, and qualification invalidation decisions. | Incidents are closed without systemic learning. |

---

# E — Economic and Resource-Viability Overlay

## 29. E hard criteria

Exact numeric targets must be selected before execution. `null` or `TBD` blocks a commercial production claim.

| ID | PASS | FAIL |
|---|---|---|
| `E-001` | p50/p95 total cost per completed and degraded report is measured and within target. | Cost is unknown or exceeds target. |
| `E-002` | Vendor/source royalty and minimum-commitment costs are included, not only compute cost. | Unit cost omits contractual data cost. |
| `E-003` | Median/p95 human-review and support time per report is measured and within target. | Manual labor makes the workflow economically infeasible. |
| `E-004` | Storage, egress, map/tile, LLM if enabled, queue, logging, and backup costs are allocated. | Material cost categories are unmeasured. |
| `E-005` | Batch/backfill and source-refresh worst-case cost is modeled and bounded. | A refresh can cause uncontrolled spend. |
| `E-006` | Rate limits, quotas, and plan entitlements prevent negative-margin abuse. | A user can consume unbounded cost under fixed pricing. |
| `E-007` | Expected commercial gross margin or approved internal budget envelope meets target for the intended pricing/usage model. | Product cannot support its intended operating model. |
| `E-008` | Data-license scaling and export restrictions are compatible with forecast users/volume. | Commercial growth would violate rights or economics. |
| `E-009` | Cost alerts and per-source/per-run attribution function in staging/production. | Cost spikes cannot be attributed. |
| `E-010` | A sensitivity analysis covers low, expected, and high usage plus vendor-price/source-change scenarios. | Viability depends on one optimistic assumption. |
| `E-011` | Cost is compared with measured user time saved, avoided rework, or other frozen value metric; commercial claims are not inferred from cost alone. | Economically cheap output is called valuable without outcome evidence. |
| `E-012` | Vendor concentration and contract-renewal sensitivity have an approved mitigation or accepted bounded risk. | One pricing/terms change makes the service nonviable without warning. |

---

# G — Governance, Release, Expiry, and Residual-Risk Overlay

## 30. G hard criteria

| ID | PASS | FAIL |
|---|---|---|
| `G-001` | Machine-readable status records every gate, criterion, result, tested commit, evidence path, owner, reviewer, date, expiry, and invalidation reason. | Qualification exists only in prose. |
| `G-002` | CI validates status schema, evidence paths, prerequisite ordering, and absence of illegal `PASS` states. | Status can drift from evidence. |
| `G-003` | Gate prerequisites are enforced: P0 before Q1–Q3; Q1 before Q2; Q1/Q2 before expansion claim; overlays before production claim. | Higher claim bypasses lower proof. |
| `G-004` | Every `N/A` has scope rationale, approver, evidence, and expiry; prohibited N/A uses are rejected. | N/A becomes an escape hatch. |
| `G-005` | Safety-critical criteria cannot be waived. | Critical false reassurance, lineage, rights, or tenant isolation is waived. |
| `G-006` | Noncritical accepted risk has named owner, rationale, mitigation, review date, and expiry. | Residual risk is ownerless or permanent. |
| `G-007` | Qualification validity periods are defined and monitored; expired gates cannot support release claims. | Old results are treated as current indefinitely. |
| `G-008` | Change-impact mapping invalidates affected gates automatically or through reviewed release workflow. | Material changes leave stale passes active. |
| `G-009` | Every discovered material defect updates the risk taxonomy, regression suite, and affected qualification status. | Incidents do not strengthen future tests. |
| `G-010` | Release notes identify schema, rule, source, report-semantic, rights, and qualification changes. | Users/operators cannot identify behavior changes. |
| `G-011` | Product claims and marketing text are bounded by passed gates and exact coverage. | Claims exceed evidence. |
| `G-012` | An independent adversarial review is completed for every production release candidate; critical/high findings are resolved. | Same implementation team performs the only review. |
| `G-013` | Sealed cases are rotated after disclosure/use and a future acceptance pool remains uncontaminated. | No independent future holdout remains. |
| `G-014` | Raw qualification evidence is retained under controlled policy long enough to audit claims. | Evidence is unavailable for challenge. |
| `G-015` | The qualification report includes failures, limitations, exclusions, conflicts, uncertainty, and residual risks—not only pass metrics. | Report is promotional rather than auditable. |
| `G-016` | A final release decision records exact passed classification and explicitly lists what is not qualified. | “Production-grade” is asserted without boundaries. |
| `G-017` | A machine-readable criterion catalog is canonical; Markdown tables, schemas, targets, and status records are generated from or validated against it. | Prose and machine state can diverge. |
| `G-018` | Qualification schemas enforce PASS/FAIL/BLOCKED/N/A semantics, unique criterion IDs, prerequisites, evidence, expiry, and exact artifact identity. | Illegal PASS states validate. |
| `G-019` | Change classes map deterministically to affected gates and require reviewed invalidation decisions. | Maintainers decide ad hoc whether a pass remains valid. |
| `G-020` | Protected qualification artifacts are content-hashed/signed and access-controlled according to role. | Criteria or evidence can be changed without detection. |
| `G-021` | Competing objectives and exceptions are resolved through an ADR/risk decision, not by silently weakening a gate. | Convenience overrides qualification without trace. |
| `G-022` | The always-loaded agent context references qualification state concisely and does not bulk-load raw evidence/history. | Governance causes context bloat or stale agent behavior. |

---


# W — Windows-Native Development and Operator Environment Overlay

## Applicability

W applies because the canonical local development/operator environment is Windows and the repository is expected to work from a normal Windows directory, including paths containing spaces and potentially a OneDrive-synchronized repo checkout.

| ID | PASS | FAIL |
|---|---|---|
| `W-001` | PowerShell commands/scripts are canonical for Windows setup, verification, DB operation, and qualification validation. | Windows users must translate Bash instructions manually. |
| `W-002` | A clean supported Windows machine can bootstrap and verify from documented prerequisites without Git Bash/WSL dependence. | Hidden Unix tooling is required. |
| `W-003` | Critical workflows pass from paths containing spaces, Unicode, and configured long-path limits. | Path parsing or MAX_PATH assumptions break operation. |
| `W-004` | Repository and generated paths have no case-only name collisions or case-sensitive import assumptions. | Behavior differs because NTFS is normally case-insensitive. |
| `W-005` | `.gitattributes`, newline policy, encoding, and script invocation prevent CRLF/LF or BOM corruption. | Line ending/encoding changes break SQL, scripts, fixtures, or hashes. |
| `W-006` | Operation does not require symlink privileges, administrator rights, or execution-policy weakening unless explicitly justified and tested. | Normal Windows security posture prevents setup. |
| `W-007` | Docker Desktop/Postgres/PostGIS workflows, ports, volumes, startup, shutdown, and health checks are tested on Windows. | DB proof exists only on Linux. |
| `W-008` | Source repo may be synchronized, but PostgreSQL data directories, object-store data, caches, secrets, and active job state are kept outside OneDrive/sync folders unless a tested safe design exists. | Sync software can corrupt, lock, duplicate, or roll back runtime state. |
| `W-009` | Atomic write/rename, file-lock, antivirus/indexer, temp-file, and cleanup behavior is tested for generated reports and state files. | Windows file semantics cause partial or stuck artifacts. |
| `W-010` | `windows-latest` or equivalent Windows CI executes the canonical PowerShell verification and path/line-ending tests. | Windows support is documentation-only. |
| `W-011` | Supported Windows/Python/Docker Desktop/browser versions are frozen and have an upgrade policy. | “Windows supported” has no version boundary. |
| `W-012` | Windows credential/secret storage and environment-variable handling avoid plaintext persistence and shell-history leakage. | Local credentials leak through scripts, profiles, logs, or command history. |

---

# CG — Conditional Candidate Generation, Search, and Ranking Overlay

## Applicability

CG becomes release-blocking when the system automatically generates, filters, ranks, recommends, or alerts on candidate parcels/areas. It is not required for analysis-only operation.

| ID | PASS | FAIL |
|---|---|---|
| `CG-001` | The candidate universe, geographic boundary, time window, listing/parcel inventory, and known coverage gaps are frozen per run. | Search completeness is implied from an unknown universe. |
| `CG-002` | User hard constraints, soft preferences, exclusions, priorities, and default assumptions are explicit and versioned. | Hidden defaults determine candidates. |
| `CG-003` | Hard constraints are applied deterministically with evidence and fail closed when required data is unavailable. | Missing data is treated as satisfying an exclusion constraint. |
| `CG-004` | Soft scoring/ordering is transparent, decomposable, versioned, and separate from confidence/data completeness. | One opaque universal score controls ranking. |
| `CG-005` | Weight and threshold sensitivity is tested; small plausible changes do not cause unexplained rank instability. | Ranking is arbitrary or brittle. |
| `CG-006` | Candidate-generation recall is evaluated against a sealed set of suitable/eligible cases and known exclusion traps. | The engine can omit strong candidates without measurement. |
| `CG-007` | False-exclusion and opportunity-loss rates meet frozen targets, with critical false exclusions separately reported. | Useful candidates are silently discarded beyond target. |
| `CG-008` | Duplicate, overlapping, subdivided, merged, stale, withdrawn, or re-listed candidates are resolved and lineage-preserved. | The shortlist contains duplicate or obsolete opportunities. |
| `CG-009` | Spatial diversity/deduplication rules are explicit and cannot hide many near-equivalent candidates without disclosure. | Ranking creates artificial variety or concentration. |
| `CG-010` | Every candidate and exclusion is traceable to input inventory, source versions, constraints, calculations, and rule/score version. | A shortlist cannot be reproduced. |
| `CG-011` | Unknown, stale, restricted, or unavailable candidate attributes are visible and affect confidence rather than becoming favorable defaults. | Data gaps improve rank. |
| `CG-012` | Protected classes, demographic proxies, neighborhood desirability proxies, and residential steering signals are absent from candidate generation. | Automated search steers housing choices unlawfully or deceptively. |
| `CG-013` | Generated-region algorithms record geometry method, parameters, objective, constraints, seed/randomness, and source versions. | Automatically designed AOIs cannot be recreated. |
| `CG-014` | Repeated pinned runs are semantically reproducible; stochastic search has frozen seeds or stability bounds. | Candidate lists change unpredictably. |
| `CG-015` | Users can inspect why a candidate was included/excluded and can override soft preferences without bypassing hard safety/rights constraints. | Ranking is unchallengeable or safety constraints are casually bypassed. |
| `CG-016` | Alerts/new-candidate detection handle source refresh, duplicate events, backfill, late data, and withdrawal correctly. | Users receive missing, duplicated, or stale opportunity alerts. |
| `CG-017` | Batch/search performance and cost meet frozen candidate-volume and refresh targets. | Search utility collapses or cost becomes unbounded at intended scale. |
| `CG-018` | Adversarial queries, extreme weights, impossible constraints, empty universes, and conflicting preferences produce explicit recoverable outcomes. | Edge inputs create fabricated candidates or misleading success. |

---

# FIN — Conditional Valuation, Investment, and Financial-Decision Overlay

## Applicability

FIN becomes release-blocking if the product estimates value, return, liquidity, investment attractiveness, financing suitability, insurance suitability, or produces appraisal/AVM-like outputs. It is not required while those outputs remain disabled and explicitly unqualified.

| ID | PASS | FAIL |
|---|---|---|
| `FIN-001` | The exact financial claim class, intended users, decision context, jurisdiction, and prohibited downstream uses are frozen. | Generic “investment insight” hides a regulated/high-stakes use. |
| `FIN-002` | Market, transaction, listing, tax, cost, and comparable data have approved rights, provenance, temporal alignment, and survivorship-bias controls. | Backtests use unavailable/future/biased data. |
| `FIN-003` | Train/tune/validation/acceptance time periods and geographies prevent temporal, entity, parcel, and neighborhood leakage. | The model sees its test outcome indirectly. |
| `FIN-004` | Out-of-time and out-of-geography validation meets frozen error, calibration, coverage, and interval targets. | In-sample fit is treated as predictive validity. |
| `FIN-005` | Comparable selection and adjustment are explainable, reproducible, and reviewed for inappropriate proxy use. | Value is driven by opaque or discriminatory comparables. |
| `FIN-006` | Estimates include uncertainty/intervals and data sufficiency; low-data cases become unknown or wide-range, not false precision. | A precise point estimate is emitted from weak evidence. |
| `FIN-007` | Transaction costs, taxes, carrying costs, capex, liquidity/time-to-sell, financing assumptions, and scenario dates are explicit. | Return estimates omit material costs/assumptions. |
| `FIN-008` | Scenario/sensitivity analysis covers rates, prices, costs, delays, source error, and regulatory/entitlement outcomes. | One optimistic scenario is presented as expected return. |
| `FIN-009` | Performance is stratified by geography, property/land type, price band, liquidity, data availability, and relevant protected-class proxy risk. | Aggregate accuracy hides a harmful subgroup. |
| `FIN-010` | Market drift and recalibration are monitored; stale estimates expire and affected outputs can be recalled. | Old market conditions remain active indefinitely. |
| `FIN-011` | Human review/escalation is required for configured high-value, low-confidence, regulated, or adverse-decision cases. | High-stakes financial output is fully automated without control. |
| `FIN-012` | AVM, appraisal, lending, insurance, securities/investment-advice, consumer-reporting, and professional-license applicability is reviewed before enabling related uses. | A disclaimer substitutes for required compliance. |
| `FIN-013` | Users can trace estimates to data, assumptions, comparables, model/rule version, and limitations without exposing prohibited data. | Financial output is unauditable. |
| `FIN-014` | No financial metric can override critical diligence unknowns or convert missing legal/buildability evidence into attractiveness. | High projected return suppresses unresolved feasibility risk. |
| `FIN-015` | Claims, marketing, and exports state that screening/analysis is not a guarantee and name the exact qualified financial scope. | Output is presented as a recommendation or guaranteed result. |
| `FIN-016` | Benchmarking includes a defensible baseline and economic loss/error-cost analysis, not only RMSE or ranking accuracy. | Statistical fit ignores decision harm. |
| `FIN-017` | Correction, dispute, and adverse-output review workflows preserve original evidence and notify affected users where applicable. | Incorrect financial output cannot be challenged or corrected. |
| `FIN-018` | Independent review finds no material model-risk, fairness, leakage, or regulatory blocker for the released claim. | Serious unresolved financial/model risk remains. |

---

# Conditional AI/LLM Overlay

## 31. Applicability

These criteria become release-blocking whenever an LLM or probabilistic model affects user-facing claims, summaries, retrieval, prioritization, report wording, source interpretation, or verification tasks.

| ID | PASS | FAIL |
|---|---|---|
| `AI-001` | AI cannot create a supported claim without deterministic evidence/claim validation. | Free-form output bypasses evidence rules. |
| `AI-002` | Model/provider/version, prompt/template, tools, parameters, and output schema are recorded per run. | AI output is not attributable. |
| `AI-003` | Prompt/document injection and malicious-source tests prove source text cannot override system policies or exfiltrate data. | Injection succeeds. |
| `AI-004` | Structured output validation rejects malformed, uncited, unsupported, or prohibited claims. | Invalid output reaches users. |
| `AI-005` | AI failure has deterministic fallback or explicit unavailable state; no silent lower-quality substitute. | Failure produces fabricated or degraded certainty. |
| `AI-006` | Hallucination/unsupported-statement rate meets frozen threshold with zero critical unsupported claims. | Critical hallucination occurs. |
| `AI-007` | Model changes trigger regression, calibration, cost, privacy, and relevant gate invalidation. | Provider/model changes silently. |
| `AI-008` | Sensitive/user/vendor data handling complies with provider terms, retention, training, and regional requirements. | Data is sent or retained contrary to policy. |
| `AI-009` | AI summaries preserve caveats, unknowns, contradictions, rights restrictions, and source attribution. | Compression removes safety context. |
| `AI-010` | AI cost/latency remains within targets and cannot cause uncontrolled retries. | AI behavior breaks unit economics or availability. |
| `AI-011` | Human review is required for configured high-risk AI-assisted output classes. | High-risk output is fully automated without approval. |
| `AI-012` | An AI-off mode can execute the deterministic core workflow for the qualified scope. | Core product correctness depends irreducibly on opaque AI. |
| `AI-013` | Evaluation cases, prompts, and expected outputs are protected from training/tuning contamination where reasonably controllable. | The model is evaluated on disclosed/tuned acceptance material without disclosure. |
| `AI-014` | Repeated-run variability is measured; critical outputs are deterministic, consensus-checked, or routed to explicit review. | Random variation changes a critical conclusion silently. |
| `AI-015` | Retrieval/source ranking cannot hide contradictory or lower-authority evidence without recorded policy. | AI-selected context manufactures one-sided certainty. |
| `AI-016` | Model/provider outage, refusal, truncation, context overflow, and tool failure are fault-injected. | AI infrastructure failure yields incomplete but apparently complete output. |
| `AI-017` | Red-team coverage includes indirect prompt injection, poisoned documents, citation fabrication, tool abuse, multilingual attacks, and data exfiltration. | Material attack class is untested. |
| `AI-018` | AI-generated verification tasks and summaries are evaluated separately by domain, language, risk class, and confidence. | Aggregate AI metrics hide a dangerous subgroup. |

---

# 32. Qualification hierarchy

Use the following classifications. Product-scope qualification and deployment qualification are recorded separately.

```text
L9-R
  Repo-proven private MVP.
  Existing fixtures, tests, and local workflow pass.

L9-P
  Protocol-qualified candidate.
  P0 PASS.

L9-E1
  Empirically screened bounded MVP.
  P0 + Q1 + applicable DQ/IR/DB/S/M/R/G criteria PASS.

L9-E2
  User-validated bounded MVP.
  L9-E1 + Q2 + applicable A/W criteria PASS; CG, FIN, and AI also PASS when enabled.

L10-BP-LOCAL
  Bounded production-grade local/single-user product.
  L9-E2 + applicable DB/S/A/M/O/R/F/W/G PASS for LOCAL_SINGLE_USER; E, CG, FIN, and AI PASS when activated.
  Q3 is not required.

L10-BP-ST
  Bounded production-grade hosted single-tenant product.
  L9-E2 + applicable DQ/IR/DB/S/A/M/O/R/F/W/G PASS.
  E required when commercial; CG, FIN, and AI required when enabled.
  Q3 is not required.

L10-BP-MT
  Bounded production-grade public multi-tenant product.
  L10-BP-ST plus all multi-tenant/auth/privacy/isolation criteria PASS.

X-US
  US expansion-ready architecture.
  A valid bounded-production or bounded-user-validated base + Q3A + Q3B PASS.

X-GLOBAL-ARCH
  Global architecture probed.
  X-US + Q3C PASS.
  This does not establish operational or purchase-grade coverage for any foreign jurisdiction.

J-QUALIFIED-<jurisdiction>
  Named jurisdiction operationally qualified.
  That exact jurisdiction's P0/Q1/Q2 as applicable, DQ/IR/DB/S/A/M/O/R/F/W/G,
  source rights, domain profiles, and deployment gates PASS; E, CG, FIN, and AI pass when activated.
```

`E` is mandatory only for a commercial/economic-viability claim. `CG` is mandatory only when automatic candidate generation/ranking is released. `FIN` is mandatory only when financial/valuation/investment output is released. `AI` is mandatory only when AI affects the released scope. International/data-residency criteria are mandatory only for an international profile.

No classification may be inferred from code volume, commit count, test count, roadmap position, or a different jurisdiction's pass.

---

# 33. Validity and invalidation

## Recommended maximum validity periods

| Qualification | Maximum validity without review |
|---|---:|
| P0 protocol | Candidate-specific; expires when candidate/scope changes. |
| Q1 | 180 days or earlier material semantic/source change. |
| Q2 | 365 days or earlier workflow/persona/semantics change. |
| Q3 | 365 days or earlier extension-contract/rights/architecture change. |
| Security review | 180 days or every material release, whichever is earlier. |
| Accessibility conformance | Every material UI change and at least annually. |
| Backup/restore | At least quarterly. |
| Load/capacity | Every material workload/architecture change and at least quarterly during active growth. |

## Material invalidation triggers

- evidence, claim, confidence, severity, or caveat semantics change;
- geometry or spatial calculation behavior changes;
- report wording/section semantics change;
- source authority, license, schema, freshness, or connector behavior changes materially;
- user workflow, comparison, export, or review behavior changes materially;
- auth, tenancy, storage, deployment, queue, or recovery architecture changes;
- rulepack registration or jurisdiction adapter contracts change;
- AI model/provider/prompt changes for decision-relevant behavior;
- a production incident reveals an untested material failure;
- a reviewer/reference defect changes benchmark truth;
- a qualification artifact or sealed cohort is compromised.

A change-impact record must identify which gates remain valid and why. Silence means invalidation.

---

# 34. Machine-readable status requirements

Recommended path:

```text
state/EMPIRICAL_QUALIFICATION_STATUS.yaml
```

Each gate and sub-gate record must include:

```text
status
scope_version
candidate_commit
candidate_tag_or_digest
protocol_version
targets_version
started_at
completed_at
expires_at
reviewers
independent_reproducer
evidence_path
selected_product_scope_profile
selected_deployment_profile
criterion_results
failed_criteria
blocked_criteria
accepted_residual_risks
invalidation_reason
supersedes
```

CI must reject:

- `PASS` with any missing hard criterion;
- `PASS` with missing/invalid evidence path;
- `PASS` on expired or invalidated prerequisite;
- production classification with any required overlay not passed;
- `N/A` without required approval/rationale;
- a tested commit that is not an ancestor of the release commit;
- a release artifact digest different from the qualified digest;
- qualification targets changed after protocol freeze;
- missing sealed-case hashes;
- contradictory status across state, milestone map, release manifest, and docs;
- duplicate criterion IDs or missing required criterion contracts;
- aggregate PASS where a configured safety-critical subgroup fails;
- a bounded production claim that incorrectly requires or infers Q3, or an expansion claim that bypasses Q3 lanes;
- a target/profile/status file that does not validate against its schema.

---

# 35. Evidence retention and case rotation

- Development fixtures stay in the ordinary repo.
- Validation cases may be in a controlled repo area after use.
- Sealed acceptance inputs and expected outcomes remain in a separate restricted vault until execution.
- The public/main repo stores only hashes, schema, protocol, and non-sensitive aggregate evidence before unsealing.
- Once a sealed case is disclosed to implementers, it becomes a regression case and must be replaced in the future sealed pool.
- Participant data remains de-identified and separately access-controlled.
- Source terms may prohibit retaining or redistributing raw data; evidence packaging must respect those terms while preserving reproducibility through approved snapshots, hashes, or retrieval manifests.

---

# 36. Completeness mapping to project intentions

| Project intention | Primary qualification coverage |
|---|---|
| Functional correctness | Q1, DQ, M |
| Safety/non-misleading output | Q1, S, G |
| Practical utility | Q2 |
| User efficiency | Q2, E |
| Evidence transparency | Q1, Q2, G |
| Modularity | Q3, M |
| Non-fragility/fail-closed behavior | Q1, Q3, O |
| Flexibility across sources | Q3 |
| Flexibility across jurisdictions | Q3 Lane A and C |
| Worldwide architectural ambition | Q3 Lane C, explicit claim boundary |
| Scalability/throughput | DB, O, E; CG/FIN/AI when enabled |
| Postgres/PostGIS durability | DB, M, O |
| Data quality | DQ, Q1 |
| Source licensing/rights | Q1, Q3, DQ, S, R |
| Security/privacy | S, O |
| Accessibility/human factors | Q2, A |
| Test effectiveness | P0, M, G |
| Reproducibility/auditability | P0, Q1–Q3, G |
| Economic viability | E |
| Production operations | O |
| Automatic candidate generation/ranking | Conditional CG overlay |
| Valuation/investment/financial output | Conditional FIN overlay |
| Windows-native operation | W overlay, M, DB |
| AI safety if added | Conditional AI overlay |

No significant current intention should be classified as qualified unless its listed gates pass.

---

# 37. Recommended execution order

```text
1. Select the exact product-scope and deployment profiles.
2. Freeze qualification vocabulary, targets, domain profiles, source profiles, criterion contracts, and candidate identity.
3. Validate all machine-readable schemas/status/profile prerequisites.
4. Pass P0.
5. Execute Q1 on a sealed cohort; remediate only under the frozen retest rule.
6. Execute Q2 when a user-utility claim is intended.
7. Complete applicable DQ/IR/DB/S/A/M/R/W/G controls.
8. Complete conditional CG, FIN, AI, and E gates only when those capabilities/claims are enabled.
9. Complete O and F for the selected production profile.
10. Execute Q3A/Q3B only before a US expansion-readiness claim.
11. Execute Q3C only before a global-architecture-probe claim.
12. Claim only the highest unexpired classification whose exact prerequisites pass.
```

The next highest-value work is Q1. Portability and production hardening cannot compensate for an unproven core land-screening result.

---

# 38. Change classification and invalidation matrix

Every material change must receive exactly one primary class and zero or more secondary classes.

| Change class | Minimum gates to review/invalidate |
|---|---|
| `DOCS_NONSEMANTIC` | M/G coherence checks only |
| `SOURCE_DATA_REFRESH` | DQ, Q1 current-source results, F; rights/freshness if changed |
| `SOURCE_SCHEMA_OR_CONNECTOR` | DQ, Q1, Q3A/B as applicable, M, F |
| `SOURCE_RIGHTS_OR_TERMS` | S, R, G, Q1/Q3 rights criteria, affected production outputs |
| `AOI_IDENTITY_OR_GEOMETRY` | IR, DQ, Q1, DB, affected reports |
| `RULE_OR_CONFIDENCE_SEMANTICS` | Q1, Q2 where decisions/wording change, M, G, F |
| `REPORT_OR_CAVEAT_SEMANTICS` | Q1, Q2, A, R, G |
| `UI_WORKFLOW` | Q2, A, S, affected end-to-end O checks |
| `DB_SCHEMA_OR_MIGRATION` | DB, M, O, G, plus Q1 if semantics/lineage change |
| `AUTH_TENANCY_PRIVACY` | S, DB, O, R |
| `DEPLOYMENT_INFRASTRUCTURE` | O, S, DB, M |
| `CANDIDATE_SEARCH_OR_RANKING` | CG, Q1, Q2, IR, DQ, S, F |
| `FINANCIAL_MODEL_OR_MARKET_DATA` | FIN, Q1, Q2, DQ, S, R, E, F |
| `WINDOWS_TOOLING_OR_LOCAL_RUNTIME` | W, M, DB, G |
| `AI_MODEL_PROMPT_PROVIDER` | AI, Q1, Q2, S, E, F |
| `NEW_INTENT_OR_DOMAIN` | P0, domain profile, Q1/Q2, DQ/IR/R |
| `NEW_US_JURISDICTION` | Q3A and that jurisdiction's own qualification profile |
| `NEW_NON_US_JURISDICTION` | Q3C plus that jurisdiction's own R/DQ/IR qualification |

A reviewed impact record may preserve unaffected gates, but silence means invalidation of all plausibly affected gates.

---

# 39. Adversarial adequacy rules

The framework itself fails adequacy review if any of the following is true:

1. A release-blocking criterion cannot be evaluated as `PASS`, `FAIL`, `BLOCKED`, or justified `N/A`.
2. A criterion uses an undefined qualitative term.
3. A selected profile has no explicit required-gate set.
4. A numeric target is absent after protocol freeze.
5. A machine-readable schema permits an illegal pass state.
6. An empirical result can be pooled to hide a failed critical subgroup.
7. A new geography can be called production-qualified from an architecture probe alone.
8. A bounded production release is blocked solely because an unrelated global expansion probe has not run.
9. A source can be qualified without rights, preservation mode, freshness, coverage, and quality profiles.
10. A wrong-AOI, wrong-version, or ambiguous-input path is not tested.
11. Post-release drift/incidents cannot invalidate a prior pass.
12. The framework requires organizational roles that cannot be fulfilled by a small team without allowing documented role combination and independent review where necessary.
13. Pass evidence depends on chat history, mutable local state, or inaccessible proprietary data without an approved reproducibility mode.
14. The qualification process creates enough always-loaded documentation to undermine agent operation; detailed evidence must remain routed, not startup context.

---

# 40. Reference frameworks

This framework is project-specific. The following external frameworks are used as completeness and terminology checks rather than claimed certification:

- ISO/IEC 25010:2023 product quality model;
- ISO/IEC 25019:2023 quality-in-use model;
- ISO/IEC 25040:2024 quality evaluation framework;
- ISO 19157-1:2023 geographic data quality;
- ACM SIGSOFT Empirical Standards for software-engineering studies;
- NIST SP 800-218 SSDF and SP 800-218A when generative AI development is applicable;
- OWASP ASVS 5.0 for application-security verification;
- WCAG 2.2 for web accessibility;
- NIST AI RMF and Generative AI Profile when AI affects released behavior;
- PostgreSQL/PostGIS official operational guidance for backup, recovery, concurrency, and production operation.

Passing this project framework does not constitute third-party certification against any external standard unless an authorized assessment explicitly establishes that claim.
