# Adversarial Review Findings

**Reviewed artifact:** Empirical Qualification Framework v2  
**Replacement produced:** Empirical Qualification Framework v3  
**Review stance:** hostile-to-hand-waving, hostile-to false precision, and hostile to unnecessary process rigidity.

## Verdict

Version 2 was broad and substantially better than an ordinary test plan, but it was not yet optimally scoped or mechanically enforceable.

The most consequential defect was conceptual: it mixed four different questions—

1. whether the implementation exists;
2. whether bounded land-screening behavior is empirically valid;
3. whether the deployed service is production-grade;
4. whether the architecture can expand internationally—

and sometimes required expansion evidence to qualify an otherwise bounded production release.

Version 3 separates those axes; adds Postgres/PostGIS, AOI identity, Windows, candidate-generation, financial, regulatory, and field-surveillance gates; converts vague terms into controlled definitions and criterion contracts; and makes invalid PASS states executable validation failures.

## Findings and disposition

| Severity | Finding | Why it mattered | v3 disposition |
|---|---|---|---|
| Critical | Non-US Q3 Lane C was effectively required for Level 10. | A production-grade NC product should not fail solely because Bologna was untested. This conflated scope breadth with production quality. | Separate bounded-production and expansion classifications. Q3A/B/C are independent sub-gates. |
| Critical | Deployment assumptions were implicit. | Multi-tenant SaaS, private hosted, local single-user, API, and on-prem products have different mandatory controls. | Added product-scope and deployment profiles with explicit gate applicability. |
| Critical | Pass/fail prose was not mechanically enforceable. | The JSON schema allowed illegal or incomplete PASS states; targets/status lacked dedicated schemas. | Added criterion-contract, target, status, and result schemas plus validation script. |
| Critical | PostgreSQL/PostGIS was central to the project but only indirectly qualified. | Migration correctness, transactionality, spatial indexes, isolation, pooling, PITR, bloat, and restore are core non-fragility concerns. | Added a dedicated 20-gate DB overlay. |
| Critical | AOI/address/parcel identity resolution was under-specified. | A perfectly reasoned report about the wrong parcel is a catastrophic failure. Parcel IDs are jurisdiction/time scoped and can split/merge. | Added a dedicated 15-gate IR overlay and Q1 acceptance criteria. |
| Critical | Aggregates could hide subgroup failure. | Good pooled recall could conceal a failed county, intent, domain, persona, or output channel. | Added mandatory stratification and subgroup floors. |
| Critical | Windows-native support was treated as a setup concern rather than a qualified operating environment. | The canonical repo is used from a Windows/OneDrive path; path semantics, CRLF, case-insensitivity, Docker Desktop, file locks, sync clients, credentials, and PowerShell can invalidate otherwise passing behavior. | Added the 12-gate W overlay and Windows CI/runtime targets. |
| Critical | Automatic candidate generation/search/ranking was absent from the qualification model. | The original product includes automatically designed or discovered areas; analysis accuracy does not prove candidate-universe completeness, ranking stability, false-exclusion control, or anti-steering. | Added the conditional 18-gate CG overlay. |
| Critical | Financial/investment/valuation behavior was not separately controlled. | “Investing” can introduce leakage, market drift, false precision, AVM/appraisal/lending/insurance applicability, fairness, and decision-loss risks beyond ordinary land screening. | Added the conditional 18-gate FIN overlay; it remains disabled for the current scope. |
| Critical | Exact source and domain qualification were not machine-bound to P0. | General source registries do not prove that the exact sources/domains used by a release have frozen authority, rights, quality, reference, rubric, and preservation profiles. | Added source-quality and domain-qualification profiles plus P0 enforcement. |
| Major | Document extraction/OCR/table/figure behavior was implicit. | Zoning and legal/planning evidence often lives in PDFs and maps; an evidence link is insufficient when the extracted page/section/table is wrong or unresolvable. | Added DQ-021–023 for anchors, extraction confidence, review, and presentation-tile misuse. |
| Major | Foreign land-tenure representation could still be US-parcel-shaped. | A non-US probe must handle leasehold, strata, communal/customary tenure, concessions, public land, and other local rights without forcing US ownership semantics. | Expanded Q3C representation requirements and retained jurisdiction-specific qualification. |
| Major | Scope versions and active source set were not frozen strongly enough. | Candidate commit alone does not identify report/API/normalization/geometry/ruleset/source-snapshot semantics. | Added exact scope/version/source-profile fields and validator blockers. |
| Major | The qualification control plane itself lacked adversarial executable tests. | A schema/validator can look strict while allowing classification outrun, conditional mismatch, or framework/catalog drift. | Added validator self-tests covering baseline, outrun, conditional mismatch, catalog drift, and false P0. |
| Major | Q3's >=85% extension-code LOC rule was gameable and rigid. | LOC placement is not a reliable modularity measure and can punish legitimate generic improvements. | Reclassified change dispersion as diagnostic; dependency direction, adapter removal, registration, and regression remain hard gates. |
| Major | Qualitative words lacked controlled definitions. | “Material,” “appropriate,” “representative,” “critical,” and “independent” permitted inconsistent evaluation. | Added controlled vocabulary and mandatory criterion-contract fields. |
| Major | Reviewer competence was not separately gated. | Independence does not imply subject-matter competence. | Added reviewer qualification/calibration and domain reference hierarchy gates. |
| Major | Reference truth could be unstable or circular. | A system cannot validate itself against its own output or a convenient shared source without disclosure. | Added explicit domain reference hierarchy, source independence, reliability, and adjudication controls. |
| Major | Evidence retention and source-license restrictions could conflict. | Full snapshots may be prohibited, but hash-only evidence may be insufficient for some claims. | Added approved evidence-preservation modes and blocking semantics. |
| Major | Q2's safety-comprehension gate was absolute but poorly operationalized. | One initially confused participant should trigger an in-product correction test, not necessarily make the study unusable; uncorrected confusion must remain disqualifying. | Gate now requires zero uncorrected final misconception and records pre/post correction. |
| Major | Persona-specific outcomes could be hidden by aggregate utility. | Experts may succeed while novice target users fail. | Added persona-specific safety and utility floors. |
| Major | Accessibility ended primarily at the web workflow. | Exported PDF/HTML and map-only findings can remain inaccessible. | Added export accessibility, uncertainty visualization, and readability gates. |
| Major | Vulnerability severity lacked applicability semantics. | Scanner severity alone can create impossible gates; “not affected” is different from accepting risk. | Added reachability/applicability evidence and distinct triage states. |
| Major | Small-team governance assumed many separate people. | Requiring five distinct signatories is unnecessary rigidity for a founder-scale project. | Roles may be combined, while independence-sensitive security/data review remains independent. |
| Major | No dedicated post-release empirical surveillance layer existed. | Pre-release qualification decays as sources, rules, users, and field conditions change. | Added a 12-gate field surveillance/drift overlay. |
| Major | Regulatory/professional-scope applicability was distributed and incomplete. | Generic disclaimers do not resolve fair-housing, AVM, professional-practice, public-record, or international obligations. | Added a profile-based regulatory/professional-scope overlay. |
| Major | Citation resolvability was weaker than claim linkage. | A claim can link to an evidence row while the underlying source/reference has rotted. | Added citation resolution, content hash, version, and preservation checks. |
| Major | Benchmark challenge-set performance could be confused with prevalence. | Balanced hard-case cohorts do not estimate field prevalence. | Added explicit challenge-set versus prevalence-weighted reporting. |
| Major | Change invalidation remained judgment-heavy. | Teams could preserve stale passes after semantic changes. | Added a change classification/invalidation matrix. |
| Moderate | First-use and trained-use utility were pooled. | Repeated exposure can overstate onboarding usability. | Added separate first-use/trained-use reporting. |
| Moderate | Tool comparator fairness was unspecified. | A weak baseline can manufacture apparent utility. | Added comparator-equivalence controls while preserving the manual baseline. |
| Moderate | Environment reproducibility omitted some low-level dimensions. | Locale, timezone, PROJ/GDAL/PostGIS versions can change spatial or temporal output. | Added exact toolchain/runtime recording. |
| Moderate | Sensitive geospatial data misuse was not explicit enough. | Location intelligence can support stalking, bulk owner harvesting, or sensitive-site discovery. | Added sensitive-location classification and abuse-case gates. |
| Moderate | Long-running operational degradation was under-tested. | Short load tests miss queue buildup, leaks, bloat, and slow decay. | Added soak/endurance qualification. |
| Moderate | Commercial value was inferred mostly through cost. | Low cost does not prove user value. | Added measured value/cost comparison; willingness-to-pay remains diagnostic unless a commercial claim is made. |
| Moderate | Agent governance itself could become context bloat. | A 1,000+ line framework should not be loaded every session. | Added routed evidence/state requirements and concise startup-context gate. |

