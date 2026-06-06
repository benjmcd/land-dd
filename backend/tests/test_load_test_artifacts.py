from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_run_load_test_ps1_exists_and_is_not_empty() -> None:
    path = REPO_ROOT / "scripts" / "run_load_test.ps1"
    assert path.is_file(), f"missing: {path}"
    assert os.path.getsize(path) > 0, f"empty: {path}"


def test_run_load_test_sh_exists_and_is_not_empty() -> None:
    path = REPO_ROOT / "scripts" / "run_load_test.sh"
    assert path.is_file(), f"missing: {path}"
    assert os.path.getsize(path) > 0, f"empty: {path}"


def test_load_testing_runbook_exists_and_is_not_empty() -> None:
    path = REPO_ROOT / "docs" / "runbooks" / "load_testing.md"
    assert path.is_file(), f"missing: {path}"
    assert os.path.getsize(path) > 0, f"empty: {path}"


def test_load_testing_runbook_documents_validate_only_flag() -> None:
    path = REPO_ROOT / "docs" / "runbooks" / "load_testing.md"
    content = path.read_text(encoding="utf-8")
    assert "--validate-only" in content or "validate-only" in content, (
        "runbook must document the --validate-only flag"
    )


def test_load_testing_runbook_mentions_sequential_request_count() -> None:
    path = REPO_ROOT / "docs" / "runbooks" / "load_testing.md"
    content = path.read_text(encoding="utf-8")
    assert "20" in content, "runbook must mention the sequential request count (20)"


def test_load_testing_runbook_mentions_scope_limitations() -> None:
    path = REPO_ROOT / "docs" / "runbooks" / "load_testing.md"
    content = path.read_text(encoding="utf-8")
    lower = content.lower()
    assert "scope" in lower or "limitation" in lower or "sequential" in lower, (
        "runbook must describe scope limitations of the load test"
    )
