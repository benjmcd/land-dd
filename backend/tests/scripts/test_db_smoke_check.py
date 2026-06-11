from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_db_smoke_module() -> ModuleType:
    module_path = REPO_ROOT / "scripts" / "db_smoke_check.py"
    spec = importlib.util.spec_from_file_location("db_smoke_check", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_db_smoke_loads_current_registry_ids() -> None:
    module = _load_db_smoke_module()

    registry_ids = module._load_expected_source_registry_ids()

    assert len(registry_ids) == 25
    assert {"DS-001", "DS-017", "DS-023", "DS-025"}.issubset(registry_ids)


def test_db_smoke_allows_runtime_sources_without_registry_ids() -> None:
    module = _load_db_smoke_module()
    expected = {"DS-001", "DS-002"}

    module._validate_seeded_source_registry_ids({"DS-001": 1, "DS-002": 1}, expected)


@pytest.mark.parametrize(
    ("registry_counts", "expected_error"),
    [
        ({"DS-001": 1}, "Missing seeded source registry IDs"),
        ({"DS-001": 1, "DS-002": 1, "DS-999": 1}, "Unexpected seeded source registry IDs"),
        ({"DS-001": 2, "DS-002": 1}, "Duplicated seeded source registry IDs"),
    ],
)
def test_db_smoke_fails_closed_for_registry_seed_mismatches(
    registry_counts: dict[str, int],
    expected_error: str,
) -> None:
    module = _load_db_smoke_module()

    with pytest.raises(SystemExit, match=expected_error):
        module._validate_seeded_source_registry_ids(
            registry_counts,
            {"DS-001", "DS-002"},
        )
