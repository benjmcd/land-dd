from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = ROOT / "local_artifacts" / "openapi.generated.json"


def main() -> None:
    output_path = DEFAULT_OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema: dict[str, Any] = create_app().openapi()
    output_path.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"openapi export: wrote {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
