# ODP-BOL-001 Scope-Intake Form — Bologna Pilot Product / AOI / Scope Authorization

**Decision:** ODP-BOL-001 (Bologna pilot product, AOI, and scope)
**Current status:** `review_only_scope_pursuit_answered` — one review-only answer on file (`odp-bol-001-scope-pursuit-2026-06-26`); zero pilot-scope authority records exist.
**Target schema:** `config/bologna_odp1_owner_answer_packet.yaml` (owner_answer_template + pilot_scope_authority_record_template), evaluated by `scripts/bologna_owner_answer_evaluator.py`.
**Provenance:** generated + harness-verified 2026-07-06 (fields/counts/fail-closed rules/CI pins cross-checked against the packet YAML, evaluator, gate-check scripts, and `test_bologna_owner_answer_gate_evaluation.py`). Fill-in form (not raw YAML) so a non-engineer can complete it without YAML-syntax failures; transcription into config is a separate recording slice.

---

## Read this first (what this form is and is not)

1. **This form grants NO authority.** Filling it in changes nothing in the repository. It is an evaluation input. All packet/gate mechanisms are validate-only (`no_overclaim_controls`: no authority, no AOI selection, no source approval, no fixture capture, no DB seed, no report/runtime use, no legal/title/buildability/value claim, no Level-10/hosted claim).
2. **Recording is a separate, later step.** After you complete and sign this form and it passes review, a dedicated "recording slice" (engineering change) writes your answer into `config/bologna_owner_answer_intake.yaml` (`current_owner_answers`) and `config/bologna_pilot_scope_authority.yaml` (`current_authority_records`), with companion updates to the frozen-state CI pins in `scripts/bologna_owner_answer_intake_check.py` and `scripts/bologna_odp1_owner_response_gate_check.py`. This form must not be committed into those config files directly — doing so fails CI by design.
3. **What flips review-only to owner-authorized** (all three together, in one non-bundled submission):
   - a NEW owner answer with `answer_type: approve_with_cited_authority` (the only accepted value for authorization — the current `approve_review_only` answer is a dead end by design);
   - the FIRST-EVER pilot-scope authority record covering ALL 12 scope decisions;
   - an EXTERNAL authority citation (a signed decision record, ADR, or ticket outside this repo's own inference chain) on both records. The existing "Codex thread owner directive 2026-06-26" citation does not qualify.
4. **Authorizing ODP-BOL-001 unlocks nothing downstream.** ODP-BOL-002 (source authority/rights), ODP-BOL-003 (recorded corpus), ODP-BOL-004 (DB-backed report proof), the DS-017 vendor decision, and hosted/Level-10 authority all remain separately gated no matter what you answer here.
5. **Fail-closed rules.** The gate rejects the whole submission on any single violation. There is no partial credit. Anywhere this form says REJECTED IF, treat it literally. A truly blank or whitespace-only field is auto-rejected by the evaluator's code; `TBD`, `UNKNOWN`, `N/A`, or an unchanged placeholder (e.g. the packet's `OWNER_TO_PROVIDE`) is a non-empty string that passes the code's emptiness check but is rejected at human review — either way the submission fails, so fill every field with a real value.

---

## Part 1 — Owner Answer Record

Target: `config/bologna_owner_answer_intake.yaml` -> `owner_answer_contract.current_owner_answers` (via later recording slice).
**Shape rule:** this record must contain EXACTLY the 11 fields below — no fields may be added, none removed (extra keys are rejected: `owner_answer has unexpected fields`).

### 1.1 `owner_answer_id` — REQUIRED
A unique ID for this answer. Suggested pattern: `odp-bol-001-scope-authorization-YYYY-MM-DD`.
> Fill in: `____________________________________________`

REJECTED IF: empty; a placeholder; or equal to the existing answer's ID `odp-bol-001-scope-pursuit-2026-06-26` (this must be a NEW record, not an edit of the old one — the old record is frozen by CI and may not be mutated).

### 1.2 `odp_id` — REQUIRED (pre-filled, do not change)
> Value: `ODP-BOL-001`

REJECTED IF: any other value, including different casing or whitespace.

### 1.3 `answer_type` — REQUIRED (choose exactly one)
Your decision for the whole packet. Check ONE box:

