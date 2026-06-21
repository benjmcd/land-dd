# Handoff from Claude Code -> Codex

## ACTIVE HANDOFF (2026-06-21): EQ Phase 2 — Operationalize the Qualification Control Plane

Phase 1 (EQ-1…EQ-5) is merged. Next milestone makes the control plane EXECUTABLE.
Full self-contained spec: `plans/2026-06-21-eq-phase2-operationalize.md` (read it whole first).

**Session goal to set (use your goal function / `/goal`):**
> Operationalize the empirical-qualification control plane: make qualification status
> executable and drift-proof (derived from the crosswalk + real checker results), make
> change-impact invalidation executable, and collect repo-local evidence for the
> auto-verifiable P0 invariants — all while remaining honestly `P0 = BLOCKED`, with no gate
> moved to PASS and no owner-decision unfrozen.

**Lanes (bottom-up, one PR each):**
- **EQP2-1**: `scripts/qualification_status_check.py` — derive gate/overlay status from catalog + crosswalk + real checker exit results; assert committed status matches (fail-closed on drift); verify wiring; selftest drift case. Status stays BLOCKED/NOT_RUN only.
- **EQP2-2**: `scripts/qualification_change_impact_check.py` — executable change-impact (diff → implicated change_classes + criterion_ids); advisory, no false gate; selftest mapping case.
- **EQP2-3**: collect repo-local evidence for auto-verifiable P0 invariants (P0-021 test-suppression, P0-023 evidence-linkage, P0-004 sealed-isolation, P0-005 anti-contamination); link in status; KEEP BLOCKED (no PASS); mark them "auto-evidenced, still target-blocked" in QUALIFICATION_PARAMETERIZATION_BACKLOG.md.
- **EQP2-4**: subordinate existing checkers (release_readiness_check.py, readiness_matrix_check.py, authority checkers) so they advertise their crosswalk criterion IDs and feed status; validator proves crosswalk↔checker parity. Additive reporting only — no gate-behavior change.

**Hard non-goals:** no gate/criterion PASS (P0 stays BLOCKED; keep the P0-freeze rule), no
unfreezing owner-decisions (candidate.* null, source_profile_ids empty, domain profiles
template-only, targets DRAFT), no Q3A/B/C, no AI/CG/FIN/E rubrics/targets, no
DB/API/auth/report-semantics changes, no file deletion (archive instead), no AI/agent/model
attribution. Do NOT add new ad-hoc product/guardrail modules — subordinate, don't duplicate.

**ISOLATION — a parallel Claude lane is running concurrently. Coordinate to avoid conflicts:**
- You OWN: `config/qualification/**`, `schemas/qualification/**`, `scripts/{validate,selftest,qualification_*}_qualification*.py` + new `scripts/qualification_*`, `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`, `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md`, `docs/qualification/**`, and (EQP2-4) the existing readiness/authority checker scripts. You also OWN ALL shared state/control files (`state/PROJECT_STATE.md`, `WORKLOG.md`, `VALIDATION_LOG.md`, `tasks/task_queue.yaml`, `MANIFEST.md`, `plans/README.md`, `LEVEL_9_10_GATE_MATRIX.md`, `residual-reconciliation.md`).
- Do NOT touch: `backend/app/api/ui.py`; the DEFER product modules `backend/app/{dossier_readiness,product_correctness,production_authority,expansion_readiness,selected_geography_coverage}.py` + tests; any `defer/*` branch; and **do not create/remove/prune git worktrees other than your own `worktrees/eqp2-*`** (the parallel lane is cleaning stale worktrees and will avoid yours).
- The parallel Claude lane is read-only QA of the EQ spine + worktree housekeeping; it will NOT edit your subsystem or the shared state files.

**Canonical authority:** live `origin/main` (was `8dadfbf` at handoff). If the plan conflicts
with live main, reconcile to main first.

**CI note:** there IS a dedicated `qualification-selftest` job in `.github/workflows/ci.yml`
(runs the selftest + validator wrappers), AND verify.ps1/verify.sh also run them. Wire new
qualification checks in BOTH: a verify step (local) AND the CI job/wrappers (enforced).

---

### Channel reference (unchanged)
- File-drop:  `./scripts/handoff_to_codex.sh "task for Codex"` then paste the printed pickup line.
- GUI inject: `./scripts/handoff_to_codex.sh --ipc <conversationId> "task"` (thread must be open in the Desktop app).
