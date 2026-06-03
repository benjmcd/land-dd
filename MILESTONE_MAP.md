# MILESTONE_MAP.md

## Purpose

This file is the canonical maturity map for the land-diligence repository. It defines **ten auditable milestones** from initial governed scaffold to production-grade operation.

Use it to determine:

```text
1. What maturity level is the repo currently at?
2. What is the next lowest-dependency work?
3. What exactly must pass before a milestone is complete?
4. What evidence proves completion?
5. What is still partial, blocked, unsafe, or premature?
```

The repo's maturity is the **highest numbered milestone whose pass/fail gates all pass from a fresh checkout or clean deployment**.

No milestone is complete because it "mostly works." It is complete only when its gates pass and the required evidence exists in the repo or controlled runtime.

---

## Non-certainty statement

This milestone map is intended to be exhaustive for the **core platform maturity path**: governed repo → Postgres/PostGIS foundation → provenance → geometry → evidence → claims → reports → connectors → MVP workflow → production operation.

It is not a substitute for future jurisdiction-specific legal review, data-license review, security audit, infrastructure review, or production incident learnings. Those are represented as required gates. If a gate depends on an external decision or professional review, the repo must mark it as **blocked**, not silently assume it is done.

---

## External reference frameworks considered

This map intentionally aligns with common production-readiness patterns from:

- NIST SSDF / SP 800-218 for secure software development practice.
- OWASP ASVS for application security verification.
- SLSA for software supply-chain integrity.
- Twelve-Factor App principles for deployable service configuration and operational behavior.

These references inform the pass/fail gates for security, supply chain, configuration, testing, deployment, and operations. They do not override the project-specific data/evidence/claim requirements below.

---

## Definitions

### Milestone status values

Every milestone must be classified using exactly one of these statuses:

| Status | Meaning |
|---|---|
| `NOT_STARTED` | The repo has no meaningful implementation for this milestone. |
| `PARTIAL` | Some artifacts exist, but at least one required gate fails or has not been checked. |
| `BLOCKED` | Work cannot be completed because a required external decision, credential, license, infrastructure dependency, or product decision is missing. |
| `PASS` | Every required gate passes and completion evidence is recorded. |
| `INVALIDATED` | The repo previously claimed this milestone, but a regression, architecture change, failed check, or missing evidence invalidated that claim. |

### Gate result values

Every gate in this file is binary unless explicitly marked optional.

| Gate result | Meaning |
|---|---|
| `PASS` | The gate is satisfied and evidence exists. |
| `FAIL` | The gate is not satisfied. |
| `N/A` | The gate is demonstrably not applicable to the current scoped product. Must include rationale. |
| `BLOCKED` | The gate is required but cannot be evaluated yet. Must name the blocker. |

### Completion evidence

A gate is not passed by assertion. It needs evidence.

Valid evidence includes:

```text
- passing test output;
- CI run link or local command output copied into state/VALIDATION_LOG.md;
- migration file;
- schema snapshot;
- ADR;
- source registry row;
- seed fixture;
- API contract;
- generated report artifact;
- security scan output;
- backup/restore transcript;
- documented reviewer sign-off;
- production runbook;
- deployment smoke test result.
```

Invalid evidence includes:

```text
- chat history;
- "the agent said it works";
- uncommitted local state;
- manual DB edits not represented by migrations/seeds;
- one-off scripts outside repo governance;
- screenshots without reproducible command or artifact;
- tests skipped without a documented reason.
```

---

## How to assess maturity

Use this algorithm:

```text
1. Start at Level 1.
2. Evaluate every gate in that level.
3. If all required gates pass, move to the next level.
4. Stop at the first required gate that fails, is blocked, or lacks evidence.
5. The repo's current maturity is the previous fully passed level.
6. If Level 1 fails, the repo is below tracked maturity.
```

Higher-level code does not raise the maturity level if lower-level gates are incomplete.

Example:

```text
A UI exists, but evidence records are not source-linked.
Current maturity: at most Level 4.
Reason: Level 5 evidence gates fail.
```

---

## Current-state reporting format

`state/PROJECT_STATE.md` must include this block:

```text
Current milestone: Level N — <name>
Milestone status: NOT_STARTED | PARTIAL | BLOCKED | PASS | INVALIDATED
Last verified: YYYY-MM-DD
Verification command(s):
- <command>
Verification result:
- <pass/fail/blocked summary>
Failed or blocked gates:
- <gate id>: <reason>
Completion evidence:
- <file or command output reference>
Next lowest-dependency task:
- <task>
Do not work on yet:
- <premature layer or feature>
```

---

## Global invariants

These are always required. A violation of any global invariant can invalidate any milestone.

### G-I. System-of-record invariants

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| G-I-001 | Postgres/PostGIS is the canonical transactional system of record. | Core state is stored only in flat files, local memory, spreadsheets, or ad hoc JSON. |
| G-I-002 | Large raw assets may live in object storage, but Postgres stores durable references, metadata, source identity, and run state. | Artifacts exist without durable database metadata or provenance. |
| G-I-003 | Schema changes use migrations. | Tables or columns are created manually or only through app startup side effects. |
| G-I-004 | State needed for reproducibility is persisted. | Reproducing a report requires chat history, local scratch files, or manual recall. |
| G-I-005 | Every mutable production record has update/audit semantics appropriate to its risk. | Sensitive or decision-impacting records can be overwritten silently. |

### G-II. Evidence and claim invariants

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| G-II-001 | No claim exists without at least one linked evidence item or explicit source-failure/unknown evidence. | Claims can be generated from direct connector output, prompts, UI text, or unstored calculation. |
| G-II-002 | Evidence has source/provenance/caveat/confidence metadata. | Evidence rows contain observations without origin, freshness, or caveat. |
| G-II-003 | Missing or failed sources create explicit unknown/blocker evidence. | Missing data is treated as "no issue found." |
| G-II-004 | Suitability and confidence are modeled separately. | A single score collapses risk and certainty into one opaque value. |
| G-II-005 | Claims distinguish direct observation, derived metric, inference, and human verification. | User-facing outputs blur official source data, model inference, and analyst notes. |
| G-II-006 | Rule/model/source versions are persisted for report runs. | Reports cannot explain why the same area produced a different result later. |

