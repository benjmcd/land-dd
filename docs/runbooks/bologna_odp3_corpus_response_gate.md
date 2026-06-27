# Bologna ODP-BOL-003 Corpus Response Gate

Schema: `bologna_odp3_corpus_response_gate_v1`

This runbook is validate-only. It does not record corpus authority, record owner
authority, approve a recorded corpus, capture fixtures, capture source-failure fixtures,
seed the database, create runtime/report artifacts, approve DS-017, or claim hosted/Level
10 authority.

Use this gate only to check that a future owner response for `ODP-BOL-003` is complete
enough to be recorded in a later authority slice. The current committed state must keep
`ODP-BOL-001` pilot-scope authority missing after the review-only scope-pursuit answer
and keep `ODP-BOL-002` missing, `current_owner_answer_references`,
`current_corpus_authority_references`, and `current_recorded_corpus_references` empty.
Every `downstream_updates_allowed` value must remain false.

Run:

```powershell
.\scripts\run_bologna_odp3_corpus_response_gate_check.ps1
```

The gate aligns the owner response with these required corpus decisions from
`config/bologna_recorded_source_corpus.yaml`:

- `one_aoi_scope`
- `exact_source_selection`
- `completed_per_source_rights_review`
- `source_contract_fields_complete`
- `source_registry_row_review`
- `recorded_fixture_scope`
- `retrieval_metadata_policy`
- `source_version_policy`
- `attribution_policy`
- `crs_precision_policy`
- `field_allowlist`
- `field_denylist`
- `no_data_policy`
- `source_failure_policy`
- `caveat_policy`
- `report_use_policy`
- `raw_data_export_policy`
- `review_owner`
- `no_overclaim_review`

It also aligns required manifest fields with `config/bologna_recorded_source_corpus.yaml`:

- `manifest_schema_version`
- `corpus_id`
- `one_aoi_authority_reference`
- `source_authority_references`
- `source_contract_references`
- `source_versions`
- `retrieval_metadata`
- `fixture_file_manifest`
- `source_failure_fixture_manifest`
- `attribution_text`
- `crs_and_precision`
- `field_allowlist`
- `field_denylist`
- `no_data_policy`
- `caveat_policy`
- `report_use_policy`
- `review_owner`
- `no_overclaim_review`

Candidate corpus requirements remain blocked for:

- `comune_bologna_pug_webgis`
- `comune_bologna_open_data_pug_constraints`
- `rer_geoportale_dbtr_altimetry`
- `rer_geoportale_catalog_services`
- `rer_crs_reference`
- `arpae_cartographic_portal`
- `cadastral_gap`

A future owner response may choose `approve_with_cited_authority`, `keep_blocked`,
`approve_review_only`, or `exclude_or_defer`. None of those outcomes authorizes corpus
authority recording, recorded corpus approval, fixture capture, source-failure fixture
capture, DB mutation, report proof, hosted deployment, or Level 10 claims in this gate.
