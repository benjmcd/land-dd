# 04 Evidence, Claims, Rules, and Scoring Spec

Generated: 2026-05-28

## 1. Conceptual split

The product should store four things separately:

1. **Source record**: where a fact came from.
2. **Evidence**: an observed datum or failed lookup.
3. **Claim**: an interpreted assertion derived from evidence.
4. **Score/band**: a purpose-specific synthesis of claims.

Do not collapse these into one map-layer result.

## 2. Evidence object

Minimum fields:
- evidence_id
- area_id
- source_id / dataset_version_id
- evidence_type
- domain
- observation
- observed_value
- method_code
- method_version
- source_date
- retrieved_at
- authority_level
- confidence
- caveat
- geometry if applicable
- is_negative_evidence
- is_source_failure
- metadata

Examples:
- parcel intersects 0.42 acres of mapped NWI wetland
- no road adjacency found within 20m using source X
- zoning text extraction found "minimum lot area"
- EPA ECHO source unavailable at run time

## 3. Claim object

Minimum fields:
- claim_id
- area_id
- intent
- claim_code
- domain
- assertion
- severity
- confidence
- user_safe_language
- evidence_ids
- contradictions
- verification_required
- verification_task
- created_by_rule_version

## 4. Hard gates before scoring

The rules engine should evaluate disqualifying or high-risk gates before weighted scoring.

| Code | Gate | Fail condition |
|---|---|---|
| ACCESS_G001 | legal/physical access risk | no apparent public road adjacency or access source unavailable |
| ZONING_G001 | intended use not clearly compatible | zoning prohibits or cannot determine residential/homestead use |
| FLOOD_G001 | flood conflict | material intersection with high-risk flood zone |
| WETLAND_G001 | wetland conflict | material mapped wetland/deepwater intersection |
| SLOPE_G001 | buildability | insufficient low-slope area |
| SOIL_G001 | septic/soil constraint | severe septic limitation proxy |
| WATER_G001 | water path unclear | no plausible well/water context and no alternative water strategy |
| ENV_G001 | nearby environmental compliance concern | regulated facility/known site within threshold |
| TITLE_G001 | unverified title/easement | title/easement data unavailable |

Hard gates do not always mean "do not buy." They mean "do not proceed without verification/price adjustment."

## 5. Red-flag taxonomy

### Access

- `ACCESS_001`: parcel appears landlocked or no road adjacency found
- `ACCESS_002`: road appears private/unmaintained
- `ACCESS_003`: physical access detected but legal access unknown
- `ACCESS_004`: seasonal/topographic access risk

### Flood/wetlands

- `FLOOD_001`: intersects high-risk flood zone
- `FLOOD_002`: flood source unavailable
- `WETLAND_001`: intersects mapped wetland/deepwater feature
- `WETLAND_002`: wetland source indicates uncertainty or outdated mapping

### Buildability

- `SLOPE_001`: steep slope reduces usable area
- `SLOPE_002`: no contiguous buildable envelope found
- `SOIL_001`: severe septic limitation proxy
- `SOIL_002`: poor drainage/erosion/foundation proxy

### Water

- `WATER_001`: no nearby well logs/groundwater evidence found
- `WATER_002`: drought/water-stress context elevated
- `WATER_003`: water-rights source unavailable
- `WATER_004`: surface water presence does not imply legal right

### Zoning/legal

- `ZONING_001`: intended use not clearly permitted
- `ZONING_002`: minimum lot size conflict
- `ZONING_003`: overlay district requires special review
- `ZONING_004`: zoning text source stale/unavailable
- `TITLE_001`: easements/covenants/title restrictions unavailable

### Environmental/resource

- `ENV_001`: EPA-regulated facility within buffer
- `ENV_002`: known remediation/contamination context nearby
- `MINERAL_001`: mineral occurrence/claim screen positive; rights unknown
- `MINERAL_002`: mineral source stale or incomplete

### Market/financial

- `MARKET_001`: price/acre outlier
- `MARKET_002`: low comparable-sales support
- `TAX_001`: tax/assessment anomaly
- `LIQUIDITY_001`: weak resale/transaction signal

## 6. Confidence scoring

Confidence is not suitability.

Inputs:
- source authority
- source freshness
- spatial precision
- consistency between sources
- directness of observation vs proxy
- missing data
- human verification

Bands:
- very_high: current official source + direct observation + no conflict
- high: strong source + reproducible method + no major gaps
- medium: usable screening evidence but verification needed
- low: proxy, stale, incomplete, or conflicting
- very_low: weak/uncertain evidence only
- unknown: source unavailable or not evaluated

## 7. Suitability scoring

Use intent-specific scoring only after hard gates.

Homestead MVP weights:
- Buildability: 20%
- Access: 20%
- Water: 15%
- Zoning/legal: 15%
- Flood/wetlands: 10%
- Soil/septic: 10%
- Environmental hazards: 5%
- Market/context: 5%

Output bands:
- Strong candidate
- Potential candidate
- High-risk candidate
- Insufficient information
- Not compatible based on available evidence

## 8. Contradiction handling

A contradiction exists when two evidence items support materially different interpretations.

Examples:
- parcel vendor boundary differs from county GIS
- zoning vendor says residential allowed; county ordinance text suggests special use permit
- road layer shows access; title/easement data unavailable
- tax acreage differs from GIS acreage materially

Requirements:
- create contradiction group
- identify domains affected
- downgrade confidence
- list verification task
- never hide contradiction behind a final score

## 9. Safe language rules

Forbidden:
- "You can build here."
- "This parcel has legal access."
- "This land has water rights."
- "This property is safe."
- "This property is worth $X."
- "No environmental problems exist."

Allowed:
- "Available sources suggest..."
- "Mapped data indicates..."
- "No source was found for..."
- "This requires verification by..."
- "This is a screening result, not a survey/title/legal determination."

## 10. Ruleset governance

Rulesets must be versioned, reviewable, testable, tied to intent, tied to jurisdiction where needed, immutable after report publication, and explainable in the report.
