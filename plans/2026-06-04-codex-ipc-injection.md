# Codex Live IPC Injection (Claude Code -> live Codex Desktop session)

**Status:** WORKING / GUI-CONFIRMED / EXPERIMENTAL. Phases 0-5 are implemented on the authorized test thread and
`--ipc` is wired as an opt-in path with file-drop fallback. The owner-gated
`thread-follower-start-turn` route forwards an external client's turn to the owning Desktop
renderer; renderer handling and model replies are proven. Isolation is proven for the recorded
tests (global config byte-identical; no unexpected non-target thread changed). Renderer DERIVES
turn params, so external model/effort overrides are not honored. That means the original
model/effort-pinning subgoal is not achievable through this route, but Claude's input also cannot
change a thread's model/reasoning. User GUI-visible behavior was later confirmed by the user after
the Claude run. A read-only post-update revalidation wrapper now checks local IPC prerequisites and
can optionally re-prove router `initialize` without sending a prompt. New-session targeting now has
a read-only thread locator for workspace/project candidate discovery before inspection, and
`scripts/codex_ipc_write_proof.mjs` provides a dry-run-first controlled write re-proof harness for
future Desktop update/drift events.
**Supersedes:** the exec-targeting portion of `.omc/plans/codex-handoff-hardening.md` (the
"resume a session via `codex exec`" idea is proven incapable of GUI visibility — see Current state).
**Owner interface unchanged:** `./scripts/handoff_to_codex.sh "task"` stays the entry point.

---

## Goal

Programmatically inject a message into a **live Codex Desktop session** so that:

1. It appears in the Codex Desktop **GUI** (the chat the user is actually looking at), with no
   manual paste step.
2. The injected turn is scoped to exactly one explicit `conversationId` and cannot alter global
   config or other sessions.
3. It has **provably zero effect** on any other running Codex session — especially no change to
   any other session's selected model or reasoning level, and no change to global config.

Evidence correction: the original plan expected per-thread model/reasoning pinning through
`turnStartParams`. Live testing showed the owning renderer derives those params and ignores
external model/effort overrides. Treat this as a safety property, not as a completed pinning
feature.

This removes the one manual step in the shipped file-drop path (Phase 0): today the user must
paste `read state/agent-inbox/for-codex.md and proceed` into their session. The end state is a
`--ipc` mode that delivers the handoff straight into the live GUI thread.

## Non-goals

- Replacing file-drop. File-drop remains the **safe default and fallback**; `--ipc` is opt-in
  and must fall back to file-drop on any failure.
- Modifying `~/.codex/config.toml` or any global setting (forbidden — would affect other sessions).
- Writing to the Desktop app's SQLite store directly (forbidden — corruption/contention risk).
  All state changes must go **through the app-server protocol**.
- A general-purpose Codex automation framework. Scope is the Claude Code -> Codex handoff bridge.
- Any change to the land-diligence product code, schema, or reports.

## Current state

### Current audit corrections (2026-06-04 re-audit)

- Generated protocol artifacts under `local_artifacts/` are ignored local evidence, not source
  files or durable contracts. Re-run schema generation after any Codex CLI/Desktop update.
- `turn/start` is the relevant existing-thread turn method. `thread/start` creates/starts a
  thread and is not part of the one-live-thread handoff path unless a later plan explicitly
  chooses new-thread creation.
- `thread/inject_items` is not yet approved as the first write. The generated type accepts
  `items: Array<JsonValue>` and describes them as raw Responses API items. Until a valid,
  minimal item payload is proven from protocol evidence or a read-only thread sample, and unless a
  direct app-server endpoint is found, `thread/inject_items` remains unavailable for the proven
  router path.
- Generated `turn/start` model/effort overrides are scoped in the generated schema, but the proven
  Desktop router route does not pass external overrides through as authoritative settings. The
  owning renderer derives effective turn params; the override test showed requested `medium`
  effort did not replace the thread's `xhigh`.
- Target selection is under-specified in the older plan. Phase 2 must resolve exactly one
  target by explicit `conversationId` / `threadId`; the proven router path does not expose
  `thread/list` for cwd/newest-thread heuristics.
- The previously recorded validation-log config snapshot is stale for
  `model_reasoning_effort`: live config now reports `xhigh`, not `low`. Treat config values as
  evidence to refresh before and after every IPC probe/write.
- `\\.\pipe\codex-ipc` is owned by the main Desktop wrapper process (`Codex.exe`), not by a raw
  `codex.exe app-server` process. The pipe is an IPC router, not the direct generated app-server
  JSON-RPC endpoint.
- The Desktop router frame is a 4-byte little-endian body length followed by UTF-8 JSON. The router
  envelope is `{type:"request", requestId, method, params, ...}`. Router `initialize` with
  `{clientType}` is proven live and returns `{clientId}`.
- Routed non-initialize method evidence is now narrow, not general: `thread-follower-start-turn`
  version `1` is the only promoted write route. Generic `thread/*` or `turn/*` methods remain
  unavailable on the proven router path.
- Follow-up static inspection narrows this further: Desktop webcontents expose
  `thread-follower-*` handlers, not generic generated app-server methods such as `thread/list`,
  `thread/read`, or `turn/start`.
- Router method versions are defined by `Dr(method)`: methods absent from the map default to
  version `0`; `thread-follower-start-turn`, `thread-follower-steer-turn`, and related follower
  actions are version `1`.
- `thread-follower-submit-user-input` is not an arbitrary prompt-injection route. It replies to an
  existing pending user-input request by `requestId`.
