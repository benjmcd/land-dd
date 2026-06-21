# Project State

## Current checkpoint (2026-06-21 EQP2-4 checker advertisement parity)

Live `origin/main` contains EQP2-3 blocked P0 repo-local auto-evidence through
PR #135 at `2ba6f1b7423a59e23dec7f3895fb5f6ceb72f663`, on top of the jsonschema
mypy stub fix through PR #136 at `71c6a74eae08811d4e178b0c11365ff1e247772d`,
the report-run rights optionality fix through PR #134 at
`af6dd94d9bb3fb9f53afbd369a7568dfeb72e65e`, the report-run contract
backward-compat ADR through PR #133 at
`8822a1408cce54bc99fe760f3386243a29e64b0d`, the error-safety redaction
hardening through PR #132 at `be2f504a91dc5503a2fe160432fa7e7e8e05a2ab`,
`EQP2-2` through PR #131 at
`0f0f592b9522d26afb70007281870325edd13579`, `EQP2-1` through PR #130 at
`a291d0d41eaa5b85b6ec8c80a79b33f2f7d5e670`, and the EQ Phase 2 handoff
through PR #129 at `b88d608aec21a988bc4127f167ee0972f6da06f2`.
`EQP2-4` makes mapped readiness/authority checkers advertise their crosswalk
criterion IDs, makes validation prove crosswalk/checker parity, and makes status
derivation consume checker-advertised criteria while keeping all statuses honest
and non-passing.

- **Current implementation plan**:
  `plans/2026-06-21-eqp2-4-checker-parity.md`.
- **Latest repo-local test hardening**:
  `backend/tests/test_qualification_status_check.py` proves the derived status view
  matches the committed `P0 = BLOCKED` / non-P0 `NOT_RUN` shape, rejects P0 drift to
  `NOT_RUN`, treats unexpected checker failures as mapped `BLOCKED` drift, and fails
  closed if a mapped checker result is missing. `backend/tests/test_qualification_change_impact_check.py`
  now proves advisory path-to-change-class mapping, crosswalk surface enrichment,
  unmatched-path reporting, unsafe-path fail-closed behavior, and CLI output for the
  EQP2-2 change-impact checker. `backend/tests/test_qualification_p0_auto_evidence.py`
  proves the P0 auto-evidence artifact matches the live catalog rows, links from the
  blocked status file, leaves `result_path` null, records backlog rows as
  `auto-evidenced; still target-blocked`, and fails closed when the status link is
  missing.
- **Current task state**: `BSR-001`, post-BSR routing, `BSG-001`, `PAI-001`,
  `SRP-001`, `RSR-001`, `PR114-SYNC`, `BRC-001`, `PR116-SYNC`, `AUTH-HANDOFF`,
  `READINESS-CORE`, `BOL-PRIORITY`, `BPS-001`, `BPS-REQ-001`, `EQ-1`, `EQ-BOL`,
  `EQ-2`, `EQ-3`, `EQ-4`, `EQP2-1`, `EQP2-2`, and `EQP2-3` are done in the current routing model. `EQP2-1` adds
  `scripts/qualification_status_check.py`, `scripts/qualification_status_check.ps1`,
  and `scripts/run_qualification_status_check.sh`. The checker runs mapped readiness,
  authority, source, release, security, operations, and spatial checker paths; default
  passing checks remain qualification `NOT_RUN`; the known unstarted runtime inputs
  for package-manifest and spatial DB-runtime checks remain `NOT_RUN`; any other
  nonzero mapped checker result derives `BLOCKED` and fails the committed-status
  comparison. `EQP2-2` adds `scripts/qualification_change_impact_check.py`,
  `scripts/qualification_change_impact_check.ps1`, and
  `scripts/run_qualification_change_impact_check.sh`; the checker maps changed paths
  through matrix-owned `path_globs` and crosswalk config/checker paths while remaining
  advisory. `EQP2-3` adds `docs/qualification/P0_AUTO_EVIDENCE.yaml`,
  `scripts/qualification_p0_evidence_check.py`,
  `scripts/qualification_p0_evidence_check.ps1`, and
  `scripts/run_qualification_p0_evidence_check.sh`; the checker validates exactly
  `P0-004`, `P0-005`, `P0-021`, and `P0-023` as blocked repo-local evidence rows
  against the live catalog, status, backlog, and local suppression/control signals.
  `EQP2-4` adds `scripts/qualification_checker_advertisement.py`, checker
  `--qualification-criteria-json` hooks, validator crosswalk/checker parity, and
  status derivation through checker-advertised criterion IDs. EQ Phase 2 is
  implementation-complete in repo-local state pending PR merge and detached
  post-merge proof.
- **Empirical qualification boundary**: `P0` remains `BLOCKED`, all other
  qualifications/overlays remain `NOT_RUN`, `candidate.*` remains null, targets remain
  `DRAFT`, and no owner/source/AOI/Bologna/hosted/DS-017 decision is unfrozen.
- **Verification routing**: the new status checker is wired after structural
  qualification validation in `scripts/verify.ps1` and `scripts/verify.sh`, and in the
  dedicated `qualification-selftest` CI job through
  `scripts/run_qualification_status_check.sh`. The EQP2-2 change-impact checker is
  wired immediately after the status checker in the same local verify scripts and
  dedicated qualification CI job. The EQP2-3 P0 auto-evidence checker is wired after
  change-impact in the same local verify scripts and dedicated qualification CI job.
- **Immediate next pursuit after EQP2-4**: merge/verify this lane, then treat the
  active Phase 2 goal as complete if post-merge proof still shows status derivation,
  change-impact invalidation, P0 repo-local evidence, and checker advertisement
  parity all green. The Bologna path remains prioritized but still requires external
  product/AOI/source-rights authority before corpus or DB-backed report work.
- **Known boundaries to preserve**: no qualification `PASS`, owner-decision unfreeze,
  Q3 expansion target, AI/CG/FIN/E target or rubric, Bologna AOI selection, source
  approval, source registry promotion, recorded fixture, connector, DB seed,
  report/API/UI/schema change, auth change, report semantic change, DS-017 approval,
  vendor selection, hosted deployment, hosted identity/RBAC, hosted observability/log
  retention/alerting, hosted object-store proof, new jurisdiction, EU/Italy rulepack,
  production traffic proof, ranking/recommendation semantics, multi-geography
  framework implementation, report semantic overclaim, or Level 10 completion claim.

## Previous checkpoint (2026-06-21 EQ-4 readiness crosswalk)

Live `origin/main` contains EQ-3 through PR #127 at
`961bffd513df6b8fc66b177e605094c7205e1dee`. `EQ-4` is the current repo-local lane:
subordinate the existing readiness, authority, release, source, security, operations,
and spatial gate surfaces to empirical-qualification criterion IDs without changing
checker behavior or claiming any qualification pass.

- **Current implementation plan**:
  `plans/2026-06-21-eq-4-readiness-crosswalk.md`.
- **Latest repo-local test hardening**:
  `backend/tests/test_qualification_readiness_crosswalk.py` and
  `backend/tests/test_qualification_spine.py` prove the readiness crosswalk covers the
  live derived inventory, every mapped criterion ID exists in the catalog, the
  crosswalk document records mapped surfaces/gaps/orphans, and the change-impact matrix
  invalidates by catalog criterion IDs rather than prose labels.
- **Current task state**: `BSR-001`, post-BSR routing, `BSG-001`, `PAI-001`,
  `SRP-001`, `RSR-001`, `PR114-SYNC`, `BRC-001`, `PR116-SYNC`, `AUTH-HANDOFF`,
  `READINESS-CORE`, `BOL-PRIORITY`, `BPS-001`, `BPS-REQ-001`, `EQ-1`, `EQ-BOL`,
  `EQ-2`, `EQ-3`, and `EQ-4` are done in the current routing model. `EQ-BLOCK-*` tasks record blocked
  external/owner-authority decisions for targets, rubrics, domains, source profiles,
  scope/version fields, Bologna pilot scope, Bologna source rights, Bologna recorded
  corpus, and a DB-backed Bologna report proof. `EQ-5` and `EQ-R` remain queued.
  `BSA-001` remains blocked until explicit product/AOI/source-review
  authority exists for exact candidate sources. Must-source readiness remains
  `sources=8 ready=7 blocked=1`, with `DS-017` as the only blocked Must source.
- **Empirical qualification boundary**: ADR 0004 records that the
  empirical-qualification catalog is the canonical empirical-validity authority.
  Existing readiness YAML/checkers, authority packets, release-readiness checks, and
  `state/LEVEL_9_10_GATE_MATRIX.md` remain CI/deployment gates that report into the
  qualification control plane rather than competing qualification authorities.
- **Empirical qualification spine**: `docs/qualification/**`,
  `config/qualification/**`, `schemas/qualification/**`,
  `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`, `scripts/validate_qualification.py`,
  and `scripts/selftest_qualification_validator.py` now land as repo-owned structural
  artifacts. Validation reports `target status: DRAFT`,
  `highest valid classification: L9-R`, and `BLOCKED-READINESS` warnings for
  template-only domain profiles, no frozen `source_profile_ids`, unresolved
  scope/version fields, unresolved ruleset versions, draft qualification targets,
  draft criterion contracts, and draft judgment rubrics.
- **Empirical qualification crosswalk**:
  `config/qualification/readiness_crosswalk.yaml`,
  `schemas/qualification/readiness_crosswalk.schema.json`, and
  `docs/qualification/readiness-crosswalk.md` map `27` active readiness/authority gate
  surfaces to catalog criterion IDs, list current gaps, and record no known orphaned
  surfaces. `config/qualification/change_impact_matrix.yaml` now invalidates by
  criterion IDs, and the validator fails closed if the crosswalk inventory drifts or a
  crosswalk/change-impact criterion ID is absent from the catalog. This mapping does
  not satisfy or pass any mapped criterion.
- **Blocked product posture**: the imported status file preserves no `PASS` claim.
  Its structural P0 row is now `BLOCKED` with `result_path: null`,
  `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md`, and
  `docs/qualification/PROJECT_PARAMETERIZATION_BLOCKERS.md` as blocker references.
  Product qualification remains blocked until owner decisions, selected source
  profiles, frozen domain profiles, target bindings, rubrics, reviewers, candidate
  artifacts, and empirical evidence are frozen. Do not fabricate a candidate commit,
  artifact digest, or result record just to make P0 look run.
- **Current Bologna scope boundary**: `config/bologna_pilot_scope_authority.yaml`
  records the missing product, one-AOI, intended-operator, non-goal, stop-condition,
  jurisdiction, rulepack/evidence-only, DS-017-treatment, candidate-source-selection,
  fixture-boundary, runtime-boundary, and no-overclaim decisions. Its
  `scope_decision_requests` rows name the expected reference, minimum evidence, and
  downstream use for each missing decision. It is validate-only, uncited, and blocked;
  all downstream source-authority, source-rights, and corpus updates remain disabled.
- **Immediate next pursuit**: the substantive Bologna path still requires external
  product/AOI/source-rights authority before source-rights rows, recorded corpus
  manifests, or DB-backed report proof can change. If no external authority arrives,
  the next repo-local empirical-qualification slice is `EQ-5`: reconcile the blocker
  backlog against the landed spine and crosswalk. Lane R may proceed independently to
  correct the false residual-reconciliation claim.
- **If qualification authority is absent**: keep all qualification PASS claims blocked
  and do not invent thresholds, reviewers, source profiles, domain profiles, empirical
  evidence, owner decisions, source rights, hosted authority, deployment targets,
  candidate commits, or artifact digests.
- **Known boundaries to preserve**: no qualification `PASS`, owner-decision unfreeze,
  Q3 expansion target, AI/CG/FIN/E target or rubric, Bologna AOI selection, source
  approval, source registry promotion, recorded fixture, connector, DB seed,
  report/API/UI/schema change, auth change, report semantic change, DS-017 approval,
  vendor selection, hosted deployment, hosted identity/RBAC, hosted observability/log
  retention/alerting, hosted object-store proof, new jurisdiction, EU/Italy rulepack,
  production traffic proof, ranking/recommendation semantics, multi-geography
  framework implementation, report semantic overclaim, or Level 10 completion claim.

## Current checkpoint (2026-06-20 Bologna source-candidate discovery BSC-001)

The active implementation authority is now `BSC-001` from
`plans/2026-06-20-bologna-source-candidate-discovery.md`. This follows merged PR #107
at `295c96a4308b39e77fee7935d3b5e465755ad6bf`, which completed `BP-001` post-SE001
Bologna preflight. The dirty root checkout remains preserved candidate evidence only;
continued work should happen from fresh or already-clean worktrees under
`worktrees/<short-name>`.

- **Active plan**: `plans/2026-06-20-bologna-source-candidate-discovery.md`.
- **Purpose**: turn the Bologna preflight's `italy_source_inventory` gap into a
  validate-only, candidate-only source inventory so the next source-rights review has
  concrete official candidate surfaces without approving sources or starting Bologna.
- **Current implementation slice**: clean worktree `worktrees/bol-src` adds
  `config/bologna_source_candidates.yaml`, `docs/runbooks/bologna_source_candidates.md`,
  `docs/source-reviews/bologna-source-candidates.md`,
  `scripts/bologna_source_candidates_check.py`, Windows/POSIX wrappers, focused
  artifact tests, and preflight composition. Candidate domains cover municipal
  planning, municipal open data, regional topographic data, regional catalog services,
  CRS/reference systems, and environmental map discovery. Every candidate remains
  `not_approved`, not source-registry-promoted, disallowed for runtime use, and
  disallowed for fixture-corpus use.
- **Next required step**: complete focused and canonical validation, then publish/merge
  `BSC-001` and remove the worktree if checks and CI pass.
- **Goal sequence**: immediate work is candidate-source packet validation and merge.
  The next repo-local pass after that should be a source-rights review plan for exact
  Bologna layers/documents/datasets only if product/AOI authority is available; absent
  that, record the blocker and do not fabricate a fixture corpus. Mid-term work is an
  authorized one-AOI Bologna recorded-source corpus with source versions, retrieval
  metadata, CRS policy, attribution, source-failure fixtures, and evidence-only or
  rulepack scope; then one DB-backed report proof with evidence, unknowns/claims,
  caveats, artifacts, and lineage. Parallel external blockers remain DS-017 treatment,
  hosted platform/database/DNS/TLS, identity/RBAC, object-store, observability,
  alerting, billing, secret-manager, image-publication, and production workload
  authority. Long-term work is a repeatable multi-geography source/rulepack framework
  only after the Bologna pilot exposes real shared contracts and country-specific
  boundaries.
- **Known boundaries to preserve**: no Bologna AOI selection, source approval, source
  registry promotion, recorded fixture, connector, DB seed, report/API/UI/schema
  change, DS-017 approval, vendor selection, hosted deployment, hosted identity/RBAC,
  hosted observability/log retention/alerting, hosted object-store proof, new
  jurisdiction, EU/Italy rulepack, production traffic proof, ranking/recommendation
  semantics, multi-geography framework implementation, report semantic overclaim, or
  Level 10 completion claim.

## Current checkpoint (2026-06-20 post-SE001 Bologna preflight BP-001)

The active implementation authority is now `BP-001` from
`plans/2026-06-20-post-se001-bologna-preflight.md`. This follows merged PR #106 at
`a508cd207c95fb79736340295c7eaaee908cc2bf`, which completed the `SE-001`
source-entitlement decision packet. The dirty root checkout remains preserved
candidate evidence only; continued work should happen from fresh or already-clean
worktrees under `worktrees/<short-name>`.

- **Active plan**: `plans/2026-06-20-post-se001-bologna-preflight.md`.
- **Purpose**: restore live routing after SE-001 and add a validate-only Bologna
  recorded-source pilot preflight that makes the long-term Bologna and multi-geography
  path explicit without selecting Bologna, approving Italy/EU/local sources, approving
  a rulepack, unblocking DS-017, creating hosted authority, seeding data, or changing
  runtime behavior.
- **Current implementation slice**: clean worktree `worktrees/authority-next` adds
  `config/bologna_preflight.yaml`, `docs/runbooks/bologna_preflight.md`,
  `scripts/bologna_preflight_check.py`, Windows/POSIX wrappers, focused artifact tests,
  a Bologna section in `state/PRODUCTION_AUTHORITY_PACKET.md`, and routing/state
  updates. Baseline source-readiness, source-entitlement, checklist dry-run,
  release-readiness, and readiness-matrix validators passed before edits. DS-017 remains
  blocked and Bologna remains not started.
- **Next required step**: validate BP-001 with the focused preflight tests/checker,
  source/readiness validators, workspace validation, diff/no-deletion checks, and
  default `.\scripts\verify.ps1`; then publish/merge and clean the worktree if checks
  pass.
- **Goal sequence**: immediate work is BP-001 routing/preflight validation and merge;
  mid-term work is external DS-017 decision resolution or explicit deferral/removal,
  hosted platform/identity/observability/artifact authority if granted, and then a
  separately authorized Bologna recorded-source implementation plan; long-term work is
  a repeatable multi-geography source/rulepack framework designed only after the
  Bologna pilot exposes real shared contracts and country-specific boundaries.
- **Known boundaries to preserve**: no Bologna implementation, recorded-source corpus,
  source registry promotion, connector, DB seed, report/API/UI/schema change, DS-017
  approval, vendor selection, owner/value/title/raw vendor exposure, paid-source
  metering proof, hosted deployment, hosted identity/RBAC, hosted observability/log
  retention/alerting, hosted object-store proof, new jurisdiction, rulepack,
  production traffic proof, ranking/recommendation semantics, multi-geography framework
  implementation, report semantic overclaim, or Level 10 completion claim.

## Previous checkpoint (2026-06-20 source entitlement decision packet SE-001)

The active implementation authority is now `SE-001` from
`plans/2026-06-20-source-entitlement-decision-packet.md`. This follows merged PR #105
at `cbde4572c1aa99cf4f5ba69b258db815612b700c`, which completed the G9c
supported-AOI UI/runtime proof. The dirty root checkout remains preserved candidate
evidence only; continued work should happen from fresh or already-clean worktrees under
`worktrees/<short-name>`.

- **Active plan**: `plans/2026-06-20-source-entitlement-decision-packet.md`.
- **Purpose**: make DS-017 decision-ready by adding a validate-only,
  machine-readable source-entitlement packet and checker that cross-check current
  source-readiness truth, release readiness, and the production authority packet.
- **Current implementation slice**: clean worktree `worktrees/ds017-ent` adds
  `config/source_entitlements.yaml`, `docs/runbooks/source_entitlements.md`,
  `scripts/source_entitlement_check.py`, Windows/POSIX wrappers, focused artifact
  tests, and release-readiness composition. Focused tests, source-entitlement wrapper,
  source-readiness, release readiness, readiness matrix, diff/no-deletion checks,
  workspace validation, and default `.\scripts\verify.ps1` passed. DS-017 remains
  blocked and unselected.
- **Completion status**: SE-001 was published and merged through PR #106. Follow-on
  work should still wait for external DS-017 vendor/license/cost/entitlement authority,
  an explicit product decision to defer or remove DS-017 from Must scope, a substitute
  public/official source decision, or hosted authority if those external prerequisites
  arrive first.
- **Known boundaries to preserve**: no DS-017 approval, vendor selection, connector,
  source-readiness promotion, owner/value/title/raw vendor exposure, paid-source
  metering proof, hosted deployment, hosted identity/RBAC, hosted observability/log
  retention/alerting, hosted object-store proof, Bologna pilot, new county,
  jurisdiction, rulepack, production traffic proof, ranking/recommendation semantics,
  report semantic overclaim, DB schema change without plan, or Level 10 completion
  claim.

## Previous checkpoint (2026-06-20 supported-AOI UI runtime proof G9c)

The active implementation authority is now `G9c` from
`plans/2026-06-20-supported-aoi-ui-runtime.md`. This follows merged PR #104 at
`a7c4ceca2ca02afa19c656d853c4e3720ee8b92b`, which completed the G9b API/service/DB
supported-AOI `area_id` path. The dirty root checkout remains preserved candidate
evidence only; continued work should happen from fresh or already-clean worktrees under
`worktrees/<short-name>`.

- **Active plan**: `plans/2026-06-20-supported-aoi-ui-runtime.md`.
- **Purpose**: prove the supported-AOI `area_id` path through the browser/operator
  workflow by adding a no-JavaScript UI launcher and runtime smoke support that posts
  an existing stored AOI to the same reviewed fixture-backed report path.
- **Current implementation slice**: clean worktree `worktrees/next-route` adds a
  supported-AOI panel on `/ui/`, a
  `/ui/operator-cases/supported-aoi/report` POST handler, focused UI tests, runtime
  smoke support for `--supported-aoi-area-id`, regenerated OpenAPI stubs, and the
  routing/state updates needed after G9b merged. The handler reuses reviewer
  `report:run` scope and workspace identity handling, then delegates to the existing
  supported-AOI API helper.
- **Next required step**: complete focused and canonical validation, then publish/merge
  G9c and clean the worktree. Follow-on work should reassess whether the next unblocked
  pass is deeper supported-AOI runtime ergonomics, source-entitlement/DS-017 decision
  support, or hosted authority collection if external prerequisites exist.
- **Known boundaries to preserve**: no arbitrary in-county coverage, no new source
  authority, new county, jurisdiction, rulepack, DS-017 approval, Bologna pilot, hosted
  deployment, hosted identity/RBAC, hosted observability/log retention/alerting, hosted
  object-store proof, production traffic proof, ranking/recommendation semantics, public
  API contract overclaim, DB schema change without plan, report semantic overclaim, or
  Level 10 completion claim.

## Current checkpoint (2026-06-20 generic supported-AOI evidence-rich workflow G9b)

The active implementation authority is now `G9b` from
`plans/2026-06-20-generic-aoi-evidence-closure.md`. This follows merged PR #102 at
`47913930ea6b5fc0af71e463d998f57535b7cad4` and the completed `REC-002` residual
reconciliation pass. The dirty root checkout remains preserved candidate evidence only;
continued work should happen from fresh or already-clean worktrees under
`worktrees/<short-name>`.

- **Active plan**: `plans/2026-06-20-generic-aoi-evidence-closure.md`.
- **Purpose**: audit and then prove that non-packaged operator-supplied AOIs inside the
  selected North Carolina counties can produce evidence-rich, reviewed, DB-backed
  reports with source inventory, caveats, unknowns, artifact retrieval, and evidence
  lineage, without using packaged operator-case IDs as a hidden fallback.
- **Current reconciliation evidence**: `state/residual-reconciliation.md` compares the
  preserved dirty-root candidate stack against current live main and classifies `128`
  candidate paths: `8` already landed exactly, `64` landed differently, `3` still
  divergent, `17` deferred/still blocked, `34` obsolete reference artifacts, and `2`
  coordination/generated artifacts. No dirty-root implementation slice should be copied
  forward wholesale.
- **Current implementation slice**: clean worktree `worktrees/g9b-aoi` now proves the
  first generic supported-AOI path below packaged case IDs. The new
  `/operator-cases/supported-aoi/report` route takes an existing `area_id`, classifies
  selected-county scope from stored geometry, requires a recorded generic AOI fixture
  profile match, ingests selected-county fixture connector evidence against that same
  `area_id`, approves connector-QA handoffs plus the final report, and returns the
  approved UI/dossier/artifact links. Bare generic `POST /report-runs` remains
  evidence-consumer-only by default. Local validation includes focused OpenAPI contract
  tests, default `.\scripts\verify.ps1`, and DB-enabled `.\scripts\verify.ps1` against
  isolated PostGIS on port `55470`.
- **Next required step**: publish/merge the G9b branch and remove the completed
  worktree after merge. Follow-on work should decide whether to extend UI ergonomics for
  the supported-AOI area-ID route or move to the next source-entitlement/hosted-authority
  blocker, without broadening source or geography authority.
- **Known boundaries to preserve**: no new source authority, new county, new
  jurisdiction, rulepack, DS-017 approval, Bologna pilot, hosted deployment, hosted
  identity/RBAC, hosted observability/log retention/alerting, hosted object-store proof,
  production traffic proof, ranking/recommendation semantics, public API contract
  overclaim, DB schema change without plan, report semantic overclaim, or Level 10
  completion claim.

## Previous checkpoint (2026-06-20 post-G9a roadmap and reconciliation routing)

The active implementation authority is now the metadata-only `REC-002` routing pass
from `plans/2026-06-20-post-g9a-roadmap-reconciliation.md`. This follows merged PR
#101 at `b525439e6bcddefba81c7d6bf12290b3f8551b55`, which completed `G9a` custom AOI
UI runtime smoke. The dirty root checkout remains preserved candidate evidence only;
continued work should happen from fresh or already-clean worktrees under
`worktrees/<short-name>`.

- **Active plan**: `plans/2026-06-20-post-g9a-roadmap-reconciliation.md`.
- **Purpose**: restore live routing after G9a, preserve the lane-reference handoff as
  non-authoritative context, and define the next immediate, mid-term, and long-term
  sequence without claiming hosted, source, DS-017, Bologna, or Level 10 authority.
- **Current live authority**: `origin/main` is
  `b525439e6bcddefba81c7d6bf12290b3f8551b55` (`Merge pull request #101 from
  benjmcd/codex/aoi-smoke`). The exact named handoff file
  `C:\Users\benny\Downloads\land_dd_lane_reference_handoff_v4(1).md` was absent; the
  nearest `land_dd_lane_reference_handoff_current.md` was read only as planning context
  and names the older `c3364ea` baseline.
- **Next required step**: run a residual Lane 1 reconciliation pass from current live
  `origin/main`, comparing the preserved dirty-root candidate stack against `b525439...`
  to mark candidate concepts as already landed, still divergent, deferred, obsolete, or
  coordination/generated. Select the next retained engineering slice only after that
  residual inventory.
- **Goal sequence**: immediate work is residual reconciliation and next-slice selection;
  mid-term work is generic supported-AOI evidence-rich closure, repo-local
  source-entitlement guardrails/DS-017 decision support, and hosted authority only when
  external prerequisites exist; long-term work is a Bologna recorded-source pilot and
  then a repeatable multi-geography source/rulepack framework.
- **Known boundaries to preserve**: no product behavior, source, connector, county,
  jurisdiction, rulepack, DS-017 approval, Bologna pilot, hosted deployment, hosted
  identity/RBAC, hosted observability/log retention/alerting, hosted object-store proof,
  production traffic proof, ranking/recommendation semantics, public API contract
  change, DB schema change, report semantics change, or Level 10 completion claim.
- **Post-REC-002 status**: residual classification is recorded in
  `state/residual-reconciliation.md`. `REC-002` found no dirty-root implementation slice
  to copy forward wholesale; the next active plan is `G9b` generic supported-AOI
  evidence-rich workflow closure.

## Previous checkpoint (2026-06-20 custom AOI UI runtime smoke G9a)

The active implementation authority is now the narrow `G9a` custom AOI UI runtime
smoke slice from `plans/2026-06-20-custom-aoi-ui-runtime-smoke.md`. This follows the
merged `G8` observability readiness UI slice from PR #100 at
`2522b734578ad498910f10598aa5404fb6601129`. The dirty root checkout remains preserved
candidate evidence only; continued work should happen from fresh or already-clean
worktrees under `worktrees/<short-name>`.

- **Active plan**: `plans/2026-06-20-custom-aoi-ui-runtime-smoke.md`.
- **Purpose**: prove that the existing custom GeoJSON UI intake path can complete the
  repo-local runtime workflow under reviewer control: submit a fixture AOI through
  `/ui/intake`, wait for async report generation, approve pending reports through the
  existing reviewer UI route, then verify approved delivery, artifact persistence, and
  evidence lineage.
- **Implemented scope so far**: `scripts/ui_runtime_smoke.py` now accepts
  `--custom-aoi-fixture`, posts the fixture GeoJSON to `/ui/intake`, waits for report
  delivery or pending approval, uses existing reviewer session or fallback reviewer
  fields for approval when needed, verifies custom AOI delivery links with
  `custom-aoi-report`, checks artifact persistence when requested, and follows
  custom lineage with `custom-aoi-lineage`. The PowerShell and POSIX deployment smoke
  wrappers now include this custom AOI UI proof in the existing DB-backed reviewer
  smoke run.
- **Current local validation**: focused runtime-smoke tests first failed on the missing
  `--custom-aoi-fixture` option and then on the missing pending-approval approval path;
  after implementation, `py -3.12 -m pytest backend\tests\test_ui_runtime_smoke_script.py
  -q` passed (`19 passed`). Focused `ruff check` passed for the changed smoke script and
  tests, and focused mypy passed for the changed smoke script and tests after widening
  the fake route map helper type. Private-MVP, release-readiness, and readiness-matrix
  validators passed; the readiness-matrix wrapper and artifact tests passed; `git diff
  --check`, no-deletion, and workspace validation passed. Final `.\scripts\verify.ps1`
  passed with backend tests, ruff, and mypy over `341` source files. DB smoke was skipped
  by default.
- **Known boundaries to preserve**: no new source, connector, county, jurisdiction,
  rulepack, DS-017 approval, Bologna pilot, hosted deployment, hosted identity/RBAC,
  hosted observability/log retention/alerting, hosted object-store proof, production
  traffic proof, ranking/recommendation semantics, public API contract change, DB schema
  change, report semantics change, or Level 10 completion claim.
- **Post-merge status**: PR #101 is merged on `origin/main` at
  `b525439e6bcddefba81c7d6bf12290b3f8551b55`; `worktrees/aoi-smoke` was removed after
  post-merge proof. The next active pass is the metadata-only `REC-002` residual Lane 1
  reconciliation and roadmap routing update.

## Previous checkpoint (2026-06-20 observability readiness UI G8)

The implementation authority for `G8` was the narrow observability readiness slice from
`plans/2026-06-20-observability-readiness-ui-g8.md`. This followed the merged
`G6c` performance guardrails UI slice from PR #99 at
`3ea51589fd2a69e52b474c8a38baf8047a5d7744`. The dirty root checkout remains preserved
candidate evidence only; continued work should happen from fresh or already-clean
worktrees under `worktrees/<short-name>`.

- **Plan**: `plans/2026-06-20-observability-readiness-ui-g8.md`.
- **Purpose**: reconstruct the retained local-only observability readiness surface from
  live `origin/main`, focused on existing repo-owned metrics, queue/recovery,
  connector observability, source-failure evidence, alert-rule, deployment-smoke
  reference, and hosted-observability blocker authority, before hosted dashboard,
  alert-routing, pager, hosted log-retention, or production traffic observability work.
