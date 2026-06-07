# DS-023 Chatham Zoning Live-Candidate Scope

## Decision

Chatham County, NC is the first DS-023 live-candidate county. This is a scope decision, not a production-use approval.

## Why Chatham first

- DS-010 already provides Chatham parcel/zoning-adjacent live evidence with restricted fields.
- Chatham has the clearest current zoning ordinance path among the selected counties.
- Chatham golden AOIs already include zoning-edge and parcel/zoning stress cases.
- A Chatham-first DS-023 slice can test zoning document handling without broadening county scope.

## Official candidate sources

| Source | URL | Current role |
|---|---|---|
| Planning Ordinances & Regulations | https://www.chathamcountync.gov/government/departments-programs-i-z/planning/ordinances-regulations | County page that links current zoning ordinance and related land-use ordinances. |
| Zoning Ordinance PDF | https://www.chathamcountync.gov/home/showpublisheddocument/75675/639046935454470000 | Candidate current zoning ordinance document; county page labels it updated 1/20/2026. |
| County-Wide Zoning | https://www.chathamcountync.gov/government/departments-programs-i-z/planning/zoning-information/county-wide-zoning | Candidate authority for countywide zoning context, zoning map reference, and planning-office verification path. |
| Public Records Requests | https://www.chathamcountync.gov/government/public-records-requests-open-government/public-records-requests | Candidate authority for public-records posture and records-request fallback. |

## Minimum live connector scope

The first Chatham DS-023 connector, if approved, should be document-first and bounded:

- Fetch only the reviewed Chatham zoning ordinance URL.
- Record source URL, retrieval timestamp, ordinance update label, and document hash.
- Extract only section headings, district names, permitted-use table references, and citation snippets needed for screening.
- Emit UNKNOWN or NEEDS_REVIEW evidence when section parsing is incomplete, stale, conflicted, or unsupported.
- Preserve mandatory caveat: zoning screening only; verify with Chatham County Planning before legal, permit, buildability, lending, or construction decisions.

## Required policy decisions before approval

- Whether county-hosted PDF text may be cached in full, cached as snippets only, or fetched per run.
- Whether extracted text can be included in user-visible reports or only cited.
- Whether generated summaries may use ordinance text beyond short evidence-grounded snippets.
- Whether report export may include ordinance excerpts.
- How often the connector must re-check the county page for ordinance update changes.
- Whether the countywide zoning map PDF/layer is a separate source review or part of DS-023.

## Fail-closed behavior

- Missing or changed PDF URL -> SOURCE_FAILURE / UNKNOWN.
- Hash changed without review -> STALE_EVIDENCE_NEEDS_REVIEW.
- Unknown zoning district -> ZONING_EVIDENCE_NEEDS_REVIEW.
- Municipality or ETJ boundary ambiguity -> jurisdiction UNKNOWN; require Chatham County Planning or municipality confirmation.
- No connector output may claim final zoning compliance, permitted use, entitlement, permit eligibility, buildability, or legal status.

## Acceptance gates

- `docs/source-reviews/ds-023.md` updated from pending only if terms and policy support it.
- `registers/data_source_registry.csv` and `db/seeds/002_seed_source_registry.sql` updated only after review approval.
- Connector tests prove bounded URL handling, hash/update tracking, failure evidence, stale evidence, and overclaim caveats.
- Report tests prove DS-023 evidence remains caveated and does not replace human zoning verification.
- `py -3.12 .\scripts\source_readiness.py --priority Must --json` count changes only if registry/seeds truthfully support readiness.