### G-III. Safety and liability invariants

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| G-III-001 | Reports use screening language and verification tasks for legal/professional matters. | Reports assert final legal, title, survey, zoning, wetland, septic, appraisal, lending, insurance, or investment determinations. |
| G-III-002 | Residential features avoid protected-class or demographic steering. | Product ranks/recommends residential areas using protected classes or proxies. |
| G-III-003 | Valuation outputs, if any, are scoped and compliance-reviewed before production. | The system produces appraisal-like, lending, or collateral-value outputs without review. |
| G-III-004 | Every user-facing risk conclusion carries caveats and source appendix. | Outputs omit source limitations. |
| G-III-005 | Human review can add verification notes without overwriting source evidence. | Manual review mutates or erases provenance. |

### G-IV. Engineering invariants

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| G-IV-001 | Build order is bottom-up. | UI, LLM summaries, or live connectors precede the storage/evidence/claim foundation. |
| G-IV-002 | Fixture-backed behavior is proven before live data. | Tests depend on live external APIs by default. |
| G-IV-003 | Verification commands are executable and documented. | "Manual testing" is the only validation method. |
| G-IV-004 | Changes are small, reversible, and aligned to active plans. | Large cross-cutting edits happen without plan, tests, or ADR. |
| G-IV-005 | Critical failures fail closed. | Errors are swallowed to keep the workflow appearing successful. |
| G-IV-006 | New dependencies require justification. | Dependencies are added casually without license/security/maintenance review. |

### G-V. Data governance invariants

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| G-V-001 | Every production source has license/terms status. | Unknown license data is used in production reports. |
| G-V-002 | Redistribution/export rights are tracked. | Reports or APIs expose data beyond allowed license terms. |
| G-V-003 | Source freshness and jurisdictional coverage are visible. | Outputs imply current/national/global coverage when sources are stale or local. |
| G-V-004 | Adding a new jurisdiction requires a jurisdiction readiness checklist. | New regions are treated as simple data additions with no legal/data caveats. |
| G-V-005 | Paid/vendor data is isolated behind entitlements. | All users can access all licensed data regardless of rights. |

---

# Ten-level milestone map

## Level 1 — Governed Repo Scaffold

### Objective

A fresh Codex, Claude Code, or human developer can enter the repo cold, understand the project, run verification, identify the active plan, and continue without relying on chat history.

### Required capabilities

- Canonical agent operating contract exists.
- Human-facing README exists.
- Repo/file routing map exists.
- Plans and state files exist.
- Verification scripts exist.
- Context-bloat guard exists.
- Active plan is discoverable.
- Bottom-up implementation order is explicit.
- No duplicated contradictory instruction layers.

### Required artifacts

```text
AGENTS.md
CLAUDE.md
README.md
MANIFEST.md
.agent/PLANS.md
plans/
state/PROJECT_STATE.md
state/WORKLOG.md
state/VALIDATION_LOG.md
scripts/verify.sh
scripts/agent-context-check.sh
.github/workflows/ci.yml or documented CI placeholder
```

### Pass/fail gates

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L1-001 | `AGENTS.md` is concise, canonical, and names non-negotiables. | Agent instructions are missing, bloated, duplicated, or contradictory. |
| L1-002 | `CLAUDE.md` imports/adapts `AGENTS.md` without duplicating core rules. | Claude and Codex receive divergent core instructions. |
| L1-003 | `README.md` explains purpose, setup, verification, and docs. | A new developer cannot run the project from README. |
| L1-004 | `MANIFEST.md` routes agents to relevant files and identifies protected/generated areas. | Agents must bulk-read the repo to know what matters. |
| L1-005 | `.agent/PLANS.md` defines how to write resumable implementation plans. | Large tasks rely on chat history or vague TODOs. |
| L1-006 | `state/PROJECT_STATE.md` states current milestone, active plan, last verification, blockers, and next task. | Project state is unknown or stored only in chat. |
| L1-007 | `scripts/verify.sh` exists, is executable, and returns clear pass/fail/skip output. | Verification is prose-only or fails opaquely. |
| L1-008 | `scripts/agent-context-check.sh` detects instruction bloat or required-file absence. | No guard exists against context bloat or missing control files. |
| L1-009 | CI exists or a documented CI placeholder identifies the intended verification command. | There is no path from local verification to CI. |
| L1-010 | The active plan identifies the next bottom-up task. | Agents can start anywhere and drift into premature UI/data work. |

### Required validation

```bash
./scripts/agent-context-check.sh
./scripts/verify.sh
```

### Completion evidence

- Command output recorded in `state/VALIDATION_LOG.md`.
- `state/PROJECT_STATE.md` updated with `Current milestone: Level 1`.
- Active plan exists and is referenced.

### Not complete if

- The repo contains many broad generated context files.
- The agent needs prior conversation to understand intent.
- Verification cannot run from the repo.
- There is no explicit "do not work on yet" list.

---

## Level 2 — Postgres/PostGIS Storage Spine

### Objective

The canonical storage foundation exists and is reproducible from a fresh local environment.

### Required capabilities

- Local Postgres/PostGIS environment.
- Migration system.
- Database reset/seed.
- DB smoke test.
- Typed or clearly bounded persistence access.
- Core tables for source, area, evidence, claim, report, and audit concepts.
- Schema documentation or ADR.

### Required artifacts

```text
docker-compose.yml or equivalent local DB setup
db/migrations/
db/seeds/
backend DB access module
scripts/db_reset.* or documented equivalent
scripts/db_smoke.* or equivalent test
docs/adr/<storage-decision>.md
```

### Minimum schema coverage

```text
jurisdictions
sources
source_versions
source_licenses or source_terms
retrieval_runs
areas
area_geometries
evidence_items
claims
claim_evidence_links
report_runs
report_artifacts
audit_events
```

If any table is intentionally deferred, the ADR must explain why and what placeholder contract exists.

