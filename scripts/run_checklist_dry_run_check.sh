#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

validator="./scripts/checklist_dry_run_check.py"
if [[ ! -f "$validator" ]]; then
  echo "required checklist dry-run artifact missing: scripts/checklist_dry_run_check.py" >&2
  exit 1
fi

"${PYTHON_BIN:-python}" "$validator"

echo "checklist dry-run check: ok"
