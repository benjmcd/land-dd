# Owner Decision Packet

Status: `decision-request-only`

This packet is the owner-facing consequence map for the remaining qualification and
Bologna decisions after QFREEZE-1. It is not an authority ledger and does not freeze or approve anything by itself. Only `state/owner-decisions.md`, cited review artifacts, or
approved source/profile records can authorize state changes.

Current repo-confirmed floor:
- QFREEZE-1 is the latest completed owner-authorized freeze.
- `P0` remains `BLOCKED`.
- All non-P0 qualifications and overlays remain `NOT_RUN`.
- `DS-002` is the only selected approved source profile.
- W-003 and W-011 are the only frozen target bindings from QFREEZE-1.
- Bologna has no approved AOI, source authority, source-rights approval, recorded
  corpus, fixture capture, DB seed, runtime proof, or report proof.

## How To Use This Packet

Each decision below can be resolved only by explicit owner authority plus any required
review evidence. The recommended default is conservative: keep a decision blocked until
the owner can cite the evidence that would make the choice reproducible before any
qualification run is unsealed.

Controlled outcomes are limited to:

`FROZEN_TARGET`, `FROZEN_RUBRIC`, `FROZEN_DOMAIN_PROFILE`,
`APPROVED_SOURCE_PROFILE`, `PROFILE_EXCLUDED_WITH_EVIDENCED_NA`,
`BLOCKED_WITH_OWNER_AND_DECISION`, or `REMOVED_THROUGH_REVIEWED_FRAMEWORK_CHANGE`.

## Coherence Check

Position A: freeze broad values now to reduce blocker counts. This is rejected because
it would turn agent inference into qualification authority and would invite post-result
threshold changes.

Position B: leave the backlog as-is. This is accurate but insufficient because it does
not tell the owner what each choice will cause downstream.

Position C: record every material owner choice, consequence, evidence need, and
reversal cost in a non-authorizing packet. This is the selected path because it keeps
authority clean while making the next decisions executable.

## Decision Queue

### ODP-DOM-001 Domain Profile Freeze

Owner question: Which MVP domains remain in scope for P0, and which are excluded before
qualification?

Current state: Eight qualified-domain profiles remain represented by the template only:
`flood`, `wetlands`, `slope_terrain`, `soils_septic_proxy`,
`physical_road_access_proxy`, `zoning_context`, `environmental_context`, and
`source_availability_and_conflict`.

Recommended default: keep every domain `BLOCKED_WITH_OWNER_AND_DECISION` until each
domain has a frozen source hierarchy, issue taxonomy, critical/material definitions,
severity/confidence rubric, tolerances, exclusions, metrics, reviewer roles, and
surveillance plan.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Freeze all eight domains | P0 can later evaluate the full current MVP claim surface, but every domain becomes a pre-result commitment. | P0, Q1, Q2, DQ, R, S |
| Exclude a domain with evidenced N/A | The product claim narrows; reports must avoid that domain and tests must prove no implied coverage. | P0, report caveats, API/report semantics |
| Keep one or more domains blocked | Qualification remains blocked, but no unsupported domain claim is made. | P0 stays `BLOCKED` |

Required evidence: domain profile YAML updates, reviewer/owner approval, source
coverage mapping, caveat language, and change-impact review.

Reversal cost: high after a sealed run because adding or removing a domain changes the
meaning of the product claim and requires full requalification.

### ODP-TGT-001 Active Targets And Criterion Contracts

Owner question: Which active target thresholds and criterion contracts are frozen before
P0, and which are intentionally blocked or removed?

Current state: Active target bindings remain unresolved across P0, Q1, Q2, DQ, DB, S,
A, M, G, and R, while 60 active criterion contracts remain DRAFT.