### Pass/fail gates

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L2-001 | Local Postgres/PostGIS can be started from repo instructions. | DB requires undocumented manual setup. |
| L2-002 | PostGIS extension is enabled and verified by test. | Geometry features are emulated without PostGIS. |
| L2-003 | Migrations apply cleanly from an empty database. | Schema is manually created or depends on hidden state. |
| L2-004 | DB can be reset and reseeded deterministically. | Local state cannot be recreated. |
| L2-005 | Core tables for source/area/evidence/claim/report/audit exist or have documented deferred contracts. | Higher-level code has no durable storage target. |
| L2-006 | Geometry columns use explicit SRID and spatial indexes where needed. | Geometry storage is raw JSON only with no spatial query ability. |
| L2-007 | Application DB access goes through a bounded persistence layer. | Arbitrary modules open ad hoc DB connections and write directly. |
| L2-008 | Migration tests or smoke tests run in local verification. | Migrations are never tested from zero. |
| L2-009 | Schema changes require migration files and review. | App startup silently mutates schema. |
| L2-010 | DB failure modes are explicit in tests or error handling. | Connection/migration failures are swallowed. |

### Required validation

```bash
./scripts/verify.sh
RUN_DB_SMOKE=1 ./scripts/verify.sh
```

or documented equivalent.

### Completion evidence

- Passing DB smoke test.
- Migration files committed.
- Seed data committed.
- Storage ADR committed.
- Validation log updated.

### Not complete if

- Tests use only in-memory storage for PostGIS-dependent behavior.
- Report/evidence/claim code exists without persistent tables.
- DB can only be made to work through manual commands not in the repo.

---

## Level 3 — Source Registry + Provenance Core

### Objective

The system can represent data sources, licenses, source versions, retrievals, caveats, freshness, and authority before ingesting meaningful data.

### Required capabilities

- Source registry CRUD or seed mechanism.
- Source versioning.
- License/terms status.
- Retrieval-run lifecycle.
- Caveat storage.
- Source freshness and authority level.
- Source usage constraints.
- Provenance validation.

### Required artifacts

```text
source registry seed file
source/provenance domain model
source/retrieval tests
license review template
data source registry doc or table export
ADR for source/provenance model
```

### Minimum source metadata

```text
source_id
name
source_type
jurisdiction
authority_level
license_status
commercial_use_status
redistribution_status
ai_use_status
attribution_required
update_cadence
source_url_or_reference
caveat
freshness_class
last_checked_at
owner/reviewer
```

### Pass/fail gates

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L3-001 | Source records include required metadata fields. | Sources are just names/URLs. |
| L3-002 | License/terms status is explicit, including unknown/blocking statuses. | Unknown terms are treated as allowed. |
| L3-003 | Source versions can be recorded and linked to retrieval runs. | Data version/freshness is unrecoverable. |
| L3-004 | Retrieval runs have status lifecycle: pending/running/succeeded/failed/blocked/skipped. | Failed retrievals disappear. |
| L3-005 | Source caveats are stored in machine-readable and reportable form. | Caveats live only in docs or code comments. |
| L3-006 | Evidence cannot be created from an unknown/unregistered source except controlled human note types. | Connector output can bypass registry. |
| L3-007 | Production use is blocked for sources with incompatible or unknown license status. | License-blocked data can reach user outputs. |
| L3-008 | Source freshness is visible to downstream claims/reports. | Stale data is indistinguishable from current data. |
| L3-009 | Tests cover allowed, unknown, stale, failed, and license-blocked sources. | Only happy-path source metadata is tested. |
| L3-010 | Source metadata can be exported/reviewed by humans. | Governance state is buried in DB with no review workflow. |

### Required validation

```bash
./scripts/verify.sh
pytest tests/source* tests/provenance*  # or equivalent
```

### Completion evidence

- Seeded MVP source records.
- Passing source/provenance tests.
- License review template exists.
- Validation log updated.

### Not complete if

- Public datasets are assumed safe without license review status.
- Caveats cannot propagate to evidence/claims.
- Data freshness cannot be represented.
- Source failure is not modeled.

---

## Level 4 — Area + Geometry Domain

### Objective

The system can represent, validate, normalize, store, and query areas of interest.

### Required capabilities

- Area creation.
- Geometry persistence in PostGIS.
- GeoJSON input validation.
- SRID normalization.
- Geometry validity checks.
- Spatial indexes.
- Area/bounds/centroid metrics.
- Area type classification.
- Geometry source/confidence/caveat.
- Basic spatial predicates.

### Required artifacts

```text
area domain model
geometry validation service
area repository
GeoJSON contract/schema
area/geometry tests
sample fixture geometries
ADR or architecture section for geometry rules
```

### Supported area types

Minimum:

```text
parcel_like
drawn_polygon
multi_polygon
locality
buffer
generated_candidate
```

Future-compatible:

```text
watershed
corridor
assemblage
administrative_boundary
```

### Pass/fail gates

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L4-001 | Valid GeoJSON polygon/multipolygon can create area geometry. | Geometry input is undefined or ad hoc. |
| L4-002 | Invalid geometry handling is deterministic: reject or explicitly repair with audit. | Invalid geometry passes silently. |
| L4-003 | All stored geometries have explicit SRID. | CRS assumptions are implicit. |
| L4-004 | Area, bounds, and centroid can be computed reproducibly. | Derived metrics differ unpredictably. |
| L4-005 | Spatial intersection/contains/distance can be queried through PostGIS. | Spatial logic is only application-side approximation. |
| L4-006 | Geometry source and confidence are stored. | Parcel/drawn/locality boundaries are treated as equally authoritative. |
| L4-007 | Parcel-like geometry is caveated as non-survey unless verified. | The system implies surveyed legal boundaries. |
| L4-008 | Tests cover polygon, multipolygon, invalid geometry, empty geometry, wrong SRID, and large geometry. | Only one happy-path polygon is tested. |
| L4-009 | Geometry simplification, if used, does not overwrite canonical geometry. | Canonical geometry is degraded for display performance. |
| L4-010 | Area records can support future multi-geometry versions. | Geometry update destroys old boundary state with no history. |

### Required validation

```bash
./scripts/verify.sh
pytest tests/area* tests/geometry*  # or equivalent
```

### Completion evidence

- Fixture geometries committed.
- Passing geometry tests.
- Area/geometry service documented.
- Validation log updated.

### Not complete if

- Geometry is only accepted through UI.
- CRS/SRID is unspecified.
- Boundaries are treated as legal survey output.
- Spatial queries are not backed by PostGIS.

---

## Level 5 — Evidence Ledger

### Objective

The system can durably store evidence items, source failures, derived metrics, document extracts, and human verification notes in a way that downstream claims can cite.

### Required capabilities

