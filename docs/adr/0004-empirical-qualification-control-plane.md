# ADR 0004: Empirical qualification control plane

## Status
Accepted

## Context
The repository already has several validate-only governance surfaces:
readiness YAML/checkers, authority packets, release-readiness checks, and
`state/LEVEL_9_10_GATE_MATRIX.md`. The empirical-qualification framework adds a
self-validating vocabulary, criterion catalog, profiles, status records, and validator
for empirical-validity claims.

Adopting the framework as another independent gate system would multiply authority
surfaces and make it easier to overclaim. The framework is useful only if it
consolidates empirical-validity governance and makes unresolved product, source,
domain, target, reviewer, and evidence decisions remain blocked.

The framework source package is read-only input. Its validation report supports an
ADAPT decision: the framework structure and adversarial selftest pass, but the current
project-specific qualification remains blocked. `P0` cannot pass while targets,
source profiles, domain profiles, rubrics, reviewers, and empirical evidence are
unfrozen.

## Decision
Adopt the empirical-qualification catalog, once the spine lands, as the canonical
empirical-validity authority for land-dd. Existing readiness YAML/checkers, authority
packets, release-readiness checks, and `state/LEVEL_9_10_GATE_MATRIX.md` remain
CI/deployment gate layers that report into the empirical-qualification control plane.
They are not parallel empirical-validity authorities.

EQ-1 records only the boundary. Later lanes may land the vocabulary, catalog, profiles,
schemas, validator, status file, crosswalk, and backlog under this ADR. Those later
lanes must preserve an honest `P0 = BLOCKED` until external owner decisions and
empirical evidence are frozen.

`jsonschema` is approved only as a development/validation dependency for the
qualification validator and CI gate. It is not a runtime/product dependency and does
not authorize broader framework or product behavior.

## Deferrals
- Do not land Q3A, Q3B, or Q3C expansion docs, targets, or governance beyond catalog
  entries required by the spine.
- Do not land AI, CG, FIN, or E rubrics or targets while those capabilities remain
  disabled.
- Do not copy the eight byte-identical domain-profile stubs; later lanes must collapse
  them to one template.
- Do not claim qualification `PASS`, Level 10 completion, new source authority, hosted
  authority, Bologna authority, DS-017 approval, or owner-decision resolution from this
  ADR.

## Consequences
- Future agents should route empirical-validity questions through the qualification
  catalog/status once landed, not through ad hoc readiness prose alone.
- Existing readiness and authority validators remain valuable, but their durable role is
  evidence into the qualification catalog and status, not independent product
  qualification.
- EQ-2 must wire a self-validating spine and CI gate under this decision.
- EQ-3 must report the current product state honestly as blocked.
- EQ-4 must map existing readiness/authority checks to criterion IDs and expose gaps or
  orphaned checks.
- Changes that would move a gate to `PASS` or unfreeze an owner decision require
  explicit authority and validation, not repo-local inference.
