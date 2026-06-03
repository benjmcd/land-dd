# 07 Financial Constraints and Unit Economics

Generated: 2026-05-28

## 1. Financial thesis

The product can fail financially even if it works technically. The main risk is underpricing reports while paying for commercial data, compute, LLM extraction, map usage, and human QA.

## 2. Cost centers

| Cost center | Severity | Notes |
|---|---:|---|
| parcel/ownership/comps data | very high | likely largest recurring cost for pro/national product |
| zoning normalization | very high | fragmented local codes; human/AI QA |
| human review | high early | necessary for trust and liability control |
| cloud storage/compute | medium/high | rasters, maps, batch jobs, report rendering |
| LLM/document extraction | medium/high | zoning and ordinance parsing; cache aggressively |
| legal/compliance | medium/high | fair housing, valuation, disclaimers, licensing |
| customer support | medium | users will ask parcel-specific questions |
| insurance | medium | professional liability/E&O may be required |
| sales/customer acquisition | unknown/high | depends on B2C vs pro/enterprise wedge |

## 3. Unit economics model

Per report:

```text
gross_margin =
report_price
- data_royalties
- geocoding/map_cost
- compute/storage
- LLM_cost
- human_review_minutes * review_rate
- support_cost
- payment_processing
- liability/compliance allocation
```

Do not launch an unlimited low-price plan before these are measured.

## 4. Pricing hypotheses

### Consumer/concierge

- per report
- limited refreshes
- no raw data export
- human QA included above a price threshold

### Pro

- monthly subscription
- report credits
- batch screening limits
- saved areas
- team workspaces
- no unrestricted data resale

### Enterprise

- negotiated contract
- API
- bulk screening
- custom data layers
- dedicated data-license terms
- audit logs and SLA

## 5. Financial blockers to resolve

| Blocker | Decision needed |
|---|---|
| parcel vendor pricing | before private beta |
| data export rights | before any downloadable reports with vendor data |
| report price floor | before public launch |
| human QA requirement | before margin model |
| map/tile usage costs | before interactive UI launch |
| LLM cost per report | before scaling zoning/document extraction |
| support load | measured during concierge beta |
| legal review cost | before housing/valuation/investment claims expand |

## 6. MVP cost instrumentation

Every report run should store:
- source lookup count
- paid API calls
- LLM tokens/cost
- raster processing time
- worker runtime
- map asset generation cost
- reviewer minutes
- support tickets
- failed-source count
- report price
- gross margin estimate

## 7. Financial acceptance criteria

Proceed from private beta to public beta only if:
- report cost is measured on at least 100 runs
- gross margin is positive after human review at target price
- source costs scale predictably
- no license forbids intended display/export
- users pay without requiring custom consulting every time
- support burden does not erase margin

## 8. Capital requirements

### Low-capital path

- manual reports
- limited counties
- public data + one parcel provider
- no heavy UI initially
- charge per dossier

### Higher-capital path

- national parcel/comps licenses
- full map UI
- batch screening
- zoning/document AI pipeline
- sales team for pro/enterprise

Recommendation: start low-capital. Let paid reports prove which data licenses and automations are justified.
