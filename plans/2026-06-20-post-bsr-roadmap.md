# Post-BSR Roadmap And Source-Authority Blocker

## Goal

Close the merged `BSR-001` Bologna source-rights matrix lane and make the remaining
sequence explicit without overclaiming source, AOI, hosted, DS-017, or multi-geography
authority.

## Current facts

- PR #109 merged `BSR-001` at
  `4decd1bb3135a060c75c3534d5223da79f7618a7`.
- `config/bologna_source_rights.yaml` exists and validates every Bologna candidate
  source as pending review, not approved, not promoted, and disallowed for fixture,
  runtime, report, and raw export use.
- `config/bologna_preflight.yaml` still blocks Italy source-rights review and Bologna
  implementation.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 milestone-gate authority
  for separating local readiness evidence from source, hosted, DS-017, Bologna, and
  Level 10 claims.
- Must-source readiness remains `sources=8 ready=7 blocked=1`; DS-017 is still blocked.
- The dirty root checkout remains preserved candidate evidence only.

## Coherence check

- Position A: fill the rights matrix now from apparent public-source status. Rejected:
  exact AOI, terms version, source version/date, cache/export/AI/raw-data permissions,
  attribution, caveats, CRS, and report-use authority are not approved.
- Position B: capture Bologna recorded fixtures next. Rejected: no source-rights approval
  and no authorized one-AOI scope exist.
- Position C: generalize to a multi-geography framework now. Rejected: the Bologna pilot
  has not exposed reusable contracts or country-specific exceptions yet.
- Position D: close BSR and block the next Bologna authority intake until external or
  operator-approved source/AOI authority exists. Accepted as the only coherent route.

## Next sequence

1. `BSA-001` source-authority intake: blocked until explicit product/AOI/source-review
   authority exists for exact Bologna candidate sources.
2. If authority arrives, update the rights matrix with reviewed decisions and rerun the
   Bologna rights/preflight/readiness validators.
3. Only after approved rights, create a one-AOI recorded-source corpus plan covering
   source versions, retrieval metadata, attribution, CRS, caveats, source failures, and
   fixture storage boundaries.
4. Implement the one-AOI recorded-source corpus and validate that no raw/export/report
   permissions are exceeded.
5. Build the lowest-layer Bologna evidence/claim/report proof, keeping legal/access/
   title/buildability/wetland/appraisal/lending/investment conclusions out of scope.
6. Reconcile DS-017 and hosted platform blockers separately; neither is unblocked by
   Bologna source-rights work.
7. After one Bologna pilot report is proven, extract shared source/rulepack contracts for
   a repeatable multi-geography framework.

## Validation

Use validate-only checks first:

```powershell
py -3.12 .\scripts\bologna_source_rights_check.py
py -3.12 .\scripts\bologna_preflight_check.py
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\readiness_matrix_check.py
.\scripts\verify.ps1
```

Do not seed runtime state, capture fixtures, or approve sources in this routing pass.
