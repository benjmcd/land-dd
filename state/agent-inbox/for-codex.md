# Handoff from Claude Code -> Codex

## ACTIVE HANDOFF (2026-06-21): Harden the Qualification Control Plane

EQP2 (operationalize) is complete + sound. Next milestone fixes the verified review-bot
defects in the control plane itself, and **stops the Bologna scaffolding** (externally blocked,
no actionable value). Full self-contained spec: `plans/2026-06-21-harden-control-plane.md`
(read it whole first; re-confirm each finding against current main before fixing).

**Session goal to set (use your goal function / `/goal`):**
> Harden the empirical-qualification control plane: resolve the verified review-bot
> correctness/security defects in the qualification validators, checkers, crosswalk, and status
> derivation — re-confirming each against current main, fixing the still-valid ones with tests,
> and keeping the framework honestly `P0 = BLOCKED`. STOP adding new Bologna/authority
> scaffolding: it is externally blocked and adds no actionable value until an external owner
> decision exists.

**Lanes (bottom-up, one PR each):**
- **HCV-1**: `validate_qualification.py` correctness gaps (#126/#127) — expired-gate check, result gate_id↔status match, scope/version identity, evidence-ref resolution, FROZEN-with-TBD rejection, domain modality/channel coverage, source coverage vs targets, CONDITIONAL-rights proof, P0 blocked_record validated even with result_path, RAW_EXPORT export-right; + `qualification_result.schema.json` require reviewer/repro metadata for PASS. Each fix → a selftest fail-closed case. NO gate ever becomes PASS.
- **HCV-2**: checker robustness/security — `checklist_dry_run_check.py` (#82: reject empty contains/regex; more checklist markers; **confine path resolution to repo root — path-traversal**), `package_manifest_check.py` (#88: reject duplicate ZIP entries; broaden secret-path patterns beyond `.env*`), `private_mvp_readiness_check.py` (#92: per-county connector + provenance-class bindings), `run_bologna_pilot_scope_authority_check.ps1` (#121: check `$LASTEXITCODE`) — fix only, NO new Bologna scaffolding.
- **HCV-3**: crosswalk completeness (#128) — map `run_provenance_check.sh`, `run_security_scan.sh`, `run_backup_restore_check.ps1` into `readiness_crosswalk.yaml`; validator enforces inventory coverage so a future unmapped CI gate fails closed.
- **HCV-4**: status-derivation + config — align `qualification_status_check.py` P0 blocker set with the validator's full set (#130); reconcile `source_quality_profile.ds-002.yaml` CONDITIONAL vocab with `usage_rights.py` (#127); drop stale "active" routing entries (#86/#121).

**Hard non-goals:** NO new Bologna/authority scaffolding (hard stop), no gate/criterion PASS, no
unfreezing owner-decisions, no DB/API/report-semantics change, no file deletion (archive), no
AI/agent/model attribution. Skip the historical plan-doc findings (#129/#123) — just resolve
those threads.

**ISOLATION — a parallel lane runs concurrently:** You OWN the qualification subsystem
(`scripts/validate_qualification.py`, `selftest_*`, `qualification_status_check.py`,
`qualification_change_impact_check.py`, `config/qualification/**`, `schemas/qualification/**`),
the readiness/authority checker scripts, and ALL shared state/control files (`state/**`,
`tasks/task_queue.yaml`, `MANIFEST.md`, `plans/**`). **Do NOT touch
`backend/app/api/ui.py`, `backend/app/api/connectors.py`, `backend/app/main.py`, or any
`defer/*`/`fix/*` branch — the parallel lane owns those product files.**

**Merge discipline (learned the hard way):** confirm ALL checks green via `gh pr checks`
(not a `--watch` exit alone) immediately before merging; run the full `verify` gate incl. mypy
on py-3.12 locally before merge.

**Canonical authority:** live `origin/main` (was `9490a7d` at handoff). Reconcile to main if the
plan conflicts.

---

### Channel reference (unchanged)
- File-drop:  `./scripts/handoff_to_codex.sh "task for Codex"` then paste the printed pickup line.
- GUI inject: `./scripts/handoff_to_codex.sh --ipc <conversationId> "task"` (thread must be open in the Desktop app).