## Remaining unavoidable decisions

The framework can define how decisions are frozen and tested, but it cannot honestly preselect every product target. The following remain deliberate `BLOCKED` values until the project owner freezes them:

- deployment profile;
- production availability/SLO/error budget;
- RPO/RTO;
- p95/p99 latency and report-runtime budgets;
- acceptable unit cost and human-review time;
- security verification profile;
- exact target personas;
- exact commercial claim;
- initial legal/regulatory applicability decisions;
- domain-specific materiality/severity rubrics;
- production data-retention periods;
- exact source-profile set and source-rights decisions;
- domain-specific reference hierarchies and issue taxonomies;
- Windows support/version matrix;
- candidate-generation and financial targets if those capabilities are later enabled.

Leaving these as `null` in a `DRAFT` target file is correct. Allowing a `PASS` while they remain unresolved is not.

## Residual limits

No static framework can eliminate:

- future legal or source-term changes;
- unknown geospatial/data failure modes;
- imperfect reference truth;
- rare events not represented in the cohort;
- users deliberately stripping caveats;
- external infrastructure/provider failures;
- future product intents not yet scoped.

Version 3 addresses this through invalidation, field surveillance, residual-risk ownership, restricted claims, and periodic requalification rather than pretending completeness.

## Final adversarial classification

```text
Framework structural adequacy: PASS
Machine-control self-test: PASS
Current project parameterization: BLOCKED
Highest evidence-supported classification in the example state: L9-R
```

The `BLOCKED` result is deliberate. A framework is not made stronger by inventing thresholds, reviewers, source rights, or production targets. It is stronger when unresolved decisions remain explicit and cannot be converted into a pass.
