# Source Manifest — Brunswick County, NC

**State:** North Carolina  
**County:** Brunswick  
**Private MVP representative stress cases:** Coastal flood / low elevation; wetlands / soils / septic proxy; municipal-vs-county zoning jurisdiction

---

## Official data portals

| Domain | Authority | Portal / URL |
|---|---|---|
| GIS / Open data | Brunswick County GIS | https://www.brunswickcountync.gov/876/GIS-Maps-Data |
| Parcel downloads | Brunswick County | Available via county GIS portal |
| Assessor / tax | Brunswick County Tax Administration | https://www.brunswickcountync.gov/212/Tax |
| Flood | FEMA NFHL (DS-002) | https://msc.fema.gov/portal/home |
| Zoning | Brunswick County Planning | https://www.brunswickcountync.gov/297/Planning |
| Soils | USDA NRCS SSURGO (DS-003) | https://websoilsurvey.nrcs.usda.gov/ |
| Wetlands | USFWS National Wetlands Inventory (DS-004) | https://www.fws.gov/program/national-wetlands-inventory |
| Coastal management | NC Division of Coastal Management | https://www.deq.nc.gov/about/divisions/coastal-management |

---

## Source stance by domain

### Flood (DS-002)
- **Queryability class:** fixture-backed (StaticFloodFixtureConnector) for private MVP regression
- **Source authority:** FEMA National Flood Hazard Layer — public official, approved-with-restrictions
- **Known caveats:** Brunswick County has significant coastal and inland flood exposure. FEMA NFHL effective maps may not reflect post-storm changes or sea-level rise projections. Low-elevation coastal AOIs are a key stress scenario.
- **Report caveat:** Mapped flood data for Brunswick County, NC reflects the current FEMA Effective NFHL map. Coastal AOIs may be subject to additional flood, storm-surge, and sea-level risk not fully captured by effective NFHL maps. Requires confirmation by a licensed surveyor, flood-plain manager, and coastal engineer before any construction, lending, or insurance decision.

### Access (road / right-of-way)
- **Queryability class:** fixture-backed (StaticAccessFixtureConnector) for private MVP regression
- **Source authority:** OSM / county road layer — open community data; not authoritative for legal access
- **Known caveats:** Coastal and low-elevation access routes may include flood-prone roads, tidal areas, or private beach access easements. Mapped road data indicates probable access routes; does not confirm legal access rights, recorded easements, or road-maintenance obligations.
- **Report caveat:** Mapped road data for Brunswick County, NC indicates probable access routes. Coastal access routes may be subject to flood, tidal, or seasonal closures not reflected in mapped data. Requires confirmation by a title professional and licensed surveyor.

### Zoning (DS-023)
- **Queryability class:** fixture-backed (StaticZoningFixtureConnector) for private MVP regression
- **Source authority:** Brunswick County Planning zoning GIS layer; incorporated municipalities (e.g., Southport, Oak Island, Leland) maintain separate zoning jurisdictions
- **Known caveats:** Municipal-vs-county zoning jurisdiction is a key stress scenario for Brunswick County. Incorporated areas are regulated by municipal ordinances, not county zoning. AOIs near municipal boundaries require jurisdiction verification.
- **Private MVP note:** The jurisdiction stress case tests detection of municipal-vs-county zoning boundary ambiguity. The fixture connector uses representative mapped zoning data; boundary-adjacent parcels produce a jurisdiction-ambiguity caveat.
- **Report caveat:** Mapped zoning data for Brunswick County, NC indicates the applicable zoning jurisdiction and classification as of the data retrieval date. AOIs near incorporated municipality boundaries may fall under municipal rather than county zoning jurisdiction. Requires confirmation by the Brunswick County Planning office or the relevant municipal planning department for current zoning status, jurisdiction, and pending amendments.

### Parcels / cadastral (DS-010)
- **Queryability class:** deferred — NOT_EVALUATED for private MVP fixture regression
- **Source authority:** Brunswick County GIS parcel layer — local official; download available via county GIS portal
- **Private MVP stance:** No machine-queryable county parcel connection is wired for private MVP. Parcel geometry and attributes are recorded as NOT_EVALUATED with an explicit unknown in the report.
- **Known caveats:** Coastal parcel boundaries may include tidal or water-adjacent areas requiring survey-grade verification.
- **Report caveat:** Parcel boundary and cadastral data for Brunswick County, NC was not available through the data pipeline for this analysis. Coastal parcel information requires confirmation by the Brunswick County Register of Deeds and a licensed surveyor.

### Assessor / tax (DS-011)
- **Queryability class:** deferred — NOT_EVALUATED for private MVP fixture regression
- **Source authority:** Brunswick County Tax Administration — local official
- **Private MVP stance:** No machine-queryable assessor connection is wired for private MVP. Assessed value, tax year, and situs are recorded as NOT_EVALUATED with an explicit unknown in the report.
- **Known caveats:** Tax schema and access vary; coastal-area properties may have supplemental assessments or coastal management overlay records.
- **Report caveat:** Assessor and tax data for Brunswick County, NC was not available through the data pipeline for this analysis. Tax records require confirmation by the Brunswick County Tax Administration office.

### Commercial parcel vendor (DS-017)
- **Queryability class:** blocked / not required for private MVP
- **Private MVP stance:** DS-017 (commercial parcel vendor) is blocked due to license/cost. Not required for private MVP utility proof; public/official county sources and NOT_EVALUATED sentinels are sufficient.

---

## Coastal area notes (CAMA / AEC)

Brunswick County is subject to the NC Coastal Area Management Act (CAMA). Coastal areas include Areas of Environmental Concern (AECs): ocean beaches, estuarine waters, coastal wetlands, inlet hazard areas, and public trust waters. CAMA permits are required for development within AECs.

Mapped data indicates approximate AEC boundaries and coastal hazard zones. Does not constitute jurisdictional delineation, CAMA permit eligibility determination, or wetland regulatory opinion. Requires confirmation by the NC Division of Coastal Management and a licensed environmental professional.

Soils / wetlands / septic notes: Coastal soils in Brunswick County frequently have high water tables and hydric characteristics. Mapped SSURGO soil data indicates general soil class; does not constitute a site-specific septic evaluation or wetland delineation. Requires confirmation by a licensed soil scientist and environmental professional.

---

## Forbidden report language

No report for Brunswick County AOIs may assert:
- legal access or right-of-way
- legal parcel boundary or survey-grade dimensions
- zoning entitlement or permit-ready status
- septic suitability
- wetland jurisdictional determination or Clean Water Act jurisdiction
- CAMA AEC status or CAMA permit eligibility
- buildability or development feasibility
- property value, appraisal, or investment suitability