- [ ] `approve_with_cited_authority` — **the ONLY choice that authorizes the Bologna pilot scope.** Requires Parts 2–4 fully completed.
- [ ] `keep_blocked` — Bologna scope stays blocked.
- [ ] `approve_review_only` — stays in today's review-only state (this is the currently recorded answer; re-selecting it changes nothing).
- [ ] `exclude_or_defer` — Bologna is deferred or excluded from current scope.

REJECTED IF: any value outside these exact 4 strings (e.g. "approved", "yes"). NOTE: this authorization evaluator (`evaluate_owner_answer`, with `required_answer_type = approve_with_cited_authority`) accepts ONLY `approve_with_cited_authority`. The other three are schema-valid enum values, but selecting any of them makes this evaluator reject the submission with the error `owner_answer.answer_type must be approve_with_cited_authority`. They are legitimate owner outcomes, but they are recorded through the plain owner-answer intake path — this authorization gate does not accept them.

### 1.4 `decision_owner` — REQUIRED
Named person or role accountable for this decision (e.g. `benjmcd`).
> Fill in: `____________________________________________`

REJECTED IF: empty or placeholder.

### 1.5 `decision_date` — REQUIRED
Date you made this decision, in strict ISO format `YYYY-MM-DD` (e.g. `2026-07-07`). This is the only date in the submission that is machine format-checked (`date.fromisoformat`).
> Fill in: `______ - __ - __`

REJECTED IF: not a parseable ISO date (blank, `TBD`, `07/07/2026`, "July 7" all fail).

### 1.6 `authority_reference` — REQUIRED
Citation to the EXTERNAL decision record backing this answer: a signed decision document, ADR, or ticket that exists outside this repository's own inference chain (an owner-signed, owner-merged ADR committed to docs/adr/ qualifies; an external ticket is optional corroboration). Give a locator a reviewer can independently find (document title + date + where it lives, or ticket ID).
> Fill in: `____________________________________________`

REJECTED IF: empty; OR (human review) it is repo-local inference, self-referential (cites this form), or cites only the prior review-only pursuit note — that note explicitly disclaims supplying a complete pilot-scope authority record. The code checks only non-emptiness; a reviewer checks externality. Both must pass.

### 1.7 `answer_summary` — REQUIRED
Plain-language summary of what you decided. Do not claim more than the other fields support (no downstream unlocks, no source approvals, no legal/title/value claims).
> Fill in:
> `____________________________________________`
> `____________________________________________`

REJECTED IF: empty; or (human review) it asserts scope beyond what this decision covers.

### 1.8 `cited_artifacts` — REQUIRED (list, at least 1 item)
Supporting artifacts (the external decision record from 1.6, plus any ADRs/tickets/signed docs). One per line; every line must be non-empty.
> 1. `____________________________________________`
> 2. `____________________________________________`
> 3. `____________________________________________`

REJECTED IF: the list is empty, or any listed item is blank.

### 1.9 `caveats` — REQUIRED (list, at least 1 item)
Limits on this answer. Must reflect true scope limits. Recommended baseline caveats (keep, and add your own):
> 1. `This answer authorizes pilot scope only; it does not approve sources, source rights, corpus, fixtures, DB, reports, hosted use, or Level 10 claims.`
> 2. `No legal, title, access, buildability, valuation, or investment conclusions are authorized.`
> 3. `____________________________________________`

REJECTED IF: the list is empty, or any listed item is blank.

### 1.10 `downstream_unlocks_requested` — REQUIRED (locked, must stay empty)
> Value: `[]` (empty list — do not add anything)

REJECTED IF: it contains ANY entry. Requesting any downstream unlock hard-rejects the entire submission even if everything else is perfect. This mechanism never unlocks ODP-BOL-002/003/004 regardless of your answer.

### 1.11 `supersedes_owner_answer_ids` — REQUIRED (pre-filled)
Prior answers this one replaces. If you selected `approve_with_cited_authority`, keep the pre-filled value so the review-only answer is cleanly superseded:
> Value: `[odp-bol-001-scope-pursuit-2026-06-26]`

May be empty only if you intend this answer NOT to replace the existing review-only answer. REJECTED IF: it contains a blank item.

---

## Part 2 — Pilot-Scope Authority Record

Target: `config/bologna_pilot_scope_authority.yaml` -> `authority_record_contract.current_authority_records` (via later recording slice). This is the first-ever such record (the list is currently empty and pinned empty by CI until the recording slice).
**Shape rule:** all 14 fields below are required and must be non-empty except where marked "must stay empty". Extra fields are tolerated by the evaluator but discouraged — add none.

