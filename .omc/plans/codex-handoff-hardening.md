# Plan: Codex Handoff Hardening

**Date:** 2026-06-04
**Status:** Draft -- pending user confirmation
**Scope:** `scripts/handoff_to_codex.sh`, `.claude/skills/handoff-to-codex`, `state/agent-inbox/README.md`
**Estimated complexity:** MEDIUM (3 files changed, 1 new file)

---

## RALPLAN-DR Summary

### Principles

1. **Determinism over convenience.** Every handoff must reach a predictable Codex session with predictable model and reasoning settings. `--last` is convenient but non-deterministic; explicit targeting is safer.
2. **Worktree-safe by default.** The script must produce correct results whether invoked from the project root, a worktree subdirectory, or a nested path.
3. **No new dependencies.** All fixes use bash builtins, git plumbing, and existing `codex exec resume` flags. No new production packages.
4. **Single-arg UX preserved.** The caller interface stays `./scripts/handoff_to_codex.sh "task"`. All complexity is internal.
5. **Fail loud, not silent.** If session resolution, model pin, or reasoning effort override fails, the script must abort with a clear message rather than silently degrade.

### Decision Drivers (top 3)

1. **Reasoning effort correctness.** The global config has `model_reasoning_effort = "low"`. Without an explicit override on `codex exec resume`, every handoff runs at low reasoning -- this is the single highest-impact bug.
2. **Session targeting reliability.** `--last` picks by modification time, not creation time. Combined with worktree cwd filtering, this is a consistent source of wrong-session delivery.
3. **Staleness elimination.** Hardcoded session ID, relative paths, and missing model pin all create drift failures that worsen over time.

### Options Considered

#### Option A: Patch the existing script with CLI flag overrides (CHOSEN)

Add `-m`, `-c model_reasoning_effort=xhigh`, `-C`, and `--all` flags to the existing `codex exec resume` invocation. Replace hardcoded session ID with a dynamic lookup. Make OUTFILE absolute.

**Pros:**
- Smallest diff. 1 file materially changed.
- Uses only documented CLI flags already verified as working.
- No architectural change to the handoff flow.

**Cons:**
- `--last --all` still picks by modification time (but `-C` to project root + `--all` makes this more predictable).
- No persistent session registry across conversations.

#### Option B: Build a session registry file that tracks Codex session IDs per branch

Write a `.omc/state/codex-sessions.json` mapping branches to session IDs. Resume by explicit ID instead of `--last`.

**Pros:**
- Fully deterministic session targeting.
- Could track reasoning effort per session.

**Cons:**
- Requires a new state file and maintenance logic.
- Session IDs become stale when Codex sessions expire or are deleted.
- Adds complexity for a problem that Option A mostly solves.
- **Invalidated:** The marginal reliability gain does not justify the maintenance cost. `--last --all -C <root>` plus explicit model/reasoning flags addresses the critical issues.

#### Option C: Replace `codex exec resume` with `codex exec` (new session each time)

**Invalidated:** Loses conversation continuity, which is valuable for multi-step handoffs (e.g., "create PR" then "merge when CI passes"). The resume model is correct; the targeting just needs to be more robust.

---

## ADR

**Decision:** Option A -- patch the existing script with CLI flag overrides and dynamic context.

**Drivers:** Reasoning effort correctness, session targeting reliability, staleness elimination.

**Alternatives considered:** Session registry (Option B, rejected: maintenance cost exceeds benefit), new-session-per-handoff (Option C, rejected: loses conversation continuity).

**Why chosen:** Smallest change that addresses all 7 confirmed gaps using only documented, tested CLI flags. No new state files or dependencies.

**Consequences:** `--last` still uses modification-time ordering, but the combination of `--all` (disables cwd filtering) and `-C` (sets working directory) makes this predictable for the common case. If the user runs many concurrent Codex sessions, the wrong session could still be picked -- but this is an edge case solvable later with Option B if needed.

**Follow-ups:** Monitor whether `--last` mis-targeting recurs. If it does, implement Option B (session registry) as a targeted addition.

---

## Guardrails

### Must Have
- Every `codex exec resume` call must include `-m <model>` and `-c model_reasoning_effort=<effort>`.
- OUTFILE must be an absolute path derived from the git toplevel.
- The script must work correctly from any worktree subdirectory.
- The hardcoded Claude session ID must be removed.
- The script must fail with a clear error if `codex` is not on PATH or if the project root cannot be determined.

### Must NOT Have
- No new production dependencies.
- No file deletions (archive if replacing).
- No changes to the caller interface (`./scripts/handoff_to_codex.sh "task"`).
- No changes to Codex's global `~/.codex/config.toml` (per-invocation overrides only).

---

## Task Flow

### Step 1: Fix the script -- session targeting, model pin, reasoning effort, paths

**Files:** `scripts/handoff_to_codex.sh`

**Changes:**

1. **Remove hardcoded `CLAUDE_SESSION`.** Replace with a dynamic marker that identifies the handoff source without a stale session ID. Use the git branch name and a timestamp instead -- these are always fresh.

2. **Add project root resolution.** At the top of the script, resolve `PROJECT_ROOT` via `git rev-parse --show-toplevel`. All relative paths become `${PROJECT_ROOT}/...`. This fixes Gap 4 (worktree CWD) and Gap 6 (relative OUTFILE).

