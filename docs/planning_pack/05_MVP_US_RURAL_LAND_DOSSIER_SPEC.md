# 05 MVP Spec: U.S. Rural Land Dossier

Generated: 2026-05-28

## 1. MVP decision

Build the first version as:

> A U.S. rural land / homestead due-diligence dossier for 3-5 counties in one selected state.

Do not start with worldwide coverage. Do not start with enterprise infrastructure siting. Do not start with a generic map viewer.

## 2. Target user

Primary:
- rural land buyer
- homestead buyer
- small land investor
- rural broker doing first-pass diligence

Secondary:
- small developer
- land scout
- conservation buyer
- attorney/title/survey partner workflows later

## 3. Primary user question

"Before I make an offer or spend money on inspections, what are the obvious red flags, unknowns, and verification tasks for this parcel?"

## 4. MVP inputs

- parcel ID/APN
- address
- coordinates
- drawn polygon
- uploaded CSV of candidate parcels
- user intent: rural land purchase or homestead feasibility
- user constraints: acreage, budget, desired use, residence/build intent, water strategy, septic expectation, access tolerance, maximum slope, hazard tolerance

## 5. MVP outputs

### Human-readable dossier

Sections:
1. executive summary
2. top red flags
3. source confidence summary
4. parcel identity
5. access screen
6. buildability screen
7. flood/wetlands screen
8. soil/septic proxy
9. water context
10. zoning/use screen
11. environmental/compliance hazards
12. market context
13. unknowns
14. verification tasks
15. source appendix

### Machine-readable output

JSON:
- area
- intent
- source manifest
- evidence list
- claim list
- risk bands
- confidence bands
- verification tasks
- report metadata

### Map pack

- parcel boundary
- flood overlay
- wetland overlay
- slope visualization
- soils overlay
- road/access proxy
- nearby regulated facilities
- zoning overlay where available

## 6. MVP acceptance criteria

| Area | Acceptance criterion |
|---|---|
| report reproducibility | same inputs/source versions produce same output |
| source lineage | every claim links to evidence/source version |
| unknowns | unavailable data creates explicit unknown/source-failure entries |
| red flags | hard gates are evaluated before scores |
| human review | all beta reports pass human QA |
| cost tracking | each report records data/compute/LLM/human-review costs |
| safe wording | no forbidden legal/title/survey/appraisal claims |
| export | report can be exported to Markdown/PDF later; JSON available from start |
| data rights | all displayed/exported data permitted by license |
| geometry | all parcel/polygon geometries validated and stored in PostGIS |

## 7. MVP state/county selection criteria

| Criterion | Weight |
|---|---:|
| rural land transaction demand | 20 |
| public data availability | 20 |
| zoning/permitting tractability | 15 |
| parcel data quality | 15 |
| water/septic relevance | 10 |
| manageable legal complexity | 10 |
| commercial data cost | 5 |
| founder/customer access | 5 |

Candidate starting regions:
- Tennessee rural counties: buyer demand, less western water-rights complexity, zoning variation
- Arizona/New Mexico counties: strong land/homestead interest, water complexity useful but harder
- Colorado rural counties: high-value diligence, water/mineral/fire complexity, tougher
- Texas counties: huge rural market, limited county zoning in many areas, water/mineral complexity
- North Carolina mountain/rural counties: slope, septic, zoning, access issues

## 8. MVP technical implementation

### Phase 0: manual baseline

- choose 20-30 parcels
- produce manual dossiers
- track source time and failure points
- define red flags
- validate whether users pay or act on output

### Phase 1: storage and source registry

- create Postgres/PostGIS schema
- load source registry
- load parcel geometries for target counties
- load public baseline layers
- store source versions and checksums

### Phase 2: feature extraction

- parcel area/acres
- flood intersection
- wetland intersection
- slope stats
- road adjacency/distance
- soil/septic proxy
- nearest EPA-regulated facilities
- zoning district where available

### Phase 3: evidence and claims

- write evidence observations
- execute MVP ruleset
- generate red flags and unknowns
- create verification tasks
- store report run metadata

### Phase 4: report compiler

- generate Markdown dossier
- generate map assets
- generate JSON output
- add reviewer notes

### Phase 5: private beta

- pay-per-report or concierge workflow
- all reports reviewed
- measure cost and user outcomes
- refine rules and source adapters

## 9. MVP kill criteria

Stop or pivot if:
- users will not pay for manual reports
- parcel/zoning data costs exceed plausible price
- source fragmentation makes target geography uneconomic
- users want pure comps/listings rather than risk diligence
- professional liability risk cannot be controlled
- there is no clear wedge beyond existing parcel-map tools
