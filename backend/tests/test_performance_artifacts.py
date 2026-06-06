from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK_PATH = REPO_ROOT / "docs" / "runbooks" / "performance.md"


def _runbook_text() -> str:
    return RUNBOOK_PATH.read_text(encoding="utf-8")


def test_performance_runbook_exists_and_is_not_empty() -> None:
    assert RUNBOOK_PATH.exists(), f"performance.md not found at {RUNBOOK_PATH}"
    text = _runbook_text()
    assert text.strip(), "performance.md must not be empty"


def test_performance_runbook_contains_cache() -> None:
    assert "cache" in _runbook_text().lower(), (
        "performance.md must contain a cache strategy section"
    )


def test_performance_runbook_contains_backpressure_or_degraded() -> None:
    text = _runbook_text().lower()
    assert "backpressure" in text or "degraded" in text, (
        "performance.md must contain a backpressure or degraded-mode section"
    )


def test_performance_runbook_contains_spatial() -> None:
    assert "spatial" in _runbook_text().lower(), (
        "performance.md must contain spatial index coverage documentation"
    )


def test_performance_runbook_contains_db_pool_size() -> None:
    assert "DB_POOL_SIZE" in _runbook_text(), (
        "performance.md must document the DB_POOL_SIZE setting"
    )


def test_performance_runbook_contains_load_test() -> None:
    text = _runbook_text().lower()
    assert "load_test" in text or "run_load_test" in text, (
        "performance.md must reference load_test or run_load_test"
    )
