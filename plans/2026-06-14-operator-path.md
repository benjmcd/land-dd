# Plan: Selected-County Operator Path

Status: implemented; proof-semantics docs closeout in progress
Created: 2026-06-14
Updated: 2026-06-16

## Current State

The app-owned selected-county operator path is implemented in
`backend/app/operator_cases`, `backend/app/api/operator_cases.py`, and the `/ui/`
selected-county launcher. Focused API/private-MVP tests pass for the packaged cases.
Remaining work for this plan is documentation/proof-semantics hardening and final
verification, not new source coverage or architecture.

## Problem

The selected-county private-MVP path is proven by `scripts/generate_dossier.py`
and private-MVP tests, but it is not reachable as a first-class operator API/UI
workflow. The default HTTP fixture path only exposes the generic embedded
fixtures, so a no-Docker operator cannot create the evidence-rich Buncombe,
Chatham, or Brunswick approved dossiers without leaving the app surface.

## Decision

Add a narrow private-MVP operator path for the nine selected-county fixture
cases. This is not live-source production coverage. It is a packaged,
fixture-only utility path that preserves the existing source caveats, connector
review gating semantics, report approval state, and JSON artifact serialization.

The app must not depend on `tests/fixtures/**` at runtime. Promote the selected
county case catalog and fixture files into an app-owned package, keep the test
corpus as regression input, and validate parity between the two.

## Scope

- Add app-owned selected-county case resources under `backend/app/operator_cases`.
- Add a service that lists cases and creates an approved report from one case
  using the existing fixture connectors, provenance registration, evidence
  ingestion, connector review handoff, and report approval service.
- Add API routes to list cases and generate an approved case report.
- Add UI controls on `/ui/` to choose a selected-county case and open the
  generated report.
- Update operator docs/state/validation logs after verification.

## Non-goals

- No live connector expansion.
- No DS-017 vendor decision.
- No new database schema, report semantics, source-readiness status, auth model,
  OAuth/session work, or external service dependency.
- No legal, title, survey, wetland jurisdiction, appraisal, lending, insurance,
  or investment conclusions.

## Acceptance

- API lists all nine selected-county cases.
- Unsupported case IDs fail closed.
- A generated case report is approved, exposes downloads through existing
  dossier/artifact routes, and keeps claims evidence-linked.
- UI can launch the case flow without pasting GeoJSON.
- App-owned case resources remain in parity with the golden test manifest.
- Focused API/private-MVP tests, OpenAPI parity, ruff, mypy, and default
  `.\scripts\verify.ps1` pass; DB smoke remains a separate optional gate.
