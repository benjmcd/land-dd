#!/usr/bin/env bash
# Hand off work from Claude Code to Codex.
#
# DEFAULT (file-drop, GUI-safe): write a self-contained handoff to the inbox, then you
# paste one line into your live Codex session (Desktop app or TUI) to pick it up.
#   ./scripts/handoff_to_codex.sh "task for Codex"
#
# This is the recommended path: it appears in the Codex Desktop GUI (because YOUR own
# session reads the file), and it has zero effect on any other running Codex session.
#
# Other modes:
#   ./scripts/handoff_to_codex.sh --ipc <conversationId> "task"  # inject into a live Desktop GUI thread
#   ./scripts/handoff_to_codex.sh --open [session_id]   # open a session in the terminal TUI
#   ./scripts/handoff_to_codex.sh --app                 # open the workspace in the Codex desktop app
#   ./scripts/handoff_to_codex.sh --exec "task" [sid]   # HEADLESS exec (NOT visible in the GUI)
#
# Why --exec is not the default: `codex exec` writes only to the JSONL rollout files, while
# the Desktop app renders from a separate SQLite store. Exec handoffs therefore never appear
# in the Desktop GUI. Use --exec only for fire-and-forget tasks where you read the reply file.
#
# Optional env:
#   CODEX_SESSION_ID=<uuid>        target a specific session (positional arg overrides this)
#   CODEX_REASONING_EFFORT=xhigh   advisory note added to the handoff (file-drop) / pin (--exec)

set -euo pipefail

# --- Resolve main workspace root (works from any worktree) ---
PROJECT_ROOT=$(git worktree list 2>/dev/null | head -1 | awk '{print $1}')
if [[ -z "$PROJECT_ROOT" ]]; then
    echo "ERROR: Could not resolve project root. Run from within the git repository." >&2
    exit 1
fi

INBOX="${PROJECT_ROOT}/state/agent-inbox"
OUTBOUND="${INBOX}/for-codex.md"   # Claude Code -> Codex
INBOUND="${INBOX}/for-claude.md"   # Codex -> Claude Code

is_uuid() { [[ "${1:-}" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; }
need_codex() {
    command -v codex &>/dev/null || { echo "ERROR: 'codex' not found on PATH. Install the Codex CLI first." >&2; exit 1; }
}

# --- Parse mode and arguments ---
MODE="filedrop"
SESSION_ID="${CODEX_SESSION_ID:-}"
IPC_CID=""
TASK=""

case "${1:-}" in
    --exec)
        MODE="exec"; shift
        if [[ -z "${1:-}" ]]; then
            echo "ERROR: --exec requires a task: $0 --exec \"task\" [session_id]" >&2
            exit 1
        fi
        TASK="${1}"
        is_uuid "${2:-}" && SESSION_ID="${2}"
        ;;
    --ipc)
        MODE="ipc"; shift
        if ! is_uuid "${1:-}"; then
            echo "ERROR: --ipc requires a conversationId (UUID): $0 --ipc <conversationId> \"task\"" >&2
            echo "Find the id in the Codex Desktop thread, or via state inspection. Mechanism injects" >&2
            echo "straight into that live GUI thread; falls back to file-drop on any failure." >&2
            exit 1
        fi
        IPC_CID="${1}"; shift
        if [[ -z "${1:-}" ]]; then
            echo "ERROR: --ipc requires a task: $0 --ipc <conversationId> \"task\"" >&2
            exit 1
        fi
        TASK="${1}"
        ;;
    --open)
        MODE="open"
        is_uuid "${2:-}" && SESSION_ID="${2}"
        ;;
    --app)
        MODE="app"
        ;;
    "")
        printf "ERROR: No task provided.\n\nUsage:\n  %s \"task for Codex\"               # file-drop handoff (recommended default)\n  %s --ipc <conversationId> \"task\"  # inject into a live Desktop GUI thread (opt-in)\n  %s --open [session_id]            # open session in TUI\n  %s --app                          # open Codex desktop app\n  %s --exec \"task\" [session_id]     # headless exec (not visible in GUI)\n" "$0" "$0" "$0" "$0" "$0" >&2
        exit 1
        ;;
    --*)
        echo "ERROR: Unknown flag '$1'." >&2
        exit 1
        ;;
    *)
        TASK="${1}"
        is_uuid "${2:-}" && SESSION_ID="${2}"
        ;;
esac

# --- OPEN IN DESKTOP APP ---
if [[ "$MODE" == "app" ]]; then
    need_codex
    echo "Opening Codex desktop app at ${PROJECT_ROOT}..."
    codex app "${PROJECT_ROOT}"
    exit 0
