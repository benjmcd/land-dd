# Lane C ADR: Rules and Claim Persistence

## Status

Accepted

## Context

Level 6 requires deterministic evidence-to-claim behavior, versioned rules, evidence links, separate severity and confidence, unknown/source-failure handling, contradiction handling, and verification tasks. The current ruleset is a fixture-backed MVP ruleset, not a production jurisdictional rulepack.

The database already has durable claim tables: `claims.claims`, `claims.claim_evidence`, and `claims.verification_tasks`.

## Decision

Use deterministic Python rule evaluation backed by the checked-in ruleset file for the current vertical slice.

- Rule output must cite stored evidence IDs.
- Rule metadata (`rule_code`, `ruleset_id`, `ruleset_version`) is preserved on generated claims.
- Claims persist through `claims.claims`; evidence links persist through `claims.claim_evidence`.
- Verification tasks persist through `claims.verification_tasks` when a claim requires professional or local confirmation.
- Severity and confidence remain separate fields.
- Source failures produce unknown/blocker claims instead of being treated as safe or absent.
- Contradictory active evidence produces needs-review claims where implemented.
- Suitability scoring remains deferred; the current ruleset declares scoring weights, but the current implementation emits hard-gate claims, unknowns, red flags, caveats, and verification tasks rather than a final suitability score.

## Consequences

- Claims are reproducible from stored evidence plus rule version metadata.
- A later rulepack can replace or extend the current hard-gate implementation, but must preserve evidence links, rule versioning, and safe-language constraints.
- Missing rule categories must either be implemented with fixture-backed tests or clearly labeled as not evaluated in report/API output before Level 6/7 can be claimed as complete.
- Production rulepacks need jurisdiction and intent readiness review before live use.

## Links

- `MILESTONE_MAP.md` Level 6
- `config/ruleset_homestead_mvp.yaml`
- `backend/app/claims_engine/rule_engine.py`
- `backend/app/claims_engine/claim_repo.py`
- `backend/tests/claims_engine/`