- The first plausible GUI-visible write route is `thread-follower-start-turn` with
  `{conversationId, turnStartParams}`. Desktop discovery asks each registered webcontents whether
  `getThreadRole(conversationId) === "owner"`; the owner renderer then asserts ownership and calls
  app-server `turn/start` with derived `TurnStartParams`.
- Static inspection did not find an external, non-mutating owner query. The router treats
  `client-discovery-request` as an internal router-to-client message; a normal external client
  sending that message type is logged as unexpected. For a real target, ownership discovery and
  write forwarding appear coupled unless another direct app-server/UI state surface is found.

### Storage architecture (proven this session)

- The Codex **Desktop app renders conversations from a SQLite store**, not from the JSONL
  rollout files. Active store: `~/.codex/state_5.sqlite` (SQLx-managed; ~6.8 MB; last-written
  timestamp tracks live GUI activity). A stale `~/.codex/sqlite/codex-dev.db` exists but is not
  the live store.
- `state_5.sqlite` tables: `threads`, `thread_dynamic_tools`, `thread_spawn_edges`, `agent_jobs`,
  `agent_job_items`, `jobs`, `stage1_outputs`, `backfill_state`, `_sqlx_migrations`.
- **`codex exec resume` writes ONLY to the JSONL rollout files** (`~/.codex/sessions/<date>/rollout-*.jsonl`).
  It never writes the SQLite store. **Decisive evidence:** after sending exec handoffs to session
  `019e932e-385b-7ee3-ad58-3157c9accaf5`, the live store contained the GUI-visible turn
  ("Await message") 1x and the session id 8x, but the unique exec marker
  ("Handoff from Claude Code") **0x**. The exec turns are present in the JSONL file (verified:
  file grew 152,245 -> 168,991 bytes; 5 `task_complete` events) but are invisible to the GUI.
- Conclusion: **no JSONL-based approach (exec/resume) can ever appear in the Desktop GUI.** This
  is why the file-drop path routes through the user's own session instead.
- `backfill_state` table hints the app may import JSONL -> SQLite under some condition (e.g. on
  open/refresh). Unverified. If a backfill can be triggered, it is a cheaper alternative to IPC
  (see Option IV).

### App-server protocol (captured this session)

- The Desktop app embeds an **app-server** exposing a JSON-RPC-style protocol. Schema generated
  offline with: `codex app-server generate-json-schema --out <dir>` (safe; does not touch the
  running server). The union request type is `ClientRequest.json`.
- **Relevant methods** (wire names):
  - Read-only: `initialize`, `thread/list`, `thread/loaded/list`, `thread/read` (`includeTurns`),
    `account/read`, `model/list`.
  - Write (thread-scoped): `thread/resume`, `thread/start`, `turn/start`, `thread/inject_items`,
    `turn/steer`, `turn/interrupt`, `thread/name/set`, `thread/metadata/update`.
  - **Forbidden for this work** (global / destructive blast radius): `config/value/write`,
    `config/batchWrite`, `config/mcpServer/reload`, `account/*` mutations, `marketplace/*`,
    `plugin/*`, `thread/archive`, `thread/rollback`, `thread/fork` (except in an isolated test).
- **`turn/start` params (`TurnStartParams`)** — the isolation guarantee:
  - Required: `threadId` (single target), `input` (array of `UserInput`).
  - Optional, all documented as "Override ... **for this turn and subsequent turns**" (i.e. scoped
    to the targeted thread, never global): `model`, `effort`, `sandboxPolicy`, `approvalPolicy`,
    `approvalsReviewer`, `cwd`, `personality`, `summary`, `outputSchema`.
  - Because `model`/`effort` are per-thread overrides, sending a handoff to thread X cannot change
    the model or reasoning level of any other thread or the global config. This is the mechanism
    that satisfies Goal 3 — to be **verified empirically** in Phase 4, not assumed.
- **`thread/inject_items` (`ThreadInjectItemsParams`)** would add items to a thread **without
  starting a turn** (no model invocation), but it is not reachable through the proven router path
  and remains under-specified.
- Generated app-server request envelope: `{ "id": <string|int>, "method": <string>, "params": <object> }`
  (+ optional `trace`). This is useful for method schemas, but it is not the direct wire envelope for
  `\\.\pipe\codex-ipc`; the live pipe first requires the Desktop IPC-router envelope and frame.
  Static handler inspection did not find generic `thread/list`, `thread/read`, or `turn/start`
  router handlers on Desktop webcontents. Whether raw app-server JSON can be reached through
  another local endpoint remains unconfirmed.

Re-audit correction: the older line above calling `thread/inject_items` "lowest-risk" is only
conditionally true. The method is not approved for a write until the raw Responses API item
payload is specified and validated.

### Transport (partly proven; routed method semantics still open)

- The live Desktop IPC router is the **Windows named pipe `\\.\pipe\codex-ipc`** (confirmed present
  alongside `codex-browser-use-<uuid>` and a git fsmonitor pipe). 40+ `codex.exe`/`Codex.exe`
  processes run (the Desktop app spawns workers per session/agent).
- The named pipe is owned by the main Desktop wrapper process (`Codex.exe`). Per-thread worker
  processes appear as `codex.exe app-server --listen stdio://`; they are not the named-pipe server.
- The default control socket that `codex app-server proxy` targets —
  `~/.codex/app-server-control/app-server-control.sock` (AF_UNIX) — **does not exist**.
- `codex app-server proxy` is **AF_UNIX-only** and cannot speak to the Windows named pipe
  (`--sock '\\.\pipe\codex-ipc'` -> "dead network", os error 10050; git-bash also mangles the path
  to `C:\pipe\...`). **The proxy is the wrong tool here.**
