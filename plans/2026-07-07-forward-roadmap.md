# Forward Roadmap — What Comes Next For The Whole Project

Status: `living-analysis` (Claude initial pass 2026-07-06; Opus adversarial pass appended below)
Basis: live `origin/main@26d8b134`. Evidence: `docs/IMPLEMENTATION_READINESS.md`,
`state/p0-sealed-run-decision-packet.md`, `tasks/task_queue.yaml`,
`state/EMPIRICAL_QUALIFICATION_STATUS.yaml`, `backend/app/connectors/`,
`state/owner-decisions.md`.

This file is a standalone, maintained analysis. Findings are appended/updated as they land.
It records **strategy**, not implementation authority — it changes no qualification value/status.

---

## 0. One-paragraph answer

The engineering scaffold is essentially built out for what can be built **owner-independently**
(layers 5–9 proven; L9-R private-MVP posture; DB spine proven; flood-only qualification frozen).
The project is now at an **owner-decision inflection point**: the two things that convert it from an
impressive-scaffold-on-fixtures into a *useful, trustworthy* product are both **owner-gated** — (B)
**real data** (live NC connectors + source approvals) and (A) **empirical qualification** (a sealed
P0 run → PASS). Everything else (UI, hosted production, schedulers, dossier polish) is secondary. The
highest-leverage sequence is three owner decisions: **C (pick the geography: NC vs Bologna) → B
(authorize live NC data) → A (commit the P0 sealed-run bundle)**, with owner-independent scaffolding
sequenced *after* the owner signals A rather than built speculatively now.

> **CORRECTED (post-Opus §6 — operative):** the strict C→B→A serialization above is *superseded*. The
> Opus audit established: (i) **A depends only on B-narrow** (a fresh real DS-002/FEMA flood cohort —
> already approved, credential-free) + owner AOI-selection + vault sealing — **not** on DS-017 or broad
> source approvals (a *parallel* B-full utility track); (ii) **A-prep should be built NOW**
> (owner-independent, packet-authorized, spec-frozen, hold-at-PR) — prereg/stats methodologically precede
> the cohort; (iii) the **full P0 run is a credibility/governance gate, not a user-value pillar** — it only
> *unseals* the Q1/Q2 accuracy/utility qualifications; the near-term **user-utility unlock is
> real-data-on-a-real-workflow** (+ the already-built caveat surface), and an **A-lite internal
> calibration** spot-check delivers most user-facing trust cheaply. Operative ordering: **C-lite (defer
> Bologna) ‖ [A-prep NOW + B-narrow + B-full parallel] → A-run → Q1→Q2→Q3 → A-expand.** Full reasoning in §6.

---

## 1. The three axes (conceptual frame)

The forward landscape is not one backlog; it is three orthogonal axes. Conflating them is the main
way prior sessions burned effort on diminishing-returns plumbing.

- **Axis A — Empirical Qualification (credibility / "is the output trustworthy?").** P0 = `NOT_RUN`
  (`BLOCKED=0 NOT_RUN=21`), frozen flood-only for DS-002. PASS is a *separate* sealed-run gate.
- **Axis B — Product / Utility (functionality / "does it produce real dossiers?").** NC private MVP
  (Buncombe, Chatham, Brunswick), currently on **fixtures only**. L9-R.
- **Axis C — Geography fork (strategy).** NC (built out) vs Bologna (fully externally blocked).

The product's *whole purpose* is trustworthy, cited, provenance-tracked land due-diligence. Today it
produces dossiers on **fixture** data that are **not empirically qualified**. Fulfilling the purpose
requires closing **both** A (qualification) and B (real data). The rest is polish.

---

## 2. Current floor (repo-confirmed)

- Qualification: `P0 = NOT_RUN`; flood-only frozen under `benjmcd` (QFREEZE-2); the freeze forbids PASS.
  No `qualification_result_v3` writer/runner exists (greenfield). Highest valid classification `L9-R`.
- Product: layers 5–9 (evidence ledger, claim/rule engine, report reproducibility, API façade,
  human-review) proven in-memory + DB spine proven under `RUN_DB_SMOKE`. Fixture connectors for
  minerals/broadband/env/water/geology/flood. DS-002 (FEMA NFHL) is the **only approved source**.
- Connector modules exist for live sources (`fema_nfhl`, `epa_echo`, `fcc_broadband`, `census_tiger`,
  `noaa_climate`, `nwi`, `blm_mlrs`, `nc_geologic_map`, county parcels) but are **not enabled** — live
  enablement is gated by the `IMPLEMENTATION_READINESS` **Stop Rule** (live creds / license review).
