# 03 Data Source and Ingestion Spec

Generated: 2026-05-28

## 1. Data strategy

The system needs data, but data volume is not the product. The product requires source-linked evidence that can support or reject decision-critical claims.

## 2. Source tiers

### Tier A: public U.S. baseline data

| Domain | Seed source | MVP role | Caveat |
|---|---|---|---|
| Terrain/topography | USGS The National Map | elevation, hydrography, boundaries, land cover, transportation | physical screening only |
| Flood | FEMA NFHL | floodplain/flood hazard intersection | modernized map coverage and effective-date limitations |
| Soils | USDA NRCS Web Soil Survey / SSURGO | soil/septic/farmland proxy | not a substitute for site test |
| Wetlands | USFWS National Wetlands Inventory | wetland/deepwater screening | not a jurisdictional wetland determination |
| Water monitoring | USGS Water Data APIs | streamflow, groundwater, water-quality context | monitor proximity may be weak proxy |
| Environmental compliance | EPA ECHO | regulated facilities, permits, violations, enforcement | facility data does not prove contamination on subject parcel |
| Mineral/public land | BLM MLRS, USGS MRDS/USMIN | mining claims, mineral occurrence screening | rights/severance and stale data risks |
| Zoning baseline | National Zoning Atlas where available | normalized reference where present | incomplete coverage |

### Tier B: commercial normalized data

Likely required for credible national/pro product:
- parcels/boundaries
- ownership/assessor
- sales/comps
- zoning normalization
- forward-looking hazards/climate
- listings
- imagery/building footprints

### Tier C: local/jurisdiction-specific data

Usually the highest-value and highest-friction class:
- county assessor
- county recorder
- county GIS
- planning/zoning department
- septic/permitting office
- state well logs
- state water-rights records
- road maintenance authority
- conservation easement records
- local tax delinquency records
- HOA/covenants/deed restrictions where obtainable

### Tier D: global baseline data

Future global screening, not legal diligence:
- Sentinel/Landsat imagery
- OSM/Overture base layers
- global elevation
- global soils estimates
- WRI Aqueduct water-risk screen
- HydroSHEDS
- WDPA/protected areas
- global climate grids

## 3. Ingestion principles

1. Every source has a registry record before ingestion.
2. Every dataset version has a source date, retrieval date, checksum, and storage URI.
3. Raw source data is immutable.
4. Normalized tables never erase source attributes; keep source JSON.
5. Failed ingest runs are stored.
6. Data-license terms are machine-readable enough to control display/export.
7. Every derived metric records method code and version.
8. Every source must have an authority/freshness/caveat rating.
9. Commercial data must be isolated by entitlement.
10. No production source without a license review.

## 4. Connector model

Each connector should implement:

```text
discover()
fetch()
validate_raw()
archive_raw()
normalize()
load()
qa()
publish_version()
```

## 5. Source metadata requirements

Minimum fields:
- name
- organization
- domain
- geographic scope
- authority level
- source URL
- update cadence
- license summary
- cache allowed
- commercial use allowed
- export allowed
- attribution required
- AI use allowed
- legal caveat
- source freshness policy
- known limitations

## 6. Source quality dimensions

| Dimension | Description |
|---|---|
| authority | official primary, official secondary, commercial normalized, open community, model-derived |
| freshness | age relative to expected cadence |
| completeness | geography/fields present |
| precision | spatial and attribute precision |
| legal relevance | whether source has legal/regulatory authority |
| reproducibility | whether old versions can be retained |
| license freedom | cache/display/export/derived report rights |
| verification burden | professional or agency follow-up needed |

## 7. MVP source priority

### Must-have

1. Parcel geometry and parcel ID
2. Assessor/tax basics
3. FEMA flood overlay
4. USFWS NWI overlay
5. USDA soils/SSURGO or Web Soil Survey data
6. USGS elevation/slope
7. road/access proxy
8. zoning district + ordinance text where feasible
9. EPA ECHO regulated facility proximity
10. water/well context

### Should-have

1. wildfire hazard if relevant to geography
2. local well logs
3. public land/BLM context
4. local permit records
5. county planning documents
6. market comps/listings

### Later

1. water rights
2. mineral rights
3. title/easements
4. deed restrictions/covenants
5. insurance availability
6. forward-looking climate risk
7. utility serviceability

## 8. Data blockers

| Blocker | Impact | Required response |
|---|---|---|
| parcel licensing unclear | cannot ship reports or exports safely | license audit before beta |
| zoning source fragmented | claims may be wrong | start in few counties, human QA |
| legal access unavailable | core land-risk unresolved | phrase as unknown; title verification task |
| water rights unavailable | western-state feasibility risk | separate water-rights module later |
| mineral rights severed | mineral opportunity/liability uncertain | only screen occurrences/claims, never assert rights |
| wetlands source not jurisdictional | permitting risk | caveat + field delineation task |
| source outages | false "nothing found" risk | first-class source-failure evidence |
| API rate limits | production instability | bulk ingestion/cache/self-host where permitted |
| commercial-use constraints | product constraint | entitlement and report-display rules |

## 9. Data QA

### Ingest QA

- row count comparison
- geometry validity
- CRS validation
- null critical field check
- duplicate ID check
- spatial extent sanity check
- source date extraction
- checksum verification
- schema drift detection

### Feature QA

- overlay result bounds check
- area intersection cannot exceed parcel area
- nearest distance must be non-negative
- slope percentiles within plausible range
- no projection mismatch warnings
- generated geometry is valid
- method version included

### Report QA

- every claim has evidence
- every critical/high claim has verification task
- every missing source appears as unknown/source failure
- no prohibited wording
- no demographic steering
- no hidden data-license violation
