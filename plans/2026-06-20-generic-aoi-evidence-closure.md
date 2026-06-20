# Generic AOI Evidence-Rich Workflow Closure

## Goal

Prove that non-packaged, operator-supplied AOIs inside the currently selected North
Carolina counties can produce evidence-rich, reviewed, DB-backed reports with source
inventory, caveats, unknowns, artifacts, and evidence lineage. This is the next
unblocked engineering step after `REC-002` because it moves beyond packaged
operator-case demos while staying below hosted, DS-017, Bologna, and multi-geography
authority gates.

## Non-goals

- No new counties, states, countries, jurisdictions, rulepacks, source registry rows, or
  source approvals.
- No DS-017 vendor decision, paid source integration, owner/value/title field exposure,
  or entitlement model claim.
- No hosted deployment, hosted identity/RBAC, hosted observability, hosted object-store,
  hosted SLO, billing, registry publication, or production traffic proof.
- No Bologna recorded-source pilot or international/geography framework.
- No legal access, title, survey, wetland jurisdiction, water-rights, buildability,
  appraisal, lending, insurance, investment, desirability, or protected-class claim.

## Current state

- `state/residual-reconciliation.md` records that the dirty-root candidate stack has no
  implementation slice that should be copied forward wholesale. The remaining divergent
  candidates are either orientation/control-plane surfaces or a narrow selected-county
  runtime-provenance regression candidate.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority. L9 custom AOI
  intake/runtime smoke is proven repo-locally, but hosted Level 10 gates remain partial,
  validate-only, or blocked.
- `docs/runbooks/mvp_operator.md` explicitly distinguishes packaged selected-county
  operator cases from generic `POST /report-runs`; the generic path is currently lower
  evidence by default and does not auto-load the selected-county fixture corpus.
- `config/private_mvp_beta_readiness.yaml` and selected-county manifests define the
  current Buncombe, Chatham, and Brunswick source/provenance scope. DS-017 remains not
  required for private MVP and blocked for full-release source readiness.
- `G9a` proved the custom GeoJSON UI path can submit an AOI, wait for report generation,
  approve when needed, and inspect artifact/lineage for one fixture path. It did not
  prove one non-packaged AOI per selected county with useful selected-county evidence.

## Proposed design

Start with an audit of the current generic AOI path, then implement the smallest
bottom-up slice that gives generic supported AOIs selected-county evidence without
turning packaged cases into hidden fallbacks. The likely implementation should reuse
existing selected-county manifests, fixture connectors, source-provenance expectations,
report approval, artifact, and lineage contracts. It must identify supported county
scope from AOI geometry/source metadata rather than packaged case IDs.

Rejected approaches:

- Treat `G9a` custom AOI smoke as complete generic-AOI proof. It proves intake/runtime
  mechanics, not selected-county evidence utility for arbitrary AOIs.
- Copy dirty-root readiness or project-overview modules. They do not produce user-facing
  evidence and do not advance the generic-AOI product path.
- Start hosted staging or DS-017 work. Both remain external-authority gated.
- Start Bologna before generic-AOI/source-rights prerequisites. That would risk a
  geography-specific fork before the current supported geography is proven.

## Bottom-up sequence

1. Audit `/intake`, `/ui/intake`, `/report-runs`, selected-county operator cases,
   private-MVP readiness, source-provenance, report service, artifact, and lineage code
   paths. Record whether generic AOI reports currently receive useful selected-county
   evidence or mostly empty/unknown output.
2. Add focused failing tests for at least one non-packaged AOI per selected county. The
   tests must not identify the AOI by packaged `case_id`.
3. Add or reuse a compact generic-AOI fixture manifest that maps custom AOI fixtures to
   selected-county support scope, expected source domains, expected caveats, and expected
   unknown/source-failure behavior.
4. Implement the narrowest selected-county evidence orchestration needed for supported
   generic AOIs, reusing existing fixture connector and source-provenance boundaries
   where possible.