- A direct **Node** client connects to `\\.\pipe\codex-ipc` successfully. The initial raw
  app-server attempts (Content-Length, newline, raw JSON) closed with zero response bytes because
  they used the wrong envelope/framing for this pipe.
- Packaged Desktop evidence and live validation now prove the correct router transport:
  `uint32le(length) + JSON` with request
  `{type:"request",requestId:"1",method:"initialize",params:{clientType:"external-probe"}}`.
  The live response returned `resultType:"success"` with a temporary `clientId`; global config was
  unchanged before/after.
- Static routed-method evidence:
  - Router discovery forwards only after a target client reports `canHandle:true`.
  - Desktop webcontents register handlers for `thread-follower-*` methods and gate them on
    ownership of `conversationId`.
  - `thread-follower-start-turn` is the candidate handoff write because it eventually calls
    app-server `turn/start`.
  - Generic `thread/list` / `thread/read` enumeration is not available through this router path.
  - No external read-only owner query was found; owner discovery for a real target appears coupled
    to forwarding the follower request.

### Tooling constraints on this machine

- `node` is available (used for MCP servers) — **use Node for the pipe client**, not bash.
- `sqlite3` CLI is **NOT** installed; `python`/`python3` is **NOT** available. DB inspection must
  use Node (e.g. a bundled `better-sqlite3`/`node:sqlite`) or binary `grep` heuristics.
- git-bash mangles `\\.\pipe\...` arguments; set `MSYS2_ARG_CONV_EXCL='*'` or avoid passing pipe
  paths through bash entirely.
- Codex CLI (exec) reports `v0.130.0`; Desktop app build `26.601.2237.0`. **Version skew between
  the CLI's generated protocol and the Desktop app-server's actual protocol is possible** — treat
  the generated schema as a guide, feature-detect at runtime.

### Phase 0 (shipped + validated this session)

- `scripts/handoff_to_codex.sh` default mode writes a self-contained handoff to
  `state/agent-inbox/for-codex.md` and prints the pickup line. `--open`/`--app`/`--exec` modes
  retained; `--exec` is labelled headless/not-GUI-visible.
- Return channel: Codex appends to `state/agent-inbox/for-claude.md`.
- Round-trip validated against the test session: Codex read `for-codex.md`, restated the task,
  made no edits, and the reply landed in `for-claude.md`. Global config verified unchanged.

## Implemented design

Safe current slice: `scripts/codex_ipc_probe.mjs` is read-only, timeout-bound, and hard
allowlisted. Its default `ipc-router` mode allows only router `initialize` until an owner-gated
follower route is deliberately promoted. Its explicit `app-server-json` compatibility mode still
supports only generated read-only app-server methods (`initialize`, `thread/list`,
`thread/loaded/list`, and `thread/read`) for use only if another direct app-server endpoint is
found.

Primary: a small **Node named-pipe router client** (`scripts/codex_ipc_client.mjs`) invoked by the
handoff script's opt-in `--ipc` mode:

```
connect \\.\pipe\codex-ipc
 -> ipc-router initialize { clientType }  (proven)
 -> use explicit conversationId           (user-supplied, UUID-validated)
 -> owner-gated follower discovery        (coupled to the forwarded request)
 -> thread-follower-start-turn { conversationId, turnStartParams }  (proven on test thread)
```

The client initializes with the router, targets exactly one explicit `conversationId`, emits
machine-readable success/failure, and exits non-zero so the shell can **fall back to file-drop** on
any error.

Current client state: `scripts/codex_ipc_client.mjs` is dry-run-first. It builds the proven
`thread-follower-start-turn` envelope with `version:1`, explicit `conversationId`, and minimal
`turnStartParams.input:[{type:"text", text, text_elements:[]}]`. It supports optional `model`,
`effort`, and `cwd` in direct client output, but production `--ipc` does not pass those flags
because the owning renderer derives effective model/effort. Live sends require both `--send` and
`--ack-live-write`; production `--ipc` also requires a caller-supplied UUID and relies on file-drop
fallback for any non-zero client result.

Current snapshot state: `scripts/codex_ipc_snapshot.mjs` is a read-only preflight/compare helper.
It opens `~/.codex/state_5.sqlite` with `readOnly:true`, reads `~/.codex/config.toml`, verifies
the explicit target thread exists, hashes selected thread rows, can count a unique marker in DB
bytes, and can compare before/after snapshots for config drift and non-target thread-row changes.
It does not connect to `\\.\pipe\codex-ipc` and writes no files. Compare mode supports explicit
operator/background-thread allowances and live-write expectations (`--expect-target-change` and
`--expect-marker-increase`) so no-op or confounded tests fail closed.

Production gating result: `--ipc` is wired only as an opt-in path. It writes the file-drop first,
then injects the pickup line into the specified live Desktop thread. If the thread is not open or
owned by a renderer, or if the router/client fails, the script exits non-zero after printing the
file-drop fallback instruction.

### Approach options

- **Option I - Direct named-pipe router client (chosen primary).** Talks to the Desktop IPC router.
  The generic app-server-method variant is rejected for `\\.\pipe\codex-ipc`; the viable candidate
  is an owner-gated follower action.
- **Option II - `thread/inject_items` before `turn/start` (downgraded).** This is not currently
  reachable through the proven router path, and its raw Responses item payload is still
  under-specified. Keep only if a direct app-server endpoint is found.
- **Option III — Spawn a separate headless app-server** (`codex app-server --listen unix://…|ws://…`)
  on the same `CODEX_HOME`. **Rejected unless Desktop server is unreachable**: two servers writing
  the same SQLite store risks contention/corruption, violating the no-impact constraint.
