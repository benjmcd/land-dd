# Checklist Dry-Run Runbook

## Purpose

Use `config/checklist_dry_run.yaml` as the repo-local validate-only rehearsal for
jurisdiction and rulepack expansion checklists. The catalog dry-runs the existing
checklists against a `hypothetical_not_selected` candidate shape so the repo can prove
the checklists are executable before any future geography, source, connector, or
rulepack decision.

This proof does not approve a new geography, does not approve a new rulepack, does not
approve a new source, does not unblock DS-017, and does not claim hosted production
readiness.

In short: it does not claim hosted production readiness.

## Validate

Run from the repository root:

```powershell
.\scripts\run_checklist_dry_run_check.ps1
```

The check is validate-only. It verifies that:

- `config/checklist_dry_run.yaml` uses `checklist_dry_run_v1`;
- the candidate shape remains `hypothetical_not_selected`;
- all approval flags remain false;
- all limits preserve static, DB-free, artifact-free validation;
- every checkbox item in `docs/checklists/jurisdiction_readiness.md` is classified
  exactly once;
- every checkbox item in `docs/checklists/rulepack_readiness.md` is classified exactly
  once;
- every `repo_confirmed` item has catalog-owned evidence assertions that still match
  the cited repository evidence;
- every non-`repo_confirmed` item has a `next_action` and blocker authority;
- every `blocked_external_authority` item points to authority beyond the originating
  checklist;
- the dry run exercises all fail-closed classes:
  `missing_candidate_decision`, `missing_repo_evidence`,
  `blocked_external_authority`, and `not_applicable_existing_scope`.

## Status Meanings

`repo_confirmed` means current repository files provide evidence for the generic
checklist requirement inside the current selected-county/private-MVP scope.

`missing_candidate_decision` means the item cannot be completed until a specific
jurisdiction, source, connector, or rulepack scope is authorized.

`missing_repo_evidence` means the future candidate would need additional committed
tests, fixtures, sample reports, source-readiness outputs, or caveat documentation
before approval.

`blocked_external_authority` means repo-local work cannot satisfy the item without
external legal, source/license, local-domain, security, hosted, or vendor authority.

`not_applicable_existing_scope` means the dry run deliberately reuses the existing
homestead MVP intent and therefore does not approve a new intent or rulepack.

## Operator Interpretation

Passing validation means the checklist files and dry-run catalog are internally
consistent. It does not mean an expansion is approved.

Before any future expansion, replace the hypothetical candidate with an explicit plan
that names the candidate authority, source decisions, rulepack changes, tests, and
external blockers. Keep missing or blocked items visible until the required evidence is
committed or the external authority is obtained.

## Known Limits

- No new county, state, jurisdiction, source, connector, vendor, intent, or rulepack is
  selected.
- No live connector runs, database mutations, runtime artifacts, package builds, image
  pushes, hosted deployments, or seed operations happen.
- DS-017 remains blocked by vendor/license/cost/source-rights authority.
- Local checklist executability does not replace legal review, fair-housing review,
  local professional review, source-license review, security review, hosted IdP/RBAC,
  hosted alerting, billing, secret-manager, or production workload proof.
- Future expansion approval still requires checklist completion against the actual
  candidate, not this dry run.
