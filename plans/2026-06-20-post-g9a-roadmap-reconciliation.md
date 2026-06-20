# Post-G9a Roadmap and Reconciliation Routing

## Goal

Make live `main` honest after the merged G9a custom AOI proof and route the next work
toward the largest coherent objective: a repeatable, evidence-led due-diligence compiler
that can move from selected North Carolina counties to generic supported AOIs, hosted
authority, source-entitlement decisions, a Bologna recorded-source pilot, and then a
multi-geography source/rulepack framework.

The immediate system-visible outcome is routing clarity: `state/PROJECT_STATE.md`,
`plans/README.md`, `tasks/task_queue.yaml`, and the reconciliation artifacts should no
longer say G9a is active or that PR #101 still needs publication.

## Non-goals

- No product behavior, API, schema, report semantics, source registry, connector, or UI
  change.
- No DS-017 approval, vendor entitlement decision, source expansion, or paid-source
  integration.
- No hosted deployment, hosted identity/RBAC, hosted observability, hosted object-store,
  billing, secret-manager, registry-publication, or SLO proof.
- No Bologna source implementation, recorded-source fixture, new jurisdiction/rulepack,
  or Italy-wide abstraction.
- No deletion, cleanup, reset, or physical archiving of the dirty-root candidate
  workspace.

## Current state

- Live `origin/main` has advanced to `b525439e6bcddefba81c7d6bf12290b3f8551b55`, which
  merged PR #101 from `codex/aoi-smoke`.
- The handoff file named by the session was not present at
  `C:\Users\benny\Downloads\land_dd_lane_reference_handoff_v4(1).md`. The nearest lane
  reference found and read was `land_dd_lane_reference_handoff_current.md`; it is useful
  as non-authoritative planning context but names the older `c3364ea` live baseline.
- Live routing still points at `plans/2026-06-20-custom-aoi-ui-runtime-smoke.md` and
  active task `G9a`, even though G9a is merged.
- The root checkout remains a dirty preserved-candidate branch, not implementation
  authority. New implementation work must happen from fresh worktrees under
  `worktrees/<short-name>`.
- Existing reconciliation artifacts already provide the initial dirty-root inventory,
  slice map, and dispositions. They predate the later G-slice landings and need a
  residual pass rather than a restart.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 gate authority. This routing
  pass may clarify next work, but it does not change any Level 9/10 gate status.
- External-authority blockers remain: hosted platform, identity/RBAC, secret manager,
  hosted alerting/log retention/on-call, object-store/artifact publication, billing,
  registry/image publication, DS-017 vendor/license/cost authority, and production
  workload/SLO evidence.

## Proposed design

Update the repo routing to treat G9a as completed and make the next active slice
`REC-002`: a residual Lane 1 reconciliation and roadmap pass. That pass should compare
the preserved dirty-root candidate workspace against current live `origin/main`, mark
which candidate concepts have already landed through PR #101, and identify the next
unblocked retained slice.

Talmudic debate / coherence check:

- Position A: continue directly into hosted staging. Rejected for now because hosted
  platform, secret, identity, artifact, billing, alerting, and production workload
  authority are still external blockers.
- Position B: start Bologna now. Rejected for now because Bologna depends on stable
  generic AOI/report behavior, source-rights review for recorded Italian sources, CRS
  handling, and a source manifest. Starting it now would risk a geography fork.
- Position C: implement DS-017 or vendor entitlement now. Rejected for repo-local work
  because DS-017 remains an external product/legal/cost decision; engineering can only
  prepare fail-closed guardrails until authority exists.
- Position D: keep landing retained dirty-root slices blindly. Rejected because many
  retained slices have now landed and the original inventory baseline is stale.
- Position E: route to residual reconciliation first. Accepted because it is the
  narrowest step that restores authoritative state, prevents duplicate work, and
  preserves the dependency order for generic AOI, hosted authority, DS-017, Bologna, and
  multi-geography work.

## Bottom-up sequence

1. Mark G9a done in the task queue and route the active plan to this post-G9a
   reconciliation plan.
2. Update project state, plan index, reconciliation artifacts, worklog, and validation
   log to reflect PR #101 and the new residual Lane 1 pass.
3. Validate the metadata-only change with YAML parsing, workspace validation, diff
   hygiene, no-deletion check, and the normal Windows verification gate.
4. In the next implementation worktree, regenerate a residual dirty-root inventory
   against `b525439...` and classify each candidate path as already landed, still
   divergent, deferred, obsolete, or coordination/generated.
5. From that residual inventory, select the next unblocked engineering slice:
   source-entitlement/DS-017 decision support if it is still repo-local, generic AOI
   evidence-rich closure if more supported-AOI proof is the best available work, or
   hosted authority work only if external platform/identity/artifact prerequisites have
   been granted.
6. After generic AOI and source-rights prerequisites are credible, prepare the Bologna
   recorded-source pilot as one AOI with recorded sources, CRS provenance, caveats, and
   DB-backed dossier/artifact/lineage proof.
7. Only after Bologna reveals the real extension points, design the multi-geography
   source/rulepack framework around common NC plus Bologna contracts.

## Files likely to change

| File | Expected change |
|---|---|
| `plans/2026-06-20-post-g9a-roadmap-reconciliation.md` | Active executable plan for post-G9a routing. |
| `plans/README.md` | Mark G9a completed and this plan active. |
| `tasks/task_queue.yaml` | Mark `G9a` done and add active `REC-002`. |
| `state/PROJECT_STATE.md` | New current checkpoint, G9a post-merge status, and next pass. |
| `state/reconciliation-slices.md` | Record that the original slice map is stale after G9a and needs residual refresh. |
| `state/reconciliation-dispositions.md` | Record live progress through G9a and residual classification requirement. |
| `state/WORKLOG.md` | Note the routing correction and current authority facts. |
| `state/VALIDATION_LOG.md` | Record validation for this metadata-only slice. |

## Tests / verification

```powershell
py -3.12 -c "from pathlib import Path; import yaml; data=yaml.safe_load(Path('tasks/task_queue.yaml').read_text(encoding='utf-8')); print(data['active_plan']); print([t['id'] for t in data['tasks'] if t.get('status') == 'active'])"
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signal: active plan is this file, only active task is `REC-002`, no tracked
deletions are present, workspace validation passes, and the normal verification gate
passes. DB smoke remains default-off unless explicitly requested.

## Risks and blockers

- A state-only routing update can look like product progress. It is not; it only restores
  authority alignment after PR #101.
- The residual dirty-root inventory may show that some candidate concepts are now
  obsolete or already landed differently. That is expected and should not be treated as a
  regression.
- Hosted, DS-017, identity, billing, alerting, object-store, registry, and Bologna work
  remain blocked or premature until their prerequisites are available.

## Decision log

- 2026-06-20: Selected residual Lane 1 reconciliation as the next active pass after live
  `origin/main` was confirmed at PR #101 merge commit `b525439...` and current routing
  still pointed at active G9a.

## Progress log

- 2026-06-20: Created clean worktree `worktrees/lane-route` on `codex/lane-route` from
  `origin/main`, confirmed the exact named handoff file was absent, read the nearest
  current lane-reference handoff as non-authoritative context, and prepared this
  metadata-only routing plan.
- 2026-06-20: Continued in clean worktree `worktrees/res-rec` on `codex/res-rec` from
  live `origin/main` at `47913930ea6b5fc0af71e463d998f57535b7cad4`, generated
  `state/residual-reconciliation.md` from the preserved dirty-root candidate checkout,
  and routed the next active plan to `G9b` generic supported-AOI evidence-rich workflow
  closure.