- **Option IV — Backfill trigger.** Keep exec (JSONL) and induce the app to import JSONL -> SQLite
  via `backfill_state`. **Investigate in Phase 1b**; if a safe, supported trigger exists it may beat
  IPC for simplicity. Unknown whether user-triggerable.
- **Option V - `thread-follower-start-turn` (new candidate first write).** Sends a turn through the
  owning renderer for exactly one `conversationId`, then the renderer calls app-server `turn/start`.
  This is more GUI-native than raw app-server injection but higher blast radius than additive item
  injection because it invokes a model turn.

Option II correction: `thread/inject_items` is a candidate only if a direct app-server path is
found. For the proven router path, `thread-follower-start-turn` is the current candidate first
write because it uses the renderer's normal owner-gated turn-start flow.

## Bottom-up sequence

- **Phase 0 - Safe baseline. DONE.** File-drop handoff + return channel, validated. This remains
  the default and supported fallback.
- **Phase 0.5 - Plan hardening + read-only probe. DONE.** Overclaims were corrected, generated
  schema evidence was re-audited, and `scripts/codex_ipc_probe.mjs` was added as a read-only,
  allowlisted, timeout-bound named-pipe probe.
- **Phase 1 - Crack the transport. DONE for the promoted route.** The Desktop pipe is an IPC
  router using `uint32le(length)+JSON`; router `initialize` returns a client id. Generic
  app-server `thread/*` and `turn/*` routes are not exposed on this pipe.
- **Phase 2 - Target and owner proof. DONE with explicit-target caveat.** The authorized test
  thread exists in `state_5.sqlite`; static inspection found no non-mutating owner query, so real
  owner proof is coupled to the forwarded `thread-follower-start-turn` request. Targeting remains
  explicit `conversationId` only; no cwd/title/newest-thread heuristic is accepted.
- **Phase 3 - Controlled owner-gated write. DONE on the authorized test thread.** Negative
  sentinel probe returned `no-client-found`; real target write returned success with a different
  `handledByClientId` (owning renderer), real turn id, model reply, unchanged config, and no
  unexpected non-target thread row changes.
- **Phase 4 - Handoff/override proof. PARTIALLY DONE by revised requirement.** Full handoff
  behavior is proven: `--ipc` delivered a pickup line, the model read `for-codex.md`, and it
  replied. The original model/effort override subgoal is explicitly rejected for this route:
  renderer-derived params kept the thread at `xhigh` despite a requested `medium` effort.
- **Phase 5 - Productionize. DONE as experimental opt-in.** `handoff_to_codex.sh --ipc
  <conversationId> "task"` writes file-drop first, invokes the Node client, and falls back to
  file-drop on any failure. File-drop remains default.
- **Phase 6 - Operational hardening. DONE for current implementation; future re-proof is
  contingent.** GUI visibility is user-confirmed. `/ipc`
  exists as an inspect-before-send skill, and `scripts/codex_ipc_revalidate.mjs` gives operators a
  validate-only post-update gate for required files, syntax, state DB/sessions, pipe presence,
  target rollout inspection, and optional read-only router `initialize`. New/fresh-session
  targeting is covered by `scripts/codex_ipc_thread_locator.mjs`, which discovers candidate
  conversationIds from the Desktop thread index without authorizing a write.
  `scripts/codex_ipc_write_proof.mjs` now turns any future controlled live-write re-proof into a
  dry-run-first, inspect/revalidate/snapshot/poll/compare workflow instead of an ad hoc recipe.
  Running the live re-proof is still contingent on a future Desktop update/drift and explicit
  operator approval.

## Files changed / maintained

| File | Expected change |
|---|---|
| `scripts/codex_ipc_client.mjs` | NEW - dry-run-first Node named-pipe router client (initialize, explicit target guard, follower start-turn, live-write gates) |
| `scripts/codex_ipc_snapshot.mjs` | NEW - read-only config/state DB snapshot and compare helper for Phase 3/4 isolation proof |
| `scripts/handoff_to_codex.sh` | Add opt-in `--ipc` mode with file-drop fallback |
| `scripts/codex_ipc_probe.mjs` | NEW (research) — read-only framing/auth probe; may be archived after Phase 1 |
| `scripts/codex_ipc_revalidate.mjs` | NEW - validate-only post-update wrapper for syntax, state, pipe presence, target inspection, and optional read-only router initialize |
| `scripts/codex_ipc_thread_locator.mjs` | NEW - read-only candidate conversationId discovery by workspace/project/title/time |
| `scripts/codex_ipc_contract_audit.mjs` | NEW - static requirement matrix for external audit of IPC contract evidence |
| `scripts/codex_ipc_write_proof.mjs` | NEW - dry-run-first controlled write re-proof harness for future Desktop update/drift events |
| `scripts/check_json_files.py` | Skip ignored `local_artifacts/` evidence so repo JSON validation remains source-scoped |
| `.claude/skills/handoff-to-codex` | Documents `--ipc` as experimental opt-in with fallback |
| `state/agent-inbox/README.md` | Documents `--ipc` as experimental opt-in with fallback |
| `plans/2026-06-04-codex-ipc-injection.md` | Records progress, decisions, caveats, and future hardening gates |
| `state/PROJECT_STATE.md` | Do not change unless IPC becomes the repo-wide active plan; avoid displacing the product plan |

## Tests / verification

Reproduction + verification commands (run from the project root):