- `tasks/task_queue.yaml` = 154 done / 10 blocked / 1 active. All 10 blocked are owner/external
  authority: **5 EQ-freeze (non-Bologna)** (TARGETS/RUBRICS/DOMAINS/SOURCES/SCOPE-VERSIONS) + **5 Bologna**
  (4 EQ-BLOCK-BOLOGNA-* + BSA-001). Active = `AUTH-EVIDENCE-INTAKE` (validate-only routing).
- Hosted production / Level 10 blocked (OAuth/OIDC, registry publication, billing, external
  secret-manager) — deliberately out of the private-MVP gate.

---

## 3. The forward landscape — every lane

### Axis A — Empirical Qualification

**A-prep (owner-INDEPENDENT; hold-at-PR; must NOT flip `p0.status`)** — from packet §68–82:
- A1. `qualification_result_v3` result-writer scaffold (conforms to the result schema).
- A2. P0-003 protocol-preregistration machinery against the frozen targets.
- A3. Sampling frame / coverage matrix / sample-size machinery (P0-006/007/008).
- A4. Statistical machinery (P0-009/016/026): Wilson/exact intervals, AOI-clustered denominators,
  Holm-Bonferroni for secondary families, fail-closed unknown handling.
- A5. Integrity + controlled-storage manifest machinery (P0-021/027).
- A6. Empty provenance-register machinery (P0-005) — no real cohort.

**A-gate (owner/infra-gated)** — from packet §87–99, the ODP-PRO-001 family:
- A7. External restricted vault for sealed acceptance cases (P0-004) — repo-local store cannot satisfy.
- A8. Fresh non-fixture cohort (P0-005) — reusing `tests/fixtures/golden_aois` is an explicit FAIL.
- A9. ≥2 appointed independent reviewers + standby adjudicator, blinding, attestations, IRR ≥ 0.7
  (P0-012/013/014/015/025).
- A10. Independent second-operator reproducer + report (P0-022).
- A11. Explicit run authorization + `NOT_RUN → PASS` status-flip authorization.

**A-expand (owner-gated) — beyond flood:** EQ-BLOCK-TARGETS / RUBRICS / DOMAINS / SOURCES /
SCOPE-VERSIONS (freeze non-flood qualification for the other 7 domains + source-quality profiles;
0 source profiles approved today).

### Axis B — Product / Utility (NC private MVP)

**B-eng (owner-INDEPENDENT; the `IMPLEMENTATION_READINESS` "Recommended Next Passes"):**
- B1. Authority pass — keep `MILESTONE_MAP.md`/`LANE_OWNERSHIP.md`/state current; `render_project_status.py` runnable.
- B2. API contract hardening — OpenAPI as runtime authority; `REPORT_AUTH_MODE=signed_token` before beta; trusted-header enforcement.
- B3. Report-job scheduling **decision** — bounded operator/API execution vs scheduler/daemon.
- B4. Dossier surface expansion — Markdown dossier + safe-language lint; Operator Path Proof Matrix before PDF/dashboard/UI.
- B5. Legacy/null-ownership **decision** — backfill vs stay inaccessible.

**B-gate (owner-gated):**
- B6. Live-connector enablement for selected NC counties (creds + license review — **Stop Rule**).
- B7. Source approvals — EQ-BLOCK-SOURCES (0 approved; needs exact sources, rights, cache/export/AI/raw permissions, coverage, freshness).
- B8. DS-017 — commercial parcel vendor (the one blocked "Must" source): license/cost/terms decision.
- B9. Hosted production / Level 10 — OAuth/OIDC, registry publication, billing, external secret-manager (only after private-MVP utility proven).

### Axis C — Bologna fork (owner-gated, strictly sequenced)

- C1. ODP-BOL-001 pilot product/AOI scope → C2. ODP-BOL-002 source rights → C3. ODP-BOL-003 recorded corpus → C4. ODP-BOL-004 DB-backed report proof. Plus BSA-001 source-authority intake. **None can start without cited owner authority, in order.**

### Cross-cutting (owner-independent, low-stakes)

- X1. F4 — provenance-guard decision (forbidden-fragment CI guard vs process-enforcement); tracked in PROJECT_STATE + VALIDATION_LOG.
- X2. CI — rec 2 (push→main restriction, needs owner + dispatch convention), rec 4 (mypy cache, optional), rec 9 (buildx cache, deferred on 10 GB LRU).
- X3. Workspace debt — orphaned worktree dirs; ~1.1 GB; OneDrive-lock cleanup.

---

## 4. Prioritized decisions (initial call — SUPERSEDED by §6 REVISED PRIORITIZATION)

