#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

echo "== workspace structure =="
required=(
  AGENTS.md
  CLAUDE.md
  README.md
  MANIFEST.md
  docs/ARCHITECTURE.md
  docs/PRODUCT_SPEC.md
  docs/POSTGRES_FIRST_STORAGE.md
  .agent/PLANS.md
  .codex/config.toml
  plans/2026-06-03-foundation-vertical-slice.md
  tasks/task_queue.yaml
  state/PROJECT_STATE.md
  backend/pyproject.toml
  db/migrations/0001_initial_spine.sql
)
for f in "${required[@]}"; do
  [[ -f "$f" ]] || { echo "missing $f" >&2; exit 1; }
done

./scripts/agent-context-check.sh
"$PYTHON_BIN" scripts/check_json_files.py
"$PYTHON_BIN" scripts/check_source_registry.py

echo "workspace validation: ok"
