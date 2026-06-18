# UI CSRF Route Coverage

## Goal
Pin route-level CSRF regressions for cookie-authorized UI mutation routes and extend
the static access-control checker so those proofs cannot silently disappear.

## Non-goals
- No new authentication mechanism.
- No change to CSRF token format, cookie format, reviewer scopes, or route semantics.
- No public API, OpenAPI, database schema, connector runtime, or report behavior change.
- No browser smoke expansion unless route-level TestClient coverage exposes a real UI
  rendering issue.

## Current state
- `backend/app/api/ui_shared.py` centralizes CSRF protection in `require_ui_csrf()`.
  It requires a signed submitted token when a UI API-key, reviewer, or report identity
  cookie is present.
- `backend/app/api/ui.py`, `backend/app/api/ui_review.py`, and
  `backend/app/api/ui_operations.py` already call `require_ui_csrf()` on the relevant
  mutation handlers.
- Existing tests cover shared UI API-key-cookie CSRF on `/ui/intake`, selected-county
  UI report creation, identity auth, approve-report, connector approve, operations
  dashboard POST, and logout.
- Audit proof gap before this slice: route-specific missing-CSRF regressions were not
  pinned for reviewer-session `/ui/intake`, report retry, connector
  reject/requeue/cancel/resume-report, or operations recovery-preview POST.
- `scripts/access_control_check.py` checked broad helper usage and a smaller named-test
  set before this slice, but it did not require the remaining route-specific test names.

## Proposed design
Add route-level tests first, using existing TestClient helpers and real cookie sessions:

- For `/ui/intake`, prove a reviewer-session cookie makes the POST require CSRF before
  payload validation.
- For `/ui/report-runs/{id}/retry`, prove reviewer-session retry requires CSRF and still
  succeeds with the token from the failed-report page.
- For connector review reject/requeue/cancel/resume-report, prove reviewer-session POSTs
  without CSRF fail with `403`, and valid reviewer-session CSRF tokens still allow
  each action to reach its expected state transition.
- For `/ui/operations/recovery-preview`, prove reviewer-session POST without CSRF fails
  with `403`, and a valid reviewer-session CSRF token still renders the preview.
- Extend `scripts/access_control_check.py` to require these test names across
  `test_ui_routes.py`, `test_ui_review_routes.py`, and
  `test_ui_operations_routes.py`.

Rejected alternatives:
- Rewriting CSRF middleware would broaden scope without evidence of a runtime miss.
- Adding only static checker phrases would not prove behavior.
- Adding only behavior tests would not prevent future deletion of the coverage.

## Bottom-up sequence
1. Add failing route-level tests for the currently unpinned CSRF surfaces.
2. Run focused pytest selections and confirm failures where names/behavior are absent.
3. If runtime behavior is already correct, update only the static checker to require the
   new tests.
4. Run focused UI route tests, access-control checker, ruff/mypy on touched files, and
   default verification.
5. Update state/worklog/validation logs.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/tests/api/test_ui_routes.py` | Add intake and retry reviewer-session CSRF route tests |
| `backend/tests/api/test_ui_review_routes.py` | Add connector review action CSRF reject and valid-token route tests |
| `backend/tests/api/test_ui_operations_routes.py` | Add recovery-preview POST CSRF reject and valid-token route tests |
| `scripts/access_control_check.py` | Require the new named route-level CSRF tests |
| `plans/README.md` | Route active plan to this slice |
| `tasks/task_queue.yaml` | Route active plan to this slice |
| `state/PROJECT_STATE.md` | Record checkpoint after behavior lands |
| `state/WORKLOG.md` | Record implementation summary |
| `state/VALIDATION_LOG.md` | Record validation evidence |

## Tests / verification
Focused:
```powershell
cd backend
python -m pytest -q .\tests\api\test_ui_routes.py -k "csrf or retry"
python -m pytest -q .\tests\api\test_ui_review_routes.py -k "csrf or reviewer_session"
python -m pytest -q .\tests\api\test_ui_operations_routes.py -k "csrf or recovery_preview"
python -m ruff check .\tests\api\test_ui_routes.py .\tests\api\test_ui_review_routes.py .\tests\api\test_ui_operations_routes.py ..\scripts\access_control_check.py
python -m mypy .\tests\api\test_ui_routes.py .\tests\api\test_ui_review_routes.py .\tests\api\test_ui_operations_routes.py
cd ..
python .\scripts\access_control_check.py
```

Handoff:
```powershell
.\scripts\verify.ps1
```

## Risks and blockers
- Tests must distinguish header-submitted reviewer credentials, which do not require
  CSRF, from reviewer-session cookie authorization, which does.
- The access-control checker is static and should name behavioral tests rather than
  inspect exact route internals too deeply.
- Avoid DB-backed tests for this slice unless an existing helper demands DB state; all
  targeted UI paths can be covered with in-memory services.

## Decision log
- 2026-06-18: Treat the CSRF work as a proof-hardening slice because repo audit shows
  the shared runtime helper is already installed on the relevant route handlers.

## Progress log
- 2026-06-18: Created plan after artifact-path trust PR #61 merged to live `main`.
- 2026-06-18: Added route-level reviewer-session CSRF regressions for UI intake,
  report retry, connector review mutations, and operations recovery-preview.
- 2026-06-18: Added valid-CSRF success coverage for connector reject/requeue/cancel/
  resume-report and operations recovery-preview to prove the new route pins do not
  only cover rejection paths.
- 2026-06-18: Extended `scripts/access_control_check.py` to require the new named
  route-level CSRF proof tests.
- 2026-06-18: Focused UI route/review/operations CSRF tests, access-control artifact
  proof, ruff, mypy, and static access-control validation passed.
