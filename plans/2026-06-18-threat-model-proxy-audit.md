# Threat-Model Proxy Audit

## Goal

Audit and harden the repo-local security, access-control, protected-class, and
residential-steering safeguards before any hosted or residential expansion claim. The
pass should make current boundaries easier to verify without pretending to replace an
external security review, hosted IdP/RBAC design, legal review, or production incident
review.

## Non-goals

- No hosted identity provider, OAuth/OIDC, user/org RBAC tables, billing, alerting,
  SIEM, secret-manager, or deployment work.
- No DS-017 connector, paid/vendor entitlement model, new geography, new rulepack, or
  new source approval.
- No recommendation, ranking, suitability scoring, demographic desirability, school
  quality, neighborhood quality, market/investment/lending suitability, or
  protected-class proxy feature.
- No legal conclusion that the system is fair-housing compliant or production secure.
- No public API or database schema change unless the audit finds a repo-confirmed bug.

## Current state

- `state/POST_RC_AUTHORITY_SPLIT.md` lists threat-model/proxy audit update as a
  repo-local implementation candidate.
- `state/LEVEL_9_10_GATE_MATRIX.md` keeps `L10-SEC-005` repo-local, `L10-SEC-008`
  private-MVP scoped, and `L10-SEC-009` partial. Those statuses require explicit
  hosted/external evidence before stronger claims.
- `docs/SECURITY.md`, `config/access_control.yaml`, `docs/runbooks/access_control.md`,
  source-review restrictions, report-language tests, private-MVP readiness checks, and
  security-scan artifacts already provide scattered safeguards.
- The missing piece is a single repo-local audit surface that maps threat/proxy risks to
  existing controls, tests, and remaining blockers without broadening product scope.

## Proposed design

Use an audit-first pass:

1. Identify canonical security/proxy authority files and tests.
2. Map protected surfaces: authentication, authorization, report access, review actions,
   source-derived evidence exposure, error pages, source reviews, and claim/report
   language.
3. Check for current safeguards against protected-class inputs, demographic proxies,
   recommendation/ranking semantics, and residential steering language.
4. Add a compact threat/proxy audit artifact or validator only if it reduces drift in
   existing repo-local controls.
5. Preserve all hosted, external review, DS-017, paid-vendor, and identity blockers.

Rejected alternatives:

- Implementing full RBAC/IdP now would exceed repo-local authority.
- Adding demographic/proxy data tests by ingesting demographic fields would violate the
  current MVP boundary.
- Treating static scans as sufficient would miss product-language and proxy-risk
  controls that are outside normal security scanners.

## Bottom-up sequence

1. Audit `docs/SECURITY.md`, `config/access_control.yaml`,
   `docs/runbooks/access_control.md`, source-review restrictions, overclaim tests,
   route error tests, and readiness validators.
2. Determine whether the manifest/index surfaces are exhaustive or intentionally scoped
   before adding any new declared entry.
3. Add or update the narrowest repo-local artifact that ties risks to controls and
   blockers.
4. Add focused tests or validator coverage only for concrete drift risks found during
   audit.
5. Run security/access-control/proxy-focused tests and the standard release/readiness
   gates.
6. Update state logs while keeping `L10-SEC-005`, `L10-SEC-008`, and `L10-SEC-009`
   scoped to repo-local/private-MVP evidence unless stronger external proof exists.

## Files likely to change

| File | Expected change |
|---|---|
| `docs/SECURITY.md` | Add or link a threat/proxy audit map if current guidance is incomplete. |
| `docs/runbooks/access_control.md` | Clarify access-control and hosted-identity boundaries if needed. |
| `config/access_control.yaml` | Change only if audit finds a declared-surface drift issue. |
| `scripts/*` | Add a small validator only if static docs/tests cannot guard the drift risk. |
| `backend/tests/*` | Add focused regressions only for repo-confirmed gaps. |
| `state/PROJECT_STATE.md` | Record active threat/proxy audit scope and validation. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and residual risk. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Update evidence/routing without promoting hosted readiness. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\private_mvp_readiness_check.py
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
cd backend; python -m pytest -q .\tests\api .\tests\reports .\tests\source_registry
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

Narrow checks may be refined after the audit identifies the actual affected files.

## Risks and blockers

- A repo-local audit can prevent drift, but it is not a substitute for an external
  security review, legal review, hosted identity design, production error/log review,
  or residential fair-housing review.
- Proxy-risk safeguards can be weakened by future source/geography/rulepack expansion,
  especially if demographic, valuation, school, neighborhood, insurance, lending, or
  recommendation language enters the system.
- Security and protected-class safety span docs, config, source reviews, routes, and
  report language, so the pass must trace controls end-to-end rather than checking a
  single file.

## Decision log

- 2026-06-18: Selected after `R-017` because compare/diff workflow smoke is complete
  and `state/POST_RC_AUTHORITY_SPLIT.md` lists threat-model/proxy audit update as the
  next unblocked repo-local candidate. This protects the Level 9/10 boundary around
  `L10-SEC-005`, `L10-SEC-008`, and `L10-SEC-009` without replacing external proof.
- 2026-06-18: Added a validate-only threat/proxy audit catalog and checker, composed it
  into release readiness, strengthened the security product boundary wording, and
  recorded Bandit medium findings as review debt rather than release blockers.
- 2026-06-18: Included two repo-confirmed audit hardening items: report source manifests
  now carry source-rights fields, and readiness-matrix validation pins
  `L10-SEC-008` plus compare semantics so future edits cannot silently overpromote
  protected-class/proxy or ranking/recommendation readiness.

## Progress log

- 2026-06-18: Plan opened after R-017 completed local release-candidate compare/diff
  workflow smoke.
- 2026-06-18: Read-only security, data-governance, and test-review audits completed.
  They found no need for hosted/auth runtime changes, but did identify the missing
  canonical threat/proxy map, source-rights manifest propagation, matrix pinning, and
  direct compare/diff API semantic guards as narrow repo-local hardening.
