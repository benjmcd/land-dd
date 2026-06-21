from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CROSSWALK_PATH = REPO_ROOT / "config" / "qualification" / "readiness_crosswalk.yaml"


def _load_script(path: Path, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def _expected_by_checker() -> dict[str, set[str]]:
    expected: dict[str, set[str]] = {}
    for entry in _yaml(CROSSWALK_PATH)["entries"]:
        for checker_path in entry.get("checker_paths", []):
            expected.setdefault(checker_path, set()).update(entry["criterion_ids"])
    return expected


def test_each_crosswalk_checker_emits_declared_qualification_criteria() -> None:
    expected = _expected_by_checker()

    for checker_path, criterion_ids in sorted(expected.items()):
        completed = subprocess.run(
            [sys.executable, checker_path, "--qualification-criteria-json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert completed.returncode == 0, (
            checker_path,
            completed.stdout,
            completed.stderr,
        )
        payload = json.loads(completed.stdout)
        assert payload["schema_version"] == "qualification_checker_advertisement_v1"
        assert payload["checker_path"] == checker_path
        assert set(payload["criterion_ids"]) == criterion_ids


def test_validator_rejects_checker_advertisement_drift(monkeypatch: Any) -> None:
    validator = _load_script(
        REPO_ROOT / "scripts" / "validate_qualification.py",
        "validate_qualification_under_test",
    )
    real_run = validator.subprocess.run

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        command = args[0]
        checker_path = command[1]
        if checker_path == "scripts/source_readiness.py":
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps(
                    {
                        "schema_version": "qualification_checker_advertisement_v1",
                        "checker_path": checker_path,
                        "criterion_ids": ["Q1-012"],
                        "entries": [],
                    },
                ),
                stderr="",
            )
        return cast(subprocess.CompletedProcess[str], real_run(*args, **kwargs))

    monkeypatch.setattr(validator.subprocess, "run", fake_run)
    errors: list[str] = []

    validator.validate_checker_advertisements(
        root=REPO_ROOT,
        crosswalk=_yaml(CROSSWALK_PATH),
        errors=errors,
    )

    assert any(
        "checker advertisement mismatch: scripts/source_readiness.py" in error
        for error in errors
    )