5. Prove DB-backed report persistence, approval gating, artifact retrieval, and lineage
   for the generic AOI cases.
6. Prove unsupported/off-scope AOI behavior fails clearly or reports explicit limited
   coverage without selected-county assumptions.
7. Update readiness/state/runbook artifacts only after executable behavior exists.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/operator_cases/**` or a narrower selected-county helper | Reuse selected-county source/evidence orchestration for generic AOI without packaged case IDs. |
| `backend/app/api/intake.py` / `backend/app/api/reports.py` | Only if generic AOI runtime needs explicit supported-county evidence orchestration. |
| `backend/app/reports/service.py` | Only if report creation needs existing evidence attached without weakening report semantics. |
| `tests/fixtures/**` | Add compact non-packaged AOI fixtures/manifest if current fixtures are insufficient. |
| `backend/tests/private_mvp/**` / `backend/tests/api/**` | Focused generic-AOI DB-backed and API/UI tests. |
| `scripts/ui_runtime_smoke.py` / deployment smoke wrappers | Only if runtime smoke must cover the new generic-AOI evidence path beyond G9a. |
| `config/private_mvp_beta_readiness.yaml` | Update only after proof exists. |
| `docs/runbooks/mvp_operator.md` | Clarify generic AOI evidence path after proof exists. |
| `state/PROJECT_STATE.md`, `state/WORKLOG.md`, `state/VALIDATION_LOG.md` | Record implementation and validation. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Refresh evidence wording only if gate evidence changes. |

## Tests / verification

```powershell
py -3.12 -m pytest backend\tests\private_mvp -q
py -3.12 -m pytest backend\tests\api\test_operator_cases_api.py backend\tests\api\test_ui_routes.py -q
py -3.12 .\scripts\private_mvp_readiness_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

If DB-backed behavior changes, also run the relevant `RUN_DB_SMOKE=1` path or record
the exact environmental blocker. Runtime/browser smoke should be added only after the
lower service/API behavior is proven.

## Risks and blockers

- Generic AOI evidence can accidentally become packaged-case lookup by another name.
  Tests must reject case-ID dependence.
- Source fixtures may not cover arbitrary AOI geometry cleanly; unknowns and source
  failures must stay visible instead of becoming silent "no issue found" output.
- County classification and CRS/geometry assumptions must not overgeneralize beyond the
  selected counties.
- DS-017 and live vendor data remain unavailable; the slice must preserve that blocker
  rather than broadening parcel/title/value claims.
- DB-backed proof may require local Postgres/PostGIS availability. If unavailable,
  record the blocker instead of substituting in-memory proof for DB proof.

## Decision log

- 2026-06-20: Selected generic supported-AOI evidence-rich closure as the next active
  engineering plan after `REC-002` because residual reconciliation found no dirty-root
  implementation slice to copy forward, hosted/DS-017/Bologna work remains gated, and
  the largest unblocked gap is proving useful evidence for non-packaged AOIs inside the
  supported selected counties.

## Progress log

- 2026-06-20: Opened plan from clean worktree `worktrees/res-rec` after generating
  `state/residual-reconciliation.md` against current live main.
- 2026-06-20: Implemented the first generic supported-AOI slice in clean worktree
  `worktrees/g9b-aoi`: non-packaged operator areas that match recorded selected-county
  generic AOI fixture profiles can now use `/operator-cases/supported-aoi/report` to
  ingest selected-county fixture connector evidence against the existing `area_id`,
  approve connector-QA handoffs and the final report, and return approved UI/dossier/
  artifact links. Bare generic `POST /report-runs` remains evidence-consumer-only by
  default, and arbitrary in-county AOIs still fail closed unless they match a recorded
  fixture profile.
- 2026-06-20: Validated the slice with focused OpenAPI/planning-pack contract tests,
  default `.\scripts\verify.ps1`, and DB-enabled `.\scripts\verify.ps1` against an
  isolated PostGIS runtime on port `55470`.
