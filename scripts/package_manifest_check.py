from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SCHEMA = "release_package_manifest_v1"
EXPECTED_SOURCE = "current_worktree"
EXPECTED_LIMITS = {
    "pushes_registry_image": False,
    "creates_hosted_deployment": False,
    "includes_secrets": False,
}


class PackageManifestError(RuntimeError):
    """Raised when a built release package cannot be trusted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PackageManifestError(message)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"JSON object required: {path}")
    return cast(dict[str, Any], payload)


def require_text(value: object, label: str) -> str:
    require(isinstance(value, str) and bool(value), f"{label} must be a non-empty string")
    return cast(str, value)


def require_bool(value: object, label: str) -> bool:
    require(isinstance(value, bool), f"{label} must be a boolean")
    return cast(bool, value)


def require_int(value: object, label: str) -> int:
    require(isinstance(value, int) and value >= 0, f"{label} must be a non-negative int")
    return cast(int, value)


def require_mapping(value: object, label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be a mapping")
    return cast(dict[str, Any], value)


def require_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    require(isinstance(value, list), f"{key} must be a list")
    items = cast(list[object], value)
    result: list[str] = []
    for item in items:
        require(isinstance(item, str) and bool(item), f"{key} entries must be strings")
        result.append(cast(str, item))
    return result


def load_package_config(root: Path) -> dict[str, Any]:
    config_path = root / "config" / "release_package.yaml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "release package config must be a mapping")
    require(
        payload.get("schema_version") == "release_package_v1",
        "unexpected release package config schema",
    )
    return cast(dict[str, Any], payload)


def require_relative_package_path(value: object, label: str) -> PurePosixPath:
    text = require_text(value, label).replace("\\", "/")
    path = PurePosixPath(text)
    require(not path.is_absolute(), f"{label} must be relative")
    require(".." not in path.parts, f"{label} must not contain parent traversal")
    require("." not in path.parts, f"{label} must not contain current-directory segments")
    require(bool(path.parts), f"{label} must not be empty")
    return path


def boundary_includes_path(
    path: PurePosixPath,
    includes: set[str],
    exclude_parts: set[str],
    exclude_suffixes: set[str],
) -> bool:
    if set(path.parts) & exclude_parts:
        return False
    if path.suffix in exclude_suffixes:
        return False
    for include_text in includes:
        include = PurePosixPath(include_text.replace("\\", "/"))
        if path == include or include in path.parents:
            return True
    return False


def is_forbidden_secret_or_state_path(path: PurePosixPath) -> bool:
    if path.name == ".env":
        return True
    if path.name.startswith(".env.") and path.name != ".env.example":
        return True
    return any(part in {".git", "local_artifacts", "agent-inbox"} for part in path.parts)


def normalized_external_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "zip_sha256"}


def validate_limits(manifest: dict[str, Any]) -> None:
    limits = require_mapping(manifest.get("limits"), "limits")
    for key, expected in EXPECTED_LIMITS.items():
        actual = require_bool(limits.get(key), f"limits.{key}")
        require(actual is expected, f"manifest limit must be {key}={str(expected).lower()}")


def validate_manifest(manifest_path: Path, root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    require(manifest_path.is_file(), f"release manifest missing: {manifest_path}")
    require(
        manifest_path.is_relative_to(root),
        "release manifest must be inside the repository root",
    )

    config = load_package_config(root)
    manifest_name = require_text(config.get("manifest_filename"), "manifest_filename")
    includes = set(require_string_list(config, "include_paths"))
    exclude_parts = set(require_string_list(config, "exclude_path_parts"))
    exclude_suffixes = set(require_string_list(config, "exclude_suffixes"))

    manifest = read_json_object(manifest_path)
    require(manifest.get("schema_version") == EXPECTED_SCHEMA, "unexpected manifest schema")
    require(manifest.get("source") == EXPECTED_SOURCE, "unexpected manifest source")
    package_id = require_text(manifest.get("package_id"), "package_id")
    require(package_id.startswith("land-diligence-"), "unexpected package_id")
    validate_limits(manifest)

    zip_relative = require_relative_package_path(manifest.get("zip_path"), "zip_path")
    zip_path = (root / zip_relative.as_posix()).resolve()
    require(zip_path.is_relative_to(root), "zip path must stay inside repository root")
    require(zip_path.is_file(), f"release package ZIP missing: {zip_relative.as_posix()}")
    expected_zip_hash = require_text(manifest.get("zip_sha256"), "zip_sha256")
    require(
        sha256_file(zip_path) == expected_zip_hash,
        "release package ZIP hash does not match manifest",
    )

    files = manifest.get("files")
    require(isinstance(files, list), "manifest files must be a list")
    file_items = cast(list[object], files)
    file_count = require_int(manifest.get("file_count"), "file_count")
    require(file_count == len(file_items), "file_count does not match files list")

    records: dict[str, dict[str, Any]] = {}
    for index, raw_record in enumerate(file_items):
        record = require_mapping(raw_record, f"files[{index}]")
        relative = require_relative_package_path(record.get("path"), f"files[{index}].path")
        path_text = relative.as_posix()
        require(path_text not in records, f"duplicate manifest file path: {path_text}")
        require(
            boundary_includes_path(relative, includes, exclude_parts, exclude_suffixes),
            f"manifest file is outside package boundary: {path_text}",
        )
        require(
            not is_forbidden_secret_or_state_path(relative),
            f"manifest file includes forbidden local state or secret path: {path_text}",
        )
        require_int(record.get("size_bytes"), f"files[{index}].size_bytes")
        digest = require_text(record.get("sha256"), f"files[{index}].sha256")
        require(
            len(digest) == 64 and all(char in "0123456789abcdef" for char in digest),
            f"files[{index}].sha256 must be lowercase sha256 hex",
        )
        records[path_text] = record

    with zipfile.ZipFile(zip_path) as archive:
        names = {info.filename for info in archive.infolist() if not info.is_dir()}
        allowed_names = set(records) | {manifest_name}
        extra_names = sorted(names - allowed_names)
        missing_names = sorted(allowed_names - names)
        require(not extra_names, f"ZIP contains undeclared entries: {extra_names}")
        require(not missing_names, f"ZIP missing declared entries: {missing_names}")

        embedded_manifest = json.loads(archive.read(manifest_name).decode("utf-8"))
        require(
            embedded_manifest == normalized_external_manifest(manifest),
            "embedded manifest does not match external manifest",
        )

        for path_text, record in records.items():
            payload = archive.read(path_text)
            require(
                len(payload) == record["size_bytes"],
                f"ZIP entry size mismatch: {path_text}",
            )
            require(
                sha256_bytes(payload) == record["sha256"],
                f"ZIP entry hash mismatch: {path_text}",
            )

    return manifest


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a built release package ZIP against its JSON manifest.",
    )
    parser.add_argument(
        "manifest",
        type=Path,
        help="Path to land-diligence-<version>-release-manifest.json",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        manifest = validate_manifest(args.manifest)
    except (PackageManifestError, OSError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"package manifest check failed: {exc}", file=sys.stderr)
        return 1

    print(f"package manifest check: ok {manifest['package_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