Only complete Part 2 if you selected `approve_with_cited_authority` in 1.3.

### 2.1 `authority_record_id` — REQUIRED
Unique ID. Suggested pattern: `bologna-pilot-scope-authority-YYYY-MM-DD`.
> Fill in: `____________________________________________`

REJECTED IF: empty or placeholder.

### 2.2 `authority_type` — REQUIRED (pre-filled recommendation)
Category label for this record. The schema allows exactly 11 values: `product_decision`, `aoi_boundary_decision`, `operator_use_case_decision`, `non_goal_review`, `jurisdiction_review`, `scope_mode_decision`, `ds017_treatment_decision`, `source_selection_policy`, `fixture_boundary_decision`, `runtime_boundary_decision`, `no_overclaim_review`. Because this ONE record bundles all 12 scope decisions (coverage is proven by `scope_decision_ids` in 2.7, not by this label), use the umbrella value:
> Value: `product_decision` (keep unless you have a specific reason to change; if changing, pick only from the 11 values above)

REJECTED IF: empty. (Known schema note: the 11-value list is not enforced by the pre-record intake evaluator, but IS enforced at recording time by `scripts/bologna_pilot_scope_authority_check.py` (EXPECTED_AUTHORITY_TYPES, exact match); and no value maps 1:1 to the stop-conditions decision — stay inside the list.)

### 2.3 `authority_reference` — REQUIRED
Citation to the external decision record for the scope bundle. Normally the same external record as 1.6.
> Fill in: `____________________________________________`

REJECTED IF: empty; or (human review) not genuinely external.

### 2.4 `decision_owner` — REQUIRED
> Fill in: `____________________________________________`

REJECTED IF: empty.

### 2.5 `decision_date` — REQUIRED
Use strict `YYYY-MM-DD`. (The machine check here is non-empty-string only, but use ISO anyway — reviewers require it.)
> Fill in: `______ - __ - __`

REJECTED IF: empty.

### 2.6 `effective_date` — REQUIRED
Date the authority takes effect, `YYYY-MM-DD` (may equal 2.5).
> Fill in: `______ - __ - __`

REJECTED IF: empty.

### 2.7 `scope_decision_ids` — REQUIRED (locked, do not edit)
This record must cover ALL 12 scope decisions. The list below is verbatim and complete — do not rename, drop, or reorder-encode any entry. Missing even one rejects the submission (`missing decisions`).
> Value (all 12, fixed):
> `product_authorizes_bologna_pilot_reference`
> `one_aoi_geometry_or_named_boundary`
> `intended_operator_and_use_case`
> `pilot_non_goals_and_exclusions`
> `stop_conditions_and_reversion_plan`
> `jurisdiction_boundary_review`
> `evidence_only_or_rulepack_scope`
> `ds017_treatment_for_pilot`
> `candidate_source_selection_policy`
> `fixture_capture_boundary`
> `report_runtime_boundary`
> `no_overclaim_review_owner`

### 2.8 `decision_summary` — REQUIRED (assembled from Part 3)
One flat text field summarizing all 12 decisions. **Do not write it here directly** — complete the 12 worksheets in Part 3; the "Decision" line of each worksheet is concatenated (labeled by decision ID) into this field at recording time.

REJECTED IF: empty; or (human review) any of the 12 decisions cannot be individually identified in it.

### 2.9 `evidence_summary` — REQUIRED (assembled from Part 3)
One flat text field summarizing the evidence for all 12 decisions. **Do not write it here directly** — the "Evidence cited" lines of each Part 3 worksheet are concatenated (labeled by decision ID) into this field at recording time.

