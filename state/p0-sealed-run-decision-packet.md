# P0 Sealed-Run Decision Packet

Status: `decision-packet-only`

Generated: 2026-07-06

This packet records the post-QFREEZE-2 path from `P0 = NOT_RUN` to a possible
future `P0 = PASS`. It does not authorize, implement, or record a qualification
result. It does not change qualification config, `state/owner-decisions.md`, or
`state/EMPIRICAL_QUALIFICATION_STATUS.yaml`.

## Current Repo-Confirmed Floor

- QFREEZE-2 landed through PR #191 and live `origin/main`
  `b8c5f096f3d535974e8a41bde1ee38dc2565ec98`.
- QFREEZE-2 is recorded under `benjmcd` authority as a flood-only parameterization
  freeze in `state/owner-decisions.md` under the 2026-07-06 QFREEZE-2 block.
- `scripts/qualification_status_check.py --root .` derives
  `BLOCKED=0 NOT_RUN=21`; `P0` is `NOT_RUN`.
- `P0 = PASS` is a separate sealed-run gate. The freeze did not produce a sealed run,
  a result artifact, or a qualification `PASS`.

## Sealed-Run PASS Checklist

A future `P0 = PASS` requires all of the following, in this order:

1. Author a `qualification_result_v3` PASS artifact that conforms to
   `schemas/qualification/qualification_result.schema.json`.
2. The result artifact must have `status: PASS`, `completed_at`, future
   `expires_at`, `evidence_path`, `criteria_catalog_digest`, at least one
   `reviewers[]` entry with `independent: true`, and an
   `independent_reproducer` object with `independent: true`.
3. The result artifact must include `criterion_results` for every applicable
   non-`DIAGNOSTIC` P0 criterion. PASS permits only `PASS` or `N/A` rows; no
   `FAIL` or `BLOCKED` rows are allowed.
4. Every PASS criterion row must cite at least one existing repo-local evidence file.
5. Result identity must match `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`
   field-by-field: selected product scope, selected deployment profile, candidate
   commit, artifact digest, protocol version, targets version, vocabulary version,
   and criteria catalog digest. Candidate tag must also match if a tag is present.
6. Only after the result artifact exists and validates may the committed status
   change `qualifications.p0.status` from `NOT_RUN` to `PASS`, set
   `qualifications.p0.result_path`, and keep committed status, derived status, and
   the result file in agreement under `scripts/validate_qualification.py` and
   `scripts/qualification_status_check.py`.

## Never-N/A P0 Invariants

The following six P0 invariants must never be marked `N/A` for a P0 PASS. They must
pass with concrete evidence or the run cannot pass.

| Criterion | Statement | PASS requirement |
|---|---|---|
| `P0-004` | Sealed acceptance isolation | Acceptance cases remain sealed from the implementation and agent-visible fixture paths. |
| `P0-005` | Anti-contamination rule | The cohort is fresh and not drawn from test/golden fixtures or implementation-visible cases. |
| `P0-021` | Evidence integrity | Evidence paths, hashes, storage, and lineage are controlled and reproducible. |
| `P0-023` | Threshold immutability | Thresholds and pass rules remain fixed before and during the run. |
| `P0-027` | Qualification implementation integrity | Qualification tooling is itself controlled, validated, and not altered to force a PASS. |
| `P0-030` | Safety stop rule | Stop conditions fire on critical failures, source failures, contamination, or safety breaches. |

## No Existing Runner

The current `scripts/qualification_*.py` tools are read-only validators/checkers. They
derive or validate qualification state; they do not write a sealed P0 result artifact
and do not flip committed status. A result writer or sealed-run runner is greenfield
work.

## Owner-Independent Build Lane

The following engineering work can improve readiness but cannot flip `P0` to `PASS`.
Any such branch must hold at PR and must not edit `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`
`qualifications.p0.status` or `result_path`.

- Result-writer scaffold for a future `qualification_result_v3` artifact.
- Protocol preregistration machinery for `P0-003` against the already-frozen targets.
- Sampling frame, coverage matrix, and sample-size machinery for `P0-006`,
  `P0-007`, and `P0-008`.
- Statistical analysis support for `P0-009`, `P0-016`, and `P0-026`, including
  Wilson or exact intervals, AOI-clustered denominators, Holm-Bonferroni handling for
  secondary families, and fail-closed treatment for unknown/missing outcomes.
- Integrity and controlled-storage manifest machinery for `P0-021` and `P0-027`.
- Empty provenance-register machinery for `P0-005`, without populating a real cohort.

This lane can prepare the sealed-run path. It cannot satisfy the owner/infra decisions
below and cannot claim or record `PASS`.

## Decision Dependencies For PASS

The future PASS gate is blocked on new owner or infrastructure decisions. These are
part of the ODP-PRO-001 protocol/evidence authority family in
`state/owner-decisions.md` and must be recorded before a sealed run can pass.

| Dependency | Required decision | Why repo-local inference is insufficient |
|---|---|---|
| `P0-004` external restricted vault | Owner provisions `external_restricted_vault` storage for cases outside the agent-visible repo, or owner ratifies a re-parameterization. | A repo-local store cannot satisfy sealed acceptance isolation. |
| `P0-005` fresh non-fixture cohort | Owner authorizes AOI/case selection and provenance records for fresh cases. | Reusing `tests/fixtures/golden_aois` is an explicit anti-contamination failure. |
| `P0-012`/`P0-013`/`P0-014`/`P0-015`/`P0-025` reviewers | Owner appoints at least two qualified independent reviewers plus a standby adjudicator, with blinding, independence attestations, and IRR floor `>= 0.7`. | Reviewer identities, qualifications, independence, and conflict controls cannot be fabricated by implementation work. |
| `P0-022` independent reproduction | Owner appoints an independent second operator/reproducer and records the reproduction report. | The implementation author cannot self-reproduce qualification evidence. |
| Run authorization and status flip | Owner explicitly authorizes the sealed run and the later `NOT_RUN -> PASS` status update if evidence passes. | QFREEZE-2 froze parameterization only and forbids treating the freeze as a PASS. |

## Honest Flags

The following must never be faked or treated as engineering shortcuts:

- A golden-fixture cohort fails `P0-005`.
- A repo-local store is not the `P0-004` `external_restricted_vault`.
- Fabricated reviewers, reviewer qualifications, or attestations fail `P0-025` and
  related reviewer criteria.
- A fabricated independent reproducer fails `P0-022`.
- PASS-from-freeze is invalid; QFREEZE-2 produced `NOT_RUN`, not `PASS`.
- `expires_at` cannot be null or in the past for a PASS result.
- Threshold tuning during or after the run violates `P0-023` and invalidates the run.

## Net Decision

`P0 = PASS` is blocked on owner and infrastructure decisions, not on ordinary
implementation alone. Owner-independent scaffolding can proceed only as preparation;
it cannot record `PASS`, cannot change P0 status, and cannot substitute for ODP-PRO-001
authority, an external vault, a fresh cohort, appointed reviewers, or an independent
reproducer.
