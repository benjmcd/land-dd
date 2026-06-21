# EQ-1 Boundary Consolidation

## Goal
Record the empirical-qualification adoption boundary before any framework spine code
lands. The outcome is an accepted ADR plus thin agent/routing references stating that
the empirical-qualification catalog will become the canonical empirical-validity
authority, while existing readiness and authority checks remain CI/deployment gates
that report into that control plane.

## Non-goals
- Do not copy qualification catalog, vocabulary, profile, schema, validator, selftest,
  status, crosswalk, or backlog artifacts in this lane.
- Do not add CI jobs, verification steps, runtime dependencies, product dependencies, or
  framework source files.
- Do not attempt any qualification `PASS`, change `P0 = BLOCKED`, or unfreeze owner
  decisions.
- Do not change DB schema, public API, auth boundaries, report semantics, source rights,
  Bologna authority, DS-017 authority, hosted authority, or Level 10 status.
- Do not delete files; archive only if a later lane explicitly retires an artifact.

## Current state
Live `origin/main` is `358389b2904a06e2a2b3192b5d118ec71190efce`, merged from PR
#123. The root checkout remains dirty preserved handoff state on
`codex/r026-raw-readiness-ui`; this lane is isolated in `worktrees/eq-1` on branch
`eq/eq1`.

The empirical-qualification handoff in
`plans/2026-06-21-empirical-qualification-adoption.md` requires EQ-1 as a hard gate
before EQ-2 can land the self-validating spine. The source package at
`C:\Users\benny\Downloads\land-dd_empirical_qualification` is read-only input. Its
assessment files support an ADAPT decision: the framework self-validates, but product
qualification is still blocked because active targets, source profiles, domain
profiles, rubrics, reviewers, and empirical evidence are not frozen.

Existing repo governance already includes readiness YAML/checkers, validate-only
authority packets, and `state/LEVEL_9_10_GATE_MATRIX.md`. The main EQ-1 risk is
creating a third competing authority surface instead of documenting a hierarchy.
This lane preserves the Level 9/10 authority context and does not change any
`state/LEVEL_9_10_GATE_MATRIX.md` gate status.

## Proposed design
Add `docs/adr/0004-empirical-qualification-control-plane.md` with an accepted decision:
the empirical-qualification catalog is the canonical empirical-validity authority once
the spine lands, and the existing readiness/authority checks are subordinate
CI/deployment gates that feed it rather than parallel truth sources.

Add one concise `AGENTS.md` paragraph so future agents see the boundary without loading
the long framework. Add a `MANIFEST.md` route entry for the upcoming qualification
control-plane files. Add queued tasks for EQ-1 through EQ-5 plus Lane R in
`tasks/task_queue.yaml`, keeping EQ-1 as the active governance lane and leaving later
lanes blocked or queued.

Rejected alternative: land the framework files in EQ-1. That would violate the
handoff's hard gate and risk a third authority surface before the boundary is decided.

Rejected alternative: defer the ADR until after validator integration. That would
allow EQ-2 to define authority by implementation rather than by an explicit decision.

## Bottom-up sequence
1. Add the EQ-1 ADR with status, context, decision, consequences, deferrals, and
   upcoming `jsonschema` dev/validation dependency boundary.
2. Add a concise `AGENTS.md` control-plane paragraph.
3. Add a `MANIFEST.md` source-of-truth route for empirical qualification.
4. Update `tasks/task_queue.yaml` so EQ-1 through EQ-5 and Lane R are visible, ordered,
   and parseable.
5. Update `state/PROJECT_STATE.md`, `state/WORKLOG.md`, and `state/VALIDATION_LOG.md`
   for this lane.
6. Run YAML parse, workspace validation, full verification, diff/no-deletion checks, and
   review before merge.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-21-eq-1-boundary-consolidation.md` | This lane plan |
| `docs/adr/0004-empirical-qualification-control-plane.md` | New boundary ADR |
| `AGENTS.md` | Thin empirical-qualification boundary paragraph |
| `MANIFEST.md` | Route entry for qualification control-plane artifacts |
| `plans/README.md` | Route current plan and adoption sequence |
| `tasks/task_queue.yaml` | Add EQ-1 through EQ-5 plus Lane R task entries |
| `state/PROJECT_STATE.md` | Record current checkpoint and next sequence |
| `state/WORKLOG.md` | Record work completed |
| `state/VALIDATION_LOG.md` | Record validation evidence |
| `backend/tests/test_readiness_core_artifacts.py` | Update current routing assertions |

## Tests / verification
```powershell
py -3.11 -c "import yaml; yaml.safe_load(open('tasks/task_queue.yaml', encoding='utf-8')); print('task queue parses')"
.\scripts\agent-context-check.ps1
.\scripts\validate_workspace.ps1
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

Expected signal: all checks pass; no tracked deletions; no product code changes; no
qualification spine, status, CI, or PASS claim is introduced.

## Risks and blockers
- If the ADR wording lets readiness checks remain independent authorities, EQ-2/EQ-4
  would multiply governance instead of consolidating it.
- If `jsonschema` is described as a runtime/product dependency, the ADR would conflict
  with the non-goal; it must be scoped to dev/validation tooling for EQ-2.
- `tasks/task_queue.yaml` is parse-sensitive, so every edit must be validated with
  PyYAML before commit.
- Separate-lane review is required before merge.

## Decision log
- 2026-06-21: Selected governance-only EQ-1. The framework is adapted under an ADR
  boundary before any validator/catalog/status files land.

## Progress log
- 2026-06-21: Created `worktrees/eq-1` from live `origin/main` at
  `358389b2904a06e2a2b3192b5d118ec71190efce`.
