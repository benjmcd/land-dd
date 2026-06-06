"""Tests for US-076: jurisdiction and rulepack readiness checklists."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
JURISDICTION_CHECKLIST = REPO_ROOT / "docs" / "checklists" / "jurisdiction_readiness.md"
RULEPACK_CHECKLIST = REPO_ROOT / "docs" / "checklists" / "rulepack_readiness.md"


def test_jurisdiction_checklist_exists() -> None:
    assert JURISDICTION_CHECKLIST.exists(), (
        f"Jurisdiction readiness checklist not found at {JURISDICTION_CHECKLIST}"
    )


def test_jurisdiction_checklist_not_empty() -> None:
    content = JURISDICTION_CHECKLIST.read_text(encoding="utf-8")
    assert content.strip(), "Jurisdiction readiness checklist is empty"


def test_rulepack_checklist_exists() -> None:
    assert RULEPACK_CHECKLIST.exists(), (
        f"Rulepack readiness checklist not found at {RULEPACK_CHECKLIST}"
    )


def test_rulepack_checklist_not_empty() -> None:
    content = RULEPACK_CHECKLIST.read_text(encoding="utf-8")
    assert content.strip(), "Rulepack readiness checklist is empty"


def test_jurisdiction_checklist_contains_parcel() -> None:
    content = JURISDICTION_CHECKLIST.read_text(encoding="utf-8")
    assert "Parcel" in content, "Jurisdiction checklist missing 'Parcel' section"


def test_jurisdiction_checklist_contains_zoning() -> None:
    content = JURISDICTION_CHECKLIST.read_text(encoding="utf-8")
    assert "Zoning" in content, "Jurisdiction checklist missing 'Zoning' section"


def test_jurisdiction_checklist_contains_water_rights() -> None:
    content = JURISDICTION_CHECKLIST.read_text(encoding="utf-8")
    assert "Water rights" in content, (
        "Jurisdiction checklist missing 'Water rights' section"
    )


def test_jurisdiction_checklist_contains_signoff() -> None:
    content = JURISDICTION_CHECKLIST.read_text(encoding="utf-8")
    assert "Sign-off" in content, "Jurisdiction checklist missing 'Sign-off' section"


def test_rulepack_checklist_contains_intent_definition() -> None:
    content = RULEPACK_CHECKLIST.read_text(encoding="utf-8")
    assert "Intent definition" in content, (
        "Rulepack checklist missing 'Intent definition' section"
    )


def test_rulepack_checklist_contains_hard_gates() -> None:
    content = RULEPACK_CHECKLIST.read_text(encoding="utf-8")
    assert "Hard gates" in content, "Rulepack checklist missing 'Hard gates' section"


def test_rulepack_checklist_contains_verification_tasks() -> None:
    content = RULEPACK_CHECKLIST.read_text(encoding="utf-8")
    assert "Verification tasks" in content, (
        "Rulepack checklist missing 'Verification tasks' section"
    )


def test_rulepack_checklist_contains_signoff() -> None:
    content = RULEPACK_CHECKLIST.read_text(encoding="utf-8")
    assert "Sign-off" in content, "Rulepack checklist missing 'Sign-off' section"
