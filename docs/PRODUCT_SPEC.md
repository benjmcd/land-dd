# Product Spec

## Product concept

An intent-aware due-diligence compiler for land and locality decisions.

Input:
```text
Area: parcel, polygon, locality, corridor, assemblage, or generated candidate region
Intent: homestead, rural land purchase, farmland, development, conservation, resources, infrastructure, investment
Constraints: optional budget, acreage, slope, water, access, zoning, hazard, market, and infrastructure filters
```

Output:
```text
Dossier: source-linked evidence, interpreted claims, red flags, unknowns, confidence, caveats, and verification tasks
```

## MVP

```text
Rural Land Dossier
Geography: 3-5 counties in one selected U.S. state
Intent: rural land purchase / homestead feasibility
Input: parcel ID, address, or drawn polygon
Output: web/API report run with source-linked evidence and cautious claims
```

## MVP report sections

- Parcel/area identity
- Source inventory and missing-source warnings
- Access proxy and legal-access caveat
- Buildability proxy: slope, flood, wetlands, soils/septic indicators
- Water context: wells/groundwater/surface water/drought as available
- Zoning/use: source-linked extraction where available; no final legal conclusion
- Environmental hazards: EPA-regulated facilities and other approved source layers
- Red flags and unknowns
- Verification plan: county planning, title, survey, septic/perc, well/water, wetlands, insurance

## Non-goals for v1

- final legal access determination
- title/easement verification
- surveyed boundary determination
- wetland jurisdictional delineation
- appraisal/AVM output
- lending/insurance eligibility output
- investment advice
- demographic/protected-class/neighborhood desirability scoring
- live paid vendor integration
- global legal-grade parcel diligence

## Differentiator

The differentiator is not more layers. It is: evidence-graded, intent-specific claim resolution with explicit unknowns, contradictions, and verification tasks.

## Product risk language

Use:
```text
Available sources suggest...
Mapped data indicates...
No source was available to determine...
This requires confirmation by...
```

Avoid:
```text
You can build here.
This parcel has legal access.
This property has water rights.
This is a good investment.
This land is safe.
This property is worth X.
```