- **Implemented scope so far**: `config/observability_readiness.yaml` catalogs the local
  observability signals, alert-rule coverage, hosted blockers, validation commands, and
  false hosted/provisioning/runtime limits. `scripts/observability_readiness_check.py`
  and wrappers validate the catalog against existing metrics, operations, connector,
  alerting, hosted-deployment, and retention authority without running runtime smoke or
  provisioning hosted services. `backend/app/observability_readiness.py` fails closed on
  catalog/path/blocker/limit drift, and `/ui/observability-readiness` renders a GET-only
  local operator view linked from the current UI authority pages. Release-readiness
  composition and OpenAPI stubs were updated for the new route.
- **Current local validation**: live `origin/main` was fetched and the clean
  `codex/obs-ready` worktree was confirmed at
  `3ea51589fd2a69e52b474c8a38baf8047a5d7744`, matching `origin/main`. Focused G8 tests
  first failed on the missing `app.observability_readiness` module, then passed after
  implementation and review hardening (`14 passed`). Adjacent observability,
  operations, alerting, deployment-smoke, and release-readiness tests passed after
  adding the new release-readiness allowlist entries. OpenAPI stubs were regenerated
  and OpenAPI parity passed (`3 passed`). Focused ruff and mypy passed. The
  observability readiness validator, wrapper, release-readiness validator, and
  readiness-matrix validator passed. `tasks/task_queue.yaml` parses with active plan
  `plans/2026-06-20-observability-readiness-ui-g8.md` and active task `G8`.
  `git diff --check` passed with only existing OpenAPI line-ending normalization
  warnings, no tracked deletions were reported, workspace validation passed, and final
  `.\scripts\verify.ps1` passed with backend tests, ruff, and mypy over `341` source
  files. DB smoke was skipped by default.
- **Known boundaries to preserve**: no hosted dashboard creation, alert dispatch, pager
  or on-call provisioning, hosted log-retention provisioning, hosted infrastructure
  mutation, secret writing, public endpoint opening, deployment-smoke execution from
  the UI helper, connector execution, runtime provenance seeding, source-failure
  evidence mutation, DS-017 approval, source/vendor expansion, generic AOI proof,
  Bologna pilot, public JSON API behavior change, DB schema change, report-semantics
  change, hosted deployment, hosted source authority, hosted identity/RBAC, hosted SLO
  or capacity proof, production traffic observability proof, or Level 10 completion
  claim.
- **Post-merge status**: PR #100 is merged on `origin/main` at
  `2522b734578ad498910f10598aa5404fb6601129`; `worktrees/obs-ready` was removed after
  post-merge proof. The next retained slice is the narrow `G9a` custom AOI UI runtime
  smoke proof.

## Previous checkpoint (2026-06-20 performance guardrails UI G6c)

The implementation authority for `G6c` was
`plans/2026-06-20-performance-guardrails-ui-g6c.md`. It followed the merged `G6b`
operations guardrails UI slice from PR #98 at
`51f347d9940016ef428ea3837cbc4888f6ac81c1` and merged through PR #99 at
`3ea51589fd2a69e52b474c8a38baf8047a5d7744`.

- **Purpose**: reconstruct the third retained `G6` local guardrail surface from live
  `origin/main`, focused on existing repo-owned performance baseline, spatial
  query-plan, and queue-backpressure authority, before `G8` local observability
  readiness or any hosted performance/SLO work.
- **Implemented scope**: `backend/app/performance_guardrails.py` parses the repo-owned
  performance baseline and spatial query-plan catalogs, validates required load-test
  scenarios, result schema fields, false hosted/CI/measured-result limits, required GIST
  indexes, opt-in manual runtime `EXPLAIN` posture, false spatial runtime/default
  limits, queue-backpressure settings from `Settings`, runbook phrases, and
  repo-relative authority paths. `/ui/performance-guardrails` renders a GET-only local
  operator view over those checked artifacts and links from the current local UI
  authority pages. OpenAPI stubs were regenerated for the FastAPI UI route.
- **Validation**: focused G6c tests first failed on the missing
  `app.performance_guardrails` module, then passed after implementation (`8 passed`).
  Focused performance guardrails plus performance artifact, load-test artifact, spatial
  query-plan, spatial runtime query-plan, and backpressure tests passed (`63 passed`).
  OpenAPI parity passed (`2 passed`). Focused ruff and mypy passed.
  Performance-baseline, spatial query-plan, release-readiness, and readiness-matrix
  validators passed. `.\scripts\run_load_test.ps1 -ValidateOnly` passed without live
  HTTP requests or measured artifacts. `git diff --check` passed with only existing
  OpenAPI line-ending normalization warnings, no tracked deletions were reported,
  workspace validation passed, and final `.\scripts\verify.ps1` passed with backend
  tests, ruff, and mypy over `338` source files. DB smoke was skipped by default.
- **Known boundaries to preserve**: no live load-test execution, runtime `EXPLAIN`, DB
  connection, queue mutation, generated performance artifact, Docker invocation, hosted
  dashboard, alert routing, production capacity claim, SLO claim, DS-017 approval,
  source/vendor expansion, generic AOI proof, Bologna pilot, public JSON API behavior
  change, DB schema change, report-semantics change, hosted deployment, hosted source
  authority, hosted identity/RBAC, hosted observability, or Level 10 completion claim.
- **Post-merge status**: PR #99 is merged on `origin/main` at
  `3ea51589fd2a69e52b474c8a38baf8047a5d7744`; `worktrees/perf-guard` was removed after
  post-merge proof. The next retained slice is the narrow `G8` observability readiness
  surface.

## Previous checkpoint (2026-06-20 operations guardrails UI G6b)

The active implementation authority is now the narrow `G6b` operations guardrails slice
from `plans/2026-06-20-operations-guardrails-ui-g6b.md`. This follows the merged `G6a`
security/access-control guardrails UI slice from PR #97 at
`98d7211f705a91fe3e0963b294aeb5813916bff5`. The dirty root checkout remains preserved
candidate evidence only; continued work should happen from fresh or already-clean
worktrees under `worktrees/<short-name>`.

- **Active plan**: `plans/2026-06-20-operations-guardrails-ui-g6b.md`.
- **Purpose**: reconstruct the second retained `G6` local guardrail surface from live
  `origin/main`, focused on existing repo-owned alerting, incident/rollback,
  backup/restore, data-retention, queue/recovery, and cost-monitoring authority, before
  performance guardrails or `G8` local observability readiness.
- **Implemented scope so far**: `backend/app/operations_guardrails.py` now parses the
  repo-owned operations catalogs and runbooks, validates required alert signals,
  incident/recovery text, backup/restore references, retention classes and dry-run
  purge posture, blocked hosted scheduler status, cost categories, and repo-relative
  authority paths, and fails closed on drift. `/ui/operations-guardrails` renders a
  GET-only local operator view over those checked artifacts and links from the current
  local UI authority pages. OpenAPI stubs were regenerated for the new FastAPI UI route.
- **Current local validation**: live `origin/main` was fetched and the clean
  `codex/ops-guard` worktree was confirmed at
  `98d7211f705a91fe3e0963b294aeb5813916bff5`, matching `origin/main`. Focused G6b tests
  first failed on the missing `app.operations_guardrails` module, then passed after
  implementation (`8 passed`). Focused operations guardrails plus alerting,
  incident/rollback, data-retention, cost-monitoring, operations API, and operations UI
  route tests passed (`75 passed`). OpenAPI parity passed (`2 passed`). Focused ruff
  and mypy passed. Alert rules, incident/rollback, data-retention, cost-monitoring,
  release-readiness, and readiness-matrix validators passed. `tasks/task_queue.yaml`
  now parses as YAML after narrow syntax fixes to older unquoted scalar lines. Full
  `.\scripts\verify.ps1` first failed because the active G6b plan did not cite
  `state/LEVEL_9_10_GATE_MATRIX.md`; the plan was corrected, the readiness-matrix
  validator and focused readiness-matrix test passed, and final `.\scripts\verify.ps1`
  passed with backend tests, ruff, and mypy over `336` source files. DB smoke was skipped
  by default.
- **Known boundaries to preserve**: no hosted alert routing, pager/on-call system,
  dashboard provisioning, hosted observability, cloud billing integration, hosted backup
  policy, hosted scheduler, production operations claim, queue mutation, recovery
  execution, report retry, live connector execution, purge execution, backup/restore
  execution, alert dispatch, Docker invocation from the UI helper, runtime
  source-readiness validation from the UI helper, DS-017 approval, source/vendor
  expansion, generic AOI proof, Bologna pilot, DB schema change, public JSON API behavior
  change, report-semantics change, hosted deployment, hosted source authority, hosted
  identity/RBAC, or Level 10 completion claim.
- **Next required step**: publish the focused `codex/ops-guard` PR, wait for CI, merge
  only if local and CI proof agree, then re-check live `origin/main` before selecting
  the next retained G6 performance guardrail or G8 local observability slice.

## Previous checkpoint (2026-06-20 security guardrails UI G6a)

The active implementation authority is now the narrow `G6a` security/access-control
guardrails slice from `plans/2026-06-20-security-guardrails-ui-g6a.md`. This follows
the merged `G5` source-provenance UI slice from PR #96 at
`e27dc88e470d8fa861af8194bf330d98e9f164c1`. The dirty root checkout remains preserved
candidate evidence only; continued work should happen from fresh or already-clean
worktrees under `worktrees/<short-name>`.

- **Active plan**: `plans/2026-06-20-security-guardrails-ui-g6a.md`.
- **Purpose**: reconstruct the first retained `G6` local guardrail/auth-hardening
  surface from live `origin/main`, focused on existing access-control and security
  posture authority, before operations/performance guardrails or `G8` local
  observability readiness.
- **Implemented scope so far**: `backend/app/security_guardrails.py` now parses the
  repo-owned access-control catalog, validates current-control, production-blocker,
  secret-management, identity/RBAC, route-scope, authority-path, and validate-only
  limit invariants, and fails closed on drift. `/ui/security-guardrails` renders a
  GET-only local operator view over those checked artifacts and links from the current
  local UI authority pages. OpenAPI stubs were regenerated for the new FastAPI UI route.
- **Current local validation**: live `origin/main` was fetched and the clean
  `codex/guard-next` worktree was confirmed at
  `e27dc88e470d8fa861af8194bf330d98e9f164c1`, matching `origin/main`. Before edits,
  `py -3.12 .\scripts\source_readiness.py --priority Must --json` preserved
  `8` Must sources, `7` ready, and `1` blocked source, with DS-017 as the blocked
  source. `py -3.12 .\scripts\hosted_deployment_check.py`,
  `py -3.12 .\scripts\access_control_check.py`,
  `py -3.12 .\scripts\readiness_matrix_check.py`, and
  `py -3.12 .\scripts\private_mvp_readiness_check.py` passed before this routing
  update. Focused G6a tests first failed on the missing `app.security_guardrails`
  module, then passed after implementation (`7 passed`). Focused security/access-control
  tests passed (`20 passed`), OpenAPI parity passed (`2 passed`), focused ruff and mypy
  passed, access-control, release-readiness, readiness-matrix, and Must-source readiness
  validators passed, diff/no-deletion checks passed with only existing OpenAPI
  line-ending normalization warnings, `.\scripts\validate_workspace.ps1` passed, and
  final `.\scripts\verify.ps1` passed with backend tests, ruff, and mypy over `334`
  source files. DB smoke was skipped by default.
- **Known boundaries to preserve**: no OAuth/OIDC, user accounts, org/user RBAC,
  tenant provisioning, entitlement enforcement, secret-manager integration, automatic
  key rotation, hosted log retention, SIEM integration, connector execution, runtime
  provenance creation, evidence row creation, report creation, source registry
  mutation, DS-017 approval, paid/vendor source decision, source or county expansion,
  generic AOI proof, Bologna pilot, jurisdiction/rulepack approval, DB schema change,
  public JSON API behavior change, report-semantics change, hosted deployment, hosted
  source authority, hosted observability, or Level 10 completion claim.
- **Post-merge status**: PR #97 is merged on `origin/main` at
  `98d7211f705a91fe3e0963b294aeb5813916bff5`; `worktrees/guard-next` was removed after
  post-merge proof. The next retained slice is the narrow `G6b` operations guardrails
  surface.

## Previous checkpoint (2026-06-20 source-provenance UI G5)

The implementation authority for `G5` source-provenance UI was
`plans/2026-06-20-source-provenance-ui-g5.md`. It followed the merged `G3`
deployment-readiness UI slice from PR #94 at
`28a4d811355bb54727e6db944ddb913af56dfde1` and merged through PR #96 at
`e27dc88e470d8fa861af8194bf330d98e9f164c1`.

- **Purpose**: expose the selected-county source-provenance catalog and current
  Must-source readiness records through a local read-only `/ui/source-provenance` page
  that fails closed on catalog/registry drift and keeps DS-017/source authority blockers
  explicit before generic AOI, Bologna, or multi-geography expansion work.
- **Implemented scope so far**: focused parser and route tests cover selected-county
  catalog composition, DS-017 catalog drift, safe repo-relative read-error text, 503
  fail-closed behavior, page rendering, and live home/raw-data/deployment-readiness
  navigation links. `backend/app/source_provenance.py` reads the repo-owned
  private-MVP readiness catalog and source registry, validates request-critical
  invariants against packaged Must-source readiness records, and `/ui/source-provenance`
  renders DS-010/DS-011/DS-023 dataset, version, retrieval, connector, and out-of-scope
  expectations plus the DS-017 blocker.
- **Current local validation**: baseline `.\scripts\validate_workspace.ps1`,
  `py -3.12 .\scripts\source_readiness.py --priority Must --json`, and
  `py -3.12 .\scripts\private_mvp_readiness_check.py` passed before edits.
  Intentional red focused pytest failed for the missing `app.source_provenance` module.
  Focused source-provenance UI tests passed after implementation (`6 passed`). Focused
  ruff and mypy passed over the new module, UI route, and test. OpenAPI stubs were
  regenerated for the new FastAPI UI route, and OpenAPI parity tests passed (`2 passed`).
  Source-readiness, private-MVP, release-readiness, and readiness-matrix validators
  passed. `git diff --check` and the no-deletion audit passed with only OpenAPI
  line-ending normalization warnings. `.\scripts\validate_workspace.ps1` passed. Final
  `.\scripts\verify.ps1` passed with backend tests, ruff, and mypy over `332` source
  files. DB smoke was skipped by default.
- **Known boundaries to preserve**: no connector execution, no fixture seeding, no
  runtime provenance creation, no evidence row creation, no report creation, no source
  registry mutation, no DS-017 approval, no paid/vendor source decision, no source or
  county expansion, no Bologna pilot, no jurisdiction/rulepack approval, no DB schema
  change, no public JSON API behavior change, no report-semantics change, no auth/RBAC
  change, no hosted deployment, no hosted source authority, and no Level 10 completion
  claim.
- **Post-merge status**: PR #96 is merged on `origin/main` at
  `e27dc88e470d8fa861af8194bf330d98e9f164c1`; `worktrees/prov-next` was already
  removed after post-merge proof. The next retained slice is the narrow `G6a`
  security/access-control guardrails surface.

## Previous checkpoint (2026-06-20 deployment-readiness UI G3)

The implementation authority for `G3` deployment-readiness UI was
`plans/2026-06-20-deployment-readiness-ui-g3.md`. It followed `G2` runtime/browser
smoke reconstruction and merged through PR #94 at
`28a4d811355bb54727e6db944ddb913af56dfde1`.

- **Purpose**: expose the existing release-package, image-publication, and
  hosted-deployment catalogs through a local read-only `/ui/deployment-readiness` page
  that fails closed on catalog drift and keeps package/image/hosted blockers explicit.
- **Implemented scope**: `backend/app/deployment_readiness.py` reads the repo-owned
  deployment-path catalogs and validates request-critical invariants.
  `/ui/deployment-readiness` renders package, image, hosted runtime input/evidence,
  blocker, and validate-only limit sections.
- **Validation**: focused deployment-readiness tests passed (`9 passed`); focused mypy
  and ruff passed; OpenAPI stubs were regenerated and OpenAPI parity tests passed
  (`2 passed`); release-package, image-publication, hosted-deployment,
  release-readiness, readiness-matrix, private-MVP, and access-control validators
  passed; diff/no-deletion and workspace checks passed; local `.\scripts\verify.ps1`
  passed before merge and again after merge; PR checks were green before merge. DB smoke
  was skipped by default in local full verify.
- **Post-merge status**: PR #94 is merged on `origin/main`, the `codex/g3-deploy-readiness`
  branch was deleted by the merge workflow, and the `worktrees/g3-deploy` worktree was
  removed after post-merge proof.

## Previous checkpoint (2026-06-20 runtime/browser smoke reconstruction)

The implementation authority for `G2` runtime/browser smoke reconstruction was
`plans/2026-06-20-runtime-browser-smoke-g2.md`. This retained product/control slice
followed `G3b` selected-county source-provenance catalog, which merged through PR #92
at `cc272d0de492c424ff1b3ad715f25b25587c9e53`. The dirty root checkout remains
preserved candidate evidence only; the slice was opened from live `origin/main` in
`worktrees/g2-smoke`.

- **Active plan**: `plans/2026-06-20-runtime-browser-smoke-g2.md`.
- **Purpose**: rebuild local runtime and browser smoke around the accepted G1 UI
  surface: account-free default local operation, read-only `/ui/raw-data`, explicit
  default-disabled `/ui/auth*` checks, opt-in protected auth checks, and DB-backed
  deployment smoke composition.
- **Implemented scope so far**: focused tests now cover default runtime smoke labels,
  default-disabled auth route 404s, opt-in API-key and reviewer auth checks, browser
  smoke route contract updates, and deployment-smoke composition. `scripts/ui_runtime_smoke.py`
  and `scripts/ui_browser_smoke.mjs` now include `/ui/raw-data`, keep protected auth
  checks opt-in, and make default-disabled auth route expectations explicit.
  `scripts/run_deployment_smoke.ps1` and `.sh` now run DB-backed UI runtime smoke with
  `BUN-slope`, same-area compare, and `postgres+object_store` artifact persistence.
  A live browser smoke failure also exposed `/ui/raw-data` mobile page overflow; the
  raw-data page now keeps dense raw tables inside a scrollable wrapper on mobile.
- **Current local validation**: intentional red focused pytest failed on the stale G2
  contract (`10 failed, 16 passed`). Final focused raw-data/smoke/deployment tests
  passed (`31 passed`), `node --check .\scripts\ui_browser_smoke.mjs` passed, release
  readiness and readiness-matrix validators passed, focused ruff and mypy passed,
  `.\scripts\run_deployment_smoke.ps1` passed against DB-backed Compose/Postgres, and
  `.\scripts\run_ui_browser_smoke.ps1 -BaseUrl http://127.0.0.1:18081 -Mode both`
  passed in headed and headless Chrome after starting a temporary local Uvicorn server.
  `git diff --check`, no-deletion check, workspace validation, and final
  `.\scripts\verify.ps1` passed. Full verify ran backend tests, ruff, and mypy over
  `328` source files; DB smoke was skipped by default in the full verify gate, while
  deployment smoke supplied the DB-backed runtime proof for this slice.
- **Known boundaries to preserve**: no new readiness/provenance/guardrail/deployment/
  production-authority/dossier UI pages, no fixture seeding from default smoke routes,
  no live connectors, no source/vendor expansion, no DS-017 approval, no DB schema
  change, no public JSON API contract change, no report-semantics change, no hosted
  deployment claim, no hosted identity/RBAC claim, and no Level 10 completion claim.
- **Post-merge status**: PR #93 merged at
  `beedde0990e598beaa3ccefd99392fe5d9856e1f`; the next retained slice is the narrow
  `G3` deployment-readiness UI surface.

## Previous checkpoint (2026-06-20 selected-county source-provenance catalog)

The implementation authority for `G3b` selected-county source-provenance catalog was
`plans/2026-06-20-selected-county-source-provenance-catalog.md`. That retained
product/control slice followed `G1b` raw-data inventory UI and merged through PR #92 at
`cc272d0de492c424ff1b3ad715f25b25587c9e53`. The dirty root checkout remains preserved
candidate evidence only; the slice was opened from live `origin/main` in
`worktrees/prov-cat`.

- **Active plan**: `plans/2026-06-20-selected-county-source-provenance-catalog.md`.
- **Purpose**: add a validate-only selected-county source-provenance expectation
  catalog for DS-010, DS-011, and DS-023 across Buncombe, Chatham, and Brunswick so
  future raw-data/source-provenance UI and report-path work has a machine-checkable
  source of truth for dataset, version, retrieval, connector, and out-of-scope
  expectations.
- **Implemented scope so far**: focused tests now cover the provenance catalog shape,
  DS-017 exclusion, connector cross-checking against selected-county source scope, and
  Buncombe DS-023 out-of-scope expectations. `config/private_mvp_beta_readiness.yaml`
  now declares `selected_county_source_provenance_scope`; the private-MVP readiness
  checker validates that scope against selected source scope and county manifest scope.
  `MANIFEST.md`, `docs/IMPLEMENTATION_READINESS.md`, and `docs/runbooks/mvp_operator.md`
  route future source/provenance work to the catalog without claiming runtime
  hydration, live vendor execution, DS-017 approval, hosted deployment, or identity/RBAC
  completion.
- **Current local validation**: intentional red focused pytest failed for the missing
  `selected_county_source_provenance_scope` section; after adding the catalog and
  validator, focused private-MVP readiness tests passed (`31 passed`). Private-MVP,
  release-readiness, readiness-matrix, Must-source readiness, focused ruff, focused
  mypy, wrapper, diff/no-deletion, workspace validation, and full `.\scripts\verify.ps1`
  passed. Full verify ran backend tests, ruff, and mypy over `328` source files; DB
  smoke was skipped by default.
- **Known boundaries to preserve**: no connector execution, no fixture/runtime seeding,
  no provenance record creation, no DB requirement, no DS-017 approval, no source/vendor
  expansion, no public API/UI/runtime semantics change, no report semantics change, no
  auth/security boundary change, no hosted deployment, no full identity/RBAC, and no
  Level 10 completion claim.
- **Post-merge status**: PR #92 is merged; `G2` runtime/browser smoke reconstruction is
  now the active retained slice.

## Previous checkpoint (2026-06-20 raw-data inventory UI)

The active implementation authority is `G1b` raw-data inventory UI from
`plans/2026-06-20-raw-data-inventory.md`. This is the next retained
product/control slice after `G1a` account-free local auth posture merged through
PR #90 at `6d8b9d66019453e99628e21d595a7a97b149d41c`. The dirty root checkout remains
preserved candidate evidence only; this slice was opened from live `origin/main` in
`worktrees/raw-inv`.

- **Active plan**: `plans/2026-06-20-raw-data-inventory.md`.
- **Purpose**: add a local read-only `/ui/raw-data` route and `/ui/` runtime inventory
  summary over current source, area, evidence, claim, report-run, report-job,
  connector-review, and live-connector records.
- **Implemented scope so far**: focused tests cover populated raw inventory rendering,
  empty-runtime read-only GET behavior, home link/count summary, and fail-closed home
  summary behavior when a collector raises. `EvidenceService.list_all`, `ApiServices`
  claim-service exposure, and bounded report-run contract listing were added as
  read-only service seams. The UI route renders unavailable rows per failed collector
  and records that it does not seed fixtures, create reports, run connectors, create
  accounts, approve DS-017, or prove hosted/source-readiness authority.
- **Current local validation**: intentional red focused pytest failed for missing
  `/ui/raw-data`, missing home link/summary, and absent evidence list-all service read;
  focused raw-data inventory tests passed (`4 passed`); focused ruff and focused mypy
  over the touched service/UI/test files passed; release-readiness and readiness-matrix
  validators passed; the first full `.\scripts\verify.ps1` failed only because
  generated OpenAPI stubs had not yet been refreshed for `/ui/raw-data`; after
  `scripts/export_openapi_stub.py`, OpenAPI parity tests passed (`2 passed`) and final
  `.\scripts\verify.ps1` passed with backend tests, ruff, and mypy over `328` source
  files. DB smoke was skipped by default.
- **Known boundaries to preserve**: no hidden seeding, no connector execution, no report
  creation from GET, no source-rights or DS-017 decision, no DB schema change, no public
  JSON API contract change, no report-semantics change, no hosted deployment, no
  OAuth/OIDC, no user accounts, no full RBAC, and no Level 10 completion claim.
- **Next required step**: publish the focused `codex/raw-inv` PR, wait for CI, merge
  only if local and CI proof agree, then re-check live `origin/main` and re-rank the
  next retained slice.

## Previous checkpoint (2026-06-20 account-free local auth posture)

The active implementation authority is `G1a` account-free local auth posture from
`plans/2026-06-20-account-free-local-auth.md`. This is the next retained
product/control slice after `G7a` package-manifest CI gate merged through PR #88 and
`G3a` source-readiness module extraction merged through PR #89. The dirty root checkout
remains preserved candidate evidence only; this slice was opened from live
`origin/main` at `7204d9fbba182eb21fb32176449be3d0d174de71`.

- **Active plan**: `plans/2026-06-20-account-free-local-auth.md`.
- **Purpose**: make default local/dev/development/test browser operation account-free
  by not mounting `/ui/auth*` login/session setup routes when `REQUIRE_API_KEY=false`,
  and by keeping those paths absent from default OpenAPI output.
- **Implemented scope so far**: focused tests prove default local `/ui/auth*` paths
  return 404 and are absent from default OpenAPI while protected local mode still
  exposes `/ui/auth`; `backend/app/main.py` conditionally mounts `ui_auth_router`;
  shared UI helpers avoid linking default local pages to unmounted auth setup routes;
  access-control catalog/checker/tests, `DESIGN.md`, `.env.example`, and operator
  runbooks record the same default-local versus protected-mode boundary; default
  OpenAPI stubs were regenerated to remove `/ui/auth*`.
- **Current local validation**: intentional red auth-route pytest failed for the
  expected default local `/ui/auth` 200 before implementation; focused UI auth tests
  passed (`37 passed`); focused UI auth plus access-control artifact tests passed
  (`50 passed`); generated OpenAPI parity tests passed (`2 passed`);
  `scripts/access_control_check.py`, release-readiness, readiness-matrix, focused
  ruff/mypy, diff/no-deletion, and workspace validation passed; the first full verify
  exposed default-local UI route tests still using `/ui/auth/reviewer`; after replacing
  those tests with direct reviewer-session cookies and hiding dead auth links, final
  `.\scripts\verify.ps1` passed with backend tests, ruff, and mypy over `327` source
  files. DB smoke was skipped by default.
- **Known boundaries to preserve**: no auth module deletion, no JSON/API API-key
  weakening, no reviewer-scope or CSRF weakening, no OAuth/OIDC, no user accounts, no
  full RBAC, no hosted identity, no hosted deployment, no source/connector/evidence/
  claim/report/release-package behavior, no DB schema change, and no DS-017 authority.
- **Next required step**: publish the focused `codex/auth-posture` PR, wait for CI,
  merge only if local and CI proof agree, then re-check live `origin/main` and re-rank
  the next retained slice.

## Previous checkpoint (2026-06-20 source-readiness module extraction)

The active implementation authority is `G3a` source-readiness packaged-module
extraction from `plans/2026-06-20-source-readiness-module.md`. This is the next
retained product/control slice after the `G7a` package-manifest CI gate merged through
PR #88. The dirty root checkout remains preserved candidate evidence only; this slice
was opened from live `origin/main` at
`8b0e750ec13d6289af279b06716e9cddbaaf67a0`.

- **Active plan**: `plans/2026-06-20-source-readiness-module.md`.
- **Purpose**: make `backend/app/source_registry/readiness.py` the packaged authority
  for source-readiness record construction and freshness fail-closed behavior while
  keeping `scripts/source_readiness.py` as the validate-only CLI wrapper.
- **Implemented scope so far**: an intentional red test proved the packaged module was
  absent; the readiness dataclasses and record/freshness helpers were extracted into
  `backend/app/source_registry/readiness.py`; the CLI now delegates to that module; and
  source-readiness tests import the package module directly while subprocess tests
  continue proving CLI JSON output.
- **Current local validation**: focused source-readiness tests passed (`17 passed`);
  focused alerting/source-readiness compatibility tests passed (`18 passed`);
  Must-source CLI JSON and `--require-ready` paths passed and preserved
  `sources=8 ready=7 blocked=1`; release-readiness and readiness-matrix validators
  passed after the plan was corrected to cite `state/LEVEL_9_10_GATE_MATRIX.md`;
  focused ruff and mypy passed; `git diff --check`, no-deletion audit,
  `.\scripts\validate_workspace.ps1`, and final `.\scripts\verify.ps1` passed with
  backend tests, ruff, and mypy over `327` source files. DB smoke was skipped by
  default.
- **Known boundaries to preserve**: no source-readiness count changes, no DS-017
  approval, no source-rights policy change, no connector behavior change, no UI/public
  API change, no DB schema change, no release-package/publishing behavior change, and
  no hosted/source/tenant authority claim.
- **Merge status**: PR #89 merged at
  `7204d9fbba182eb21fb32176449be3d0d174de71`; detached post-merge source-readiness,
  release-readiness, readiness-matrix, workspace, and full verification proof passed
  before selecting `G1a`.

## Previous checkpoint (2026-06-20 package-manifest CI gate)

The active implementation authority is `G7a` package-manifest CI gate from
`plans/2026-06-20-package-manifest-ci.md`. This is the first retained product/control
slice after `REC-001` repository-state reconciliation. Live `origin/main` was refreshed
at `52b167a96643befa863f9501d1171385c4a25383` before `worktrees/pkg-manifest` was
created on `codex/pkg-manifest`; no open GitHub PRs were present at slice start. The
dirty root checkout remains preserved candidate evidence only.

- **Active plan**: `plans/2026-06-20-package-manifest-ci.md`.
- **Purpose**: add post-build verification for generated local release-package manifests
  and an additive read-only CI job that validates the package boundary, builds an
  ignored local package, and checks the generated manifest against the ZIP.
- **Implemented scope**: `scripts/package_manifest_check.py` validates external manifest
  schema/source/package id, local-only limit flags, ZIP SHA-256, embedded manifest
  parity, declared ZIP entries, file sizes, file hashes, duplicate paths, undeclared
  entries, and `config/release_package.yaml` include/exclude boundaries. Windows/POSIX
  wrappers require an existing manifest path. `scripts/release_package_check.py` now
  fails closed if the checker, wrappers, or runbook coverage drift.
- **Release-readiness and CI authority**: `config/release_readiness.yaml` maps the
  existing `release_package` check to `release-package-manifest`; the CI job uses
  read-only repository permissions, runs the release-package boundary validator, builds
  a local package under `local_artifacts/releases`, and runs the package-manifest
  checker against the generated sibling manifest.
