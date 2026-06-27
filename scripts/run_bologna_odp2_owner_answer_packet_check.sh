#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/bologna_odp2_owner_answer_packet_check.py
echo "Bologna ODP-BOL-002 owner answer packet check: ok"
