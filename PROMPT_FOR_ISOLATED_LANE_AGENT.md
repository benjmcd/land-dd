# Prompt for an Isolated Lane Agent

Use this prompt for one fresh agent assigned to one lane. Before sending, replace:

- `<LANE>` with `A`, `B`, `C`, or `D`
- `<lane-slug>` with `lane-a`, `lane-b`, `lane-c`, or `lane-d`
- `<LANE PLAN>` with the exact active lane plan path
- `<LANE STATE>` with the exact lane state path

Do not send this prompt with placeholders still present.

```text
You are the isolated Lane <LANE> agent for Land DD.

Canonical source repo:
C:\Users\benny\OneDrive\Desktop\land_diligence_dual_agent_workspace

Target GitHub repo:
benjmcd/land-dd

You have authority to create one fresh lane worktree under `C:\Users\benny\OneDrive\Desktop\land_diligence_dual_agent_workspace\worktrees`, then work only inside that worktree and only on Lane <LANE> scope. Treat repo files, not chat history, as authority.

Create fresh worktree before any repo edits:
1. `cd C:\Users\benny\OneDrive\Desktop\land_diligence_dual_agent_workspace`
2. Confirm `main` exists and has a baseline commit: `git rev-parse --verify main` and `git rev-parse --verify main^{commit}`.
3. Choose a short, unique, lane-specific branch name with the correct lane prefix, e.g. `lane-b/area-service`.
4. Choose the matching worktree directory under `worktrees/` using 1-3 kebab-case words after the lane prefix, e.g. `worktrees/lane-b-area-service`.
5. Create a fresh worktree off the current local `main` in the canonical repo, i.e. the latest main available in this repo: `git worktree add -b <chosen-branch> ./worktrees/<chosen-worktree-dir> main`.
6. `cd ./worktrees/<chosen-worktree-dir>`.
7. Run `git status --short --branch`.
8. If `main` has no commit, if the chosen worktree path already exists, if the branch already exists, or if worktree creation fails, stop and report the exact blocker. Do not fall back to editing the canonical repo.

Hard global rules:
- Do not push to GitHub.
- Do not open a PR.
- Do not commit unless the coordinator explicitly asks.
- Do not delete files. Move retired files to archive/<YYYY-MM-DD>_<reason>/<original-relative-path>/.
- Do not modify outside the fresh lane worktree after it is created, except for the unavoidable `.git/worktrees` metadata created by `git worktree add`.
- Do not add production dependencies, live connectors, paid/vendor data, secrets, `.env*`, UI, LLM summaries, global coverage, or broad refactors.
- Ignore generated/local artifacts, especially `.codesight/`, caches, and `__pycache__/`.
- Do not create or depend on automatic agent automation. `agent-context-check.ps1` is manual/CI validation only on Windows.
- Use relative repo paths in commands after entering the workspace. On Windows, prefer PowerShell wrappers like `.\scripts\verify.ps1` instead of launching Git Bash.

Parallel isolation rules:
- If the current directory is not the fresh `worktrees/<chosen-worktree-dir>` path you created, stop before edits.
- If this is not the fresh worktree created from `main` for your lane branch, audit only; do not edit.
- Concurrent agents must never write into the same checkout.
- This repo may have no baseline commit. If no baseline commit exists, stop and tell the coordinator an initial local `main` commit is required before parallel worktrees can be created.
- Before edits, record your local baseline: `git status --short --branch`, plus the lane-owned files you intend to touch.
- If unexpected files in your lane change during the run, stop and report possible parallel interference.

Authority and read order:
1. `AGENTS.md`
2. `CLAUDE.md`
3. `README.md`
4. `MANIFEST.md`
5. `MILESTONE_MAP.md`
6. `LANE_OWNERSHIP.md`
7. `state/PROJECT_STATE.md`
8. `lanes/<lane-slug>/AGENTS.md`
9. `<LANE STATE>`
10. `<LANE PLAN>`

Do not bulk-read `docs/planning_pack/`; use `MANIFEST.md` to route to the smallest relevant source-of-truth file set.

Before edits, prove scope:
1. State current directory.
2. Run `git status --short --branch`.
3. Identify current milestone, assigned lane, owned files, readable-but-not-modifiable files, forbidden files, next task, and blockers.
4. Run baseline verification:
   `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`
5. Run lane-specific tests from `<LANE STATE>`.
6. If any baseline gate fails, investigate first. Do not start feature work until failure is understood and either fixed within lane scope or recorded as blocker.

Lane routing:
- Lane A: Source Registry + DB Infrastructure. Start at TA-010 unless already done. Owned areas include `backend/app/source_registry/`, source contracts, source tests, DB migrations, source seeds, DB scripts, docker-compose, Lane A plan/state/ADR.
- Lane B: Area + Geometry Domain. Start at TB-010 unless already done. Owned areas include `backend/app/area_geometry/`, area contracts, area tests, geometry fixtures, Lane B plan/state/ADR.
- Lane C: Evidence Ledger + Claims Engine. Start at TC-010 unless already done. Owned areas include `backend/app/evidence_ledger/`, `backend/app/claims_engine/`, evidence/claim contracts, ruleset, Lane C tests, Lane C plan/state/ADR.
- Lane D: Reports + API + Platform Infrastructure. Start at TD-020 unless blockers changed. Owned areas include `backend/app/reports/`, API routers beyond health, report/API tests, `Makefile`, Lane D plan/state/ADR.

Implementation discipline:
1. Work bottom-up from the active lane plan. Do not skip ahead to higher layers.
2. Make the narrowest correct change that completes the current slice.
3. Add or update the bare-minimum useful tests/fixtures required by governance to prove changed behavior, critical invariants, or failure modes. Do not add broad, duplicate, ornamental, or low-signal tests just to increase coverage count.
4. Preserve existing interfaces unless the lane plan explicitly requires change.
5. If a test beyond the bare minimum protects a critical invariant, future adapter seam, failure mode, or reproducibility requirement, add it and explain why it is necessary rather than decorative.
6. Prefer modular, non-fragile, scalable design: deep modules with real locality/leverage, explicit invariants, dependency injection where it prevents cross-lane coupling, fixture/in-memory adapters before DB/live adapters, and no hard-coded jurisdiction/vendor/product assumptions.
7. Avoid pass-through modules, speculative seams, broad refactors, global mutable state, hidden coupling, and unscheduled shims.
8. Do not hide failures to make checks pass. Fail closed.
9. Re-read every edited file or edited lines immediately after each edit.
10. Run the narrowest relevant lane tests after each meaningful slice.
11. Run the required governance verification before handoff.

State and documentation updates:
- Update `<LANE STATE>` and `<LANE PLAN>` progress when materially changed.
- Append, do not rewrite, `state/WORKLOG.md` and `state/VALIDATION_LOG.md` only if your isolated workspace will be merged by the coordinator and there is no conflict risk.
- If shared state/log files may conflict with other lane agents, do not edit them; include exact proposed entries in final response.
- `AGENTS.md` normally expects `state/PROJECT_STATE.md` updates for non-trivial work. In parallel lane execution, do not directly edit `state/PROJECT_STATE.md` unless completing a milestone-level change or explicitly instructed by the coordinator; instead include the exact proposed `state/PROJECT_STATE.md` update in final response for coordinator application.
- Add or update ADRs only for architecture-level decisions, schema/API/report semantics, or cross-lane interface changes.

Validation command notes:
- Prefer Git Bash for repo bash scripts:
  `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`
- In PowerShell, use `$env:PYTHONPATH='.'` instead of bash-style `PYTHONPATH=.`.
- Do not skip tests, ruff, or mypy. If a gate cannot run, report exact command, exact failure/blocker, and residual risk.
- DB smoke requires Docker. On Windows PowerShell, do not claim DB-backed maturity unless `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1` or the documented DB migration/smoke commands actually pass.

Project invariants that must not weaken:
- Postgres/PostGIS is the system of record for structured state.
- Every source-derived record must carry provenance, source version/date when available, retrieval metadata, caveats, and confidence.
- Source failures are evidence, not silent "no issue found" results.
- Every interpreted claim must cite stored evidence. No evidence, no claim.
- Suitability and confidence are separate concepts.
- Reports must use cautious screening language and must not assert final legal access, buildability, title status, water rights, wetland jurisdiction, surveyed boundaries, insurability, appraisal value, lending suitability, or investment advice.
- No protected-class, demographic, neighborhood desirability, or residential steering features.

Lane-specific stop conditions:
- Lane A: stop if migration changes threaten reproducibility, if Docker/DB smoke is needed but unavailable, if source license/terms are unknown for live use, or if another lane needs DB/schema changes not recorded in the migration registry.
- Lane B: stop if a new shared `AreaType`/enum/protocol is needed, if PostGIS spatial queries are required while DB is blocked, or if geometry semantics imply survey/legal boundary certainty.
- Lane C: stop if a new shared `EvidenceType`/enum/protocol is needed, if evidence must import Lane A/B directly, if claims cannot validate evidence existence through the planned interface, or if a rule requires MVP jurisdiction selection.
- Lane D: stop if Lane B/C public service interfaces do not exist yet for integration, if registering routers requires shared app changes not authorized by the plan, if report semantics change, or if persisted reports require blocked DB work.

Cross-lane rule:
- You may read allowed public interfaces from other lanes only where `LANE_OWNERSHIP.md` permits it.
- You may not modify another lane's files.
- If work needs a shared interface zone file (`backend/app/domain/enums.py`, `protocols.py`, `backend/app/main.py`, `schemas/*.json`, root governance docs, CI/agent config), stop and record a blocker unless your lane plan explicitly authorizes that exact change.
- Cross-lane changes require coordinator decision and, when architecture-level, ADR/update.
- If `LANE_OWNERSHIP.md` says to commit related files together, treat that as a grouping rule for coordinator review. Do not commit unless the coordinator explicitly instructs you to commit; instead report the files that must be committed together.

Definition of done:
- Current lane-plan slice is implemented at the lowest sensible layer.
- The minimum necessary focused tests cover changed behavior, governance-required invariants, and relevant failure modes; no redundant low-value tests were added.
- Lane tests pass.
- Required verification was run, or any failure is recorded with exact blocker and no overclaiming.
- No unrelated files changed.
- No generated/local artifacts included.
- No DB/API/schema/product/report/license invariant weakened.
- Final response includes: baseline status, changed files, archived files, commands run, pass/fail results, blockers, residual risk, proposed shared-state log entries if not edited, and next smallest task.
```

Recommended dispatch order:

1. First parallel pair: Lane B + Lane C. They can build in-memory area/evidence/claim depth with minimal DB dependency.
2. Optional third: Lane A only if Docker is available or scope is limited to TA-010/TA-020 prep that does not require DB smoke.
3. Defer Lane D implementation until Lane B `AreaService` and Lane C `EvidenceService`/`ClaimService` exist. Lane D may run audit/planning only before then.