- Evidence creation.
- Evidence type validation.
- Evidence-source linkage.
- Evidence-area linkage.
- Evidence-geometry linkage where applicable.
- Source failure evidence.
- Confidence/caveat propagation.
- Temporal validity.
- Spatial precision.
- Audit trail.
- Controlled amendment/supersession.

### Required artifacts

```text
evidence domain model
evidence repository/service
evidence payload schemas
evidence tests
source failure fixtures
human verification note model
audit event tests
ADR or architecture section for evidence immutability/amendment
```

### Minimum evidence types

```text
source_observation
spatial_intersection
derived_metric
document_extract
source_failure
human_verification
manual_note
```

### Pass/fail gates

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L5-001 | Evidence cannot be stored without required provenance. | Evidence exists as untracked free text or raw connector payload only. |
| L5-002 | Evidence payload schema is validated by evidence type. | Any arbitrary JSON can be stored without validation. |
| L5-003 | Source failure is stored as evidence. | Failed/missing data is invisible downstream. |
| L5-004 | Evidence is linked to area and geometry where applicable. | Evidence cannot be spatially attributed. |
| L5-005 | Evidence has confidence, caveat, method, temporal validity, and spatial precision fields. | Evidence lacks interpretive limits. |
| L5-006 | Evidence can be superseded or amended without silent overwrite. | Evidence can be changed with no audit. |
| L5-007 | Human verification notes are typed separately from source-derived evidence. | Analyst notes are mixed with official source observations. |
| L5-008 | Evidence retrieval by area/source/type works. | Claims cannot query evidence deterministically. |
| L5-009 | Tests cover source observation, source failure, derived metric, human note, invalid payload, and supersession. | Only happy-path observations are tested. |
| L5-010 | Evidence creation emits audit events. | Evidence changes are not auditable. |

### Required validation

```bash
./scripts/verify.sh
pytest tests/evidence* tests/audit*  # or equivalent
```

### Completion evidence

- Evidence fixtures committed.
- Source failure fixture committed.
- Passing evidence/audit tests.
- Validation log updated.

### Not complete if

- Claims are generated directly from connector outputs.
- Missing data creates no record.
- Human review overwrites source data.
- Evidence has no caveats.

---

## Level 6 — Claim + Rules Engine

### Objective

The system can deterministically convert evidence into evidence-linked claims, red flags, unknowns, confidence/severity classifications, and verification tasks.

### Required capabilities

- Claim model.
- Claim-evidence links.
- Rule definitions.
- Rule versioning.
- Intent-specific rule selection.
- Severity.
- Confidence.
- Unknown/blocker claim generation.
- Contradiction handling.
- Verification-task output.

### Required artifacts

```text
ruleset file or rules module
claim domain model
claim generation service
claim-evidence link tests
rule fixture cases
verification task templates
ADR or architecture section for rules/scoring
```

### Minimum rule categories

```text
access_screen
flood_screen
wetland_screen
soil_septic_screen
slope_buildability_screen
water_context_screen
zoning_screen
environmental_hazard_screen
market_context_screen
resource_context_screen
unknown_or_unverified
```

A category may be marked deferred for the first vertical slice only if the report clearly labels it as not evaluated.

### Pass/fail gates

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L6-001 | No claim can be created without evidence links. | Claims can be free-standing conclusions. |
| L6-002 | Rules are versioned and reportable. | Rule changes cannot be traced. |
| L6-003 | Rule output is deterministic for fixed inputs. | Same evidence produces inconsistent claims without version explanation. |
| L6-004 | Missing/failed source evidence produces unknown/blocker claims. | Unknowns are omitted or treated as safe. |
| L6-005 | Source/evidence caveats propagate into claims. | Claims omit source limitations. |
| L6-006 | Severity and confidence are separate fields. | Risk and certainty are collapsed into one score. |
| L6-007 | Claims include verification tasks where professional/local confirmation is required. | Reports identify risks but not what to verify. |
| L6-008 | Contradictory evidence creates conflict/needs-review claims. | Conflicts are silently resolved without explanation. |
| L6-009 | Tests cover positive, negative, unknown, stale, source-failure, and contradiction cases. | Only happy-path rules are tested. |
| L6-010 | Rule definitions are not embedded only in LLM prompts or UI copy. | Business logic cannot be tested outside generation/UI. |

### Required validation

```bash
./scripts/verify.sh
pytest tests/claim* tests/rules*  # or equivalent
```

### Completion evidence

- Rule fixtures committed.
- Passing claim/rules tests.
- Rule version included in generated claims/report runs.
- Validation log updated.

### Not complete if

- There is a score but no evidence trail.
- Claim text is created by prompt with no deterministic rule record.
- Missing data suppresses claims.
- Conflicts are invisible.

---

## Level 7 — Reproducible Report Vertical Slice

### Objective

The repo can generate a complete fixture-backed diligence report run from area input through source metadata, evidence, claims, unknowns, verification tasks, and API/service output.

### Required capabilities

- Report-run creation.
- Report-run status lifecycle.
- Report-run reproducibility metadata.
- Source/evidence/claim snapshot references.
- Intent selection.
- Machine-readable report output.
- Human-readable summary.
- API or service facade.
- Report artifact metadata.
- Repeatable fixture demo.

### Required artifacts

```text
report run model
report generation service
report API endpoints or service methods
report JSON schema
fixture report input/output
report regression tests
API contract tests
sample generated report artifact
```

### Minimum vertical slice

Input:

```text
area geometry fixture
source registry fixtures
evidence fixtures
intent = rural_land_purchase or homestead_screen
```

Output:

```text
report_run_id
area summary
source summary
evidence summary
claims
red flags
unknowns
verification tasks
source/caveat appendix
report artifact metadata
machine-readable JSON
```

### Pass/fail gates

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L7-001 | Report run is persisted with status lifecycle. | Report is generated as ephemeral output only. |
| L7-002 | Report run stores source/evidence/rule/model versions or snapshot references. | Report cannot be reproduced or explained later. |
| L7-003 | API/service can create and retrieve area and report run. | Report workflow requires manual DB edits. |
| L7-004 | Report output includes evidence-linked claims. | Report contains unsupported assertions. |
| L7-005 | Report output includes unknowns/source failures. | Missing source data disappears. |
| L7-006 | Report output includes caveats and verification tasks. | User sees conclusions without limits or next actions. |
| L7-007 | Re-running the same fixture produces same output or documented version differences. | Regression output drifts unexpectedly. |
| L7-008 | API contract is tested. | Endpoint behavior is undocumented or untested. |
| L7-009 | Report artifact metadata is stored even if artifact generation is minimal. | Generated files are not tied to report runs. |
| L7-010 | Vertical slice does not require live external APIs. | Local test/demo is flaky due to network/source dependency. |

