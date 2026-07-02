#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXECUTABLE="${LAND_DD_PYTHON_EXECUTABLE:-python}"

"${PYTHON_EXECUTABLE}" "${SCRIPT_DIR}/bologna_owner_answer_intake_check.py"
echo "Bologna owner answer intake check: ok"
