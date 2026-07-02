#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" scripts/production_authority_evidence_references_check.py "$@"
if [[ "$#" -eq 0 ]]; then
  echo "production authority evidence references: ok"
fi