- **Current local validation**: focused package/release-readiness tests passed
  (`32 passed`) after an intentional red run failed for the expected missing checker,
  wrappers, docs, CI job, and release-readiness mapping. Focused ruff passed; focused
  mypy passed over the touched package/readiness scripts and tests; release-package and
  release-readiness validators passed through direct, Windows, and POSIX paths; local
  generated-package manifest checks passed for both PowerShell and POSIX package proof
  paths; Python compile, PowerShell parser, `git diff --check`, no-deletion audit,
  `.\scripts\validate_workspace.ps1`, and final `.\scripts\verify.ps1` passed. DB smoke
  was skipped by default.
- **Known boundaries to preserve**: this does not publish, push, sign, attest, deploy,
  approve DS-017, change source-rights policy, change public APIs, change DB schema,
  change report semantics, or claim hosted release authority. Generated package
  artifacts remain ignored under `local_artifacts/releases`.
- **Merge status**: PR #88 merged at
  `8b0e750ec13d6289af279b06716e9cddbaaf67a0`; detached post-merge package and full
  verification proof passed before selecting `G3a`.

## Previous checkpoint (2026-06-20 repository-state reconciliation)

The active implementation authority is Lane 1 repository-state reconciliation and
selective landing. Live `origin/main` remains the only default product authority; the
dirty root checkout contains recoverable local candidate work that must be classified
and selectively revalidated before any slice is treated as merged functionality.

- **Active plan**: `plans/2026-06-20-lane1-reconciliation.md`.
- **Purpose**: reconcile live `R-022` authority with material local uncommitted
  readiness/UI/control-plane candidate work without landing the dirty workspace as a
  single broad change or promoting local state prose to repo truth.
- **Live authority envelope**: refreshed `origin/main`, local `main`, and dirty-root
  `codex/r026-raw-readiness-ui` all point at
  `c3364ea01605cef09e03da6da8551fa4d1a155e8`; ahead/behind is `0/0`; no open GitHub
  PRs were found for `benjmcd/land-dd`.
- **Candidate envelope**: dirty root has `53` tracked modified files, `75` untracked
  files, and `0` tracked deletions relative to `origin/main`. The local candidate stack
  includes later `R-023` through `R-056` readiness/UI claims, but those remain
  `LOCAL_UNCOMMITTED` candidate evidence until decomposed and re-landed from clean
  worktrees.
- **Current authority surfaces**:
  `plans/2026-06-20-lane1-reconciliation.md`, `plans/README.md`,
  `tasks/task_queue.yaml`, `state/reconciliation-inventory.md`,
  `state/reconciliation-slices.md`, `state/r023-review.md`,
  `state/reconciliation-dispositions.md`, `state/PROJECT_STATE.md`,
  `state/WORKLOG.md`, and `state/VALIDATION_LOG.md`.
- **Known boundaries to preserve**: do not reset, clean, delete, rebase, overwrite, or
  destructively partition the dirty root candidate stack; do not publish
  coordination-only `state/agent-inbox/*`; do not change product behavior, DB schema,
  source registry decisions, public APIs, auth/security boundaries, report semantics,
  claim/rule behavior, hosted/source/identity authority, DS-017 status, or Level 10
  claims during the control-plane slice.
- **Next required step**: validate and merge the `REC-001` control-plane artifacts
  before product landing work. The first retained product slices should be opened in
  separate clean worktrees from live `origin/main`; current disposition review ranks
  package-manifest/CI, source-readiness extraction, local account-free/auth posture,
  and raw-data inventory as the earliest coherent candidates. Do not copy dirty-root
  `backend/app/api/ui.py`, smoke scripts, OpenAPI mirrors, or state prose wholesale.

## Current checkpoint (2026-06-18 error-state/no-leak hardening)

Audit-retention proof hardening is complete. The active implementation authority now
points at error-state/no-leak hardening: strengthen repo-local proof that current
API/UI error and recovery surfaces do not leak stack traces, secrets, raw connector
payloads, local paths, or internal implementation details while preserving first-class
source-failure evidence and without claiming hosted error/log review.

- **Active plan**: `plans/2026-06-18-error-state-no-leak-hardening.md`.
- **Purpose**: harden the next repo-local security/error-boundary proof after
  audit-retention proof while preserving the Level 9/10 distinction between local
  evidence and hosted production authority.
- **R-022 implemented proof**: shared user-facing error safety now lives in
  `backend/app/core/error_safety.py`; failed-report API/list/detail and failed-report
  UI detail render safe summaries instead of raw stored `error_msg`; live-connector
  job API/UI responses return safe error, URL, and allowlisted payload summaries instead
  of raw `last_error`, query-bearing request URLs, or arbitrary job payload dumps;
  connector-review queue API/UI last-error surfaces use safe summaries; operations
  recovery preview delegates to the same shared helper; and raw stored job/queue
  failure evidence remains available internally for inspection.
- **R-022 validation**: threat/proxy audit checker and wrapper passed;
  release-readiness and readiness-matrix validators passed; focused no-leak
  regressions passed; full affected API/UI/threat-proxy artifact pytest set passed
  with one existing skip; focused ruff and mypy passed; `git diff --check` passed; no
  deleted files were reported; and full `.\scripts\verify.ps1` passed with backend
  tests, ruff, and mypy over `325` source files. DB smoke was skipped by default.
- **Completed immediately prior**: `R-021` removed the silent hard-coded retention
  fallback from `scripts/purge_audit_events.py`, made every purge validate
  `config/data_retention.yaml` before dry-run or apply, kept `--retention-days` as a
  numeric operator override only after catalog validation, added runtime data-retention
  checker proof for catalog defaults and event allowlist parity, and hardened DB-gated
  apply tests so they require `AUDIT_PURGE_TEST_DB_ISOLATED=1` plus zero pre-existing
  eligible in-scope audit rows before deletion proof can run.
- **R-021 validation**: data-retention checker and wrapper passed; purge dry-run
  wrapper passed against an isolated local DB; focused retention tests, ruff, and mypy
  passed; isolated DB-gated purge tests passed with `RUN_DB_SMOKE=1`,
  `AUDIT_PURGE_TEST_DB_ISOLATED=1`, and `DATABASE_URL_SYNC` pointed at the disposable
  DB; release-readiness and readiness-matrix validators passed; `git diff --check`
  passed; no deleted files were reported; and full `.\scripts\verify.ps1` passed.
- **Current authority surfaces**: `state/PRODUCTION_AUTHORITY_PACKET.md`,
  `state/POST_RC_AUTHORITY_SPLIT.md`, `state/LEVEL_9_10_GATE_MATRIX.md`,
  `plans/2026-06-18-error-state-no-leak-hardening.md`,
  `plans/2026-06-18-audit-retention-proof-hardening.md`, `plans/README.md`,
  `tasks/task_queue.yaml`, `config/threat_proxy_audit.yaml`,
  `docs/runbooks/threat_proxy_audit.md`, `scripts/threat_proxy_audit_check.py`,
  `backend/app/api/ui*.py`, `backend/app/api/reports.py`,
  `backend/app/api/connectors.py`, `backend/app/api/operations.py`,
  `backend/app/api/ui_live_connector_jobs.py`, `backend/app/api/ui_review.py`,
  `backend/app/core/error_safety.py`, `backend/app/operations/recovery_preview.py`,
  and existing UI/API/threat-proxy tests.
- **Known boundaries preserved**: no DS-017 vendor/license/cost decision, no DS-017
  connector, no hosted deployment or hosted alert route, no registry image push, no
  production SLO/capacity claim, no new county/source/rulepack, no full user identity
  or RBAC, no OAuth/OIDC, no hosted scheduler, no hosted log-retention/export/SIEM, no
  hosted error/log review, no recommendation/ranking semantics, no
  demographic/protected-class scoring, no legal/security review claim, no secret
  writes, no committed measured runtime artifacts, and no Level 10 completion claim.

## Previous checkpoint (2026-06-18 audit-retention proof hardening)

`R-021` completed audit-retention proof hardening after `R-020` route-scope/RBAC
handoff coverage. It strengthened repo-local audit purge safety and proof without
provisioning hosted scheduler, hosted log-retention/export/SIEM, user-bound identity
audit, OAuth/OIDC, full RBAC, DS-017 entitlement, or hosted production workload
authority.

## Previous checkpoint (2026-06-18 jurisdiction/rulepack checklist dry run)

`R-019` completed the jurisdiction/rulepack checklist dry run after `R-018` proved the
threat/proxy audit guard. It added validate-only checklist dry-run proof and kept every
future expansion item either repo-confirmed or explicitly unresolved without selecting
or approving any geography, rulepack, source, connector, DS-017 path, hosted
production path, legal/security review, or identity/RBAC work.

## Previous checkpoint (2026-06-18 threat-model/proxy audit update)

`R-018` completed the threat/proxy audit update after `R-017` proved compare/diff
workflow smoke. It added repo-local drift controls for security, access-control,
protected-class, demographic-proxy, residential-steering, recommendation/ranking,
suitability, source-rights, overclaim, and error-leakage boundaries without replacing
external security review, legal review, hosted IdP/RBAC, production error/log review,
DS-017 entitlement work, billing, alerting, or deployment authority.

## Previous checkpoint (2026-06-18 compare/diff workflow smoke)

`R-017` completed the compare/diff workflow smoke after `R-016` rehearsed local
performance. It extended the release-candidate UI runtime smoke to follow two approved
selected-county reports through compare UI, compare API, and same-area diff API checks,
and kept compare/diff scoped to report summaries and caveated change review.

## Previous checkpoint (2026-06-18 representative performance rehearsal)

`R-016` completed the representative local performance rehearsal after `R-015` proved
the release-candidate package boundary. It kept measured artifacts ignored under
`local_artifacts/`, fixed the sentinel source concurrency race described above, and did
not promote hosted SLO/capacity, DS-017, hosted deployment, IdP/RBAC, billing, alerting,
image publication, or secret-manager blockers.

## Previous checkpoint (2026-06-18 source review cadence consistency)

The source freshness review-drift guard routed work to source review cadence
consistency: make source-review cadence prose and runbook guidance align with the
repo-local 90-day Must-source freshness horizon without starting hosted alerting or
changing source approval decisions. `R-014` completed that guard and routed the next
active lane to local release-candidate package rehearsal.

## Previous checkpoint (2026-06-18 source freshness review-drift guard)

The source-rights export guard routed work to a source freshness review-drift guard:
add repo-local fail-closed proof that Must-source registry freshness and review
metadata cannot silently drift stale while still being treated as production-ready.
`R-013` completed that guard and routed the next active lane to source review cadence
consistency.

## Previous checkpoint (2026-06-18 source-rights export guard)

The production authority packet routed the next repo-local lane to a source-rights
export guard: prove source-rights metadata controls report/export exposure for
restricted or vendor-derived fields without approving DS-017 or starting hosted
production work. `R-012` completed that guard and routed the next active lane to
source freshness review-drift proof.

## Previous checkpoint (2026-06-18 production authority packet)

The post-RC authority split routed work to a production authority packet: turn the
remaining external blockers into explicit decision/evidence requests before starting
hosted, paid-source, full identity/RBAC, secret-manager, billing, alerting,
image-publication, or production workload work. DS-017 was first because it is the only
current Must-source readiness blocker. `state/PRODUCTION_AUTHORITY_PACKET.md` completed
that packet and selected source-rights export guarding as the next repo-local lane.

## Current checkpoint (2026-06-18 spatial runtime query-plan proof)

The active implementation authority now points at the next unblocked `L10-PERF-003`
runtime-evidence slice selected from the Level 9/10 gate matrix.

- **Active plan**: `plans/2026-06-18-spatial-runtime-plan-proof.md`.
- **Purpose**: add an opt-in DB-enabled runtime `EXPLAIN ANALYZE` harness for the
  configured selected-county private-MVP spatial workloads without making static
  release-readiness validation open a DB connection or seed runtime state.
- **Current authority surfaces**: `state/LEVEL_9_10_GATE_MATRIX.md`,
  `config/spatial_query_plan.yaml`, `scripts/spatial_query_plan_check.py`,
  `scripts/spatial_query_plan_runtime_check.py`,
  `docs/runbooks/performance.md`, `docs/runbooks/release_readiness.md`,
  `plans/README.md`, and `tasks/task_queue.yaml`.
- **Known boundaries preserved**: no DB schema change, no fixture/source seeding in
  validate-only actions, no default DB runtime gate, no hosted performance/SLO claim,
  and no Level 10 completion claim.
- **Design direction**: runtime evidence must require a caller-provided local or
  release-candidate database and `area_id`, run configured plan-review SQL in a
  read-only transaction, fail closed when the expected target GIST index is absent from
  JSON plan evidence, and write a JSON result only when explicitly requested.
- **Implemented proof**: `spatial_query_plan_runtime_result_v1` runtime checker and
  Windows/POSIX wrappers now run the configured statements as read-only
  `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` checks against a caller-supplied DB/area.
- **Validation**: static checker and Windows wrapper passed, runtime Windows wrapper
  passed against an isolated local workload, focused spatial/performance/release/matrix
  artifact tests passed (`46 passed`), release-readiness and readiness-matrix validators
  and wrappers passed, focused ruff/mypy passed, `git diff --check` passed, no deleted
  files were reported, isolated DB smoke passed on port `55450`, default
  `.\scripts\verify.ps1` passed, and DB-enabled `.\scripts\verify.ps1` passed on a clean
  isolated DB at port `55451`. The runtime evidence observed `parcels_geom_gix`,
  `reference_features_geom_gix`, and `observations_geom_gix`.

## Current checkpoint (2026-06-18 spatial query SQL contract guard)

The active implementation authority now points at a follow-up hardening slice for the
static spatial query-plan proof.

- **Active plan**: `plans/2026-06-18-spatial-query-sql-contract.md`.
- **Purpose**: correct and guard the configured spatial plan-review SQL so static
  release-readiness proof cannot name non-existent canonical schema columns.
- **Current authority surfaces**: `db/migrations/0001_initial_spine.sql`,
  `config/spatial_query_plan.yaml`, `scripts/spatial_query_plan_check.py`,
  `backend/tests/test_spatial_query_plan_artifacts.py`, `plans/README.md`, and
  `tasks/task_queue.yaml`.
- **Known boundaries preserved**: no DB schema change, no default live DB plan execution,
  no seeded runtime state, no generated artifacts, no hosted performance/SLO claim, and
  no Level 10 completion claim.
- **Issue fixed**: the pre-fix static observations workload selected
  `o.observation_id`, but canonical `evidence.observations` uses `evidence_id`.
- **Implemented proof**: `area_observation_intersections` now selects canonical
  `o.evidence_id`, and `scripts/spatial_query_plan_check.py` validates configured
  review statements against canonical DDL-derived table/column identifiers, aliases,
  primary-key projections, spatial predicates, area filters, and expected index/table
  relationships.
- **Validation**: spatial query-plan checker and Windows wrapper passed, focused
  spatial artifact tests passed (`10 passed`), release-readiness and readiness-matrix
  validators passed, focused spatial/performance/release/matrix artifact tests passed
  (`35 passed`), focused ruff/mypy passed, `git diff --check` passed, no deleted files
  were reported, and default `.\scripts\verify.ps1` passed with backend tests, ruff,
  and mypy over `318` source files. DB smoke was skipped by default.

## Current checkpoint (2026-06-18 spatial query-plan proof)

The active implementation authority now points at the next unblocked Level 10
performance-readiness slice selected from the Level 9/10 gate matrix.

- **Active plan**: `plans/2026-06-18-spatial-query-plan-proof.md`.
- **Purpose**: turn the current manual spatial query-plan review gap into a repo-local
  validate-only contract/checker for selected private-MVP spatial workloads without
  claiming hosted production performance readiness.
- **Current authority surfaces**: `state/LEVEL_9_10_GATE_MATRIX.md`,
  `db/migrations/0001_initial_spine.sql`, `docs/runbooks/performance.md`,
  `scripts/release_readiness_check.py`, `scripts/readiness_matrix_check.py`,
  `config/release_readiness.yaml`, `plans/README.md`, and `tasks/task_queue.yaml`.
- **Known boundaries preserved**: no DB schema change, no live DB query-plan gate by
  default, no seeded runtime state, no committed measured plan artifacts, no hosted
  performance/SLO claim, and no Level 10 completion claim.
- **Canonical DDL facts**: the initial PostGIS spine already defines GIST indexes for
  `core.areas.geom`, `core.area_versions.geom`, `geo.parcels.geom`,
  `geo.reference_features.geom`, and `evidence.observations.geometry`.
- **Implemented proof**: `spatial_query_plan_v1` contract, validate-only checker,
  Windows/POSIX wrappers, release-readiness composition, and performance/release runbook
  boundaries. The matrix keeps `L10-PERF-003` at `PARTIAL` until representative
  DB-enabled `EXPLAIN ANALYZE` evidence exists.
- **Validation so far**: spatial query-plan checker and Windows wrapper passed,
  release-readiness and readiness-matrix validators/wrappers passed, focused
  spatial/performance/release/matrix artifact tests passed (`32 passed`), ruff passed,
  mypy passed, `git diff --check` passed, no deleted files were reported, and full
  `.\scripts\verify.ps1` passed with workspace validation, backend tests, ruff, and
  mypy over `318` source files. DB smoke was skipped by default.

## Current checkpoint (2026-06-18 performance baseline evidence)

The active implementation authority now points at the next unblocked Level 10
readiness slice selected from the Level 9/10 gate matrix.

- **Active plan**: `plans/2026-06-18-performance-baseline-evidence.md`.
- **Purpose**: make release-candidate performance regression evidence observable and
  repeatable for the selected-county private-MVP runtime without claiming hosted
  production performance readiness.
- **Current authority surfaces**: `state/LEVEL_9_10_GATE_MATRIX.md`,
  `config/performance_baseline.yaml`, `scripts/performance_baseline_check.py`,
  `docs/runbooks/load_testing.md`, `docs/runbooks/performance.md`,
  `scripts/load_test_runner.py`, `scripts/run_load_test.ps1`,
  `scripts/run_load_test.sh`, `scripts/release_readiness_check.py`,
  `scripts/readiness_matrix_check.py`, `config/release_readiness.yaml`,
  `plans/README.md`, and `tasks/task_queue.yaml`.
- **Known boundaries preserved**: no hosted load test, no production SLO, no CI
  live-load gate, no new dependency, no committed measured runtime artifact, and no
  Level 10 completion claim.
- **Implemented proof**: local release-candidate baseline contract
  `performance_baseline_v1`; optional `load_test_result_v1` JSON output from the
  existing load-test runner; result-directory support in Windows/POSIX wrappers;
  validate-only baseline checker; release-readiness composition; runbook boundaries.
- **Validation so far**: performance-baseline checker and Windows wrapper passed,
  load-test validate-only wrapper passed, focused load/performance/release/matrix
  artifact tests passed (`40 passed`), ruff passed, mypy passed, release-readiness
  validator passed, readiness-matrix validator passed, `git diff --check` passed, and
  full `.\scripts\verify.ps1` passed with workspace validation, backend tests, ruff,
  and mypy over `317` source files. DB smoke was skipped by default.

## Current checkpoint (2026-06-18 Level 9/10 readiness reconciliation)

The active implementation authority now points at the post-private-MVP
readiness-reconciliation pass instead of the completed UI CSRF route-coverage slice.

- **Active plan**: `plans/2026-06-18-level9-10-readiness-reconciliation.md`.
- **Purpose**: reconcile Level 9 product-grade MVP evidence and Level 10 production-grade
  blockers before selecting the next unblocked implementation slice.
- **Current authority surfaces**: `MILESTONE_MAP.md`,
  `config/private_mvp_beta_readiness.yaml`, `config/release_readiness.yaml`,
  `config/hosted_deployment.yaml`, `plans/README.md`, and `tasks/task_queue.yaml`.
- **Known production blockers preserved**: hosted deployment attestation, registry image
  publication attestation, hosted billing reconciliation, non-ready Must sources, full
  user auth/RBAC, hosted alerting, external secret-manager integration, and hosted
  platform/TLS/database authority.
- **Validation**: private-MVP, release-readiness, hosted-deployment, access-control,
  Must-source readiness, and readiness-matrix validators passed; Must-source readiness
  remains `sources=8 ready=7 blocked=1` with DS-017 blocked. Focused matrix artifact
  tests, ruff, mypy, and whitespace checks also passed.
- **Gate matrix**: `state/LEVEL_9_10_GATE_MATRIX.md` now classifies every Level 9 and
  Level 10 gate against current evidence and names the next unblocked pass.
- **Static guard**: `scripts/readiness_matrix_check.py` validates the matrix covers every
  Level 9/10 gate from `MILESTONE_MAP.md`, pins the canonical routing commands, and
  prevents high-risk hosted/source/auth/security/performance gates from being promoted
  without an intentional checker update.
- **Limit**: this checkpoint changes planning/readiness-state artifacts only; it does
  not claim Level 10 completion or create hosted infrastructure.

## Current checkpoint (2026-06-18 UI CSRF route coverage)

Cookie-authorized UI mutation routes now have route-level CSRF regression coverage and
static access-control pinning.

- **Route-level CSRF proofs**: reviewer-session POST coverage now pins missing-CSRF
  `403` behavior for `/ui/intake`, `/ui/report-runs/{report_run_id}/retry`,
  connector review `reject`, `requeue`, `cancel`, `resume-report`, and
  `/ui/operations/recovery-preview`.
- **Success-side coverage**: connector review `reject`, `requeue`, `cancel`,
  `resume-report`, and operations recovery-preview also have valid reviewer-session
  CSRF tests, so the route pins prove both fail-closed rejection and accepted-token
  continuity.
- **Header-vs-cookie boundary**: the tests preserve the existing distinction that
  reviewer credentials submitted in form fields do not require CSRF, while reviewer
  session cookies do.
- **Static guard**: `scripts/access_control_check.py` now reads UI review and
  operations route tests and requires the new named route-level CSRF rejection and
  accepted-token proofs, so the coverage cannot be removed without failing the
  access-control gate.
- **Validation**: focused UI route/review/operations CSRF tests, access-control
  artifact coverage, ruff, mypy, `scripts/access_control_check.py`, and
  `.\scripts\verify.ps1` passed.

## Current checkpoint (2026-06-18 report artifact path trust)

DB-backed report artifact delivery now treats the configured object-store root as the
artifact file trust boundary.

- **Object-store root authority**: `SqlAlchemyReportRunRepository` resolves
  `OBJECT_STORE_ROOT`, accepts only artifact paths under that root, and requires the
  persisted artifact filename to match `{report_run_id}.json`.
- **Artifact body consistency**: DB-backed report reloads now reject artifact JSON whose
  `report_run_id` does not match the report row being read.
- **Artifact endpoint hardening**: `GET /report-runs/{report_run_id}/artifact` no
  longer performs a second filesystem read from URIs embedded in the artifact payload;
  it returns the validated report contract already loaded by the repository.
- **API failure mode**: report API reads now translate artifact path trust-boundary
  failures to `409` for authorized callers instead of leaking implementation
  exceptions from the repository; workspace-scoped reads check DB row ownership before
  loading artifact files, so wrong-workspace callers still receive `404`.
- **Tamper regression**: DB-gated artifact export coverage now updates an approved
  report row to point outside `OBJECT_STORE_ROOT` and verifies artifact delivery fails
  closed with `409`; it also verifies in-root wrong filenames fail with `409` for the
  owning workspace and `404` for another workspace. Repository coverage rejects
  unexpected artifact filenames and artifact JSON whose `report_run_id` differs from
  the DB row.
- **Validation**: focused in-memory artifact tests, focused DB-gated artifact tests,
  report repository/export tests, ruff, mypy, default `.\scripts\verify.ps1`, and
  DB-enabled `.\scripts\verify.ps1` passed on isolated Postgres port `55449`.

## Current checkpoint (2026-06-18 connector review workspace scope)

Legacy connector review mutations and connector-derived report creation now preserve
workspace boundaries instead of relying on reviewer credentials alone.

- **Scoped review mutations**: legacy
  `/connector-runs/{ingest_run_id}/review-actions/*` routes now require request
  workspace/user identity and use workspace-scoped connector review queue lookup before
  approve, fixture-fix request, requeue, or cancel transitions.
- **Scoped connector report resume**: `POST /connector-runs/{ingest_run_id}/report-runs`
  now hides other-workspace queue items, verifies the queue item's area belongs to the
  caller workspace, and stores `workspace_id`/`requested_by` on the queued async report
  job and background report execution.
- **Intake producer alignment**: authenticated `/intake` requests now copy report
  identity into the created `AreaContract`, scope intake idempotency keys by principal,
  and propagate workspace/requester identity through report job creation. Legacy local
  unauthenticated intake remains available when the existing report-auth rules allow it.
- **Authenticated continuation**: authenticated `POST /report-runs` now still runs
  request-time live connector orchestration before queueing a report job, so
  authenticated intake-created DS-001 -> DS-002 -> DS-004 -> DS-003 review chains can
  continue without falling back to local unauthenticated report creation.
- **Evidence lineage persistence**: DB-gated verification exposed a repository mapper
  gap where SQLAlchemy evidence rows preserved `source_ingest_run_id` only in JSON
  metadata. `SqlAlchemyEvidenceRepository` now writes and reads the existing
  `dataset_version_id` and `ingest_run_id` columns while retaining metadata fallback
  for legacy rows.
- **OpenAPI and routing**: tracked OpenAPI stubs were regenerated with
  `scripts/export_openapi_stub.py`; `plans/README.md` and `tasks/task_queue.yaml` now
  route the current checkpoint to
  `plans/2026-06-18-connector-review-workspace-scope.md` instead of the older
  source-readiness closure plan.
- **Validation**: focused connector review action, intake/idempotency, report-auth,
  live-connector intake/report continuation, OpenAPI parity, ruff, mypy, focused
  DB-gated selected-county/evidence/claim/public-wiring tests, and full DB-enabled
  `.\scripts\verify.ps1` passed on isolated Postgres port `55448`.

## Current checkpoint (2026-06-17 deployment recovery smoke)

Deployment smoke now exercises the read-only recovery-preview operations surface in
addition to health, version, metrics, queue health, and report workflow checks.

- **Recovery-preview smoke coverage**: `scripts/run_deployment_smoke.ps1` and
  `scripts/run_deployment_smoke.sh` call reviewer-authenticated
  `/operations/recovery-preview`, require `operations_recovery_preview_v1`, check the
  900-second stale-running threshold, and verify report/live-connector queue recovery
  counters and candidate metadata fields.
- **Static proof alignment**: `backend/tests/test_deployment_smoke_scripts.py` records
  the recovery-preview smoke contract for both Windows and POSIX wrappers.
- **Limit preserved**: this is still a local Compose deployment smoke contract. It does
  not retry jobs, requeue live connectors, call live sources, or create hosted
  infrastructure.

## Current checkpoint (2026-06-17 hosted runtime secret contract)

Hosted deployment readiness now mirrors the current non-local auth requirements without
changing the repo's validate-only hosted posture.

- **Hosted runtime inputs**: `config/hosted_deployment.yaml` no longer lists local-only
  `API_KEYS` as a required hosted input. The hosted contract requires
  `API_KEY_SPECS`, `REVIEWER_ACCOUNTS`, `REVIEWER_ACCOUNT_SCOPES`,
  `UI_AUTH_COOKIE_SECRET`, `REPORT_IDENTITY_TOKEN_SECRET`, and the existing image,
  URL, and database inputs.
- **Static proof alignment**: `scripts/hosted_deployment_check.py` now requires the
  hosted runtime input set to exactly match that contract, so `API_KEYS` cannot return
  as an extra hosted input.
- **Runbook alignment**: hosted-deployment, release-readiness, and MVP operator
  guidance document the non-local auth handoff while preserving the limits: no hosted
  infrastructure is created, no secrets are written, and no hosted secrets manager is
  claimed.

## Current checkpoint (2026-06-17 UI report identity bridge)

Selected-county UI report creation now has a real browser workspace/user identity
bridge for non-local environments.

- **Token authority preserved**: `verify_report_identity_token` now returns the
  verified expiration timestamp along with workspace/user claims, so browser identity
  sessions can be bounded by the submitted token.
- **Derived UI identity session**: `/ui/auth/identity` and selected-county UI report
  forms accept `report_identity_token`, verify it with `REPORT_IDENTITY_TOKEN_SECRET`,
  and set a signed HttpOnly SameSite `/ui` cookie carrying only workspace id, user id,
  and expiry. The raw token is not stored in the cookie or rendered back.
- **Non-local selected-county path**: `/ui/operator-cases/report` now uses the
  submitted identity token or identity session cookie to persist `workspace_id` and
  `requested_by`. It still fails closed outside local/dev/development/test when no
  identity is present, and preserves local seeded fallback only for local-like app
  environments.
- **Validation/docs**: focused report-auth/UI route tests pass for submitted token,
  identity cookie reuse, invalid/missing identity, local fallback coverage, and CSRF
  on identity login and selected-county report creation when UI API-key, reviewer,
  or identity session cookies authorize the UI mutation. Access-control and MVP
  operator runbooks document the bridge, and `scripts/access_control_check.py` pins
  the helper/routes/tests/static route condition.

## Current checkpoint (2026-06-17 non-local secret hygiene)

Non-local app environments now fail closed for weak static secret configuration while
local private-MVP ergonomics remain intact.

- **API-key secret shape**: local/dev/development/test may still use raw `API_KEYS` and
  raw `API_KEY_SPECS` secrets. Outside those app environments, `API_KEYS` is rejected;
  configured `API_KEY_SPECS` secrets must use `sha256:<64-hex>`; and
  `REQUIRE_API_KEY=true` requires `API_KEY_SPECS`.
- **Reviewer secret shape**: local/dev/development/test may still use the fixture
  reviewer account and raw reviewer tokens. Non-local app environments reject the
  fixture reviewer default, reject raw reviewer token specs, and require explicit
  `REVIEWER_ACCOUNT_SCOPES` coverage for each reviewer id.
- **Startup path**: `create_app` now runs the secret-hygiene validator before building
  auth middleware and service state.
- **Operator guidance**: `.env.example`, Compose comments, and access-control/MVP
  runbooks now describe the non-local hashed-spec requirements while preserving the
  existing blockers for OAuth/OIDC, user accounts/RBAC, hosted secret management, and
  automatic rotation.
- **Validation**: focused non-local API-key boundary tests passed (`7 passed`), API-key
  and reviewer-auth files passed (`70 passed`, `1 skipped`), impacted API/UI/runtime/
  access-control artifact suite passed (`139 passed`, `1 skipped`), access-control
  checker exited `0`, ruff passed on touched Python files, mypy passed on touched
  source plus focused touched tests from the backend import path, default
  `scripts/verify.ps1` passed, and private-MVP/hosted/release readiness validators
  exited `0`.

## Current checkpoint (2026-06-17 async report-create contract)

