# Bologna Source Authority Intake

`bologna_source_authority_intake_v1` is a validate-only intake guard for future Bologna
source/AOI authority. It records exactly what evidence must exist before the pending
Bologna source-rights matrix can be changed.

This does not approve sources, select a Bologna AOI, promote source registry rows,
capture fixtures, run connectors, change source readiness, approve a rulepack, unblock
DS-017, create hosted authority, or claim Level 10 production readiness.

## Use

Run:

```powershell
.\scripts\run_bologna_source_authority_intake_check.ps1
```

The checker cross-checks `config/bologna_source_authority_intake.yaml` against
`config/bologna_source_rights.yaml` and `config/bologna_preflight.yaml`. Every candidate
intake row must match the source-rights matrix candidate ids and required evidence
slots. The cadastral authority row must match the separate direct-review cadastral gap.

`source_authority_record_contract` is the structured format a future cited per-source
authority packet must satisfy before any source-rights row can change. Its contract
state is `ready_for_external_source_authority_evidence`; that means the record format
is ready, not that any source has been approved. The committed
`current_source_authority_records` list remains empty.

Any future source-authority record must link to upstream pilot-scope authority, target
a known candidate source or the cadastral gap, cover all required rights decisions,
provide the required evidence slots for that source, record terms/version/retrieval
metadata/CRS/attribution/caveats/storage-export boundaries/source-failure policy, and
request no downstream unlocks. A record that is incomplete, uncited, or requests source
promotion, source-rights edits, fixture capture, runtime/report use, DB seeding,
hosted/Level 10 status, or legal/title/buildability/value claims must fail validation.

## Promotion Boundary

Authority intake can unlock a later source-rights edit only when cited evidence names:

- the product-approved one-AOI Bologna scope;
- the exact candidate source or cadastral source;
- source owner, terms, license, source version/date, attribution, and retrieval policy;
- cache, export, raw-data, AI-use, fixture, runtime, and report-use decisions;
- CRS/precision, caveat, no-data, and source-failure policies;
- review owner and no-overclaim boundary.

Until then, every `authority_state` remains `missing_authority`, every
`authority_references` list remains empty, and every `decision_updates_allowed` value
remains false.
