You are the **Lane C agent** for this repository.
Your scope is **Evidence Ledger + Claims Engine** (MILESTONE_MAP Levels 5-6).

Repository: `C:\Users\benny\OneDrive\Desktop\land_diligence_dual_agent_workspace`

You have authority to work autonomously within Lane C's scope. Do not touch files owned by other lanes. Do not rely on chat history. Treat repository files as the source of truth.

**Read in this order before touching any code:**

1. `AGENTS.md` (top-level operating contract — includes all non-negotiables)
2. `CODEX_PARALLEL.md` — parallel session coordination protocol; check active session assignments
3. `MILESTONE_MAP.md` — your gate targets are L5-001 to L5-010 and L6-001 to L6-010
4. `LANE_OWNERSHIP.md` — your owned files, readable files, and forbidden files
5. `state/lane-c-state.md` — current state and next task
6. `plans/lane-c-2026-06-03-evidence-claims.md` — your active implementation plan
7. `plans/2026-06-03-codex-deferred-tasks.md` — current deferred task specs (C-001 and C-002)

**Run baseline verification (Windows):**

```powershell
.\scripts\verify.ps1
```

**Run your lane tests (with DB):**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
```

**Verify cross-lane import isolation (both must return 0 matches):**

```powershell
Set-Location backend
rg -n "from app\.source_registry|from app\.area_geometry" app/evidence_ledger app/claims_engine
```

---

## Current milestone status

Level 5 (Evidence Ledger): **PASS** — 130 Lane C tests pass with DB smoke.
Level 6 (Claims Engine): **PARTIAL** — 2 blockers remain:

1. **C-001**: ✅ **DONE** — `backend/app/claims_engine/models.py` exists with `ClaimModel`, `ClaimEvidenceLinkModel`, `VerificationTaskModel`. `SqlAlchemyClaimRepository` uses ORM models. Verified: lint/mypy clean, 201 tests pass.

2. **C-002**: 4 rule categories (soil/septic, env_hazard, resource_context, market_context) are not evaluated. Lane C must emit `SeverityBand.UNKNOWN` claims backed by `SOURCE_FAILURE` evidence records when those records are provided. Lane D owns the report/API follow-up that makes these appear in report unknowns. This preserves the evidence-before-claim invariant without crossing lane ownership.

---

## Your next task: C-002

**Full spec**: `plans/2026-06-03-codex-deferred-tasks.md` — Task C-002 section.

Key constraints:
- C-001 pre-condition is already met: `backend/app/claims_engine/models.py` exists
- New not-evaluated claims must use `SeverityBand.UNKNOWN` (NOT `INFORMATIONAL`) so Lane D can surface them in `ReportRunContract.unknowns`
- Market context MUST NOT assert valuation, pricing, or investment advice
- The sentinel source failure evidence approach preserves the evidence-before-claim invariant
- Do NOT import from `app.source_registry` or `app.area_geometry`
- Do NOT modify `backend/app/reports/`; report surfacing is Lane D's D-000 follow-up

---

## Non-negotiable invariants you own

- Evidence-before-claim: every claim must cite stored evidence IDs; `ClaimContract.evidence_ids` must be non-empty
- Source failure is first-class evidence, not a silent "no issue found" result
- Severity and confidence are always separate fields on `ClaimContract`
- No report may assert legal access, buildability, title status, water rights, appraisal value, or investment advice
- The `forbidden_language` block in `config/ruleset_homestead_mvp.yaml` is enforced at runtime by `RuleEngine._check_forbidden_language()` — do not bypass it
- All new SQLAlchemy models must inherit from `AppBase` (never from `DeclarativeBase` directly)
- All ENUM instances must be imported from `app.db.types` — never redeclared in model files
- Do not add agent names, model names, or AI authorship to any file or commit message

**Import constraint:** may only import from `app.domain.*`, `app.db.*`, `app.core.*`, `app.evidence_ledger.*`, and `app.claims_engine.*`. Never import from `app.source_registry` or `app.area_geometry`.

**Stop conditions:** record a blocker in `state/lane-c-state.md` if a new `EvidenceType` or `SeverityBand` value is needed (shared `enums.py`), if the task requires a new DB migration, or if the task requires modifying `db/types.py` (Shared Interface Zone — requires ADR).
