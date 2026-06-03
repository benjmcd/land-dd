#!/usr/bin/env bash
set -euo pipefail

fail=0

check_file_exists() {
  if [[ ! -f "$1" ]]; then
    echo "missing required file: $1" >&2
    fail=1
  fi
}

check_max_lines() {
  local file="$1"
  local max_lines="$2"
  if [[ -f "$file" ]]; then
    local lines
    lines=$(wc -l < "$file" | tr -d ' ')
    if (( lines > max_lines )); then
      echo "$file has $lines lines; limit is $max_lines" >&2
      fail=1
    fi
  fi
}

check_file_exists AGENTS.md
check_file_exists CLAUDE.md
check_file_exists MANIFEST.md
check_file_exists state/PROJECT_STATE.md
check_file_exists plans/2026-06-03-foundation-vertical-slice.md
check_file_exists scripts/verify.sh

check_max_lines AGENTS.md 140
check_max_lines CLAUDE.md 80
check_max_lines MANIFEST.md 160

if [[ -f CLAUDE.md ]] && ! grep -q '^@AGENTS.md' CLAUDE.md; then
  echo "CLAUDE.md must import AGENTS.md with @AGENTS.md" >&2
  fail=1
fi

for bad in CONTEXT.md RULES.md DEVELOPMENT.md CODING_STANDARDS.md AI_NOTES.md SYSTEM_OVERVIEW.md; do
  if [[ -f "$bad" ]]; then
    echo "avoid root context-bloat file: $bad" >&2
    fail=1
  fi
done

if (( fail != 0 )); then
  exit 1
fi

echo "agent context check: ok"