`POST /report-runs` now uses the async job contract for authenticated creation instead
of returning a synchronous `201 Created` `ReportRunContract`.

- **Unified create response**: authenticated and unauthenticated report creation both
  return `AsyncReportRunResponse`; first queueing returns `202 Accepted`, and
  `Idempotency-Key` replay returns `200 OK` with the same job ID.
- **Attribution preserved**: report jobs now carry `workspace_id` and `requested_by`
  through the in-memory and SQLAlchemy-backed async job stores. Background report
  execution passes those fields to the eventual `ReportRunContract`.
- **Workspace-scoped job reads**: authenticated `GET /report-runs` filters job rows to
  the caller's workspace, and authenticated `GET /report-runs/{id}` no longer returns
  queued/running/failed job placeholders for another workspace. Succeeded legacy rows
  still fall through to report-level workspace checks.
- **Readiness/runbook update**: `sync_async_create_divergence` is marked complete in
  `config/private_mvp_beta_readiness.yaml`, and the MVP operator runbook now documents
  the unified async creation/idempotency response.
- **OpenAPI stub refreshed**: tracked stub files under `api/` and
  `docs/planning_pack/api/` were regenerated with the repo export script.
- **Validation**: focused report job/auth/async/idempotency tests passed (`54 passed`,
  `7 skipped`) before the list-isolation follow-up; focused integration/list-isolation
  tests, ruff, mypy, private-MVP readiness, access-control, and OpenAPI parity passed.
  DB-enabled `.\scripts\verify.ps1` passed on ephemeral PostGIS port `55446` after a
  post-readiness settle wait, covering migrations/seeds, backend tests, ruff, mypy over
  309 source files, and DB smoke.

## Current checkpoint (2026-06-16 operator proof-semantics closeout)

The selected-county operator implementation remains the app-owned packaged fixture path:
`backend/app/operator_cases`, `GET /operator-cases`, `POST /operator-cases/{case_id}/report`,
and the `/ui/` selected-county launcher. This checkpoint did not add source coverage or
change report/auth/DB behavior; it closed the proof-boundary gap around how operators and
future agents should interpret the existing paths.

- **Proof matrix added**: `docs/runbooks/mvp_operator.md` now maps the no-server
  `generate_dossier.py` path, `/operator-cases`, `/ui/`, generic `/report-runs`,
  DB-backed verification, and live connector queues to what each proves and does not
  prove.
- **Overclaim wording tightened**: CLI artifact docs now say the no-server path emits the
  same in-memory artifact contract shape and does not exercise HTTP routing, access
  gates, or DB artifact persistence.
- **Regression guard**: `backend/tests/test_private_mvp_readiness.py` now pins the proof
  matrix and rejects stale CLI/API artifact overclaim wording.
- **Reviewer-session doc alignment**: the MVP operator runbook no longer claims UI
  approval has no session/cookie path; it now distinguishes UI-only reviewer sessions
  from JSON/API header-only reviewer authentication, and
  `backend/tests/test_access_control_artifacts.py` guards that wording.
- **Validation**: focused private-MVP/operator-case tests passed (`45 passed`); ruff and
  mypy passed on touched surfaces; access-control, hosted-deployment, image-publication,
  release-readiness, private-MVP, workspace validation, whitespace/no-delete, and
  attribution scans passed. DB-enabled `.\scripts\verify.ps1` passed on isolated
  Compose DB port `55443` after an explicit readiness wait. UI runtime smoke passed, and
  Chrome UI smoke passed in both headless and headed modes at desktop and mobile
  viewports. Final default `.\scripts\verify.ps1` passed on the current tree.

## Current checkpoint (2026-06-15 production report-create auth guard)

The report-create API no longer leaves the anonymous async creation path available in
non-local runtime environments.

- **Non-local report-create guard**: `POST /report-runs` still preserves the
  local/dev/development/test anonymous async private-MVP path, but `_optional_report_auth_context`
  now delegates to configured report auth outside those app environments. In
  non-local trusted-header mode, missing `X-Workspace-Id` / `X-User-Id` fails closed
  with `401` before report creation; signed-token mode keeps the existing bearer-token
  enforcement.
- **Private-MVP readiness update**: `config/private_mvp_beta_readiness.yaml` now marks
  `unauthenticated_workspace_isolation` complete for the non-local production boundary
  while leaving `sync_async_create_divergence` as an accepted private-MVP API ergonomics
  risk.
- **Access-control/design reconciliation**: the static access-control proof now tracks
  the current UI reviewer-session contract in `DESIGN.md` instead of the stale
  stateless-per-action reviewer-token phrase.
- **Validation routing**: `MANIFEST.md` now routes future operators/agents to the
  explicit UI browser/runtime smoke entrypoints under the validation source-of-truth row.
- **Validation**: focused report-auth/async/UI-smoke/access-control artifact tests
  passed; ruff and mypy passed on the touched Python surfaces; access-control,
  private-MVP, release-readiness, Must-source readiness, workspace validation, and
  default `.\scripts\verify.ps1` passed. DB smoke remains skipped unless
  `RUN_DB_SMOKE=1` is set.

## Current checkpoint (2026-06-15 explicit UI browser smoke)

The operator UI now has a repo-owned, non-mutating browser smoke gate instead of relying
only on ad hoc local screenshot scripts or route-level TestClient assertions.

- **Tracked browser smoke harness**: `scripts/ui_browser_smoke.mjs` launches Chrome with
  temporary profiles, checks the core `/ui/*` surfaces at desktop (`1366x900`) and
  mobile (`390x844`) viewports, fails closed on missing DOM contracts or page-level
  horizontal overflow, and removes temporary profiles. It accepts `--base-url`,
  `--chrome-path`, `--mode`, optional API-key/reviewer-session inputs, and optional
  screenshot output. Screenshots and JSON are opt-in; the script does not create areas,
  report runs, connector-review items, or review actions.
- **Operator wrappers**: `scripts/run_ui_browser_smoke.ps1` and
  `scripts/run_ui_browser_smoke.sh` provide explicit Windows/POSIX entrypoints without
  adding browser smoke to default `verify`.
- **Lightweight runtime smoke**: `scripts/ui_runtime_smoke.py` gives a fast HTTP-only
  HTML contract check for the same core UI surfaces and fail-closed empty-page behavior.
- **Browser-found UI fix**: the new browser smoke found a mobile overflow on `/ui/auth`;
  the API-key auth input now uses `box-sizing: border-box`, matching the reviewer auth
  form behavior.
- **Evidence**: against a fresh memory-backed runtime on port `8768`, HTTP runtime smoke
  passed; headless Chrome smoke passed for core UI routes with screenshots under
  `local_artifacts/ui-browser-smoke/`; reviewer-session Chrome smoke also passed at
  desktop and mobile viewports with no screenshots. Sample inspected screenshots:
  `ui-smoke-api-key-auth-headless-mobile.png`,
  `ui-smoke-report-runs-headless-mobile.png`, and
  `ui-smoke-operations-headless-desktop.png`.
- **Validation**: focused smoke/auth tests passed; node syntax check passed; focused
  ruff/mypy passed; default `.\scripts\verify.ps1` passed with workspace validation,
  backend tests, ruff, and mypy over 309 source files. DB smoke remains skipped unless
  `RUN_DB_SMOKE=1` is set.

## Current checkpoint (2026-06-15 report-list mobile operator cards)

The report-run list is now usable as a mobile operator work surface instead of
requiring horizontal table scrolling before the operator can see status or act.

- **Mobile report-run cards**: `/ui/report-runs` keeps the desktop table layout above
  the small-screen breakpoint, while mobile renders each run as a label-over-value card
  with visible select, ID, intent, status, created, and action fields. The action links
  wrap naturally, and pending-review rows expose `Approve from detail` without relying
  on horizontal scroll.
- **Accessible mobile table context**: mobile table headers are visually hidden with a
  clipped/absolute pattern rather than removed from the accessibility tree. The visual
  cell labels still come from `data-label` pseudo-content, but table headers remain
  present for assistive technology.
- **Responsive report-list navigation**: the report-list nav is now a real labeled
  `<nav>` that wraps on desktop and stacks on mobile, preventing the connector review
  queue link from clipping before the report list content.
- **Browser evidence**: headed/in-app browser screenshots were refreshed at
  `local_artifacts/ui-report-list-mobile-cards-mobile.png` and
  `local_artifacts/ui-report-list-mobile-cards-desktop.png`; independent headless
  Chrome proof is at `local_artifacts/ui-report-list-mobile-cards-headless.png`.
  Mobile metrics showed no page-level horizontal overflow
  (`clientWidth=375`, `scrollWidth=375`), visible status/action cells, stacked nav, and
  mobile table headers visually hidden rather than `display:none`.
- **Validation**: focused report-list tests passed; `test_ui_routes.py` passed; focused
  ruff and mypy passed; default `.\scripts\verify.ps1` passed with workspace
  validation, backend tests, ruff, and mypy over 307 source files; standalone workspace
  validation and hygiene scans passed. DB smoke remains skipped unless
  `RUN_DB_SMOKE=1` is set.

## Current checkpoint (2026-06-15 production evidence contract and no-JS compare)

The production readiness boundary now has a machine-readable future proof contract for
both registry image publication and hosted deployment without changing the repo's
validate-only posture.

- **Image and hosted attestation contracts**: `config/image_publication.yaml` and
  `config/hosted_deployment.yaml` now include `attestation_evidence` sections with
  `status: not_available`, exact required fields, current blockers, runbook authority,
  and empty evidence templates. The validators fail closed if a future
  available/published/deployed status is claimed while required evidence values remain
  empty.
- **No-JavaScript report comparison**: `/ui/report-runs` now submits the compare form
  natively to `/ui/compare` using repeated `ids` parameters. The existing server-side
  compare validation remains the authority for selection count and malformed IDs.
- **Browser evidence**: screenshots were captured at
  `local_artifacts/ui-report-list-compare-desktop.png`,
  `local_artifacts/ui-report-list-compare-mobile.png`, and
  `local_artifacts/ui-compare-native-submit.png`. The mobile probe showed no page-level
  horizontal overflow (`clientWidth=390`, `scrollWidth=390`) and no scripts on the
  report-list page.
- **Validation**: image-publication, hosted-deployment, and release-readiness checks
  passed; focused artifact/UI tests passed; focused ruff/mypy passed; default
  `.\scripts\verify.ps1` passed with backend tests, ruff, and mypy over 307 source
  files; standalone workspace validation passed. DB smoke remains skipped unless
  `RUN_DB_SMOKE=1` is set.

## Current checkpoint (2026-06-14 selected-county operator API/UI path)

The selected-county private-MVP approved dossier path is now reachable through the app
surface, not only through `scripts/generate_dossier.py`.

- **Fresh worktree baseline**: `prod-grade-20260614` was created from fetched
  `origin/main` at `d7ec75ba7aec52794fc82f29658ce262e15974fc`; initial
  `.\scripts\verify.ps1` passed after installing `backend[dev]` and
  `python-multipart`.
- **App-owned case package**: `backend/app/operator_cases` packages the nine
  Buncombe/Chatham/Brunswick private-MVP cases plus their local connector fixtures.
  Runtime no longer depends on `tests/fixtures/**` for this operator path.
- **Design source of truth**: `DESIGN.md` now defines the private operator console
  contract, information architecture, visual language, accessibility targets, and
  implementation constraints for the server-rendered UI.
- **HTTP/UI utility path**: `GET /operator-cases` lists cases, and
  `POST /operator-cases/{case_id}/report` ingests the packaged local fixture
  connectors, approves eligible connector-QA handoffs, creates an approved report, and
  returns links to the existing UI, dossier download, and JSON artifact. `/ui/` is now a
  production-oriented operator console with selected-county case table actions, status
  strip, visible fixture/live boundary metadata, responsive/mobile table layout, and
  server-side custom GeoJSON intake. The operator API now exposes fixture scope/language,
  not-evaluated domains, and expected unknowns for each case, and rejects blank or
  unexpected report-create body fields. The custom AOI form now posts to `/ui/intake`
  without requiring JavaScript, redirects to the created report or connector-review queue,
  and returns safe HTML errors for invalid GeoJSON or intent values. Report status/detail
  pages now share a responsive report shell for queued/running, failed, missing,
  pending-approval, and approved states, with status-first content and explicit operator
  action panels. Print/export attempts for missing or unapproved reports use the same
  shell without exposing dossier content before approval. Connector review, operations,
  and evidence-lineage UI pages now include the same viewport contract so support
  workflows stay usable on constrained screens; that page-head and shared error-page
  behavior is centralized in `ui_shared.py`.
- **Comparison workflow**: `/ui/report-runs` exposes report comparison as a native
  `GET /ui/compare` form, so selecting 2-4 rows works without JavaScript. The compare
  route accepts both repeated `ids` query parameters and the original comma-separated
  `ids=<uuid>,<uuid>` URL format. `/ui/compare` now shows report/review/delivery
  status, approval-gated next-action links, high-severity claim code/domain details,
  and, for exactly two same-area reports, a Change Review section pinned to the same
  diff semantics as `/report-runs/{id}/diff`.
- **Workflow recoverability**: the home operator console and report-run list now link
  directly to `/ui/connector-review-queue`, making review-gated connector handoffs
  discoverable after an operator leaves the initial pending-intake result.
- **Private-beta UI access bridge**: when `REQUIRE_API_KEY=true`, `/ui/auth` now lets
  browser operators submit the configured API key once and receive a signed, expiring,
  HttpOnly, SameSite cookie scoped to `/ui`; JSON/API paths still require `X-API-Key`.
  UI-cookie signing uses `UI_AUTH_COOKIE_SECRET` rather than API-key specs/hashes;
  non-local API-key-locked app environments fail startup if that setting is blank,
  while local/dev/development/test app environments may use a per-process fallback.
  Non-local `APP_ENV` values set `Secure` automatically, and `/ui/auth` login attempts
  are audit-logged without storing submitted secrets. Unsafe `/ui` POST forms
  authenticated by the UI cookie now carry signed CSRF tokens derived from the HttpOnly
  cookie, and sign-out is a confirmation GET plus CSRF-protected POST.
- **Private-beta reviewer UI session**: `/ui/auth/reviewer` and successful
  reviewer-credential UI actions now establish a signed, expiring, HttpOnly reviewer
  cookie scoped to `/ui`. The cookie carries reviewer id, scopes, expiry, and an HMAC
  binding to the configured reviewer token spec; token rotation, scope removal,
  tampering, or expiry invalidates the session. Report approval, connector-review,
  and operations UI forms hide token inputs when the reviewer session has the required
  scope, while JSON/API routes remain header-only for reviewer credentials. UI logout
  clears both the API-key UI cookie and reviewer UI cookie.
- **Operations drilldown**: `/ui/operations` queue-health counts now link to the
  corresponding report-list or connector-review filters, making aggregate failed,
  queued, cancelled, and needs-review counts immediately actionable while preserving the
  read-only operations contract. A reviewer session with `operations:read` can now open
  the dashboard directly via `GET /ui/operations`; missing or under-scoped sessions
  still fall back to the scoped credential form. Report-list and connector-review queue
  status filters fail closed with safe HTML errors on unknown values instead of silently
  showing unfiltered work.
- **Connector review action gating**: connector-review detail pages now show only
  actions valid for the current queue-item status according to the repository transition
  rules; terminal no-action states render an explicit no-actions message rather than
  invalid mutation forms.
- **Connector review decision context**: connector review packets and queue payloads now
  preserve compact evidence summaries plus retrieval counts, log URI, metrics, signals,
  and human-review tasks. `/ui/connector-review-queue/{ingest_run_id}` renders that
  snapshot as a Decision Context panel with responsive evidence cards before approve,
  reject, requeue, cancel, or resume-report actions, without dumping arbitrary payload
  fields or secret-looking metric keys. `/ui/connector-review-queue` also exposes a
  compact triage summary and next-action link per row, derived from the same payload and
  queue status, so operators can prioritize work without opening every detail page.
- **Evidence-lineage delivery boundary**: `/ui/report-runs/{id}/lineage` now follows
  the approved-report delivery contract. Succeeded-but-unapproved direct UI visits get
  an Approval Required page that links back to report review, while approved reports
  render lineage without embedding reviewer credentials. The JSON lineage API remains
  on its existing API access policy, and the UI lineage tables are contained in
  responsive horizontal scroll regions for narrow screens.
- **Durable runtime state boundary**: production-like app environments now fail closed
  if the operator runtime would use in-memory API services. `USE_DB_SERVICES=true` is
  required outside local/dev/development/test `APP_ENV` values, and `DATABASE_URL` must
  be non-blank when DB services are enabled. `scripts/run_api.ps1 -StorageBackend
  postgres` and `scripts/run_api.sh --postgres` now set the canonical
  `USE_DB_SERVICES=true` switch; memory mode remains available for local fixture demos.
- **Refresh control**: queued/running report pages still auto-refresh every 3 seconds by
  default, but now expose no-JavaScript 3/10/30/60-second interval controls plus pause,
  manual refresh, and resume links so operators can inspect long-running jobs without
  involuntary page reloads. Non-default refresh intervals survive pause/resume URLs.
- **Report-list actions**: `/ui/report-runs` now includes a row-level Action column that
  routes queued/running jobs to status, failed jobs to retry detail, pending succeeded
  reports to approval detail, and approved reports to dossier, JSON artifact, and
  lineage links without adding new mutation semantics.
- **Responsive case launcher**: selected-county fixture cases now collapse to
  label-over-value mobile rows with explicit overflow wrapping, keeping long
  descriptions and source-boundary metadata readable in narrow Chrome viewports.
- **Approval audit notes**: the UI report approval form now accepts an optional approval
  reason and stores trimmed non-empty text on the existing report review action audit
  trail; blank notes remain omitted.
- **Boundary preserved**: this is fixture-only private-MVP utility coverage. It does
  not use live-source production coverage, unblock DS-017, change report semantics, or
  assert legal zoning, surveyed boundary, wetland jurisdiction, buildability, legal
  access, appraisal, lending, insurance, or investment conclusions.
- **Validation**: focused operator/private-MVP/OpenAPI/UI tests passed; ruff and mypy
  passed on touched files; default `.\scripts\verify.ps1` passed with workspace
  validation, backend tests, ruff, and mypy over 304 source files. Headless and headed
  Chrome screenshots were captured under `local_artifacts/`; the final desktop probe
  confirmed the case action column is fully visible, the no-JavaScript custom intake path
  landed on a report page, the report-detail HTTP probe confirmed the new pending report
  shell/action panel after a fresh server restart, and the final iPhone/mobile probes had
  no horizontal page overflow. The latest connector-review action-gating slice passed the
  135-test expanded operator/UI/private-MVP/OpenAPI set and a fresh default
  `.\scripts\verify.ps1`; the refresh-control slice then passed focused report-state
  tests, the full UI route file, regenerated OpenAPI/schema-copy checks, the expanded
  operator/UI/private-MVP/OpenAPI set, and another default `.\scripts\verify.ps1`. The
  report-list action slice passed focused action/responsive tests, the full UI route
  file, the expanded operator/UI/private-MVP/OpenAPI set, and another default
  `.\scripts\verify.ps1`; fresh desktop/mobile action-list screenshots were captured
  under `local_artifacts/`. The approval-reason slice then passed focused approval
  tests (`5 passed`), the full UI route file (`71` collected tests), regenerated
  OpenAPI/schema-copy checks (`3 passed`), the expanded operator/UI/private-MVP/OpenAPI
  set (`145` collected tests), and another default `.\scripts\verify.ps1`; headless
  desktop/mobile plus headed Chrome screenshots were captured under
  `local_artifacts/ui-report-approval-reason*.png`, with matching input/textarea widths
  after screenshot-driven form polish. The redirect-consistency slice then moved report
  approval, report retry, and connector-review resume-report successes from meta-refresh
  handoff pages to real `303` redirects to the resulting report pages; focused tests,
  the combined changed UI route files, ruff, mypy, and OpenAPI/schema-copy checks passed,
  and redirect target screenshots were captured under
  `local_artifacts/ui-*-redirect-result.png`. The DB-backed verification lane then
  passed on isolated Docker PostGIS with `RUN_DB_SMOKE=1`, `DATABASE_URL_SYNC`, and
  `DATABASE_URL` pointed at DB port `55434`; migrations, backend tests, ruff, mypy,
  and `scripts/db_smoke_check.py` were green with 25 seeded source-registry rows,
  26 total source rows, and 2 seeded intents. Deployment smoke initially exposed a
  PostGIS-image startup race where `pg_isready` returned during the temporary init
  server; `scripts/run_deployment_smoke.ps1` and `.sh` now wait for stable
  `pg_postmaster_start_time()` samples before applying migrations, and the Windows
  script applies SQL through a copied in-container file rather than a PowerShell
  pipe into `docker compose exec`. Fresh deployment smoke passed on isolated project
  `land-diligence-smoke-pg6` with backend port `18084` and DB port `55439`, then a
  final default `.\scripts\verify.ps1` passed with DB smoke skipped by design because
  `RUN_DB_SMOKE=1` was not set for that fast gate. The UI API-key bridge hardening
  slice then passed focused UI/API-key auth tests, focused ruff/mypy, access-control
  validation, OpenAPI contract/schema-copy tests, and another default `.\scripts\verify.ps1`;
  headless/mobile/headed Chrome screenshots for the login and authenticated home paths
  were captured under `local_artifacts/ui-auth-*` and
  `local_artifacts/ui-home-authenticated-*`. The CSRF hardening slice then passed
  focused UI/auth/OpenAPI tests, focused ruff/mypy, access-control validation, and
  another default `.\scripts\verify.ps1`; DB smoke was skipped by design for that
  fast gate. The design/config alignment slice then reconciled `DESIGN.md` and the
  `UI_AUTH_COOKIE_SECRET` settings description with the implemented `/ui/auth` bridge
  and local-only signing-secret fallback, added static access-control checks for the
  design source of truth, and passed access-control validation plus focused ruff/mypy.
  The manifest/catalog alignment slice then added `DESIGN.md` to the intentionally
  scoped repo routing manifest, expanded `ui_api_key_cookie_bridge` authority in
  `config/access_control.yaml`, and made the access-control validator fail if those
  authority files drift out of the catalog. Review then tightened that guard to read
  `MANIFEST.md`, pin `DESIGN.md`'s canonical ownership statement, include
  `backend/app/api/ui_lineage.py`, and fail on unexpected UI bridge authority entries.
  The release-readiness coverage slice then made `scripts/release_readiness_check.py`
  require the full declared catalog rather than a historical subset, including
  security scan, data retention, jurisdiction/rulepack checklists, load testing,
  performance, and data-lineage gates. The responsive browser-proof slice then tightened
  the selected-county mobile case launcher, captured headless and headed Chrome evidence
  under `local_artifacts/ui-console-*`, and verified the 390px CDP mobile viewport had
  no horizontal page overflow; the monolithic verify wrapper timed out during backend
  pytest output handling, so the same verification phases were run separately with
  workspace validation, all backend test groups, full ruff, and full mypy passing. The
  QA-runner hardening slice then buffered backend pytest through replayed
  `local_artifacts/backend-pytest.log` transcripts, used fresh-on-collision log paths
  to preserve prior evidence, added runner behavior regressions, and passed focused
  pytest/ruff/mypy, Git Bash POSIX syntax, and a fresh default `.\scripts\verify.ps1`
  over 307 source files. The compare UI change-review slice then passed the focused
  compare route tests (`16 passed`), focused ruff/mypy, and live preview screenshot
  checks with headless and headed Chrome under `local_artifacts/ui-compare-*`; the
  headed desktop/mobile metrics showed no document-level horizontal overflow. The full
  UI route file, workspace validation, and another default `.\scripts\verify.ps1`
  passed after the compare docs/state update.

## Current checkpoint (2026-06-13 operator approved-path proof — 1627 tests)