### Required validation

```bash
./scripts/verify.sh
pytest tests/report* tests/api*  # or equivalent
```

### Completion evidence

- Sample report artifact.
- Report JSON fixture.
- Passing report/API tests.
- Validation log updated.
- Project state updated to Level 7 candidate or pass.

### Not complete if

- Output depends on live data.
- Reports are not persisted.
- Claims lose evidence links in export/API.
- Report status cannot represent failure/blocked states.

---

## Level 8 — Connector + Operational Hardening

### Objective

The system can safely ingest real or near-real public data through controlled connectors while preserving provenance, idempotency, observability, and failure handling.

### Required capabilities

- Connector interface.
- Connector run lifecycle.
- Idempotent ingestion.
- Retry/timeout/rate-limit policy.
- Failure taxonomy.
- Data-quality gates.
- Source-version creation.
- Normalized evidence output.
- Connector fixtures.
- Observability logs/metrics.
- Connector test strategy that does not make local tests flaky.

### Required artifacts

```text
connector interface
connector run model
fixture connector
static file connector
at least one approved public-source connector or near-real local extract connector
connector contract tests
data quality checks
observability/logging module
connector runbook
license review record for each production connector
```

### Recommended connector progression

```text
fixture connector
  -> static local file connector
  -> public bulk dataset connector
  -> public API connector
  -> paid/vendor connector only after license review and entitlement model
```

### Pass/fail gates

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L8-001 | All connectors use a shared interface and source registry. | Each connector writes custom ad hoc records. |
| L8-002 | Connector runs are persisted with status, timing, source version, and error metadata. | Connector execution is not auditable. |
| L8-003 | Ingestion is idempotent. | Retries duplicate records. |
| L8-004 | Failures become source_failure evidence or blocked retrieval records. | Failures are swallowed. |
| L8-005 | Rate limits, timeouts, and retry policies are explicit. | Connectors can hang or overload external services. |
| L8-006 | Data quality gates reject malformed or unsafe records. | Bad data reaches evidence/claims. |
| L8-007 | Connector output enters evidence ledger before claims. | Connectors directly produce user claims. |
| L8-008 | Normal local verification does not require live network. | Tests are flaky or dependent on external uptime. |
| L8-009 | Production connector use is blocked if license/terms are unresolved. | License-unknown data enters reports. |
| L8-010 | Logs/metrics are sufficient to diagnose connector failures. | Operators cannot see why ingestion failed. |

### Required validation

```bash
./scripts/verify.sh
pytest tests/connectors* tests/data_quality*  # or equivalent
```

Optional live connector tests must be opt-in:

```bash
RUN_LIVE_CONNECTOR_TESTS=1 ./scripts/verify.sh
```

### Completion evidence

- Passing connector contract tests.
- Connector run logs/fixtures.
- License review records.
- Data-quality report.
- Validation log updated.

### Not complete if

- Connectors bypass evidence.
- Live network tests are mandatory for normal development.
- Source failures disappear.
- Ingestion cannot be rerun safely.

---

## Level 9 — Product-Grade MVP Workflow

### Objective

A user or operator can complete the initial U.S. rural land / homestead due-diligence workflow reliably without developer intervention.

### Required capabilities

- Area creation/select flow.
- Intent selection.
- Report-run initiation.
- Report status tracking.
- Evidence explorer.
- Claim/red-flag/unknowns view.
- Verification-task checklist.
- Source/caveat appendix.
- Report export.
- Human review/annotation.
- Candidate comparison.
- Rerun/update behavior.
- Basic user/operator roles if needed.
- Clear MVP geography/source limitations.

### Required artifacts

```text
MVP workflow documentation
API/UI workflow tests
report export template
sample MVP reports
human review workflow
operator runbook
MVP scope/coverage statement
MVP release checklist
```

UI may be minimal. The workflow may be operator-facing. It must still be coherent and testable.

### Pass/fail gates

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L9-001 | A non-developer operator can complete the MVP workflow from documented steps. | Workflow requires manual DB edits or developer-only scripts. |
| L9-002 | User can create/select area and choose intent. | Inputs are hard-coded fixtures only. |
| L9-003 | User can start and monitor report run status. | Report execution is invisible or one-shot. |
| L9-004 | User can inspect evidence behind each claim. | Claims are not explainable in product surface. |
| L9-005 | User can see red flags, unknowns, blockers, and verification tasks. | Product only shows favorable or simplified summary. |
| L9-006 | Exported report preserves source/caveat/evidence appendix. | Export loses the evidence trail. |
| L9-007 | Human review can annotate or verify without overwriting source evidence. | Review destroys provenance. |
| L9-008 | At least two candidate areas can be compared on claims/unknowns/evidence. | Product is single-report only with no comparison capability. |
| L9-009 | Scope/coverage limitations are visible to user/operator. | Product implies broader coverage or certainty than supported. |
| L9-010 | MVP workflow has regression tests and release checklist. | Product workflow is validated only manually. |
| L9-011 | Failure paths are user-visible and recoverable. | Failed report leaves user with no explanation or next action. |
| L9-012 | Basic auth/role/permission model exists if multiple users/operators access data. | Sensitive report/data access is uncontrolled. |

### Required validation

```bash
./scripts/verify.sh
./scripts/run_mvp_regression.sh  # or equivalent
```

If UI exists:

```bash
./scripts/run_ui_tests.sh  # or equivalent
```

### Completion evidence

- MVP demo transcript.
- Sample exported reports.
- Passing MVP regression tests.
- Operator runbook.
- Release checklist.
- Validation log updated.

### Not complete if

- Only developers can use it.
- User-facing outputs overclaim certainty.
- Exports are not source-linked.
- Manual review mutates evidence.
- The product expands geography/intents before the first workflow is stable.

---

## Level 10 — Production-Grade End-to-End System

### Objective

The system is production-ready for the approved MVP scope: secure, deployable, scalable, observable, recoverable, compliance-aware, modular, and end-to-end testable.

