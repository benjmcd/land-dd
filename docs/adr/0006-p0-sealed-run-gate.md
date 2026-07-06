# ADR 0006: P0 sealed-run gate

## Status
Accepted

## Context
QFREEZE-2 froze flood-only parameterization and moved the derived P0 status to
`NOT_RUN`. It did not produce a sealed run, result artifact, or qualification `PASS`.

The current `scripts/qualification_*.py` tools are validators and checkers. They read,
validate, and derive qualification state; they do not write a
`qualification_result_v3` artifact and do not flip committed status.

## Decision
A future `P0 = PASS` requires a separate sealed-run lane and a greenfield
`qualification_result_v3` writer or runner. That lane must produce a result artifact
that validates against `schemas/qualification/qualification_result.schema.json` before
`state/EMPIRICAL_QUALIFICATION_STATUS.yaml` can point P0 at the result.

The six never-N/A P0 invariants are:

- `P0-004`
- `P0-005`
- `P0-021`
- `P0-023`
- `P0-027`
- `P0-030`

These criteria must pass with concrete evidence in the sealed run. They cannot be
marked `N/A`, and they cannot be satisfied by the QFREEZE-2 parameterization freeze.

## Consequences
Owner-independent scaffolding may prepare the sealed-run path only if it holds at PR
and does not change P0 status or create a PASS claim.

A real PASS remains blocked on ODP-PRO-001 owner/infra decisions, including an
`external_restricted_vault`, a fresh non-fixture cohort, at least two independent
reviewers plus an adjudicator with IRR >= 0.7 for P0-012/013/014/015/025, an
independent reproducer for P0-022, run authorization, and later status-flip
authorization.

## Provenance
- Packet: `state/p0-sealed-run-decision-packet.md`
- Authority boundary: `state/owner-decisions.md`
- Status file: `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`
- Schema: `schemas/qualification/qualification_result.schema.json`
