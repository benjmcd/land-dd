# R-023 Candidate Review

## Scope

Content-review notes for dirty-root candidate `R-023 Local-only raw-data UI posture`.
This review uses the dirty-root candidate files as evidence but keeps live `origin/main`
as authority.

## Candidate Plan Facts

Dirty-root plan: `plans/2026-06-19-local-only-raw-data-ui.md`.

Stated goal: make local browser operator UI credential-free and raw-data-first while
preserving JSON/API route-scope checks and non-local fail-closed behavior.

Stated non-goals include no hosted identity, no full RBAC, no API auth weakening, no DB
schema change, no report semantic change, no deletion of auth/session source files, and
no claim that local no-login mode is safe for internet-exposed hosting.

## Actual Candidate Diff Surface

The R-023 listed file set is already much larger than a minimal local-only raw-data
posture slice in the current dirty root:

```text
13 files changed, 7182 insertions, 648 deletions
backend/app/api/ui.py: 5170 changed lines
scripts/ui_runtime_smoke.py: 702 changed lines
scripts/ui_browser_smoke.mjs: 687 changed lines
```

`backend/app/api/ui.py` in the dirty root already imports and renders later surfaces
that do not belong to a minimal R-023 patch, including deployment readiness, dossier
readiness, expansion readiness, observability readiness, production authority, project
readiness, release readiness, selected source-readiness, guardrail routes, provenance
routes, and dossier rendering.

`scripts/ui_runtime_smoke.py` also already exercises later routes such as readiness,
dossier-readiness, release-readiness, operations/security/performance/product
guardrails, observability-readiness, deployment-readiness, production-authority, and
auth-disabled route checks.

## Extractable Candidate Pieces

These pieces appear plausibly relevant to a reconstructed minimal R-023 slice, subject
to fresh implementation and focused tests from live `origin/main`:

- `backend/app/api/ui_shared.py`: local implicit reviewer principal, local browser
  operator text, and credential-free local display helpers.
- `backend/app/api/ui_auth.py`: local account-free behavior for `/ui/auth*` routes
  when app env is local and API key auth is not required.
- `backend/tests/api/test_ui_routes.py`: local-operator assertions and non-local
  reviewer requirement tests.
- `config/access_control.yaml` and `docs/runbooks/access_control.md`: local browser
  posture documentation, if the runtime behavior is reimplemented and proven.

## Non-Extractable As-Is

Do not copy the dirty-root versions of these files wholesale for R-023:

- `backend/app/api/ui.py`
- `scripts/ui_runtime_smoke.py`
- `scripts/ui_browser_smoke.mjs`
- broad `DESIGN.md` and `docs/runbooks/mvp_operator.md` changes
- local candidate `state/*` and `tasks/task_queue.yaml` entries

They already carry later readiness/provenance/guardrail/release/observability work and
would collapse many candidate lanes into one patch.

## Required Reconstruction Test

A minimal R-023 implementation should prove at least:

- local `/ui/` renders without login/account/reviewer credential inputs;
- local selected-county fixture report creation works without submitted reviewer
  credentials and records the local operator principal;
- invalid submitted reviewer credentials still fail;
- non-local/protected settings still require reviewer credentials/session as before;
- `/ui/auth*`, login, account, session, and logout browser routes are absent, inert, or
  explicitly account-free only in local mode;
- raw-data inventory route renders current runtime state without seeding or mutating
  state;
- JSON/API auth and reviewer scope checks remain intact.

## Recommendation

Reconstruct R-023 as a narrow product slice from live `origin/main`, using the dirty-root
candidate only as reference. Do not cherry-pick or copy the broad dirty-root UI/smoke
files. If reconstruction needs later R-026+ readiness routes, stop and split the local
browser posture from the raw-data inventory route.
