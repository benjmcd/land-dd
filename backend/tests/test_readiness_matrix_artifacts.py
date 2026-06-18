from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "readiness_matrix_check.py"
    spec = importlib.util.spec_from_file_location("readiness_matrix_check", script_path)
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_readiness_matrix_validator_covers_all_level_9_and_10_gates() -> None:
    validator = cast(Any, _load_validator())

    expected_gates = validator.milestone_gate_ids()
    rows = validator.matrix_rows()

    assert expected_gates
    assert set(rows) == expected_gates


def test_readiness_matrix_validator_passes_current_artifacts() -> None:
    validator = cast(Any, _load_validator())

    validator.validate_matrix()


def test_readiness_matrix_validator_guards_high_risk_statuses() -> None:
    validator = cast(Any, _load_validator())
    rows = validator.matrix_rows()
    guarded_statuses = validator.REQUIRED_STATUS_BY_GATE

    assert set(guarded_statuses).issubset(set(rows))
    for gate_id, required_status in guarded_statuses.items():
        promoted_rows = dict(rows)
        promoted_rows[gate_id] = (
            "PROVEN_REPO_LOCAL"
            if required_status != "PROVEN_REPO_LOCAL"
            else "PARTIAL"
        )
        with pytest.raises(SystemExit, match=gate_id):
            validator.validate_guarded_statuses(promoted_rows)


def test_readiness_matrix_wrappers_call_validator() -> None:
    for path in (
        REPO_ROOT / "scripts" / "run_readiness_matrix_check.ps1",
        REPO_ROOT / "scripts" / "run_readiness_matrix_check.sh",
    ):
        text = path.read_text(encoding="utf-8")
        assert "scripts/readiness_matrix_check.py" in text or (
            "scripts\\readiness_matrix_check.py" in text
        )
