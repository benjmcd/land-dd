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

`scope_decision_requests` is the structured request table for the missing first-gate
decisions. Each row names the expected reference, minimum evidence, and downstream use
for one required decision while keeping `status: missing_authority`,
`authority_references: []`, and `decision_updates_allowed: false`.

`authority_record_contract` is the structured format a future cited authority packet
must satisfy before the missing decisions can be recorded. Its contract state is
`ready_for_external_authority_evidence`; that means the format is ready, not that any
authority has been granted. It defines required record fields such as
`authority_record_id`, `authority_type`, `authority_reference`,
`decision_owner`, `decision_date`, `effective_date`, `scope_decision_ids`,
`decision_summary`, `evidence_summary`, `cited_artifacts`,
`downstream_unlocks_requested`, `caveats`, `stop_conditions`, and
`supersedes_authority_record_ids`.

The contract is ready for external evidence, but `current_authority_records` remains
empty in the committed packet. The checker uses a complete-record-only policy for any
future non-empty record list: together, the records must cover all required scope
decisions, cite artifacts, carry caveats and stop conditions, and request no downstream
unlocks. A pilot-scope authority record must cover all required scope decisions before
any decision update is allowed. The record itself must not approve sources, change
source rights, authorize fixture capture, authorize report/runtime use, seed the
database, assert legal/title/buildability/value conclusions, or claim hosted/Level 10
readiness.

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
