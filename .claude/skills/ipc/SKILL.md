---
name: ipc
description: |
  MANUAL TRIGGER ONLY: invoke when the user types /ipc. Inspect, watch, or manage Codex Desktop sessions and send opt-in handoffs after reading the target session history/current state.
---

# /ipc - Claude Code to Codex Desktop coordination

Use this skill only for an explicit `/ipc` command or when the user directly asks to operate the
Claude-to-Codex IPC bridge.

## First decision

Classify the invocation before doing anything else:

1. Existing Codex session: `/ipc <conversationId> [instruction]`
2. Watch/status: `/ipc watch <conversationId>` or `/ipc status <conversationId>`
3. New Codex session: `/ipc [new] [workspace/project] [instruction]` with no UUID

If a UUID is present, treat it as the explicit target. Do not infer a different target from title,
cwd, recency, or project name.

## Existing-session mode

Always inspect before sending any message.

Run the read-only inspector from the repository root:

```bash
node scripts/codex_ipc_session_inspect.mjs --thread <conversationId> --tail-events 20
```

If Codex Desktop or Codex CLI may have updated since the last proven IPC run, run the validate-only
post-update wrapper before sending:

```bash
node scripts/codex_ipc_revalidate.mjs --thread <conversationId>
```

Use `--allow-live-ipc-read --timeout-ms 1500` only when you need to re-prove router framing on the
current Desktop runtime; it sends `initialize` only and must not be confused with a prompt-send
proof.

If read-only revalidation detects drift after a Codex Desktop update, do not improvise a live
probe. Use the controlled write-proof harness. First run the dry-run path:

```bash
node scripts/codex_ipc_write_proof.mjs --thread <conversationId> --marker <unique-marker>
```

Run the live path only with explicit operator approval:

```bash
node scripts/codex_ipc_write_proof.mjs --thread <conversationId> --marker <unique-marker> --send --ack-live-write --allow-any-thread
```

The harness inspects the target, revalidates, snapshots before/after in memory, sends one marker
task, polls for marker acknowledgement plus `task_complete`, and compares config/thread isolation.

Use the output to identify:

- the target title, cwd/project, model, reasoning effort, archived flag, and rollout path;
- the latest user/agent/task-complete signals;
- whether the tail suggests the session may be mid-turn;
- whether the instruction is a handoff, oversight request, status check, continuation, review,
  wait/watch request, or management request.

If the inspector is ambiguous, read the referenced rollout JSONL directly with targeted grep/tail
before asking the user. Ask one concise question only when sending would risk interrupting or
misdirecting the wrong thread.

### Send rule

Send only after inspection and only when the invocation contains, or clearly implies, a task for
Codex. Use the maintained wrapper, not raw IPC:

```bash
./scripts/handoff_to_codex.sh --ipc <conversationId> "<task>"
```

`--allow-any-thread` is accepted for the long-term explicit-thread path because production `--ipc`
requires a caller-supplied UUID, the router is conversation-scoped, and the script writes a
file-drop fallback first. Keep the invariant: one explicit conversationId per send.

Do not send while the target appears mid-turn unless the user explicitly asked to interrupt,
continue, or manage that active state. Never use `turn/interrupt`, config/account/plugin methods,
or direct SQLite writes as part of `/ipc`.

### Watch/status mode

For `/ipc <conversationId>` with no task, report status only. For `watch`, repeat read-only
inspection at a conservative interval and stop when the user-specified condition is met or when a
clear `task_complete`/idle signal appears. Do not send during watch mode unless the user separately
requests a send.

## New-session mode

No UUID means there is not yet a proven IPC target. Resolve the intended workspace first.

Known local Codex Desktop project folders:

- `C:\Users\benny\OneDrive\Desktop\project6_REPO_MCP_FOLDER`
- `C:\Users\benny\OneDrive\Desktop\land_diligence_dual_agent_workspace`

Prefer an explicit path or project name in the command. If absent, infer from the current repo and
current conversation context. If it is genuinely ambiguous between the known projects, ask one
concise question before creating/opening the wrong context.

To open the correct project in Codex Desktop:

```bash
./scripts/handoff_to_codex.sh --app
```

or run `codex app <workspace>` from the intended workspace.

After the Desktop project/session exists, obtain a concrete conversationId before using `--ipc`.
Use the read-only locator to discover candidates from Codex Desktop's local thread index:

```bash
node scripts/codex_ipc_thread_locator.mjs --project <project-folder-name> --limit 10
node scripts/codex_ipc_thread_locator.mjs --cwd <absolute-workspace-path> --since-iso <timestamp-before-open>
```

If the user created a clearly titled waiting thread, narrow with `--title-contains <text>` and
`--require-single`. A locator result is only candidate discovery, not send authority. If exactly
one intended candidate remains, run `codex_ipc_session_inspect.mjs` on that conversationId and then
apply the existing-session send rule. If no candidate or multiple plausible candidates remain,
fall back to the file-drop handoff and ask the user to select/create the Desktop thread and paste
the pickup line or provide the session id.

Default desired target configuration for a fresh Codex session is the latest/highest setting
currently used by the user (`gpt-5.5`, `xhigh` as of this skill). Do not claim `/ipc` can set those
values through the owner-renderer route; model/reasoning are controlled by the Desktop thread.
Mention desired model/reasoning in the task only when it matters.

## Cross-session context

Every `handoff_to_codex.sh` handoff includes Claude's session id and transcript path so Codex can
inspect the full Claude transcript if needed. For `--ipc`, Claude already knows the Codex
conversationId, which is the rollout id and can be used to find the full Codex JSONL transcript
under `~/.codex/sessions/`.

Transcript pointers expose full session context and may include unrelated material. Use them for
orientation and verification, not for broad disclosure outside the local machine.

## Invariants

- Inspect existing sessions before sending.
- Use exactly one explicit UUID per IPC send.
- Keep file-drop as default/fallback.
- Use `node scripts/codex_ipc_contract_audit.mjs` when you need a static requirement-by-requirement
  audit of the IPC contract from repo artifacts.
- Treat GUI visibility as user-confirmed for the proven Desktop path, but revalidate after Codex
  Desktop updates because the IPC route uses undocumented internals. Use
  `codex_ipc_write_proof.mjs` for any future controlled live-write re-proof.
- Do not modify global Codex config, account state, plugins, marketplace, thread archive state, or
  SQLite directly.
- Keep all assertions scoped to the evidence actually inspected in the current run.
