# Bologna Preflight Runbook

## Purpose

Use `config/bologna_preflight.yaml` as the repo-local validate-only preflight for a
future Bologna recorded-source pilot. The catalog keeps the pilot in a not-started
state while making its prerequisites explicit: candidate authority, Italy/EU/local
source rights, DS-017 treatment, rulepack scope, recorded fixtures, DB-backed report
proof, hosted authority, and the later multi-geography framework boundary.

`config/bologna_source_candidates.yaml` (`bologna_source_candidates_v1`) is the
candidate-only source inventory attached to this preflight. It narrows source-rights
follow-up work, but it does not approve any source for recorded fixtures, runtime use,
or reports.

`config/bologna_source_rights.yaml` (`bologna_source_rights_v1`) is the fail-closed
rights matrix attached to this preflight. It keeps every candidate source pending until
terms, license, cache, export, AI-use, raw-data, attribution, source version,
retrieval, caveat, CRS, fixture, and report-use decisions are reviewed.

`config/bologna_pilot_scope_authority.yaml`
(`bologna_pilot_scope_authority_v1`) is the blocked first-gate pilot-scope authority
packet. It must cite product, one-AOI, jurisdiction, rulepack/evidence-only,
DS-017-treatment, fixture-boundary, runtime-boundary, and no-overclaim decisions before
source-authority or corpus updates can start.

`config/bologna_source_authority_intake.yaml`
(`bologna_source_authority_intake_v1`) is the blocked source-authority intake guard. It
must cite real product/AOI/source-review authority before any pending source-rights
matrix decision is changed.

`config/bologna_recorded_source_corpus.yaml`
(`bologna_recorded_source_corpus_v1`) is the blocked recorded-source corpus contract. It
defines future manifest requirements for source versions, retrieval metadata,
attribution, CRS, source-failure fixtures, caveats, and no-overclaim review without
allowing fixture capture.

This proof does not select Bologna, does not approve Italy sources, does not approve an
EU/Italy rulepack, does not unblock DS-017, does not create runtime artifacts, and does
not claim hosted production readiness.

In short: it does not approve an EU/Italy rulepack and does not claim hosted
production readiness.

It does not claim hosted production readiness.

## Validate

Run from the repository root:

```powershell
.\scripts\run_bologna_preflight_check.ps1
```

The check is validate-only. It verifies that:

- `config/bologna_preflight.yaml` uses `bologna_preflight_v1`;
- the candidate remains `not_started_external_authority_required`;
- every approval flag remains false;
- limits preserve static, DB-free, artifact-free validation;
- every preflight gate is classified exactly once with an allowed fail-closed status;
- every `repo_confirmed` gate has evidence assertions that still match cited files;
- the Bologna source-candidates packet remains candidate-only and unapproved;
- the Bologna source-rights matrix remains validate-only and unapproved;
- the Bologna pilot-scope authority packet remains blocked and uncited;
- the Bologna source-authority intake remains blocked and uncited;
- the Bologna recorded-source corpus contract remains blocked and fixture-free;
- every non-`repo_confirmed` gate has a `next_action` and blocker authority;
- `blocked_external_authority` gates point to existing authority files;
- the runbook and production authority packet preserve the boundary that this does not
  start Bologna.

## Status Meanings

`repo_confirmed` means current repo files prove a lower-layer prerequisite in the
selected-county/private-MVP or repo-local scope only.

`missing_candidate_decision` means the item cannot be completed until a named pilot,
source, jurisdiction, or rulepack decision is authorized.

`missing_repo_evidence` means the future pilot would need committed fixtures, tests,
source manifests, report evidence, or documentation before approval.

`blocked_external_authority` means repo-local work cannot satisfy the item without
external source/license, local-domain, product, security, hosted, or vendor authority.

## Operator Interpretation

Passing validation means the Bologna preflight catalog is internally consistent. It
does not mean the pilot is approved, implemented, source-ready, legally reviewed,
hosted, or generalizable.

Before a Bologna implementation pass starts, open a separate executable plan that names
the authorized AOI, recorded sources, source-rights decisions, rulepack scope, fixture
corpus, CRS/geometry policy, tests, and explicit non-goals. Keep missing or blocked
items visible until the required evidence is committed or the external authority is
obtained.

## Known Limits

- No new geography, source, connector, vendor, intent, or rulepack is selected.
- No live connector runs, database mutations, runtime artifacts, package builds, image
  pushes, hosted deployments, or seed operations happen.
- DS-017 remains blocked unless a later product/source decision approves, defers,
  removes, or substitutes it through the source-entitlement process.
- The current US jurisdiction and rulepack checklists are useful patterns, not approval
  for an Italy/EU locality.
- Local preflight consistency does not replace legal review, local professional review,
  source-license review, security review, hosted IdP/RBAC, hosted alerting, billing,
  secret-manager, or production workload proof.
