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
- Bologna recorded-source authority: `config/bologna_source_authority_intake.yaml`

## Boundary

Every stream remains `blocked`, every `authority_references` list remains empty, and
every `decision_updates_allowed` value remains false until the matching external
authority evidence exists and the stream-specific checker validates it.