Recommended default: freeze only thresholds and pass rules that the owner can defend
before seeing results; otherwise record `BLOCKED_WITH_OWNER_AND_DECISION`.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Freeze target and contract values | Enables a future P0 protocol to run against stable acceptance criteria. | P0, Q1, Q2, overlays |
| Block with explicit owner decision | Keeps the path stopped while preserving why a value is not ready. | P0 remains `BLOCKED` |
| Remove through reviewed framework change | Reduces scope only if ADR/framework review proves the criterion is inapplicable. | Qualification catalog, validator, crosswalk |

Required evidence: exact field paths, numeric or categorical values, rationale,
reviewer competence, pass/fail logic, affected criteria, and pre-result timestamp.

Reversal cost: high after results because threshold movement can invalidate the run.

### ODP-RUB-001 Judgment Rubrics

Owner question: Which judgment-heavy criteria have frozen rubrics, reviewers,
adjudication, and calibration cases?

Current state: Sixteen active judgment rubrics remain DRAFT, including `P0-025`,
`Q1-020`, multiple Q2 criteria, DQ/R/A/M criteria, and source-conflict review rows.

Recommended default: freeze rubrics only when reviewer competence, dimensions, scale,
pass rule, adjudication, calibration cases, and evidence schema are all explicit.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Freeze rubric | Human judgment becomes reproducible enough for qualification use. | P0, Q1, Q2, DQ, M, R, A |
| Keep rubric blocked | The related criterion cannot pass. | P0 or dependent gate remains blocked/not run |
| Remove judgment requirement through review | Requires catalog and validator review so a judgment criterion is not silently weakened. | Criterion catalog, validator |

Required evidence: frozen rubric rows, reviewer roles, calibration cases, adjudication
method, and no post-result mutation pledge.

Reversal cost: high if changed after reviewers see cases or system output.

### ODP-SRC-001 Selected Source Profile Set

Owner question: What exact source set is selected for the qualification scope beyond
`DS-002`, and which source-quality profiles are approved?

Current state: `scope.source_profile_ids` contains only `DS-002`. All other source
coverage, rights, preservation, cache/export/AI/raw-data, freshness, quality, failure
behavior, retirement, and enforcement decisions remain blocked.

Recommended default: approve no additional source until the source profile and rights
review identify exactly which operations are allowed.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Approve one source profile | Adds one source to the qualification/source lineage, subject to its operation limits. | P0, DQ, R, source-readiness |
| Exclude or defer a source | Narrows source coverage and may narrow supported geographies/domains. | P0, reports, source caveats |
| Keep source blocked | Prevents fixture/runtime/report use and keeps source coverage incomplete. | P0 stays `BLOCKED` |

Required evidence: source profile file, source registry mapping, terms/license review,
rights decisions, retrieval metadata policy, source-version policy, attribution,
caveats, failure behavior, and storage/export boundaries.

Reversal cost: medium before fixtures; high after evidence capture or report generation.

### ODP-PRO-001 Candidate And Evidence Protocol

Owner question: What sealed candidate, evidence storage, reviewer, and acceptance-case
protocol is approved for P0?

Current state: candidate commit/tag/artifact/protocol/target/vocabulary/catalog digests
are null. P0 auto-evidence rows remain blocked because external vault, sealed case
identity, controlled storage, archive manifests, and evidence hashes are not approved.

Recommended default: keep P0 blocked until the owner approves the storage authority,
case identity register, reviewer access, artifact hashing, and no-mutation controls.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Freeze protocol | Allows a future P0 run to be reproducible and auditable. | P0 |
| Block protocol with owner decision | Keeps P0 stopped without weakening evidence expectations. | P0 remains `BLOCKED` |
| Change protocol after a run starts | Invalidates the run unless a reviewed requalification path is recorded. | P0, Q1/Q2 prerequisites |

Required evidence: protocol version, target version, acceptance-case manifest, storage
authority, reviewer access controls, sealed hashes, and artifact lineage policy.

Reversal cost: high once a candidate or acceptance set is sealed.

### ODP-CON-001 Conditional Profiles

