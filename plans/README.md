# Plans

This directory contains active execution plans, completed or historical plans,
strategic analyses, and roadmap candidates. File presence does not confer active
authority.

## Current routing (2026-07-22)

- Active execution plan: `plans/2026-07-02-authority-evidence-intake.md`.
- Machine-readable task and plan lifecycle: `tasks/task_queue.yaml`; it is the
  authority for which task is active, blocked, or done.
- Current strategic roadmap candidate: `plans/2026-07-22-program-roadmap.md`. It
  consolidates progress, choices, risks, and the future sequence, but it does not
  record owner/source/corpus/report authority or change qualification state.
- Superseded strategic analysis: `plans/2026-07-07-forward-roadmap.md`; it remains at
  its stable path for referenced history and points to the current candidate.
- Latest completed standalone routing plan:
  `plans/2026-07-02-post-geology-routing.md`.

The dated entries below are retained history. Any use of "current" inside an older
entry means current at the time of that entry unless the routing block above says
otherwise.

`AUTH-EVIDENCE-INTAKE` is the active authority-evidence routing posture after
`POST-GEOLOGY-ROUTING` merged through PR #173, authority-evidence routing merged
through PR #174, and the authority evidence intake composition guard merged through
PR #175. PRs #176-#179 then synchronized state, added reporting-only summary/JSON
output, linked that output from runbooks, and forwarded wrapper arguments for those
reporting modes. PR #180 synchronized state after wrapper support, and the current
follow-on sequencing contract machine-checks the packet's authority-dependent
repo-local follow-on map without unlocking work. PR #181 merged that sequencing
contract, PR #182 merged the validate-only production authority evidence reference
contract, PR #183 merged reporting-only output for that reference contract so
future cited-reference fields and per-stream templates can be collected
without writing artifacts, recording authority, or requesting downstream unlocks, PR
#184 synchronized state after that output support, PR #95 completed the checkout v7
dependency-policy closeout while PR #185 synchronized state afterward, and PR #186
added side-effect-free synthetic submitted-reference evaluation so future cited-
reference shapes can be checked in memory before any authority recording remains
externally blocked. The current scope-authority reporting hardening adds optional
summary/JSON output to `bol_scope_auth` so the immediate ODP-BOL-001 cited-authority
acceptance requirements are visible without creating artifacts, recording authority,
or unblocking ODP-BOL-002/003/004. The current authority-validator consolidation
extracts shared guard/YAML/reporting plumbing into `scripts/authority_check_lib.py`,
refactors the overlapping authority validator family to consume it, and routes
pilot-scope authority summary/JSON output through the shared helper without recording
authority, selecting an AOI, approving sources, changing source rights, or unlocking
downstream work. The
posture records that the
owner-independent extended-domain
fixture-ingestion sequence and post-geology closeout are complete, and that the next
substantive work requires cited product/AOI/source/source-rights/corpus/report-proof
authority before Bologna, DS-017, hosted/Level 10, or empirical qualification
implementation can proceed. It does not add another connector, run live calls, approve
sources, change source rights, capture Bologna fixtures, seed the DB, prove a report,
create hosted authority, touch schema/API/auth/UI surfaces, unfreeze qualification,
claim Level 10 authority, approve DS-017, or unblock P0.

`ODGAV-1` completed the owner-independent Bologna validation pass through PR #167
under `plans/2026-06-28-odgav-owner-answer-evaluation.md`. The minerals
extended-domain fixture-ingestion pass under
`plans/2026-06-29-extended-domain-minerals-fixture-ingestion.md` completed through
PR #168, the broadband extended-domain fixture-ingestion pass under
`plans/2026-07-02-extended-domain-broadband-fixture-ingestion.md` completed through
PR #169, and the environmental hazard fixture-ingestion pass under
`plans/2026-07-02-env-fixture.md` completed through PR #170, the water fixture
ingestion pass under `plans/2026-07-02-water-fixture.md` completed through PR #171,
and the geology fixture-ingestion pass under `plans/2026-07-02-geology-fixture.md`
completed through PR #172. The post-geology routing closeout is tracked under
`plans/2026-07-02-post-geology-routing.md` and completed through PR #173. The
authority-evidence intake posture is tracked under
`plans/2026-07-02-authority-evidence-intake.md`; its composition guard completed
through PR #175, and its reporting/runbook/wrapper support completed through PR #179
while state sync completed through PR #180. The authority follow-on sequence checker
completed through PR #181, the production authority evidence reference checker
completed through PR #182, its reporting modes completed through PR #183, post-output
state synchronization completed through PR #184, and checkout v7 policy alignment
completed through PR #95. The
same active posture remains pending external authority evidence.
ODGAV does not record
real owner authority, approve sources, create a corpus, capture Bologna fixtures,
mutate the DB, prove a Bologna report, unfreeze qualification, or unblock P0.

