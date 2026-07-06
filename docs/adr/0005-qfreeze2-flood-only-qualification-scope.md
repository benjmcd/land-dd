# ADR 0005: QFREEZE-2 flood-only qualification scope

## Status
Accepted

## Context
The owner-independent parameterization frontier was exhausted by the 2026-07-06
qualification closeout. The only selected approved source profile was `DS-002`, and
that source covers FEMA NFHL flood screening. It does not supply authority for the
other domain profiles.

`state/qfreeze2-flood-proposal.md` recorded the proposed flood-only freeze. PR #190
landed the proposal packet, and PR #191 applied the owner-authorized QFREEZE-2 freeze
under `state/owner-decisions.md`.

## Decision
Freeze the qualification scope to `qualified_domains: [flood]` for the DS-002 FEMA
NFHL screening profile.

The seven non-flood domains are excluded from the qualified scope as
`PROFILE_EXCLUDED_WITH_EVIDENCED_NA`:

- `wetlands`
- `slope_terrain`
- `soils_septic_proxy`
- `physical_road_access_proxy`
- `zoning_context`
- `environmental_context`
- `source_availability_and_conflict`

The target registry, applicable criterion contract parameterization, judgment rubrics,
candidate identity, and `config/qualification/domain_profiles/flood.yaml` are frozen
under the QFREEZE-2 owner decision. The live authority record is the 2026-07-06
QFREEZE-2 block in `state/owner-decisions.md`.

## Consequences
QFREEZE-2 closes parameterization blockers for the flood-only DS-002 scope and lets
the derived P0 state move from parameterization-blocked to `NOT_RUN`.

It does not record a sealed P0 run, result artifact, empirical qualification `PASS`,
non-flood domain qualification, source approval beyond DS-002, Bologna authority,
DS-017 approval, hosted authority, or Level 10 authority.

## Provenance
- Owner: `benjmcd`
- Owner decision date: 2026-07-06
- Proposal packet: `state/qfreeze2-flood-proposal.md`
- Authority ledger: `state/owner-decisions.md`
- PRs: #190, #191