This does **not** mean purchase-grade legal coverage worldwide. It means the core system and approved production coverage area are operationally production-grade, and new jurisdictions/sources/intents can be added through controlled adapters and readiness gates.

### Required capabilities

#### Platform

- Production deployment.
- Environment-specific config.
- Secrets management.
- CI/CD.
- Rollback.
- Database migrations.
- Backup/restore.
- Observability.
- Alerting.
- Incident response.
- Cost monitoring.
- Performance/load testing.
- Security scanning.
- Audit logging.
- Access control.
- Data retention policy.

#### Product

- Production MVP workflow.
- Report generation.
- Report export.
- Evidence explorer.
- Claims/unknowns/verification tasks.
- Human review/audit.
- Candidate comparison.
- Rerun with source-version changes.
- Source/caveat appendix.
- Coverage limitation disclosures.

#### Data/governance

- License/terms enforcement.
- Dataset entitlements.
- Source freshness monitoring.
- Connector monitoring.
- Jurisdiction readiness process.
- User-safe language controls.
- No unsupported legal/valuation/residential steering claims.
- Compliance review records.

#### Architecture

- Modular connectors.
- Jurisdiction adapters.
- Intent/rule packs.
- Versioned evidence/claims/reports.
- API contracts.
- Batch report capability.
- Queued async processing.
- Degraded-mode behavior.
- Documented extension points.

### Required artifacts

```text
production deployment docs
environment config template
secrets management docs
CI/CD workflow
migration/rollback runbook
backup/restore runbook and test record
observability dashboards or config
alerting rules
incident response runbook
security checklist
dependency/supply-chain scan config
license/entitlement enforcement tests
data retention policy
privacy/security policy draft
production operator runbook
release checklist
SLO/SLA targets or explicit non-SLA statement
load/performance test plan and results
production smoke test
jurisdiction readiness checklist
connector readiness checklist
rulepack readiness checklist
```

### Pass/fail gates — deployment and operations

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L10-OPS-001 | Production environment can be deployed from documented commands/pipeline. | Deployment depends on undocumented manual steps. |
| L10-OPS-002 | Config is environment-based and secrets are not committed. | Secrets/config are hard-coded or stored in repo. |
| L10-OPS-003 | CI/CD runs required checks before deploy. | Production deploy can bypass verification. |
| L10-OPS-004 | Database migrations are forward-tested and rollback/mitigation strategy exists. | Schema changes are unsafe or unrecoverable. |
| L10-OPS-005 | Backup and restore have been tested. | Backups exist but restore has never been verified. |
| L10-OPS-006 | Production smoke test validates core workflow after deploy. | Deploy success is assumed from process exit code. |
| L10-OPS-007 | Observability covers API, DB, queue/jobs, connectors, report runs, and errors. | Operators cannot diagnose production failures. |
| L10-OPS-008 | Alerts exist for high-severity failures and stale data. | Critical failures are only found by users. |
| L10-OPS-009 | Incident response runbook exists and names severity, owner, escalation, and rollback. | No operational response process exists. |
| L10-OPS-010 | Cost monitoring exists for compute, storage, LLM if used, maps, geocoding, and data vendors. | Usage can spike without detection. |

### Pass/fail gates — security

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L10-SEC-001 | Authentication is implemented if any user-specific or restricted data exists. | Sensitive data is accessible without identity. |
| L10-SEC-002 | Authorization enforces user/org/report/data entitlements. | Users can access reports or datasets they do not own. |
| L10-SEC-003 | Secrets are managed through approved secret store/environment, never repo. | Secrets appear in code, config, logs, or committed files. |
| L10-SEC-004 | Dependency and supply-chain scanning run in CI. | Vulnerable or unreviewed dependencies can ship silently. |
| L10-SEC-005 | Static/security checks cover API input, auth, data access, and injection risks. | Security testing is absent or manual-only. |
| L10-SEC-006 | Audit logs cover login/access where applicable, report generation, evidence amendment, claim generation, exports, and admin actions. | Decision-impacting activity is not traceable. |
| L10-SEC-007 | Data retention/deletion rules are documented and implemented where required. | Data persists indefinitely without policy. |
| L10-SEC-008 | Protected-class/residential steering safeguards are tested if residential workflows exist. | Area recommendations can use protected-class proxies. |
| L10-SEC-009 | Production error responses do not leak secrets, stack traces, or licensed raw data. | Errors expose sensitive internals. |
| L10-SEC-010 | Access to paid/vendor data is entitlement-controlled. | Licensed data leaks through reports/API/export. |

### Pass/fail gates — data governance

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L10-DATA-001 | Every production source has reviewed license/terms status. | Unknown-license data appears in production. |
| L10-DATA-002 | Attribution, redistribution, export, and AI-use constraints are enforced. | Reports/API violate source terms. |
| L10-DATA-003 | Source freshness monitoring flags stale datasets. | Stale data continues to appear as current. |
| L10-DATA-004 | Connector failures and source outages are visible in reports/operators dashboards. | Source unavailability produces silent false negatives. |
| L10-DATA-005 | Jurisdiction readiness checklist is required before adding production geography. | New geography is added by copying data without legal/source review. |
| L10-DATA-006 | Rulepack readiness checklist is required before adding production intent. | New intents produce unsupported claims. |
| L10-DATA-007 | Data lineage from source -> retrieval -> evidence -> claim -> report is queryable. | Lineage breaks at any layer. |
| L10-DATA-008 | Human verification is separate from source evidence and auditable. | Analyst review overwrites original facts. |
| L10-DATA-009 | Coverage limitations are user-visible. | Product implies complete national/global coverage. |
| L10-DATA-010 | Data-quality failures fail closed. | Bad records silently reach reports. |

### Pass/fail gates — performance and scalability

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L10-PERF-001 | Report jobs run asynchronously with status and retry/failure handling. | User requests block on long spatial/report jobs. |
| L10-PERF-002 | Batch screening has bounded concurrency and cost controls. | Bulk jobs can exhaust DB/API/vendor resources. |
| L10-PERF-003 | Spatial queries use indexes and tested query plans for common workloads. | Spatial performance depends on accidental small data. |
| L10-PERF-004 | Large artifacts use object storage/reference pattern, not DB blobs unless justified. | DB stores huge files in a way that harms operations. |
| L10-PERF-005 | Cache strategy is documented and invalidation is source-version aware. | Cached reports hide updated source data. |
| L10-PERF-006 | Load tests cover expected MVP workload and failure thresholds. | No evidence the system can handle expected usage. |
| L10-PERF-007 | Queue depth, job latency, and report failure rates are monitored. | Job system can degrade silently. |
| L10-PERF-008 | Backpressure/degraded mode exists for source outage or high load. | Outages cascade into system failure. |
| L10-PERF-009 | DB connection pooling and transaction boundaries are configured. | DB access fails under modest concurrency. |
| L10-PERF-010 | Performance regressions are testable or observable before release. | Releases can degrade performance unnoticed. |

