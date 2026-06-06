# Rulepack Readiness Checklist

## Purpose
Mandatory checklist before adding a new intent or rulepack to production.

## Intent definition
- [ ] Intent code added to backend/app/domain/enums.py IntentCode enum
- [ ] User (who uses this), decision (what they decide), non-goals (what it does not determine) documented
- [ ] Prohibited claims listed (e.g., no appraisal value, no legal access determination)

## Required evidence categories
- [ ] Required domains listed (flood, wetlands, soil_septic, access, zoning, water, buildability, etc.)
- [ ] Each domain has a registered data source with reviewed license
- [ ] Source failures for each domain produce explicit UNKNOWN claims

## Hard gates and scoring separation
- [ ] Hard gates (critical/high severity) explicitly listed in rulepack YAML
- [ ] Scoring bands (not raw scores) defined if scoring is used
- [ ] Suitability and confidence are separate fields in all output claims

## Rule versions and test fixtures
- [ ] config/ruleset_<intent>.yaml created with version field
- [ ] At least one fixture test that exercises each hard gate
- [ ] Tests cover: positive case (gate triggers), negative case (gate does not trigger), source failure case (UNKNOWN)

## Verification tasks
- [ ] Each claim code has a human-readable verification_task string
- [ ] Verification tasks name the professional or record type required
- [ ] No verification task says "it is safe" or "no issues found"

## User-safe language review
- [ ] User-safe language (user_safe_language field) reviewed for forbidden phrases
- [ ] forbidden_language list in rulepack YAML covers key overstatement patterns
- [ ] All language reviewed against the AGENTS.md non-negotiables list

## Negative and unknown cases
- [ ] NOT_EVALUATED claim codes defined for unsupported domains
- [ ] Each UNKNOWN case has a verification_task
- [ ] Test cases cover conflicting evidence and stale evidence scenarios

## Jurisdiction applicability
- [ ] applies_to.country and applies_to.geography_scope fields set in ruleset YAML
- [ ] Rulepack does not apply outside documented geography without review

## Human review requirements
- [ ] Professional review requirements documented in verification tasks
- [ ] No claim asserts final legal, title, survey, wetland, or buildability determination
- [ ] Legal/regulatory interpretation requires human review flag

## Regression reports
- [ ] test_report_regression.py updated with known red-flag case for this intent
- [ ] Known clean-ish case added to regression test
- [ ] Rulepack version pinned in regression fixtures

---
## Sign-off
- Intent code: ________________
- Reviewer: ________________
- Date: ________________
- Notes: ________________