```bash
# Regenerate the protocol schema (offline; safe):
codex app-server generate-json-schema --out /tmp/codex_schema_out
#   then read /tmp/codex_schema_out/ClientRequest.json (definitions: TurnStartParams, ThreadInjectItemsParams, ...)

# Confirm the live pipe exists (read-only):
#   PowerShell: [System.IO.Directory]::GetFiles('\\.\pipe\') | Where-Object { $_ -match 'codex' }

# Phase 1 probe (Node, read-only): initialize first; thread/read later only after target proof.
node --check scripts/codex_ipc_probe.mjs
node scripts/codex_ipc_probe.mjs --dry-run --protocol ipc-router --framing uint32le
node scripts/codex_ipc_probe.mjs --protocol ipc-router --framing uint32le --timeout-ms 1500
node scripts/codex_ipc_probe.mjs --dry-run --protocol app-server-json --framing all --experimental-api
# Must fail closed until the follower write route is deliberately promoted:
node scripts/codex_ipc_probe.mjs --dry-run --protocol ipc-router --sequence thread-list

# Phase 2 client scaffold (dry-run only; no pipe connection unless --send is present):
node --check scripts/codex_ipc_client.mjs
node scripts/codex_ipc_client.mjs --thread 019e932e-385b-7ee3-ad58-3157c9accaf5 --task "read state/agent-inbox/for-codex.md and proceed" --model gpt-5.5 --effort xhigh
node scripts/codex_ipc_client.mjs --thread 019e932e-385b-7ee3-ad58-3157c9accaf5 --task-file state/agent-inbox/for-codex.md
# Must fail closed before any live write:
node scripts/codex_ipc_client.mjs --thread 019e932e-385b-7ee3-ad58-3157c9accaf5 --task "test" --send
node scripts/codex_ipc_client.mjs --thread 019e0000-0000-0000-0000-000000000000 --task "test" --send --ack-live-write

# Phase 2 target/config snapshot helper (read-only; no IPC connection):
node --check scripts/codex_ipc_snapshot.mjs
node scripts/codex_ipc_snapshot.mjs --summary --thread 019e932e-385b-7ee3-ad58-3157c9accaf5 --marker CODEx_IPC_MARKER_VALIDATION_2026_06_04
node scripts/codex_ipc_snapshot.mjs --summary --thread 019e0000-0000-0000-0000-000000000000
# Before/after compare for a future controlled write should use full snapshots, not --summary:
# node scripts/codex_ipc_snapshot.mjs --thread 019e932e-385b-7ee3-ad58-3157c9accaf5 --marker <unique-marker> > before.json
# node scripts/codex_ipc_snapshot.mjs --thread 019e932e-385b-7ee3-ad58-3157c9accaf5 --marker <unique-marker> > after.json
# node scripts/codex_ipc_snapshot.mjs --compare before.json after.json
# For a live-write proof, add explicit allowances only for predeclared operator/background rows:
# node scripts/codex_ipc_snapshot.mjs --compare before.json after.json --allow-thread-change <operator-thread-id> --expect-target-change --expect-marker-increase

# DB isolation check:
#   prefer codex_ipc_snapshot.mjs full before/after snapshots plus --compare.
#   If node:sqlite is unavailable after a future runtime change, fall back to binary marker counts
#   only as weaker supporting evidence, not as sufficient row-level isolation proof.

# Post-update revalidation wrapper (no prompt injection, no follower-start-turn):
node --check scripts/codex_ipc_revalidate.mjs
node scripts/codex_ipc_revalidate.mjs --thread 019e932e-385b-7ee3-ad58-3157c9accaf5
# Optional live read probe: connects to the Desktop IPC pipe and sends initialize only.
node scripts/codex_ipc_revalidate.mjs --thread 019e932e-385b-7ee3-ad58-3157c9accaf5 --allow-live-ipc-read --timeout-ms 1500

# New-session/no-UUID candidate discovery (read-only; inspect selected id before sending):
node --check scripts/codex_ipc_thread_locator.mjs
node scripts/codex_ipc_thread_locator.mjs --project land_diligence_dual_agent_workspace --limit 10
node scripts/codex_ipc_thread_locator.mjs --project land_diligence_dual_agent_workspace --title-contains "Await message" --require-single

# Static external audit matrix (repo files only; no IPC/SQLite runtime access):
node --check scripts/codex_ipc_contract_audit.mjs
node scripts/codex_ipc_contract_audit.mjs

# Controlled write re-proof harness (dry-run/read-only unless --send is present):
node --check scripts/codex_ipc_write_proof.mjs
node scripts/codex_ipc_write_proof.mjs --thread 019e932e-385b-7ee3-ad58-3157c9accaf5 --marker CODEX_IPC_DRYRUN_PROOF_2026_06_05
# Live path only after explicit operator approval:
# node scripts/codex_ipc_write_proof.mjs --thread <conversationId> --marker <unique-marker> --send --ack-live-write --allow-any-thread

# Global-config invariant (must be identical before/after EVERY test):
grep -E '^(model|model_reasoning_effort|sandbox_mode|approval_policy)' ~/.codex/config.toml
```

Current verification signals:
- Transport: a well-formed IPC-router `initialize` response, plus static route correction to
  owner-gated follower actions.
- External reachability: sentinel `thread-follower-start-turn` returns structured
  `no-client-found`, proving external follower requests are accepted and scoped by
  `conversationId`.
- Controlled write: real target `thread-follower-start-turn` returns success with
  `handledByClientId` different from the external client id, proving the owning renderer handled
  the turn.
- Content proof: injected prompt and model replies appear in the target rollout JSONL. Do not use
  DB byte-marker counts as content proof; `state_5.sqlite` stores thread metadata, not turn text.
- Isolation proof: `codex_ipc_snapshot.mjs --compare` shows unchanged config, changed target row,
  no added/removed thread rows, and no unexpected non-target thread-row changes.
