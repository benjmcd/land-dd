# Production Authority Packet

## Goal
Create the decision/evidence packet needed before the project can move from
selected-county private MVP and local release-candidate proof toward hosted,
multi-geography production. The packet should preserve Level 9/10 authority context
while turning external blockers into explicit decisions, required evidence fields,
owner questions, and acceptable unblock criteria, with DS-017 source authority handled
first.

## Non-goals
- No hosted infrastructure, DNS, TLS, registry publication, billing, alerting, or pager
  setup.
- No DS-017 connector implementation or vendor-data ingestion.
- No OAuth/OIDC, user-account tables, full org RBAC, or entitlement implementation.
- No secret writes, secret-manager provisioning, or production credential handling.
- No new geography, source, rulepack, API contract, schema, or report semantics.

## Current state
- `state/POST_RC_AUTHORITY_SPLIT.md` classifies remaining gaps into external blockers,
  repo-local candidates, and audit-only evidence candidates.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the gate-level authority for why these
  blockers cannot be promoted from local selected-county proof.
- Must-source readiness is still `sources=8 ready=7 blocked=1`; DS-017 is blocked.
- `config/hosted_deployment.yaml`, `config/access_control.yaml`,
  `config/image_publication.yaml`, `config/ops_alert_rules.yaml`, and
  `config/ops_cost_monitoring.yaml` are validate-only catalogs, not external proof.
- Private-MVP selected-county proof and lineage smoke are complete but do not prove
  hosted deployment, paid-vendor entitlement, full identity/RBAC, or production SLOs.

## Proposed design
Add a concise authority packet under `state/` that can be handed to a human/product or
infrastructure owner. It should list each blocker, the exact decision required, the
evidence that would unblock repo work, and the repo lane that becomes available after
the decision. DS-017 should be the first section because it is the only Must-source
readiness blocker and has legal, export, entitlement, and cost consequences.

## Bottom-up sequence
1. Extract blocker fields from source-readiness, hosted-deployment, access-control,
   release-readiness, alerting, cost, and image-publication catalogs.
2. Draft the authority packet with DS-017 first, then hosted platform/secrets/identity,
   image publication, billing, alerting, and production workload proof.
3. Cross-check the packet against `state/POST_RC_AUTHORITY_SPLIT.md` and
   `state/LEVEL_9_10_GATE_MATRIX.md` to avoid contradiction.
4. Validate catalog/checker consistency and record exact results.

## Files likely to change
| File | Expected change |
|---|---|
| `state/PRODUCTION_AUTHORITY_PACKET.md` | New decision/evidence packet. |
| `state/PROJECT_STATE.md` | Record active packet target and boundaries. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and result. |
| `tasks/task_queue.yaml` | Mark this task active/done as appropriate. |
| `plans/README.md` | Route active plan if this becomes active. |

## Tests / verification
```powershell
python .\scripts\source_readiness.py --priority Must --json
python .\scripts\private_mvp_readiness_check.py
python .\scripts\release_readiness_check.py
python .\scripts\hosted_deployment_check.py
python .\scripts\access_control_check.py
python .\scripts\readiness_matrix_check.py
python .\scripts\data_retention_check.py
git diff --check
git diff --name-only --diff-filter=D
```

Run `.\scripts\verify.ps1` before handoff if executable contracts change.

## Risks and blockers
- The packet may identify blockers that cannot be resolved without user or external
  platform input; record them without marking the goal blocked unless the strict
  repeated-blocker threshold is met.
- Do not approve DS-017, hosted deployment, full identity/RBAC, or billing by inference.
- Do not commit generated evidence artifacts, secrets, vendor data, screenshots, DB dumps,
  or local runtime outputs.

## Decision log
- 2026-06-18: Selected this as the next active lane after `R-010` because the remaining
  high-leverage work depends on external source, hosted, identity, secret-manager,
  billing, alerting, and production-workload authority.

## Progress log
- 2026-06-18: Plan opened after post-RC authority split.
- 2026-06-18: Routed as the active plan after `R-010`; initial validators for source
  readiness, private-MVP readiness, release readiness, hosted deployment, access
  control, readiness matrix, data retention, diff hygiene, and default verification
  passed.
