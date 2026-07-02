# Bologna ODP-BOL-004 DB Report Proof Response Gate

Schema: `bologna_odp4_db_report_proof_response_gate_v1`

This runbook is validate-only. It does not record report-proof authority, record owner
authority, approve DB report proof, seed the database, create a DB report run, create
runtime/report artifacts, change API surfaces, change report semantics, approve DS-017,
or claim hosted/Level 10 authority.

Use this gate only to check that a future owner response for `ODP-BOL-004` is complete
enough to be recorded in a later authority slice. The current committed state must keep
`ODP-BOL-001` pilot-scope authority missing after the review-only scope-pursuit answer
and keep `ODP-BOL-002` and `ODP-BOL-003` missing, `current_owner_answer_references`,
`current_report_proof_authority_references`, `current_db_report_run_references`, and
`current_report_artifact_references` empty. Every `downstream_updates_allowed` value
must remain false.

Run:

```powershell
.\scripts\run_bologna_odp4_db_report_proof_response_gate_check.ps1
```

The gate aligns the owner response with these required report-proof fields from
`config/bologna_owner_answer_intake.yaml`:

- `one_local_db_report_run_id`
- `approved_corpus_reference`
- `evidence_ledger_rows`
- `claim_evidence_links`
- `unknowns_list`
- `caveats_list`
- `artifact_manifest`
- `source_lineage`
- `report_use_policy`
- `no_overclaim_review`
- `storage_export_boundaries`

It also aligns required report-run contract fields with `schemas/report_run_schema.json`:

- `report_run_id`
- `workspace_id`
- `requested_by`
- `area_id`
- `intent_code`
- `idempotency_key`
- `status`
- `review_status`
- `reviewed_by`
- `reviewed_at`
- `review_actions`
- `source_manifest`
- `assumptions`
- `caveats`
- `evidence`
- `claims`
- `unknowns`
- `red_flags`
- `advisory_claims`
- `verification_tasks`
- `artifact_metadata`
- `started_at`
- `finished_at`
- `output_uri`

Required evidence contract fields from `schemas/evidence_schema.json`:

- `evidence_id`
- `area_id`
- `evidence_type`
- `evidence_code`
- `domain`
- `observation`
- `observed_value`
- `source_id`
- `dataset_version_id`
- `source_ingest_run_id`
- `method_code`
- `method_version`
- `confidence`
- `caveat`
- `is_negative_evidence`
- `is_source_failure`
- `superseded_by`
- `source_date`
- `observed_at`
- `geometry_geojson`
- `geometry_srid`
- `spatial_precision_meters`

Required claim contract fields from `schemas/claim_schema.json`:

- `claim_id`
- `area_id`
- `claim_code`
- `domain`
- `assertion`
- `user_safe_language`
- `severity`
- `confidence`
- `evidence_ids`
- `rule_code`
- `ruleset_id`
- `ruleset_version`
- `verification_required`
- `verification_task`

A future owner response may choose `approve_with_cited_authority`, `keep_blocked`,
`approve_review_only`, or `exclude_or_defer`. None of those outcomes authorizes report
proof authority recording, DB seed, DB report run, report artifact creation, API surface
changes, report semantics changes, hosted deployment, or Level 10 claims in this gate.
