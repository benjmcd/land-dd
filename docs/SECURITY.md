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

Do not recommend, rank, score, or steer residential areas. Do not use
protected-class, demographic, school-quality, neighborhood-quality,
safety-by-demographic, lending, insurance, appraisal, market desirability, or
residential-steering proxy features.

## Data licensing

Unknown license means blocked for live/commercial use. Record cache/export/AI-use/attribution status before integrating.

## External access

Default agent network access is off. Enable only with approval and task-specific justification.
