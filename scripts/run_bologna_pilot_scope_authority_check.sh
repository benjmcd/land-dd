#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" scripts/bologna_pilot_scope_authority_check.py "$@"
if [[ "$#" -eq 0 ]]; then
  echo "Bologna pilot scope authority check: ok"
fi
