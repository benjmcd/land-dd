# Bologna Source Candidates Runbook

## Purpose

Use `config/bologna_source_candidates.yaml` (`bologna_source_candidates_v1`) as the
validate-only candidate inventory for a future Bologna recorded-source pilot. It
records official candidate discovery surfaces and known gaps; it does not approve
sources, create source registry rows, commit recorded fixtures, or allow report/runtime
use.

Run from the repository root:

```powershell
.\scripts\run_bologna_source_candidates_check.ps1
```

The check is validate-only. It does not fetch official datasets, call live connectors,
seed the database, generate artifacts, change source readiness, or select a Bologna
AOI.

It does not approve sources.

## Boundary

This packet is candidate-only. Every candidate must remain:

- `approval_status: not_approved`
- `source_registry_promoted: false`
- `allowed_for_runtime: false`
- `allowed_for_fixture_corpus: false`

A passing check means only that the candidate packet is structurally current and fail
closed. It is not source approval, legal review, rulepack approval, cadastral authority,
hosted authority, or report proof.

## Candidate Domains

The packet currently records candidate surfaces for:

- municipal planning/PUG context;
- municipal open-data PUG-derived datasets;
- regional topographic/elevation context;
- regional geodata catalog and service discovery;
- CRS/reference-system policy;
- environmental map/metadata discovery.

Italian cadastral cartography remains a direct source-review gap. It must not be
treated as parcel, owner, title, legal access, or buildability authority without a
separate official-source terms review and pilot scope decision.

## Promotion Sequence

Before any candidate can be used for a recorded-source fixture or report:

1. Authorize exactly one Bologna AOI and stop conditions.
2. Select exact source layers/documents/datasets from the candidate surfaces.
3. Review source owner, version/date, license terms, cache, redistribution, export, AI
   use, raw-data handling, attribution, update cadence, and caveats.
4. Decide CRS/geometry precision and transformation policy.
5. Decide whether the pilot is evidence-only, a constrained locality dossier, or a new
   rulepack.
6. Commit recorded fixtures with retrieval metadata and source-failure/no-data fixtures.
7. Prove one DB-backed report with evidence, unknowns/claims, caveats, artifact
   persistence, and lineage.

Do not promote a candidate into `registers/data_source_registry.csv` until the source
review can answer the source-schema rights fields without pending or inferred values.
