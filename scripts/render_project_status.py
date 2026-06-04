from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ["state/PROJECT_STATE.md", "state/OPEN_QUESTIONS.md", "state/VALIDATION_LOG.md"]:
    path = ROOT / rel
    print(f"\n===== {rel} =====\n")
    print(path.read_text(encoding="utf-8"))