`BSR-001` completed the validate-only Bologna source-rights matrix through PR #109.
Post-BSR routing landed through PR #110, and `BSG-001` completed the validate-only
Bologna source-authority intake guard through PR #111. `PAI-001` adds a
production-wide validate-only authority intake guard across DS-017, hosted platform,
secrets, identity/RBAC, image publication, billing, hosted observability, and Bologna
recorded-source blockers. There is still no unblocked Bologna implementation lane until
product/AOI/source-review authority exists. `BSA-001` remains blocked. Do not proceed
to fixture capture, runtime integration, source registry promotion, rulepack
implementation, hosted authority, DS-017 approval, or a multi-geography framework from
repo-local inference alone.

`SRP-001` reworks the retained dirty-root runtime-provenance regression into a
current-main selected-county fixture review-bundle/idempotency test. It is test-only
and does not change source/report behavior, source readiness, hosted authority, Bologna
authority, or Level 10 status.

`RSR-001` merged through PR #114 and records the post-SRP residual routing closeout.
After `RSR-001`, the only remaining `STILL_DIVERGENT` residual candidate paths are
`backend/app/project_readiness.py` and `backend/app/release_readiness.py`; both remain
deferred until a real control-plane consolidation slice is explicitly selected.

`BRC-001` adds a validate-only Bologna recorded-source corpus contract. It is allowed
because it defines future fixture-manifest requirements while preserving every external
authority blocker; it does not capture fixtures, promote sources, start Bologna, or
claim hosted/Level 10 authority. `BRC-001` merged through PR #116 at
`4b29bcf646e0cf61bbf3eedee00417a4eed9f115`.

`PR116-SYNC` is the current routing-only follow-up after PR #116. It updates live-state
surfaces to stop treating the completed corpus contract as active work while preserving
the same DS-017, hosted, Bologna implementation, and Level 10 blockers.

`AUTH-HANDOFF` hardens the production-authority intake runbook and validator so the
external evidence checklist stays in sync with the machine-readable blocked authority
streams. It does not approve DS-017, hosted, identity/RBAC, observability, image,
billing, Bologna, or Level 10 authority.

`READINESS-CORE` reworks the remaining dirty-root `project_readiness.py` and
`release_readiness.py` parser concepts into current-main read-only app models. The
models parse existing project/routing/release artifacts only; they do not change source
readiness, release semantics, report behavior, hosted authority, or Bologna authority.
`READINESS-CORE` merged through PR #119 at
`fa66b561e8820273963f51642d7dc3ef56ac0491`.

`BOL-PRIORITY` records the next-pursuit decision: the Bologna recorded-source pilot path
is now preferred over generic hosted-production, generic DS-017, and broad
production-authority lanes. `BPS-001` is now the first Bologna pursuit because it
splits pilot-scope authority from later `BSA-001` source/AOI/right-authority
preparation; fixture capture, source promotion, runtime/report use, DB seeds, hosted
authority, DS-017 approval, and Level 10 claims remain blocked until cited authority
exists.

`BPS-001` adds the missing first-gate pilot-scope authority packet before `BSA-001`.
It records the required product, one-AOI, jurisdiction, evidence-only/rulepack,
DS-017-treatment, fixture-boundary, runtime-boundary, and no-overclaim decisions while
keeping all authority references empty and downstream source/corpus updates disabled.
`BPS-001` merged through PR #121 at
`df96c21f9445fc5cb915d2b06ec0b2eb6c731f2f`.

`BPS-REQ-001` added structured
`scope_decision_requests` rows inside the existing pilot-scope authority packet so the
missing external evidence is actionable without approving a source, selecting an AOI,
capturing fixtures, changing source rights, or starting runtime work.

`EQ-ADOPT` records the empirical-qualification framework adoption milestone from PR
#123. The framework is an ADAPT path, not a whole-bundle adoption: EQ-1 must first
record the consolidation boundary, EQ-2 lands the self-validating spine, EQ-3 reports
an honest `P0 = BLOCKED`, EQ-4 subordinates existing readiness/authority checks through
a crosswalk, and EQ-5 tracks owner-decision blockers. Lane R separately corrects the
known false residual-reconciliation claim. No qualification `PASS`, source authority,
hosted authority, DS-017 approval, Bologna authority, or owner-decision unfreeze is
introduced by this routing.

