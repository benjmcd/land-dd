# Security, Legal, and Compliance Guardrails

## Secrets

- Never commit secrets, API keys, credentials, private keys, `.env`, or paid-vendor data dumps.
- `.env.example` is allowed.
- Live connectors require explicit approval and license review.

## Product-claim restrictions

The system may not produce final determinations for:

- legal access;
- title/easements;
- surveyed boundaries;
- water rights;
- wetland jurisdiction;
- buildability/permitting;
- appraisal/property value;
- lending/insurance eligibility;
- investment quality.

It may produce source-linked screening observations and verification tasks.

## Residential/fair-housing guardrail

Do not create protected-class, demographic, neighborhood desirability, safety-by-demographic, school-by-demographic, or steering features. Residential area recommendations must avoid proxies that could function as steering.

## Data licensing

Unknown license means blocked for live/commercial use. Record cache/export/AI-use/attribution status before integrating.

## External access

Default agent network access is off. Enable only with approval and task-specific justification.

## Request Identity Boundary

- Area, evidence, report, connector-run, and connector review queue API routes
  support two explicit identity modes:
  - `REPORT_AUTH_MODE=trusted_headers`: local/dev or trusted-gateway mode. The
    backend requires `X-Workspace-Id` and `X-User-Id` headers. Area creation
    binds stored owner fields to those headers, evidence reads are limited to
    areas in the authenticated workspace, and report routes reject
    body/query/reviewer mismatches.
  - `REPORT_AUTH_MODE=signed_token`: beta deployment mode. The backend requires
    an `Authorization: Bearer ...` report identity token signed with
    `REPORT_IDENTITY_TOKEN_SECRET`; token claims are the workspace/user
    authority. The secret must be at least 32 characters, and tokens must carry
    an expiration.
- In signed-token mode, optional `X-Workspace-Id` and `X-User-Id` headers may be
  supplied by a gateway/operator only when they match the bearer token claims.
  Mismatches fail closed.
- Report creation, report-job submission, and fixture connector runs also
  verify that the requested or fixture-referenced `area_id` belongs to the
  authenticated workspace before creating durable report, evidence, provenance,
  or review queue work.
- Connector review queue rows are stored and listed by workspace. Review queue
  actions require `reviewer_id` to match the authenticated user.
- Source registry routes remain governance/admin scaffolding, not public
  multi-tenant product APIs.
- Operators can mint short-lived local/beta tokens with
  `scripts/mint_report_token.py`; do not expose that script as a public token
  issuance API.
- External identity-provider/session integration may later mint or replace these
  signed report identity tokens, but untrusted exposed deployments should not run
  in `trusted_headers` mode.
