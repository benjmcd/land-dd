# 13 Assumptions, Ambiguities, Blockers, and Decision Gates

Generated: 2026-05-28

## 1. Strategic assumptions

| ID | Assumption | Confidence | Consequence if wrong |
|---|---|---|---|
| A-001 | U.S. rural land/homestead is the best MVP wedge | medium | may need pivot to developer/enterprise |
| A-002 | 3-5 counties are enough to validate willingness to pay | high | if not, expand before automating |
| A-003 | Postgres/PostGIS can support MVP and early scale | high | if not, introduce specialized stores later |
| A-004 | Commercial parcel data will be needed | high | public-only product may be too weak |
| A-005 | Human review is required in beta | high | if not, automation can scale faster |
| A-006 | Users value red flags/unknowns more than pretty map layers | medium/high | if false, product becomes map/data subscription |
| A-007 | Global expansion should be tiered | high | legal-grade global promise would be unsafe |

## 2. Ambiguities

| ID | Ambiguity | Resolution path |
|---|---|---|
| AMB-001 | first state/county selection | score candidate geographies using MVP selection matrix |
| AMB-002 | exact target buyer | interview land buyers, brokers, investors separately |
| AMB-003 | source provider strategy | compare public+vendor costs and rights |
| AMB-004 | acceptable report price | test concierge pricing |
| AMB-005 | human review depth | measure QA time and error rate |
| AMB-006 | zoning automation feasibility | prototype in target counties |
| AMB-007 | whether to include market comps in v1 | depends on license and buyer demand |
| AMB-008 | whether to provide PDF in v1 | Markdown/web report first; PDF after template stabilizes |
| AMB-009 | whether batch screening is v1 | not until single-parcel quality is proven |
| AMB-010 | global roadmap timing | only after repeatable U.S. expansion pattern |

## 3. Blockers

| ID | Blocker | Severity | Required action |
|---|---|---:|---|
| BLK-001 | parcel/ownership data licensing | critical | vendor/license audit |
| BLK-002 | local zoning fragmentation | critical | county-scoped adapter + human QA |
| BLK-003 | legal access/easement uncertainty | critical | title verification task; do not assert access |
| BLK-004 | water rights/well uncertainty | high | separate water module; cautious wording |
| BLK-005 | wetland/flood regulatory limits | high | caveats and professional verification |
| BLK-006 | false precision in scoring | high | confidence separate from suitability |
| BLK-007 | underpriced reports | high | per-report cost instrumentation |
| BLK-008 | protected-class/steering risk | high | no demographic scoring |
| BLK-009 | AVM/valuation risk | high | no mortgage valuation |
| BLK-010 | global legal data availability | high | tiered global strategy |

## 4. Decision gates

| Gate | Decision | Required evidence |
|---|---|---|
| DG-001 | choose first geography | selection matrix + source audit |
| DG-002 | choose parcel data source | license/cost/coverage comparison |
| DG-003 | approve schema | DDL review + test load |
| DG-004 | approve MVP ruleset | golden parcel regression tests |
| DG-005 | approve report language | legal/compliance review |
| DG-006 | approve beta pricing | measured cost + customer feedback |
| DG-007 | approve public beta | source stability + QA metrics |
| DG-008 | approve second state | repeatability proven |
| DG-009 | approve global Tier 0 | U.S. architecture stable |