### Pass/fail gates — product correctness

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| L10-PROD-001 | End-to-end workflow passes from clean deployment. | Production requires manual developer intervention. |
| L10-PROD-002 | Reports include claims, evidence, unknowns, caveats, source appendix, and verification tasks. | Reports are summaries without traceability. |
| L10-PROD-003 | Export artifacts preserve report-run identity and evidence links. | Exported reports detach from audit trail. |
| L10-PROD-004 | Reruns show source/rule/version differences. | Users cannot tell why output changed. |
| L10-PROD-005 | Human review workflow is usable and audited. | Review is external to the product or undocumented. |
| L10-PROD-006 | Candidate comparison is consistent with underlying claims/evidence. | Comparison uses separate logic from reports. |
| L10-PROD-007 | User-facing language is caveated and does not overclaim. | Product states professional determinations. |
| L10-PROD-008 | Error states are understandable and actionable to user/operator. | Failures appear as blank/misleading reports. |
| L10-PROD-009 | MVP scope boundaries are enforced. | Users can request unsupported geographies/intents without clear blocking. |
| L10-PROD-010 | Regression suite includes known red-flag cases and known clean-ish cases. | Product correctness is only tested on synthetic happy path. |

### Required validation

Exact commands may vary, but equivalent gates must exist.

```bash
./scripts/verify.sh
./scripts/run_integration.sh
./scripts/run_security_checks.sh
./scripts/run_db_migration_check.sh
./scripts/run_report_regression_suite.sh
./scripts/run_mvp_regression.sh
./scripts/run_backup_restore_check.sh
./scripts/run_deployment_smoke.sh
./scripts/run_load_test.sh
```

### Completion evidence

- Production deployment record.
- Passing CI.
- Passing production smoke test.
- Backup/restore test record.
- Security scan results.
- Load test report.
- Report regression suite results.
- License/entitlement review records.
- Incident/rollback runbooks.
- Operator runbook.
- Release checklist signed off.
- `state/PROJECT_STATE.md` records Level 10 pass.

### Not complete if

- The app is feature-complete but not observable.
- Backups exist but restore was not tested.
- Source licenses are unresolved.
- Users can access unentitled data.
- Reports cannot be reproduced.
- Connectors can fail silently.
- Performance only works with toy data.
- New jurisdictions require core rewrites.
- Production depends on manual memory.

---

# Add-on readiness gates

These gates do not create new maturity levels, but they are mandatory when adding new sources, jurisdictions, rulepacks, or AI features.

## New data source readiness

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| DS-001 | Source is registered with full metadata. | Source used before registration. |
| DS-002 | License/terms reviewed. | Terms unknown. |
| DS-003 | Commercial/redistribution/export/AI-use rights recorded. | Usage constraints unknown. |
| DS-004 | Connector or ingestion method is documented. | Manual opaque import. |
| DS-005 | Source version/freshness tracked. | Currentness unknown. |
| DS-006 | Caveats are user-reportable. | Limitations hidden. |
| DS-007 | Data-quality checks exist. | Bad records can enter evidence. |
| DS-008 | Failure behavior produces source_failure evidence. | Failure disappears. |
| DS-009 | Test fixtures exist. | Tests require live source. |
| DS-010 | Entitlement enforcement exists if restricted. | All users can access restricted data. |

## New jurisdiction readiness

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| JR-001 | Jurisdiction boundary and administrative hierarchy modeled. | Geography is ambiguous. |
| JR-002 | Parcel/cadastre availability assessed. | Parcel support assumed. |
| JR-003 | Zoning/planning authority model documented. | Local legal structure unknown. |
| JR-004 | Water rights/usage regime assessed if relevant. | Water claims copied from another region. |
| JR-005 | Mineral/resource-rights regime assessed if relevant. | Resource claims unsupported. |
| JR-006 | Local caveats and professional-verification requirements documented. | Reports overclaim certainty. |
| JR-007 | Source registry entries exist for all required sources. | Data sources are ad hoc. |
| JR-008 | Rulepack adjusted for jurisdiction-specific concepts. | Rules assume another jurisdiction. |
| JR-009 | Sample reports reviewed by domain expert or qualified local reviewer when required. | No local review. |
| JR-010 | Coverage limitations are user-visible. | Product implies full support. |

## New intent/rulepack readiness

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| RP-001 | Intent has explicit user, decision, non-goals, and prohibited claims. | Intent is vague. |
| RP-002 | Required evidence categories are defined. | Rules use whatever data exists. |
| RP-003 | Hard gates and soft scores are separated. | One opaque score drives everything. |
| RP-004 | Rule versions and test fixtures exist. | Rule behavior is untracked. |
| RP-005 | Verification tasks are defined. | Report gives warnings without next actions. |
| RP-006 | User-safe language is reviewed. | Claims overstate certainty. |
| RP-007 | Negative/unknown/contradictory cases are tested. | Only favorable cases are tested. |
| RP-008 | Jurisdiction applicability is declared. | Rulepack used outside valid geography. |
| RP-009 | Human review requirement is specified. | Professional review needs are omitted. |
| RP-010 | Regression reports exist. | Rulepack can drift unnoticed. |

## AI/LLM feature readiness

AI/LLM features are optional and must not become the source of truth.

