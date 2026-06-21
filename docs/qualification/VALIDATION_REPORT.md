# Validation Report — Empirical Qualification Framework v3

**Generated:** 2026-06-21  
**Framework version:** 3.0

## Overall result

```text
Standalone-bundle structural validation: PASS
Canonical-repo structural validation: PASS
Qualification-validator adversarial self-test: PASS in both layouts
JSON/YAML/schema consistency: PASS
Windows PowerShell execution in this build environment: BLOCKED
Project-specific qualification readiness: BLOCKED
Highest evidence-supported example classification: L9-R
```

`BLOCKED` does not mean the framework failed. It means project-specific targets, exact source rights, domain profiles, reviewers, candidate identity, and empirical results have not been invented merely to obtain a pass.

## Mechanical validation

| Check | Result | Evidence |
|---|---|---|
| Required core paths present | PASS | 33/33 |
| Standalone bundle files | PASS | 45 files |
| Repo-patch files | PASS | 46 files |
| Framework criterion IDs unique | PASS | 392 unique IDs |
| Framework/catalog ID parity | PASS | Zero missing; zero extra |
| Framework/catalog digest | PASS | SHA-256 matches |
| Criterion contract validation | PASS | 392 contracts |
| JSON Schema meta-validation | PASS | 11 schemas |
| YAML parse validation | PASS | 18 YAML files |
| Bundle-layout control validation | PASS | Return code 0 |
| Repo-layout control validation | PASS | Return code 0 |
| Bundle-layout adversarial self-test | PASS | 8/8 cases |
| Repo-layout adversarial self-test | PASS | 8/8 cases |
| Duplicate criterion IDs | PASS | None |
| Stale v2 counts or “all Q3 required for production” wording | PASS | No detected stale patterns |
| PowerShell wrapper execution | BLOCKED | PowerShell unavailable in this Linux build environment |
| Actual Windows/OneDrive path qualification | NOT_RUN | Must run on a supported Windows machine |
| Product empirical qualification | BLOCKED | P0/Q1/Q2 and applicable overlays have not been executed |

## Bundle validator result

```text
qualification structural validation: PASS
layout: bundle
framework criteria: 392
target status: DRAFT
highest valid classification: L9-R
BLOCKED-READINESS: 8 qualified-domain profiles remain DRAFT
BLOCKED-READINESS: no source_profile_ids are frozen in the target scope
BLOCKED-READINESS: 6 scope/version fields remain unresolved
BLOCKED-READINESS: ruleset_versions remain unresolved
BLOCKED-READINESS: qualification targets are DRAFT
BLOCKED-READINESS: 96 criterion contracts remain DRAFT
BLOCKED-READINESS: 19 judgment rubrics remain DRAFT
```

## Repo-layout validator result

```text
qualification structural validation: PASS
layout: repo
framework criteria: 392
target status: DRAFT
highest valid classification: L9-R
BLOCKED-READINESS: 8 qualified-domain profiles remain DRAFT
BLOCKED-READINESS: no source_profile_ids are frozen in the target scope
BLOCKED-READINESS: 6 scope/version fields remain unresolved
BLOCKED-READINESS: ruleset_versions remain unresolved
BLOCKED-READINESS: qualification targets are DRAFT
BLOCKED-READINESS: 96 criterion contracts remain DRAFT
BLOCKED-READINESS: 19 judgment rubrics remain DRAFT
```

## Adversarial self-test result

```text
PASS: baseline DRAFT validates structurally
PASS: classification cannot outrun gate status
PASS: conditional applicability/status mismatch is rejected
PASS: framework/catalog criterion drift is rejected
PASS: frozen target registry cannot retain unresolved active bindings
PASS: applicable invariant cannot be marked N/A
PASS: incomplete gate result cannot be labeled PASS
PASS: P0 cannot pass with draft targets/contracts/missing evidence
qualification validator self-test: PASS
```

The self-test proves that the control plane rejects:

1. classification outrunning gate status;
2. conditional-capability/status inconsistency;
3. framework/catalog drift;
4. a frozen target registry with unresolved active bindings;
5. `N/A` on an applicable invariant;
6. an incomplete gate result labeled `PASS`;
7. P0 passing with draft targets/contracts/missing evidence.

It also proves that a structurally valid DRAFT configuration is accepted without being misrepresented as qualification readiness.

## Current active blockers

For the selected `BOUNDED_USER_VALIDATED` + `LOCAL_SINGLE_USER` profile:

```text
active gates: 12
active DRAFT criterion contracts: 60
active DRAFT/unresolved target bindings: 51
active DRAFT judgment rubrics: 16
qualified-domain profiles still DRAFT: 8
approved selected source profiles: 0
unresolved scope/version fields: 6 plus ruleset versions
```

Conditional gates that do not currently block the selected scope:

```text
CG  candidate generation/ranking: disabled
FIN financial/valuation/investment output: disabled
AI  decision-relevant AI/LLM: disabled
E   commercial/economic-viability claim: disabled
Q3A/Q3B/Q3C expansion claims: not selected
O/F production operation and field surveillance: not required for the current L9-R state
```

## Required Windows proof

From the intended repository root:

```powershell
python .\scripts\validate_qualification.py --root . --layout repo
python .\scripts\selftest_qualification_validator.py
```

Then execute the W overlay against the actual supported Windows matrix, including:

- a path containing spaces and Unicode;
- configured long-path behavior;
- CRLF/LF and encoding controls;
- case-insensitive path behavior;
- Docker Desktop/PostgreSQL/PostGIS workflows;
- file-lock and atomic-write behavior;
- OneDrive-safe separation of source checkout from database/object-store/cache/secrets/job state;
- Windows CI.

## Release interpretation

This report proves that the framework and its machine-readable controls are internally coherent enough to integrate and instantiate.

It does **not** prove:

- real-parcel screening accuracy;
- user decision utility;
- source-license approval;
- production operation;
- accessibility or security conformance;
- candidate-generation quality;
- financial/valuation quality;
- a new jurisdiction;
- nationwide or worldwide coverage.

Those remain explicit gates rather than assumptions.
