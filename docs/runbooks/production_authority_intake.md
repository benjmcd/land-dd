# Production Authority Intake

`production_authority_intake_v1` is a validate-only map of the external authority
streams that block hosted, source-entitlement, identity, observability, artifact, DS-017,
and Bologna progress.

It does not approve sources, select vendors, provision hosted infrastructure, publish
images, write secrets, create billing integration, select a Bologna AOI, create runtime
artifacts, or claim Level 10 authority.

## Use

Run:

```powershell
.\scripts\run_production_authority_intake_check.ps1
```

The checker cross-checks `config/production_authority_intake.yaml` against the existing
authority catalogs:

- DS-017 source entitlement: `config/source_entitlements.yaml`
- hosted deployment: `config/hosted_deployment.yaml`
- secrets and identity/RBAC: `config/access_control.yaml`
- image publication: `config/image_publication.yaml`
- billing/cost: `config/ops_cost_monitoring.yaml`
- hosted observability: `config/observability_readiness.yaml`
- Bologna pilot scope authority: `config/bologna_pilot_scope_authority.yaml`
- Bologna recorded-source authority: `config/bologna_source_authority_intake.yaml`

## Boundary

Every stream remains `blocked`, every `authority_references` list remains empty, and
every `decision_updates_allowed` value remains false until the matching external
authority evidence exists and the stream-specific checker validates it.

## Evidence Checklist

Use `config/production_authority_intake.yaml` as the source of truth. The checklist
below is for collecting evidence; it is not approval and does not change any stream
status.

### `ds017_source_entitlement`

Source catalog: `config/source_entitlements.yaml`

Collect:

- `reviewed_terms_or_redacted_contract_reference`
- `vendor_product_or_dataset_name`
- `allowed_geography_and_coverage_statement`
- `source_version_or_effective_date`
- `update_cadence_and_staleness_policy`
- `field_allowlist_and_denylist`
- `cache_ttl_or_no-cache_policy`
- `export_policy`
- `raw_data_retention_policy`
- `ai_use_policy`
- `attribution_policy`
- `entitlement_owner_and_review_owner`
- `per-report_paid_data_cost_policy`
- `connector_scope_and_failure_mode_policy`

### `hosted_platform`

Source catalog: `config/hosted_deployment.yaml`

Collect:

- `hosted_platform_selected`
- `domain_tls_authority`
- `secrets_manager_authority`
- `database_instance_authority`
- `registry_image_digest_available`
- `hosted_billing_reconciliation`
- `hosted_alerting_route`

### `secrets_manager`

Source catalog: `config/access_control.yaml`

Collect:

- `external_secret_manager_reference_names`
- `no_plaintext_committed_secret_values`
- `per_environment_secret_owner`
- `post_rotation_access_control_check`
- `rotation_runbook_or_ticket`

### `identity_rbac`

Source catalog: `config/access_control.yaml`

Collect:

- `subject`
- `email`
- `display_name`
- `workspace_id`
- `user_id`
- `groups_or_roles`

Required roles:

- `operator`
- `platform_admin`
- `read_only`
- `reviewer`
- `workspace_admin`

### `image_publication`

Source catalog: `config/image_publication.yaml`

Collect:

- `registry_repository_authority`
- `hosted_deployment_authority`
- `registry_image_attestation_authority`
- `signed_image_sbom_authority`

Required attestations:

- `image_digest`
- `registry_image_ref`
- `vulnerability_scan`
- `dependency_sbom`
- `provenance`

### `billing_cost`

Source catalog: `config/ops_cost_monitoring.yaml`

Collect:

- `hosted_billing_owner`
- `approved_budget_thresholds`
- `unit_cost_policy`
- `paid_source_metering_policy`
- `vendor_spend_approval`
- `cost_overrun_alert_owner`

Blocked categories:

- `data_vendors`
- `geocoding`
- `llm`
- `maps`

### `hosted_observability`

Source catalog: `config/observability_readiness.yaml`

Collect:

- `hosted_dashboard`
- `hosted_alert_routing`
- `pager_on_call`
- `hosted_log_retention`
- `production_traffic_observability`

### `bologna_pilot_scope`

Source catalog: `config/bologna_pilot_scope_authority.yaml`

Collect:

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

### `bologna_recorded_source`

Source catalog: `config/bologna_source_authority_intake.yaml`

Collect:

- `authorized_one_aoi_scope`
- `exact_source_selection`
- `completed_per_source_rights_review`
- `source_contract_fields_complete`
- `source_registry_row_review`
- `recorded_fixture_scope`
- `crs_precision_policy`
- `rulepack_or_evidence_only_scope`
- `no_overclaim_review`
