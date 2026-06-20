# Reconciliation Slice Map

## Scope

Provisional dependency grouping for dirty-root candidate work after the initial
file-level inventory. This map is based on recoverable candidate plan files and the
dirty-root task sequence. It is not a retain/merge decision.

The original REC-001 baseline was `origin/main` at
`c3364ea01605cef09e03da6da8551fa4d1a155e8`. Current live authority is recorded in the
update note below.

Initial per-file disposition decisions are recorded in
`state/reconciliation-dispositions.md`. This slice map explains grouping; the
disposition matrix controls retain/rework/defer/archive/discard decisions.

## 2026-06-20 Live Update After G9a

Live `origin/main` has advanced to
`b525439e6bcddefba81c7d6bf12290b3f8551b55` after PR #101 merged the `G9a` custom AOI
UI runtime smoke slice. The original slice map remains the historical grouping for the
dirty-root candidate stack, but its first-content-review sequence is stale: multiple
retained G-slices have now been reconstructed from clean worktrees and merged.

The next Lane 1 pass should not restart from the original `c3364ea` inventory or copy
dirty-root files wholesale. It should regenerate a residual comparison against current
live `origin/main` and classify each remaining dirty-root candidate path as:

| Residual class | Meaning |
|---|---|
| `ALREADY_LANDED` | The retained concept is present on live `origin/main`; no new slice needed. |
| `LANDED_DIFFERENTLY` | Live `origin/main` solved the concept by a narrower or safer implementation; treat dirty-root content as historical evidence only. |
| `STILL_DIVERGENT` | Candidate behavior still differs materially and may need a focused plan. |
| `DEFER_STILL_BLOCKED` | Candidate remains blocked by hosted, source, DS-017, identity, artifact, or geography prerequisites. |
| `OBSOLETE` | Candidate no longer fits the product/architecture after landed slices. |
| `COORDINATION_OR_GENERATED` | Agent coordination, cache, generated, or local runtime state; do not promote as product work. |

Only after this residual classification should the next implementation worktree be
selected.

## Slice Groups

| Group | Candidate range | Candidate purpose | Initial disposition |
|---|---|---|---|
| G0 | `REC-001` | Reconciliation control plane: state envelope, inventory, slice map, disposition matrix. | Active in clean worktree. |
| G1 | `R-023` | Local-only raw-data UI posture: local browser no-login posture plus raw-data inventory route. | Rework narrowly; split auth posture from raw-data route. |
| G2 | `R-024` to `R-025` | DB-backed local UI smoke and deployment-smoke/release-readiness guard. | Review after G1 because smoke expectations depend on local UI posture. |
| G3 | `R-026` to `R-033` | Raw source readiness, readiness overview, selected-geography, expansion, release, deployment, and production-authority UI surfaces. | Source-readiness and deployment-readiness retain as focused slices; expansion/production/coverage defer. |
| G4 | `R-034` to `R-041` | Account-free runtime, project trajectory, validation evidence/proof, dossier/source/raw-evidence provenance, and local production profile. | Review after baseline route posture and readiness surfaces are clear. |
| G5 | `R-042` to `R-048` | Selected-county source/runtime provenance bridge, provenance status UI, report inventory/list contracts, evidence deps, and raw claim task inventory. | Higher semantic risk; requires report/evidence contract review before landing. |
| G6 | `R-049` to `R-053` | Local auth surface hardening plus operations/security/performance/product-correctness guardrail UI. | Operations/security/performance retain as isolated read-only guardrail slices; product-correctness defers. |
| G7 | `R-054` to `R-055` | Release-package manifest verification and CI package-manifest gate. | Retain as an early packaging/CI slice. |
| G8 | `R-056` | Observability readiness UI. | Retain as local-only catalog/parser/UI slice, but land after deployment/release boundaries are clear. |

## First Content-Review Target

`R-023 Local-only raw-data UI posture` was the first content-review target because its
dirty-root plan depends only on `R-022` and it establishes assumptions used by later
smoke, readiness, and account-free runtime slices.

Content review notes are recorded in `state/r023-review.md`. The review found that
R-023 should be reconstructed narrowly from live `origin/main`; the dirty-root `ui.py`
and smoke scripts already include later readiness/provenance/guardrail/release and
observability routes and should not be copied wholesale.

After the broader disposition pass, `R-023` is no longer the only early landing
candidate. `state/reconciliation-dispositions.md` ranks package-manifest/CI,
source-readiness extraction, local auth posture, and raw-data inventory as the earliest
coherent candidates. Each still requires a fresh current-main worktree and focused
tests before implementation.

Before implementing or cherry-picking anything from `R-023`, review these files from the
dirty root against live `origin/main`:

| Surface | Candidate files |
|---|---|
| UI runtime | `backend/app/api/ui.py`, `backend/app/api/ui_shared.py` |
| Local/non-local auth boundary | `backend/app/api/ui_auth.py`, `config/access_control.yaml`, `docs/runbooks/access_control.md` |
| UI tests | `backend/tests/api/test_ui_routes.py`, `backend/tests/api/test_ui_operations_routes.py`, `backend/tests/api/test_ui_review_routes.py`, `backend/tests/api/test_ui_live_connector_jobs.py` |
| Smoke proof | `scripts/ui_runtime_smoke.py`, `scripts/ui_browser_smoke.mjs` |
| Operator docs/design | `DESIGN.md`, `docs/runbooks/mvp_operator.md` |
| State/control | `plans/2026-06-19-local-only-raw-data-ui.md`, `tasks/task_queue.yaml`, `state/*` candidate entries |

## R-023 Review Questions

- Does the candidate keep JSON/API auth and reviewer scope checks intact?
- Is local no-login behavior strictly limited to local/dev/test browser operation?
- Are `/ui/auth*`, login, account, session, and logout routes absent or dormant as
  claimed?
- Does raw-data inventory expose current runtime state without seeding, mutating, or
  implying live-source/hosted proof?
- Can the slice be reapplied without bringing later R-024+ assumptions into the same
  patch?
- Are docs/state updates limited to behavior proven by tests and validators?

## Stop Conditions

- Stop and split further if `R-023` requires broad `backend/app/api/ui.py` changes that
  already contain later R-026+ route work.
- Stop if local no-login behavior weakens non-local fail-closed auth or JSON/API route
  protections.
- Stop if raw-data inventory depends on generated local artifacts, seeded hidden state,
  live connectors, or hosted assumptions.
- Stop if the candidate cannot be validated without absorbing unrelated dirty-root
  state prose or coordination inbox material.
- Stop if implementation depends on copying dirty-root `backend/app/api/ui.py` or smoke
  scripts wholesale instead of reconstructing the minimal local-browser posture.
