#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python scripts/bologna_source_authority_intake_check.py
echo "Bologna source authority intake check: ok"
