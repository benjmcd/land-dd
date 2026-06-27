# Bologna Scope Authority Readiness

## Goal
Add a validate-only Bologna ODP-BOL-001 authority-promotion readiness gate that
proves the current review-only owner answer cannot record pilot-scope authority, while
making the later cited-authority recording slice explicit and machine-checkable.

## Non-goals
- Do not record a new owner answer or pilot-scope authority record.
- Do not select a Bologna AOI or boundary.
- Do not approve sources, source rights, source registry promotion, fixture capture,
  source-failure fixtures, DB seeds, runtime use, report artifacts, DS-017, hosted
  authority, Level 10 authority, or qualification PASS.
- Do not change public APIs, database schema, report semantics, or source readiness.

## Current state
- `config/bologna_owner_answer_intake.yaml` contains one `ODP-BOL-001`
  `approve_review_only` answer:
  `odp-bol-001-scope-pursuit-2026-06-26`.
- `config/bologna_pilot_scope_authority.yaml` has
  `authority_record_contract.current_authority_records: []`; its checker can validate
  complete future records in isolation, but the committed catalog remains blocked.
- `config/bologna_odp1_owner_response_gate.yaml` and
  `config/bologna_odp1_owner_answer_packet.yaml` align required owner-answer and
  pilot-scope authority-record fields to the intake and pilot-scope authority packet.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the hosted and Level 9/10 authority
  boundary; this slice must not claim hosted readiness or Level 10 completion.
- `ODP-BOL-002`, `ODP-BOL-003`, and `ODP-BOL-004` remain unresolved prerequisites for
  source-rights, recorded-source corpus, and DB-backed report proof.
- The active routing still points to the completed
  `plans/2026-06-26-bologna-scope-pursuit.md` plan, so the next pass needs a fresh
  executable plan and state routing.

## Proposed design
Add a small `bol_scope_auth` validate-only artifact that sits between the review-only
owner answer and the later real authority-record mutation.

Rejected alternatives:
- Directly record pilot-scope authority now. Rejected because no cited product/AOI
  authority exists.
- Stop with prose asking for owner input. Rejected because the future mutation would
  remain underspecified and easy to bundle with source/corpus/report changes.
- Add another generic blocker. Rejected because existing ODP gates already block the
  path; the missing piece is a checked promotion boundary for the later authority
  recording slice.

The chosen gate will validate that the current state is still review-only, that the
future promotion requires `approve_with_cited_authority`, that authority records must
cover all required scope decisions, and that downstream source/corpus/report updates
remain disallowed even after a valid ODP-BOL-001 promotion.

## Bottom-up sequence
1. Add `config/bol_scope_auth.yaml` with current blocked state, promotion readiness
   requirements, allowed future mutation targets, and no-overclaim controls.
2. Add `scripts/bol_scope_auth_check.py` plus Windows/POSIX wrappers.
3. Add focused artifact tests proving validation passes today and fails closed if the
   current answer is treated as cited authority.
4. Route the new artifact through `MANIFEST.md`, qualification crosswalk, task queue,
   plans README, project state, worklog, and validation log.
5. Run focused checks, then the canonical verification gate.

## Files likely to change
| File | Expected change |
|---|---|
| `config/bol_scope_auth.yaml` | New validate-only readiness gate. |
| `docs/runbooks/bol_scope_auth.md` | Operator boundary and use instructions. |
| `scripts/bol_scope_auth_check.py` | New fail-closed checker. |
| `scripts/run_bol_scope_auth_check.ps1` | Windows wrapper. |
| `scripts/run_bol_scope_auth_check.sh` | POSIX wrapper. |
| `backend/tests/test_bol_scope_auth_artifacts.py` | Focused tests. |
| `config/qualification/readiness_crosswalk.yaml` | Map the checker to existing Bologna authority criteria. |
| `MANIFEST.md` | Route the new artifact. |
| `tasks/task_queue.yaml` | Mark the new slice active/completed and keep downstream blockers. |
| `plans/README.md` | Update current routing. |
| `state/PROJECT_STATE.md` | Update current checkpoint and next steps. |
| `state/WORKLOG.md` | Record implementation. |
| `state/VALIDATION_LOG.md` | Record verification. |

## Tests / verification
Expected focused commands:

```powershell
py -3.12 scripts\bol_scope_auth_check.py
.\scripts\run_bol_scope_auth_check.ps1
py -3.12 -m pytest backend\tests\test_bol_scope_auth_artifacts.py -q
py -3.12 scripts\validate_qualification.py --root . --layout repo
```

Final gate:

```powershell
.\scripts\verify.ps1
```

Expected signal: all checks pass, while `current_authority_records` remains empty and
all downstream Bologna implementation targets remain blocked.

## Risks and blockers
- The true blocker remains external owner authority. This slice cannot and must not
  turn `approve_review_only` into `approve_with_cited_authority`.
- The new checker must be mapped coherently in the qualification crosswalk if it is
  advertised as a qualification evidence surface.
- The artifact must avoid broadening the Bologna path into ODP-BOL-002/003/004 work.

## Decision log
- 2026-06-27: Chose a validate-only authority-promotion readiness gate because direct
  promotion lacks cited owner authority, while prose-only routing leaves the future
  mutation boundary too implicit.

## Progress log
- 2026-06-27: Live audit found one review-only ODP-BOL-001 answer, empty
  pilot-scope authority records, and blocked source/corpus/report follow-ons.
- 2026-06-27: Added `config/bol_scope_auth.yaml`, checker, wrappers, runbook, focused
  tests, manifest/crosswalk/backlog routing, and task/project/plan state updates.
- 2026-06-27: Focused checks passed for the new gate, backlog checker, readiness
  matrix, qualification status, structural qualification validation, change-impact,
  ruff, mypy, and qualification selftest. The first full verify run caught a missing
  human crosswalk-doc row and stale readiness-core active-plan assertion; both were
  fixed. The second `.\scripts\verify.ps1` passed.
