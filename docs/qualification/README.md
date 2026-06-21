# Empirical Qualification Framework v3

This bundle is the adversarially revised qualification system for `land-dd`.

It does not declare the product qualified. It supplies the control plane needed to make future qualification claims binary, scoped, reproducible, and invalidatable.

## Current result

```text
Framework structural validation: PASS
Qualification-validator adversarial self-test: PASS
Framework criteria: 392
Current target status: DRAFT
Highest evidence-supported example classification: L9-R
Project-specific qualification readiness: BLOCKED
```

The example remains blocked because targets, criterion contracts, judgment rubrics, domain profiles, source profiles, scope versions, candidate identity, reviewers, and empirical evidence have not yet been frozen.

## Principal v3 corrections

- separates implementation maturity, empirical validity, deployment quality, and expansion readiness;
- makes bounded production independent of unrelated global expansion testing;
- adds explicit product-scope and deployment profiles;
- adds dedicated Postgres/PostGIS and AOI/parcel-identity qualification;
- adds Windows-native qualification for the canonical local environment;
- adds conditional candidate-generation/ranking and financial/investment overlays;
- adds document/OCR/table/figure extraction qualification;
- binds exact domain and source profiles to P0;
- adds regulatory/professional-scope and post-release surveillance gates;
- converts pass/fail rules into schemas, criterion contracts, status records, and executable validation;
- permits `N/A` only through scoped, evidenced, approved, expiring inapplicability;
- keeps disabled capabilities from becoming unnecessary release blockers.

## Qualification axes

```text
Implementation maturity
  MILESTONE_MAP.md

Bounded empirical validity
  P0 + Q1 + Q2 as applicable

Deployment quality
  DQ + IR + DB + S + A + M + O + R + F + W + G
  with E / CG / FIN / AI only when activated

Expansion readiness
  Q3A cross-state
  Q3B restricted/unavailable source
  Q3C non-US representation
```

A successful Q3 probe is not jurisdictional operational qualification. A bounded production release does not require Q3 unless it makes an expansion claim.

## Bundle files

```text
README.md
EMPIRICAL_QUALIFICATION_FRAMEWORK.md
ADVERSARIAL_REVIEW_FINDINGS.md
FRAMEWORK_ADEQUACY_GATES.md
PROJECT_PARAMETERIZATION_BLOCKERS.md
MILESTONE_QUALIFICATION_MAPPING.md
VALIDATION_REPORT.md
ARTIFACT_MANIFEST.json

qualification_profiles.yaml
qualification_vocabulary.yaml
qualification_targets.example.yaml
empirical_qualification_status.example.yaml
judgment_rubrics.example.yaml
qualification_result.example.json
criterion_catalog.yaml
change_impact_matrix.yaml

criterion_contract.schema.json
criterion_catalog.schema.json
qualification_result.schema.json
qualification_targets.schema.json
empirical_qualification_status.schema.json
qualification_profiles.schema.json
qualification_vocabulary.schema.json
change_impact_matrix.schema.json
judgment_rubrics.schema.json
domain_qualification_profile.schema.json
source_quality_profile.schema.json

domain_profiles/*.yaml
source_profiles/*.yaml

scripts/validate_qualification.py
scripts/validate_qualification.ps1
scripts/validate_qualification.cmd
scripts/selftest_qualification_validator.py
scripts/selftest_qualification_validator.ps1
scripts/selftest_qualification_validator.cmd
```

## Recommended repo placement

```text
docs/qualification/EMPIRICAL_QUALIFICATION_FRAMEWORK.md
docs/qualification/ADVERSARIAL_REVIEW_FINDINGS.md
docs/qualification/FRAMEWORK_ADEQUACY_GATES.md
docs/qualification/PROJECT_PARAMETERIZATION_BLOCKERS.md
docs/qualification/MILESTONE_QUALIFICATION_MAPPING.md
docs/qualification/VALIDATION_REPORT.md
docs/qualification/ARTIFACT_MANIFEST.json
MILESTONE_QUALIFICATION_MAPPING.md

config/qualification/qualification_profiles.yaml
config/qualification/qualification_vocabulary.yaml
config/qualification/qualification_targets.yaml
config/qualification/judgment_rubrics.yaml
config/qualification/criterion_catalog.yaml
config/qualification/change_impact_matrix.yaml
config/qualification/domain_profiles/
config/qualification/source_profiles/

schemas/qualification/*.json
state/EMPIRICAL_QUALIFICATION_STATUS.yaml

scripts/validate_qualification.py
scripts/validate_qualification.ps1
scripts/validate_qualification.cmd
scripts/selftest_qualification_validator.py
scripts/selftest_qualification_validator.ps1
scripts/selftest_qualification_validator.cmd
```

The detailed framework and evidence packages should not be loaded automatically into every agent session. `AGENTS.md` and the concise current-state file should contain only the classification, active gate, blockers, and links.

## Windows-native validation

From PowerShell, after adapting paths to the repo placement:

```powershell
python .\scripts\validate_qualification.py `
  --root . `
  --layout repo
```

Run the control-plane adversarial smoke test:

```powershell
python .\scripts\selftest_qualification_validator.py
```

The validator auto-detects the canonical repo layout above. The standalone example bundle can be checked with:

```powershell
.\scripts\validate_qualification.ps1
```

## Integration barriers

Before replacing the current framework in the repo:

1. Apply the repo-structured patch on a branch.
2. Reconcile `MANIFEST.md`, `MILESTONE_MAP.md`, and current state with the new classifications.
3. Add qualification validation and its self-test to canonical PowerShell verification and CI.
4. Convert example target/status/rubric files into canonical files.
5. Freeze only the bounded scope actually intended for the next empirical run.
6. Complete the active blockers in `PROJECT_PARAMETERIZATION_BLOCKERS.md`.
7. Do not unseal Q1 cases until P0 passes.
8. Do not enable CG, FIN, or AI merely to satisfy future architecture ambitions.
9. Do not claim production grade from static configuration; hosted/local operational drills must pass for the selected deployment profile.
10. Do not claim a new jurisdiction from Q3 alone; qualify that jurisdiction separately.

## Correct interpretation

```text
A structurally adequate framework may coexist with a blocked product qualification.
A high test count is not empirical validation.
A global-ready architecture claim is not worldwide operational coverage.
An omitted or unresolved required value is BLOCKED, not passed.
A disabled capability is not required, but enabling it activates its complete gate.
```