`EQ-1` completed the boundary gate. It adds ADR 0004 and thin routing references so the
empirical-qualification catalog can become the canonical empirical-validity authority
without turning existing readiness and authority gates into competing truth sources.

`EQ-BOL` pulls the parameterization backlog visibility slice forward for the
prioritized Bologna path. It adds `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md`
and blocked task routing for P0 target/contract/rubric/domain/source/scope blockers,
plus Bologna pilot-scope, source-rights, recorded-corpus, and DB-backed report proof
blockers. It does not land the qualification spine, status file, CI gate, source
approval, AOI selection, fixture capture, runtime/report use, DS-017 approval, hosted
authority, owner-decision unfreeze, or Level 10 claim. If no external Bologna authority
arrives, the next repo-local empirical-qualification slice is `EQ-4`.

`EQ-2` lands the self-validating empirical-qualification spine. It imports the
framework docs, configuration, schemas, structural status, validator, and adversarial
selftest into repo-owned paths; adds `backend/tests/test_qualification_spine.py`;
adds `jsonschema` as a dev/validation dependency; and wires the qualification gate into
CI plus `verify`. The target registry remains `DRAFT`, the structural status has no
`PASS`, and the validator reports blocked-readiness warnings.

`EQ-3` formalizes the honest blocked status. It records P0 as `BLOCKED` with concrete
blocker references and no result artifact, archives the cloned draft domain stubs in
favor of one active template, and adds one DS-002 source-quality profile mapped to
production usage fields. No qualification `PASS`, owner-decision unfreeze, source
rights expansion, Bologna approval, fixture capture, runtime/report use, or fabricated
candidate artifact is introduced. If no external authority arrives, the next
repo-local slice is `EQ-4` readiness/authority crosswalk.

`EQ-4` subordinates existing readiness and authority gates to the empirical
qualification control plane. It adds a checked readiness crosswalk, schema, and human
doc; normalizes the change-impact matrix to catalog criterion IDs; and extends the
qualification validator/selftest so inventory drift and unknown criterion IDs fail
closed. It does not change checker behavior, satisfy any mapped criterion, claim a
qualification `PASS`, or unblock owner decisions. If no external authority arrives,
the next repo-local slice is `EQ-5` backlog reconciliation.

`EQP2-1` starts EQ Phase 2 operationalization after the PR #129 handoff. It adds a
derived qualification status checker that runs mapped readiness/authority checker
paths, treats passing readiness checks as non-passing inputs, keeps package-manifest
and spatial DB-runtime checks as explicit `NOT_RUN` cases until runtime inputs exist,
and fails closed when committed status drifts from the derived `P0 = BLOCKED` /
non-P0 `NOT_RUN` view. It wires that status check into verify and the dedicated
qualification CI job. No qualification `PASS`, owner-decision unfreeze, Bologna
approval, source approval, fixture capture, DB seed, report/runtime use, hosted
authority, DS-017 approval, or Level 10 claim is introduced. `EQP2-1` merged
through PR #130 at `a291d0d41eaa5b85b6ec8c80a79b33f2f7d5e670`.

`EQP2-2` makes change-impact invalidation executable against a diff while staying
advisory and non-passing. It extends the canonical change-impact matrix with
path-matching metadata, combines that with readiness-crosswalk surface mappings,
and reports implicated change classes, review groups, invalidated criterion IDs,
surface criterion IDs, and unmatched paths without changing status or creating a
false gate. It must not claim qualification `PASS`, unfreeze owner decisions, or
expand Bologna/source/runtime authority.

`EQP2-3` collects repo-local evidence pointers for `P0-004`, `P0-005`, `P0-021`,
and `P0-023` while keeping each row and the P0 gate blocked. It adds
`docs/qualification/P0_AUTO_EVIDENCE.yaml` plus a checker/wrappers that validate
the artifact, status link, backlog rows, no-PASS status, no CI `continue-on-error`,
no pytest xfail suppression, and fixture-boundary signals. It does not create a
P0 result artifact, unfreeze owner decisions, claim sealed acceptance, capture
fixtures, approve sources, run connectors, or start Bologna runtime/report work.