Pivot from claim-narrative enrichment (passes 4–12 were diminishing-returns polish — the handoff's "readiness theater" risk) to **operator utility**. Lane: Source-Authority Closeout → Selected-County Operator Utility Transition.

- **Baseline verified, no drift**: source-readiness + private-MVP readiness scripts pass. Must 7 ready / 1 blocked (DS-017 only, deferred). All 25/16/9. DS-010 Chatham/Buncombe/Brunswick connectors, DS-011 NOT_EVALUATED sentinel, DS-023 Chatham/Brunswick recorded-fixture — all truthful. Catalog/validator work is DONE; stopped adding it.
- **No-Docker approved path**: `generate_dossier.py` gains `--approve` (real `approve_report_run`) + `--artifact` (byte-identical to API serialization). One copy-runnable command yields an APPROVED selected-county dossier + JSON artifact, no server/Docker. Commit 254a893.
- **Two new tests**: `test_operator_approved_path.py` (Chatham delta: approval state + artifact shape, not duplicating manifest caveat/forbidden coverage); `test_approved_path_http.py` (no-Docker HTTP proof the shipped `fixture-reviewer`/`fixture-token-123` credential flows 409→approve→200 + parity + 401 — previously only DB-gated).
- **Architectural truth documented**: `connector_runbook.md` now documents the two non-interchangeable fixture corpora (generic embedded = HTTP-reachable, 3 connector types; county golden = filesystem-only, all 8 domains) and the reachability gap — the HTTP curl path CANNOT serve county dossiers in fixture mode; the script is the only no-Docker path. This subtlety nearly derailed the planning pass (confirmed via adversarial grill).
- **§18 Source Appendix defect fixed**: columns were mislabeled — `review_status` shown under "Use", `license_status` under "Caveat" (so every source read "Caveat: approved"). Renamed to Review/License (honest labels for the data; `source_details` has no caveat field). Regression test pins the mapping. Commit follows 254a893.
- **Stronger completion proven**: `test_manifest_driven.py` now runs the approved path + artifact assertion across ALL 9 golden AOIs — Chatham, Buncombe, Brunswick each have a representative operator-usable case reaching review_status=approved with a well-formed artifact.
- Full suite: 1627 passed, 73 skipped. ruff clean.

## Previous checkpoint (2026-06-13 claim narrative enrichment pass 12 — 1614 tests)

Water and wetland needs-review claim enrichments:
- **Water needs-review station count**: `_water_needs_review_claim()` now surfaces `monitoring_station_count` from first non-failure evidence record when present, e.g. "(3 USGS monitoring station(s) in screening bbox)". Commit 5753f26.
- **Wetland needs-review feature detail**: `_wetland_needs_review_claim()` now surfaces NWI feature count, mapped acres, and wetland type labels (same pattern as `_wetland_positive_claim`). Commit 5753f26.
- 2 new regression tests. Full suite: 1614 passed, 73 skipped; ruff clean.

## Previous checkpoint (2026-06-13 claim narrative enrichment pass 11 — 1611 tests)

Three more claim narrative enrichments:
- **Zoning needs-review zone codes**: `_zoning_needs_review_claim()` now surfaces zone code(s) from non-failure evidence in `user_safe_language`, e.g. "(code(s) found: RA)". Commit cad76c0.
- **Flood needs-review zone codes**: `_flood_needs_review_claim()` now surfaces flood zone code(s) from non-failure evidence, e.g. "(zone(s) found: AE, X)". Commit 8bc0aee.
- 3 new regression tests pinning enriched narratives. Full suite: 1611 passed, 73 skipped; ruff clean.

## Previous checkpoint (2026-06-13 dossier output quality pass 10 — 1610 tests)

Three dossier output quality fixes:
- **Buildability dedup fix**: `_buildability_summary()` no longer emits raw `metric_code` strings (e.g. `fixture_slope_buildability_screen`) when structured fields (`relief_m`, `mean_slope_pct`, etc.) are present in the same evidence record. Also deduplicates identical entries (e.g. `terrain relief ~215m` from two records sharing `relief_m`). Commits 58f983e.
- **CHA-zoning-edge fixture**: `nc_chatham_cha_zoning_edge_zoning.json` `observed_value` now includes `udo_note` so Section 10 "District description" shows the human-readable note instead of "not available". Commit 58f983e.
- **Zoning lot-size phrase**: `_zoning_lot_size_result()` changed "recorded fixture" to "current screening data" — removes implementation-leaking language. Commit f0272ef.
- 2 new regression tests. Full suite: 1610 passed, 73 skipped; ruff/mypy/verify.ps1 clean (297 source files).

## Previous checkpoint (2026-06-13 claim narrative enrichment pass 9 — 1609 tests)

Soil screening review claim enrichment:
- **Soil screening review claim**: `_soil_screening_review_claim()` now surfaces `soil_mapunit_name` and `hydrologic_group` from SSURGO evidence, e.g. "(dominant unit: Cecil sandy loam; hydrologic group B)". Commit 3a7d421.
- 1 new regression test (`test_soil_screening_review_claim_surfaces_mapunit_name_and_hydrologic_group`). Full suite: 1609 passed, 73 skipped; ruff/mypy clean.

## Previous checkpoint (2026-06-13 claim narrative enrichment pass 8 — 1608 tests)

Access claim enrichment + "in the fixture" purge across 7 stale/prohibited claim functions:
- **Access no-adjacency claim**: `_access_no_adjacency_claim()` now surfaces `(0 OSM road segments in screening area)` when `road_count=0`. Commit 0ffe2ac.
- **"in the fixture" removed**: `_access_stale_claim()`, `_zoning_prohibited_claim()`, `_zoning_stale_claim()`, `_water_stale_claim()`, `_slope_stale_claim()`, `_wetland_stale_claim()`, `_flood_stale_claim()` all had the implementation-leaking phrase removed. Commit 0ffe2ac.
- 1 new regression test (`test_access_no_adjacency_claim_surfaces_road_count_when_zero`). verify.ps1: ok; 1608 passed, 73 skipped; ruff/mypy clean (297 source files).

## Previous checkpoint (2026-06-13 claim narrative enrichment pass 7 — 1604 tests)

Three more claim enrichments and a lint fix; verify.ps1 passes clean:
- **Env hazard proximity claim**: `_env_hazard_proximity_claim()` now surfaces `regulated_facility_count`. Commit 262f8d4.
- **Water no-context claim**: removes legacy "in the fixture" phrasing; surfaces `monitoring_station_count` when present. Commit 8f92e70.
- **Parcel screen claim**: surfaces `parcel_pin`, `parcel_acres`, and `parcel_county` from evidence. Commit eb9a79a.
- **Lint fix**: E501 errors in `test_dossier_enrichment.py` fixed. Commit 3528151.
- 4 new regression tests. verify.ps1: ok; 1604 passed, 73 skipped; ruff/mypy clean (297 source files).

## Previous checkpoint (2026-06-13 claim narrative enrichment pass 6 — 1601 tests)

Seven claim function enrichments and one dossier improvement this session:
- **Domain-aware recommended action**: `_recommended_next_action()` replaced with logic that varies by severity: critical → lists domains, high → lists domains, advisory → advisory message, else → verification plan. Commit 6ea4fa0.
- **Wetland positive claim**: `_wetland_positive_claim()` now surfaces NWI feature count, mapped acres (~0.42ac from 1700sq_m), and wetland class/type when present. Commit 26a9f66.
- **Slope insufficient claim**: `_slope_insufficient_claim()` now surfaces buildable area in acres, `low_slope_area_ratio`, and `mean_slope_pct` when present. Commit 26a9f66.
- **Flood positive claim**: `_flood_positive_claim()` now surfaces high-risk zone codes (AE, A, VE, etc.) using the same `_flood_zone_values()` helper as `_flood_moderate_claim()`. Commit 4096067.
- **Geology not-evaluated claim**: `_geology_not_evaluated_claim()` now surfaces `primary_geologic_unit_label` and `primary_geologic_formation` when present. Commit 2251de4.
- **Minerals active claim**: `_minerals_active_claim()` now surfaces `blm_active_mining_claim_count`, `primary_blm_mlrs_case_name`, and serial number when present. Commit 85bd662.
- **Zoning prohibited claim**: `_zoning_prohibited_claim()` now surfaces `zoning_code`, `district_name`, and `use_category` when present. Commit 26b866d.
- 8 new regression tests pinning enriched claim narratives. ruff/mypy clean on all changed files. 1601 passed, 73 skipped.

## Previous checkpoint (2026-06-13 connector enrichment pass 5 — 1593 tests)

Eight targeted connector/dossier/test improvements this session:
- **SSURGO water_table_depth_cm**: `comonth` join added to `_build_query()` fetches `min(wtdepannmin_r)` per component; mapped to `water_table_depth_cm` in evidence `observed_value`. Commit acba0a5.
- **SSURGO soil claim narrative**: `_soil_poor_drainage_claim()` now includes "water table ~Xcm depth" in `detail_parts` when `water_table_depth_cm` is present in evidence. Commit d6acf90.
- **USGS TNM mean/min/max elevation + sample_count**: `_evidence_for_samples()` now stores `mean_elevation_m`, `min_elevation_m`, `max_elevation_m`, `sample_count` in `observed_value`; all were already whitelisted in `DERIVED_METRIC_KEYS`. Commit d6acf90, cd2bde3.
- **Dossier Section 6 elevation range**: `_buildability_summary()` shows "elevation range X–Ym (N samples)" when min/max present; falls back to "mean elevation ~Xm" without them. Commit cd2bde3.
- **Dossier Section 14 BLM primary case name**: `_mineral_mining_result()` now includes primary case name and serial number when active claims are present. Commit cd2bde3.
- **Assessor scope note**: Section 2 assessor line changed from "were not available" to "not evaluated — out of scope for this screening version". Commit d6acf90.
- **2 new regression tests**: `test_evaluate_soil_drainage_claim_includes_water_table_depth_when_present` pins water table depth in claim narrative; `test_dossier_renders_buildability_terrain_from_evidence` updated to pin elevation range/sample_count display. Commit d3aa9a9.
- **mypy clean**: 4 `type: ignore` comment errors fixed (`call-overload` vs `arg-type`). Commit 394d061.
- Full suite: 1593 passed, 73 skipped. ruff/mypy clean on all changed files.

## Previous checkpoint (2026-06-13 advisory claims + rule coverage + dossier enrichment pass 4 — 1592 tests)

Eight improvements across rule engine, dossier output, and test coverage:
- **GEOLOGY_G001 advisory rule**: new LOW-severity hard gate fires when geology
  evidence is present but `geologic_hazard_determined: False`. Commit 6abde71.
  Severity corrected from `informational` to `low` so it surfaces in advisory
  findings table. Commit 0cc1f4a.
- **Section 11 contamination context**: `_env_contamination_context()` replaces
  hardcoded "unknown" with ECHO-derived facility count + Phase I ESA note.
  Commit 96e06e8.
- **Section 2 geometry confidence**: `_geometry_confidence()` replaces hardcoded
  "unknown" with parcel county GIS source and `~50m` spatial precision note.
  Commit 85d56d7.
- **Section 10 zoning overlays/lot size**: `_zoning_overlay_result()` and
  `_zoning_lot_size_result()` replace hardcoded "unknown" with "not screened"
  messages surfacing the `udo_source_url` from zoning evidence. Commit 2e8d265.
- **Advisory claim dossier tests**: new tests verify FLOOD_G002, SOIL_G002,
  GEOLOGY_G001, and BROADBAND_G001 advisory claims each appear in Section 3.
  Commits 0418e38, eb8ca04.
- **Advisory claims regression test**: pins `advisory_claim_codes` and
  `advisory_count` in cost_metrics when FLOOD_MODERATE_001 fires. Commit ce49829.
- 22 new tests total this session. Full suite: 1592 passed, 73 skipped.
- ruff/mypy clean on all changed files.

## Previous checkpoint (2026-06-13 dossier enrichment pass 3 + OSM highway types — 1570 tests)

Seven connector-field surfacing improvements and one connector query upgrade:
- **NOAA nearest city/state in Section 13**: `_climate_result()` now surfaces
  `nws_nearest_city` / `nws_nearest_state` stored by NOAA connector but previously
  unused. Commit b01ec52.
- **FCC broadband upload speed in Section 12**: `_broadband_result()` now shows
  combined down/up Mbps as "max 1000/100 Mbps (down/up)" when both values present.
  Commit 370fd6c.
- **OSM highway types in Section 5**: Overpass query upgraded from `out count;` to
  `out tags;` so each matched way's `highway` tag is captured. Connector stores
  deduplicated `highway_types` list; dossier surfaces road categories (primary, track,
  etc.) alongside segment count. Fixes payload validation to include `highway_types`
  in `SPATIAL_INTERSECTION_KEYS`. Connector tests updated for new response format.
  Commits 1796376, 92b3a47.
- Also committed in prior context: NWI wetland class/system names, census geography
  names, UDO source URL fallback, SSURGO slope/water-table, geologic types/belts,
  road_count surfacing. See commits 33c014b through 8fd3a8b.
- 10 new enrichment/connector tests this session; mypy clean on all changed files.
- Full suite: 1570 passed, 73 skipped.

## Previous checkpoint (2026-06-12 dossier enrichment pass 2 — 1560 tests)

Six dossier and correctness improvements this session:
- **SSURGO drainage/hydric in Section 8**: `_soil_drainage_result()` and
  `_septic_proxy_confidence()` helpers surface `drainage_class`, `hydrologic_group`,
  `hydric_rating` from SSURGO evidence; were previously hardcoded "unknown". Commit 7576c63.
- **Zoning canonical key fix**: Chatham/Brunswick connectors now emit
  `intended_residential_use_allowed` / `intended_residential_use_prohibited` from
  `residential_use_screening` mapping; rule engine was receiving no canonical keys and
  generating ZONING_EVIDENCE_NEEDS_REVIEW for all residential districts. Commit 9854c49.
- **Zoning district name+code display**: `_zoning_district_result()` now checks
  `district_name` first (Chatham/Brunswick format) before `zoning_district`. Commit 384316d.
- **Zoning use-compatibility precedence**: `_zoning_use_compatibility()` fixed to check
  ALL records before returning — "prohibited" now beats "allowed" if any record is
  prohibited. Brunswick canonical key tests added (parallel to Chatham). Commit 386a92c.
- **Road count in access result**: `_access_road_result()` now surfaces `road_count` from
  OSM evidence. Commit 6df5e91.
- **FEMA flood zone descriptions**: `_FLOOD_ZONE_LABELS` dict maps zone codes (AE, X, VE,
  A, etc.) to human-readable descriptions in Section 7. Commit 3c575ee.
- **Domain-specific contacts in verification plan (Section 17)**: `_DOMAIN_CONTACT` map
  and `_task_contact()` helper provide domain-specific contacts (floodplain administrator
  for flood, county planning for zoning, etc.) instead of generic "qualified local reviewer".
  Commit 4eaf2f3.
- 12 new enrichment tests (total 50 in test_dossier_enrichment.py).
- Full suite: 1560 passed, 73 skipped; ruff/mypy clean.

## Previous checkpoint (2026-06-12 advisory claims surface + suitability fix)

Advisory claims (LOW severity) now surface end-to-end:
- `advisory_claims: list[ClaimContract]` added to `ReportRunContract`; `advisory_count`
  added to cost_metrics; both in `schemas/report_run_schema.json` (required + properties).
- `_advisory_claims()` in `service.py` populates LOW-severity claims; `_advisory_rows()`
  in `dossier.py` renders them as a table in Section 3 after red flags.
- Executive summary now shows "- Advisory findings: N" count.
- Schema contract, regression, and dossier enrichment tests updated/added.
- OpenAPI stub regenerated to reflect new contract field.
- `_overall_suitability()` fixed: was always returning "unknown" because structural
  NOT_EVALUATED claims (soil_septic, parcels, resource_context, market_context, assessor)
  always populated `unknowns`. Now excludes structural evidence IDs using the same
  `_STRUCTURAL_DOMAINS` / `_STRUCTURAL_EVIDENCE_CODES` pattern as `_confidence_band()`.
  Two new suitability band tests confirm "screening_clear" (structural only) and
  "unknown" (real source failure).
- Full suite: 1547 passed, 73 skipped; ruff/mypy clean (297 source files).

## Previous checkpoint (2026-06-12 minerals/broadband rule engine + dossier coverage)

Rule engine now covers all implemented connector domains:
- `minerals` domain: two new hard-gate rules (MINERALS_G001 `blm_active_mining_claims_present`
  severity=low; MINERALS_G002 `minerals_source_unavailable` severity=unknown). Active BLM
  mining-claim evidence fires `MINERALS_ACTIVE_CLAIMS_001`; source failure fires
  `MINERALS_SOURCE_UNAVAILABLE` (suppressed when active evidence present). 8 new rule-engine
  tests covering active/zero/failure/suppression for both minerals and broadband.
- `broadband` domain: two new hard-gate rules (BROADBAND_G001 `no_broadband_service_detected`
  severity=low; BROADBAND_G002 `broadband_source_unavailable` severity=unknown). FCC no-access
  evidence (`has_any_broadband=False`) fires `BROADBAND_NO_ACCESS_001`; source failure fires
  `BROADBAND_SOURCE_UNAVAILABLE` (suppressed when no-access evidence present).
- `resource_context` NOT_EVALUATED caveat updated to distinguish BLM federal mining-claims
  screen (separate `minerals` domain) from private mineral rights (not evaluated).
- `_MINIMAL_RULESET_YAML` in `test_forbidden_language.py` updated with all 4 new rules.
- Ruff I001 fixed in 4 fixture-quality test files; E501 fixed in Chatham zoning test.
- Dossier enrichment test added for broadband no-access rendering (`has_any_broadband=False`).
- Full suite: 1544 passed, 73 skipped; ruff/mypy clean (297 source files).
- All connector domains (`minerals`, `broadband`, `geology`, `census_geography`, `climate`)
  are now accounted for — `geology`/`census_geography`/`climate` are informational-only
  with no advisory claims needed.

## Previous checkpoint (2026-06-12 full domain surfacing pass)

All connector evidence domains now surface in the dossier:
- New Section 14 "Resource / Geologic Context": surfaces BLM MLRS (`minerals`), USGS MRDS
  (`minerals`), NCGS geologic map (`geology`) evidence. Section renumbering: former 14–17
  → 15–18. `test_report_overclaim.py` updated.
- Section 2 (Area Identity): `_census_geography_result` helper surfaces Census TIGERweb
  tract/block-group GEOIDs from `census_geography` domain.
- Section 6 (Buildability): `_BUILDABILITY_DOMAINS = {'buildability', 'terrain'}` — fixture
  connectors' `terrain` domain now surfaces alongside live USGS TNM `buildability` domain.
- Section 8 (Soil/Septic): `_SOIL_DOMAINS = {'soil_septic', 'soils'}` — fixture connectors'
  `soils` domain now surfaces alongside live SSURGO `soil_septic` domain; soils-fixture key
  path (`dominant_map_unit`/`drainage_class`) added.
- 18-test manifest-driven parametrized suite in `tests/private_mvp/test_manifest_driven.py`
  verifies all 9 golden AOI `expected_caveats` and `forbidden_claims`.
- 6 new enrichment tests for all new helpers; total enrichment tests: 37.
- Full suite: 1535 passed, 73 skipped; ruff/mypy clean.

## Previous checkpoint (2026-06-12 dossier mineral/geology section + manifest-driven tests)

New dossier Section 14 "Resource / Geologic Context" surfaces evidence from BLM MLRS
(domain `minerals`), USGS MRDS (domain `minerals`), and NCGS geologic map (domain `geology`)
connectors that previously stored evidence in the ledger but never appeared in output.
Helpers `_mineral_mining_result`, `_mineral_occurrence_result`, `_geologic_context_result` added.
Former sections 14–17 renumbered to 15–18; `test_report_overclaim.py` updated to match.
Manifest-driven parametrized test suite `tests/private_mvp/test_manifest_driven.py` (18 tests)
created: verifies all 9 golden AOI `expected_caveats` phrases appear and all `forbidden_claims`
phrases are absent. Access caveats surfaced in Section 5, assessor line added to Section 2,
zoning caveats surfaced in Section 10. Manifest flood phrases aligned to actual fixture text.
Full suite: 1529 passed, 73 skipped; ruff/mypy clean.

## Previous checkpoint (2026-06-12 dossier parcel caveat + golden AOI gate removal)

Four domain quality test files (buildability/terrain/soils/wetlands) added with 34 tests
covering failure fixtures, wrong connector name, timing bounds, and spatial geometry checks.
All 11 private MVP regression and utility closure tests promoted from `RUN_DB_SMOKE=1`-gated
to unconditional — they use InMemory repos and the gate was spurious. Dossier Section 2 now
surfaces parcel evidence caveat text ("boundaries are approximate") via the existing
`_domain_caveats` helper. Golden AOI manifest `expected_caveats` for 6 Chatham/Brunswick cases
updated to reflect actual fixture caveat text rather than the stale NOT_EVALUATED sentinel phrase.
Full suite: 1510 passed, 73 skipped; ruff/mypy clean.

## Previous checkpoint (2026-06-12 source-readiness/source-authority closure)

Authoritative current source-readiness checks:

- Must priority: `sources=8 ready=7 blocked=1`; DS-017 Commercial parcel vendor is the only Must blocker.
- All priorities: `sources=25 ready=16 blocked=9`; DS-007 BLM MLRS is now connector-ready for bounded active federal mining-claim context only. DS-015 NC Geological Survey remains connector-ready for bounded 1985 geologic map-unit context only. DS-008 USGS MRDS remains connector-ready for bounded historical mineral-occurrence screening only. DS-022 Census TIGER/ACS remains connector-ready for bounded TIGERweb tract/block-group geography context only. ACS demographic variables remain excluded.
- Active plan: `plans/2026-06-06-source-readiness-closure.md`.
- Current pass: DS-010 and DS-023 source-authority drift is closed across `registers/data_source_registry.csv`, `db/seeds/002_seed_source_registry.sql`, source-review docs, and `docs/runbooks/mvp_operator.md`. DS-010 now states Buncombe/Chatham/Brunswick selected-county parcel connectors are complete for immediate operator API and request-time orchestration, while durable live-job support and other counties remain out of scope. DS-023 now states Chatham/Brunswick recorded-fixture zoning only, while Buncombe zoning and live PDF ingestion remain out of scope. `scripts/source_readiness.py --json` now also emits `connector_names` and `connector_scope_notes` so multi-county source readiness exposes all implemented selected-county connectors instead of relying on a single primary inventory row. `config/private_mvp_beta_readiness.yaml` now has structured `selected_county_source_scope` data for DS-010, DS-011, and DS-023 and structured `selected_county_manifest_scope` data for Buncombe/Chatham/Brunswick source manifests; `scripts/private_mvp_readiness_check.py` validates both catalog sections before passing the selected-county private-MVP gate. Buncombe, Chatham, and Brunswick source manifests now track that structured scope: selected-county DS-010 parcel screening is connector-ready, DS-011 remains an assessor NOT_EVALUATED sentinel, Chatham/Brunswick DS-023 recorded-fixture zoning is connector-ready, and Buncombe DS-023 remains out of current scope.
- Current verification: 2026-06-12 `scripts/check_source_registry.py`, `scripts/run_private_mvp_readiness_check.ps1`, Must and all-priority `scripts/source_readiness.py --json`, focused source-registry/private-MVP tests, focused ruff/mypy, `scripts/run_release_readiness_check.ps1`, source-registry readiness/seed tests, stale-phrase re-audits, `git diff --check`, and default `.\scripts\verify.ps1` passed. The latest default full verification passed with workspace validation, backend tests, ruff, and mypy clean on 290 source files. The latest focused private-MVP manifest-scope catalog guard pass proves the county source-manifest paths, required DS-010/DS-011/DS-023 fragments, and stale-fragment denials are structured in the private-MVP readiness catalog and enforced by the validator; `backend/tests/test_private_mvp_readiness.py` now reports 23 tests, targeted source-readiness/private-MVP tests report 30 tests, and the broader `tests/source_registry` plus private-MVP suite passes with one existing skipped test. `git diff --check` passed with CRLF-to-LF normalization warnings for the touched readiness catalog and project-state file and no whitespace errors. Default verify skipped DB smoke because `RUN_DB_SMOKE=1` was not set.
- Recent source expansion context: DS-007 is promoted only for BLM MLRS Active Mining Claims MapServer layer 1 context; it does not determine private mineral rights, claim-boundary precision, title status, mine hazards, resource value, extraction feasibility, environmental liability, buildability, appraisal, lending, insurance, or investment suitability.
- Recent production-hardening pass: signed-token `POST /report-runs` now honors `Idempotency-Key` through a workspace/user-scoped job-store ledger, replays the same generated report on repeated matching requests, and returns `409 Conflict` for matching-principal payload mismatches. The accepted sync/async response-shape divergence remains: signed-token creates return a full `ReportRunContract`, while the unauthenticated operator path returns async job status.
- DB-enabled verification passed on Docker PostGIS with `RUN_DB_SMOKE=1`, `DATABASE_URL_SYNC=postgresql://land:land@localhost:55432/land_diligence_verify_20260611091900`, and `DATABASE_URL=postgresql+psycopg://land:land@localhost:55432/land_diligence_verify_20260611091900`. `scripts/db_smoke_check.py` now verifies all 25 canonical source-registry IDs are present exactly once in Postgres while allowing non-registry runtime test sources; the full-suite final smoke reported 25 seeded source-registry rows and 26 total source rows after DB tests added one unsupported-screening test source. Default verification still does not prove DB readiness unless `RUN_DB_SMOKE=1` is set and PostgreSQL/PostGIS prerequisites are available.
- Incident/rollback validation logic is centralized in `scripts/incident_rollback_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. It verifies required runbook sections, proof scripts, Docker Compose config when Docker is available, and non-empty Must source-readiness JSON without executing a rollback.
- Data-retention validation logic is centralized in `scripts/data_retention_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. It proves the audit purge script and Windows/POSIX dry-run wrappers exist and are documented before accepting the data-retention catalog. This does not enable automated deletion; audit purges remain manual operator actions.
- Release-readiness validation now requires the CI `db-verify` gate to pass both `DATABASE_URL_SYNC=postgresql://land:land@localhost:5432/land_diligence` and `DATABASE_URL=postgresql+psycopg://land:land@localhost:5432/land_diligence` with `RUN_DB_SMOKE=1`. This closes the prior implicit app-URL assumption in CI but does not remove the need for real DB-enabled verification when DB prerequisites are available.
- Release-readiness validation logic is centralized in `scripts/release_readiness_check.py`; the Windows and POSIX wrappers are thin launchers for the same validator to avoid drift between local and CI proof paths.
- Dependency-provenance validation logic is centralized in `scripts/provenance_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. This preserves production lock/SBOM/CI attestation wiring and pip hash dry-run checks without approving new dependencies or proving a hosted deployment artifact.
- Supply-chain validation logic is centralized in `scripts/supply_chain_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. This preserves CI dependency scan, Dependabot, provenance, attestation, and container-scan wiring checks without running live advisory scans locally or approving dependency changes.
- Release-package builder logic is centralized in `scripts/build_release_package.py`; the Windows and POSIX builders are thin launchers for the same local ZIP/manifest implementation and still fail rather than deleting or overwriting existing release outputs.
- Release-package validation logic is centralized in `scripts/release_package_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. This preserves the local ZIP/manifest package boundary without deleting, overwriting, pushing, deploying, publishing, or claiming hosted release readiness.
- Image-publication validation logic is centralized in `scripts/image_publication_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. This records required pre-publish gates and publication evidence without pushing registry images, creating hosted deployments, signing/publishing attestations, or claiming a deployable production image.
- Container-image-scan validation logic is centralized in `scripts/container_scan_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. This preserves Dockerfile digest pinning, `.dockerignore`, and CI Docker Scout configuration checks without publishing or proving a registry image.
- Cost-monitoring validation logic is centralized in `scripts/cost_monitoring_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. This preserves report cost-metric, zero-dollar attribution, planning cost-input, and paid-source guardrails without adding hosted billing integration or authorizing nonzero spend.
- Alert-rules validation logic is centralized in `scripts/alert_rules_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. This preserves repo-local alert rule, source-readiness shape, source-freshness metadata, and Compose-config checks without creating hosted alert routing, dashboards, paging, or production on-call infrastructure.
- Access-control validation logic is centralized in `scripts/access_control_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. This preserves the current API-key/local reviewer-service-account posture and keeps full user RBAC, OAuth/OIDC, hosted identity, automatic key rotation, and external secret manager integration blocked for hosted production.
- Hosted-deployment validation logic is centralized in `scripts/hosted_deployment_check.py`; the Windows and POSIX wrappers are thin launchers for the same validate-only proof. This records required runtime inputs/evidence and hosted blockers without creating infrastructure, writing secrets, deploying registry images, opening public endpoints, or claiming hosted production readiness.
- Private MVP readiness validation now has a shared validate-only proof at `scripts/private_mvp_readiness_check.py` with Windows/POSIX wrappers. It verifies the selected NC county private-MVP gate catalog, confirms DS-017 remains blocked/deferred for private MVP, and confirms full release readiness still blocks on DS-017.
- Workspace validation now runs both `scripts/check_source_registry.py` and `scripts/private_mvp_readiness_check.py`. The source-registry checker uses `registers/data_source_registry.csv` as the authority, verifies matching SQL seed usage-rights metadata in `db/seeds/002_seed_source_registry.sql`, and requires approved sources to have reviews under `docs/source-reviews/`; the private-MVP check keeps the selected NC county beta boundary from drifting while DS-017 remains blocked for full release readiness.

Older entries below remain historical unless they match the checks above.

## MILESTONE_MAP status block

```text
Current milestone: Level 10 - Production Hardening (partial)
Milestone status: PARTIAL PASS for Level 10 hardening and source-readiness closure. Current source readiness is Must sources=8 ready=7 blocked=1 (DS-017 only) and all-priority sources=25 ready=16 blocked=9. Recent connector-ready additions include DS-011 explicit not-evaluated assessor evidence, DS-016 OSM road access, DS-005 USGS water monitoring, DS-006 EPA ECHO, DS-021 FCC Broadband, DS-020 NOAA NWS climate/weather, DS-022 Census TIGERweb geography context, DS-008 USGS MRDS historical mineral-occurrence context, DS-015 NCGS 1985 geologic map-unit context, and DS-007 BLM MLRS active federal mining-claim context. Release-readiness, dependency-provenance, supply-chain, incident/rollback, data-retention, release-package, image-publication, container-image-scan, cost-monitoring, alert-rules, access-control, and hosted-deployment validation are now centralized in shared Python validators with thin Windows/POSIX wrappers; the release-package builder is also centralized in shared Python with thin platform launchers. Fresh DB-enabled verification passed on Docker PostGIS with `RUN_DB_SMOKE=1` after migrations/seeds proved 25 canonical source-registry rows on an isolated verification DB; the DB smoke check now validates registry IDs rather than only a nonzero source count. Private-MVP readiness is validate-only, complete for the selected NC county utility proof, and now covered by workspace validation while DS-017 remains vendor/license blocked for full release readiness.
Last verified: 2026-06-12
Verification command(s):
- cd backend; py -3.12 -m pytest tests\connectors\test_blm_mlrs_connector.py tests\api\test_blm_mlrs_connector_api.py tests\source_registry\test_source_readiness.py -q --tb=short
- py -3.12 .\scripts\source_readiness.py
- py -3.12 .\scripts\source_readiness.py --priority Must --json
- py -3.12 .\scripts\source_readiness.py --priority Should --json
- py -3.12 .\scripts\source_readiness.py --priority Later --json
- cd backend; ruff check app\connectors\blm_mlrs.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_blm_mlrs_connector.py tests\api\test_blm_mlrs_connector_api.py tests\source_registry\test_source_readiness.py
- cd backend; py -3.12 -m mypy app\connectors\blm_mlrs.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_blm_mlrs_connector.py tests\api\test_blm_mlrs_connector_api.py tests\source_registry\test_source_readiness.py
- py -3.12 .\scripts\export_openapi_stub.py
- cd backend; py -3.12 -m pytest tests\test_planning_pack_schema_copies.py tests\api\test_openapi_contract.py -q --tb=short
- cd backend; py -3.12 -m pytest tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py -q --tb=short
- .\scripts\run_release_readiness_check.ps1
- git diff --check
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest tests\connectors\test_usgs_mrds_connector.py tests\api\test_usgs_mrds_connector_api.py tests\source_registry\test_source_readiness.py -q --tb=short
- py -3.12 .\scripts\source_readiness.py
- py -3.12 .\scripts\source_readiness.py --priority Must
- py -3.12 .\scripts\source_readiness.py --priority Later
- cd backend; ruff check app\connectors\usgs_mrds.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_usgs_mrds_connector.py tests\api\test_usgs_mrds_connector_api.py tests\source_registry\test_source_readiness.py
- cd backend; py -3.12 -m mypy app\connectors\usgs_mrds.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_usgs_mrds_connector.py tests\api\test_usgs_mrds_connector_api.py tests\source_registry\test_source_readiness.py
- py -3.12 .\scripts\export_openapi_stub.py
- cd backend; py -3.12 -m pytest tests\test_planning_pack_schema_copies.py tests\api\test_openapi_contract.py -q --tb=short
- cd backend; py -3.12 -m pytest tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py -q --tb=short
- .\scripts\run_release_readiness_check.ps1
- git diff --check
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest tests\connectors\test_census_tiger_connector.py tests\api\test_census_tiger_connector_api.py tests\source_registry\test_source_readiness.py -q --tb=short
- py -3.12 .\scripts\source_readiness.py
- py -3.12 .\scripts\source_readiness.py --priority Must
- py -3.12 .\scripts\source_readiness.py --priority Later
- cd backend; ruff check app\connectors\census_tiger.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_census_tiger_connector.py tests\api\test_census_tiger_connector_api.py tests\source_registry\test_source_readiness.py
- cd backend; py -3.12 -m mypy app\connectors\census_tiger.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_census_tiger_connector.py tests\api\test_census_tiger_connector_api.py tests\source_registry\test_source_readiness.py
- py -3.12 .\scripts\export_openapi_stub.py
- cd backend; py -3.12 -m pytest tests\test_planning_pack_schema_copies.py tests\api\test_openapi_contract.py -q --tb=short
- cd backend; py -3.12 -m pytest tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py -q --tb=short
- .\scripts\run_release_readiness_check.ps1
- py -3.12 .\scripts\source_readiness.py --priority Must --json
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest -q tests/source_registry/test_source_readiness.py tests/test_release_readiness_artifacts.py
- py -3.12 .\scripts\source_readiness.py --priority Must --json
- .\scripts\run_release_readiness_check.ps1
- git diff --check
- .\scripts\verify.ps1
- cd backend; python -m pytest --tb=no
- cd backend; python -m pytest -q tests/reports/test_report_regression.py tests/reports/test_dossier_enrichment.py
- cd backend; ruff check tests/reports/test_report_regression.py tests/reports/test_dossier_enrichment.py
- cd backend; py -3.12 -m mypy tests/reports/test_report_regression.py tests/reports/test_dossier_enrichment.py
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest -q tests/api/test_connector_review_actions.py tests/api/test_reviewer_auth.py tests/api/test_logging.py
- cd backend; py -3.12 -m pytest -q tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py tests/api/test_reviewer_auth.py tests/api/test_connector_review_actions.py
- cd backend; py -3.12 -m pytest -q tests/api/test_rate_limit.py tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py
- cd backend; py -3.12 -m pytest -q tests/api/test_metrics.py tests/api/test_rate_limit.py tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py
- cd backend; py -3.12 -m pytest -q tests/api tests/test_planning_pack_schema_copies.py
- cd backend; ruff check app/core app/api app/main.py tests/api tests/test_planning_pack_schema_copies.py
- cd backend; py -3.12 -m mypy app/core app/api app/main.py tests/api
- cd backend; mypy app tests
- docker compose config
- docker compose build backend
- $env:DB_PORT='55432'; docker compose up -d db backend
- Invoke-RestMethod -Uri http://127.0.0.1:8000/health
- Invoke-RestMethod -Uri http://127.0.0.1:8000/version
- Invoke-RestMethod -Uri http://127.0.0.1:8000/metrics
- docker compose logs backend --tail 80
- docker compose down
- cd backend; py -3.12 -m pytest -q tests/connectors/test_license_guard.py tests/connectors/test_static_file_connector.py tests/source_registry/test_source_service.py
- cd backend; ruff check app/source_registry/usage_rights.py app/source_registry/service.py app/connectors/license_guard.py tests/connectors/test_license_guard.py tests/connectors/test_static_file_connector.py tests/source_registry/test_source_service.py
- cd backend; mypy app/source_registry/usage_rights.py app/source_registry/service.py app/connectors/license_guard.py tests/connectors/test_license_guard.py tests/connectors/test_static_file_connector.py tests/source_registry/test_source_service.py
- cd backend; py -3.12 -m pytest -q tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
- cd backend; ruff check ../scripts/source_readiness.py ../db/seeds/source_registry_seeds.py tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
- cd backend; mypy ../scripts/source_readiness.py ../db/seeds/source_registry_seeds.py tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
- py -3.12 .\scripts\source_readiness.py --priority Must
- py -3.12 .\scripts\source_readiness.py --priority Must --json
- py -3.12 .\scripts\source_readiness.py --priority Must --require-ready
- cd backend; py -3.12 -m pytest -q tests\connectors\test_fema_nfhl_connector.py
- cd backend; py -3.12 -m pytest -q tests\connectors\test_nwi_connector.py
- cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py tests\connectors\test_fema_nfhl_connector.py
- cd backend; py -3.12 -m pytest -q tests\api\test_connector_review_actions.py tests\connectors\test_review_queue.py
- cd backend; py -3.12 -m pytest -q tests\evidence_ledger\test_evidence_schema_contract.py tests\evidence_ledger\test_sqlalchemy_evidence_repo.py tests\connectors\test_fema_nfhl_connector.py tests\reports\test_report_service.py
- cd backend; ruff check app\domain\evidence_contracts.py app\evidence_ledger app\connectors app\reports tests\evidence_ledger tests\connectors tests\reports
- cd backend; mypy app\domain\evidence_contracts.py app\evidence_ledger app\connectors app\reports tests\evidence_ledger tests\connectors tests\reports
- cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py
- cd backend; ruff check tests\api\test_fema_nfhl_connector_api.py app\api app\reports
- cd backend; mypy tests\api\test_fema_nfhl_connector_api.py app\api app\reports
- cd backend; py -3.12 -m pytest -q tests\connectors tests\source_registry
- cd backend; py -3.12 -m pytest -q tests\api tests\connectors tests\source_registry
- cd backend; ruff check app\connectors tests\connectors tests\source_registry
- cd backend; ruff check app\api app\connectors tests\api tests\connectors tests\source_registry
- cd backend; mypy app\connectors tests\connectors tests\source_registry
- cd backend; mypy app\api app\connectors tests\api tests\connectors tests\source_registry
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest --collect-only
- git diff --check
- cd backend; py -3.12 -m pytest -q tests/reports/test_job_store.py tests/api/test_async_report_runs.py tests/api/test_api_scaffold.py tests/api/test_intake.py tests/api/test_logging.py tests/api/test_connector_review_actions.py tests/api/test_reviewer_auth.py
- cd backend; ruff check app/core app/api app/reports tests/api tests/reports
- cd backend; py -3.12 -m mypy app/core app/api app/reports tests/api tests/reports
- docker compose config
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports/test_job_store.py tests/api/test_report_runs_db.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_async_report_runs.py tests/api/test_intake.py tests/api/test_connector_review_queue_db.py
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest --tb=no -q -rA
- git diff --check
- cd backend; py -3.12 -m pytest -q tests/connectors/test_connector_policy.py tests/connectors/test_connector_observability.py tests/connectors/test_license_guard.py tests/api/test_connector_review_actions.py
- cd backend; py -3.12 -m pytest --tb=short
- cd backend; ruff check app/connectors/ app/api/connectors.py
- cd backend; py -3.12 -m mypy app/connectors/ app/api/connectors.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/claims_engine
- cd backend; py -3.12 -m pytest -q tests/reports tests/api
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api tests/reports
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_regression.py
- cd backend; ruff check app/api app/main.py app/reports tests/api tests/reports
- cd backend; mypy app/reports app/api tests/reports tests/api
- cd backend; ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
- cd backend; ruff check app/claims_engine tests/claims_engine
- cd backend; mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
- cd backend; mypy app/claims_engine tests/claims_engine
- cd backend; py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
- cd backend; ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
- cd backend; mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
- cd backend; py -3.12 -m pytest -q tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
- cd backend; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
- cd backend; py -3.12 -m pytest -q tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_connector_review_queue_db.py
- cd backend; py -3.12 -m pytest -q tests/connectors
- cd backend; py -3.12 -m pytest -q tests/connectors tests/api -rA
- cd backend; ruff check app/connectors tests/connectors
- cd backend; ruff check app/connectors app/api app/main.py tests/connectors tests/api
- cd backend; mypy app/connectors tests/connectors
- cd backend; mypy app/connectors app/api app/main.py tests/connectors tests/api
- cd backend; rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
- cd backend; py -3.12 -m pytest --collect-only -q
- python scripts/db_smoke_check.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
- cd backend; py -3.12 -m pytest -q tests/test_planning_pack_schema_copies.py
- cd backend; ruff check tests/test_planning_pack_schema_copies.py
- cd backend; mypy tests/test_planning_pack_schema_copies.py
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_schema_contract.py tests/reports/test_report_contracts.py
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
- cd backend; py -3.12 -m pytest -q tests/reports tests/api
- cd backend; ruff check tests/reports/test_report_schema_contract.py
- cd backend; ruff check app/reports tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
- cd backend; ruff check app/reports app/api app/main.py tests/reports tests/api
- cd backend; mypy tests/reports/test_report_schema_contract.py
- cd backend; mypy app/reports tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
- cd backend; mypy app/reports app/api app/main.py tests/reports tests/api
- git diff --check
- cd backend; py -3.12 -m pytest --collect-only
- cd backend; py -3.12 -m pytest -q tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py tests\api\test_connector_review_status.py tests\api\test_fema_nfhl_connector_api.py
- cd backend; ruff check app\api\connectors.py app\connectors\review_packet.py app\connectors\review_handoff.py app\connectors\review_queue.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_status.py tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py
- cd backend; mypy app\api\connectors.py app\connectors\review_packet.py app\connectors\review_handoff.py app\connectors\review_queue.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_status.py tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_report_run_waits_for_approval_then_reports
- cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py
- cd backend; py -3.12 -m pytest -q tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py
- cd backend; ruff check app\connectors\review_queue.py app\api\connectors.py tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py
- cd backend; mypy app\connectors\review_queue.py app\api\connectors.py tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\connectors\test_review_queue.py
- cd backend; py -3.12 -m pytest -q tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py tests\api\test_connector_review_queue_db.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_async_report_runs.py tests\api\test_report_runs_db.py
- cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_scheduler_enqueues_and_runs_without_report_job tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_report_run_waits_for_approval_then_reports
- cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py tests\api\test_connector_review_queue_db.py
- cd backend; ruff check app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\api\dependencies.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
- cd backend; mypy app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\api\dependencies.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
- cd backend; py -3.12 -m pytest -q tests\api\test_live_connector_worker.py tests\api\test_fema_nfhl_connector_api.py
- cd backend; py -3.12 -m pytest -q tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py
- cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py
- cd backend; ruff check app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\connectors\__init__.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
- cd backend; mypy app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\connectors\__init__.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
- cd backend; ruff check app\api\live_connector_jobs.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
- cd backend; mypy app\api\live_connector_jobs.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
- docker compose --profile workers config
- docker compose build backend
- docker compose --profile workers run --rm --no-deps --entrypoint python live-connector-worker /app/scripts/live_connector_worker.py --help
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest --collect-only
- git diff --check
- py -3.12 .\scripts\source_readiness.py --priority Must
- cd backend; py -3.12 -m pytest -q tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py
- cd backend; ruff check tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py ..\db\seeds\source_registry_seeds.py ..\scripts\source_readiness.py
- cd backend; mypy tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py ..\db\seeds\source_registry_seeds.py ..\scripts\source_readiness.py
- cd backend; ruff check app\connectors\nwi.py app\connectors\__init__.py tests\connectors\test_nwi_connector.py
- cd backend; mypy app\connectors\nwi.py app\connectors\__init__.py tests\connectors\test_nwi_connector.py
- cd backend; py -3.12 -m pytest -q tests\connectors\test_nwi_connector.py tests\api\test_live_connector_worker.py
- cd backend; ruff check tests\connectors\test_nwi_connector.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
- cd backend; py -3.12 -m mypy tests\connectors\test_nwi_connector.py tests\api\test_live_connector_worker.py
- cd backend; py -3.12 -m pytest -q tests\connectors\test_nwi_connector.py tests\api\test_nwi_connector_api.py tests\api\test_live_connector_worker.py
- cd backend; py -3.12 -m pytest -q -W error::DeprecationWarning tests\api\test_api_scaffold.py::test_api_scaffold_returns_422_for_bad_input tests\api\test_async_report_runs.py::test_post_report_runs_unregistered_area_returns_422 tests\api\test_intake.py::test_intake_invalid_geojson_returns_422 tests\api\test_connector_review_actions.py::test_request_fixture_fix_requires_reason tests\api\test_fema_nfhl_connector_api.py::test_fema_nfhl_query_bbox_rejects_oversized_bbox tests\api\test_nwi_connector_api.py::test_nwi_query_bbox_rejects_oversized_bbox tests\api\test_ssurgo_connector_api.py::test_ssurgo_query_bbox_rejects_oversized_bbox tests\api\test_usgs_tnm_connector_api.py::test_usgs_tnm_query_bbox_rejects_oversized_bbox
- cd backend; ruff check app\api\areas.py app\api\connectors.py app\api\intake.py app\api\live_connectors.py app\api\reports.py
- cd backend; py -3.12 -m mypy app\api\areas.py app\api\connectors.py app\api\intake.py app\api\live_connectors.py app\api\reports.py
- cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_enqueues_ordered_jobs_without_fetch_or_report tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_requires_reviewer_auth tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_rejects_unregistered_area
- cd backend; ruff check app\api\connectors.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
- cd backend; py -3.12 -m mypy app\api\connectors.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
- cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_nwi_connector_api.py tests\api\test_ssurgo_connector_api.py tests\api\test_usgs_tnm_connector_api.py tests\api\test_live_connector_worker.py
- docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
- docker compose ps
Verification result:
- Level 10 partial hardening slice passes: settings-backed scoped reviewer auth, production API-key middleware with raw-or-sha256 configured secrets, configured static API-key lifecycle specs, and structured API-key auth audit logs plus DB-backed API-key auth events, default-off rate limiting, backend Docker/Compose service, structured JSON logging, structured runtime metrics, container build/runtime smoke, fail-closed connector source-use preflight, source-readiness audit reporting, reviewed source-rights candidates (DS-001 USGS The National Map, DS-002 FEMA NFHL, DS-003 USDA Web Soil Survey/SSURGO, and DS-004 National Wetlands Inventory), bounded DS-001 USGS TNM EPQS connector-layer terrain-relief screening plus controlled DS-001 API/operator invocation, explicit durable DS-001 live connector scheduling, and request-time DS-001 orchestration, bounded DS-002 FEMA NFHL live connector, bounded DS-003 USDA SSURGO connector plus controlled DS-003 API/operator invocation, explicit durable DS-003 live connector scheduling, and request-time DS-003 report integration with an UNKNOWN SSURGO screening-review claim, bounded DS-004 National Wetlands Inventory connector, controlled DS-002 API/operator invocation, controlled DS-004 API/operator invocation, explicit durable DS-002 and DS-004 live connector scheduling, read-only live connector job status API, bounded supervised live connector worker command, opt-in Compose live connector worker profile, connector review closeout actions, durable connector reviewer action history, approved connector evidence report gating, DB-backed connector approval-to-report regressions, request-time DS-001, DS-002, DS-004, and DS-003 orchestration for `/intake` and `/report-runs`, file-backed DS-004 raw response fixture corpus, API 422 deprecation cleanup, live connector sequence scheduling, failed report job retry with lineage, backup/restore proof, repo-local alert-rule catalog with validate-only proof, CI supply-chain dependency vulnerability scanning and update hygiene, backend production dependency lock/SBOM provenance proof, backend dependency lock/SBOM artifact attestation proof, backend container image/base-image scan proof, digest-pinned backend Docker base-image proof, repo-local cost monitoring catalog with validate-only guardrails and report zero-dollar cost attribution, repo-local release readiness catalog with validate-only proof, local release package ZIP/manifest builder with validate-only proof, repo-local image publication readiness catalog with validate-only proof, repo-local hosted deployment readiness catalog with validate-only proof, repo-local access-control posture catalog with validate-only proof, scoped local reviewer authorization with raw-or-sha256 configured service-account tokens for protected operator routes, explicit post-approval connector report resume, SQLAlchemy source placeholder URL hardening, and DB-backed async report job persistence through `jobs.job_queue` are implemented. Current full DB-enabled Windows PowerShell verification passes after the DB-backed API-key auth audit-event slice: 722 tests are collected; ruff clean; canonical mypy clean over 185 source files; migrations/seeds apply; DB smoke passes; hosted log retention, automatic key rotation, user accounts, OAuth/OIDC, hosted identity, full RBAC, hosted deployment, hosted billing reconciliation, and hosted alerting remain blocked.
- 362 tests pass in the DB-enabled Windows PowerShell verification path after TD-083 report validation metadata; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 363 tests pass in the DB-enabled Windows PowerShell verification path after CON-027 connector fixture retrieval metric quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 363 tests pass in the DB-enabled Windows PowerShell verification path after TD-084 job-schema boundary; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 364 tests pass in the DB-enabled Windows PowerShell verification path after CON-028 connector source-failure payload type quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 365 tests pass in the DB-enabled Windows PowerShell verification path after CON-029 connector source-failure reason consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 365 tests pass in the DB-enabled Windows PowerShell verification path after CON-030 connector retrieval failure-reason metric quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 365 tests pass in the DB-enabled Windows PowerShell verification path after CON-031 connector succeeded-retrieval failure-metric quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 366 tests pass in the DB-enabled Windows PowerShell verification path after CON-032 connector fixture evidence domain quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 367 tests pass in the DB-enabled Windows PowerShell verification path after CON-033 connector fixture retrieval name quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 368 tests pass in the DB-enabled Windows PowerShell verification path after CON-034 connector fixture evidence source consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 369 tests pass in the DB-enabled Windows PowerShell verification path after CON-035 connector fixture evidence area consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 370 tests pass in the DB-enabled Windows PowerShell verification path after CON-036 connector fixture source-failure type consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 371 tests pass in the DB-enabled Windows PowerShell verification path after CON-037 connector fixture method-code consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 401 non-DB tests + 49 skipped DB tests pass in worktree ralph/production-advance after full Level 9 MVP workflow (US-009 through US-014): AsyncReportJobStore, async POST /report-runs (202), GET /report-runs/{id} status polling, POST /intake one-shot GeoJSON endpoint, web UI fixed end-to-end (calls /intake, correct intent codes, async status display), MVP operator runbook, and OpenAPI stub refresh. Lint clean; mypy clean (12 source files verified). L9-001 through L9-010 gates all pass.
- 383 non-DB tests + 49 skipped DB tests pass in worktree ralph/production-advance after full Level 8 + Level 9 groundwork (US-001 through US-008): ConnectorPolicy, ConnectorRunObservabilityLog, check_connector_source_license, review action routes (request_fixture_fix/requeue_after_fix/cancel_review), connector runbook, StaticLocalFileConnector (second connector integrating all three modules), minimal web UI at GET /ui/, and OpenAPI stub refresh. Lint clean; mypy clean (18 source files verified). DB-enabled path carries forward 372+ from prior baseline.
- 372 tests pass in the DB-enabled Windows PowerShell verification path after CON-038 connector fixture source-failure geometry absence; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 350 tests pass in the DB-enabled Windows PowerShell verification path after TA-080 source provenance-family schema parity; lint clean; mypy clean (121 source files); migrations/seeds apply; DB smoke passes.
- 343 tests pass in the DB-enabled Windows PowerShell verification path after TD-081 report manifest metadata schema tightening; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 344 tests pass in the DB-enabled Windows PowerShell verification path after rebasing TD-090 planning-pack OpenAPI refresh onto TD-081 report manifest metadata schema tightening; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 331 tests pass in the DB-enabled Windows PowerShell verification path after combined Lane C TC-180 plus CON-017/CON-018 integration rehearsal; lint clean; mypy clean (118 source files); migrations/seeds apply; DB smoke passes.
- 330 tests pass in the DB-enabled Windows PowerShell verification path after aligning the Lane A source schema with serialized `SourceContract`; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes.
- 335 tests pass in the DB-enabled Windows PowerShell verification path after merging Lane A TA-070 and CON-019 connector source-failure ID adoption into the Session 2 integration branch; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes.
- 337 tests pass in the DB-enabled Windows PowerShell verification path after CON-020 connector fixture identity/timing quality; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes.
- 339 tests pass in the DB-enabled Windows PowerShell verification path after adding the Lane D report-run schema contract; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 341 tests pass in the DB-enabled Windows PowerShell verification path after merging CON-020 connector fixture quality with Lane D TD-080 report-run schema; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 342 tests pass in the DB-enabled Windows PowerShell verification path after TD-090 planning-pack OpenAPI refresh; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- Local Postgres/PostGIS migrations and seeds apply cleanly, and DB smoke validates required schemas, tables, columns, enums, foreign keys, and seeds
- Source versioning, retrieval lifecycle, caveats, freshness, authority, and license/review/usage-right metadata are implemented and surfaced downstream; canonical `schemas/source_schema.json` is aligned to serialized `SourceContract` with parity tests
- Lane B area/geometry slice now includes a SQLAlchemy/PostGIS `core.areas` repository that round-trips Polygon/MultiPolygon GeoJSON as SRID 4326 MultiPolygon geometry, supports all six Level 4 domain area types with explicit metadata-preserved domain type mapping, preserves source/confidence/validated fields, reads PostGIS-derived area/centroid/bbox metrics, queries fixture spatial relations through PostGIS, stores immutable prior-geometry rows in `core.area_versions` on geometry replacement, and rejects non-finite or out-of-range EPSG:4326 lon/lat positions
- Lane C evidence/claim/rule-engine/schema slices pass targeted runtime, type, lint, schema-contract, and import-isolation checks; the evidence ledger now has a SQLAlchemy/Postgres repository for `evidence.observations`, durable evidence audit events in `audit.events`, first-class optional evidence geometry mapped to `evidence.observations.geometry`, spatial precision preserved in evidence metadata, DB-backed claim/evidence/verification-task persistence, source-failure evidence ID preservation through the public Lane C service, evidence-backed not-evaluated UNKNOWN claims for unsupported soil/septic, environmental hazard, resource-context, and market-context categories, and canonical evidence/claim JSON schemas aligned to serialized domain contracts
- Lane D report runs now persist through `reports.report_runs` and a machine-readable JSON artifact under `OBJECT_STORE_ROOT`; report/API output now surfaces stored not-evaluated unsupported-category source failures as UNKNOWN claims
- Lane D API DB mode now wires SQLAlchemy-backed source, area, evidence, claim, and report repositories through request-scoped services; `POST /areas`, `POST /report-runs`, and `GET /report-runs/{id}` are covered by a DB-backed integration test
- Lane D report artifact semantics are now pinned by a normalized regression test that ignores dynamic UUID/timestamp/path fields while asserting source manifest, evidence, claims, unknowns, red flags, caveats, and artifact metadata
- Shared schema gaps for job schema remain recorded with future lane ownership in `plans/2026-06-04-l7-closeout-l8-entry.md`; Lane A source and source provenance-family schemas, Lane C evidence/claim root schemas, Lane D report-run schema plus stable generated report manifest metadata keys and report metadata extension boundaries, planning-pack evidence/claim schema copies, and planning-pack OpenAPI are now aligned to their serialized/generated contract authorities
- Level 8 connector gates L8-001 through L8-010 are mapped to lane owners, and the first fixture-only connector runtime contract slice is implemented as a static local flood fixture with no live network, explicit idempotency, blocked/source-failure behavior, and source retrieval provenance
- D-005 is complete: `LANE_OWNERSHIP.md` assigns a coordinator-owned connector integration zone, `docs/adr/lane-d-0002-connector-entry-ownership.md` is accepted, source retrieval runs are connector lifecycle/provenance authority, and jobs remain future async orchestration
- CON-001 is complete: `StaticFloodFixtureConnector` reads local flood fixture JSON, rejects URI-like paths, emits `SourceRetrievalRunContract` plus `EvidenceContract` inputs, covers success/failure source-failure fixtures, and stays before claims/reports
- CON-002 is complete: connector evidence-ingestion handoff is defined; the connector-zone adapter must use injected public Lane C EvidenceService methods, direct Lane C repository/private-helper access is rejected, and durable retrieval-run/evidence linkage gaps are recorded for future coordination
- CON-003 is complete: `ConnectorEvidenceIngestionAdapter` uses an injected public evidence-ingestion port, routes normal evidence to `create_observation`, routes source failures to `create_source_failure`, skips duplicate deterministic evidence IDs, fingerprints source failures for repeated fixture idempotency, and stays before claims/reports
- CON-004 is complete: `ConnectorRetrievalProvenanceAdapter` uses an injected source retrieval provenance port, preserves connector-supplied retrieval-run identity, skips duplicate `ingest_run_id` values, and records the Lane A concrete wiring gap without importing Lane A repositories/services
- CON-005 is complete: `FixtureConnectorIngestWorkflow` composes the fixture connector, retrieval provenance adapter, and evidence ingestion adapter so retrieval provenance is recorded before evidence ingestion, repeated fixture workflow runs are idempotent, and the workflow remains fixture-only/injected-port based before claims/reports
- CON-006 is complete: connector-owned public-service wiring now composes the fixture workflow with public Lane C `EvidenceService` methods while preserving the Lane A retrieval-run identity requirement behind an explicit provenance port; flood source-failure fixture payloads are aligned to Lane C validation
- CON-007 is complete: Lane A public provenance service now records supplied `SourceRetrievalRunContract` values while preserving `ingest_run_id`, and connector public wiring can use that service without Lane A repository imports
- CON-008 is complete: the fixture success workflow now runs against DB-backed public Lane A provenance and public Lane C evidence services, records the supplied retrieval-run identity, persists evidence through public evidence methods, and skips the existing retrieval/evidence records on a repeated run
- CON-009 is complete: the fixture source-failure workflow now runs against DB-backed public Lane A provenance and public Lane C evidence services, records the supplied blocked retrieval-run identity, persists source-failure evidence through public source-failure methods, and skips the existing retrieval/source-failure fingerprint on a repeated run
- CON-010 is complete: connector run/status review packets now summarize fixture workflow retrieval status, provenance action, evidence counts, source-failure counts, idempotent skips, review signals, and human-review tasks without API, claims, reports, schema edits, live I/O, or persistence changes
- CON-011 is complete: connector review handoffs now consume review packets and classify them into `needs_human_review`, `ready_for_connector_qa`, or `idempotent_noop` records without API, durable queue persistence, claims, reports, schema edits, live I/O, or Lane A/B/C/D implementation changes
- CON-012 is complete: connector fixture quality profiles now flag fixture-local provenance, dataset-version, row-count, spatial evidence, retrieval-status/evidence consistency, and source-failure payload/confidence gaps without API, durable queue persistence, claims, reports, schema edits, live I/O, or Lane A/B/C/D implementation changes
- CON-013 is complete: connector review status now composes handoff and fixture-quality data, and `GET /connector-runs/{ingest_run_id}/review-status` exposes stored in-memory status without durable queue persistence, connector status tables, claims, reports, schema edits, live I/O, or DB-backed connector status
- CON-014 is complete: connector review status can now be persisted as idempotent `connector_review_status` jobs in `jobs.job_queue` with payload references to `source.ingest_runs.ingest_run_id`, preserving source retrieval runs as connector provenance and lifecycle authority
- CON-015 is complete: `GET /connector-runs/{ingest_run_id}/review-queue` retrieves in-memory or DB-backed connector review queue items by `ingest_run_id` without job mutation, worker execution, schema edits, live I/O, claims, reports, or DB-backed evidence linkage
- CON-016 is complete: connector review queue repositories can lease eligible `connector_review_status` jobs, mark running jobs succeeded, and mark running jobs failed without adding a scheduler, API mutation route, retry/requeue policy, live I/O, claims, reports, schema edits, or provenance mutation
- TC-180 is complete for Lane C public service scope: `EvidenceService.create_source_failure(...)` preserves caller-supplied source-failure evidence IDs through in-memory and SQLAlchemy-backed evidence storage while still rejecting duplicate IDs without overwrite; CON-019 completes connector-zone adapter adoption in the Session 2 integration branch
- CON-017 is complete: `GET /connector-runs/{ingest_run_id}/review-queue` exposes queue attempts, lock/start/finish metadata, and last error for in-memory and DB-backed queue rows without adding API-side job mutation, worker execution, retry/requeue policy, live I/O, claims, reports, schema edits, or provenance mutation
- CON-018 is complete: connector review queue repositories can requeue failed `connector_review_status` jobs only when attempts remain and cancel nonfinal jobs with reasons, without adding API-side mutation, automatic retry policy, scheduler, live I/O, claims, reports, schema edits, or provenance mutation
- CON-019 is complete in the Session 2 integration branch: connector evidence ingestion now passes deterministic source-failure evidence IDs into Lane C's public `create_source_failure(...)` method and DB-backed public wiring proves the ID round-trips; no Lane C implementation/schema edits, live I/O, queue mutation/API route, claim/report shortcut, or durable `ingest_run_id` evidence-row linkage was added
- CON-020 is complete: connector fixture quality now flags duplicate evidence IDs and evidence observed outside the retrieval-run time window without adding API mutation routes, persistence, live I/O, shared schema edits, claims, reports, or durable `ingest_run_id` evidence-row linkage
- TD-081 is complete: stable generated report `source_manifest`, `source_details`, `artifact_metadata`, and `cost_metrics` schema keys are constrained with parity tests and ADR `docs/adr/lane-d-0010-report-manifest-metadata.md`, without adding runtime validation, API behavior changes, DB migrations, connector behavior, live I/O, hook config, or POSIX scripts
- TD-090 is complete: the planning-pack OpenAPI reference now matches the live FastAPI-generated OpenAPI contract and the planning-pack API spec separates implemented endpoints from future roadmap endpoints.
- CON-021 is complete as a planning-only human-review action semantics pass. Future connector review actions are named before any API mutation route, worker, scheduler, dashboard, connector runtime change, schema, or migration.
- CON-022 is complete as a planning-only human-review API semantics pass. Future route/reviewer/auth/idempotency semantics are accepted before API mutation implementation or OpenAPI change.
- TA-080 is complete: the separate source provenance-family schema now covers serialized source dataset, dataset-version, and retrieval-run contracts without changing runtime validation, migrations, connector behavior, queue semantics, live I/O, or durable evidence-row linkage.
- CON-023 is complete: connector-local fixture quality now fails closed when evidence provenance text, caveats, or non-failure source dates are missing, without changing APIs, schemas, queues, source/evidence/claim/report behavior, or live I/O.
- TD-082 is complete as a planning-only report metadata extension boundary. Future report metadata extension families and promotion rules are accepted without changing report runtime behavior, APIs, schemas, queues, migrations, or live I/O.
- CON-024 is complete as a connector review action API auth blocker decision. The future review-action mutation route remains blocked until an authenticated reviewer/operator principal dependency or accepted service-account delegation rule is added and tested.
- CON-025 is complete as a local service-account reviewer principal dependency for future connector review mutation routes, without registering a route or changing OpenAPI.
- CON-026 is complete as a connector review action route-subset decision for `request_fixture_fix`, `requeue_after_fix`, and `cancel_review`; route/OpenAPI implementation remains deferred to avoid Session 1's Lane C evidence-linkage/OpenAPI branch.
- TD-083 is complete as a report validation metadata implementation: `artifact_metadata.validation` records report contract/profile and ruleset identity, with schema/regression coverage, without claiming verification-command execution or changing routes, OpenAPI, DB schema, connector runtime, queue behavior, live I/O, hook config, POSIX scripts, or Lane A/B/C modules.
- CON-027 is complete: connector-local fixture quality now fails closed when succeeded retrievals have nonzero errors or missing/mismatched row counts, and when blocked/failed retrievals lack explicit zero row count or positive error count, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- TD-084 is complete as a job-schema boundary decision: `schemas/job_schema.json` remains unedited and is not promoted to a live connector-run/API contract until a future schema/test slice chooses `jobs.job_queue`, `ConnectorReviewQueueItem`, or a new `JobContract` as authority; source retrieval runs remain connector provenance authority.
- CON-028 is complete: connector-local fixture quality now fails closed when source-failure payload values have empty/non-string `failure_reason` or `error_message`, or non-boolean `retryable`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-029 is complete: connector-local fixture quality now fails closed when source-failure payload `failure_reason` disagrees with retrieval `metrics.failure_reason`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-030 is complete: connector-local fixture quality now fails closed when blocked/failed retrievals lack non-empty `metrics.failure_reason`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-031 is complete: connector-local fixture quality now fails closed when succeeded retrievals carry non-empty `metrics.failure_reason`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-032 is complete: connector-local fixture quality now fails closed when flood fixture evidence has a domain other than `flood`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-033 is complete: connector-local fixture quality now fails closed when flood fixture retrievals have a connector name other than `fixture_flood_static`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-034 is complete: connector-local fixture quality now fails closed when one flood fixture retrieval emits evidence with mixed `source_id` values, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-035 is complete: connector-local fixture quality now fails closed when one flood fixture retrieval emits evidence with mixed `area_id` values, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-036 is complete: connector-local fixture quality now fails closed when `is_source_failure` disagrees with `evidence_type == "source_failure"`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-037 is complete: connector-local fixture quality now fails closed when non-empty flood fixture evidence `method_code` values do not start with `fixture_flood_`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-038 is complete: connector-local fixture quality now fails closed when source-failure fixture evidence carries geometry or spatial precision, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
Failed or blocked gates:
- No Level 5 blockers remain in the fixture-backed DB repository path verified on 2026-06-04.
- L5-001 through L5-010: PASS for the DB-backed evidence repository/service scope (source observations, source failures, spatial intersections, derived metrics, document extracts, human verification notes, geometry/SRID/spatial precision, invalid payload rejection, supersession, deterministic retrieval, rollback behavior, durable audit events, and the evidence-ledger persistence ADR are tested or documented)
- L6-001 through L6-010: PASS for Lane C claim/rule scope (claims require evidence links, unknowns require source-failure evidence, severity/confidence stay separate, verification tasks persist, rules are versioned/deterministic, caveats propagate, contradiction/stale/incomplete/source-failure/not-evaluated cases are tested, and rule logic lives in code/config rather than an LLM/UI prompt)
- L7-001 through L7-010: PASS for the fixture-backed report/API vertical slice (persisted report run, source/evidence/rule manifest data, API create/retrieve path, evidence-linked claims, unknown/source-failure surfacing, caveats/verification tasks, repeatable fixture behavior, API contract coverage, artifact metadata, and no live external APIs)
Completion evidence:
- state/VALIDATION_LOG.md
- backend/tests/source_registry/ (48 tests collected)
- backend/tests/area_geometry/ (49 tests)
- backend/app/domain/area_contracts.py (`AreaContract`, `AreaMetricsContract`, `AreaSpatialRelationContract`, `AreaVersionContract`)
- backend/app/area_geometry/models.py (`AreaModel`, `AreaVersionModel`)
- backend/app/area_geometry/area_repo.py (`SqlAlchemyAreaRepository`)
- backend/tests/evidence_ledger/ and backend/tests/claims_engine/ (153 tests)
- backend/app/domain/evidence_contracts.py (`EvidenceContract` with optional GeoJSON/SRID/spatial precision fields)
- backend/app/evidence_ledger/evidence_repo.py (`SqlAlchemyEvidenceRepository`)
- backend/app/evidence_ledger/audit_log.py (`SqlAlchemyEvidenceAuditLog`)
- docs/adr/lane-c-evidence.md
- backend/app/claims_engine/claim_repo.py (`SqlAlchemyClaimRepository`)
- backend/app/claims_engine/not_evaluated.py
- backend/tests/claims_engine/test_not_evaluated_claims.py
- backend/tests/evidence_ledger/test_evidence_schema_contract.py
- backend/tests/claims_engine/test_claim_schema_contract.py
- schemas/evidence_schema.json
- schemas/claim_schema.json
- docs/adr/lane-c-schemas.md
- docs/adr/lane-c-rules.md
- backend/app/reports/service.py
- backend/app/reports/models.py
- backend/app/reports/report_repo.py
- backend/app/reports/adapters.py
- docs/adr/lane-d-0001-report-persistence.md
- backend/tests/reports/test_report_repository.py (1 test)
- backend/tests/reports/test_adapters.py (4 tests)
- backend/tests/reports/ and backend/tests/api/ (20 tests)
- backend/tests/api/test_report_runs_db.py
- backend/tests/reports/test_report_regression.py
- schemas/report_run_schema.json
- backend/tests/reports/test_report_schema_contract.py
- docs/adr/lane-d-0010-report-manifest-metadata.md
- docs/adr/lane-d-0013-report-metadata-extension-boundary.md
- docs/adr/lane-d-0011-connector-human-review-actions.md
- docs/adr/lane-d-0014-connector-review-api-auth-blocker.md
- docs/adr/lane-d-0012-connector-human-review-api-semantics.md
- docs/adr/lane-d-0015-connector-reviewer-principal.md
- docs/adr/lane-d-0016-connector-review-action-route-subset.md
- docs/adr/lane-d-0017-report-validation-metadata.md
- docs/adr/lane-d-0018-job-schema-boundary.md
- docs/adr/lane-d-0019-connector-review-closeout-api.md
- backend/app/api/reviewer_auth.py
- backend/tests/api/test_reviewer_auth.py
- docs/planning_pack/api/openapi_stub.yaml
- backend/tests/test_planning_pack_schema_copies.py
- db/seeds/source_registry_seeds.py
- scripts/seed_sources.py
- docs/adr/lane-a-0001-provenance-model.md
- templates/data_source_license_review.md
- registers/data_source_registry.csv
- schemas/source_schema.json
- schemas/source_provenance_schema.json
- backend/tests/source_registry/test_source_schema_contract.py
- backend/tests/source_registry/test_source_provenance_schema_contract.py
- backend/tests/connectors/test_fixture_quality.py
- tests/fixtures/geometries/
- plans/2026-06-05-l10-production-hardening.md
- backend/Dockerfile
- .dockerignore
- docker-compose.yml
- backend/app/core/logging.py
- backend/app/core/metrics.py
- backend/app/api/metrics.py
- backend/app/api/rate_limit.py
- backend/app/source_registry/usage_rights.py
- backend/app/connectors/license_guard.py
- backend/app/connectors/nwi.py
- scripts/source_readiness.py
- scripts/live_connector_worker.py
- backend/tests/source_registry/test_source_readiness.py
- backend/tests/api/test_live_connector_worker.py
- docs/source-reviews/ds-002.md
- backend/app/reports/job_store.py (`SqlAlchemyAsyncReportJobStore`)
- backend/app/api/reports.py (`POST /report-runs/{report_run_id}/retry`)
- backend/tests/api/test_logging.py
- backend/tests/api/test_metrics.py
- backend/tests/api/test_rate_limit.py
- backend/tests/api/test_async_report_runs.py
- backend/tests/connectors/test_license_guard.py
- backend/tests/connectors/test_nwi_connector.py
- backend/tests/connectors/test_static_file_connector.py
- backend/tests/reports/test_job_store.py
- backend/app/api/operations.py
- backend/app/domain/job_health.py
- backend/tests/api/test_operations.py
- backend/tests/api/test_app_runtime_mode.py
- backend/tests/test_deployment_smoke_scripts.py
- scripts/run_deployment_smoke.ps1
- scripts/run_deployment_smoke.sh
- docs/runbooks/incident_response.md
- scripts/run_incident_rollback_check.ps1
- scripts/run_incident_rollback_check.sh
- backend/tests/test_incident_rollback_artifacts.py
- config/ops_alert_rules.yaml
- docs/runbooks/alerting.md
- scripts/run_alert_rules_check.ps1
- scripts/run_alert_rules_check.sh
- backend/tests/test_alerting_artifacts.py
- .github/workflows/ci.yml
- .github/dependabot.yml
- docs/runbooks/supply_chain.md
- scripts/run_supply_chain_check.ps1
- scripts/run_supply_chain_check.sh
- backend/tests/test_supply_chain_artifacts.py
- backend/requirements-prod.lock
- docs/sbom/backend-prod-sbom.json
- docs/runbooks/dependency_provenance.md
- scripts/run_provenance_check.ps1
- scripts/run_provenance_check.sh
- backend/tests/test_provenance_artifacts.py
- config/ops_cost_monitoring.yaml
- docs/runbooks/cost_monitoring.md
- scripts/run_cost_monitoring_check.ps1
- scripts/run_cost_monitoring_check.sh
- backend/tests/test_cost_monitoring_artifacts.py
- docs/planning_pack/api/openapi_stub.yaml
- backend/tests/api/test_report_runs_db.py
- scripts/run_backup_restore_check.ps1
- scripts/run_backup_restore_check.sh
- docs/runbooks/backup_restore.md
Next lowest-dependency task:
- Decide the DS-017 Commercial parcel vendor path: either select and review a vendor
  license/cost/field policy/entitlement boundary before implementation, or formally
  defer DS-017 from private-MVP release gating with an ADR/plan/update and matching
  release-readiness expectations.
- Publish or otherwise hand off the local stack: `main` is locally ahead of
  `origin/main`; remote handoff is not complete until the unpublished commits are
  pushed or intentionally held local.
- Next source-readiness expansion must start from a fresh source review for one of
  the remaining non-ready sources. Do not assume DS-012, DS-013, DS-014, DS-024, or
  DS-025 is unblocked without terms/source review plus connector proof.
- Remaining L10 hardening: hosted auth/RBAC, secret-manager integration, automatic
  key rotation, hosted log retention, billing reconciliation, image-publication
  attestation, hosted deployment proof, hosted alerting, and recovery/ops drills.
Do not work on yet:
- Live connectors other than DS-001 USGS TNM, DS-002 FEMA NFHL, DS-003 SSURGO, DS-004 NWI,
  DS-005 USGS water monitoring, DS-006 EPA ECHO, DS-007 BLM MLRS, DS-008 USGS MRDS,
  DS-010 county GIS parcels (Chatham/Buncombe/Brunswick), DS-011 assessor
  (not-evaluated), DS-015 NC Geological Survey, DS-016 OSM road access, DS-020 NOAA
  NWS climate/weather, DS-021 FCC Broadband Map, DS-022 Census TIGERweb geography,
  and DS-023 county zoning (Chatham/Brunswick UDO) unless source rights are reviewed
  and the work is explicitly bounded
- LLM summary generation (Level 10 scope)
- New jurisdictions or intents until the DS-002 connector slice or another registered/licensed live connector is implemented
- Paid APIs without explicit license review and plan approval
```


## Current objective

Harden the MVP workflow toward production operation while preserving the evidence-ledger-first spine:

```text
source registry -> area geometry -> evidence -> claim -> report run -> API response -> durable jobs/runtime packaging
```

## Active plan (overall)

`plans/2026-06-06-source-readiness-closure.md` is active for the current tail cleanup and
next source-readiness pass. The operator-complete surface plan remains completed history.

## 4-lane agent architecture (active)

This workspace uses 4 isolated agent lanes, each with dedicated scope, plans, and state files.
See `LANE_OWNERSHIP.md` for ownership boundaries.

| Lane | Scope | Active plan | State | Milestone gates |
|---|---|---|---|---|
| Lane A | Source Registry + DB Infrastructure | `plans/lane-a-2026-06-03-source-registry.md` | `state/lane-a-state.md` | L2-*, L3-* |
| Lane B | Area + Geometry Domain | `plans/lane-b-2026-06-03-area-geometry.md` | `state/lane-b-state.md` | L4-* |
| Lane C | Evidence Ledger + Claims Engine | `plans/lane-c-2026-06-03-evidence-claims.md` | `state/lane-c-state.md` | L5-*, L6-* |
| Lane D | Reports + API + Platform | `plans/lane-d-2026-06-03-reports-api-infra.md` | `state/lane-d-state.md` | L7-* |

**Each lane agent must read `LANE_OWNERSHIP.md` before any code change.**

## Key constraints

- Bottom-up implementation only.
- Postgres/PostGIS is system of record.
- Evidence-before-claim invariant is non-negotiable.
- No live data connectors before license/source registry/fixture tests.
- No UI or LLM work until the storage/evidence/claim/report spine works.
- Lane agents MUST NOT modify files owned by other lanes.

## Known blockers / undecided items

| Item | Status | Impact |
|---|---|---|
| MVP state/counties | Undecided | Do not hard-code jurisdiction-specific logic |
| Parcel vendor | Undecided | Use fixtures/public source registry only |
| Live connector credentials | Not required for DS-002 public FEMA NFHL; unavailable for commercial vendors | DS-002 may proceed to a bounded public live connector slice; vendor connectors remain blocked |
| Docker availability | Available | DB smoke now passes locally |
| Connector integration zone | Canonical in `LANE_OWNERSHIP.md` | CON-001 through CON-020 complete; next Level 8 connector pass needs selection |

## Last verified state

Dossier confidence band fix on 2026-06-11: `_confidence_band()` in `dossier.py` was
always returning `'low'` because structural NOT_EVALUATED UNKNOWN claims (5 domains:
soil_septic, parcels, resource_context, market_context, assessor; plus the
ZONING_NOT_SCREENED sentinel injected by `_with_zoning_sentinel_if_missing()` in
`service.py`) are always present in every report run regardless of whether any real
connector ran. Fixed by evidence-ID correlation: `_STRUCTURAL_DOMAINS` and
`_STRUCTURAL_EVIDENCE_CODES = frozenset({'ZONING_NOT_SCREENED'})` identify structural
evidence; UNKNOWN claims backed exclusively by structural evidence no longer reduce
confidence. Band now returns `'unknown'` (no non-structural evidence), `'medium'`
(non-structural evidence, no UNKNOWN claims), or `'low'` (non-structural evidence with
at least one UNKNOWN claim). Three new tests cover all three bands. 1310 tests
collected; committed `98afd51`.

Dossier Section 8 (Soil/Septic) SSURGO surfacing fix on 2026-06-11: Section 8 was
hardcoding "Soil map units: not evaluated" even when SSURGO evidence (domain
`soil_septic`, evidence code `SSURGO_SOIL_MAPUNIT_INTERSECTION`) was present. Added
`_soil_septic_result()` helper that reads `soil_mapunit_name`/`soil_mapunit_symbol`/
`soil_mapunit_key` observed_value keys and renders a deduplicated mapunit list; also
fixed `_domain_verification` and `_domain_caveats` calls from wrong domain string
`'soil'` to `'soil_septic'`. Added caveats line to Section 8. Two new tests
(`test_dossier_renders_ssurgo_mapunit_from_evidence`,
`test_dossier_renders_soil_source_failure_from_evidence`). 1228 tests pass, mypy
clean on 120 source files. Committed `9b40dd4`. DS-013 NC well logs blocked review
also committed (`ceff1b4`).

Latest DS-016/DS-005/DS-006 connector verification on 2026-06-11: three Should-priority
live connectors are implemented and all 1222 tests pass with mypy clean over 120 source
files. DS-016 OSM road access (`OsmRoadAccessConnector` via Overpass API) and DS-005 USGS
water monitoring (`UsgsWaterMonitoringConnector` via USGS NWIS REST) were committed as
`af940bf` and `77a8ece`. DS-006 EPA ECHO (`EpaEchoConnector` via EPA FRS REST, 3 req/min
rate limit, bbox-to-centroid+radius spatial query) promotes `env_hazard` from
NOT_EVALUATED_DOMAINS to a real evaluation domain: ENV_G001 now gates on
`env_hazard_facility_proximity` (severity=high), and two claims paths are generated
(proximity found → ENV_001; no proximity or failure → UNKNOWN/review claims). Payload
validation, connector inventory, live-connector orchestration, API route, openapi_stub,
source-readiness tests, and rule-engine tests are all updated. Source readiness: 7/8
Must (DS-017 remains blocked by vendor/license), 3 Should (DS-005, DS-006, DS-016)
connector-ready; 10/25 total connector-ready. Next-task candidates: DS-012 county
recorder source-rights review + connector (Should, county deeds/easements, NC counties),
DS-013 state well logs source-rights review + connector (Should, NC Division of Water
Resources), dossier/report surfacing of water/env_hazard/road-access claims, or
consolidating the job_repo.py idempotency path. DS-017 (Must, commercial parcel) and
DS-018 (Should, commercial comps) remain blocked by license/cost.

Latest batch-round-2 verification on 2026-06-10 (merged to `main`, PRs #23–#33): the
operator surface is merged and live on main, plus ten parallel units: source-rights
reviews for DS-005/006/010/011/016 (DS-010 county parcels — a previously blocked Must
source — is now approved-with-restrictions for Buncombe/Chatham/Brunswick NC), an
audit-event retention purge tool (closing the not_yet_automated retention blocker),
per-claim evidence identifiers in the dossier, a concurrent-user load-test scenario,
an executed live-connector smoke for a bounded Buncombe bbox (USGS TNM/NWI/SSURGO
succeeded with real evidence; FEMA NFHL recorded a first-class source failure; a real
SSURGO null-field bug was found and fixed), shared UI styling consolidation, and
Idempotency-Key support on POST /report-runs and /intake. Full DB-enabled
`.\scripts\verify.ps1` is green on merged main; every PR passed GitHub CI before
merge; attribution scan clean. Known CI caveat: `dependency-attestations` fails at the
attestation publish step on pull_request events (entitlement/OIDC boundary) while the
push-event run passes. Next-task candidates: Buncombe/Brunswick parcel connectors
(DS-010 restrictions permitting), DS-005/006 connectors for water/enviro context,
consolidating the unwired reports.report_runs idempotency mechanism (job_repo.py)
with the wired job-store path, and the hosted-production lane when infrastructure
exists.

Previous operator-surface verification on 2026-06-10 (branch
`worktree-prod-advance-20260610`): the operator web UI is now workflow-complete and
auth-consistent with the API. UI report approval requires reviewer credentials with
`report:approve` scope and records the authenticated reviewer in `reviewed_by` and
`review_actions` (the prior credential-free first-account approval path is removed —
this was a falsified-attribution audit defect). New approved-only export endpoints
serve the Markdown dossier as a download and the machine-readable JSON report artifact
(persisted artifact in DB mode) with a forbidden-phrase regression on the artifact body.
New UI surfaces: connector review queue list/detail with approve/reject/requeue/cancel
and resume-report actions (reviewer-scope model), pending-connector-review intake
surfacing, failed-report retry, operations queue-health dashboard, report list status
filter + pagination (plus a bounded `GET /report-runs` list endpoint and job-store
offset/status support in both implementations), evidence lineage page, and report
comparison page sharing the API's summary/parsing helpers.
`scripts/export_openapi_stub.py` now regenerates the planning-pack OpenAPI stub; the
parity test is environment-sensitive and must run under `py -3.12`. Full DB-enabled
`.\scripts\verify.ps1` passes with `RUN_DB_SMOKE=1` (suite grew from 871 to 975+ passed
tests); a three-lens adversarial review with per-finding re-verification confirmed 9
findings, all fixed. The UI targets the default trusted-network posture;
`REQUIRE_API_KEY=true` locks all `/ui` routes fail-closed (runbook documents this).
Next-task recommendation: live-connector exercise of the operator workflow end-to-end
against the three NC counties, source-rights review progress on the four blocked Must
sources (DS-010/011/017/023), or hosted-production lane items if infrastructure becomes
available.

Latest US-052 verification on 2026-06-05: reviewer-authenticated
`GET /operations/queue-health` is implemented for in-memory and DB-backed report/live
connector job stores. Full DB-enabled `.\scripts\verify.ps1` passes with
`RUN_DB_SMOKE=1`; 631 tests are collected; source-readiness remains
`sources=8 ready=4 blocked=4`; `git diff --check` reports only CRLF normalization
warnings on generated/state files; no repo Docker services or worker-run containers
remain running. Queue health is read-only and does not lease jobs, retry jobs, call live
sources, persist evidence, or create reports.

Latest US-053 verification on 2026-06-05: DB-backed deployment smoke automation is
implemented through `scripts/run_deployment_smoke.ps1` and
`scripts/run_deployment_smoke.sh`. `USE_DB_SERVICES` lets deployed `app.main:app` use
Postgres-backed services, and Compose opts into that mode with
`COMPOSE_USE_DB_SERVICES=true`. Final Windows deployment smoke passed after adding DB
readiness waiting and guarding repeated `rule_execution_report_fk` migration
application. Full DB-enabled `.\scripts\verify.ps1` passes with `RUN_DB_SMOKE=1`; 636
tests are collected; source-readiness remains `sources=8 ready=4 blocked=4`; the diff
whitespace check reports only CRLF normalization warnings on generated/state files; no
repo, smoke, or worker-run containers remain running. Deployment smoke validates local
Compose build/start, migrations/seeds, `/health`, `/version`, `/metrics`,
`/operations/queue-health`, and an area-to-report HTTP workflow.

Latest US-054 verification on 2026-06-05: incident response and rollback proof is
implemented through `docs/runbooks/incident_response.md`,
`scripts/run_incident_rollback_check.ps1`, and `scripts/run_incident_rollback_check.sh`.
The runbook names severity levels, owner roles, escalation criteria, deployment rollback,
database rollback/mitigation, connector outage handling, queue/report failure handling,
recovery criteria, and closure records. The Windows incident/rollback check passed, full
DB-enabled `.\scripts\verify.ps1` passes with `RUN_DB_SMOKE=1`; 638 tests are collected;
source-readiness remains `sources=8 ready=4 blocked=4`; the diff whitespace check reports
only CRLF normalization warnings on generated/state files; no repo, smoke, or worker-run
containers remain running. Production on-call identities, alert routing, hosted rollback
pipeline, and automated down migrations remain outside this proof.

Latest US-055 verification on 2026-06-05: repo-local alert rules are implemented through
`config/ops_alert_rules.yaml`, `docs/runbooks/alerting.md`,
`scripts/run_alert_rules_check.ps1`, and `scripts/run_alert_rules_check.sh`. The catalog
maps SEV0 safety-contract failure, SEV1 health/deployment/DB/restore failures, SEV2
metrics/queue/live-connector failures, source-readiness ready-count drops, and stale
source-registry `Last Checked At` metadata to owners, escalation, runbooks, and validation
proofs. The Windows alert-rules check passed, full DB-enabled `.\scripts\verify.ps1`
passes with `RUN_DB_SMOKE=1`; 642 tests are collected; source-readiness remains
`sources=8 ready=4 blocked=4`; the diff whitespace check reports only CRLF normalization
warnings on generated/state files; no repo, smoke, or worker-run containers remain
running. Hosted alert routing, dashboards, pager delivery, a named on-call rotation, and
independent real-time upstream dataset freshness verification remain outside this proof.

Latest US-056 verification on 2026-06-05: CI supply-chain dependency vulnerability
scanning and update hygiene are implemented through `.github/workflows/ci.yml`,
`.github/dependabot.yml`, `docs/runbooks/supply_chain.md`,
`scripts/run_supply_chain_check.ps1`, and `scripts/run_supply_chain_check.sh`. The CI
workflow now has a `supply-chain` job that installs the backend dependency environment
and runs `pip-audit --local`; Dependabot requests weekly checks for GitHub Actions and
backend Python dependency metadata. The Windows supply-chain check passed, full
DB-enabled `.\scripts\verify.ps1` passes with `RUN_DB_SMOKE=1`; canonical mypy is clean
over 175 source files. At the US-056 point, a production dependency lockfile, signed
SBOM, SLSA provenance attestation, Docker base-image package scan, and GitHub Actions
runtime attestation remained outside that proof; US-058 later added the repo-local
production lock/SBOM proof, and US-059 later added the repo-local container image scan
proof.

Latest US-058 verification on 2026-06-05: backend production dependency provenance is
implemented through `backend/requirements-prod.lock`, `docs/sbom/backend-prod-sbom.json`,
`docs/runbooks/dependency_provenance.md`, `scripts/run_provenance_check.ps1`,
`scripts/run_provenance_check.sh`, and `backend/tests/test_provenance_artifacts.py`.
The lock pins the CPython 3.12 manylinux backend runtime dependency closure with
SHA-256 hashes, the repo-local CycloneDX SBOM mirrors that component set, and the CI
`supply-chain` job now runs the provenance proof before `pip-audit --local`. The Windows
provenance proof, updated supply-chain proof, focused tests, ruff, mypy, PowerShell
parser validation, and full DB-enabled `.\scripts\verify.ps1` passed; 653 tests are
collected and canonical mypy is clean over 177 source files. Signed/published SBOM,
SLSA provenance attestation, Docker base-image scanning, and GitHub Actions runtime
attestation remained outside the US-058 proof; US-059 later added the repo-local
container image scan proof.

Latest US-059 verification on 2026-06-05: backend container image/base-image
vulnerability scanning is implemented through the CI `container-image-scan` job,
`docs/runbooks/container_image_scan.md`, `scripts/run_container_scan_check.ps1`,
`scripts/run_container_scan_check.sh`, and
`backend/tests/test_container_scan_artifacts.py`. The CI job builds
`backend/Dockerfile` into `land-diligence-backend:${{ github.sha }}` and runs
`docker/scout-action@v1` with `command: cves`, `local://` image resolution,
`only-severities: critical,high`, and `exit-code: true`. The Windows container scan
proof, updated supply-chain proof, focused tests, ruff, mypy, PowerShell parser
validation, and full DB-enabled `.\scripts\verify.ps1` passed; 657 tests are collected
and canonical mypy is clean over 178 source files. Digest-pinned base images remained
outside the US-059 proof; US-060 later added the repo-local digest-pinned backend
base-image proof. Published-registry image attestation, signed image SBOM, SLSA
provenance attestation, hosted deployment runtime scanning, GitHub Actions runtime
attestation, and source/vendor rights remain outside this proof.

Latest US-060 verification on 2026-06-05: the backend Docker runtime base image is pinned
by OCI index digest in `backend/Dockerfile`:
`python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203`.
The digest was verified from live `docker buildx imagetools inspect python:3.12-slim`
output before editing. The Windows container scan proof, focused tests, ruff, mypy, an
actual pinned `docker build`, and full DB-enabled `.\scripts\verify.ps1` passed;
canonical mypy remains clean over 178 source files. Published-registry image
attestation, signed image SBOM, SLSA provenance attestation, hosted deployment runtime
scanning, GitHub Actions runtime attestation, and source/vendor rights remain outside
this proof.

Latest US-061 verification on 2026-06-05: GitHub dependency lock/SBOM artifact
attestations are wired through the CI `dependency-attestations` job. The job validates
dependency provenance first, then uses `actions/attest@v4` with `id-token: write`,
`attestations: write`, and `artifact-metadata: write` to create a provenance
attestation for `backend/requirements-prod.lock` and `docs/sbom/backend-prod-sbom.json`,
plus an SBOM attestation binding `docs/sbom/backend-prod-sbom.json` to the production
lock subject. The Windows provenance proof, supply-chain proof, focused tests, ruff,
mypy, PowerShell parser validation, and full DB-enabled `.\scripts\verify.ps1` passed;
canonical mypy remains clean over 178 source files. Release package, hosted deployment,
published registry-image attestation, GitHub Actions runtime attestation, and
source/vendor rights remain outside this proof.

Latest US-062 verification on 2026-06-05: report `artifact_metadata.cost_metrics` now
requires and emits explicit zero-dollar attribution fields for current local-only paths:
`estimated_total_usd_cents`, `compute_usd_cents`, `storage_usd_cents`,
`llm_usd_cents`, `map_tile_usd_cents`, `geocoding_usd_cents`,
`paid_data_usd_cents`, `human_review_usd_cents`, and `human_review_minutes`.
The report repository fills missing attribution defaults for older/custom metadata on
persistence while preserving extension fields. The Windows cost-monitoring proof,
focused report schema/service/repository/regression/API tests, ruff, mypy, PowerShell
parser validation, and full DB-enabled `.\scripts\verify.ps1` passed; 659 tests are
collected, canonical mypy remains clean over 178 source files, source readiness remains
`sources=8 ready=4 blocked=4`, and no Docker services or worker-run containers remain
running. Hosted billing reconciliation, approved nonzero unit-cost thresholds, paid
vendor metering, LLM metering, map/geocoding metering, and durable reviewer-time capture
remain outside this proof.

Latest US-063 verification on 2026-06-05: `config/release_readiness.yaml` now gathers
the repo-local release gates for workspace verification, DB verification, deployment
smoke, dependency provenance, supply-chain scanning, dependency attestations, container
image scanning, backup/restore, incident/rollback, alerting, cost monitoring, and
source readiness. `scripts/run_release_readiness_check.ps1` and `.sh` validate the
catalog, CI `release-readiness` job, current Must-source readiness counts, and explicit
release blockers. The Windows release-readiness proof, focused artifact tests, ruff,
mypy, PowerShell parser validation, and full DB-enabled `.\scripts\verify.ps1` passed;
664 tests are collected, canonical mypy is clean over 179 source files, source readiness
remains `sources=8 ready=4 blocked=4`, and no Docker services or worker-run containers
remain running. Release package creation, pushed registry image, hosted deployment,
published registry-image attestations, hosted billing reconciliation, blocked source
approval, full user auth/RBAC, and hosted alerting remain outside this proof.

Latest US-064 verification on 2026-06-05: `config/access_control.yaml` now records
current default-off API-key middleware, local reviewer service-account auth,
reviewer-authenticated operator routes, intentionally public health/version routes, and
production auth/RBAC blockers. `scripts/run_access_control_check.ps1` and `.sh`
validate the catalog, referenced auth authority files, failure-mode test coverage,
protected-route reviewer dependencies, `access-control` CI job, and runbook limits. The
Windows access-control proof, release-readiness proof, focused artifact/auth tests, ruff,
mypy, PowerShell parser validation, and full DB-enabled `.\scripts\verify.ps1` passed;
668 tests are collected, canonical mypy is clean over 180 source files, source readiness
remains `sources=8 ready=4 blocked=4`, and no Docker services or worker-run containers
remain running. Full user auth/RBAC, OAuth/OIDC, user accounts, key rotation, hosted
identity-provider integration, and role-scoped authorization remain outside this proof.

Latest US-065 verification on 2026-06-05: protected operator routes now enforce scoped
local reviewer service-account authorization. `REVIEWER_ACCOUNT_SCOPES` is required for
custom reviewer accounts; connector invocation/scheduling requires `connector:run`,
connector review decisions require `connector:review`, queue/live-job health reads
require `operations:read`, failed-report retry requires `report:retry`, and manual
approved-connector report creation requires `report:run`. The Windows access-control
proof, release-readiness proof, focused scoped-auth tests, ruff, mypy, PowerShell parser
validation, Compose config, and full DB-enabled `.\scripts\verify.ps1` passed; 680 tests
are collected, canonical mypy is clean over 180 source files, source readiness remains
`sources=8 ready=4 blocked=4`, auth-overclaim search has no matches, and no Docker
services or worker-run containers remain running. This is a scoped local service-account
authorization substrate, not full user auth/RBAC, OAuth/OIDC, user accounts, key
rotation, or hosted identity-provider authorization.

Latest US-066 verification on 2026-06-05: local release package creation is now
implemented through `config/release_package.yaml`, `scripts/build_release_package.ps1`,
`scripts/build_release_package.sh`, and validate-only package proofs. A clean package
build produced `local_artifacts/releases/land-diligence-us066-20260606T013648Z.zip`
and `local_artifacts/releases/land-diligence-us066-20260606T013648Z-release-manifest.json`
with 220 files, an embedded manifest, no `.git`, no `local_artifacts`, and no secret-like
`.env` files beyond allowed `.env.example`. Full DB-enabled `.\scripts\verify.ps1`
passed after the package slice; 684 tests are collected, canonical mypy is clean over
181 source files, source readiness remains `sources=8 ready=4 blocked=4`, and no Docker
services or worker-run containers remain running. Pushed registry images, hosted
deployment, registry-image attestations, signed image SBOM, SLSA provenance, hosted
billing reconciliation, and blocked-source approval remain outside this proof.

Latest US-067 verification on 2026-06-05: registry image publication readiness is now
cataloged through `config/image_publication.yaml`, `docs/runbooks/image_publication.md`,
`scripts/run_image_publication_check.ps1`, `scripts/run_image_publication_check.sh`, and
`backend/tests/test_image_publication_artifacts.py`. The proof is wired into
`config/release_readiness.yaml`, the read-only `image-publication` CI job, release
readiness proofs, `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, and this plan/state
set. Full DB-enabled `.\scripts\verify.ps1` passed after the image publication slice;
689 tests are collected, canonical mypy is clean over 182 source files, source readiness
remains `sources=8 ready=4 blocked=4`, `git diff --check` reports only CRLF warnings on
generated/state files, and no Docker services or worker-run containers remain running.
This is a validate-only publication-readiness boundary; it does not push a registry
image, create hosted deployment, sign an image SBOM, publish SLSA provenance, or attach
registry-image attestations.

Latest US-068 verification on 2026-06-05: hosted deployment readiness is now
cataloged through `config/hosted_deployment.yaml`,
`docs/runbooks/hosted_deployment.md`, `scripts/run_hosted_deployment_check.ps1`,
`scripts/run_hosted_deployment_check.sh`, and
`backend/tests/test_hosted_deployment_artifacts.py`. The proof is wired into
`config/release_readiness.yaml`, the read-only `hosted-deployment` CI job,
release readiness proofs, `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, and this
plan/state set. Full DB-enabled `.\scripts\verify.ps1` passed after the hosted
deployment readiness slice; 694 tests are collected, canonical mypy is clean over
183 source files, source readiness remains `sources=8 ready=4 blocked=4`, and no
Docker services or worker-run containers remain running. This is a validate-only
hosted deployment readiness boundary; it does not provision infrastructure,
publish a registry image, deploy the service, configure DNS/TLS, attach hosted
identity, or enable hosted alerting.

Latest US-069 verification on 2026-06-05: API-key and local reviewer
service-account secrets now accept raw local values or normalized
`sha256:<64-hex>` configured secret specs through the shared
`backend/app/api/secret_specs.py` helper. `API_KEYS` and `REVIEWER_ACCOUNTS`
parsing now fail closed for blank or malformed hash specs, compare configured
hashes using SHA-256 plus constant-time comparison, keep raw fixture secrets
available for local use, and update access-control catalogs/runbooks/proofs to
document the boundary. The Windows access-control proof, release-readiness proof,
focused auth tests, ruff, mypy, and full DB-enabled `.\scripts\verify.ps1` passed
after the hashed secret specs slice; 704 tests are collected, canonical mypy is
clean over 184 source files, migrations/seeds apply, and DB smoke passes. This is
not key rotation, user accounts, OAuth/OIDC, hosted identity, or full RBAC.

Latest US-070 verification on 2026-06-05: `API_KEY_SPECS` now provides a configured
static API-key lifecycle substrate with comma-separated `id|status|secret` entries.
Only `active` specs authenticate; `retired` specs do not; secrets may be raw or
`sha256:<64-hex>`; malformed status, duplicate IDs, duplicate secrets, and malformed
hashes fail closed during settings parsing. The access-control catalog now records
`api_key_rotation` as an implemented configured static lifecycle control and keeps
`automatic_api_key_rotation` blocked. `.env.example`, Compose, hosted deployment
readiness, access-control proofs, hosted-deployment proofs, and operator runbooks expose
the runtime knob without adding hosted secret writes. Focused API-key lifecycle tests,
access-control and hosted-deployment artifact tests, access-control proof,
hosted-deployment proof, focused ruff, and focused mypy passed before full verification.
This is not automatic rotation, external secret-manager integration, per-key usage
audit, user accounts, OAuth/OIDC, hosted identity, or full RBAC.

Latest US-071 verification on 2026-06-05: protected-path API-key auth now emits
structured runtime audit log events for accepted, missing, invalid, and unconfigured
decisions. Events include `event_type=api_key_auth`, outcome, status code, method, path,
auth source, and configured `api_key_id` for accepted `API_KEY_SPECS` credentials; they
do not include the provided key, configured secret, or query string. The access-control
catalog now records `api_key_audit_logging` as implemented structured runtime logs.
Focused API-key auth/access-control tests, access-control proof, focused ruff, focused
mypy, release-readiness proof, and full DB-enabled `.\scripts\verify.ps1` passed after
this slice; 718 tests are collected, canonical mypy is clean over 184 source files,
migrations/seeds apply, and DB smoke passes. This is not a durable database audit
ledger, hosted log-retention system, automatic rotation, external secret-manager
integration, user accounts, OAuth/OIDC, hosted identity, or full RBAC.

Latest US-072 verification on 2026-06-05: protected-path API-key auth now records
accepted, missing, invalid, and unconfigured decisions through an optional API-key auth
audit sink. In DB-service mode, the SQLAlchemy sink writes those decisions to existing
`audit.events` rows with `event_type=api_key_auth` and `target_table='api.api_key_auth'`.
The middleware fails closed with 503 if configured audit persistence fails, and the
runtime log plus DB-event payloads still exclude provided keys, configured secrets, and
query strings. Focused API-key auth/access-control tests, access-control proof, focused
ruff, and focused mypy passed before full verification. This is not hosted log retention,
SIEM export, automatic rotation, external secret-manager integration, user accounts,
OAuth/OIDC, hosted identity, or full RBAC.

Latest US-073 through US-082 verification on 2026-06-05: load test baseline (scripts/run_load_test.ps1/.sh, docs/runbooks/load_testing.md), security static analysis CI gate (scripts/run_security_scan.ps1/.sh, bandit 0 HIGH/CRITICAL, security-scan CI job), data retention policy catalog (config/data_retention.yaml with 7 classes, docs/runbooks/data_retention.md), jurisdiction and rulepack readiness checklists (docs/checklists/jurisdiction_readiness.md, docs/checklists/rulepack_readiness.md), DB connection pool explicit configuration (DB_POOL_SIZE/MAX_OVERFLOW/TIMEOUT/RECYCLE in config.py, conditional pool kwargs in engine.py), performance runbook (docs/runbooks/performance.md covering cache, batch controls, spatial indexes, backpressure), report lineage endpoint (GET /report-runs/{id}/lineage), candidate comparison endpoint (GET /report-runs/compare), and report rerun diff endpoint (GET /report-runs/{id}/diff) are implemented. Full `py -3.12 -m pytest` passes with 794 passed and 63 skipped (DB-layer); ruff clean; mypy clean over 216 source files. `config/release_readiness.yaml` now has 22 required_checks entries. The MANIFEST.md references docs/checklists/. Remaining L10 blockers: full user auth/RBAC, hosted deployment, hosted billing, hosted log retention, automatic key rotation, non-ready Must sources.

Level 10 partial hardening verified 2026-06-05 on local `main`: settings-backed scoped reviewer auth, production API-key middleware with raw-or-sha256 configured secrets, configured static API-key lifecycle specs, and structured API-key auth audit logs plus DB-backed API-key auth events, default-off fixed-window rate limiting, backend Docker/Compose service, JSON runtime logging, structured runtime metrics, container build/runtime smoke, fail-closed connector source-use preflight, source-readiness audit reporting, reviewed source-rights candidates (DS-001 USGS The National Map, DS-002 FEMA NFHL, DS-003 USDA Web Soil Survey/SSURGO, and DS-004 National Wetlands Inventory), bounded DS-001 USGS TNM EPQS connector-layer terrain-relief screening plus controlled DS-001 API/operator invocation, explicit durable DS-001 live connector scheduling, and request-time DS-001 orchestration, bounded DS-002 FEMA NFHL live connector, bounded DS-003 USDA SSURGO connector plus controlled DS-003 API/operator invocation, explicit durable DS-003 live connector scheduling, and request-time DS-003 report integration with an UNKNOWN SSURGO screening-review claim, bounded DS-004 National Wetlands Inventory connector, controlled DS-002 API/operator invocation, controlled DS-004 API/operator invocation, explicit durable DS-002 and DS-004 live connector scheduling, read-only live connector job status API, bounded supervised live connector worker command, opt-in Compose live connector worker profile, connector review closeout actions, durable connector reviewer action history, approved connector evidence report gating, DB-backed connector approval-to-report regressions, request-time DS-001, DS-002, DS-004, and DS-003 orchestration for intake/report-run flows, file-backed DS-004 raw response fixture corpus, API 422 deprecation cleanup, live connector sequence scheduling, failed report job retry with lineage, backup/restore proof, repo-local alert-rule catalog with validate-only proof, CI supply-chain dependency vulnerability scanning and update hygiene, backend production dependency lock/SBOM provenance proof, backend dependency lock/SBOM artifact attestation proof, backend container image/base-image scan proof, digest-pinned backend Docker base-image proof, repo-local cost monitoring catalog with validate-only guardrails and report zero-dollar cost attribution, repo-local release readiness catalog with validate-only proof, local release package ZIP/manifest builder with validate-only proof, repo-local image publication readiness catalog with validate-only proof, repo-local hosted deployment readiness catalog with validate-only proof, repo-local access-control posture catalog with validate-only proof, scoped local reviewer authorization with raw-or-sha256 configured service-account tokens for protected operator routes, explicit post-approval connector report resume, SQLAlchemy source placeholder URL hardening, and Postgres-backed async report job state are implemented. Full DB-enabled `.\scripts\verify.ps1` passes with `RUN_DB_SMOKE=1` after the DB-backed API-key auth audit-event slice; 722 tests are collected; ruff is clean and canonical mypy is clean over 185 source files; migrations/seeds apply; DB smoke passes. Backend image build passes with the pinned base image; Compose runtime smoke serves `/health`, `/version`, and `/metrics`. Source-readiness audit reports current `Must` sources as `sources=8 ready=4 blocked=4`; DS-001 is approved-with-restrictions plus implemented as a bounded connector-layer EPQS terrain-relief screening slice with controlled API/operator invocation, durable scheduling, and request-time orchestration, DS-002 is approved-with-restrictions for bounded FEMA NFHL screening use, DS-003 is approved-with-restrictions plus implemented as a bounded connector-layer SSURGO mapunit/component screening slice with immediate, durable queued-worker, and request-time report paths, DS-004 is approved-with-restrictions for wetland/deepwater screening source-rights use only, and the SQL seed refreshes first-class DS-001/DS-002/DS-003/DS-004 usage-rights fields on re-seed. The DS-001 connector samples the official USGS TNM EPQS JSON service at the bbox center and corners with EPSG:4326 coordinates, emits one low-confidence terrain-relief `DERIVED_METRIC` for screening, emits source-failure evidence for no-data/error/malformed cases, and reuses existing retrieval provenance plus evidence-ingestion adapters. The reviewer-authenticated DS-001 route at `POST /connector-runs/usgs-tnm/query-bbox` invokes the bounded connector, records retrieval provenance, persists terrain-relief derived metric or source-failure evidence, and enqueues connector review status. `POST /connector-runs/usgs-tnm/schedule-bbox` enqueues durable DS-001 `live_connector_run` jobs without fetching EPQS or creating reports; the shared worker leases by `source_registry_id`, executes the existing DS-001 orchestration, and records the resulting connector review item. When `ENABLE_LIVE_CONNECTORS=true`, `/intake` and `/report-runs` run bounded DS-001 first, returning `pending_connector_review` until DS-001 approval before advancing to DS-002, DS-004, and DS-003; approved DS-001 evidence may enter reports as buildability-domain terrain screening evidence, but DS-001 still does not add DEM downloads, survey-grade elevation, engineering, site-plan, legal, buildability, lending, appraisal, investment conclusions, or a DS-001-specific claim. The DS-002 connector is implemented with reviewer-authenticated immediate, request-time, and queued-worker paths that record retrieval provenance, persist evidence, enqueue review status, support authenticated review closeout with queue-payload action history, and gate report use of connector-lineage evidence on succeeded `approve_for_connector_qa` queue state. The DS-003 connector/API/scheduler/request-time slice uses official USDA NRCS Soil Data Access `post.rest` with `JSON+COLUMNNAME` output and the documented WGS84 WKT mapunit-intersection function, exposes reviewer-authenticated immediate operator invocation at `POST /connector-runs/ssurgo/query-bbox`, records retrieval provenance, persists ledger-safe soil/septic/ag screening evidence or source-failure evidence, supports explicit durable scheduling at `POST /connector-runs/ssurgo/schedule-bbox`, and participates in request-time `/intake` and `/report-runs` after DS-004 approval. Approved DS-003 evidence can produce only an UNKNOWN `SOIL_NOT_EVALUATED` professional-review claim; it still has no pAOI state, WSS interpretation/rating execution, or final septic/soil-suitability/buildability conclusions. The DS-004 connector is implemented with reviewer-authenticated immediate, queued-worker, and request-time paths: `POST /connector-runs/nwi/query-bbox` runs the official USFWS-linked Wetlands ArcGIS REST layer 0 with EPSG:4326 bbox/feature limits immediately, and `POST /connector-runs/nwi/schedule-bbox` enqueues durable `live_connector_run` jobs without fetching NWI or creating reports. `GET /connector-runs/live-jobs/{job_id}` returns durable live connector job state without mutating, leasing, retrying, fetching, or scheduling reports. The shared worker dispatches by `source_registry_id`, executes existing DS-001, DS-002, DS-003, or DS-004 orchestration, records provenance, persists evidence, enqueues review status, and can feed the existing approved connector report-resume path without re-fetching live sources where report integration exists. DS-004 still has no source-specific autonomous scheduling policy. File-backed raw NWI fixtures now cover representative DS-004 success and empty-response source-failure behavior. API route validation/error paths now use the current FastAPI/Starlette 422 status constant name without changing the wire-level 422 status code. `POST /connector-runs/live-sequence/schedule-bbox` now enqueues the reviewed DS-001, DS-002, DS-004, and DS-003 durable live connector jobs for a registered area without fetching live sources, persisting evidence, approving review, or creating reports; its request body uses a source-neutral bbox schema rather than a FEMA-specific public model. `POST /report-runs/{report_run_id}/retry` now lets authenticated reviewers with `report:retry` create a new queued report job from a failed report job while preserving the failed job and recording `retry_of_report_run_id` lineage in in-memory and DB-backed job stores. `scripts/run_backup_restore_check.ps1` and `scripts/run_backup_restore_check.sh` now provide a Level 10 backup/restore proof that dumps the configured source DB, restores into a dedicated `land_diligence_restore_check*` database, runs `scripts/db_smoke_check.py` against the restored database, and drops the restore DB by default. The supply-chain CI job validates the backend production dependency lock/SBOM, installs the backend dependency environment, and runs `pip-audit --local`; the dependency-attestations CI job publishes GitHub artifact attestations for the production lock/SBOM files and an SBOM attestation binding the CycloneDX SBOM to the lock subject; the container-image scan CI job builds the backend image locally from a digest-pinned base image and scans it with Docker Scout for critical/high CVEs; the access-control CI job validates the repo-local access posture catalog; the hosted-deployment CI job validates the repo-local hosted deployment readiness boundary without provisioning infrastructure; the image-publication CI job validates the repo-local registry publication boundary without registry login, push, signing, or deployment; the release-readiness CI job validates the repo-local release gate catalog; Dependabot checks GitHub Actions and backend Python dependency metadata weekly. The repo-local cost monitoring catalog covers compute, storage, LLM-if-used, maps, geocoding, and data vendors, and the validate-only proof checks report `cost_metrics` counts plus zero-dollar attribution fields, planning cost inputs, alert integration, and DS-017 blocked vendor status. The repo-local release readiness catalog gathers verification, DB, deployment smoke, dependency provenance, supply-chain, dependency attestation, container scan, backup/restore, incident, alerting, cost, access-control, release-package, image-publication, hosted-deployment, and source-readiness gates while preserving release blockers for registry image publishing, hosted deployment, billing reconciliation, non-ready sources, full user auth/RBAC, and hosted alerting. The repo-local access-control catalog records current API-key middleware with raw-or-sha256 configured secrets, configured static API-key lifecycle specs, structured API-key auth audit logs, DB-service-mode API-key auth events in `audit.events`, scoped local reviewer service-account auth with raw-or-sha256 configured tokens, protected operator-route scope posture, intentionally public health/version routes, and production auth/RBAC blockers without adding full user identity, OAuth/OIDC, automatic key rotation, hosted log retention, or hosted identity-provider authorization. `docs/runbooks/mvp_operator.md` now documents reviewed live connectors, repo-local alert rules, CI supply-chain checks, dependency provenance guardrails, dependency artifact attestation guardrails, container image scan guardrails, digest-pinned base-image guardrails, cost-monitoring guardrails, scoped access-control guardrails, release-package guardrails, image-publication guardrails, hosted-deployment guardrails, and release-readiness guardrails as bounded, screening-only/review-gated or validate-only operator flows instead of describing the current app as fixture-only/no-auth. The approval-to-report operator sequence is proven in both in-memory and DB-backed API service configurations. When `ENABLE_LIVE_CONNECTORS=true`, `/intake` and `/report-runs` run bounded DS-001 first, bounded DS-002 after DS-001 approval, bounded DS-004 after DS-002 approval, and bounded DS-003 after DS-004 approval, returning `pending_connector_review` without creating report jobs until each connector review item is approved. Operators should keep the returned `area_id` and continue with `/report-runs` to complete the full request-time sequence; `POST /connector-runs/{ingest_run_id}/report-runs` remains the explicit manual one-connector report path and now requires `report:run`. Remaining Level 10 work is remaining non-DS-001/DS-002/DS-003/DS-004 source reviews, hosted billing integration and deeper spend controls, hosted log retention, automatic key rotation, external secret-manager integration, full user auth/RBAC, hosted deployment / published image attestation, any future DS-001 advanced terrain/report semantics beyond approved screening evidence, and any future DS-004 source-specific autonomous scheduling work.

Latest CI gate correction on 2026-06-06: current `origin/main` was locally green on
Windows but not CI-clean because GitHub Actions invoked tracked POSIX scripts that were
not executable, the `security-scan` job bypassed the documented wrapper and failed on
medium Bandit findings, and Docker Scout failed before scanning because the repository
had no Docker Scout entitlement. The corrective slice tracks `scripts/*.sh` as
executable, runs `./scripts/run_security_scan.sh` from CI so the gate fails on
HIGH/CRITICAL while reporting medium findings, fixes the Windows security-scan wrapper
to use Python 3.12, and makes `container-image-scan` build the image while recording the
live Docker Scout CVE scan as blocked unless `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`
are configured. This does not prove the container image is CVE-clean without Docker
Scout entitlement; it makes the blocked state explicit instead of silently overclaiming
or hard-failing every PR. Focused artifact tests, workflow YAML parsing, container-scan
static proof, release-readiness proof, and the security-scan wrapper pass. Remaining
review debt includes unresolved merged-PR threads, source-rights blockers
`DS-010`/`DS-011`/`DS-017`/`DS-023`, Bandit medium findings, and hosted production
blockers.

PR #19 remote CI follow-up on 2026-06-06 corrected additional CI-only failures: DB
migrations now run before DB-gated backend tests in `verify.ps1`/`verify.sh`,
`supply-chain` installs `PyYAML` before POSIX provenance validation, `release-readiness`
installs backend dependencies before source-readiness validation, and
`dependency-attestations` records private-repository GitHub attestation entitlement as a
blocked live attestation instead of claiming publication or hard-failing. GitHub
artifact attestations remain a real release blocker until repository visibility/plan
supports them; the lock/SBOM provenance artifacts still validate locally and in CI.
After the follow-up, PR #19 remote CI passed all configured jobs, including DB-enabled
verification.

Review-debt closeout pass on 2026-06-06 landed via PR #20 after PR and main CI passed.
Live defects from unresolved merged-PR review threads were patched
for source retrieval count validation, source-provenance review-bundle schema parity,
flood fixture quality fail-closed checks, fixture workflow quality gating before
side effects, source-failure evidence provenance preservation, raw
`SourceProvenanceService` retrieval adapter compatibility, atomic SQL connector review
queue enqueue, primary connector review-action OpenAPI required-reason parity, and
Windows API runner `OBJECT_STORE_ROOT` preservation. Focused pytest, ruff, mypy,
OpenAPI parity, `git diff --check`, full `.\scripts\verify.ps1`, post-merge detached
verification, and main CI passed for touched surfaces. Follow-up PR #20 review threads
then identified three remaining live issues now handled in an isolated follow-up:
connector review queue cross-workspace idempotency collisions fail closed instead of
returning another workspace item, source-provenance review bundles embed the strict
`SourceContract` schema, and reason-required primary review actions now require a
non-null request body in OpenAPI/runtime signatures. Focused pytest, ruff, mypy, and
full `.\scripts\verify.ps1` pass for that follow-up; DB smoke remains skipped locally
unless `RUN_DB_SMOKE=1`. Must-source readiness remains `sources=8 ready=4 blocked=4`
with `DS-010`, `DS-011`, `DS-017`, and `DS-023` blocked.

## Active lane: Source Readiness Closure (2026-06-07)

Goal: keep source-readiness truth aligned with live repo evidence, complete interrupted
OSM/NOAA/release-readiness tail cleanup, continue public-source readiness passes, and
choose the next source pass without overclaiming private MVP or Level 10 production
readiness.

Current state:

| Item | Status | Evidence |
|---|---|---|
| DB-enabled local verifier | separate proof | Run `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1` only when PostgreSQL/PostGIS prerequisites are available; default verify does not prove DB smoke |
| DS-007 BLM MLRS | connector-ready | Active federal mining-claim geospatial context only; no private mineral-rights, claim-boundary, title, mine-hazard, resource-value, extraction, environmental-liability, buildability, appraisal, lending, insurance, or investment conclusion claimed |
| DS-008 USGS MRDS | connector-ready | Historical mineral-occurrence screening only; no mineral-rights, hazard, resource-value, extraction, environmental-liability, buildability, appraisal, lending, insurance, or investment conclusion claimed |
| DS-011 County assessor | connector-ready as not-evaluated evidence | `AssessorNotEvaluatedConnector.query_area()` records explicit ASSESSOR_NOT_EVALUATED SOURCE_FAILURE evidence; this is not live assessor data |
| DS-015 State geological survey | connector-ready | NCGS 1985 statewide geologic map-unit context only; deprecated, generalized map scale; no hazard, mineral-resource, engineering, buildability, appraisal, lending, insurance, or investment conclusion claimed |
| DS-017 Commercial parcel vendor | blocked | Vendor/license/cost decision deferred; not required for private MVP |
| DS-020 NOAA NWS climate/weather | connector-ready | Bounded point/forecast-zone connector; administrative weather-zone context only, not climate normals or agricultural risk conclusions |
| DS-022 Census TIGER/ACS | connector-ready | Bounded TIGERweb tract/block-group geography context only; ACS demographic variables, protected-class analytics, neighborhood desirability, market/investment/lending suitability, and residential steering are excluded |
| DS-023 Local zoning ordinance PDFs | connector-ready, wired | Recorded-fixture zoning district connectors for reviewed county UDO tables; no live PDF retrieval or legal zoning conclusion claimed |
| DS-023 orchestration wiring | complete | Chatham/Brunswick zoning recorded-fixture orchestration and operator routes wired |
| DS-010 Buncombe parcel connector | complete | `buncombe_parcels.py`; ArcGIS property_bc_dis MapServer/1; pinnum/Acreage (no zoning field); county dispatch via centroid bounds |
| DS-010 Brunswick parcel connector | complete | `brunswick_parcels.py`; ArcGIS TaxParcels FeatureServer/0; PIN/CALCAC/Zoning; county dispatch; zoning available |
| DS-010 county dispatch | complete | `_classify_area_county()` with NC coordinate bounds; Buncombe/Brunswick orchestration functions wired; API routes added |
| Source readiness gate | hardened | `scripts/source_readiness.py` now reports `production_use_allowed`, `connector_implemented`, `connector_surfaces`, and `connector_ready` separately |

Key artifacts:
- `plans/2026-06-06-source-readiness-closure.md`
- `docs/source-reviews/ds-011.md`
- `docs/source-reviews/ds-023.md`
- `docs/source-reviews/ds-023-chatham-live-scope.md`
- `backend/app/source_registry/connector_inventory.py`
- `backend/app/api/live_connectors.py`
- `backend/app/api/connectors.py`
- `backend/app/connectors/__init__.py`
- `backend/app/connectors/usgs_mrds.py`
- `docs/source-reviews/ds-008.md`
- `backend/tests/api/test_usgs_mrds_connector_api.py`
- `backend/tests/connectors/test_usgs_mrds_connector.py`
- `backend/app/connectors/nc_geologic_map.py`
- `docs/source-reviews/ds-015.md`
- `backend/tests/api/test_nc_geologic_map_connector_api.py`
- `backend/tests/connectors/test_nc_geologic_map_connector.py`
- `backend/app/connectors/census_tiger.py`
- `docs/source-reviews/ds-022.md`
- `backend/tests/api/test_census_tiger_connector_api.py`
- `backend/tests/connectors/test_census_tiger_connector.py`
- `backend/tests/api/test_chatham_zoning_connector_api.py`
- `scripts/source_readiness.py`
- `backend/tests/source_registry/test_source_readiness.py`

Current Must-source readiness: `sources=8 ready=7 blocked=1`. DS-001, DS-002,
DS-003, DS-004, DS-010, DS-011, and DS-023 are connector-ready. DS-017 remains
blocked by license/cost/vendor decision. DS-023 readiness uses recorded-fixture
district-code lookup only; no raw PDF redistribution, live amendment tracking, or
legal zoning conclusion is claimed. DS-010 readiness is scoped to
`immediate_operator_api` and `request_time_orchestration`; durable live-job support
is not claimed for DS-010. Current all-priority readiness: `sources=25 ready=16
blocked=9`; DS-007 is connector-ready only for active federal mining-claim
context, DS-015 is connector-ready only for historical NCGS 1985 map-unit
context, DS-008 is connector-ready only for historical mineral-occurrence screening
context, and DS-022 is connector-ready only for administrative TIGERweb geography
context, not ACS demographics or protected-class analytics.

Last verified in this pass: 2026-06-14 focused DS-007 connector/API/readiness tests
passed (`22 passed`), OpenAPI parity tests passed (`3 passed`), source registry
readiness/seed tests passed (`16 passed`), source readiness reported all-priority
`sources=25 ready=16 blocked=9`, Must `sources=8 ready=7 blocked=1`, Should
`sources=6 ready=3 blocked=3`, and Later `sources=8 ready=5 blocked=3`.
Release-readiness proof passed, focused ruff/mypy passed, and default
`.\scripts\verify.ps1` passed with workspace validation, structural checks, backend
tests, ruff, and mypy on 306 source files green. The current release-readiness proof is
now full-catalog exact, maps every declared CI-backed gate to its proof command, and
keeps live load-test scenarios local/manual while CI validates the load-test artifacts.
`git diff --check` reported no whitespace errors; it warned that touched CSV/Markdown/
OpenAPI files will normalize line endings when Git next touches them. DB smoke was
skipped because `RUN_DB_SMOKE=1` was not set.

## Completed lane: Selected-County Evidence Utility Closure (completed 2026-06-06)

Active plan: `plans/2026-06-06-private-mvp-utility-proof.md` (extended for utility closure).
Geography: North Carolina — Buncombe, Chatham, Brunswick counties.
Goal: close the highest-value evidence gaps (terrain/Buncombe, parcels/Chatham,
wetlands+soils/Brunswick) so that promoted county cases have approved DB-backed dossiers
with useful evidence or explicit unknowns.

**Status: ALL 12 WORK PACKAGES COMPLETE (WP-1 through WP-12)**

| Work Package | Title | Status |
|---|---|---|
| WP-1..8 | Private MVP Utility Proof (US-001..US-008) | PASS |
| WP-9 | Buncombe terrain fixture connector + 3 terrain JSONs | PASS |
| WP-10 | Chatham parcel fixture connector + 3 parcel JSONs | PASS |
| WP-11 | Brunswick wetlands + soils fixture connectors + 5 JSONs | PASS |
| WP-12 | Tests/manifest/state updates + verify.ps1 clean | PASS |

Key artifacts added in WP-9..WP-12:
- `backend/app/connectors/terrain_fixture.py` — StaticTerrainFixtureConnector (DERIVED_METRIC)
- `backend/app/connectors/parcel_fixture.py` — StaticParcelFixtureConnector (SPATIAL_INTERSECTION)
- `backend/app/connectors/wetlands_fixture.py` — StaticWetlandsFixtureConnector (SPATIAL_INTERSECTION)
- `backend/app/connectors/soils_fixture.py` — StaticSoilsFixtureConnector (SPATIAL_INTERSECTION)
- `tests/fixtures/connectors/` — 11 new fixture JSON files (3 terrain, 3 parcel, 3 wetlands, 2 soils)
- `tests/fixtures/golden_aois/manifest.yaml` — terrain/parcels/wetlands/soils wired into 9 cases
- `backend/tests/private_mvp/test_utility_closure.py` — 2 RUN_DB_SMOKE-gated promoted-case tests
- `backend/tests/private_mvp/test_mvp_regression.py` — terrain added to Buncombe regression

Prior WP-1..8 artifacts:
- `tests/fixtures/golden_aois/` — 9 GeoJSON cases (3 per county)
- `config/private_mvp_beta_readiness.yaml` — private MVP gate registry
- `docs/geographies/nc/{buncombe,chatham,brunswick}/source_manifest.md`
- `backend/tests/private_mvp/test_mvp_regression.py` — 3 DB-smoke-gated county tests
- `backend/tests/reports/test_report_overclaim.py` — 4 Markdown overclaim checks
- `scripts/run_mvp_regression.ps1`
- `docs/runbooks/mvp_operator.md` — Private MVP path section added

Last verified: 2026-06-06 — `.\scripts\verify.ps1` → `verify: ok`; ruff clean; mypy clean 233 source files.
Residual risk: assessor NOT_EVALUATED for all 9 cases (no connector); DS-011/023 source-rights pending; DS-010 reviewed and approved-with-restrictions (Chatham live connector active).

## Completed lane: Local Source Readiness Closure — DS-010 / DS-011 / DS-023 (2026-06-06)

Goal: Write source review docs and promote DS-010 to connector-ready; document NOT_EVALUATED stance for DS-011 and DS-023.

| Source | Status | Outcome |
|---|---|---|
| DS-010 County GIS parcels (Chatham County) | approved-with-restrictions | Live connector unblocked; ready=true in source_readiness |
| DS-011 County assessor | pending | NOT_EVALUATED; no live connector; review doc written |
| DS-023 Local zoning ordinance PDFs | pending | fixture-backed; no live connector; review doc written |

Key artifacts:
- `docs/source-reviews/ds-010.md`, `ds-011.md`, `ds-023.md`
- `registers/data_source_registry.csv` DS-010 row updated
- `db/seeds/002_seed_source_registry.sql` DS-010 entry updated
- Historical 2026-06-06 source-readiness snapshot recorded here is superseded by the current checkpoint above.

Last verified for this historical lane: 2026-06-06; current source-readiness counts are recorded at the top of this file.

Prior lane (L10 production hardening) plans remain in `plans/` for reference. Production
hardening continues as a separate blocked lane and does not gate private MVP utility proof.

## 2026-06-17 Current checkpoint - operator runbook executability

- Status: PASS for the narrow documentation/validation slice on `operator-path`.
- Current authority trail: runtime/tests plus `scripts/private_mvp_readiness_check.py`
  now require the operator runbook to distinguish selected-county packaged-case delivery,
  generic `POST /report-runs` over already-ingested state, and no-server dossier output.
- Operator route examples now use explicit `{report_run_id}` placeholders instead of
  ambiguous `{id}` report-route placeholders.
- Selected-county evidence-rich delivery remains `POST /operator-cases/{case_id}/report`
  (HTTP/UI) or `scripts/generate_dossier.py --connector all --approve --artifact`
  (no-server). Generic `POST /report-runs` remains a separate integration pattern and
  does not auto-load the packaged selected-county corpus in default fixture mode.
- Last verified: 2026-06-17 via `python -m pytest -q ./backend/tests/test_private_mvp_readiness.py`,
  `python ./scripts/private_mvp_readiness_check.py`, and `python -m ruff check` on the
  touched readiness files.

## Historical local repo bootstrap state (superseded)

- Local Git initialized on `main`.
- `origin` is configured as `https://github.com/benjmcd/land-dd.git`.
- Local baseline commit exists on `main`: `ffb73e1` (`Establish governed scaffold baseline`).
- This bootstrap snapshot is historical. Current remote authority is live `origin/main`,
  which was fetched and fast-forwarded locally to `3aff43184e46c36dd4ee3caaac902cd7ba7f1d62`
  before the 2026-06-18 connector review workspace-scope slice.
- Local Codesight index exists at `.codesight/`; regenerate after significant code changes.
