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
- **Queryability class:** fixture-backed for regression and selected-county recorded-fixture UDO district lookup for immediate operator API and request-time orchestration
- **Source authority:** Brunswick County Planning zoning GIS layer; incorporated municipalities (e.g., Southport, Oak Island, Leland) maintain separate zoning jurisdictions
- **Private MVP stance:** DS-023 is connector-ready for Brunswick County recorded-fixture UDO district lookup only. It is not live PDF ingestion, autonomous amendment tracking, final legal zoning interpretation, or raw PDF redistribution.
- **Known caveats:** Municipal-vs-county zoning jurisdiction is a key stress scenario for Brunswick County. Incorporated areas are regulated by municipal ordinances, not county zoning. AOIs near municipal boundaries require jurisdiction verification.
- **Private MVP note:** The jurisdiction stress case tests detection of municipal-vs-county zoning boundary ambiguity. The fixture/recorded connector uses representative mapped zoning data; boundary-adjacent parcels produce a jurisdiction-ambiguity caveat.
- **Report caveat:** Brunswick County zoning screening indicates a recorded/mapped jurisdiction and classification when evidence is present. It does not confirm zoning entitlement, permitted use, variance status, overlay applicability, municipal jurisdiction, or permit-ready status; confirm with Brunswick County Planning or the relevant municipal planning department.

### Parcels / cadastral (DS-010)
- **Queryability class:** selected-county live connector for immediate operator API and request-time orchestration; fixture regression cases without parcel evidence still record NOT_EVALUATED
- **Source authority:** Brunswick County GIS parcel layer - local official; download available via county GIS portal
- **Private MVP stance:** DS-010 is connector-ready for Brunswick County parcel screening only. No owner/value/title fields are exposed; durable live-job support and counties outside Buncombe/Chatham/Brunswick are not claimed.
- **Known caveats:** Coastal parcel boundaries may include tidal or water-adjacent areas requiring survey-grade verification.
- **Report caveat:** Brunswick County parcel screening data, when present, is approximate and not survey-grade. It does not confirm legal boundary, easements, title, ownership, value, CAMA status, or buildability; confirm with county records, a title professional, and a licensed surveyor. If parcel evidence is absent for a fixture case, the report must surface an explicit NOT_EVALUATED unknown.

### Assessor / tax (DS-011)
- **Queryability class:** AssessorNotEvaluatedConnector sentinel for immediate operator API and request-time orchestration; no live assessor portal query
- **Source authority:** Brunswick County Tax Administration - local official
- **Private MVP stance:** DS-011 records explicit ASSESSOR_NOT_EVALUATED source-failure evidence. No owner, assessed value, sale-history, appraisal, or lending-suitability data is asserted.
- **Known caveats:** Tax schema and access vary; coastal-area properties may have supplemental assessments or coastal management overlay records.
- **Report caveat:** Assessor and tax data for Brunswick County, NC is not evaluated by the current private-MVP pipeline. Tax records, owner information, assessed value, sale history, and supplemental assessments require confirmation by Brunswick County Tax Administration and qualified professionals.

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
