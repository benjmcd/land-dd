# Jurisdiction Readiness Checklist

## Purpose
Mandatory checklist before adding any new US state or county to the tool's production geography.

## Boundary and administrative hierarchy
- [ ] County/township boundary source identified and registered in data_source_registry.csv
- [ ] Administrative hierarchy (state → county → township) modeled in area_geometry
- [ ] Boundary source license reviewed and recorded

## Parcel / cadastre
- [ ] Parcel/cadastre availability assessed for this jurisdiction
- [ ] If available: parcel source license reviewed, connector added to scope
- [ ] If unavailable: UNKNOWN parcel claim added to rulepack

## Zoning and planning authority
- [ ] County/municipal zoning authority identified
- [ ] Zoning data source (GIS layer or manual records) assessed
- [ ] Zoning source license reviewed

## Water rights and usage regime
- [ ] Water rights regime (prior appropriation / riparian) documented
- [ ] Well permit / water right query source identified if relevant
- [ ] Water source license reviewed

## Mineral and resource rights
- [ ] Surface/mineral split deed prevalence assessed
- [ ] State BLM/GLO records or state equivalent identified
- [ ] Resource-rights caveat language added to rulepack

## Local caveats and professional review requirements
- [ ] Local disclosure requirements reviewed
- [ ] Septic / perc testing jurisdiction rules documented
- [ ] Professional wetland delineation requirement confirmed
- [ ] Floodplain administrator contact process documented

## Source registry
- [ ] All required sources registered in registers/data_source_registry.csv
- [ ] Each source has DS-001 through DS-010 readiness gates evaluated
- [ ] source_readiness.py --priority Must passes for jurisdiction sources

## Rulepack adjustment
- [ ] Homestead MVP ruleset reviewed for jurisdiction-specific concepts
- [ ] Any jurisdiction-specific hard gates added or disabled
- [ ] Forbidden language list reviewed for local context

## Sample report review
- [ ] At least one sample area created and report run generated
- [ ] Report reviewed for overclaiming, missing caveats, or incorrect claim codes
- [ ] If high-stakes output: qualified local domain expert reviewed sample

## Coverage limitations
- [ ] Coverage limitations statement added to docs/planning_pack/ or report scope
- [ ] User-visible caveat language reviewed for this jurisdiction

---
## Sign-off
- Jurisdiction: ________________
- Reviewer: ________________
- Date: ________________
- Notes: ________________
