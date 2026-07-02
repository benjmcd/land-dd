#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-${LAND_DD_PYTHON_EXECUTABLE:-python}}"

if [[ ! -f "./scripts/authority_evidence_intake_check.py" ]]; then
  echo "required authority evidence artifact missing: scripts/authority_evidence_intake_check.py" >&2
  exit 1
fi

"$PYTHON_BIN" ./scripts/authority_evidence_intake_check.py "$@"
echo "authority evidence intake: ok"
