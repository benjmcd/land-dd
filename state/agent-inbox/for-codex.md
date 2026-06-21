# Handoff from Claude Code -> Codex

## ACTIVE HANDOFF (2026-06-21): Empirical-Qualification Adoption + Readiness Consolidation

**Set your session goal first**, then execute the lanes. Full self-contained spec:
`plans/2026-06-21-empirical-qualification-adoption.md` (read it whole before starting).

**Session goal to set (use your goal function / `/goal`):**
> Adopt the empirical-qualification framework as the canonical empirical-validity control
> plane for land-dd, and consolidate the repo's ad-hoc readiness/authority governance under
> it — landing the self-validating spine on `origin/main`, reporting an honest
> `P0 = BLOCKED`, without attempting any qualification PASS or unfreezing any owner-decision.

**Milestone = mid-to-long-term**, decomposed into lanes (bottom-up, one PR each):
- **EQ-1** (GATE, do first): boundary/consolidation ADR `docs/adr/0004-*` + AGENTS.md/MANIFEST.md + task_queue lanes.
- **EQ-2**: land self-validating spine (vocabulary + catalog + profiles + schemas + validator + selftest), CI gate `qualification-selftest`, `verify` wiring. **Env reality: `jsonschema` is importable on `py -3.11` but NOT on local `py -3.12`; CI installs `backend[dev]`. Wire so this cannot false-fail (honor `PYTHON_BIN`; add `jsonschema` to `backend[dev]`).**
- **EQ-3**: honest `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` at `P0 = BLOCKED`; collapse 8 domain stubs → 1 template; one real source-quality profile mapped to `usage_rights.py`.
- **EQ-4**: consolidation crosswalk (existing readiness/authority checks → criterion IDs); change-impact-matrix validated against the catalog.
- **EQ-5**: parameterization-backlog tracking doc (owner-decision blockers; 0 sources approved).
- **Lane R** (parallel, independent): correct the FALSE `STILL_DIVERGENT: none` claim in `state/residual-reconciliation.md` (~11 stranded DEFER'd files decaying 71 commits behind main — list + grounds in the plan).

**Hard non-goals:** no Q3A/B/C, no AI/CG/FIN/E rubrics/targets, no gate PASS, no unfreezing
owner-decisions, no DB/API/auth/report-semantics changes, no file deletion (archive
instead), no AI/agent/model attribution in files/commits/branches.

**Source package (READ-ONLY input):** `C:\Users\benny\Downloads\land-dd_empirical_qualification`

**Canonical authority:** live `origin/main` (was `cc54776` at handoff). If anything in the
plan conflicts with live `origin/main`, reconcile against main first.

**Provenance of this handoff:** authored from two read-only audits (dirty-root reconciliation
+ framework assessment). Verified findings are embedded in the plan's "Background & grounding"
section — treat them as evidence, not assumptions.

---

### Channel reference (unchanged)
- File-drop:  `./scripts/handoff_to_codex.sh "task for Codex"` then paste the printed pickup line.
- GUI inject: `./scripts/handoff_to_codex.sh --ipc <conversationId> "task"` (thread must be open in the Desktop app).
- Every real handoff embeds a pointer to the originating session context; this one's grounds live in the plan file's "Background & grounding" section.
