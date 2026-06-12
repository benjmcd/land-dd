# Source Manifest — Chatham County, NC

**State:** North Carolina  
**County:** Chatham  
**Private MVP representative stress cases:** Rural/agricultural land use; zoning edge / unzoned / jurisdiction boundary; parcel/tax/easement ambiguity

---

## Official data portals

| Domain | Authority | Portal / URL |
|---|---|---|
| GIS / Open data | Chatham County GIS | https://chathamncgis.maps.arcgis.com/ |
| Parcel / CAMA | Chatham County | Available via county open data portal; CAMA parcel data downloadable |
| Assessor / tax | Chatham County Tax Administration | https://www.chathamcountync.gov/government/departments-g-z/tax |
| Flood | FEMA NFHL (DS-002) | https://msc.fema.gov/portal/home |
| Zoning | Chatham County Planning | https://www.chathamcountync.gov/government/departments-a-f/development-services/planning |
| Soils | USDA NRCS SSURGO (DS-003) | https://websoilsurvey.nrcs.usda.gov/ |

---

## Source stance by domain

### Flood (DS-002)
- **Queryability class:** fixture-backed (StaticFloodFixtureConnector) for private MVP regression
- **Source authority:** FEMA National Flood Hazard Layer — public official, approved-with-restrictions
- **Report caveat:** Mapped flood data for Chatham County, NC reflects the current FEMA Effective NFHL map. Mapped flood zone indicates modeled flood risk, not surveyed ground truth. Requires confirmation by a licensed surveyor or flood-plain manager before any construction, lending, or insurance decision.

### Access (road / right-of-way)
- **Queryability class:** fixture-backed (StaticAccessFixtureConnector) for private MVP regression
- **Source authority:** OSM / county road layer — open community data; not authoritative for legal access
- **Known caveats:** Rural road access in Chatham County may include unpaved, private, or shared roads. Mapped road data indicates probable access routes; does not confirm legal access rights, recorded easements, or road-maintenance obligations. Requires confirmation by a title search and licensed surveyor.
- **Report caveat:** Mapped road data for Chatham County, NC indicates probable access routes. Road presence on a map does not confirm legal access, right-of-way, easement, or maintenance obligation. Requires confirmation by a title professional and licensed surveyor.

### Zoning (DS-023)
- **Queryability class:** fixture-backed for regression and selected-county recorded-fixture UDO district lookup for immediate operator API and request-time orchestration
- **Source authority:** Chatham County Planning zoning GIS layer
- **Private MVP stance:** DS-023 is connector-ready for Chatham County recorded-fixture UDO district lookup only. It is not live PDF ingestion, autonomous amendment tracking, final legal zoning interpretation, or raw PDF redistribution.
- **Known caveats:** Portions of Chatham County may be unzoned or subject to a zoning jurisdiction edge between the county and incorporated municipalities. Source date matters; zoning classifications change through local ordinance.
- **Private MVP note:** Zoning/unzoned edge cases are a stress test for this county. The fixture/recorded connector uses representative mapped zoning data; unzoned parcels produce a sentinel claim.
- **Report caveat:** Chatham County zoning screening indicates a recorded/mapped classification when evidence is present. It does not confirm zoning entitlement, permitted use, variance status, overlay applicability, or permit-ready status; confirm with Chatham County Planning.

### Parcels / cadastral (DS-010)
- **Queryability class:** selected-county live connector for immediate operator API and request-time orchestration; fixture utility cases include parcel evidence, and fixture cases without parcel evidence still record NOT_EVALUATED
- **Source authority:** Chatham County GIS CAMA parcel layer - local official; download available via open data portal
- **Private MVP stance:** DS-010 is connector-ready for Chatham County parcel screening only. No owner/value/title fields are exposed; durable live-job support and counties outside Buncombe/Chatham/Brunswick are not claimed.
- **Known caveats:** Parcel boundaries are approximate; not survey-grade. Parcel/tax/easement ambiguity is a key stress scenario for Chatham County.
- **Report caveat:** Chatham County parcel screening data, when present, is approximate and not survey-grade. It does not confirm legal boundary, easements, title, ownership, value, or buildability; confirm with county records, a title professional, and a licensed surveyor. If parcel evidence is absent for a fixture case, the report must surface an explicit NOT_EVALUATED unknown.

### Assessor / tax (DS-011)
- **Queryability class:** AssessorNotEvaluatedConnector sentinel for immediate operator API and request-time orchestration; no live assessor portal query
- **Source authority:** Chatham County Tax Administration - local official
- **Private MVP stance:** DS-011 records explicit ASSESSOR_NOT_EVALUATED source-failure evidence. No owner, assessed value, sale-history, appraisal, or lending-suitability data is asserted.
- **Known caveats:** Tax schema and access vary; requires county-specific API or data feed. Easements and deed restrictions are not captured by assessor data alone.
- **Report caveat:** Assessor and tax data for Chatham County, NC is not evaluated by the current private-MVP pipeline. Tax records, owner information, assessed value, sale history, and easements require confirmation by Chatham County Tax Administration, Register of Deeds, and qualified professionals.

### Commercial parcel vendor (DS-017)
- **Queryability class:** blocked / not required for private MVP
- **Private MVP stance:** DS-017 (commercial parcel vendor) is blocked due to license/cost. Not required for private MVP utility proof; public/official county sources and NOT_EVALUATED sentinels are sufficient.

---

## Rural/agricultural land-use notes

Chatham County contains significant agricultural and rural land use, including:
- Farm parcels with multiple agriculture-related overlays
- Areas with limited or partial zoning coverage
- Shared or unpaved rural road access

Mapped data indicates land-use classification and road access patterns. Does not constitute professional agricultural assessment, legal access determination, or land-use entitlement verification. Requires confirmation by county planning staff and licensed professionals.

---

## Forbidden report language

No report for Chatham County AOIs may assert:
- legal access or right-of-way
- legal parcel boundary or survey-grade dimensions
- zoning entitlement or permit-ready status
- septic suitability
- wetland jurisdictional determination
- buildability or development feasibility
- property value, appraisal, or investment suitability
- good investment or desirable neighborhood
