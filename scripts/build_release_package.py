from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "release_package.yaml"


def fail(message: str) -> None:
    raise SystemExit(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def as_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise SystemExit(f"{key} must be a list")
    result: list[str] = []
    for item in value:
        require(isinstance(item, str) and bool(item), f"{key} entries must be strings")
        result.append(item)
    return result


def normalized_version(raw_version: str) -> str:
    if raw_version:
        require(
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", raw_version) is not None,
            "version must be 1-64 chars of letters, numbers, dot, underscore, or hyphen",
        )
        return raw_version
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def should_exclude(path: Path, exclude_parts: set[str], exclude_suffixes: set[str]) -> bool:
    parts = set(path.parts)
    if parts & exclude_parts:
        return True
    return path.suffix in exclude_suffixes


def iter_release_files(
    include_paths: list[str],
    exclude_parts: set[str],
    exclude_suffixes: set[str],
) -> list[Path]:
    seen: set[Path] = set()
    for include in include_paths:
        candidate = ROOT / include
        require(candidate.exists(), f"release include path missing: {include}")
        if candidate.is_file():
            relative = candidate.relative_to(ROOT)
            if not should_exclude(relative, exclude_parts, exclude_suffixes):
                seen.add(candidate)
            continue
        for file_path in candidate.rglob("*"):
            if not file_path.is_file():
                continue
            relative = file_path.relative_to(ROOT)
            if should_exclude(relative, exclude_parts, exclude_suffixes):
                continue
            seen.add(file_path)
    files = sorted(seen, key=lambda path: path.as_posix())
    require(bool(files), "release package would be empty")
    return files


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    version = normalized_version(args[0] if args else "")
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    require(isinstance(config, dict), "release package config must be a mapping")
    require(
        config.get("schema_version") == "release_package_v1",
        "unexpected release package schema",
    )
    package_name = config.get("package_name")
    require(isinstance(package_name, str) and bool(package_name), "package_name is required")
    output_dir_text = config.get("output_dir")
    require(
        isinstance(output_dir_text, str) and bool(output_dir_text),
        "output_dir is required",
    )
    manifest_name = config.get("manifest_filename")
    require(
        isinstance(manifest_name, str) and manifest_name.endswith(".json"),
        "manifest_filename must be a JSON file",
    )

    include_paths = as_list(config, "include_paths")
    exclude_parts = set(as_list(config, "exclude_path_parts"))
    exclude_suffixes = set(as_list(config, "exclude_suffixes"))
    files = iter_release_files(include_paths, exclude_parts, exclude_suffixes)

    output_dir = ROOT / output_dir_text
    output_dir.mkdir(parents=True, exist_ok=True)
    package_id = f"{package_name}-{version}"
    zip_path = output_dir / f"{package_id}.zip"
    manifest_path = output_dir / f"{package_id}-{manifest_name}"
    require(not zip_path.exists(), f"release package already exists: {zip_path}")
    require(not manifest_path.exists(), f"release manifest already exists: {manifest_path}")

    file_records = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in files
    ]
    manifest = {
        "schema_version": "release_package_manifest_v1",
        "package_id": package_id,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source": "current_worktree",
        "zip_path": zip_path.relative_to(ROOT).as_posix(),
        "file_count": len(file_records),
        "files": file_records,
        "limits": {
            "pushes_registry_image": False,
            "creates_hosted_deployment": False,
            "includes_secrets": False,
        },
    }

    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr(
            manifest_name,
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        )

    manifest["zip_sha256"] = sha256_file(zip_path)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"release package: {zip_path.relative_to(ROOT).as_posix()}")
    print(f"release manifest: {manifest_path.relative_to(ROOT).as_posix()}")
    print(f"release files: {len(file_records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
