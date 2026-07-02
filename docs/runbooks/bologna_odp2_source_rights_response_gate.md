# Bologna ODP-BOL-002 Source-Rights Response Gate

Schema: `bologna_odp2_source_rights_response_gate_v1`

This runbook is validate-only. It does not record source authority, record owner
authority, approve sources, change source rights, promote source registry rows, capture
fixtures, seed the database, create runtime/report artifacts, approve DS-017, or claim
hosted/Level 10 authority.

Use this gate only to check that a future owner response for `ODP-BOL-002` is complete
enough to be recorded in a later authority slice. The current committed state must keep
`ODP-BOL-001` pilot-scope authority missing after the review-only scope-pursuit answer,
`current_owner_answer_references`, `current_source_authority_record_references`, and
`current_source_rights_approval_references` empty, and every
`downstream_updates_allowed` value false.

Run:

```powershell
.\scripts\run_bologna_odp2_source_rights_response_gate_check.ps1
```

The gate aligns the owner response with these required rights decisions from
`config/bologna_source_rights.yaml`:

- `terms_reference`
- `terms_effective_date`
- `source_version_or_publication_date`
- `update_cadence`
- `license_status`
- `commercial_use_status`
- `redistribution_status`
- `cache_allowed`
- `export_allowed`
- `raw_data_allowed`
- `ai_use_allowed`
- `attribution_required`
- `retrieval_metadata_policy`
- `source_failure_policy`
- `no_data_policy`
- `caveat_policy`
- `crs_precision_policy`
- `field_allowlist`
- `field_denylist`
- `fixture_capture_policy`
- `report_use_policy`

It also aligns candidate evidence slots with `config/bologna_source_authority_intake.yaml`
for:

- `comune_bologna_pug_webgis`
- `comune_bologna_open_data_pug_constraints`
- `rer_geoportale_dbtr_altimetry`
- `rer_geoportale_catalog_services`
- `rer_crs_reference`
- `arpae_cartographic_portal`
- `cadastral_gap`

A future owner response may choose `approve_with_cited_authority`, `keep_blocked`,
`approve_review_only`, or `exclude_or_defer`. None of those outcomes authorizes source
approval, source-rights approval, recorded corpus work, fixture capture, DB mutation,
report proof, hosted deployment, or Level 10 claims in this gate.
