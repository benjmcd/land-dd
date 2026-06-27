# Bologna ODP-BOL-002 Owner Answer Packet

Schema: `bologna_odp2_owner_answer_packet_v1`

This runbook is validate-only. It does not record source authority, approve source
rights, promote source registry rows, capture fixtures, seed the database, create
runtime/report artifacts, approve DS-017, or claim hosted/Level 10 authority.

Use this packet to prepare the owner response for `ODP-BOL-002` after
`ODP-BOL-001` has cited pilot-scope authority. The current prerequisite status remains
`missing_pilot_scope_authority`, so this packet only gathers the checked
owner-answer template, source-authority record template, candidate evidence checklist,
rights-decision checklist, allowed outcomes, downstream blockers, and no-overclaim
controls.

Run:

```powershell
.\scripts\run_bologna_odp2_owner_answer_packet_check.ps1
```

The checker verifies alignment with:

- `config/bologna_owner_answer_intake.yaml`
- `config/bol_scope_auth.yaml`
- `config/bologna_odp2_source_rights_response_gate.yaml`
- `config/bologna_source_authority_intake.yaml`
- `config/bologna_source_rights.yaml`

The committed state must keep `current_owner_answer_references`,
`current_source_authority_records`, `current_source_authority_record_references`, and
`current_source_rights_approval_references` empty. Every `downstream_updates_allowed`
field remains false.

The candidate checklist covers `comune_bologna_pug_webgis`,
`comune_bologna_open_data_pug_constraints`, `rer_geoportale_dbtr_altimetry`,
`rer_geoportale_catalog_services`, `rer_crs_reference`, `arpae_cartographic_portal`,
and `cadastral_gap`.

The rights checklist covers `terms_reference`, `terms_effective_date`,
`source_version_or_publication_date`, `update_cadence`, `license_status`,
`commercial_use_status`, `redistribution_status`, `cache_allowed`, `export_allowed`,
`raw_data_allowed`, `ai_use_allowed`, `attribution_required`,
`retrieval_metadata_policy`, `source_failure_policy`, `no_data_policy`,
`caveat_policy`, `crs_precision_policy`, `field_allowlist`, `field_denylist`,
`fixture_capture_policy`, and `report_use_policy`.

A future owner response may choose `approve_with_cited_authority`, `keep_blocked`,
`approve_review_only`, or `exclude_or_defer`. None of those outcomes authorizes source
approval, source-rights mutation, recorded corpus work, fixture capture, DB mutation,
report proof, hosted deployment, or Level 10 claims in this packet.

If the owner supplies complete cited source authority and rights after ODP-BOL-001
authority exists, record it only in a later dedicated recording slice that updates the
owner-answer intake, source-authority intake, and source-rights matrix together with
focused validation.
