#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/bologna_odp3_corpus_response_gate_check.py
echo "Bologna ODP-BOL-003 corpus response gate check: ok"
