# Level 9/10 Readiness Reconciliation

## Goal
Turn the post-private-MVP repository state into an executable roadmap from
selected-county utility proof toward hosted, multi-geography, production-grade
operation without losing the distinction between proven local/private-MVP behavior,
validate-only production artifacts, and externally blocked hosted-production gates.

## Non-goals
- No hosted infrastructure creation, DNS/TLS change, secret write, registry push, or
  public endpoint exposure.
- No OAuth/OIDC, full user-account/RBAC implementation, billing integration, or
  external secret-manager integration in this planning slice.
- No new source, geography, rulepack, connector, schema, API, report semantic, or UI
  behavior change.
- No claim that Level 10 is complete while hosted deployment, DS-017/source readiness,
  full user auth/RBAC, hosted alerting, registry publication, and billing remain blocked.

## Current state
- `state/PROJECT_STATE.md` records that private-MVP selected-county proof is complete
  while hosted-production blockers remain.
- `config/private_mvp_beta_readiness.yaml` separates complete `private_mvp_beta` gates
  from blocked `hosted_production` gates.
- `config/release_readiness.yaml` catalogs Level 10 proof surfaces and explicit release
  blockers: hosted deployment attestation, registry image publication attestation,
  hosted billing reconciliation, non-ready Must sources, full user auth/RBAC, and hosted
  alerting.
- `config/hosted_deployment.yaml` is validate-only and blocked until platform, TLS,
  secret-manager, database, registry image digest, billing, and alerting authorities
  exist.
- `MILESTONE_MAP.md` defines Level 9 as product-grade MVP workflow and Level 10 as
  production-grade end-to-end operation.
- After PR #62, `plans/README.md` and `tasks/task_queue.yaml` still routed to the
  completed UI CSRF route-coverage slice; this plan supersedes that as the active
  coordinator authority.

## Proposed design
Use a reconciliation-first route instead of immediately adding another runtime slice.
The next productionization work needs a current, gate-by-gate matrix that maps Level 9
and Level 10 requirements to existing proof surfaces, known blockers, and the lowest
unblocked implementation pass.

Rejected alternatives:
- Re-activating the historical `2026-06-05-l10-production-hardening.md` plan would bury
  current blockers in an oversized progress log.
- Continuing with the completed CSRF plan would misroute future agents to finished work.
- Starting hosted implementation now would cross explicit blockers in
  `config/hosted_deployment.yaml`.

## Bottom-up sequence
1. Route the repo to this active reconciliation plan.
2. Run current validate-only readiness checks to re-establish private-MVP, release, hosted,
   access-control, and source-readiness facts.
3. Produce a Level 9/10 gate matrix that classifies each gate as proven, validate-only,
   blocked, or missing, with authoritative evidence paths.
4. Select the lowest-dependency unblocked implementation slice from that matrix.
5. For hosted-production blockers, record the exact external decision/evidence needed
   before implementation may proceed.
6. Only after the matrix is current, open a narrow implementation plan for the selected
   pass.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-18-level9-10-readiness-reconciliation.md` | Active coordinator plan |
| `plans/README.md` | Route current active plan to this plan |
| `tasks/task_queue.yaml` | Route active plan and add the reconciliation task |
| `state/PROJECT_STATE.md` | Record the active readiness-reconciliation checkpoint |
| `state/WORKLOG.md` | Record routing/reconciliation progress |
| `state/VALIDATION_LOG.md` | Record validation checks run for this planning slice |

Future matrix pass may change:
| File | Expected change |
|---|---|
| `state/LEVEL_9_10_GATE_MATRIX.md` | Gate-by-gate Level 9/10 evidence classification |
| `state/PROJECT_STATE.md` | Gate matrix summary and next selected implementation pass |
| `plans/*.md` | New implementation plan for the selected unblocked pass |
| `config/release_readiness.yaml` | Only if the matrix identifies a stale or missing gate |
| `scripts/*_check.py` | Only if a readiness validator misses a current required invariant |
| `scripts/readiness_matrix_check.py` | Validate-only guard that the matrix covers every Level 9/10 gate |
| `scripts/run_readiness_matrix_check.ps1` | Windows wrapper for the matrix guard |
| `scripts/run_readiness_matrix_check.sh` | POSIX wrapper for the matrix guard |
| `backend/tests/test_readiness_matrix_artifacts.py` | Focused artifact coverage for the matrix guard |

## Tests / verification
Planning/routing slice:
```powershell
python .\scripts\private_mvp_readiness_check.py
python .\scripts\release_readiness_check.py
python .\scripts\hosted_deployment_check.py
python .\scripts\access_control_check.py
python .\scripts\source_readiness.py --priority Must --json
python .\scripts\readiness_matrix_check.py
cd backend; python -m pytest -q .\tests\test_readiness_matrix_artifacts.py
git diff --check
```

Full handoff gate if any validator or runtime proof changes:
```powershell
.\scripts\verify.ps1
```

## Risks and blockers
- The repo has many older state entries; the matrix must prefer current config/checker
  outputs and live `origin/main` over historical progress logs.
- Hosted-production work remains blocked until external authorities exist for platform,
  DNS/TLS, secret management, database instance, registry image digest, billing, and
  alerting.
- Level 9 private-MVP proof must not be used as evidence for hosted multi-user
  production auth/RBAC or source entitlement enforcement.
- DS-017 remains a full-release source-readiness blocker unless a current readiness
  check proves otherwise.

## Decision log
- 2026-06-18: Chose a reconciliation plan because private-MVP readiness is complete,
  current release/hosted catalogs are validate-only, and the previous active CSRF plan
  has been merged.

## Progress log
- 2026-06-18: Created the active plan and routed the repo away from the completed UI CSRF
  route-coverage slice.
- 2026-06-18: Validate-only readiness checks passed for private MVP, release readiness,
  hosted deployment boundary, access control, and Must-source readiness. Current
  Must-source readiness remains `sources=8 ready=7 blocked=1`, with DS-017 blocked.
- 2026-06-18: Added `state/LEVEL_9_10_GATE_MATRIX.md` to classify Level 9 and Level 10
  gates as proven, validate-only, partial, blocked, or missing from current evidence.
- 2026-06-18: Added `scripts/readiness_matrix_check.py`, thin platform wrappers, and a
  focused test so the matrix must cover every Level 9/10 gate from `MILESTONE_MAP.md`.
- 2026-06-18: Matrix validator, Windows wrapper, focused matrix artifact tests, ruff,
  mypy, whitespace check, and existing readiness validators passed; DS-017 remains the
  only blocked Must source.
- 2026-06-18: Read-only review found the matrix prose was safer than the checker. The
  checker now pins high-risk hosted/source/auth/security/performance statuses and `R-001`
  includes the matrix validator and focused artifact test.
