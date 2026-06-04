from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
paths = [p for p in ROOT.rglob("*.json") if ".venv" not in p.parts]
for path in paths:
    with path.open("r", encoding="utf-8") as handle:
        json.load(handle)
print(f"json check: ok ({len(paths)} files)")
