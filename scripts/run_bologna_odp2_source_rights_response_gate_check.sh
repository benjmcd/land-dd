#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/bologna_odp2_source_rights_response_gate_check.py
echo "Bologna ODP-BOL-002 source-rights response gate check: ok"
