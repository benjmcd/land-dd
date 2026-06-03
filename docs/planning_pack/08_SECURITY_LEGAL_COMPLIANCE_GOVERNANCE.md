# 08 Security, Legal, Compliance, and Governance Spec

Generated: 2026-05-28

## 1. Governance thesis

The system must be useful without pretending to replace professionals. The key governance problem is not only data security; it is preventing overconfident legal, title, environmental, valuation, or housing-related conclusions.

## 2. Legal boundary

The product may provide:
- screening observations
- source-linked evidence
- risk flags
- unknowns
- verification tasks
- suggested agency/professional questions

The product must not provide:
- legal advice
- title opinions
- survey determinations
- wetland jurisdictional determinations
- engineering conclusions
- mortgage appraisal/AVM conclusions
- insurance underwriting decisions
- demographic desirability rankings

## 3. Required disclaimers

Each report should include:
- screening-only disclaimer
- not legal/title/survey/engineering advice
- not wetland delineation
- not appraisal/valuation for mortgage use
- data may be stale/incomplete/conflicting
- user must verify with appropriate authority/professional
- source appendix and source dates

## 4. Fair housing risk

If residential users receive location recommendations, the system must avoid:
- protected-class filters
- demographic desirability scoring
- school/crime/demographic proxies unless legally reviewed
- steering language
- "best neighborhood for X type of person"
- exclusionary recommendations based on protected characteristics

MVP mitigation:
- focus on parcel physical/legal/buildability constraints
- do not rank communities by demographic attributes
- do not ingest protected-class demographic variables for scoring
- legal review before adding residential area-recommendation features

## 5. Valuation / AVM risk

MVP should avoid automated property valuations for mortgage-related collateral decisions.

Allowed:
- market context
- comparable listing/sale observations
- price/acre distribution if licensed
- "price appears high/low relative to displayed comps" with caveats

Avoid:
- definitive fair market value
- mortgage collateral value
- AVM positioning
- lender/secondary market use without AVM controls

## 6. Data rights governance

Before production use of each source:
- cache allowed?
- commercial use allowed?
- derived reports allowed?
- export allowed?
- attribution required?
- AI processing allowed?
- retention allowed?
- user display allowed?
- raw data redistribution forbidden?
- audit logs required?

Implement:
- source entitlement tags
- display/export gates
- dataset-specific access policies
- source attribution in reports
- license review workflow

## 7. Privacy and security

Potential sensitive data:
- user accounts
- searched parcels
- saved watchlists
- owner names/addresses
- transaction/comps data
- user annotations
- payment data
- support messages

Controls:
- workspace isolation
- role-based access control
- audit logs
- encryption in transit
- encryption at rest
- secret management
- no raw payment card storage
- data retention policy
- deletion/export process
- vendor access controls
- least-privilege database roles

## 8. Human review governance

Beta rule:
- every report reviewed before customer delivery

Later:
- risk-based review for high/critical claims
- random sampling for low-risk reports
- reviewer override must preserve original evidence
- all reviewer notes audited
- model/ruleset changes require regression tests

## 9. Incident classes

| Incident | Example | Response |
|---|---|---|
| false negative | report missed flood source failure | freeze affected report type, notify users if material |
| false positive | report flagged nonexistent issue | correct rule/source and log erratum |
| data-license breach | exported restricted raw data | disable export, notify vendor/legal |
| protected-class risk | ranking implies residential steering | remove feature, legal review |
| source outage | missing source silently omitted | convert to source-failure evidence |
| security breach | user/report data exposed | incident response plan |

## 10. Governance requirements

1. Every report has source appendix.
2. Every claim has evidence.
3. Every source has license metadata.
4. Every high-risk output has safe wording.
5. Every human override is audited.
6. Every ruleset has version and tests.
7. Every model/prompt used in extraction is versioned.
8. Every source failure appears in output.
9. No protected-class scoring in MVP.
10. No mortgage AVM positioning in MVP.
