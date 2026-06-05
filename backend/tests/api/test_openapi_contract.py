from __future__ import annotations

from pathlib import Path

from app.main import create_app

ROOT = Path(__file__).resolve().parents[3]
STUB_PATH = ROOT / "api" / "openapi_stub.yaml"
HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def test_openapi_stub_path_methods_match_runtime_schema() -> None:
    runtime_schema = create_app().openapi()
    runtime_path_methods = _path_methods_from_runtime(runtime_schema)
    stub_path_methods = _path_methods_from_stub(STUB_PATH)

    assert stub_path_methods == runtime_path_methods


def _path_methods_from_runtime(
    schema: dict[str, object],
) -> dict[str, set[str]]:
    paths = schema["paths"]
    assert isinstance(paths, dict)
    result: dict[str, set[str]] = {}
    for path, path_spec in paths.items():
        assert isinstance(path, str)
        assert isinstance(path_spec, dict)
        result[path] = {
            method
            for method in path_spec
            if isinstance(method, str) and method in HTTP_METHODS
        }
    return result


def _path_methods_from_stub(path: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    in_paths = False
    current_path: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line == "paths:":
            in_paths = True
            continue

        if in_paths and not raw_line.startswith(" "):
            break

        if not in_paths:
            continue

        if raw_line.startswith("  /") and stripped.endswith(":"):
            current_path = stripped[:-1]
            result[current_path] = set()
            continue

        if (
            current_path is not None
            and raw_line.startswith("    ")
            and not raw_line.startswith("      ")
            and stripped.endswith(":")
        ):
            method = stripped[:-1]
            if method in HTTP_METHODS:
                result[current_path].add(method)

    return result