- Override proof: requested model/effort overrides are not honored by the owner-renderer route;
  the effective thread reasoning stayed `xhigh` when `medium` was requested.
- Human GUI signal: the user later confirmed the Codex Windows app showed the session and messages
  sent by Claude during testing.
- Current post-update gate: `codex_ipc_revalidate.mjs --allow-live-ipc-read` passed on the current
  Desktop runtime with required files/syntax/state/pipe checks, target rollout inspection, and a
  successful read-only router `initialize` response. It does not prove prompt-send behavior.
- New-session locator: `codex_ipc_thread_locator.mjs` can identify candidate conversationIds by
  project/cwd/title/time and returned the known `Await message` thread as a single candidate when
  filtered by project and title. It does not authorize writes.
- Contract audit: `codex_ipc_contract_audit.mjs` emits a static requirement matrix and currently
  reports all eleven IPC contract requirements evidenced from repo artifacts.
- Controlled write re-proof harness: `codex_ipc_write_proof.mjs` dry-run inspected the authorized
  thread and emitted the full inspect/revalidate/snapshot/send/poll/compare plan without sending a
  prompt.

**Original test session (authorized proof target):**
`019e932e-385b-7ee3-ad58-3157c9accaf5`
(`~/.codex/sessions/2026/06/04/rollout-2026-06-04T08-09-05-019e932e-385b-7ee3-ad58-3157c9accaf5.jsonl`).

Production `--ipc` accepts any explicit UUID because the mechanism is proven conversation-scoped
and `--allow-any-thread` is accepted as the long-term explicit-thread policy. Operators are still
responsible for inspecting and selecting the intended live Desktop thread; no heuristic targeting
is approved.

## Risks and blockers

- **Shared live app-server (highest concern).** Every pipe connection touches the server running
  ALL of the user's sessions. Controls: read-only methods first; **single dedicated test thread**;
  **never** send any `config/*`, `account/*`, `marketplace/*`, `plugin/*`, or destructive thread
  method; snapshot+diff `state_5.sqlite` and `config.toml` around every write; bound every client
  with a hard timeout; abort on the first unexpected server response.
- **Generic app-server routing rejected for this pipe.** Router framing is proven, but Desktop
  webcontents do not register generic `thread/list`, `thread/read`, or `turn/start` handlers.
  The plan must use owner-gated follower actions or find a different direct app-server endpoint.
- **Owner proof gap.** `thread-follower-start-turn` has an internal owner check, but the current
  static evidence has not identified a non-mutating way for an external client to prove exactly one
  owner before the first write. A fake/nonexistent `conversationId` can only prove the negative
  no-client-found path; it cannot prove the real target owner without risking a forwarded write.
- **Target ambiguity.** A cwd/title/newest-thread heuristic can select the wrong live GUI thread.
  Controls: explicit `conversationId` / `threadId` only for the proven router path; no heuristic
  target selection before writes.
- **Raw item ambiguity.** `thread/inject_items` accepts raw Responses API items, not a typed
  `UserInput`, and is not reachable through the proven router path. Controls: do not use it unless
  a direct app-server endpoint is found and a valid minimal payload is proven.
- **Protocol/version skew.** CLI-generated schema may not match the Desktop app-server build
  (`26.601.2237.0`). Feature-detect; do not hard-code method availability.
- **Concurrency/race.** GUI client and our client on the same thread; `thread-follower-start-turn`
  while the GUI is mid-turn. Controls: inspect the explicit target before sending, avoid live
  writes while the target appears active unless explicitly accepted, and never `turn/interrupt` a
  thread we did not start.
- **Windows named-pipe quirks.** git-bash path mangling -> use Node, never pass the pipe path
  through bash.
- **DB corruption.** Never write SQLite directly; only via the app-server.
- **Reversibility.** `thread/rollback` exists but is destructive; do not rely on it. The proven
  follower route starts a turn, so first-write tests must use a clearly marked, authorized test
  prompt and pre/post state snapshots rather than assuming easy removal.

### Guardrail invariants (must hold in every phase)

1. Exactly one explicit `conversationId` / `threadId` per write. No heuristic targeting.
2. `~/.codex/config.toml` byte-identical before and after every run.
3. No method from the Forbidden list is ever sent.
4. Any client error -> exit non-zero -> shell falls back to file-drop.
5. Every client invocation is time-bounded and logs the exact JSON it sent.

## Decision log

- **2026-06-04** — Ship file-drop as the default/safe path (Phase 0). Pursue live IPC injection as
  a phased spike behind `--ipc`, gated on cracking the named-pipe transport. Rationale: file-drop
  is GUI-visible via the user's own session and has zero cross-session risk; IPC is the superior
  UX but touches the shared live server and must be proven safe first.
- **2026-06-04** — Reject `codex app-server proxy` (AF_UNIX-only; cannot reach `\\.\pipe\codex-ipc`).
- **2026-06-04** — Reject Option III (separate app-server on same CODEX_HOME) as default due to
  SQLite contention risk; keep only as a last resort if the Desktop pipe is unreachable.
- **2026-06-04** — Historical/superseded: initially chose `thread/inject_items` as the first write
  over `turn/start` to minimize blast radius before invoking a model. Later static router evidence
  shows this is not reachable through `\\.\pipe\codex-ipc`.

- **2026-06-04** - Re-audit correction: `thread/inject_items` is provisional, not approved,
  because its generated params accept raw Responses API items. First write selection is blocked
  on payload proof or a deliberate switch to typed `turn/start`.
