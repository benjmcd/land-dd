from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "local_artifacts"}
paths = [p for p in ROOT.rglob("*.json") if not SKIP_DIRS.intersection(p.parts)]
for path in paths:
    with path.open("r", encoding="utf-8") as handle:
        json.load(handle)
print(f"json check: ok ({len(paths)} files)")
