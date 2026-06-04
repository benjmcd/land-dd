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
