# Bologna Recorded-Source Corpus Contract

## Goal
Add a validate-only recorded-source corpus contract for the future Bologna pilot. The
contract should make fixture-manifest prerequisites machine-checkable before any
recorded fixture capture, runtime use, report use, source registry promotion, or
multi-geography generalization can happen.

## Non-goals
- Do not select a Bologna AOI.
- Do not approve Italy/EU/local sources, source rights, source registry rows, fixture
  capture, source-failure fixtures, connectors, runtime use, report use, DB seeds, or
  rulepacks.
- Do not unblock DS-017, hosted deployment, identity/RBAC, hosted observability,
  billing, image publication, or Level 10 status.

## Current state
Live `origin/main` is `6253917809b5fc20a6d12c9a41678ea31c3d1de1`, which includes PR
#115 (`PR114-SYNC`). Bologna has source candidates, source-rights review structure, and
source-authority intake, but the recorded-source corpus itself is still only a prose
blocker in preflight and the production authority packet.

## Design
Add `config/bologna_recorded_source_corpus.yaml` plus a checker, wrappers, runbook, and
artifact tests. The checker cross-checks candidate ids and required evidence against
`config/bologna_source_authority_intake.yaml` and `config/bologna_source_rights.yaml`.
Every corpus row stays blocked, fixture-manifest entries stay disallowed, and
source-failure fixtures stay disallowed until upstream authority exists.

Compose the checker into `config/bologna_preflight.yaml` and release readiness so the
contract is validated by the existing authority graph.

The Level 9/10 authority context remains governed by
`state/LEVEL_9_10_GATE_MATRIX.md` and `state/PRODUCTION_AUTHORITY_PACKET.md`; a
blocked recorded-source corpus contract is not hosted production proof.

## Files likely to change

| File | Expected change |
|---|---|
| `config/bologna_recorded_source_corpus.yaml` | New validate-only corpus contract |
| `docs/runbooks/bologna_recorded_source_corpus.md` | New runbook |
| `scripts/bologna_recorded_source_corpus_check.py` | New fail-closed checker |
| `scripts/run_bologna_recorded_source_corpus_check.ps1` | Windows wrapper |
| `scripts/run_bologna_recorded_source_corpus_check.sh` | POSIX wrapper |
| `backend/tests/test_bologna_recorded_source_corpus_artifacts.py` | Focused artifact tests |
| `config/bologna_preflight.yaml` and checker/tests | Compose corpus contract |
| `config/release_readiness.yaml`, checker/tests, runbook | Compose release proof |
| `MANIFEST.md`, `state/PRODUCTION_AUTHORITY_PACKET.md`, `plans/README.md`, `tasks/task_queue.yaml`, `state/PROJECT_STATE.md`, `state/WORKLOG.md`, `state/VALIDATION_LOG.md` | Routing/state updates |

## Verification
```powershell
py -3.12 .\scripts\bologna_recorded_source_corpus_check.py
py -3.12 .\scripts\bologna_preflight_check.py
py -3.12 .\scripts\bologna_source_authority_intake_check.py
py -3.12 .\scripts\bologna_source_rights_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
cd backend; py -3.12 -m pytest tests\test_bologna_recorded_source_corpus_artifacts.py tests\test_bologna_preflight_artifacts.py tests\test_release_readiness_artifacts.py -q
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks and blockers
This slice is useful only as a contract. It does not start Bologna or reduce the
external authority needed for product/AOI/source review, DS-017 treatment, hosted
authority, or Level 10 proof.
