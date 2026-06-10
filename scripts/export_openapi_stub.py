from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
OUTPUT_PATH = ROOT / "docs" / "planning_pack" / "api" / "openapi_stub.yaml"
LEGACY_STUB_PATH = ROOT / "api" / "openapi_stub.yaml"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

yaml = cast(Any, importlib.import_module("yaml"))


def main() -> None:
    from app.main import create_app  # noqa: PLC0415

    schema: dict[str, Any] = create_app().openapi()
    stub_content = yaml.safe_dump(schema, allow_unicode=True, sort_keys=False)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(stub_content, encoding="utf-8")
    print(f"openapi stub export: wrote {OUTPUT_PATH.relative_to(ROOT)}")
    LEGACY_STUB_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEGACY_STUB_PATH.write_text(stub_content, encoding="utf-8")
    print(f"openapi stub export: wrote {LEGACY_STUB_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
