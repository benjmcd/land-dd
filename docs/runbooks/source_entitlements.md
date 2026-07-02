# Source Entitlements Runbook

## Purpose

Use `config/source_entitlements.yaml` as the validate-only source-entitlement decision
packet for DS-017. It turns the commercial parcel-vendor blocker into explicit
authority requirements without approving a vendor, changing source readiness, or adding
a connector.

Run from the repository root:

```powershell
.\scripts\run_source_entitlement_check.ps1
```

For a consolidated stdout view that includes DS-017 inside the active
authority-evidence posture, run:

```powershell
py -3.12 .\scripts\authority_evidence_intake_check.py --summary
```

Use `--json` on the same checker for machine-readable collection tracking. These
summary modes are reporting only; they do not replace the source-entitlement check,
approve DS-017, select a vendor, change source readiness, or unlock implementation.

The check is validate-only. It does not approve DS-017, call a live vendor, seed a
fixture, generate artifacts, select a vendor, change source readiness, or expose raw
vendor data.

## DS-017 Boundary

DS-017 remains blocked until external authority supplies a reviewed vendor/product
scope, license terms, source-rights decisions, entitlement owner, field allowlist and
denylist, cost policy, paid-source metering policy, and connector-scope decision.

Acceptable outcomes are:

- `approve_under_reviewed_contract`: approve a named vendor/product scope with reviewed
  terms, explicit entitlements, field policy, cost policy, and connector scope.
- `defer_or_remove_from_must_scope`: decide DS-017 is not required for the next
  full-release gate, then update source-readiness/release artifacts without pretending
  DS-017 is approved.
- `substitute_public_official_sources`: replace DS-017 with approved public or official
  source coverage and record the resulting scope limits.

No owner fields, raw vendor record, assessed or market value, sale/comps data, title
status, legal access, buildability conclusion, appraisal/lending suitability, or
investment recommendation may enter reports from DS-017 unless separately approved and
entitlement-gated.

## Required External Evidence

Before a DS-017 implementation lane can start, the decision packet needs all of the
following:

- vendor entity, dataset name, and reviewed contract or terms reference;
- terms effective date, allowed geography, source version, update cadence, and
  staleness policy;
- license, commercial-use, redistribution, cache, export, raw-data, AI-use, and
  attribution decisions;
- field allowlist and field denylist;
- workspace/report/export entitlement policy and entitlement owner;
- cost meter, billing owner, and per-report paid-source metering;
- connector scope and failure-mode mapping for auth failure, license blocked, quota,
  rate limit, stale data, outage, no coverage, ambiguous match, partial response,
  schema drift, and no-data.

## Release Use

Release readiness composes this check to prove the blocker is explicit. A passing
source-entitlement check means only that the DS-017 decision requirements are current
and fail closed. It is not source approval, production authority, or paid-source
metering proof.