`EQP2-4` makes existing readiness/authority checkers advertise their mapped
crosswalk criterion IDs through an opt-in machine-readable flag, makes the
qualification validator prove crosswalk-to-checker advertisement parity, and makes
status derivation consume the checker-advertised criterion IDs. It is additive
reporting only: no checker gate behavior, qualification status, owner decision,
source authority, Bologna authority, DB/API/auth/report semantics, or hosted
boundary changes.

`BOL-AUTH-SYNC` closes the completed EQ Phase 2 routing loop after PR #137 and makes
the next active pursuit the Bologna product/AOI/source-rights authority gate. The
substantive next task is still `BSA-001`, but it remains blocked until explicit
product/AOI/source-review authority is cited in the pilot-scope, source-authority, and
source-rights packets. This sync does not approve sources, select an AOI, change
source rights, create a corpus, capture fixtures, seed the DB, prove a report, approve
DS-017, unfreeze owner decisions, or claim hosted/Level 10 authority.

`BAP-001` added a machine-checked
`authority_record_contract` to `config/bologna_pilot_scope_authority.yaml` so future
product/AOI/scope authority can be recorded with required fields, full scope-decision
coverage, and no-overclaim controls. It merged through PR #139 at
`d356cfdf20ead6ee11573cfffc502d7c21769012`. `current_authority_records` remains
empty, and this does not approve sources, select an AOI, change source rights, create a
corpus, capture fixtures, seed the DB, prove a report, approve DS-017, unfreeze owner
decisions, or claim hosted/Level 10 authority.

`BAR-001` extended the pilot-scope authority
checker so a complete future authority record shape can be validated in test isolation
while partial records and records requesting downstream unlocks fail closed. The
committed `current_authority_records` list remains empty; this does not approve
sources, select an AOI, change source rights, create a corpus, capture fixtures, seed
the DB, prove a report, approve DS-017, unfreeze owner decisions, or claim
hosted/Level 10 authority.

`BSA-REC` is the current authority-first slice. It adds a machine-checked
`source_authority_record_contract` to the blocked Bologna source-authority intake guard
so future cited per-source authority evidence can be validated for candidate evidence
slots, source-rights decision coverage, terms/version/retrieval/CRS/attribution/caveat
and storage/export/failure policies, and no downstream unlock requests. The committed
`current_source_authority_records` list remains empty; this does not approve sources,
select an AOI, change source rights, create a corpus, capture fixtures, seed the DB,
prove a report, approve DS-017, unfreeze owner decisions, or claim hosted/Level 10
authority.

`HCV-1` redirects the current path off blocked Bologna scaffolding and hardens the
empirical-qualification validator/control plane. It adds fail-closed checks and
selftest coverage for expired PASS gates, status/result gate mismatch, scope/version
identity drift, per-criterion evidence references, frozen domain completeness and
modality/channel scope, source coverage, conditional rights enforcement, RAW_EXPORT
export rights, P0 blocked-record validation with result_path, and PASS reviewer
metadata. HCV-2, HCV-3, and HCV-4 are now complete. QFREEZE-1 is the active follow-on.
This does not promote any
qualification gate, unfreeze owner decisions, approve Bologna/source/DS-017/hosted
authority, change DB/API/UI/report semantics, or claim Level 10 authority.

`HCV-2` hardens the checker surfaces that HCV-1 now depends on: checklist dry-run
assertions and path confinement, release-package manifest duplicate/secret detection,
selected-county private-MVP connector/provenance bindings, and Bologna pilot-scope
PowerShell wrapper exit-code propagation. It is fix-only and does not add Bologna
scaffolding, promote qualification status, unfreeze owner decisions, or change DB/API/
UI/report/runtime behavior.

`HCV-3` maps readiness/release CI wrapper gates into the qualification readiness
crosswalk without treating shell/PowerShell wrappers as Python checker-advertisement
scripts. It makes future unmapped CI gate wrappers fail closed while preserving
`P0 = BLOCKED`, non-P0 `NOT_RUN`, and all owner/source/AOI/Bologna/hosted blockers.

`HCV-4` aligns qualification status derivation with the validator's unresolved P0
parameterization blocker families, changes the approved DS-002 source-quality profile
to production source-registry rights vocabulary while preserving condition enforcement,
and routes current work from completed HCV-3 to active HCV-4. It does not freeze owner
decisions, bind new sources, promote P0, start Bologna implementation, or change
DB/API/UI/report semantics.

