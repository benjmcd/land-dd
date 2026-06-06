# Agent Inbox

Shared message channel between Claude Code and Codex sessions.

| File | Direction | Written by | Read by |
|---|---|---|---|
| `for-codex.md`  | Claude Code -> Codex | `handoff_to_codex.sh` (file-drop) | Codex (when you paste the pickup line) |
| `for-claude.md` | Codex -> Claude Code | Codex (or `--exec` reply capture) | Claude Code |

## Claude Code -> Codex (file-drop, recommended)

From ANY directory within the project or its worktrees:

```bash
./scripts/handoff_to_codex.sh "task for Codex"
```

This writes the handoff (branch, commits, diff, task) to `for-codex.md` and prints a pickup
line. Paste that line into your live Codex session (Desktop app or TUI):

```
read state/agent-inbox/for-codex.md and proceed
```

The handoff appears in the Codex Desktop GUI because your own session reads the file, and it
has **zero effect on any other running Codex session**.

> **Why not `codex exec`?** The Desktop app renders from a SQLite store; `codex exec` writes
> only JSONL rollout files, so exec handoffs never show in the GUI. The optional auto-inject
> path is `--ipc`; it is experimental, opt-in, and documented in
> `plans/2026-06-04-codex-ipc-injection.md`.

### Other modes

```bash
./scripts/handoff_to_codex.sh --ipc <conversationId> "task"  # auto-inject into a live Desktop GUI thread
./scripts/handoff_to_codex.sh --open [session_id]   # open a session in the terminal TUI
./scripts/handoff_to_codex.sh --app                 # open the workspace in the Codex desktop app
./scripts/handoff_to_codex.sh --exec "task" [sid]   # headless exec (NOT visible in the GUI)
```

#### `--ipc` (opt-in, experimental — GUI auto-inject, no manual paste)

Delivers the handoff straight into a live Codex Desktop thread via the app's own owner-gated
IPC router, so the turn appears in the GUI with **no paste step**. It writes the file-drop first
and **falls back to it on any failure** (thread not open/owned, router unavailable, no Node).

> **Experimental.** The mechanism is proven end-to-end: the owning renderer handles the turn, the
> model replies, and the user confirmed the sent messages appeared in the Codex Windows app. It
> still depends on undocumented Desktop IPC internals that a Codex update could change. If a handoff
> does not appear, fall back to file-drop. File-drop is the supported default.

```bash
./scripts/handoff_to_codex.sh --ipc 019e932e-385b-7ee3-ad58-3157c9accaf5 "create a PR for this branch"
```

- The `<conversationId>` must be a thread currently **open in the Desktop app** (its owning
  renderer must be live); otherwise the router returns `no-client-found` and it falls back.
- Production `--ipc` accepts any explicit UUID via `--allow-any-thread`; this is intentional for
  the long-term explicit-thread path. Inspect the target session before sending and do not use
  cwd/title/newest-thread heuristics for writes.
- **Model/reasoning are renderer-controlled.** The injected turn runs at the thread's existing
  model/effort; this path **cannot** change a thread's model/reasoning or affect any other
  session, and never touches `~/.codex/config.toml`. (Proven: global config byte-identical and
  no non-target thread changed across live tests.)
- File-drop remains the default; `--ipc` is opt-in. See
  `plans/2026-06-04-codex-ipc-injection.md` for the full mechanism, transport, and isolation evidence.

#### Post-update revalidation

After a Codex Desktop update, revalidate before trusting `--ipc`:

```bash
node scripts/codex_ipc_revalidate.mjs --thread <conversationId>
node scripts/codex_ipc_revalidate.mjs --thread <conversationId> --allow-live-ipc-read --timeout-ms 1500
```

The first command performs validate-only file/syntax/state/pipe/target checks and sends no IPC
message. The second additionally connects to `\\.\pipe\codex-ipc` and sends router `initialize`
only. Neither command injects a prompt, starts a turn, writes config, writes SQLite, or generates
artifacts.

If read-only revalidation shows drift after a Desktop update, use the controlled proof harness
instead of rebuilding the write proof by hand. Start with dry-run:

```bash
node scripts/codex_ipc_write_proof.mjs --thread <conversationId> --marker <unique-marker>
```

Only with explicit operator approval, run the live proof:

```bash
node scripts/codex_ipc_write_proof.mjs --thread <conversationId> --marker <unique-marker> --send --ack-live-write --allow-any-thread
```

The harness inspects the target, revalidates the runtime, captures before/after snapshots in
memory, sends one marker task, polls the rollout for the marker acknowledgement and
`task_complete`, and compares config/thread isolation. It does not write config, SQLite, or proof
artifacts.

#### Finding a conversationId without a UUID

For `/ipc` workflows where a new/fresh Desktop thread was opened but the conversationId is not yet
known, use the read-only locator:

```bash
node scripts/codex_ipc_thread_locator.mjs --project land_diligence_dual_agent_workspace --limit 10
node scripts/codex_ipc_thread_locator.mjs --project land_diligence_dual_agent_workspace --title-contains "Await message" --require-single
```

The locator reads `~/.codex/state_5.sqlite` only. Candidate output is not write authority; inspect
the selected conversationId with `codex_ipc_session_inspect.mjs` before any `--ipc` send.

#### Contract audit

To audit the IPC contract from repo artifacts without touching the Desktop runtime:

```bash
node scripts/codex_ipc_contract_audit.mjs
```

This emits a JSON requirement matrix for default file-drop, opt-in IPC, explicit targeting,
fallback behavior, transcript pointers, inspect-before-send, no-UUID discovery, post-update
revalidation, controlled write re-proof, no forbidden writes, and audit evidence. It is
static/read-only only.

## Codex -> Claude Code

From inside a Codex session, append to the inbound file:

```bash
cat >> state/agent-inbox/for-claude.md << 'EOF'
[From Codex]
<message>
EOF
```

Claude Code reads `for-claude.md` with the Read tool.

## Cross-session context inspection

Each handoff carries pointers so either agent can investigate the other's **full transcript**, not
just the message:

- **Codex → Claude:** `for-codex.md` includes Claude's session id + absolute transcript path
  (`~/.claude/projects/<mangled-project>/<session-id>.jsonl`). Codex can read it (verified). Large
  file; grep/tail it; may contain unrelated context.
- **Claude → Codex:** for `--ipc`, the `conversationId` is the Codex rollout id — read
  `~/.codex/sessions/<date>/rollout-*-<conversationId>.jsonl`. For file-drop, Codex can't reliably
  self-report its id, so Claude locates the rollout by handoff content.

Override the advertised Claude pointer with `CLAUDE_SESSION_ID` / `CLAUDE_TRANSCRIPT`.
