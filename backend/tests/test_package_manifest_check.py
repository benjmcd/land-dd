from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "package_manifest_check",
        REPO_ROOT / "scripts" / "package_manifest_check.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_config(root: Path) -> None:
    config_dir = root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "release_package.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "release_package_v1",
                "package_name": "land-diligence",
                "output_dir": "local_artifacts/releases",
                "manifest_filename": "release-manifest.json",
                "include_paths": ["README.md", "docs", "state"],
                "exclude_path_parts": [
                    ".git",
                    "agent-inbox",
                    "local_artifacts",
                    "__pycache__",
                ],
                "exclude_suffixes": [".log", ".pyc", ".tmp", ".bak"],
                "required_release_gates": ["scripts/verify.ps1"],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _make_package(
    root: Path,
    *,
    files: dict[str, bytes] | None = None,
    external_mutation: dict[str, Any] | None = None,
    embedded_mutation: dict[str, Any] | None = None,
    extra_entries: dict[str, bytes] | None = None,
) -> Path:
    _write_config(root)
    release_dir = root / "local_artifacts" / "releases"
    release_dir.mkdir(parents=True)
    zip_path = release_dir / "land-diligence-test.zip"
    manifest_path = release_dir / "land-diligence-test-release-manifest.json"
    package_files = files or {
        "README.md": b"# package\n",
        "docs/runbooks/release_package.md": b"release package runbook\n",
    }
    file_records = [
        {
            "path": path,
            "size_bytes": len(payload),
            "sha256": _sha256(payload),
        }
        for path, payload in sorted(package_files.items())
    ]
    embedded_manifest: dict[str, Any] = {
        "schema_version": "release_package_manifest_v1",
        "package_id": "land-diligence-test",
        "created_at": "2026-06-19T00:00:00Z",
        "source": "current_worktree",
        "zip_path": "local_artifacts/releases/land-diligence-test.zip",
        "file_count": len(file_records),
        "files": file_records,
        "limits": {
            "pushes_registry_image": False,
            "creates_hosted_deployment": False,
            "includes_secrets": False,
        },
    }
    if embedded_mutation:
        embedded_manifest.update(embedded_mutation)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, payload in package_files.items():
            archive.writestr(path, payload)
        for path, payload in (extra_entries or {}).items():
            archive.writestr(path, payload)
        archive.writestr(
            "release-manifest.json",
            json.dumps(embedded_manifest, indent=2, sort_keys=True) + "\n",
        )

    external_manifest = copy.deepcopy(embedded_manifest)
    if embedded_mutation:
        external_manifest = {
            "schema_version": "release_package_manifest_v1",
            "package_id": "land-diligence-test",
            "created_at": "2026-06-19T00:00:00Z",
            "source": "current_worktree",
            "zip_path": "local_artifacts/releases/land-diligence-test.zip",
            "file_count": len(file_records),
            "files": file_records,
            "limits": {
                "pushes_registry_image": False,
                "creates_hosted_deployment": False,
                "includes_secrets": False,
            },
        }
    external_manifest["zip_sha256"] = _sha256(zip_path.read_bytes())
    if external_mutation:
        external_manifest.update(external_mutation)
    manifest_path.write_text(
        json.dumps(external_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _expect_manifest_error(
    checker: ModuleType,
    manifest_path: Path,
    root: Path,
    match: str,
) -> None:
    error = cast(type[Exception], checker.PackageManifestError)
    with pytest.raises(error, match=match):
        checker.validate_manifest(manifest_path, root=root)


def test_package_manifest_checker_accepts_matching_zip_manifest(tmp_path: Path) -> None:
    checker = _load_checker()
    manifest_path = _make_package(tmp_path)

    manifest = checker.validate_manifest(manifest_path, root=tmp_path)

    assert manifest["package_id"] == "land-diligence-test"


def test_package_manifest_checker_rejects_zip_hash_drift(tmp_path: Path) -> None:
    checker = _load_checker()
    manifest_path = _make_package(tmp_path, external_mutation={"zip_sha256": "0" * 64})

    _expect_manifest_error(checker, manifest_path, tmp_path, "ZIP hash")


def test_package_manifest_checker_rejects_embedded_manifest_drift(
    tmp_path: Path,
) -> None:
    checker = _load_checker()
    manifest_path = _make_package(
        tmp_path,
        embedded_mutation={"package_id": "land-diligence-drifted"},
    )

    _expect_manifest_error(checker, manifest_path, tmp_path, "embedded manifest")


def test_package_manifest_checker_rejects_undeclared_zip_entries(tmp_path: Path) -> None:
    checker = _load_checker()
    manifest_path = _make_package(tmp_path, extra_entries={"unexpected.txt": b"extra\n"})

    _expect_manifest_error(checker, manifest_path, tmp_path, "undeclared entries")


def test_package_manifest_checker_rejects_excluded_paths(tmp_path: Path) -> None:
    checker = _load_checker()
    manifest_path = _make_package(
        tmp_path,
        files={"state/agent-inbox/for-codex.md": b"volatile\n"},
    )

    _expect_manifest_error(checker, manifest_path, tmp_path, "outside package boundary")


def test_package_manifest_checker_rejects_overconfident_limits(tmp_path: Path) -> None:
    checker = _load_checker()
    manifest_path = _make_package(
        tmp_path,
        external_mutation={
            "limits": {
                "pushes_registry_image": True,
                "creates_hosted_deployment": False,
                "includes_secrets": False,
            },
        },
    )

    _expect_manifest_error(checker, manifest_path, tmp_path, "pushes_registry_image=false")
