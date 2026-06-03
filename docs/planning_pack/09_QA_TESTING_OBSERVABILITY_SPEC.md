# 09 QA, Testing, and Observability Spec

Generated: 2026-05-28

## 1. QA thesis

This system fails when it gives confident conclusions from incomplete or stale data. QA must test not only software correctness, but also source lineage, caveats, uncertainty handling, and safe language.

## 2. Test categories

### Unit tests

- geometry validation
- CRS transform correctness
- area/intersection math
- buffer/distance calculations
- ruleset evaluation
- confidence scoring
- safe-language linting
- entitlement checks

### Data tests

- source schema drift
- row count drift
- geometry validity
- duplicate IDs
- null required fields
- source freshness
- spatial extent sanity
- known test parcel comparisons

### Integration tests

- ingest -> normalize -> feature extract -> evidence -> claims -> report
- source failure path
- human review override path
- report re-run reproducibility
- entitlement-limited export
- batch parcel processing

### Regression tests

Maintain golden test parcels:
- known flood intersection
- known wetland intersection
- steep-slope parcel
- apparent landlocked parcel
- zoning compatible parcel
- zoning incompatible parcel
- source-conflict parcel
- missing-source parcel

Each golden parcel should include expected claims and acceptable confidence ranges.

## 3. Observability requirements

Log:
- report_run_id
- area_id
- source versions used
- job_id
- worker version
- method versions
- LLM/model/prompt version where applicable
- runtime
- failure reason
- reviewer overrides
- cost metrics

Metrics:
- report success rate
- source failure rate
- mean report runtime
- per-source ingest failures
- evidence count per report
- unknown count per report
- high/critical claim rate
- human review time
- gross margin estimate
- support tickets per report
- rule regression failures

Alerts:
- source ingest failure
- source freshness breach
- report failure spike
- cost spike
- tile/API quota spike
- safe-language lint failure
- entitlement/export violation
- high contradiction rate after source update

## 4. Quality gates

### Gate A: source onboarding

A source cannot be used in production unless:
- source registry record exists
- license review complete
- raw archive path defined
- schema/geometry validation tests pass
- freshness policy exists
- caveats documented

### Gate B: ruleset release

A ruleset cannot be released unless:
- versioned
- tested on golden parcels
- reviewed by product/domain owner
- safe-language lint passes
- hard gates documented
- output examples reviewed

### Gate C: report release

A report cannot be delivered unless:
- source manifest present
- evidence-to-claim links complete
- unknowns included
- high/critical claims have verification tasks
- source failures visible
- reviewer approved if beta/high-risk
- export entitlements valid

## 5. Non-fragility tests

Test deliberate breakage:
- FEMA source unavailable
- parcel geometry invalid
- zoning PDF parser fails
- source schema changes
- commercial vendor field renamed
- Postgres job worker crashes
- duplicate parcel IDs
- conflicting parcel boundaries
- impossible geometry intersection
- LLM returns uncited assertion

Expected behavior:
- no silent pass
- report blocked or source failure recorded
- confidence downgraded
- verification task generated
- audit event written

## 6. Performance tests

MVP:
- process 100 parcels in batch
- run 10 reports concurrently
- load target county parcels
- execute flood/wetland/slope extraction
- generate report artifacts
- measure cost and runtime

Early pro:
- 1,000 parcel batch screen
- nightly source refresh
- map tile serving under interactive load
- report queue under burst traffic

## 7. Human QA rubric

Reviewers verify:
- claims match evidence
- wording is safe
- unknowns are explicit
- source failures visible
- maps align with text
- source dates are visible
- verification tasks are practical
- no unsupported legal conclusions
- no demographic/protected-class content
- no data-license leakage
