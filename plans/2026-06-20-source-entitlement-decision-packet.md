# Source Entitlement Decision Packet

## Goal

Make the DS-017 commercial parcel-vendor blocker decision-ready by adding a
validate-only, machine-readable source-entitlement packet and checker. The checker must
prove the current blocked state and enumerate the external authority required before
DS-017 can be approved, deferred, removed from Must scope, or replaced.

## Non-goals

- No DS-017 vendor selection, license approval, connector, source-registry promotion,
  raw vendor-data handling, owner/value/title exposure, paid-source metering, or report
  semantic expansion.
- No hosted deployment, hosted identity/RBAC, hosted observability, billing,
  image-publication, Bologna pilot, new geography, rulepack, or Level 10 completion
  claim.
- No generated runtime artifacts, live vendor calls, fixture seeding, DB schema change,
  or public API behavior change.

## Current state

- `scripts/source_readiness.py --priority Must --json` reports `sources=8 ready=7
  blocked=1`; `DS-017` is the only blocked Must source.
- `state/PRODUCTION_AUTHORITY_PACKET.md` already names the DS-017 external decisions
  and evidence fields, but it is prose-only.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority; this slice only
  adds validate-only DS-017 decision-readiness proof and does not promote Level 10
  production gates.
- `backend/app/source_registry/usage_rights.py` and its tests already enforce
  fail-closed report/export exposure for blocked, unknown, or restricted source-rights
  values.
- Release readiness records `non_ready_must_sources` as blocked, but it does not yet
  validate a DS-017-specific decision packet.

## Proposed design

Add `config/source_entitlements.yaml` as the canonical machine-readable source
entitlement packet for DS-017. Add `scripts/source_entitlement_check.py` and
PowerShell/POSIX wrappers to validate that:

- the packet is validate-only and artifact-free;
- DS-017 is present, Must-priority, blocked in the source registry, and not connector
  ready;
- DS-017 required authority fields include vendor/license/commercial/cache/export/raw
  data/AI/cost/entitlement/field-policy/failure-mode decisions;
- acceptable decision paths are explicit: approve under contract, defer or remove from
  Must scope, or substitute public/official sources;
- forbidden outputs remain blocked until separately approved and entitlement-gated.

Rejected alternatives:

- Approving DS-017 locally is invalid without vendor/license/cost authority.
- Another prose-only packet would duplicate `state/PRODUCTION_AUTHORITY_PACKET.md`.
- Hosted/Bologna work is premature because this Must-source blocker still lacks an
  explicit decision gate.

## Bottom-up sequence

1. Add failing tests for the source-entitlement packet, validator, release-readiness
   composition, and runbook references.
2. Add `config/source_entitlements.yaml`, validator, and wrappers.
3. Wire the new validator into release readiness as a validate-only proof.
4. Update manifest/routing/state so G9c is complete and this DS-017 decision packet is
   active.
5. Run focused checks, release/source/readiness validators, workspace validation, and
   full `.\scripts\verify.ps1`.

## Files likely to change

| File | Expected change |
|---|---|
| `config/source_entitlements.yaml` | New DS-017 machine-readable decision packet |
| `scripts/source_entitlement_check.py` | New validate-only checker |
| `scripts/run_source_entitlement_check.ps1` | Windows wrapper |
| `scripts/run_source_entitlement_check.sh` | POSIX wrapper |
| `backend/tests/test_source_entitlement_artifacts.py` | New checker/config tests |
| `config/release_readiness.yaml` | Add source-entitlement release proof |
| `scripts/release_readiness_check.py` | Compose source-entitlement validator |
| `backend/tests/test_release_readiness_artifacts.py` | Update release readiness expectations |
| `docs/runbooks/source_entitlements.md` | New operator runbook |
| `docs/runbooks/release_readiness.md` | Add source-entitlement gate notes |
| `MANIFEST.md` | Route source-entitlement authority |
| `plans/README.md` | Mark G9c complete and route to this plan |
| `tasks/task_queue.yaml` | Mark G9c done and add active DS-017 decision packet task |
| `state/PROJECT_STATE.md` | Current checkpoint update |
| `state/WORKLOG.md` | Worklog entry |
| `state/VALIDATION_LOG.md` | Validation entry |

## Tests / verification

```powershell
py -3.12 -m pytest backend\tests\test_source_entitlement_artifacts.py backend\tests\test_release_readiness_artifacts.py -q
py -3.12 .\scripts\source_entitlement_check.py
.\scripts\run_source_entitlement_check.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks and blockers

- The packet could be mistaken for approval. The config, validator, and runbook must
  keep DS-017 blocked unless external authority changes.
- The release-readiness gate can become too rigid if it encodes a single vendor path.
  The checker should validate required decision fields and allowed outcomes, not a
  vendor choice.
- DS-017 could be deferred or removed from Must scope later. The packet should make
  that an explicit product decision path rather than a hidden readiness bypass.

## Decision log

- 2026-06-20: Chose a validate-only machine-readable DS-017 decision packet because
  current source readiness confirms DS-017 is the only Must blocker, while source-rights
  export enforcement and a prose production authority packet already exist.

## Progress log

- 2026-06-20: Plan opened from clean `worktrees/ds017-ent` after PR #105 landed on
  `origin/main`.
- 2026-06-20: Added the DS-017 source-entitlement packet, validate-only checker,
  wrappers, runbook, release-readiness composition, focused tests, and routing/state
  updates. Focused tests, source-entitlement wrapper, source-readiness, release
  readiness, readiness-matrix, diff/no-deletion checks, workspace validation, and
  default `.\scripts\verify.ps1` passed. DB smoke was skipped by default.
