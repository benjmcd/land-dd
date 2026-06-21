#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-${LAND_DD_PYTHON_EXECUTABLE:-python}}"

if [[ ! -f "./scripts/qualification_change_impact_check.py" ]]; then
  echo "required qualification artifact missing: scripts/qualification_change_impact_check.py" >&2
  exit 1
fi

"$PYTHON_BIN" ./scripts/qualification_change_impact_check.py --root . "$@"
echo "qualification change impact: ok"