> The C→B→A ranking below is the initial pass, retained for the reasoning trail. **The operative plan is
> §6 REVISED PRIORITIZATION** — A is decoupled from B-full, A-prep moves to a *now* lane, and the P0-run
> is reframed as a credibility gate rather than a user-value pillar. Read §6 as authoritative where it
> and §4 differ.

Ranked by leverage on the project's *purpose* (trustworthy real dossiers), with justification.

### Priority 1 — Decision C: pick the geography. **Recommend: commit NC, defer/close Bologna.**
- **Why first:** cheapest owner decision; it *focuses* all subsequent authority. Bologna is 100%
  externally blocked (C1–C4 + BSA-001, strict order, zero started); NC is the built-out line (3
  counties selected, connectors present, fixtures proven). Splitting owner authority across two
  geographies is the dominant efficiency leak (prior sessions + memory flagged "stop Bologna
  scaffolding, deepen NC").
- **Cost:** one owner directive. **Value:** unblocks focused sequencing of B and A.

### Priority 2 — Decision B: authorize live NC data. **The utility unlock.**
- **Why:** today's dossiers run on fixtures — demos, not real diligence. Real data (B6 live connectors
  + B7 source approvals + B8 DS-017) is what makes the product *do its job*. It is also a **prerequisite
  for a meaningful A**: P0-005 requires a *fresh non-fixture cohort*, which needs real AOIs/evidence →
  live data must exist before qualification is meaningful.
- **Cost:** owner license/cost/terms decisions + license review (Stop Rule). **Value:** highest —
  converts scaffold → working product.

### Priority 3 — Decision A: commit the P0 sealed-run bundle. **The credibility unlock.**
- **Why:** turns "runnable" into "qualified/trustworthy" — the core value proposition. But it is the
  **heaviest** (external vault, fresh cohort, ≥2 independent reviewers + adjudicator, independent
  reproducer, ODP-PRO-001). It depends on B (fresh cohort needs real data).
- **Cost:** owner supplies an infrastructure + personnel bundle, not a diff. **Value:** highest *trust*,
  but sequenced after B.

