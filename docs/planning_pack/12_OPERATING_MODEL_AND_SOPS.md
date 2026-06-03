# 12 Operating Model and SOPs

Generated: 2026-05-28

## 1. Operating model

The v1 product should operate as a hybrid software + analyst workflow until source quality and rules are proven.

## 2. Roles

| Role | Responsibilities |
|---|---|
| product/domain lead | scope, red flags, safe wording, user interviews |
| geospatial engineer | PostGIS, spatial joins, raster/vector processing |
| data engineer | ingestion, source registry, QA, source versions |
| backend engineer | API, jobs, report runs, entitlements |
| analyst/reviewer | report QA, claim verification, user-safe language |
| legal/compliance advisor | disclaimers, fair housing, AVM, data rights |
| customer operator | intake, support, feedback, billing |

## 3. SOP: source onboarding

1. Identify source and domain.
2. Create source registry record.
3. Perform license review.
4. Archive sample raw data.
5. Normalize to staging.
6. Run data QA.
7. Document caveats.
8. Create dataset version.
9. Add source to test reports.
10. Approve for production.

## 4. SOP: report generation

1. Receive area and intent.
2. Validate geometry.
3. Create report run.
4. Resolve source manifest.
5. Run feature extraction.
6. Create evidence.
7. Execute rules.
8. Generate claims and verification tasks.
9. Compile report.
10. Human review.
11. Approve or return for correction.
12. Deliver report.
13. Capture user feedback.

## 5. SOP: human review

Reviewer checks:
- evidence supports claims
- high/critical claims are not overstated
- unknowns are explicit
- source failures visible
- maps align with text
- verification tasks are specific
- no legal/title/survey/appraisal conclusion
- no data-license leak

## 6. SOP: source failure

If a source fails during report generation:
1. Record source failure evidence.
2. Downgrade affected claim confidence.
3. Add unknown.
4. Add verification task if material.
5. Do not say "no issue found."
6. Alert if failure rate exceeds threshold.

## 7. SOP: user challenge / correction

1. Capture challenged claim/evidence.
2. Freeze report version.
3. Open issue.
4. Re-check source versions.
5. Add reviewer note or corrected report if needed.
6. Preserve original report and correction trail.
7. Update rules/tests if systemic.

## 8. SOP: source refresh

1. Pull new source snapshot.
2. Archive raw data.
3. Load new dataset version.
4. Run QA and schema drift tests.
5. Compare derived metrics on golden parcels.
6. Promote if tests pass.
7. Re-run affected reports only if user/product policy requires.