`QFREEZE-1` records the owner directive from 2026-06-22, binds DS-002 as the only
selected source profile, freezes the explicitly authorized scope/version/source fields,
and freezes only W-003/W-011 target bindings with Windows evidence notes. The target
registry remains globally DRAFT, P0 remains BLOCKED, every non-P0 status remains
NOT_RUN, and DQ/Q1/Q2/M thresholds, domain profiles, criterion contracts, judgment
rubrics, source approvals beyond DS-002, and Bologna authority remain blocked.

`OWNER-DEC-1` is the current non-authorizing follow-on after QFREEZE-1. It adds
`state/owner-decision-packet.md` as the owner-facing consequence map for remaining
domain, target/contract, rubric, source, P0 protocol, conditional-profile, Bologna,
DS-017, hosted, and Level 10 decisions. It does not freeze additional values, approve
sources, select a Bologna AOI, create a corpus, run a DB-backed report, or change
qualification status.

`BOL-ODP-1` is the completed Bologna-first follow-on after OWNER-DEC-1. It adds
`config/bologna_owner_answer_intake.yaml` plus a validate-only checker so future
ODP-BOL-001 through ODP-BOL-004 owner answers have a machine-checkable shape tied to
the existing Bologna pilot-scope, source-authority, source-rights, recorded-corpus,
evidence, and report-run contracts. It does not record owner authority, select an AOI,
approve sources, capture fixtures, seed the DB, prove a report, or change
qualification status.

`BOL-ODP1-GATE` is the completed follow-on after BOL-ODP-1. It adds
`config/bologna_odp1_owner_response_gate.yaml` plus a validate-only checker for the
next external owner answer, `ODP-BOL-001` product/AOI/scope authority. It aligns the
required owner-answer fields with the owner-answer intake and the required
scope/authority-record fields with the pilot-scope authority packet. It keeps owner
answers, authority records, downstream updates, source/corpus/report work, and
qualification status blocked.

`BOL-ODP2-GATE` is the completed follow-on after BOL-ODP1-GATE. It adds
`config/bologna_odp2_source_rights_response_gate.yaml` plus a validate-only checker for
the next external owner answer, `ODP-BOL-002` source authority and rights. It aligns
the required owner-answer fields with the owner-answer intake, required
source-authority record fields and candidate evidence slots with the source-authority
intake, and required rights decisions/candidate IDs with the source-rights matrix. It
keeps `ODP-BOL-001` as the missing prerequisite and keeps owner answers,
source-authority records, source-rights approval references, downstream updates,
source/corpus/report work, and qualification status blocked.

`BOL-ODP3-GATE` is the completed follow-on after BOL-ODP2-GATE. It adds
`config/bologna_odp3_corpus_response_gate.yaml` plus a validate-only checker for the
next external owner answer, `ODP-BOL-003` recorded-source corpus authority. It aligns
the required owner-answer fields with the owner-answer intake and the required corpus
decisions, manifest fields, candidate evidence, source-failure, CRS, attribution,
caveat, storage/export, and no-overclaim requirements with the recorded-source corpus
contract. It keeps `ODP-BOL-001` and `ODP-BOL-002` as missing prerequisites and keeps
owner answers, corpus authority records, recorded corpus references, downstream updates,
fixture capture, DB seed, report proof, hosted authority, Level 10 authority, and
qualification status blocked.

`BOL-ODP4-GATE` is the completed follow-on after BOL-ODP3-GATE. It adds
`config/bologna_odp4_db_report_proof_response_gate.yaml` plus a validate-only checker
for the next external owner answer, `ODP-BOL-004` DB-backed Bologna report proof
authority. It aligns required owner-answer and report-proof fields with the
owner-answer intake and required report-run, evidence, and claim fields with the JSON
schemas. It keeps `ODP-BOL-001`, `ODP-BOL-002`, and `ODP-BOL-003` as missing
prerequisites and keeps owner answers, report-proof authority records, DB report-run
references, report artifacts, downstream updates, DB seed, API/report changes, hosted
authority, Level 10 authority, and qualification status blocked.

`BOL-POST-ODP4-AUTH` is the current routing boundary after BOL-ODP4-GATE. It does not
add another Bologna gate. The response-gate scaffold for `ODP-BOL-001` through
`ODP-BOL-004` is complete; the next substantive Bologna step requires cited external
owner authority in sequence: product/AOI/scope, source authority and rights,
recorded-source corpus, then one DB-backed report proof. If that authority does not
arrive, the only repo-local path is non-authorizing EQ-5-style backlog maintenance for
domains, targets/contracts, rubrics, source profiles, and P0 protocol blockers.