- **2026-06-04** - Correct transport model: `\\.\pipe\codex-ipc` is a Desktop IPC router owned by
  `Codex.exe`, using `uint32le` length-prefixed JSON router messages. Raw generated app-server
  JSON is not the direct named-pipe protocol.
- **2026-06-04** - Correct routed-method model: Desktop webcontents expose owner-gated
  `thread-follower-*` handlers, not generic app-server methods. `thread-follower-start-turn` is
  the current candidate write path; `thread-follower-submit-user-input` is not a general prompt
  submission route.
- **2026-06-04** - User confirmed the injected Codex turns appeared in the Windows Desktop GUI.
  `--allow-any-thread` remains acceptable long-term because production sends require one explicit
  UUID, the route is conversation-scoped, and file-drop is written first as fallback.
- **2026-06-04** - Added `scripts/codex_ipc_revalidate.mjs` as the post-update validation surface.
  It is validate-only, generates no artifacts, and can optionally send a read-only router
  `initialize` with `--allow-live-ipc-read`; it never sends a prompt or follower-start-turn.
- **2026-06-04** - Added `scripts/codex_ipc_thread_locator.mjs` as the no-UUID candidate discovery
  surface. It reads the local Desktop thread index, filters by cwd/project/title/time, and requires
  a follow-up session inspection before any send.
- **2026-06-04** - Added `scripts/codex_ipc_contract_audit.mjs` as the static external audit
  surface. It reads repo artifacts only and emits a requirement matrix for file-drop, opt-in IPC,
  explicit targeting, fallback, context pointers, inspection, no-UUID discovery, update
  revalidation, forbidden writes, and audit evidence.

## Progress log

- **2026-06-04 - `/ipc` skill contract added.** The Claude-facing command now treats an existing
  Codex conversationId as an explicit target that must be inspected before any send. New-session
  mode is deliberately separate: open/resolve the intended project first, then obtain a concrete
  conversationId before using IPC. A read-only `codex_ipc_session_inspect.mjs` helper supports
  DB-row plus rollout-tail inspection without touching the IPC pipe or SQLite writes.

- **2026-06-04 - Post-update revalidation wrapper added.** `scripts/codex_ipc_revalidate.mjs`
  checks required IPC scripts, Node syntax, Git Bash shell syntax, `node:sqlite`, Codex state files,
  named-pipe presence, optional target inspection, and an optional read-only IPC router
  `initialize`. Current run with `--allow-live-ipc-read` succeeded and returned a structured
  initialize success; no prompt injection or follower-start-turn was sent.
- **2026-06-04 - Thread locator added for no-UUID `/ipc`.** `scripts/codex_ipc_thread_locator.mjs`
  lists projects or filters threads by exact normalized cwd, project folder name, title text, and
  creation/update time. It found the authorized `Await message` test thread as one candidate with
  `--project land_diligence_dual_agent_workspace --title-contains "Await message" --require-single`.
  Locator output is candidate discovery only; the selected id must still be inspected before send.
- **2026-06-04 - Contract audit command added.** `scripts/codex_ipc_contract_audit.mjs` now emits a
  read-only requirement matrix for the IPC contract. Current run reported 11/11 requirements
  evidenced from repo files, with residual caveats for transcript breadth and future Desktop
  update write re-proof.
- **2026-06-05 - Controlled write proof harness added.** `scripts/codex_ipc_write_proof.mjs` now
  provides the previously contingent future re-proof workflow as a dry-run-first command. It
  inspects the target, revalidates the runtime, captures before/after snapshots in memory, sends one
  marker task only with `--send --ack-live-write`, polls the rollout for marker acknowledgement plus
  `task_complete`, and compares config/thread isolation. Dry-run on the authorized test thread
  passed without sending a prompt.
- **2026-06-04 - Verification gate source-scope fix.** `scripts/check_json_files.py` now skips
  `.git`, `.venv`, and ignored `local_artifacts/` directories. This keeps generated IPC evidence
  snapshots, including UTF-16 PowerShell snapshots and the recorded zero-byte interrupted baseline,
  out of the source JSON gate without deleting or rewriting evidence.

- **2026-06-04 — Bidirectional full-transcript context pointers added.** Each handoff now carries
  Claude's session id + absolute transcript path (`~/.claude/projects/<mangled>/<sid>.jsonl`,
  resolved from `CLAUDE_CODE_SESSION_ID` env, converted to Windows form). **Empirically verified:**
  an `--ipc` cross-context test on `019e932e` had Codex read the first line of Claude's transcript
  and reply `XCTX READ-OK {"type":"ai-title","aiTitle":"Explore inter-session messaging…` — i.e.
  Codex CAN read Claude's transcript under its sandbox. Codex self-report of its own id returned
  `not-exposed`; therefore Claude→Codex deep-read relies on the `conversationId` (== rollout id) for
  `--ipc`, and on locating the rollout by handoff content for file-drop. Global config unchanged.
  Docs (skill/README) gained a "Cross-session context inspection" section. Exposure caveat noted:
  the transcript is the FULL session and may include unrelated context.

