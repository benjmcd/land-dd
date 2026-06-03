#!/usr/bin/env bash
set -euo pipefail

echo "== bootstrap =="
echo "Python: $(python --version)"
echo "Install backend dev dependencies if needed:"
echo '  python -m pip install -e "backend[dev]"'
echo "Then run: ./scripts/verify.sh"