| Gate ID | Pass condition | Fail condition |
|---|---|---|
| AI-001 | AI output is grounded in stored evidence or source documents. | AI invents unsupported claims. |
| AI-002 | Prompt/model/version metadata is recorded for decision-impacting output. | AI output cannot be reproduced or audited. |
| AI-003 | AI output is classified as summary/extraction/inference, not official fact. | AI text is treated as authoritative. |
| AI-004 | Human review is required for legal/regulatory interpretation where applicable. | AI determines legal meaning alone. |
| AI-005 | Evaluation fixtures cover hallucination, omission, contradiction, and overclaiming. | Only happy-path prompts are tested. |
| AI-006 | Sensitive/licensed data use complies with source terms and privacy policy. | AI receives data it is not allowed to process. |
| AI-007 | Failure/degraded mode exists when model unavailable. | Product breaks or fabricates output. |
| AI-008 | Generated user-facing language preserves caveats. | Caveats are dropped during summarization. |
| AI-009 | Cost and latency are monitored. | LLM usage can spike uncontrolled. |
| AI-010 | AI can be disabled without corrupting core evidence/claims. | Core platform depends on opaque generation. |

---

# Milestone validation matrix

Use this as the high-level pass/fail summary.

| Level | Required evidence | Required validation | Must not depend on |
|---:|---|---|---|
| 1 | Control files, state, active plan | agent context check, verify script | chat history |
| 2 | migrations, seeds, DB smoke | Postgres/PostGIS smoke | manual DB setup |
| 3 | source registry, license metadata | source/provenance tests | assumed public-use rights |
| 4 | geometry service, fixtures | geometry/PostGIS tests | UI-only validation |
| 5 | evidence ledger, audit | evidence/audit tests | connector direct output |
| 6 | claim/rules engine | rule/claim tests | prompt-only business logic |
| 7 | persisted report run | report/API regression | live external APIs |
| 8 | connectors/jobs/quality | connector/data-quality tests | flaky network tests |
| 9 | MVP workflow/export/review | MVP regression/workflow tests | developer intervention |
| 10 | production ops/security/governance | CI, smoke, security, load, backup/restore | manual operation memory |

---

# Test ladder

Testing should accumulate, not replace lower-level tests.

| Test layer | First required by | Production requirement |
|---|---:|---|
| Repo/context checks | Level 1 | Required in CI |
| Unit tests | Level 2 | Required in CI |
| DB migration tests | Level 2 | Required in CI or deployment gate |
| PostGIS integration tests | Level 2/4 | Required before release |
| Source/provenance tests | Level 3 | Required in CI |
| Geometry tests | Level 4 | Required in CI |
| Evidence/audit tests | Level 5 | Required in CI |
| Rules/claim tests | Level 6 | Required in CI |
| Report regression tests | Level 7 | Required in CI |
| API contract tests | Level 7 | Required in CI |
| Connector contract tests | Level 8 | Required in CI |
| Live connector smoke tests | Level 8 | Scheduled/opt-in, not normal local default |
| Workflow/MVP tests | Level 9 | Required before release |
| Security tests | Level 10 | Required before deploy |
| Load/performance tests | Level 10 | Required before production claim |
| Backup/restore tests | Level 10 | Required before production claim |
| Deployment smoke tests | Level 10 | Required every deploy |

---

# Documentation ladder

Documentation also accumulates.

| Document | First required by | Must answer |
|---|---:|---|
| `README.md` | Level 1 | What is this and how do I run it? |
| `AGENTS.md` | Level 1 | How should agents work? |
| `MANIFEST.md` | Level 1 | Where are source-of-truth files? |
| `.agent/PLANS.md` | Level 1 | How are plans written/resumed? |
| `docs/ARCHITECTURE.md` | Level 1/2 | What are the core boundaries/invariants? |
| Storage ADR | Level 2 | Why this DB/schema approach? |
| Provenance/source ADR | Level 3 | How is source truth represented? |
| Geometry ADR/section | Level 4 | How are area geometries handled? |
| Evidence ADR/section | Level 5 | How are facts, failures, notes, and audit represented? |
| Rules/scoring ADR | Level 6 | How do evidence-backed claims work? |
| API/report spec | Level 7 | How are report runs created/retrieved? |
| Connector runbook | Level 8 | How does ingestion work and fail? |
| MVP runbook | Level 9 | How does an operator/user complete the workflow? |
| Production runbook | Level 10 | How is the system deployed, monitored, restored, and operated? |

---

# Explicit non-goals by milestone

| Level | Do not do yet |
|---:|---|
| 1 | Do not build feature logic before governance and verification. |
| 2 | Do not build reports/UI before schema and DB smoke pass. |
| 3 | Do not ingest broad data before source/license/provenance model. |
| 4 | Do not build spatial claims before geometry validation. |
| 5 | Do not generate claims before evidence ledger is durable. |
| 6 | Do not generate reports before claims are evidence-linked. |
| 7 | Do not integrate live connectors before fixture vertical slice is reproducible. |
| 8 | Do not ship MVP workflow before connector failure/idempotency is handled. |
| 9 | Do not call it production without security/ops/recovery/governance. |
| 10 | Do not claim global legal/purchase-grade coverage without jurisdiction readiness gates. |

---

# Fast maturity classifier

```text
Can a fresh agent understand and verify the repo?
No -> below Level 1.
Yes -> Level 1 candidate.

Can Postgres/PostGIS migrations/seeds/smoke pass?
No -> Level 1.
Yes -> Level 2 candidate.

Are sources/licenses/versions/retrievals/caveats modeled?
No -> Level 2.
Yes -> Level 3 candidate.

Can areas/geometries be validated, stored, and spatially queried?
No -> Level 3.
Yes -> Level 4 candidate.

Can durable evidence and source failures be stored/audited?
No -> Level 4.
Yes -> Level 5 candidate.

Can deterministic rules generate evidence-linked claims/unknowns?
No -> Level 5.
Yes -> Level 6 candidate.

Can a fixture-backed report run be generated and retrieved reproducibly?
No -> Level 6.
Yes -> Level 7 candidate.

Can real/near-real connectors ingest safely/idempotently with quality gates?
No -> Level 7.
Yes -> Level 8 candidate.

Can a non-developer complete the MVP diligence workflow?
No -> Level 8.
Yes -> Level 9 candidate.

Is it deployed, secure, observable, recoverable, scalable, governed, and fully tested?
No -> Level 9.
Yes -> Level 10.
```

---

# Recommended default assumption

Unless the repo has been freshly verified, assume:

```text
Current milestone: Level 1 candidate
Target milestone: Level 2
Next work: prove Postgres/PostGIS storage spine with migrations, seed data, and DB smoke tests
```

Never claim a higher milestone based on code presence alone. Claim it only after all gates pass with evidence.
