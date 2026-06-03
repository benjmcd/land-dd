# Data Source License Review Template

## Source identity

- Source registry ID:
- Source name:
- Organization:
- URL:
- Domain:
- Geography:
- Source type / authority level:
- MVP priority:
- Contact:
- Date reviewed:
- Review owner:
- Review status: pending | approved | approved-with-restrictions | blocked | superseded
- Terms/license URL:
- Terms/license version or effective date:
- Evidence file or citation:

## Rights review

Use `yes`, `no`, `unknown`, or `restricted`. `unknown` and `blocked` fail closed for production use.

| Question | Status | Evidence/contract section | Restrictions / notes |
|---|---|---|---|
| Can we cache the data? | | | |
| Can we modify/normalize it? | | | |
| Can we show it in-app? | | | |
| Can we include it in reports? | | | |
| Can users export reports containing derived data? | | | |
| Can users export raw data? | | | |
| Can we use it in AI extraction/summarization? | | | |
| Can we retain historical versions? | | | |
| Is attribution required? | | | |
| Are there user/seat/geography limits? | | | |
| Are there API rate/volume limits? | | | |
| Are owner/PII fields restricted? | | | |
| Are there audit obligations? | | | |

## Provenance and caveats

- Source version/date available:
- Update cadence or freshness class:
- Geographic coverage limits:
- Precision/scale limits:
- Known caveats to store with evidence:
- Required attribution text:
- Fields that must not be exposed:
- Source failure / no-data behavior:
- Reviewer notes:

## Connector gate

Do not enable a live connector until every required item is complete or explicitly waived by ADR.

| Gate | Status | Evidence |
|---|---|---|
| Source registry row exists and matches this review | | |
| License/terms status recorded in source registry | | |
| Usage constraints mapped to source fields | | |
| Fixture data exists | | |
| Success and failure tests exist | | |
| Source freshness/caveats map to evidence/report output | | |
| Rate-limit/failure behavior is defined | | |
| Entitlement or field filtering exists if restricted | | |

## Production decision

- Approved for fixture-only development? yes/no
- Approved for MVP production use? yes/no
- Approved for display? yes/no
- Approved for report export? yes/no
- Approved for machine JSON/API? yes/no
- Approved for raw data export? yes/no
- Approved for AI use? yes/no
- Restrictions / blocking conditions:
- Required attribution:
- Next review date:
- Decision recorded in source registry? yes/no