Owner question: Should candidate generation, financial modeling, AI/LLM
decision-relevant output, or commercial profiles remain disabled, become active, or be
excluded?

Current state: candidate generation, financial modeling, AI/LLM decision-relevant
output, and commercial profile flags are false. Related profiles and criteria remain
conditional or inactive.

Recommended default: keep them disabled unless the owner is ready to add the extra
criteria, safety reviews, product caveats, and evidence burdens.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Keep disabled | Current P0 surface stays narrower and avoids extra profile evidence. | P0, Q1/Q2, product scope |
| Activate profile | Pulls profile-specific criteria, rubrics, risks, and validation into scope. | CG, FIN, AI, E, report claims |
| Exclude with evidenced N/A | Requires product docs and report/API wording to avoid implied coverage. | Product scope, reports |

Required evidence: owner rationale, product claim update, risk review, criteria mapping,
rubric/target/profile updates, and caveats.

Reversal cost: medium before qualification, high after claims or user workflows rely on
the profile boundary.

### ODP-BOL-001 Bologna Product And AOI Authority

Owner question: Is a Bologna pilot authorized, and what exact AOI, product use case,
operator, non-goals, jurisdiction review, DS-017 treatment, fixture boundary, runtime
boundary, and no-overclaim owner apply?

Current state: `config/bologna_pilot_scope_authority.yaml` has no current authority
records. Bologna implementation is stopped.

Recommended default: do not proceed beyond blocked catalogs until product and one-AOI
authority are cited.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Approve product/AOI/scope | Allows the next Bologna source-authority step to evaluate exact sources for that AOI. | BSA-001, Bologna source authority |
| Approve evidence-only scope | Prevents premature Italy rulepack/legal claims while allowing source corpus planning. | Bologna corpus, report caveats |
| Keep blocked | No Bologna source, corpus, DB, report, or runtime work may start. | Bologna path remains blocked |

Required evidence: authority record covering every required scope decision, named AOI
or geometry boundary, jurisdiction review, stop conditions, non-goals, DS-017 treatment,
runtime/report boundary, and no-overclaim review owner.

Reversal cost: high after sources or fixtures are selected because AOI changes can make
corpus evidence irrelevant.

### ODP-BOL-002 Bologna Source Authority And Rights

Owner question: Which exact Bologna sources are approved for the authorized AOI, and
what rights govern cache, retain, export, AI use, raw data, attribution, fixtures,
runtime, report use, source versions, caveats, and failures?

Current state: Bologna candidate sources remain pending review; source-authority
records and source-rights approvals are empty.

Recommended default: approve no Bologna source until source schema, source-rights
matrix, and source-authority records are complete and consistent.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Approve exact source rights | Allows a recorded-source corpus manifest to be designed for those sources only. | Bologna corpus |
| Approve source for review only | Keeps runtime/report/export use blocked while allowing limited internal evaluation. | Bologna source review |
| Keep source pending | Blocks fixture capture, runtime use, report use, and source registry promotion. | Bologna remains blocked |

Required evidence: source-authority record, source-rights row, source contract fields,
license/terms version, retrieval method, CRS/precision policy, attribution, caveats,
storage/export limits, failure policy, and report-use policy.

Reversal cost: high after recorded fixture capture because rights or attribution changes
can require recapture, rehashing, and lineage repair.

### ODP-BOL-003 Bologna Recorded-Source Corpus

Owner question: What one recorded-source corpus is approved after product/AOI and
per-source rights authority exist?

Current state: `config/bologna_recorded_source_corpus.yaml` is blocked and contains no
approved corpus. No fixture capture, source-failure fixture, DB seed, runtime use, or
report use is authorized.

Recommended default: do not capture or store a corpus until the AOI, exact sources,
rights, retrieval metadata, versions, CRS, attribution, caveats, storage/export, and
failure fixtures are approved.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Approve corpus manifest | Allows controlled recorded-source fixture capture within the approved boundary. | Bologna report proof |
| Approve failure fixtures only | Improves source-failure evidence without approving substantive source use. | Source failure handling |
| Keep blocked | Prevents source data from entering fixtures or DB-backed report runs. | Bologna remains blocked |

