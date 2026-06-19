# Threat/Proxy Audit Runbook

## Purpose

Use `config/threat_proxy_audit.yaml` as the repo-local threat/proxy audit map for
security, access-control, protected-class, demographic-proxy, residential-steering,
recommendation/ranking, suitability, source-rights, overclaim, and production-error
leakage risks.

This runbook is validate-only. It does not add product semantics, ingest demographic
inputs, create recommendations, perform legal review, complete external security review,
implement hosted IdP/RBAC, review production logs, approve DS-017, provision hosted
alerting, or claim hosted production readiness.

## Validate Audit Map

Run from the repository root:

```powershell
.\scripts\run_threat_proxy_audit_check.ps1
```

The check is validate-only and static. It verifies that:

- the threat/proxy catalog exists and has schema `threat_proxy_audit_v1`;
- every declared risk has at least one existing authority file;
- protected-class, demographic, neighborhood desirability, school-by-demographic,
  safety-by-demographic, and residential-steering exclusions remain documented;
- Census TIGER remains administrative geography context only and records
  `census_demographics_used=false`;
- compare/diff workflow smoke rejects ranking/recommendation keys and remains separate
  from suitability scoring;
- report/export/private-MVP overclaim tests keep forbidden legal, water, safety,
  investment, and value certainty phrases out of generated output;
- access-control and identity/RBAC contracts remain validate-only and preserve hosted
  IdP/RBAC blockers;
- user-facing UI error pages escape content and production error/log review remains
  externally blocked;
- failed-report, live-connector job, connector-review last-error, and operations
  recovery preview surfaces redact stack traces, local paths, secret-like values,
  request query secrets, and raw payload-shaped error text while preserving underlying
  job/source-failure evidence for inspection;
- external security review, legal fair-housing review, hosted IdP/RBAC, production
  error/log review, DS-017 entitlement, and hosted alerting remain blocked.

## Operator Workflow

1. Run `.\scripts\run_threat_proxy_audit_check.ps1` before treating any release
   candidate as ready for hosted or residential expansion review.
2. If a future source, rulepack, geography, UI, report, or compare feature adds
   demographic, valuation, school, neighborhood, insurance, lending, recommendation, or
   suitability language, update this catalog and add focused tests before claiming the
   feature is safe.
3. Treat a failed check as a release blocker until the catalog, runbook, source review,
   tests, and product boundary are reconciled.
4. Do not use this check as legal signoff or security signoff. It is repo-local drift
   control for existing controls.

## Known Limits

- This audit is repo-local and validate-only.
- It does not inspect hosted logs, external dashboards, cloud IAM, production traffic, or
  third-party vendor contracts.
- It does not approve demographic analysis, protected-class proxies, residential
  recommendations, market/investment/lending suitability, or DS-017 data.
- It does not replace external security review, legal fair-housing review, hosted
  IdP/RBAC design, production error/log review, or hosted alert routing.