REJECTED IF: empty; or (human review) any decision lacks its specific required citations (each decision's "Must cite" list in Part 3).

### 2.10 `cited_artifacts` — REQUIRED (list, at least 1 item)
All artifacts cited anywhere in Part 3, plus the external decision record.
> 1. `____________________________________________`
> 2. `____________________________________________`
> 3. `____________________________________________`

REJECTED IF: empty list.

### 2.11 `downstream_unlocks_requested` — REQUIRED (locked, must stay empty)
> Value: `[]` (empty list — do not add anything)

REJECTED IF: it contains ANY entry (hard reject of the whole submission).

### 2.12 `caveats` — REQUIRED (list, at least 1 item)
Limits on this authority record. Recommended baseline (keep, and add your own):
> 1. `Scope authority only; no source, rights, corpus, fixture, DB, report, hosted, or Level 10 authority is granted or implied.`
> 2. `No legal, title, access, buildability, valuation, or investment claims.`
> 3. `____________________________________________`

REJECTED IF: empty list.

### 2.13 `stop_conditions` — REQUIRED (list, at least 1 item — common trap)
Explicit conditions that stop the pilot, copied from your Worksheet 5 answers. This list must NOT be empty — an empty list rejects the submission even though two other list fields allow empty.
> 1. `____________________________________________`
> 2. `____________________________________________`
> 3. `____________________________________________`

REJECTED IF: empty list, or inconsistent with Worksheet 5.

### 2.14 `supersedes_authority_record_ids` — REQUIRED (locked, must stay empty)
> Value: `[]` (no prior authority record exists to supersede)

---

## Part 3 — The 12 Scope-Decision Worksheets

Each worksheet below is one of the 12 required scope decisions. For EVERY worksheet you must (a) answer the owner question in 1–4 sentences ("Decision"), and (b) cite each required evidence item ("Must cite" — these lists are verbatim from the packet and are what a reviewer checks). A worksheet left blank, or missing any one "Must cite" item, blocks the ENTIRE submission (coverage policy: all 12 or nothing). Your Decision lines become `decision_summary` (2.8); your Evidence lines become `evidence_summary` (2.9).

### Worksheet 1 — `product_authorizes_bologna_pilot_reference`
**Question:** Is a Bologna recorded-source pilot authorized at all?
**Must cite:** (1) approving product owner or decision forum; (2) decision date or effective date; (3) cited ticket, ADR, or signed decision record.
**If missing:** No Bologna pilot preparation may proceed beyond blocked catalogs.
> Decision: `____________________________________________`
> Evidence cited (all 3 items): `____________________________________________`

### Worksheet 2 — `one_aoi_geometry_or_named_boundary`
**Question:** What exact one-AOI geometry, named boundary, or boundary source is authorized?
**Must cite:** (1) municipal or parcel-locality boundary reference; (2) CRS or coordinate reference policy; (3) explicit exclusion of broader Bologna or Italy coverage claims.
**If missing:** Source selection, fixture corpus scope, and report subject identity remain blocked.
**Constraint:** name exactly ONE bounded area — not a metro/regional/national scope, not multiple candidates. The gate is barred from choosing an AOI for you; ambiguity here fails.
> Decision (the single AOI): `____________________________________________`
> Evidence cited (all 3 items, including the explicit broader-coverage exclusion statement): `____________________________________________`

### Worksheet 3 — `intended_operator_and_use_case`
**Question:** Who is the intended pilot operator and what is the intended use case?
**Must cite:** (1) operator role or owner; (2) use case and audience; (3) confirmation that output remains screening/evidence-led.
**If missing:** Report language, artifact handling, and review workflow assumptions remain blocked.
**Constraint:** must not imply production, hosted, or multi-tenant use.
> Decision: `____________________________________________`
> Evidence cited (all 3 items): `____________________________________________`

### Worksheet 4 — `pilot_non_goals_and_exclusions`
**Question:** Which legal, title, access, buildability, valuation, investment, live-vendor, and hosted-production claims are excluded?
**Must cite:** (1) excluded legal, title, access, buildability, valuation, and investment claims; (2) excluded live-vendor and hosted-production behavior; (3) local professional-review boundary.
**If missing:** Caveat language, no-overclaim checks, and report semantics remain blocked.
**Constraint:** the exclusion list must be complete — omitting any enumerated category is treated as incomplete, not merely weak.
> Decision: `____________________________________________`
> Evidence cited (all 3 items): `____________________________________________`

### Worksheet 5 — `stop_conditions_and_reversion_plan`
**Question:** What conditions stop the pilot and how are partial or superseded artifacts handled?
**Must cite:** (1) conditions that halt source review or fixture capture; (2) owner for stopping the pilot; (3) reversion or archive plan for superseded pilot artifacts.
**If missing:** Partial authority, source failures, and stale evidence handling remain blocked.
**Constraint:** these stop conditions must ALSO be copied into field 2.13 (`stop_conditions`), which must be non-empty.
> Decision: `____________________________________________`
> Stop conditions (list; copy to 2.13): `____________________________________________`
> Stop owner: `____________________________________________`
> Reversion/archive plan: `____________________________________________`

### Worksheet 6 — `jurisdiction_boundary_review`
**Question:** What country, region, municipality, cadastral, CRS, and local-professional boundaries govern the pilot?
**Must cite:** (1) country, region, municipality, cadastral, and CRS boundaries; (2) legal-interpretation and local professional-review limits; (3) applicability of jurisdiction and rulepack checklists.
**If missing:** Jurisdiction checklist and rulepack/evidence-only review remain blocked.
**Constraint:** silence on the professional-review limit fails; claiming the US checklists apply to Italy unmodified without review fails.
> Decision: `____________________________________________`
> Evidence cited (all 3 items): `____________________________________________`

### Worksheet 7 — `evidence_only_or_rulepack_scope`
**Question:** Is the pilot evidence-only, a constrained locality dossier, or a new rulepack effort? (choose one)
**Must cite:** (1) selected scope category; (2) prohibited reuse of the US homestead rulepack outside documented geography; (3) owner for rulepack or evidence-only review.
**If missing:** Claim generation, unknown handling, and report semantics remain blocked.
> Decision (one of: evidence-only / constrained locality dossier / new rulepack): `____________________________________________`
> Evidence cited (all 3 items, including the explicit US-rulepack non-reuse statement): `____________________________________________`

### Worksheet 8 — `ds017_treatment_for_pilot`
**Question:** Is DS-017 (US commercial parcel vendor, currently blocked pending external authority) approved, deferred, removed, or substituted for this Bologna pilot? (choose one)
**Must cite:** (1) approve, defer, remove, or substitute decision; (2) vendor/license/cost status if approval is proposed; (3) confirmation that DS-017 is not approved by Bologna inference.
**If missing:** Source-readiness and paid/commercial data assumptions remain blocked.
**Constraint:** DS-017 is a US-registry source unrelated to the 6 Bologna candidate sources; leaving this blank, or letting Bologna scope silently "inherit" DS-017 approval, fails.
> Decision (approve / defer / remove / substitute): `____________________________________________`
> Evidence cited (all applicable items, including the explicit no-inference confirmation): `____________________________________________`

### Worksheet 9 — `candidate_source_selection_policy`
**Question:** Which candidate source IDs or categories may enter source-authority review?
**Must cite:** (1) allowed candidate IDs or source categories; (2) owner for exact source selection; (3) required per-source rights review before promotion.
**If missing:** Bologna source-authority intake and source-rights rows remain blocked.
**Constraint:** this selects candidates for REVIEW ONLY — it approves nothing and grants no rights. The 6 known candidate sources you may name (`config/bologna_source_candidates.yaml` `candidate_id` rows): `arpae_cartographic_portal`, `comune_bologna_open_data_pug_constraints`, `comune_bologna_pug_webgis`, `rer_crs_reference`, `rer_geoportale_catalog_services`, `rer_geoportale_dbtr_altimetry`. Italian cadastral coverage is a documented GAP (`known_gaps` gap_id `italian_cadastral_cartography`, represented downstream as `cadastral_gap`) with a heightened no-owner/title/legal-access/buildability caution -- it is NOT a candidate source.
> Decision (named IDs or categories): `____________________________________________`
> Evidence cited (all 3 items): `____________________________________________`

### Worksheet 10 — `fixture_capture_boundary`
**Question:** What recorded fixture and source-failure fixture capture boundary is authorized (as abstract policy — this is not a capture grant)?
**Must cite:** (1) allowed fixture capture method; (2) raw retention, cache, export, and attribution limits; (3) source-failure fixture policy.
**If missing:** Recorded-source corpus manifests and committed fixtures remain blocked.
**Constraint:** even a complete answer does not permit any fixture capture now — capture stays blocked behind later source-rights and corpus gates.
> Decision (policy): `____________________________________________`
> Evidence cited (all 3 items): `____________________________________________`

### Worksheet 11 — `report_runtime_boundary`
**Question:** What local runtime, report artifact, storage, export, lineage, and caveat proof boundary is authorized (as abstract policy)?
**Must cite:** (1) local versus hosted runtime boundary; (2) artifact storage/export limits; (3) required lineage and caveat proof.
**If missing:** DB-backed report/API/runtime proof remains blocked after any future corpus approval.
**Constraint:** must not read as authorizing DB/API/report/runtime work now — those files are forbidden bundling targets.
> Decision (policy): `____________________________________________`
> Evidence cited (all 3 items): `____________________________________________`

### Worksheet 12 — `no_overclaim_review_owner`
**Question:** Who owns no-overclaim and caveat review before fixture, report, or source promotion?
**Must cite:** (1) reviewer or decision owner; (2) required caveat and prohibited-claim checklist; (3) review timing before fixture, report, or source promotion.
**If missing:** Report wording, caveats, and multi-geography generalization remain blocked.
**Constraint:** an unnamed owner fails; review timing that lets fixture/report/source work proceed before this review fails.
> Decision (named owner + checklist + timing): `____________________________________________`
> Evidence cited (all 3 items): `____________________________________________`

---

## Part 4 — Owner Attestation (sign-off)

The automated evaluator enforces record structure/shape, all-12 scope-decision coverage (criterion 3), and the no-downstream-unlocks rule (criterion 4). A human reviewer verifies the criteria code cannot judge: external authority (criterion 1), per-decision cited evidence (criterion 2), and no bundled source/corpus/DB/report changes (criterion 5). Check every box and sign — an unchecked box means the submission is not review-ready.

- [ ] My `authority_reference` (1.6 and 2.3) cites EXTERNAL owner authority outside the AGENT-INFERENCE CHAIN (not necessarily outside the repository): an owner-signed, owner-merged ADR committed to docs/adr/ qualifies as the primary/sufficient record; an external owner-controlled ticket is optional. NOT repo-local inference, not this form, not the prior review-only pursuit note.
- [ ] Every one of the 12 scope decisions in Part 3 is answered with its specific cited evidence (every "Must cite" item addressed).
- [ ] The authority record's `scope_decision_ids` (2.7) covers every required scope decision (all 12, unedited).
- [ ] Neither record requests any downstream unlock (`downstream_unlocks_requested` is `[]` in both 1.10 and 2.11).
- [ ] No source, source-rights, corpus, fixture, DB, or report artifact changes are bundled with this response, and I understand a valid answer still leaves ODP-BOL-002/003/004, DS-017, and hosted/Level-10 authority separately blocked.

> Signature (decision owner): `____________________`  Date (`YYYY-MM-DD`): `____________`

---

## How to submit (ODGAV intake path)

1. **Complete** Parts 1–4 (Part 2/3 only required for `approve_with_cited_authority`). Ensure no blank, `TBD`, or placeholder text survives anywhere.
2. **Hand the completed form to the coordinating agent/session.** It will be evaluated (read-only, no side effects) against the acceptance logic in `scripts/bologna_owner_answer_evaluator.py::evaluate_owner_answer` — the same logic exercised by `backend/tests/test_bologna_owner_answer_gate_evaluation.py`. Any single failure above rejects the whole submission; you will get the exact failing field back.
3. **Recording slice (separate engineering step, not this form):** on pass, a dedicated slice transcribes Part 1 into `config/bologna_owner_answer_intake.yaml` (`owner_answer_contract.current_owner_answers`) and Parts 2–3 into `config/bologna_pilot_scope_authority.yaml` (`authority_record_contract.current_authority_records`), collapsing the 12 worksheets into the flat `decision_summary`/`evidence_summary` fields with per-decision labels, and updates the frozen-state CI pins in `scripts/bologna_owner_answer_intake_check.py` and `scripts/bologna_odp1_owner_response_gate_check.py` in the same change (per `submission_policy` in `config/bologna_odp1_owner_answer_packet.yaml`: `owner_answer_submission_target` / `authority_record_submission_target` / `requires_later_recording_slice: true`).
4. Only after that recording slice merges does ODP-BOL-001 become owner-authorized. Even then, nothing downstream unlocks automatically — ODP-BOL-002 (source rights) is the next separate owner decision.

---

## Pre-submission checklist (quick self-check before handing this in)

- [ ] 1.3 is exactly `approve_with_cited_authority` (if authorizing).
- [ ] 1.1 is a NEW ID; 1.11 supersedes `odp-bol-001-scope-pursuit-2026-06-26`.
- [ ] 1.5 is a real `YYYY-MM-DD` date.
- [ ] 1.8, 1.9, 2.10, 2.12 each have at least one non-blank line; **2.13 (`stop_conditions`) is non-empty.**
- [ ] 1.10 and 2.11 are still `[]` — nothing added.
- [ ] 2.7's 12 IDs are untouched.
- [ ] All 12 worksheets have both a Decision and Evidence for every "Must cite" item.
- [ ] No field anywhere contains blank, `TBD`, `UNKNOWN`, or placeholder text.
- [ ] Part 4 fully checked and signed.