fi

# --- OPEN IN TUI ---
if [[ "$MODE" == "open" ]]; then
    need_codex
    echo "Opening Codex TUI${SESSION_ID:+ (session: ${SESSION_ID})}..."
    (
        cd "${PROJECT_ROOT}"
        if [[ -n "$SESSION_ID" ]]; then
            codex resume "${SESSION_ID}"
        else
            codex resume --last
        fi
    )
    exit $?
fi

# --- Gather git context (shared by file-drop and exec) ---
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|.*/||' || echo "main")
STAMP=$(date '+%Y-%m-%d %H:%M:%S %Z' 2>/dev/null || echo "unknown time")
RECENT_COMMITS=$(git log --oneline "${MAIN_BRANCH}..HEAD" 2>/dev/null \
    || git log --oneline -8 2>/dev/null \
    || echo "(no git log available)")
DIFF_STAT=$(git diff --stat "${MAIN_BRANCH}" 2>/dev/null \
    || git diff --stat HEAD 2>/dev/null \
    || echo "(no diff available)")
UNCOMMITTED=$(git status --short 2>/dev/null || echo "")
EFFORT_NOTE=""
[[ -n "${CODEX_REASONING_EFFORT:-}" ]] && EFFORT_NOTE="
## Suggested reasoning effort
${CODEX_REASONING_EFFORT}"

