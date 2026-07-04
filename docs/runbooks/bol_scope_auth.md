# Bologna Scope Authority Readiness

Schema: `bol_scope_auth_v1`

This runbook is validate-only. It proves the current `ODP-BOL-001` answer is
review-only and cannot record pilot-scope authority, select a Bologna AOI, approve
sources, change source rights, create a recorded-source corpus, capture fixtures, seed
the database, create report artifacts, approve DS-017, claim hosted readiness, or claim
Level 10 authority.

Run:

```powershell
.\scripts\run_bol_scope_auth_check.ps1
```

For operator-facing collection, the same wrapper accepts reporting-only output modes:

```powershell
.\scripts\run_bol_scope_auth_check.ps1 --summary
.\scripts\run_bol_scope_auth_check.ps1 --json
```

The summary and JSON views report the current blocked state, required owner-answer
fields, required pilot-scope authority-record fields, required scope decisions,
downstream gates that remain blocked, and no-overclaim controls from committed
config only. They do not write artifacts, record authority, select an AOI, approve
sources, or request downstream unlocks.

The checker verifies alignment with:

- `config/bologna_owner_answer_intake.yaml`
- `config/bologna_odp1_owner_response_gate.yaml`
- `config/bologna_odp1_owner_answer_packet.yaml`
- `config/bologna_pilot_scope_authority.yaml`

The committed state must keep
`odp-bol-001-scope-pursuit-2026-06-26` as an `approve_review_only` owner answer and
must keep `current_authority_records` empty. The future promotion path requires a new
or superseding owner answer with `answer_type: approve_with_cited_authority`, plus a
pilot-scope authority record covering every required scope decision.

The future authority record must cite artifacts, caveats, and stop conditions; it must
request no downstream unlocks. Even after a valid ODP-BOL-001 promotion, ODP-BOL-002
source authority and rights, ODP-BOL-003 recorded-source corpus authority, and
ODP-BOL-004 DB-backed report proof remain separate decisions.

Do not bundle source, source-rights, corpus, fixture, DB, report, API, hosted, or
Level 10 changes with this gate.