- **2026-06-04 (BREAKTHROUGH)** — Phases 1-4 proven on the authorized test thread; live IPC GUI
  injection WORKS, isolated. Evidence:
  - **Negative owner-discovery probe** (`scripts/codex_ipc_owner_probe.mjs`, sentinel
    `00000000-0000-4000-8000-00000000c0de` verified absent in `state_5.sqlite`): one external
    `thread-follower-start-turn` returned a structured `{resultType:"error",error:"no-client-found"}`.
    The router ACCEPTS external follower requests and scopes by `conversationId` (no broadcast).
    Config byte-identical before/after. => follower route is externally VIABLE.
  - **Controlled write** on `019e932e` (default model/effort, benign no-edit task with marker
    `IPCINJECTMARKER7F3A9`): router returned `resultType:"success"`, `handledByClientId` = a
    *different* client than our initialize client (the owning Desktop renderer), with a real
    `turn.id` (`019e9534-…`), `status:"inProgress"`. The model then replied exactly
    `IPCINJECTMARKER7F3A9 ACK` (present in the rollout JSONL 5x). No file edits.
  - **Isolation proof** via `codex_ipc_snapshot.mjs --compare`: `config.sha256Unchanged:true`,
    `selectedKeysUnchanged:true`, `targetThreadChanged:true`, `unexpectedNonTargetChangedIds:[]`,
    `addedIds/removedIds:[]`. Global `model_reasoning_effort` stayed `xhigh` throughout.
  - **Override finding (important):** a second write with `--model gpt-5.5 --effort medium` also
    succeeded and the model replied (`OVR_MARKER_5B2 ACK`), but the turn ran at the thread's
    `xhigh`, NOT the requested `medium`. The owning renderer **derives** `TurnStartParams`; an
    external client CANNOT change a thread's model/reasoning via this route. This is the ideal
    safety property: Claude's IPC input cannot alter model/reasoning (global, target, or other).
  - **Storage note:** turn *content* (input + reply text) lands in the rollout JSONL; `state_5.sqlite`
    stores thread *metadata* (row hash changed). So a DB byte-marker scan will not see injected text;
    use rollout-JSONL marker + thread-row-change + GUI observation as the content/visibility proof.
  - **GUI confirmation:** the user later confirmed the Codex Windows app displayed the session and
    Claude-sent messages during testing. Mechanism and visible behavior are proven for that path.

- **2026-06-04** - Phase 3 quiescence/compare gate hardened before live write: compare mode now
  accepts PowerShell UTF-16LE snapshot files, supports explicit `--allow-thread-change` for known
  operator/background rows, and can require `--expect-target-change` plus
  `--expect-marker-increase` for live-write proof. A no-write compare detected a changing
  non-target project6 thread (`019e91e6-ebed-74a2-8575-48a6170d8e95`) even though no IPC write was
  sent; rerun with that row explicitly allowed passed, and rerun with live-write expectations
  failed as intended because the target row and marker did not change. Live write deferred because
  current non-target activity would confound isolation proof unless a quiet window or explicit
  predeclared allowance set is used.

- **2026-06-04** - Phase 2 read-only snapshot helper added: `scripts/codex_ipc_snapshot.mjs`
  captures config hash/selected keys, opens `state_5.sqlite` read-only, verifies target thread
  existence, records thread row hashes for future before/after comparison, counts a unique marker
  in DB bytes, and fails closed for nonexistent target threads. Validation snapshot for
  `019e932e-385b-7ee3-ad58-3157c9accaf5` succeeded with stable reads, DB `quick_check:"ok"`,
  `model=gpt-5.5`, `model_reasoning_effort=xhigh`, `sandbox_mode=danger-full-access`,
  `approval_policy=never`, and marker count `0`. No IPC connection or live write was attempted.

- **2026-06-04** - Phase 2 dry-run client scaffold added: `scripts/codex_ipc_client.mjs` builds
  router `initialize` and `thread-follower-start-turn` envelopes with explicit `conversationId`,
  minimal text `UserInput`, optional model/effort/cwd overrides, exact sent-request logging, and
  live-write gates requiring `--send --ack-live-write` plus the authorized test thread. No live
  follower write has been sent.

- **2026-06-04** - Phase 1 router initialize proven: `node .\scripts\codex_ipc_probe.mjs
  --protocol ipc-router --framing uint32le --timeout-ms 1500` returned a success response with a
  temporary `clientId` and `status:"response"`; pre/post config snapshots were unchanged
  (`model=gpt-5.5`, `model_reasoning_effort=xhigh`, `sandbox_mode=danger-full-access`,
  `approval_policy=never`). No thread methods or writes were sent.

- **2026-06-04** - Static route inspection after router initialize: method version map shows
  `thread-follower-*` methods at version `1` and absent methods defaulting to `0`; Desktop
  webcontents register `thread-follower-*` request handlers gated on
  `getThreadRole(conversationId) === "owner"`; `thread-follower-start-turn` forwards to the
  renderer's normal `turn/start` flow; no external read-only owner query was found. No additional
  live IPC calls were sent.

- **2026-06-04** - Phase 0.5 validation: `node --check`, dry-run, help output, and the
  fail-closed `thread-read` guard passed. Initialize-only live probe connected to
  `\\.\pipe\codex-ipc`, but the server closed with zero response bytes for content-length,
  newline, and raw JSON framing. Config remained unchanged before/after.

- **2026-06-04** - Phase 0.5 started: re-audited generated schema evidence, corrected the plan's
  stale `thread/inject_items` overclaim, recorded target-resolution and live-config drift risks,
  and added `scripts/codex_ipc_probe.mjs` as a read-only, allowlisted named-pipe probe.

- **2026-06-04** — Phase 0 complete: file-drop handoff implemented in `scripts/handoff_to_codex.sh`
  and validated end-to-end (Codex read `for-codex.md`, replied to `for-claude.md`, no edits, global
  config unchanged). Archived superseded `state/agent-inbox/from-codex.md` to
  `archive/2026-06-04_codex-handoff-filedrop/`. Captured all architecture/protocol/transport
  evidence above. Historical state at that moment: Phases 1-5 were not started and transport
  framing/auth was the next blocker. Superseded by the breakthrough entries above.
