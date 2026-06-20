# Bologna Source-Authority Intake Guard

## Goal

Add a validate-only authority-intake packet for the blocked Bologna source-authority
step. The packet makes future source/AOI authority evidence mechanically checkable
against `config/bologna_source_rights.yaml`.

This does not approve sources, select a Bologna AOI, promote source registry rows,
capture fixtures, run connectors, change source readiness, approve a rulepack, unblock
DS-017, create hosted authority, or claim Level 10 production readiness.

## Design

Add `config/bologna_source_authority_intake.yaml` and
`scripts/bologna_source_authority_intake_check.py`. The checker derives candidate ids,
per-candidate evidence slots, cadastral evidence slots, and promotion blockers from the
existing source-rights matrix.

Coherence check:

- Position A: fill source rights from public-looking source pages. Rejected because
  source/AOI/terms/version/cache/export/AI/raw-data/report authority is not cited.
- Position B: leave the blocker as prose. Rejected because later agents could change
  pending rights without a structured proof surface.
- Position C: add a validate-only intake guard. Accepted because it strengthens the
  blocked state and defines the exact evidence needed to unblock BSA later.

## Sequence

1. Add the authority-intake YAML packet, runbook, checker, wrappers, and focused tests.
2. Compose the packet into Bologna preflight's `italy_source_rights_review` gate.
3. Update manifest, task routing, state, worklog, and validation log.
4. Run focused Bologna checks, readiness checks, diff/no-deletion checks, workspace
   validation, and default `.\scripts\verify.ps1`.

## Acceptance

- Every intake candidate row matches a source-rights matrix candidate row.
- Every intake evidence slot matches that candidate's source-rights required evidence.
- The cadastral intake row matches the direct-review cadastral gap.
- All approvals remain false, authority references remain empty, and decision updates
  remain disallowed.
- Preflight includes the intake packet as evidence and blocker authority.
