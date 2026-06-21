# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-21-eqp2-1-status-check.md`.

Current routing plan: `2026-06-21-eqp2-1-status-check.md`.

`BSR-001` completed the validate-only Bologna source-rights matrix through PR #109.
Post-BSR routing landed through PR #110, and `BSG-001` completed the validate-only
Bologna source-authority intake guard through PR #111. `PAI-001` adds a
production-wide validate-only authority intake guard across DS-017, hosted platform,
secrets, identity/RBAC, image publication, billing, hosted observability, and Bologna
recorded-source blockers. There is still no unblocked Bologna implementation lane until
product/AOI/source-review authority exists. `BSA-001` remains blocked. Do not proceed
to fixture capture, runtime integration, source registry promotion, rulepack
implementation, hosted authority, DS-017 approval, or a multi-geography framework from
repo-local inference alone.

`SRP-001` reworks the retained dirty-root runtime-provenance regression into a
current-main selected-county fixture review-bundle/idempotency test. It is test-only
and does not change source/report behavior, source readiness, hosted authority, Bologna
authority, or Level 10 status.

`RSR-001` merged through PR #114 and records the post-SRP residual routing closeout.
After `RSR-001`, the only remaining `STILL_DIVERGENT` residual candidate paths are
`backend/app/project_readiness.py` and `backend/app/release_readiness.py`; both remain
deferred until a real control-plane consolidation slice is explicitly selected.

`BRC-001` adds a validate-only Bologna recorded-source corpus contract. It is allowed
because it defines future fixture-manifest requirements while preserving every external
authority blocker; it does not capture fixtures, promote sources, start Bologna, or
claim hosted/Level 10 authority. `BRC-001` merged through PR #116 at
`4b29bcf646e0cf61bbf3eedee00417a4eed9f115`.

`PR116-SYNC` is the current routing-only follow-up after PR #116. It updates live-state
surfaces to stop treating the completed corpus contract as active work while preserving
the same DS-017, hosted, Bologna implementation, and Level 10 blockers.

`AUTH-HANDOFF` hardens the production-authority intake runbook and validator so the
external evidence checklist stays in sync with the machine-readable blocked authority
streams. It does not approve DS-017, hosted, identity/RBAC, observability, image,
billing, Bologna, or Level 10 authority.

`READINESS-CORE` reworks the remaining dirty-root `project_readiness.py` and
`release_readiness.py` parser concepts into current-main read-only app models. The
models parse existing project/routing/release artifacts only; they do not change source
readiness, release semantics, report behavior, hosted authority, or Bologna authority.
`READINESS-CORE` merged through PR #119 at
`fa66b561e8820273963f51642d7dc3ef56ac0491`.

`BOL-PRIORITY` records the next-pursuit decision: the Bologna recorded-source pilot path
is now preferred over generic hosted-production, generic DS-017, and broad
production-authority lanes. `BPS-001` is now the first Bologna pursuit because it
splits pilot-scope authority from later `BSA-001` source/AOI/right-authority
preparation; fixture capture, source promotion, runtime/report use, DB seeds, hosted
authority, DS-017 approval, and Level 10 claims remain blocked until cited authority
exists.

`BPS-001` adds the missing first-gate pilot-scope authority packet before `BSA-001`.
It records the required product, one-AOI, jurisdiction, evidence-only/rulepack,
DS-017-treatment, fixture-boundary, runtime-boundary, and no-overclaim decisions while
keeping all authority references empty and downstream source/corpus updates disabled.
`BPS-001` merged through PR #121 at
`df96c21f9445fc5cb915d2b06ec0b2eb6c731f2f`.

`BPS-REQ-001` is the current Bologna pursuit. It adds structured
`scope_decision_requests` rows inside the existing pilot-scope authority packet so the
missing external evidence is actionable without approving a source, selecting an AOI,
capturing fixtures, changing source rights, or starting runtime work.

`EQ-ADOPT` records the empirical-qualification framework adoption milestone from PR
#123. The framework is an ADAPT path, not a whole-bundle adoption: EQ-1 must first
record the consolidation boundary, EQ-2 lands the self-validating spine, EQ-3 reports
an honest `P0 = BLOCKED`, EQ-4 subordinates existing readiness/authority checks through
a crosswalk, and EQ-5 tracks owner-decision blockers. Lane R separately corrects the
known false residual-reconciliation claim. No qualification `PASS`, source authority,
hosted authority, DS-017 approval, Bologna authority, or owner-decision unfreeze is
introduced by this routing.

`EQ-1` completed the boundary gate. It adds ADR 0004 and thin routing references so the
empirical-qualification catalog can become the canonical empirical-validity authority
without turning existing readiness and authority gates into competing truth sources.

`EQ-BOL` pulls the parameterization backlog visibility slice forward for the
prioritized Bologna path. It adds `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md`
and blocked task routing for P0 target/contract/rubric/domain/source/scope blockers,
plus Bologna pilot-scope, source-rights, recorded-corpus, and DB-backed report proof
blockers. It does not land the qualification spine, status file, CI gate, source
approval, AOI selection, fixture capture, runtime/report use, DS-017 approval, hosted
authority, owner-decision unfreeze, or Level 10 claim. If no external Bologna authority
arrives, the next repo-local empirical-qualification slice is `EQ-4`.

`EQ-2` lands the self-validating empirical-qualification spine. It imports the
framework docs, configuration, schemas, structural status, validator, and adversarial
selftest into repo-owned paths; adds `backend/tests/test_qualification_spine.py`;
adds `jsonschema` as a dev/validation dependency; and wires the qualification gate into
CI plus `verify`. The target registry remains `DRAFT`, the structural status has no
`PASS`, and the validator reports blocked-readiness warnings.

`EQ-3` formalizes the honest blocked status. It records P0 as `BLOCKED` with concrete
blocker references and no result artifact, archives the cloned draft domain stubs in
favor of one active template, and adds one DS-002 source-quality profile mapped to
production usage fields. No qualification `PASS`, owner-decision unfreeze, source
rights expansion, Bologna approval, fixture capture, runtime/report use, or fabricated
candidate artifact is introduced. If no external authority arrives, the next
repo-local slice is `EQ-4` readiness/authority crosswalk.

`EQ-4` subordinates existing readiness and authority gates to the empirical
qualification control plane. It adds a checked readiness crosswalk, schema, and human
doc; normalizes the change-impact matrix to catalog criterion IDs; and extends the
qualification validator/selftest so inventory drift and unknown criterion IDs fail
closed. It does not change checker behavior, satisfy any mapped criterion, claim a
qualification `PASS`, or unblock owner decisions. If no external authority arrives,
the next repo-local slice is `EQ-5` backlog reconciliation.

`EQP2-1` starts EQ Phase 2 operationalization after the PR #129 handoff. It adds a
derived qualification status checker that runs mapped readiness/authority checker
paths, treats passing readiness checks as non-passing inputs, keeps package-manifest
and spatial DB-runtime checks as explicit `NOT_RUN` cases until runtime inputs exist,
and fails closed when committed status drifts from the derived `P0 = BLOCKED` /
non-P0 `NOT_RUN` view. It wires that status check into verify and the dedicated
qualification CI job. No qualification `PASS`, owner-decision unfreeze, Bologna
approval, source approval, fixture capture, DB seed, report/runtime use, hosted
authority, DS-017 approval, or Level 10 claim is introduced.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the historical
source for initial retain/rework/defer/archive/discard decisions; current residual
classification is in `state/residual-reconciliation.md`.

Superseded plans should be moved to `plans/archive/` with a note at the top.