# --- Resolve Claude's own session transcript (for cross-agent context inspection) ---
# CLAUDE_CODE_SESSION_ID is injected by Claude Code. Allow CLAUDE_SESSION_ID / CLAUDE_TRANSCRIPT
# overrides; otherwise derive the path, falling back to the newest transcript in this project.
CLAUDE_SID="${CLAUDE_SESSION_ID:-${CLAUDE_CODE_SESSION_ID:-}}"
CLAUDE_PROJ_DIR="${HOME}/.claude/projects/$(printf '%s' "$PROJECT_ROOT" | tr ':/_' '---')"
CLAUDE_TRANSCRIPT="${CLAUDE_TRANSCRIPT:-}"
if [[ -z "$CLAUDE_TRANSCRIPT" ]]; then
    if [[ -n "$CLAUDE_SID" && -f "${CLAUDE_PROJ_DIR}/${CLAUDE_SID}.jsonl" ]]; then
        CLAUDE_TRANSCRIPT="${CLAUDE_PROJ_DIR}/${CLAUDE_SID}.jsonl"
    elif [[ -d "$CLAUDE_PROJ_DIR" ]]; then
        CLAUDE_TRANSCRIPT=$(ls -t "${CLAUDE_PROJ_DIR}"/*.jsonl 2>/dev/null | head -1 || echo "")
        [[ -z "$CLAUDE_SID" && -n "$CLAUDE_TRANSCRIPT" ]] && CLAUDE_SID=$(basename "$CLAUDE_TRANSCRIPT" .jsonl)
    fi
fi
# Convert MSYS path (/c/...) to Windows forward-slash form (C:/...) so Codex on Windows resolves it.
CLAUDE_TRANSCRIPT_WIN=$(printf '%s' "$CLAUDE_TRANSCRIPT" | sed 's|^/\([a-zA-Z]\)/|\U\1:/|')

# --- Build handoff payload ---
read -r -d '' PAYLOAD <<EOF || true
# Handoff from Claude Code -> Codex

Generated: ${STAMP} on branch \`${BRANCH}\`

## How to use this file
You (Codex) have been handed follow-up work from a Claude Code session.
Read the **Task** below and complete it in the main workspace at:
  ${PROJECT_ROOT}
When finished, append your reply/result (under a \`[From Codex]\` header) to:
  ${INBOUND}
so Claude Code can pick it up. Use that absolute path — your session may be
rooted in a different worktree than where this handoff was written.

## Branch
${BRANCH}  (merge target: ${MAIN_BRANCH})

## Commits on this branch (not yet on ${MAIN_BRANCH})
${RECENT_COMMITS}

## Files changed vs ${MAIN_BRANCH}
${DIFF_STAT}${UNCOMMITTED:+

## Uncommitted changes
${UNCOMMITTED}}${EFFORT_NOTE}

## Task
${TASK}

## Claude session context (optional — for deeper investigation)
Produced by Claude Code session: ${CLAUDE_SID:-unknown}
To inspect Claude's full transcript/reasoning behind this handoff, read this JSONL file (it is
large — grep or tail it for the relevant part; it may include context unrelated to this task):
  ${CLAUDE_TRANSCRIPT_WIN:-(transcript path unavailable on this machine)}

When you reply in ${INBOUND}, include your Codex session/conversation id if it is available to
you. (If it is not exposed to you, that is fine: for --ipc handoffs Claude already knows it as the
conversationId, and can otherwise locate your rollout under ~/.codex/sessions/ by this handoff.)
EOF

mkdir -p "$INBOX"

# --- FILE-DROP (default) ---
if [[ "$MODE" == "filedrop" ]]; then
    printf '%s\n' "$PAYLOAD" > "$OUTBOUND"
    echo "[ Handoff written to ${OUTBOUND} ]"
    echo ""
    echo "Next step -- in your Codex session (Desktop app or TUI), paste:"
    echo ""
    echo "    read state/agent-inbox/for-codex.md and proceed"
    echo ""
    echo "If that Codex session is NOT rooted at the main workspace (e.g. it is in a"
    echo "worktree), paste the full path instead so it resolves:"
    echo ""
    echo "    read ${OUTBOUND} and proceed"
    echo ""
    echo "When Codex finishes, it appends to ${INBOUND} (Claude Code reads it)."
    exit 0
fi

# --- IPC INJECT (opt-in; delivers straight into a live Desktop GUI thread) ---
# Writes the file-drop first (so the fallback is always ready), then injects the
# pickup line into the live thread via the proven owner-gated router route.
# Model/reasoning are renderer-controlled: this CANNOT change the thread's model
# or reasoning effort, nor any other session's. Falls back to file-drop on failure.
if [[ "$MODE" == "ipc" ]]; then
    printf '%s\n' "$PAYLOAD" > "$OUTBOUND"
    echo "[ Handoff written to ${OUTBOUND} ]"
    SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
    fallback() {
        echo "" >&2
        echo "FALLBACK -- file-drop is ready. In your Codex session, paste:" >&2
        echo "    read ${OUTBOUND} and proceed" >&2
    }
    if ! command -v node &>/dev/null; then
        echo "ERROR: node not found; --ipc needs Node." >&2
        fallback
        exit 1
    fi
    echo "Injecting pickup line into live Desktop thread ${IPC_CID} via IPC router..."
    if node "${SCRIPT_DIR}/codex_ipc_client.mjs" \
            --thread "${IPC_CID}" \
            --task "read '${OUTBOUND}' and proceed" \
            --allow-any-thread --send --ack-live-write --timeout-ms 9000 >/dev/null 2>&1; then
        echo "[ Delivered into live thread ${IPC_CID}. It should appear in your Codex Desktop GUI. ]"
        echo "Codex's reply will append to ${INBOUND} (Claude Code reads it)."
        exit 0
    fi
    echo "ERROR: IPC delivery failed (thread not open/owned in the Desktop app, or router unavailable)." >&2
    fallback
    exit 1
fi

# --- HEADLESS EXEC (opt-in; NOT visible in the Desktop GUI) ---
if [[ "$MODE" == "exec" ]]; then
    need_codex
    REASONING_EFFORT="${CODEX_REASONING_EFFORT:-xhigh}"
    MODEL=$(grep -E '^model\s*=' ~/.codex/config.toml 2>/dev/null | head -1 | awk -F'"' '{print $2}')
    MODEL="${MODEL:-gpt-5.5}"
    RESUME_ARGS=()
    if [[ -n "$SESSION_ID" ]]; then RESUME_ARGS=("$SESSION_ID"); else RESUME_ARGS=("--last"); fi

    echo "NOTE: --exec is headless. The result will NOT appear in the Codex Desktop GUI."
    echo "Sending to Codex (model: ${MODEL}, reasoning: ${REASONING_EFFORT}${SESSION_ID:+, session: ${SESSION_ID}})..."
    (
        cd "${PROJECT_ROOT}"
        # -m and -c are per-invocation pins: they do NOT modify ~/.codex/config.toml and have
        # NO effect on any other running Codex session.
        printf '%s\n' "$PAYLOAD" \
            | codex exec resume "${RESUME_ARGS[@]}" - \
                -o "$INBOUND" \
                -m "$MODEL" \
                -c "model_reasoning_effort=${REASONING_EFFORT}" \
                2>&1 \
            | grep -v "failed to load skill" \
            | grep -v "ERROR codex_core" \
            | grep -v "ERROR codex_memories" \
            | grep -v "^SUCCESS: The process with PID" \
            | grep -v "^tokens used" \
            | grep -v "^[0-9][0-9,]*$"
    )
    echo ""
    echo "[ Reply saved to ${INBOUND#"${PROJECT_ROOT}/"} ]"
    exit 0
fi
