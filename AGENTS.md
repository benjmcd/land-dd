# AGENTS.md

## Purpose
This is the canonical operating contract for AI coding agents working in this repository. Keep it concise. Put long procedures in `plans/`, `.agent/`, `.claude/skills/`, subagents, tests, or CI.

## Project summary
- Product: intent-aware land/locality due-diligence compiler.
- MVP: United States rural land / homestead dossier for a limited geography.
- Architecture: bottom-up, claim-first, evidence-ledger-first, Postgres/PostGIS-first.
- Backend stack: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2/Alembic-ready, pytest, ruff, mypy.
- Database: PostgreSQL 16+ with PostGIS. Postgres is the system of record.

## Non-negotiables
- Do not start with UI, LLM summaries, live vendors, global coverage, or broad refactors.
- Do not introduce production dependencies without a plan and explicit approval.
- Do not change public APIs, database schema, auth/security boundaries, or report semantics without an execution plan and ADR/update.
- Every interpreted claim must cite stored evidence. No evidence, no claim.
- Every source-derived record must carry provenance, source version/date when available, retrieval metadata, caveats, and confidence.
- Suitability and confidence are separate concepts.
- Source failures are first-class evidence, not silent “no issue found” results.
- No report may assert final legal access, buildability, title status, water rights, wetland jurisdiction, surveyed boundaries, insurability, appraisal value, lending suitability, or investment advice.
- No protected-class, demographic, neighborhood desirability, or residential steering features.
- Prefer small, reversible diffs. Do not suppress failing tests, type errors, or linter errors to make checks pass.
- Do not delete files. Archive superseded or retired code to `archive/<YYYY-MM-DD>_<reason>/` instead.
- Do not commit secrets, credentials, `.env*`, private keys, or paid-vendor data dumps.

## Context budget and read routing
Always-loaded files should stay thin. For a fresh session, read:
1. `README.md`
2. `MANIFEST.md`
3. `state/PROJECT_STATE.md`
4. the active plan referenced in `state/PROJECT_STATE.md`

Do not bulk-read `docs/planning_pack/` or all docs. Use `MANIFEST.md` to route to the smallest relevant file set. Read the planning pack only when the active plan or ambiguity requires it.

## Bottom-up build order
Build only on proven lower layers:
1. repo health and verification scripts
2. Postgres/PostGIS schema spine
3. source registry and license/provenance metadata
4. area/geometry model
5. evidence ledger
6. claim/rule engine
7. report-run reproducibility
8. API façade
9. human review/audit workflow
10. fixture connectors before live connectors
11. UI and batch workflows after the above are stable

## Planning threshold
Create or update `plans/YYYY-MM-DD-<slug>.md` when any of these are true:
- More than 3 files will likely change.
- The task affects DB schema, API contracts, security/compliance, data ingestion, scoring, report semantics, or architecture.
- The task is ambiguous, cross-cutting, a refactor, a migration, or a performance change.
- The task needs product or jurisdictional assumptions.

Follow `.agent/PLANS.md` for plan format.

## Common commands
```bash
./scripts/bootstrap.sh                 # local setup helper
./scripts/verify.sh                    # canonical verification gate
./scripts/agent-context-check.sh       # checks agent instruction bloat/invariants
cd backend && PYTHONPATH=. python -m pytest -q
```

Optional DB checks require Docker:
```bash
docker compose up -d db
./scripts/db_apply_migrations.sh
python scripts/db_smoke_check.py
```

## Work protocol
For trivial single-file fixes: make the smallest safe change, run the narrowest relevant check, then report changed files and verification result.

For non-trivial work:
1. Explore relevant files and existing tests before editing.
2. Create/update the active plan.
3. Add or update tests/fixtures before or alongside behavior changes.
4. Implement the smallest bottom-up slice.
5. Run narrow checks after each slice.
6. Run `./scripts/verify.sh` before handoff.
7. Update `state/PROJECT_STATE.md`, `state/WORKLOG.md`, and `state/VALIDATION_LOG.md`.
8. Add/update ADRs for architecture-level decisions.

## Definition of done
- Behavior is implemented at the lowest sensible layer before higher-level integrations.
- Tests or validation checks cover the changed behavior.
- Docs/plans/state are updated only where materially affected.
- `./scripts/verify.sh` passes, or failures are recorded with a specific blocker.
- Final handoff includes changed files, checks run, current risk, and next task.

## Stop-and-record conditions
Stop the current path and record a blocker when:
- a needed license/terms status is unknown or incompatible;
- the implementation requires secrets, paid APIs, external network, or destructive operations;
- a schema change threatens evidence/claim/report reproducibility;
- the task requires choosing the first MVP state/county, parcel vendor, valuation model, or legal interpretation and no decision exists;
- test results cannot be reproduced.
