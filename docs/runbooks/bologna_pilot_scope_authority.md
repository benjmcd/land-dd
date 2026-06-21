# Bologna Pilot Scope Authority

`bologna_pilot_scope_authority_v1` is a validate-only first-gate packet for the
Bologna recorded-source pilot. It separates product, one-AOI, jurisdiction, rulepack,
DS-017-treatment, fixture-boundary, and runtime-boundary authority from later
per-source rights review.

This does not select a Bologna AOI, approve Italy/EU/local sources, change source
rights, promote source registry rows, capture fixtures, run connectors, mutate the
database, create runtime artifacts, unblock DS-017, claim legal review, claim hosted
production readiness, or approve a multi-geography framework.
It does not approve Italy/EU/local sources.

## Use

Run:

```powershell
.\scripts\run_bologna_pilot_scope_authority_check.ps1
```

The checker verifies that `config/bologna_pilot_scope_authority.yaml` remains
blocked, references the current Bologna authority catalogs, and keeps every downstream
unlock disabled until cited authority exists.

## Evidence Checklist

Collect all required scope decisions before any Bologna source-rights row can move out
of pending review:

- `product_authorizes_bologna_pilot_reference`
- `one_aoi_geometry_or_named_boundary`
- `intended_operator_and_use_case`
- `pilot_non_goals_and_exclusions`
- `stop_conditions_and_reversion_plan`
- `jurisdiction_boundary_review`
- `evidence_only_or_rulepack_scope`
- `ds017_treatment_for_pilot`
- `candidate_source_selection_policy`
- `fixture_capture_boundary`
- `report_runtime_boundary`
- `no_overclaim_review_owner`

Until those are cited, `authority_state` remains `missing_authority`,
`authority_references` remains empty, and `decision_updates_allowed` remains false.

## Downstream Boundary

This packet can only unlock later review edits. It never supplies the authority itself.
The downstream targets stay blocked:

- `config/bologna_source_authority_intake.yaml`
- `config/bologna_source_rights.yaml`
- `config/bologna_recorded_source_corpus.yaml`

Per-source rights, source registry promotion, recorded fixtures, source-failure
fixtures, report/runtime proof, and any rulepack implementation require their own
validated authority after this first gate.
