# Source Manifest — Buncombe County, NC

**State:** North Carolina  
**County:** Buncombe  
**Private MVP representative stress case:** Mountain terrain / slope / elevation / floodplain / private-road access ambiguity

---

## Official data portals

| Domain | Authority | Portal / URL |
|---|---|---|
| GIS / Parcels | Buncombe County GIS | https://www.buncombenc.gov/225/Geographical-Information-Systems-GIS |
| Parcel downloads | Buncombe County | Available via county GIS portal; shapefile/GeoJSON formats |
| Assessor / tax | NC Department of Revenue + Buncombe County Tax Dept | https://www.buncombenc.gov/168/Tax-Administration |
| Flood | FEMA NFHL (DS-002) | https://msc.fema.gov/portal/home |
| Zoning | Buncombe County Planning and Development | https://www.buncombenc.gov/219/Planning-and-Development |
| Soils | USDA NRCS SSURGO (DS-003) | https://websoilsurvey.nrcs.usda.gov/ |

---

## Source stance by domain

### Flood (DS-002)
- **Queryability class:** fixture-backed (StaticFloodFixtureConnector) for private MVP regression
- **Source authority:** FEMA National Flood Hazard Layer — public official, approved-with-restrictions
- **Report caveat:** Mapped flood data for Buncombe County, NC reflects the current FEMA Effective NFHL map. Mapped flood zone indicates modeled flood risk, not surveyed ground truth. Requires confirmation by a licensed surveyor or flood-plain manager before any construction, lending, or insurance decision.

### Access (road / right-of-way)
- **Queryability class:** fixture-backed (StaticAccessFixtureConnector) for private MVP regression
- **Source authority:** OSM / county road layer — open community data; not authoritative for legal access
- **Known caveats:** Private road access in mountain areas requires deed/easement verification. Mapped road data indicates probable access routes; does not confirm legal access rights, recorded easements, or road-maintenance obligations. Requires confirmation by a title search and licensed surveyor.
- **Report caveat:** Mapped road data for Buncombe County, NC indicates probable access routes. Road presence on a map does not confirm legal access, right-of-way, easement, or maintenance obligation. Requires confirmation by a title professional and licensed surveyor.

### Zoning (DS-023)
- **Queryability class:** out of current DS-023 selected-county recorded-fixture scope; Buncombe zoning remains NOT_EVALUATED unless separately supplied and reviewed
- **Source authority:** Buncombe County Planning and Development zoning GIS layer
- **Private MVP stance:** No Buncombe DS-023 recorded-fixture UDO lookup or live PDF connector is currently claimed. Chatham and Brunswick recorded-fixture zoning are the only DS-023 selected-county connector-ready paths.
- **Known caveats:** Zoning classifications change through local ordinance; source date matters. Mapped zoning indicates the official classification at the time of data retrieval; does not confirm zoning entitlements, variances, conditional uses, or development-permit status.
- **Report caveat:** Buncombe County zoning is not evaluated by the current selected-county DS-023 source path. Any zoning classification, entitlement, overlay, variance, or permit status requires confirmation by the Buncombe County Planning and Development office.

### Parcels / cadastral (DS-010)
- **Queryability class:** selected-county live connector for immediate operator API and request-time orchestration; fixture regression cases without parcel evidence still record NOT_EVALUATED
- **Source authority:** Buncombe County GIS parcel layer - local official; download available
- **Private MVP stance:** DS-010 is connector-ready for Buncombe County parcel screening only. No owner/value/title fields are exposed; durable live-job support and counties outside Buncombe/Chatham/Brunswick are not claimed.
- **Known caveats:** Parcel boundaries are approximate; not survey-grade. Does not confirm legal boundary, easements, or title.
- **Report caveat:** Buncombe County parcel screening data, when present, is approximate and not survey-grade. It does not confirm legal boundary, easements, title, ownership, value, or buildability; confirm with county records, a title professional, and a licensed surveyor. If parcel evidence is absent for a fixture case, the report must surface an explicit NOT_EVALUATED unknown.

### Assessor / tax (DS-011)
- **Queryability class:** AssessorNotEvaluatedConnector sentinel for immediate operator API and request-time orchestration; no live assessor portal query
- **Source authority:** Buncombe County Tax Administration - local official
- **Private MVP stance:** DS-011 records explicit ASSESSOR_NOT_EVALUATED source-failure evidence. No owner, assessed value, sale-history, appraisal, or lending-suitability data is asserted.
- **Known caveats:** Assessed value is not market value. Schema and access vary; requires county-specific API or data feed.
- **Report caveat:** Assessor and tax data for Buncombe County, NC is not evaluated by the current private-MVP pipeline. Tax records, owner information, assessed value, and sale history require confirmation by the Buncombe County Tax Administration office and must not be inferred from the sentinel.

### Commercial parcel vendor (DS-017)
- **Queryability class:** blocked / not required for private MVP
- **Private MVP stance:** DS-017 (commercial parcel vendor) is blocked due to license/cost. Not required for private MVP utility proof; public/official county sources and NOT_EVALUATED sentinels are sufficient.

---

## Terrain and elevation notes

Buncombe County contains significant mountain terrain (Blue Ridge / Black Mountain range). Elevation variation is material for:
- Flood risk (mountain floodplains behave differently than piedmont/coastal)
- Road access (steep grades, seasonal closures)
- Septic feasibility (slope affects drainfield suitability)
- Site buildability (engineering-level slope analysis required; not in scope for private MVP)

Mapped terrain data indicates approximate elevation contours. Does not constitute engineering, geotechnical, or site-plan analysis. Requires confirmation by a licensed engineer.

---

## Forbidden report language

No report for Buncombe County AOIs may assert:
- legal access or right-of-way
- legal parcel boundary or survey-grade dimensions
- zoning entitlement or permit-ready status
- septic suitability
- wetland jurisdictional determination
- buildability or development feasibility
- property value, appraisal, or investment suitability
