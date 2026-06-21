#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python scripts/bologna_pilot_scope_authority_check.py
echo "Bologna pilot scope authority check: ok"
