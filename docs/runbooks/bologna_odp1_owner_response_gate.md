# Bologna ODP-BOL-001 Owner Response Gate

Schema: `bologna_odp1_owner_response_gate_v1`

This runbook is validate-only. It does not record owner authority, select a Bologna
AOI, approve sources, change source rights, capture fixtures, seed the database, create
runtime/report artifacts, approve DS-017, or claim hosted/Level 10 authority.

Use this gate only to check the owner response for `ODP-BOL-001`. The current committed
state records review-only scope pursuit through
`odp-bol-001-scope-pursuit-2026-06-26` in `current_owner_answer_references`, but keeps
`current_authority_record_references` empty and every `downstream_updates_allowed`
value false. This is not complete pilot-scope authority.

Run:

```powershell
.\scripts\run_bologna_odp1_owner_response_gate_check.ps1
```

The gate aligns the owner response with these required scope decisions from
`config/bologna_pilot_scope_authority.yaml`:

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

A future owner response may choose `approve_with_cited_authority`, `keep_blocked`,
`approve_review_only`, or `exclude_or_defer`. The current response is
`approve_review_only`. None of those outcomes authorizes source approval, source-rights
approval, recorded corpus work, fixture capture, DB mutation, report proof, hosted
deployment, or Level 10 claims in this gate.