3. **Add `-C "${PROJECT_ROOT}"` to the `codex exec resume` call.** This ensures Codex operates in the correct working directory regardless of where the script is invoked.

4. **Add `--all` to the `codex exec resume` call.** This disables cwd filtering so `--last` can find sessions created from the main workspace even when run from a worktree. This fixes Gap 4.

5. **Add `-m gpt-5.5` to the `codex exec resume` call.** Pin the model explicitly so it does not drift if the config changes. This fixes Gap 5.

6. **Add `-c model_reasoning_effort=xhigh` to the `codex exec resume` call.** Override the global `low` setting to ensure handoff tasks get high reasoning. This fixes Gap 2.

7. **Add a preamble to the CONTEXT message** stating: "Use xhigh reasoning effort for this task. Do not downgrade model or reasoning settings." This is belt-and-suspenders for Gap 7.

8. **Add a guard** at script entry: if `command -v codex` fails, exit with an error. If `git rev-parse --show-toplevel` fails, exit with an error.

**Acceptance criteria:**
- Running `./scripts/handoff_to_codex.sh "test"` from the project root produces a Codex response at `<PROJECT_ROOT>/state/agent-inbox/from-codex.md`.
- Running the same from a worktree subdirectory (e.g., `worktrees/lane-a-provenance-schemas`) also writes to the correct project-root path.
- The `codex exec resume` invocation visibly includes `-m gpt-5.5`, `-c model_reasoning_effort=xhigh`, `--all`, and `-C`.
- The CONTEXT block no longer contains a hardcoded Claude session ID.
- Script exits with error code and message if `codex` is not found or git root cannot be resolved.

### Step 2: Update the skill file to reflect new behavior

**Files:** `.claude/skills/handoff-to-codex`

**Changes:**

1. Remove the mention of `--last` as the targeting mechanism (it is an implementation detail, not a user concern).
2. Add a note that the script is worktree-safe and can be run from any directory within the project.
3. Remove any reference to the hardcoded Claude session ID.
4. Add a troubleshooting note: if Codex responds with low-quality output, verify that the `-c model_reasoning_effort=xhigh` flag is present in the script.

**Acceptance criteria:**
- The skill file accurately describes the script's current behavior.
- No stale session IDs or incorrect claims about behavior.

### Step 3: Update the inbox README

**Files:** `state/agent-inbox/README.md`

**Changes:**

1. Remove the hardcoded Claude Code session ID (`117e8bbd-...`).
2. Replace the "Codex to Claude Code" section with a generic instruction: "Write to `state/agent-inbox/for-claude.md` with a `[From Codex]` header. Claude Code will check this file."
3. Add a note that paths in the inbox are always relative to the project root.

**Acceptance criteria:**
- No hardcoded session IDs remain in any file in `state/agent-inbox/`.
- The README accurately describes the bidirectional messaging protocol.

### Step 4: Verify end-to-end

**Verification steps (to be run by the executor):**

1. From the project root, run: `./scripts/handoff_to_codex.sh "Confirm you received this message. Reply with the model you are using and your reasoning effort level."`
2. Read `state/agent-inbox/from-codex.md` and confirm:
   - Codex responded (non-empty, coherent).
   - Codex reports using gpt-5.5 (or the pinned model).
   - Response quality is consistent with xhigh reasoning (not terse/low-effort).
3. From a worktree directory, run the same command. Confirm:
   - The response is written to `<PROJECT_ROOT>/state/agent-inbox/from-codex.md`, NOT to a path relative to the worktree.
   - The response is coherent (session was found via `--all`).
4. Grep all project files for the old hardcoded session ID `117e8bbd`. Confirm zero matches.
5. Run `bash -n scripts/handoff_to_codex.sh` to confirm no syntax errors.

**Acceptance criteria:**
- All 5 verification checks pass.
- No regressions in the basic handoff flow.

---

## Gap Coverage Matrix

| Gap | Severity | Fix Location | Mechanism |
|-----|----------|-------------|-----------|
| 1. `--last` picks by mtime | CRITICAL | Step 1.4 | `--all` disables cwd filtering; `-C` sets correct root |
| 2. Reasoning effort not preserved | CRITICAL | Step 1.6 | `-c model_reasoning_effort=xhigh` override |
| 3. Hardcoded Claude session ID | CRITICAL | Steps 1.1, 2, 3 | Replace with dynamic branch+timestamp |
| 4. Worktree CWD breaks `--last` | MODERATE | Steps 1.2, 1.3, 1.4 | `PROJECT_ROOT` resolution + `-C` + `--all` |
| 5. No explicit model pin | MODERATE | Step 1.5 | `-m gpt-5.5` flag |
| 6. OUTFILE relative path | MINOR | Step 1.2 | Absolute path via `PROJECT_ROOT` |
| 7. No reasoning instruction in message | MINOR | Step 1.7 | Preamble in CONTEXT block |

---

## Success Criteria

1. All 7 gaps are addressed.
2. The caller interface is unchanged: `./scripts/handoff_to_codex.sh "task"`.
3. No new production dependencies.
4. End-to-end verification passes from both project root and worktree subdirectory.
5. No hardcoded session IDs remain in any project file.
6. Script fails loudly on missing prerequisites rather than silently degrading.
