# Owner Decisions

This file records explicit owner decisions that affect qualification state. It is a
repo-local authority ledger, not an agent inference log.

## 2026-06-22 QFREEZE-1 Qualification Freeze

owner=benjmcd
authority=owner directive 2026-06-22
rationale=conservative defaults matching operational reality
reversal=requires a new owner decision + full requalification

Provenance: owner authorization was delivered to the workspace handoff for this
QFREEZE-1 lane on 2026-06-22. This record preserves the decision inside the branch so
the freeze does not depend on a dirty-root or stale worktree inbox file.

Authorized fields:

| Field path | Authorized value | Disposition |
|---|---|---|
| `scope.product_scope_profile` | `BOUNDED_USER_VALIDATED` | FROZEN_TARGET |
| `scope.deployment_profile` | `LOCAL_SINGLE_USER` | FROZEN_TARGET |
| `scope.windows_native_required` | `true` | FROZEN_TARGET |
| `scope.source_profile_ids` | [`DS-002`] | APPROVED_SOURCE_PROFILE |
| `scope.report_contract_version` | `report_run_contract_v1` | FROZEN_TARGET |
| `scope.api_contract_version` | `0.1.0` | FROZEN_TARGET |
| `scope.ruleset_versions.homestead_mvp_v0_1` | `0.1` | FROZEN_TARGET |
| `scope.normalization_schema_version` | `0.1.0-alpha` | FROZEN_TARGET |
| `scope.geometry_pipeline_version` | `0.1.0-alpha` | FROZEN_TARGET |
| `scope.source_snapshot_policy` | `HASHED_RETRIEVAL_MANIFEST_PER_SOURCE` | FROZEN_TARGET |
| `scope.data_as_of_policy` | `SOURCE_DATA_AS_OF_AND_RETRIEVAL_TIMESTAMP_WITH_FRESHNESS_CAVEATS` | FROZEN_TARGET |
| `windows_native.long_path_policy` | `ENABLED` | FROZEN_TARGET |
| `windows_native.supported_windows_versions` | `["Windows 11 (>=22H2)"]` | FROZEN_TARGET |
| `windows_native.supported_powershell_versions` | `["5.1", "7.x"]` | FROZEN_TARGET |
| `windows_native.supported_python_versions` | `["3.12"]` | FROZEN_TARGET |
| `windows_native.supported_docker_desktop_versions` | `["4.x"]` | FROZEN_TARGET |
| `criterion_bindings.W-003` | frozen | FROZEN_TARGET |
| `criterion_bindings.W-011` | frozen | FROZEN_TARGET |

Explicit exclusions:
- no P0 `PASS`;
- no domain-profile rubric freeze;
- no DQ/Q1/Q2/M threshold freeze;
- no criterion-contract pass-rule freeze;
- no judgment-rubric freeze;
- no source approvals beyond DS-002;
- no DS-017 approval;
- no Bologna AOI/source authority;
- no fixture capture;
- no DB seed;
- no report/API/UI/runtime proof;
- no hosted authority.
