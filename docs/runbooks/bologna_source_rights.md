# Bologna Source Rights Runbook

## Purpose

Use `config/bologna_source_rights.yaml` (`bologna_source_rights_v1`) as the
validate-only rights matrix for future Bologna recorded-source candidates. It converts
candidate discovery into exact review fields for source terms, provenance, source
schema, caveats, fixture capture, runtime use, and report use.

Run from the repository root:

```powershell
.\scripts\run_bologna_source_rights_check.ps1
```

The check is validate-only. It does not approve sources, fetch datasets, call live
connectors, seed the database, generate artifacts, change source readiness, select a
Bologna AOI, or promote source registry rows.

## Boundary

Every candidate remains pending and blocked until a separate source review supplies:

- exact source or layer selection;
- source owner and version/date;
- reviewed terms reference and effective date;
- license, commercial use, redistribution, cache, export, raw-data, AI-use, and
  attribution decisions;
- retrieval metadata, source-failure, no-data, caveat, CRS, field allowlist, and field
  denylist policies;
- fixture capture and report-use decisions.

A passing check means only that the rights matrix is internally consistent and aligned
with `config/bologna_source_candidates.yaml` and `schemas/source_schema.json`. It is not
legal review, source approval, cadastral authority, fixture authority, runtime
authority, or hosted production authority.

## Promotion Sequence

Before any candidate can become a source registry row or recorded-source fixture:

1. Authorize one Bologna AOI and stop conditions.
2. Select exact source documents, layers, or datasets from the candidate catalog.
3. Complete each rights decision in this matrix.
4. Fill every required `SourceContract` field from `schemas/source_schema.json`.
5. Write a source review and source registry row for the promoted source.
6. Define recorded fixture scope, retrieval metadata, checksum/storage policy, CRS, and
   source-failure/no-data fixtures.
7. Decide evidence-only versus rulepack scope before report semantics are implemented.

Cadastral cartography remains a direct official-source review gap. Do not use it for
parcel geometry, owner, title, legal access, buildability, or report conclusions until
the gap is separately reviewed and explicitly approved.