Required evidence: corpus manifest, source version IDs, retrieval metadata, CRS and
precision notes, attribution text, field allow/deny lists, no-data policy, failure
policy, storage/export limits, caveats, review owner, and no-overclaim review.

Reversal cost: medium before capture, high after capture or report lineage is generated.

### ODP-BOL-004 DB-Backed Bologna Report Proof

Owner question: After scope, source rights, and corpus are approved, what is the exact
local DB-backed Bologna report proof required?

Current state: no DB-backed Bologna report, claim set, evidence ledger, unknown list,
caveat list, artifacts, source registry promotion, DB seed, connector, API/UI proof, or
runtime proof is authorized.

Recommended default: require a single local report proof with claims, evidence,
unknowns, caveats, artifacts, lineage, report-use policy, and no-overclaim review before
any broader Bologna work.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Approve one local DB-backed proof | Allows one narrow end-to-end Bologna proof after lower authority is satisfied. | Bologna pilot report |
| Approve report artifact only | Still blocks runtime/API/UI claims unless explicitly authorized. | Report semantics |
| Keep blocked | Prevents false evidence-ledger, report, or Level 10 claims. | Bologna remains blocked |

Required evidence: DB migration/seed boundary, fixture manifest, report-run ID, evidence
ledger rows, claim/evidence links, unknowns, caveats, artifact hashes, lineage, and
review result.

Reversal cost: high after report generation because report artifacts and lineage must
remain reproducible.

### ODP-HOST-001 DS-017, Hosted, And Level 10 Authority

Owner question: Are DS-017, hosted deployment, hosted identity/RBAC, hosted
observability, object storage, billing, production traffic, or Level 10 claims in scope
for the next phase?

Current state: all remain blocked or unapproved. QFREEZE-1 and this packet introduce no
hosted or Level 10 authority.

Recommended default: keep these blocked until separate authority packets cite external
evidence and the release-readiness checks can validate that evidence.

Allowed owner outcomes:

| Outcome | Consequence | Gates affected |
|---|---|---|
| Keep blocked | Preserves local/private MVP boundaries and avoids premature production claims. | Level 10, release readiness |
| Approve one authority stream | Requires the existing intake/checker path to validate exact evidence before implementation. | DS-017 or hosted checks |
| Remove from current milestone | Narrows milestone scope and requires documentation/routing updates. | Product scope, maturity map |

Required evidence: authority packet, source/vendor/legal/security/ops review, cost and
billing controls, secret handling, hosted monitoring/log retention, incident/rollback,
and release-readiness proof.

Reversal cost: high once production users, paid vendors, hosted data, or public claims
exist.

## Immediate Milestone Order

1. OWNER-DEC-1: keep this packet current and obtain owner answers for the decision IDs
   above.
2. If Bologna authority arrives, prioritize ODP-BOL-001 through ODP-BOL-004 in order:
   product/AOI/scope, source rights, recorded corpus, one DB-backed report proof.
3. If Bologna authority does not arrive, continue EQ-5-style qualification
   parameterization closure: domains, targets/contracts, rubrics, source profiles, and
   P0 protocol.
4. Only after owner authority and evidence exist may future implementation update
   targets, profiles, source rights, corpus manifests, DB artifacts, report proof, or
   qualification status.

## Non-Authorization Boundary

This packet does not authorize:
- P0 `PASS`;
- any non-P0 status other than `NOT_RUN`;
- source approvals beyond DS-002;
- Bologna AOI/source authority;
- fixture capture or source-failure fixtures;
- DB seed, connector, report/API/UI/runtime proof, or source registry promotion;
- DS-017, hosted deployment, hosted identity/RBAC, hosted observability, billing, or
  Level 10 authority.
