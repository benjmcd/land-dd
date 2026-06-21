# ADR: Report-Run Contract Backward-Compatibility for Added Required Fields

Date: 2026-06-21

## Status

Accepted

Verified 2026-06-21: across all 23 persisted v1 artifacts the 5 rights sub-fields are absent and the other source_details fields are universal, so only those 5 are relaxed and source_details itself stays required.

(Decision record only. The schema/test change it specifies lands as a separate small
follow-up PR — see "Sequencing".)

## Context

`schemas/report_run_schema.json` declares `contract_version` as the constant
`report_run_contract_v1` (see lane-d-0009, lane-d-0010, lane-d-0013). After that baseline
was set, the `v1` contract was tightened twice without changing the version constant:

- `ea0d69a` (TD-081, 2026-06-04) added `source_details` to `source_manifest.required`, and
  made `authority_level` and `license_status` (plus `source_id`, `name`,
  `commercial_use_status`, `freshness_class`, `review_status`, `review_owner`,
  `last_checked_at`) required inside each `source_details[]` entry.
- `8c877fd` (2026-06-18) added `redistribution_status`, `cache_allowed`, `export_allowed`,
  `raw_data_allowed`, `ai_use_allowed` to `source_details[].required`.

An automated review (chatgpt-codex-connector, flagged P1) observed that this makes the
published `v1` schema reject any persisted `v1` artifact produced before those keys existed —
a backward-compatibility / report-reproducibility concern, since the contract version did not
change to mark the tightening.

Investigation established the precise blast radius (this is the load-bearing context for the
decision):

