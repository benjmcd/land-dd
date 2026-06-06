# Cost Monitoring Runbook

## Purpose

Use `config/ops_cost_monitoring.yaml` as the repo-local cost monitoring catalog for Level
10 production hardening. It maps the required cost categories to current evidence,
guardrails, validation, and residual limits.

This runbook does not approve paid vendors, add LLM summaries, add geocoding, add map
tiles, change report semantics, or weaken source-rights review.

## Current Cost Signals

| Category | Current status | Evidence |
|---|---|---|
| Compute | Monitored locally | Report `artifact_metadata.cost_metrics` counts and zero-dollar attribution plus `/metrics` and queue health |
| Storage | Monitored locally | DB smoke, backup/restore proof, object-store retention review, and zero-dollar attribution |
| LLM | Disabled until metered | Planning cost inputs require token and USD cost before use |
| Maps | Disabled until metered | Planning cost inputs require tile/map asset cost before UI/map expansion |
| Geocoding | Disabled until metered | No production geocoding connector is enabled |
| Data vendors | Blocked until reviewed | Source-readiness keeps commercial/vendor sources blocked without rights and cost review |

`cost_metrics` currently records report-shape counts (`evidence_count`, `claim_count`,
`unknown_count`, `red_flag_count`, and `verification_task_count`) and explicit local-only
zero-dollar attribution fields (`estimated_total_usd_cents`, `compute_usd_cents`,
`storage_usd_cents`, `llm_usd_cents`, `map_tile_usd_cents`, `geocoding_usd_cents`,
`paid_data_usd_cents`, `human_review_usd_cents`, and `human_review_minutes`). Current
report generation sets these attribution fields to `0` because the local-only repo has
no billing feature, paid vendor path, LLM path, geocoding path, map-tile path, or
durable reviewer-time workflow enabled.

## Validate Monitoring

Run from the repository root:

```powershell
.\scripts\run_cost_monitoring_check.ps1
```

The check is validate-only. It verifies that:

- all Level 10 cost categories are present in `config/ops_cost_monitoring.yaml`;
- report-run schema still requires non-negative count, USD-cent, and reviewer-minute
  `cost_metrics`;
- planning cost inputs include data, compute, LLM, map, storage, and human-review rows;
- current Must-source readiness keeps unreviewed commercial/vendor sources blocked;
- the operator runbook records current limits and escalation.

## Operator Workflow

1. Inspect `artifact_metadata.cost_metrics` on report runs before pricing or batch-use
   claims. Local-only fixture/report paths must show zero-dollar attribution.
2. Use `/metrics` and `/operations/queue-health` to investigate compute or queue-driven
   cost pressure.
3. Run `scripts/source_readiness.py --priority Must --json` before enabling any data
   vendor or jurisdiction-specific source.
4. Keep LLM, geocoding, interactive map/tile, and paid data-vendor work disabled until
   token/request/vendor cost is recorded per report or per batch in the corresponding
   `*_usd_cents` metric.
5. Do not treat zero-dollar attribution as billing proof. Billing and hosted billing
   reconciliation are out of scope for local-only operation; any future paid or hosted
   scope change needs a new plan before nonzero production usage.
6. Escalate through `docs/runbooks/incident_response.md` if a cost spike threatens
   availability, causes uncontrolled vendor spend, or risks unsupported report output.

## Known Limits

- No billing feature or hosted cloud billing integration is planned for local-only
  operation.
- No production unit-cost thresholds have been approved because first geography, parcel
  vendor, pricing, and batch usage remain undecided.
- `cost_metrics` records zero-dollar attribution for current local-only paths; it does
  not prove billing reconciliation or authorize nonzero spend.
- LLM, map/tile, geocoding, and paid-vendor costs are guardrailed as disabled or blocked,
  not actively metered runtime spend.
- `human_review_minutes` and `human_review_usd_cents` are currently `0` because durable
  reviewer-time capture and approved reviewer rates do not exist yet.
