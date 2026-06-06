# DS-002 FEMA NFHL Source Review

## Source identity

- Source registry ID: DS-002
- Source name: FEMA NFHL
- Organization: FEMA
- URL: https://www.fema.gov/flood-maps/national-flood-hazard-layer
- Domain: Flood
- Geography: United States and territories where effective NFHL data exists
- Source type / authority level: Public official
- MVP priority: Must
- Contact: FEMA Map Service Center / FMIX
- Date reviewed: 2026-06-05
- Review owner: data-governance
- Review status: approved
- Terms/license URL: https://www.usa.gov/government-copyright
- Terms/license version or effective date: checked 2026-06-05
- Evidence file or citation:
  - https://hazards.fema.gov/femaportal/resources/flood_map_svc.htm
  - https://hazards.fema.gov/femaportal/NFHL/searchResult
  - https://www.copyright.gov/title17/
  - https://www.usa.gov/government-copyright

## Rights review

This is a source-governance review for product gating, not legal advice. Treat
NFHL as a FEMA federal source when the retrieved layer is the public FEMA NFHL
effective-data service. Do not infer the same status for state, county, private
basemap, logo, trademark, preliminary, or third-party material.

| Question | Status | Evidence/contract section | Restrictions / notes |
|---|---|---|---|
| Can we cache the data? | yes | Public FEMA NFHL service and federal-work copyright posture | Cache only retrieved source snapshots with retrieval date and FEMA attribution. |
| Can we modify/normalize it? | yes | Public FEMA NFHL service and federal-work copyright posture | Store normalized hazard overlays as derived evidence with caveats. |
| Can we show it in-app? | yes | FEMA public web mapping services | Do not imply FEMA endorsement. Preserve source/date caveats. |
| Can we include it in reports? | yes | FEMA public web mapping services | Reports must say this is flood hazard screening, not a full flood-risk or insurance determination. |
| Can users export reports containing derived data? | yes | Federal-work copyright posture | Export only derived report evidence by default. |
| Can users export raw data? | yes | Public FEMA download/services posture | Gate raw export behind source citation and retrieval metadata. |
| Can we use it in AI extraction/summarization? | yes | Federal-work copyright posture | Summaries must cite FEMA/NFHL and keep limitations visible. |
| Can we retain historical versions? | yes | Source provenance/audit need | Retain retrieval timestamp, endpoint, dataset label, and checksum/manifest when available. |
| Is attribution required? | yes | Product source-provenance policy; USAGov notes agency attribution may apply | Attribute FEMA NFHL in reports and API source manifests. |
| Are there user/seat/geography limits? | no | Public FEMA services | Not identified for public web/download access. |
| Are there API rate/volume limits? | restricted | FEMA WFS note | WFS requests are limited to 1000 features; prefer bounded areas or county/state downloads. |
| Are owner/PII fields restricted? | no | NFHL flood-hazard source scope | NFHL is hazard-layer data, not ownership data. |
| Are there audit obligations? | yes | Project provenance requirements | Store retrieval run, source URL, retrieved_at, and caveats. |

## Provenance and caveats

- Source version/date available: NFHL county/community extracts carry update
  dates; web service retrievals must record retrieved_at and service URL.
- Update cadence or freshness class: reviewed; NFHL updates as new study or
  Letter of Map Change data becomes effective.
- Geographic coverage limits: not all areas have modernized FIRM database data.
- Precision/scale limits: FEMA notes NFHL data and basemaps used for official
  purposes have map-accuracy requirements.
- Known caveats to store with evidence: effective-map limits; not all flood
  risk; not site design, insurance rating, mandatory-purchase, elevation,
  survey, or permitting advice.
- Required attribution text: Source: FEMA National Flood Hazard Layer (NFHL).
- Fields that must not be exposed: none identified for NFHL hazard layers.
- Source failure / no-data behavior: source unavailable, no coverage, and
  non-modernized FIRM coverage must produce explicit unknown/source-failure
  evidence.
- Reviewer notes: Federal-first review unblocks fixture/live-connector planning
  for FEMA NFHL, but it does not settle county geography or local-source rights.

## Connector gate

Do not enable a live connector until every required item is complete or
explicitly waived by ADR.

| Gate | Status | Evidence |
|---|---|---|
| Source registry row exists and matches this review | complete | `registers/data_source_registry.csv` DS-002 |
| License/terms status recorded in source registry | complete | DS-002 row |
| Usage constraints mapped to source fields | complete | DS-002 row and this review |
| Fixture data exists | complete | Static flood fixture connector |
| Success and failure tests exist | fixture-ready | Existing flood fixture tests; live connector tests pending |
| Source freshness/caveats map to evidence/report output | pending | Live connector pass must assert report-visible caveats |
| Rate-limit/failure behavior is defined | pending | Live connector pass must bound WFS/service requests |
| Entitlement or field filtering exists if restricted | not-required | No restricted fields identified for NFHL hazard layers |

## Production decision

- Approved for fixture-only development? yes
- Approved for MVP production use? yes, for FEMA NFHL hazard data only
- Approved for display? yes
- Approved for report export? yes
- Approved for machine JSON/API? yes
- Approved for raw data export? yes
- Approved for AI use? yes
- Restrictions / blocking conditions: no FEMA endorsement; no preliminary or
  pending layer for official conclusions; bounded requests; report caveats must
  stay visible.
- Required attribution: Source: FEMA National Flood Hazard Layer (NFHL).
- Next review date: before live connector enablement, or when FEMA terms/service
  access materially change.
- Decision recorded in source registry? yes
