# Bologna Owner Answer Intake

`bologna_owner_answer_intake_v1` is a validate-only intake guard for the owner answers
needed before the prioritized Bologna recorded-source path can proceed. It maps
`ODP-BOL-001` through `ODP-BOL-004` to the existing pilot-scope, source-authority,
source-rights, recorded-corpus, evidence, and report-run contracts.

This does not record owner authority, select a Bologna AOI, approve Italy/EU/local
sources, change source rights, promote source registry rows, capture fixtures, create
source-failure fixtures, run connectors, mutate the database, create runtime artifacts,
create report artifacts, approve DS-017, claim legal review, claim hosted production
readiness, or claim Level 10.

## Use

Run:

```powershell
.\scripts\run_bologna_owner_answer_intake_check.ps1
```

The checker verifies that `config/bologna_owner_answer_intake.yaml` remains blocked,
keeps every `downstream_updates_allowed` flag false, and aligns the owner-answer
threads with the existing Bologna authority contracts:

- `ODP-BOL-001`: product, one-AOI, operator/use-case, non-goal, stop-condition,
  jurisdiction, scope-mode, DS-017-treatment, source-selection, fixture-boundary,
  runtime-boundary, and no-overclaim owner decisions.
- `ODP-BOL-002`: exact source authority and rights decisions for the current Bologna
  candidate set plus the cadastral direct-review gap.
- `ODP-BOL-003`: recorded-source corpus decisions and manifest fields.
- `ODP-BOL-004`: one local DB-backed report proof with claims, evidence, unknowns,
  caveats, artifacts, lineage, storage/export boundaries, and no-overclaim review.

## Owner Answer Contract

`owner_answer_contract` defines the shape for future cited owner answers. The committed
`current_owner_answers` list remains empty until external authority exists. A future
answer record must name its `odp_id`, answer type, decision owner, decision date,
authority reference, cited artifacts, caveats, and supersession links.

The intake does not unlock downstream work by itself. Even a complete answer record
must not request downstream unlocks here. Downstream changes still require the specific
Bologna authority records and validators for pilot scope, source authority, source
rights, corpus, and report proof.

## Boundary

Use this file to prepare owner answers, not to infer them. If evidence is missing, the
correct outcome is to keep the affected decision thread blocked. The repo remains at
`P0 = BLOCKED`; Bologna remains stopped until cited authority exists.
