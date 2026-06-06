#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# 1. Validate config/data_retention.yaml exists and is parseable
if [[ ! -f "config/data_retention.yaml" ]]; then
  echo "config/data_retention.yaml not found" >&2
  exit 1
fi

python -c "import yaml; yaml.safe_load(open('config/data_retention.yaml', encoding='utf-8'))"
echo "config/data_retention.yaml: parseable"

# 2. Validate docs/runbooks/data_retention.md exists
if [[ ! -f "docs/runbooks/data_retention.md" ]]; then
  echo "docs/runbooks/data_retention.md not found" >&2
  exit 1
fi
echo "docs/runbooks/data_retention.md: exists"

# 3. Validate each retention class has required fields
python - <<'PY'
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path.cwd()
REQUIRED_FIELDS = {"id", "description", "retention_period", "deletion_approach", "blocker"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


catalog = yaml.safe_load((ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"))
require(isinstance(catalog, dict), "data_retention.yaml must be a mapping")
require(catalog.get("schema_version") == "data_retention_v1", "unexpected schema_version")
require(catalog.get("operator_runbook") == "docs/runbooks/data_retention.md", "operator_runbook mismatch")

classes = catalog.get("retention_classes")
require(isinstance(classes, list) and len(classes) >= 6, "retention_classes must be a list with at least 6 items")

ids_seen: set[str] = set()
for cls in classes:
    require(isinstance(cls, dict), "each retention class must be a mapping")
    missing = REQUIRED_FIELDS - set(cls.keys())
    require(not missing, f"retention class missing fields: {sorted(missing)} in {cls.get('id', '?')}")
    cls_id = cls["id"]
    require(cls_id not in ids_seen, f"duplicate retention class id: {cls_id}")
    ids_seen.add(cls_id)

REQUIRED_IDS = {"report_runs", "evidence_observations", "audit_events", "source_ingest_runs"}
missing_ids = REQUIRED_IDS - ids_seen
require(not missing_ids, f"retention_classes missing required ids: {sorted(missing_ids)}")

blockers = catalog.get("retention_blockers")
require(isinstance(blockers, list) and blockers, "retention_blockers must be a non-empty list")
for blocker in blockers:
    require(isinstance(blocker, dict), "each retention blocker must be a mapping")
    require("id" in blocker and "status" in blocker and "reason" in blocker, f"blocker missing fields: {blocker}")
    require(blocker["status"] == "blocked", f"blocker {blocker['id']} must have status=blocked")

print("retention catalog validation: ok")
PY

echo "PASS"
exit 0
