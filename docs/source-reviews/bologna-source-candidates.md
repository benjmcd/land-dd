# Bologna Source Candidates Review

## Status

- Review type: candidate inventory only
- Date opened: 2026-06-20
- Review status: pending
- Production use allowed: no
- Fixture corpus allowed: no
- Source registry promotion allowed: no

This review records candidate discovery surfaces for a future Bologna recorded-source
pilot. It is not a license review and does not approve any source for cache,
redistribution, export, AI use, raw-data handling, fixture capture, runtime use, or
report use.

## Candidate Surfaces

| Candidate | Organization | Candidate role | Current status |
|---|---|---|---|
| `comune_bologna_pug_webgis` | Comune di Bologna | Municipal PUG/webGIS planning context | Pending effective-document and terms review |
| `comune_bologna_open_data_pug_constraints` | Comune di Bologna | PUG-derived open-data constraint datasets | Pending exact dataset and per-dataset license review |
| `rer_geoportale_dbtr_altimetry` | Regione Emilia-Romagna | Regional topographic/elevation context | Pending layer metadata, attribution, CRS, and precision review |
| `rer_geoportale_catalog_services` | Regione Emilia-Romagna | Official regional geodata discovery root | Pending exact layer selection |
| `rer_crs_reference` | Regione Emilia-Romagna | CRS/reference-system policy | Pending CRS policy mapping |
| `arpae_cartographic_portal` | ARPAE Emilia-Romagna | Environmental map/metadata discovery root | Pending exact layer and terms review |

## Unresolved Rights Questions

Every selected source still needs answers for:

- source owner and effective version/date;
- license or terms URL/effective date;
- cache, redistribution, export, AI-use, raw-data, and attribution decisions;
- update cadence and stale-source policy;
- retrieval metadata and checksum/storage policy;
- CRS, geometry precision, and transformation policy;
- caveat language and no-overclaim review;
- source-failure, no-data, ambiguity, stale-data, and license-block behavior.

## Known Gaps

- No Bologna AOI has been authorized.
- No candidate is promoted into `registers/data_source_registry.csv`.
- No recorded-source fixture corpus exists.
- Italian cadastral cartography needs direct official-source review before it can be
  treated as a candidate source.
- No EU/Italy rulepack or evidence-only scope decision exists.

## Production Decision

Not approved. This packet only prepares the next source-rights review pass.