### Owner-independent prep — sequence *after* the owner signals A, not before.
- A-prep (A1–A6) is legitimate engineering but **speculative** until the owner commits to a run
  (YAGNI + the repo invariant "do not extend diminishing-returns plumbing absent cited owner
  authority"). Build the result-writer + prereg + sampling/stats + integrity **once Decision A is
  signaled** — then it is on the critical path, not busywork.
- B-eng (B1–B5) is low marginal utility *without* live data — do opportunistically, not as a priority.

---

## 5. Specific next steps (concrete, per branch of the decision tree)

- **If owner picks NC + commits to live data (recommended path):**
  1. Owner records geography=NC directive (closes/defers Bologna EQ-BLOCK-BOLOGNA-* + BSA-001).
  2. Owner authorizes DS-017 + the NC source approvals (EQ-BLOCK-SOURCES) with license review.
  3. Codex lane: enable live connectors for the 3 counties behind the Stop-Rule gate; capture a fresh
     non-fixture cohort → this becomes the P0-005 cohort.
  4. Owner supplies the A-gate bundle (vault, reviewers, adjudicator, reproducer, run auth).
  5. Codex/Claude lane: build A-prep (result-writer, prereg, sampling/stats, integrity) — now
     critical-path.
  6. Execute the sealed run → author `qualification_result_v3` → owner authorizes `NOT_RUN → PASS`.
- **If owner picks Bologna:** everything reroutes through C1→C4 (strict order); NC live-data work pauses.
- **If owner defers all three:** the honest state is *hold* — no owner-independent lane adds
  proportionate value; do only X1/X2 hardening opportunistically.

---

## 6. Adversarial workflow findings (Opus)

### Verdict on the roadmap
§1–§5 are directionally sound and unusually well-evidenced. The three-axis frame (A qualification / B utility / C geography), the owner-decision inflection, the flood-only QFREEZE-2 floor, and "stop extending diminishing-returns plumbing" all survive adversarial cross-check and independent re-verification (`qualification_status_check.py` → `BLOCKED=0 NOT_RUN=21`; HEAD `26d8b134`; `task_queue` 154/10/1; `fema_nfhl_live` is a genuine `urlopen` connector gated off by `config.py:51`; DS-002 is the sole approved source per `owner-decisions.md`). **But the roadmap's central sequencing rationale is materially wrong on three load-bearing points**, and each drives a wrong decomposition: (1) it treats *all of B* — including the blocked commercial parcel vendor DS-017 — as a strict prerequisite for A, when A depends only on a narrow, already-approved, credential-free real-FEMA slice; (2) it holds A-prep as "speculative," when the decision packet explicitly authorizes it as owner-independent, its spec is frozen, and preregistration/stats machinery *methodologically must precede* the cohort; (3) it ranks the full P0 sealed run as a co-equal pillar of user value, when P0 is a downstream institutional-credibility gate that adds ~zero marginal utility to any individual dossier and only *unseals* the Q1/Q2 accuracy/utility qualifications the roadmap omits entirely. The skeleton (C-first, NC-first, A+B are the real unlocks) is defensible; the **strict C→B→A serialization and the A-as-top-value ranking are not**. Fix the sequencing and value-framing and the roadmap is correct.

### CONFIRMED (held under adversarial attack)
- **"Built out owner-independently" is not an overstatement.** Layers 5–9 present and DB-report path proven byte-identical under `RUN_DB_SMOKE` (PR #188); §0–§2 keep the "fixtures-only / not-qualified" hedge adjacent throughout. Keep that hedge attached to any future "built out" phrasing so it is never quoted standalone.
- **P0 = NOT_RUN, flood-only frozen, freeze forbids PASS, greenfield writer/runner, L9-R.** Independently reproduced (`BLOCKED=0 NOT_RUN=21`); packet §99 "QFREEZE-2 froze parameterization only and forbids treating the freeze as a PASS."
- **Live connectors are real-but-unenabled.** `fema_nfhl.py:32,490` is a live HTTP connector against the public federal NFHL endpoint, gated OFF by `enable_live_connectors: default=False` (`config.py:51`). Not a fixture stub.
- **DS-002 is the only approved source; 0 source-quality profiles approved.** `owner-decisions.md:24,46,115`. These are distinct concepts (approved *data source* = DS-002; approved *source-quality profiles* = 0, EQ-BLOCK-SOURCES) — not a contradiction.
- **B genuinely gates a *meaningful* A via P0-005.** Packet §55/§96/§105: a golden-fixture cohort is an explicit anti-contamination FAIL. A cannot be executed on fixtures — it is strictly downstream of *some* real cohort. (This is the true kernel the roadmap over-generalized into "all of B before A" — see Correction 1.)
- **The A-prep↔packet §68–82 and A-gate↔packet §87–99 line-citation mapping is exact**, including the external-vault / ≥2-reviewer+adjudicator / IRR≥0.7 / independent-reproducer / run-authorization bundle.

### CORRECTIONS (ranked, with the fix to §1–§5)

**1 — [Critical] B is NOT a strict prerequisite for A. Split B; only a narrow DS-002 cohort is on A's critical path.**
Qualification is frozen flood-only (`owner-decisions.md:80-81`), sourced from DS-002 — a public FEMA service whose entitlement is "not-applicable / no key/seat" and which is already "approved for MVP flood screening" (`docs/source-reviews/ds-002.md:63,67`); the `fema_nfhl_live` connector already exists credential-free. DS-002 does not even trip the IMPLEMENTATION_READINESS Stop Rule's "requires live credentials/vendor access" clause. DS-017 (commercial *parcel* vendor) and the broad B7 source-approval batch are **flood-irrelevant** — flood qualification measures FEMA flood-zone screening, not parcels. **Fix §1/§4:** split B into **B-narrow** (a fresh real DS-002/FEMA cohort + owner AOI-selection + external-vault sealing authority — the *actual* P0-005 prerequisite) vs **B-full** (DS-017 + multi-domain source approvals + full multi-county connector enablement + user-access — a parallel product-utility track). Strike DS-017 and general source approvals from A's dependency chain. Note the cohort can be an **owner-supplied recorded real-FEMA corpus sealed in the vault** (the pattern already used for Bologna BRC-001), so even B6 live-connector *enablement* is not strictly required — the true gate is owner AOI-selection + vault sealing, an A-gate governance decision.

**2 — [Significant] The full P0 run is a governance/credibility gate, not a co-equal pillar of user value; and P0 PASS only *unseals* accuracy/utility.**
`EMPIRICAL_QUALIFICATION_STATUS.yaml` shows `q1` prereq `[p0]`, `q2` prereq `[p0,q1]`, `q3a/b/c` prereq `[p0,q1,q2]`, all NOT_RUN. P0 is the integrity/anti-contamination gate that *unseals* Q1 (accuracy: `critical_issue_recall=1.0`, false-positive ceilings) and Q2 (user-utility: decision-concordance/usefulness/time-reduction) — it proves the run was *clean*, not that dossiers are *accurate* or *useful*. AGENTS.md itself frames qualification as the "canonical empirical-VALIDITY authority / CI-deployment gate" — governance, not the thing a user reads. The user-facing trust surface (`reports/dossier.py`: screening disclaimers, suitability-vs-confidence bands, "legal access: not determined," cited-evidence + required-verification columns) is *already built* and independent of any sealed run. **Fix §1/§4:** stop calling A "the core value proposition." Reframe: a flood P0 PASS delivers *institutional/defensible* credibility for flood screening and *unseals* Q1/Q2; it is necessary for marketable trust claims but adds ~zero marginal utility to an individual dossier. The near-term *user-utility* unlock is real-data-on-a-real-workflow (Debate iv).

**3 — [Significant] Build A-prep NOW (hold-at-PR); do not hold it as speculative.**
Packet §68–82 explicitly names A-prep an "Owner-Independent Build Lane" that "can prepare the sealed-run path"; the stats/protocol spec is already FROZEN (`owner-decisions.md:84-88`: Wilson/exact, AOI-clustered denominators, Holm-Bonferroni, fail-closed); it is geography-agnostic (serves NC *or* Bologna); the owner-independent frontier is otherwise exhausted (154/10/1). Methodologically, **preregistration (A2, P0-003) and threshold/stats machinery (A3/A4) MUST be built before the cohort is drawn** to satisfy P0-003 and P0-023 threshold immutability — deferring them "until the owner signals A" risks doing prereg too close to cohort selection. The packet calls the runner "greenfield / no existing runner" (§62) — net-new critical-path capability, categorically *not* the validate-only churn the "diminishing-returns plumbing" invariant targets; and the packet IS the cited owner authority that invariant demands. **Fix §4:** move A-prep out of "sequence after the owner signals A" and into a **now** lane — sequence **A2 prereg + A3/A4 stats first**, then A1 writer + A5 integrity + A6 empty provenance-register — under P0-027 controlled-tooling discipline and a hard **hold-at-PR guardrail: must NOT flip `p0.status`/`result_path`, seal a run, or draw a cohort.** (Honest caveat: this is cold inventory only in the single scenario where the owner never runs P0 at all; geography choice does not waste it.)

**4 — [Significant] Disclose the flood-only ceiling: even the full A bundle qualifies 1 of 8 domains.**
`qualification_targets.yaml:19-20,32-48` — `qualified_domains:[flood]`; wetlands, slope_terrain, soils_septic_proxy, physical_road_access_proxy, zoning_context, environmental_context all explicitly unqualified — and the dossier *reports* on those unqualified domains (golden stress set: `bun_slope`, `bru_wetlands_soils`, `cha_zoning_edge`). **Fix §1/§4:** state plainly that even after the full A bundle the dossier remains "flood-qualified + ~6 screening domains and all legal domains unqualified"; whole-product trust requires **A-expand** (freeze the other 7 domains) plus a repeated Q1 accuracy run per newly-frozen domain. Re-rank A-expand as on the critical path to *product* trust, not a tail item.

**5 — [Minor] §2 blocked-lane miscount: 5 EQ-freeze + 5 Bologna, not "6 EQ-freeze + 4 Bologna."**
`task_queue.yaml`: 5 non-Bologna EQ-freeze (EQ-BLOCK-TARGETS/RUBRICS/DOMAINS/SOURCES/SCOPE-VERSIONS) + 4 EQ-BLOCK-BOLOGNA-* + **BSA-001** (title "Bologna source-authority intake") = **5 Bologna**. §2 mislabels BSA-001 as EQ to reach 6+4, and contradicts the roadmap's own §3. **Fix §2:** "5 EQ-freeze (non-Bologna) + 5 Bologna (4 EQ-BLOCK-BOLOGNA-* + BSA-001)."

**6 — [Minor] The A-lane silently drops 2 of the packet's 6 never-N/A P0 invariants.**
Packet §47-59 defines six: P0-004/005/021/023/027/030. A-prep/A-gate surface 004/005/021/027 but never name **P0-023** (threshold immutability) or **P0-030** (safety stop rule). **Fix §3:** add a one-line reference to the six-invariant table, noting P0-023 is *pre-satisfied* by the QFREEZE-2 threshold freeze (`owner-decisions.md:88`) but **P0-030 (stop-rule firing on critical/source-failure/contamination) is real engineering that belongs in A-prep** — so the PASS-gate list is not read as complete without it.

**7 — [Minor] Reframe Decision C: it is "close-or-defer Bologna," not "pick the geography"; and defer, don't close.**
NC is *already* the selected private-MVP geography (`IMPLEMENTATION_READINESS.md:21-22,91`), so "pick the geography" overstates an open decision and over-ranks C as #1 leverage. NC-first is genuinely evidence-based (frozen NC/US flood scope; every connector is US/NC-federal; zero Bologna connectors/fixtures) — not mere inherited bias. But "close Bologna" over-reaches: Bologna is an active owner-gated line **owned by the Codex lane under the dual-agent fence** (memory 2026-06-28), and the roadmap performs *no demand/market assessment* — if owner value is Bologna, NC-readiness is a sunk-cost argument. **Fix §4 Priority 1:** reframe C as "**defer** the dormant Bologna fork, keep it Codex-owned, pending an explicit owner geography/demand directive," and demote it below B-narrow + A-prep as the operative unlocks.

**Rulings on the four load-bearing debates:**
- **(i) Is B a strict prerequisite for A?** **No.** Only **B-narrow** (a fresh real DS-002/FEMA flood cohort — already approved, credential-free, optionally a sealed recorded corpus) plus owner AOI-selection/vault authority is on A's critical path. B-full (DS-017 + broad approvals + full connector enablement) is a *parallel* utility track, not an A predecessor.
- **(ii) Hold A-prep vs build now?** **Build now**, hold-at-PR. It is owner-independent (packet-authorized), spec-frozen, geography-agnostic, the frontier is exhausted, and prereg/stats *must* precede the cohort. The only guardrail: no status flip, no seal, no cohort.
- **(iii) NC vs Bologna evidence?** **NC-first is evidence-based** on frozen-state + connector grounds. But "pick the geography" is already decided and "close Bologna" oversteps the Codex fence and the (absent) demand axis — the defensible form is **"defer Bologna, keep Codex-owned."**
- **(iv) Is qualification necessary for user utility, or is real-data-on-a-real-workflow the true unlock?** **Real-data-on-a-real-workflow (+ the already-built caveat surface) is the near-term user-utility unlock.** The full P0 run is the *institutional-credibility* gate — necessary for defensible/marketable trust claims, but not for a single user to derive utility from cited-evidence-plus-caveats, and it cannot even begin until B-narrow lands. Corrected value ranking for a first real user: **B-narrow real data + user-access ≫ A-lite calibration evidence ≫ full P0 (A) ≫ A-expand.**

### MISSED LANES (add to §3)
- **Axis A — the Q1→Q2→Q3 ladder** (add after the P0 family). The qualifications that actually deliver output-accuracy (Q1) and proven usefulness (Q2); all NOT_RUN with `prerequisites:[p0…]`. §5 currently terminates the entire credibility axis at P0 — it must continue P0→Q1→Q2. **Critical.**
- **Axis A — "A-lite" internal calibration lane** (owner-independent). An informal accuracy spot-check of tool flood determinations vs authoritative FEMA/NFHL determinations on a small sample, reported *as evidence and explicitly labeled non-qualifying*. Permitted — AGENTS.md forbids *claiming* PASS from repo-local inference, not *measuring* internal accuracy — and it substantiates the confidence bands the dossier already exposes, delivering most user-facing trust at a fraction of the P0 cost. (Contingent only on a handful of real-FEMA lookups, which do not trip the Stop Rule.)
- **Axis B — user-access enablement** (reclassify from "polish"). Split **pilot-user** (owner/operator on fixtures — a genuine end-to-end demo is shippable TODAY with neither A nor B; `test_operator_approved_path.py` + `ui.py:3301`) vs **external-user** (needs hosted deploy + arbitrary-parcel intake, which only yields real evidence when `enable_live_connectors` is on — `intake.py:114,176`). If external users are ever a goal, hosted/intake is on the critical path, not the tail.
- **Axis A/B — pre-beta security lane.** The `security_privacy` overlay is NOT_RUN for `LOCAL_SINGLE_USER` and `qualification_targets.yaml:163-170` requires an independent security review pre-beta. File it as a distinct owner/infra-gated lane, not a hosted-only (B9) tail item.
- **B6 sub-items:** (a) **retention/privacy** — define the retention class + purge cadence for the fresh live cohort (`data_retention.yaml` marks automated deletion BLOCKED / dry-run purge) as a *precondition* of live enablement; (b) **live-data reproducibility hardening** — source-version-pinned runs + source-version-aware rerun/diff, so "reproducible" survives the transition from committed fixtures to drifting live sources.
- **Demand/wedge validation** (or surface Q2 as the utility-proof gate) BEFORE committing the heaviest owner bundle (vault + reviewers + adjudicator + reproducer). Do not spend the P0/reviewer bundle before confirming a flood-only screening product changes a real buyer's decision.

### REVISED PRIORITIZATION (supersedes §4 — the strict C→B→A serialization should NOT be adopted as written)
The skeleton holds (C-first instinct, NC-first, A and B are the real unlocks), but A must be **decoupled from B-full** and A-prep pulled forward. Corrected ordering:

0. **C-lite (owner, cheap): defer Bologna, confirm NC active.** Not "pick the geography" (already selected) — just close-or-defer the dormant fork; keep it Codex-owned.
1. **In parallel from now:**
   - **A-prep NOW** (owner-independent, hold-at-PR): A2 prereg + A3/A4 stats first, then A1 writer + A5 integrity + **A6 provenance-register + P0-030 stop-rule**. No status flip, no seal, no cohort.
   - **B-narrow** (owner): authorize a fresh real DS-002/FEMA flood cohort (public, credential-free, already approved — or a sealed recorded corpus) + owner AOI-selection + external-vault sealing. This is the *actual* A-prerequisite.
   - **B-full utility** (owner, parallel track — *not* an A predecessor): DS-017 + broad source approvals + multi-county connector enablement + user-access (hosted/intake). Its long pole (DS-017 license/cost/terms) is orthogonal to A's long pole (reviewer/vault/reproducer bundle), so the two owner asks proceed independently — A may even be reachable *before* B-full.
2. **A-run:** cohort + A-gate personnel/vault assembled → execute sealed run → author `qualification_result_v3` → owner authorizes `NOT_RUN → PASS`. Unlocks Q1.
3. **Q1 → Q2 → Q3:** the accuracy and user-utility qualifications (the real trust/utility proof) — currently omitted from §3.
4. **A-expand:** freeze the other 7 domains + repeat Q1 per domain for whole-product trust.

Justification: A decouples from B-full (Debate i), so serializing A strictly after all of B over-gates the credibility axis on a commercial vendor unlock that flood qualification does not need; A-prep is owner-independent and methodologically precedes the cohort (Debate ii); and the near-term user unlock is real data on the existing workflow, not the sealed run (Debate iv). Decompose by **critical path to the flood-only PASS**, not by axis.

### Residual uncertainty / owner-only calls
- **Geography is a genuine owner call the roadmap pre-judges.** NC-first is engineering-defensible but *not proven strategically correct* — the roadmap assesses no demand/market/owner-intent axis. If owner value is Bologna, NC-readiness is sunk cost. (Defer, don't close.)
- **Whether external users are ever a goal** — determines if hosted-deploy + arbitrary-parcel intake is critical-path or genuinely deferrable.
- **Whether to spend the heavy P0 reviewer/vault/adjudicator/reproducer bundle before Q2/demand validation** confirms a flood-only product changes a buyer's decision.
- **P0-005 cohort delivery mechanism** — live-connector enablement vs owner-supplied sealed recorded-FEMA corpus; both satisfy freshness, both require owner AOI-selection + vault sealing.
- **DS-017 license/cost/terms** — genuinely external/commercial; blocked until source/vendor authority changes.
- **Dual-agent coordination** — "close/defer Bologna" touches the Codex-owned lane; sequence via the agent-inbox rather than unilaterally.
- **The A-prep "build now" call assumes the owner will eventually commit to a P0 run** — the one scenario in which the (geography-agnostic, spec-frozen) machinery is cold inventory. Judged worth building given the frontier is otherwise exhausted; revisit if the owner signals indefinite deferral of all three decisions.

---

## 7. Owner decisions 2026-07-06 (relay-delivered) — Bologna-centric revision (SUPERSEDES the geography/user/timing calls in §4–§6)

The owner resolved the three "owner-only" questions this session (delivered via orchestrator handoff — relay-delivered; recorded in `state/owner-decisions.md`). These reorient the operative plan.

**Decision 1 — Geography = Bologna, Italy.** This *inverts* §6's "defer Bologna, NC-first." The **live product line is Bologna**. Consequences (repo-grounded):
- The NC/flood QFREEZE-2 qualification (`qualified_domains:[flood]`, DS-002) becomes a **frozen reference / proof-of-method** — it proves the architecture end-to-end but is **not the target**. It stays frozen; no unfreeze, no change.
- Bologna is its **own qualification line**, blocked at **ODP-BOL-001** (owner defines pilot product/AOI/scope) → ODP-BOL-002 + BSA-001 (source rights) → ODP-BOL-003 (recorded corpus) → ODP-BOL-004 (DB-backed report proof), **strict order, all owner-gated** (`task_queue` EQ-BLOCK-BOLOGNA-* + BSA-001).
- Zero Bologna connectors/fixtures exist; the US/NC-federal connectors (FEMA/EPA/FCC/census/etc.) **do not serve Bologna**. Bologna sources are a fresh ODP-BOL-002 batch.
- The owner-answer **intake machinery already exists** (ODGAV milestone, `scripts/bologna_owner_answer_evaluator.py`, PR #167) — it is waiting only on owner *answers* (ODP-BOL-001 content). There is nothing to *build* to unblock Bologna; it is purely owner-input-gated.

**Decision 2 — External users are never a goal.** Private/operator use only. Consequences:
- **Drop from the current product target:** hosted production / Level 10 (OAuth/OIDC, registry publication, billing, external secret-manager — old B9), arbitrary-parcel external intake, and external-user access are out of the current product target (dropped from scope unless a later owner reversal); the existing hosted/Level-10 blockers and checkers stay intact and are not deleted or relaxed by this decision.
- **Security/privacy qualification is NOT waived** (corrected per Codex state/qualification review). No external users removes the external-beta *deployment* surface, but the frozen `security_privacy` target keeps `independent_security_review_required: true` (`qualification_targets.yaml:163-170`) and `security_privacy_compliance.status: NOT_RUN` (`EMPIRICAL_QUALIFICATION_STATUS.yaml:73-75`); `owner-decisions.md:93` froze only the local single-user rate-limit/quota profile, not the security-review obligation. The qualification obligation **stands**; only the external-beta deployment context is removed. (A product-direction decision cannot relax a frozen qualification target — consistent with §7's "changes no qualification value or status.")
- The user-utility unlock (§6 Debate iv) collapses to the **operator** path (already shippable on fixtures); "external-user" half of the B-eng user-access lane is closed.

**Decision 3 — P0 reviewer/vault bundle timing: owner DELEGATED the determination to the orchestrator; orchestrator determined DEFER.** Reasoning (grounded):
1. The frozen qualification is NC/flood/DS-002 — a *different geography* from Bologna. Spending the heavy bundle (external vault + ≥2 independent reviewers + adjudicator + independent reproducer) on the NC-flood P0 qualifies a **non-target line**.
2. Bologna qualification is *far* — blocked behind ODP-BOL-001→004 (all owner-gated). The eventual P0 run is many owner-steps away, not near-term.
3. No external users → the bundle's payoff is *owner-operator* confidence (not marketable credibility), assessable against the owner's own use — genuinely deferrable.
4. Building A-prep now is also premature: target-specific prereg/sampling (A2/A3) are parameterized by the NC-flood targets and **do not transfer** to Bologna's; agnostic parts (A1/A4/A5/P0-030) would sit cold until Bologna nears its freeze — the "diminishing-returns plumbing absent cited authority" invariant applies.

**Determination: DEFER the heavy P0 bundle; do NOT speculatively build A-prep now.** The bundle awaits the *Bologna* qualification (post ODP-BOL-004 + a Bologna freeze), where it qualifies the real target. Build the geography-agnostic A-prep (result-writer, generic Wilson/Holm-Bonferroni stats, integrity manifests, P0-030 stop-rule) **only when the Bologna line nears its freeze** — not now.

### Revised operative plan (Bologna-centric)
1. **ODP-BOL-001 (owner) — THE live-line unblock.** Define Bologna pilot product, one-AOI boundary, operator/use-case, non-goals, stop conditions, jurisdiction boundary, evidence-only/rulepack scope. Feed answers to the existing ODGAV intake. *Nothing downstream can start without it.*
2. ODP-BOL-002 + BSA-001 (owner) — exact Bologna source rights (schema/license/cache/export/AI-use/raw-data/attribution).
3. ODP-BOL-003 (owner-gated capture) — recorded-source + source-failure fixture corpus for the one AOI.
4. ODP-BOL-004 — one DB-backed Bologna report proof (Codex lane; the ODGAV/report machinery pattern exists).
5. **Bologna qualification freeze** (owner-authorized, like QFREEZE-2 but Bologna-parameterized) → then build target-specific + agnostic A-prep → assemble the heavy bundle → **Bologna P0 run** → Q1→Q2→Q3.

NC/flood stays the frozen reference throughout. **Owner-independent work available right now: effectively none of high value** — the Bologna line is owner-input-gated at ODP-BOL-001, and the intake machinery is already built. The single highest-leverage action is the owner's ODP-BOL-001 scope decision.

### Dual-agent note
Bologna is the **Codex-owned lane** under the fence. This revision was drafted by the orchestrator (Claude) and is routed through Codex (state/qualification lane) for review before commit; the ODP-BOL-* execution belongs to Codex.
