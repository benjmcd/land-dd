# Bologna Recorded-Source Corpus Contract

`bologna_recorded_source_corpus_v1` is a validate-only contract for the future Bologna
recorded-source fixture corpus. It defines the manifest evidence that must exist after
authority is granted, while keeping the current corpus blocked.

This does not select a Bologna AOI, approve sources, change source rights, promote
source registry rows, capture fixtures, create source-failure fixtures, run
connectors, mutate the database, create runtime artifacts, change source readiness,
approve report use, approve hosted production, or claim Level 10 authority.

## Use

Run:

```powershell
.\scripts\run_bologna_recorded_source_corpus_check.ps1
```

The checker cross-checks `config/bologna_recorded_source_corpus.yaml` against
`config/bologna_source_authority_intake.yaml`, `config/bologna_source_rights.yaml`,
and `config/bologna_preflight.yaml`. Every candidate corpus row must match the
authority-intake evidence slots and remain blocked until the intake and rights matrix
are completed from cited authority.

## Corpus Boundary

A future recorded-source manifest must include source versions, retrieval metadata,
fixture file manifests, source-failure fixture manifests, attribution text, CRS and
precision policy, field allow/deny lists, no-data policy, caveats, report-use policy,
review owner, and no-overclaim review.

Until product/AOI/source-review authority exists, every `corpus_state` remains blocked,
every fixture manifest entry remains disallowed, and every source-failure fixture
remains disallowed.
