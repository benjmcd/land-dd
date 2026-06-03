# Agent Operating Loop

## Default loop

```text
explore -> plan -> test -> implement -> narrow verify -> review -> full verify -> update state
```

## Verification cadence

- Run narrow tests after each coherent slice.
- Run `./scripts/verify.sh` before handoff.
- Run DB smoke checks when DB migrations or persistence code changes and Docker is available.
- Run a review pass with the other model family or a Claude subagent after material implementation.

## Reinvestigation cadence

Re-read or challenge the plan when:
- a task touches architecture, schema, source semantics, scoring, or compliance;
- the implementation discovers a contradiction with docs/tests;
- three work packages have completed without a coherence check;
- a dependency, data source, or jurisdiction assumption changes.
