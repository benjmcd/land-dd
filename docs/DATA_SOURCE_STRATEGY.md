# Data Source Strategy

## Principle

Data sources are not truth. They are evidence inputs with authority, freshness, licensing, coverage, precision, and caveats.

## Source classes

| Class | Examples | MVP use |
|---|---|---|
| Public national baseline | USGS, FEMA, USFWS, USDA, EPA, BLM | good first-pass screening |
| Commercial national | parcels, ownership, comps, zoning normalization, hazard models | evaluate after MVP economics/license review |
| Local/jurisdictional | county GIS, assessor, recorder, zoning, permits, septic, wells, water rights | needed for useful diligence in chosen geography |
| Global baseline | OSM/Overture, Sentinel/Landsat, global elevation/soil/water/protected-area datasets | later Tier 0 screening only |

## Connector policy

Every connector must have:

- source registry entry;
- license/terms review file;
- fixture data;
- tests for success and failure cases;
- source freshness/caveat mapping;
- explicit no-data/source-unavailable evidence behavior.

## Live connector gate

A connector may not hit a live API or vendor until:

1. legal/license status is recorded;
2. caching/export/AI-use constraints are recorded;
3. fixture-backed behavior passes;
4. rate limits/failure modes are implemented;
5. user/API output caveats are defined.

## U.S. MVP source baseline

Start with source registry entries and fixtures for:

- USGS The National Map / elevation/topography/hydrography context
- FEMA NFHL flood hazard screening
- USFWS National Wetlands Inventory screening
- USDA/NRCS soils/septic proxy
- USGS Water Data context
- EPA ECHO regulated-facility context
- BLM MLRS/mineral/land-record context where relevant
- county GIS/assessor/zoning for selected MVP counties

## Global expansion tiers

| Tier | Capability | Constraint |
|---|---|---|
| Tier 0 | physical/environmental screening | not purchase-grade legal diligence |
| Tier 1 | national administrative/regulatory screen | country-specific caveats |
| Tier 2 | parcel/legal diligence | jurisdiction-by-jurisdiction adapters and data agreements |
