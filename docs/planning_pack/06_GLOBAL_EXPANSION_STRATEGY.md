# 06 Global Expansion Strategy

Generated: 2026-05-28

## 1. Strategic position

The architecture should be global-ready, but the product should not promise worldwide legal-grade diligence.

## 2. Global tiers

### Tier 0: physical/environmental screening

Available in many countries with global datasets:
- elevation/slope
- satellite imagery/land cover
- roads/buildings from open sources
- hydrography/watershed context
- protected areas
- global soil estimates
- water-risk indices
- population/infrastructure proximity
- climate/hazard context

Output: regional/physical suitability screen, not purchase-grade legal diligence.

### Tier 1: country-level administrative screen

Adds:
- country administrative boundaries
- land tenure regime overview
- national cadastre availability
- planning/zoning framework
- protected lands and environmental restrictions
- public lands/resource concessions where available

Output: country/locality-level diligence context and legal-data availability assessment.

### Tier 2: parcel/legal diligence

Requires:
- cadastre/parcel registry
- ownership/rights/restrictions/responsibilities
- local zoning/planning
- tax/assessment
- title/easement analogs
- water/mineral/resource rights
- local professional verification network

Output: purchase-grade screening dossier, still not legal advice.

## 3. Jurisdiction adapter model

Core remains stable:

```text
Area
Source
DatasetVersion
Evidence
Claim
Ruleset
ReportRun
VerificationTask
```

Adapter varies:
- parcel/cadastre identifiers
- land tenure categories
- zoning/planning categories
- administrative hierarchy
- water/mineral rights regime
- address system
- source authority hierarchy
- legal caveats
- language/translation rules
- privacy restrictions
- data licensing

## 4. Global architecture requirements

1. No U.S.-only assumptions in core IDs.
2. All areas can be arbitrary polygons.
3. Legal concepts represented as jurisdiction-specific claim types.
4. Rule engines can load country/state/county modules.
5. Source authority levels are configurable.
6. Multi-language source documents can be stored and cited.
7. Units normalize but original values preserved.
8. CRS transforms are explicit and tested.
9. Data-license restrictions enforced per geography.
10. Reports state the diligence tier clearly.

## 5. Global blockers

| Blocker | Effect |
|---|---|
| cadastre access | parcel/legal diligence may be impossible or expensive |
| privacy laws | owner data may be restricted |
| language/legal interpretation | zoning/planning extraction complexity |
| land tenure differences | freehold/leasehold/customary/public systems vary |
| source authority | "official" may not mean accessible, current, or legally determinative |
| commercial use rights | global protected-area/resource datasets may restrict commercial use |
| professional verification | local survey/legal/environmental experts needed |

## 6. Expansion sequence

1. US MVP in 3-5 counties.
2. Add more counties in same state.
3. Add second state with different legal/data regime.
4. Create public-data-only national U.S. screening.
5. Add commercial parcel/zoning/comps coverage.
6. Add Canada or another high-data-quality country.
7. Add global Tier 0 screening.
8. Add country-specific Tier 1 adapters.
9. Add Tier 2 parcel diligence only where legal/source coverage supports it.