1. **There is no runtime JSON Schema validation of report artifacts.** This is explicit in
   lane-d-0010 ("does not add runtime JSON Schema validation") and lane-d-0017 ("No runtime
   JSON Schema validation is introduced"). `schemas/report_run_schema.json` is consumed only
   by *structural* tests in `backend/tests/reports/test_report_schema_contract.py` that assert
   the schema's own shape — never against actual report instances.
2. **Report load/replay uses Pydantic, not the JSON Schema.** `ReportRunContract.model_validate(...)`
   deserializes the object-store artifact on read (`backend/app/reports/report_repo.py`), and
   `source_manifest` is typed `dict[str, object]` (`backend/app/domain/report_contracts.py`),
   so an artifact lacking `source_details` loads without error. `dossier.py` degrades
   gracefully when `source_details` is absent.
3. **No breaking artifacts exist.** All 23 persisted `report_run_contract_v1` artifacts under
   `local_artifacts/object_store_r016*/` already carry `source_details` with the provenance
   sub-fields. The writer (`backend/app/reports/service.py` `_source_manifest`) always emits
   them.
4. **No version-dispatch mechanism exists.** `contract_version` is written on output and
   asserted in tests, but never read back to select a schema or model. A versioned validator
   would have to be built from scratch.
5. **The latent risk is real but not active:** if a future slice adds runtime/external schema
   validation of artifacts — e.g. the qualification control plane's
   `report_contract_version` target (`config/qualification/qualification_targets.yaml`,
   currently `null`) — it would reject pre-tightening `v1` artifacts unless this is resolved
   first.

So the defect is **contract honesty / hygiene**: the published `v1` schema asserts a universal
invariant ("every `v1` artifact carries these provenance keys") that it cannot back for
`v1`-era artifacts predating the tightening, even though no consumer enforces it today.

This change does not touch the active empirical-qualification (EQP2) lane; that lane
(`config/qualification/**`, `scripts/*qualification*`, report-unrelated state) does not modify
`schemas/report_run_schema.json` or `backend/app/reports/`.

## Decision

Adopt **Option A: keep `report_run_contract_v1`, relax the post-baseline-required provenance
fields to optional, and keep enforcement at the writer.** Specifically:

1. **Relax only the `source_details[]` sub-fields that were made required after the v1
   baseline — keep `source_details` itself required.** All persisted `v1` artifacts carry the
   `source_details` provenance block (Context §3), so the block's *presence* is a true v1
   invariant and must stay in `source_manifest.required`; a manifest with no provenance block
   at all is a genuine defect the published contract should keep rejecting. What is *not* a
   true invariant for all v1-era artifacts is the `8c877fd` rights cohort
   (`redistribution_status`, `cache_allowed`, `export_allowed`, `raw_data_allowed`,
   `ai_use_allowed`) — relax exactly these five to **optional** inside `source_details[]`,
   retaining their *type/enum* definitions so any artifact that carries them is still
   shape-checked. The earlier TD-081 sub-fields (`authority_level`, `license_status`,
   `commercial_use_status`, `freshness_class`, `review_status`, `review_owner`,
   `last_checked_at`, `source_id`, `name`) are **kept required**: the artifact check found them
   present in all 23 persisted `v1` artifacts, while the five rights fields were absent from all
   23. (If a persisted `v1` artifact lacking `source_details` or a TD-081 sub-field ever
   surfaces, widen the relaxation accordingly and cite it — current evidence says keep them
   required.)
2. **Enforcement of provenance presence stays at the writer, not the published schema.**
   `backend/app/reports/service.py` `_source_manifest` always emits `source_details` with full
   provenance (each entry is a fixed-key dict; `SourceContract` defaults the rights/authority
   fields to non-null `"unknown"`/`AuthorityLevel.UNKNOWN`, so they can never serialize
   missing). Today this is asserted in exactly one place — `backend/tests/reports/test_report_service.py`
   (≈lines 221-233, which checks each `source_details` entry's rights sub-fields).
   `test_report_regression.py` does **not** cover it: its `stable_report_projection` omits
   `source_details` from the pinned `source_manifest` shape. Because relaxing the schema removes
   the (documentary) presence constraint, the follow-up PR **must add a writer/regression-level
   assertion** so provenance presence is not pinned by a single test. This keeps the AGENTS.md
   non-negotiable ("every source-derived record must carry provenance") enforced at the layer
   that actually produces records, consistent with the repo's "JSON Schema is a documentation
   contract, not the runtime gate" stance (lane-d-0010, lane-d-0017).
3. **Add a `description` to the schema** stating `report_run_contract_v1` is an additive, open
   contract (`additionalProperties: true`, per lane-d-0010/0013) documenting current writer
   output, and that historically-persisted `v1` artifacts may omit keys added after the
   baseline.
4. **Do not introduce runtime JSON Schema validation** (unchanged from lane-d-0010/0017).
5. **Defer any `report_run_contract_v2` + version-keyed validation.** If runtime/external
   contract validation is ever required, it must be designed as a dedicated slice **together
   with** the qualification `report_contract_version` target and an explicit version-dispatch
   layer — not bolted on now. Building version-dispatch today would be throwaway infrastructure
   and would pre-empt a decision that belongs to the empirical-qualification control plane.

Rejected alternatives:

- **Option B — bump to `report_run_contract_v2` with version-keyed validation now.** Requires
  building a dispatch layer that does not exist, churns 10+ test files, and contradicts the
  repo's deferred-versioning posture (lane-d-0013). It also overlaps the qualification lane's
  future `report_contract_version` decision and would risk colliding with it. Premature.
- **Option C — bump to v2 and backfill/rewrite persisted v1 artifacts.** Rewriting persisted
  evidence directly violates report reproducibility (an AGENTS.md stop-and-record condition).
  Rejected outright.
- **Option D — document only, leave the schema requiring the fields.** Leaves the published
  contract dishonest and arms a future runtime validator to reject old artifacts. Rejected in
  favor of making the schema truthful now (A), which is barely more work.

## Consequences

- The published `v1` schema becomes **truthful for all `v1`-era artifacts**; a future runtime
  or external validator can safely apply it without rejecting pre-tightening artifacts.
- **No migration, no rewriting of persisted artifacts** → reproducibility preserved.
- **Provenance guarantee for new reports is unchanged** — still enforced by the writer and
  writer tests.
- **Minimal surface:** `schemas/report_run_schema.json` (`required` arrays + a `description`)
  and the matching expected-set assertion in
  `backend/tests/reports/test_report_schema_contract.py`. No writer, repo, API, DB, or
  Pydantic-model change. No new dependency.
- The provenance keys are now "optional in schema, mandatory in practice." A future reviewer
  must understand the enforcement lives in the writer; this ADR is the pointer.
- Versioned report contracts remain an open, deferred question owned jointly by Lane D and the
  qualification control plane.

## Sequencing

Ordering chosen to minimise conflict/error risk:

1. **Land this ADR first**, on its own branch/PR (`docs/adr/lane-d-0021-*`), separate from any
   code. It records the decision and unblocks the follow-up without entangling docs and code.
2. **Implement the schema/test relax as one small follow-up PR**, branched off the **current**
   `origin/main` at implementation time. Before writing, **empirically re-confirm** every
   persisted `v1` artifact under `local_artifacts/object_store_r016*/` carries the
   `source_details` key (current evidence: all 23 do → keep `source_details` required and relax
   only the sub-fields per Decision §1; if any lacks it, widen the relaxation and cite that
   artifact). Before opening the PR, re-confirm no in-flight PR is touching
   `schemas/report_run_schema.json` or `backend/tests/reports/` (none today), and **rebase onto
   current `main` before merge** so the diff is exactly the intended files (lesson from a prior
   near-miss where a stale base would have reverted unrelated merged work).
3. **No dependency on the empirical-qualification (EQP2) lane** — zero file overlap, so this
   can proceed independently. It is **low-urgency** (latent, not an active break); it need not
   pre-empt or block any EQP2 PR. Prefer landing it when the merge queue is otherwise quiet to
   keep history clean.
4. **Coordinate the deferred v2/versioning** (Decision §5) only when the qualification lane
   activates `report_contract_version`; do not start it before then.

## Verification

- `backend/tests/reports/test_report_schema_contract.py` updated so the expected
  `source_details[].required` set matches the relaxed schema (and `source_manifest.required`
  still includes `source_details`); the structural tests pass.
- Writer enforcement: `backend/tests/reports/test_report_service.py` (≈221-233) is today the
  sole assertion that a generated report's `source_details` carries the rights sub-fields.
  The follow-up PR **adds** a writer/regression assertion (e.g. extend
  `test_report_regression.py`'s stable projection to include `source_details`, or add a
  dedicated writer test) so provenance presence is no longer pinned by a single test.
- Add one structural test that a synthetic pre-tightening `v1` `source_details[]` entry
  (omitting the now-optional sub-fields) satisfies the relaxed schema, while a writer-produced
  entry still carries them — and that a manifest with **no** `source_details` block still
  fails (presence remains required).
- `.\scripts\verify.ps1` green (incl. `qualification-selftest`, which is unaffected — no
  qualification artifact references these `required` arrays).
- Reviewed by a separate lane (data-governance / code review), not self-approved. (This ADR's
  decision was pressure-tested by a data-governance review: verdict SOUND-WITH-AMENDMENTS;
  both amendments — narrow scope to sub-fields, correct the test-coverage claim — are folded in
  above.)
