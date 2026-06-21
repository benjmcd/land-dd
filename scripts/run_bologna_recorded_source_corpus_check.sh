#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python}"

if [[ ! -f "./scripts/bologna_recorded_source_corpus_check.py" ]]; then
  echo "required Bologna recorded-source corpus artifact missing: scripts/bologna_recorded_source_corpus_check.py" >&2
  exit 1
fi

"$PYTHON_BIN" ./scripts/bologna_recorded_source_corpus_check.py
echo "Bologna recorded-source corpus check: ok"
