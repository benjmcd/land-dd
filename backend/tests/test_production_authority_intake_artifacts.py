from __future__ import annotations

import importlib.util
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "production_authority_intake.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "production_authority_intake_check.py"
    spec = importlib.util.spec_from_file_location(
        "production_authority_intake_check",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(catalog, dict)
    return cast(dict[str, Any], catalog)


def test_production_authority_intake_is_validate_only_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()

    assert catalog["schema_version"] == "production_authority_intake_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/production_authority_intake.md"
    assert catalog["status"] == "blocked_no_external_authority"
    assert catalog["validation"] == "scripts/run_production_authority_intake_check.ps1"
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert catalog["limits"]["validate_only_intake"] is True
    for key, value in catalog["limits"].items():
        if key != "validate_only_intake":
            assert value is False


def test_production_authority_intake_streams_remain_uncited_and_unpromoted() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()
    streams = {stream["id"]: stream for stream in catalog["authority_streams"]}

    assert set(streams) == validator.EXPECTED_STREAMS
    for stream in streams.values():
        assert stream["status"] == "blocked"
        assert stream["evidence_status"] == "missing"
        assert stream["authority_references"] == []
        assert stream["decision_updates_allowed"] is False


def test_production_authority_intake_matches_authority_catalogs() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_production_authority_intake_validator_fails_if_authority_promoted(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["authority_streams"][0]["decision_updates_allowed"] = True

    def fake_read_text(path: str) -> str:
        if path == "config/production_authority_intake.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="updates unexpectedly allowed"):
        validator.validate_catalog()


def test_production_authority_intake_validator_fails_if_blockers_drift(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    hosted_stream = next(
        stream
        for stream in catalog["authority_streams"]
        if stream["id"] == "hosted_platform"
    )
    hosted_stream["required_evidence"].append("uncited_extra_blocker")

    def fake_read_text(path: str) -> str:
        if path == "config/production_authority_intake.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="hosted intake blockers drifted"):
        validator.validate_catalog()


def test_production_authority_intake_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/production_authority_intake_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "production authority intake check: ok"
    ps1 = (
        REPO_ROOT / "scripts" / "run_production_authority_intake_check.ps1"
    ).read_text(encoding="utf-8")
    sh = (
        REPO_ROOT / "scripts" / "run_production_authority_intake_check.sh"
    ).read_text(encoding="utf-8")
    for script in (ps1, sh):
        assert "production_authority_intake_check.py" in script
        assert "production authority intake check: ok" in script
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_production_authority_intake_runbook_preserves_boundary() -> None:
    runbook = (
        REPO_ROOT / "docs" / "runbooks" / "production_authority_intake.md"
    ).read_text(encoding="utf-8")

    for phrase in (
        "production_authority_intake_v1",
        "validate-only",
        "does not approve sources",
        "authority_references",
        "decision_updates_allowed",
        "Level 10 authority",
    ):
        assert phrase in runbook
