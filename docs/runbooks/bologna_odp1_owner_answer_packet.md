# Bologna ODP-BOL-001 Owner Answer Packet

Schema: `bologna_odp1_owner_answer_packet_v1`

This runbook is validate-only. It records review-only scope pursuit through
`odp-bol-001-scope-pursuit-2026-06-26`, but it does not record pilot-scope authority,
select a Bologna AOI, approve sources, change source rights, capture fixtures, seed the
database, create runtime/report artifacts, approve DS-017, or claim hosted/Level 10
authority.

Use this packet to track the owner response for `ODP-BOL-001`. The packet collects the
owner-answer template, pilot-scope authority-record template, required scope-decision
checklist, allowed outcomes, downstream blockers, and no-overclaim controls in one
machine-checked place.

Run:

```powershell
.\scripts\run_bologna_odp1_owner_answer_packet_check.ps1
```

The checker verifies alignment with:

- `config/bologna_owner_answer_intake.yaml`
- `config/bologna_odp1_owner_response_gate.yaml`
- `config/bologna_pilot_scope_authority.yaml`

The committed state contains one `current_owner_answers` entry and matching
`current_owner_answer_references` entry for review-only scope pursuit. It must keep
`current_authority_records` and `current_authority_record_references` empty. Every
`downstream_updates_allowed` field remains false.

A future owner response may choose `approve_with_cited_authority`, `keep_blocked`,
`approve_review_only`, or `exclude_or_defer`. None of those outcomes authorizes
source approval, source-rights approval, recorded corpus work, fixture capture, DB
mutation, report proof, hosted deployment, or Level 10 claims in this packet.

If the owner supplies complete cited pilot-scope authority, record it only in a later
dedicated authority slice that updates the owner-answer intake and pilot-scope
authority packet together with focused validation.