`EQ-5` (`plans/2026-06-23-eq5-parameterization-backlog-check.md`) adds
`scripts/qualification_parameterization_backlog_check.py`, a validate-only consistency
checker for the qualification parameterization backlog, owner-decision packet,
owner-decision ledger, Bologna owner-answer intake, qualification status,
qualification targets, DS-002 selected source profile, task routing, and verification
wiring. It marks the backlog tracking milestone complete without resolving any
external/owner authority blocker, qualification result, Bologna authority step, source
approval beyond DS-002, fixture, DB seed, report artifact, API/report change, hosted
authority, or Level 10 claim.

`EQ-R` closes the residual-reconciliation falsehood without extracting or promoting
deferred dirty-root product work. `state/residual-reconciliation.md` now records live
main at `74af6f5a26594e80efed0fb4cfa9015e7e9e135d`, preserves `STILL_DIVERGENT` as
zero after the focused rework slices, explicitly lists the 17
`DEFER_STILL_BLOCKED` paths as decaying candidate evidence, and states that no
deferred file becomes live product authority, source authority, Bologna authority,
release authority, hosted authority, report/API/DB behavior, qualification status, or
`PASS`.

`BOL-ODP1-PACKET` adds a validate-only owner-answer packet for the first Bologna owner
decision path, `ODP-BOL-001`. It gives the owner a machine-checked response template,
pilot-scope authority-record template, required product/AOI/scope checklist, allowed
outcomes, and downstream blocker list aligned to the existing intake, ODP1 gate, and
pilot-scope authority packet. It keeps owner answers, authority records, AOI/source
approval, source-rights changes, recorded corpus work, fixture capture, DB seed,
report proof, downstream updates, qualification status, hosted authority, and Level 10
claims blocked.

`BOL-POST-ODP1-PACKET` is the current routing-only sync after PR #161. It records that
the ODP-BOL-001 owner-answer packet is merged and complete, while preserving the same
external-authority stop condition: real cited owner authority for product/AOI/scope is
required before `ODP-BOL-002` source-rights work, recorded-source corpus work, fixture
capture, DB seed, report proof, source registry promotion, hosted authority,
qualification PASS, or Level 10 claims can proceed.

`BOL-SCOPE-PURSUIT` (`plans/2026-06-26-bologna-scope-pursuit.md`) records the
2026-06-26 owner directive to pursue Bologna scope as a single `approve_review_only`
`ODP-BOL-001` owner answer. It does not record
pilot-scope authority, select an AOI, approve sources or source rights, create a
recorded-source corpus, capture fixtures, seed the DB, prove a report, approve DS-017,
unfreeze qualification, or claim hosted/Level 10 authority. The next substantive
Bologna step is a complete cited `ODP-BOL-001` pilot-scope authority record.

`BOL-SCOPE-AUTH` (`plans/2026-06-27-bol-scope-auth.md`) adds
`config/bol_scope_auth.yaml`, a validate-only readiness gate for the later cited
ODP-BOL-001 authority-recording slice. It proves the current owner answer remains
`approve_review_only`, requires a future
`approve_with_cited_authority` answer before authority can be recorded, keeps
`current_authority_records` empty, and forbids bundling source, corpus, fixture, DB,
report, hosted, or Level 10 work. The current reporting hardening makes those blocked
requirements available through opt-in `--summary` and `--json` checker output without
changing the gate state or allowing downstream work.

`BOL-ODP2-PACKET` (`plans/2026-06-27-odp2-owner-answer-packet.md`) adds
`config/bologna_odp2_owner_answer_packet.yaml`, a validate-only owner-facing packet for
the later ODP-BOL-002 source-authority/source-rights answer. It gives the owner a
checked owner-answer template, source-authority record template, candidate evidence
checklist, rights-decision checklist, allowed outcomes, and downstream blocker list
aligned to the ODP2 response gate, source-authority intake, and source-rights matrix.
It keeps ODP-BOL-001 authority missing, all ODP2/source-rights references empty, and no
source approval, source-rights mutation, corpus, fixture, DB seed, report proof,
hosted authority, Level 10 claim, or qualification PASS is introduced.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the historical
source for initial retain/rework/defer/archive/discard decisions; current residual
classification is in `state/residual-reconciliation.md`.

Superseded plans may remain at stable paths when task, state, or historical references
depend on them, but they must say what supersedes them near the top. Move a plan to
`plans/archive/` only in a deliberate reference-update slice; do not mass-move plans
for cosmetic normalization.
