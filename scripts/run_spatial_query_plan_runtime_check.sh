#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VALIDATOR="scripts/spatial_query_plan_runtime_check.py"

if [[ ! -f "$VALIDATOR" ]]; then
  echo "spatial query-plan runtime validator missing: $VALIDATOR" >&2
  exit 1
fi

"${PYTHON_BIN:-python3}" "$VALIDATOR" "$@"
