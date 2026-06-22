from __future__ import annotations

from pathlib import Path
from typing import Any, cast

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKLOG_PATH = REPO_ROOT / "state" / "QUALIFICATION_PARAMETERIZATION_BACKLOG.md"


def _yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def test_qualification_parameterization_backlog_records_p0_blockers() -> None:
    backlog = BACKLOG_PATH.read_text(encoding="utf-8")

    for phrase in (
        "# Qualification Parameterization Backlog",
        "P0 = BLOCKED",
        "BLOCKED (external/owner authority)",
        "Active gates | 12",
        "Active DRAFT criterion contracts | 60",
        "Active DRAFT/unresolved target bindings | 51",
        "Active DRAFT judgment rubrics | 16",
        "Qualified-domain profiles still DRAFT | 8",
        "Approved source profiles selected | 0",
        "ruleset_versions",
    ):
        assert phrase in backlog

    for gate_id in ("A", "DB", "DQ", "G", "IR", "M", "P0", "Q1", "Q2", "R", "S", "W"):
        assert f"`{gate_id}`" in backlog

    for criterion_id in ("P0-014", "P0-017", "P0-025", "Q2-030", "DQ-022", "W-011"):
        assert f"`{criterion_id}`" in backlog


def test_qualification_backlog_covers_bologna_scope_and_corpus_decisions() -> None:
    backlog = BACKLOG_PATH.read_text(encoding="utf-8")
    pilot_scope = _yaml(REPO_ROOT / "config" / "bologna_pilot_scope_authority.yaml")
    corpus = _yaml(REPO_ROOT / "config" / "bologna_recorded_source_corpus.yaml")

    for decision_id in pilot_scope["required_scope_decisions"]:
        assert f"`{decision_id}`" in backlog

    for decision_id in corpus["required_corpus_decisions"]:
        assert f"`{decision_id}`" in backlog

    for phrase in (
        "Bologna pilot-scope authority",
        "Bologna source-rights matrix",
        "Bologna recorded-source corpus",
        "DB-backed Bologna report proof",
        "No AOI selection, source approval, fixture capture, runtime/report use, or "
        "source registry promotion is authorized by this backlog.",
    ):
        assert phrase in backlog


def test_task_queue_reflects_bologna_first_backlog_and_blocked_followons() -> None:
    task_queue = _yaml(REPO_ROOT / "tasks" / "task_queue.yaml")
    tasks = {task["id"]: task for task in task_queue["tasks"]}

    assert (
        task_queue["active_plan"]
        == "plans/2026-06-21-hcv-1-qualification-validator.md"
    )
    assert tasks["EQ-BOL"]["status"] == "done"
    assert tasks["EQ-BOL"]["depends_on"] == ["EQ-1"]

    blocked_ids = {
        "EQ-BLOCK-TARGETS",
        "EQ-BLOCK-RUBRICS",
        "EQ-BLOCK-DOMAINS",
        "EQ-BLOCK-SOURCES",
        "EQ-BLOCK-SCOPE-VERSIONS",
        "EQ-BLOCK-BOLOGNA-SCOPE",
        "EQ-BLOCK-BOLOGNA-SOURCE-RIGHTS",
        "EQ-BLOCK-BOLOGNA-CORPUS",
        "EQ-BLOCK-BOLOGNA-REPORT",
    }
    assert blocked_ids <= set(tasks)
    for task_id in blocked_ids:
        assert tasks[task_id]["status"] == "blocked"
        assert "external/owner authority" in tasks[task_id]["notes"]

    assert tasks["EQ-2"]["depends_on"] == ["EQ-BOL"]
    assert tasks["EQ-2"]["status"] == "done"
    assert tasks["EQ-3"]["depends_on"] == ["EQ-2"]
    assert tasks["EQ-3"]["status"] == "done"
    assert tasks["EQ-4"]["depends_on"] == ["EQ-3"]
    assert tasks["EQ-4"]["status"] == "done"
    assert tasks["EQP2-1"]["depends_on"] == ["EQ-4"]
    assert tasks["EQP2-1"]["status"] == "done"
    assert tasks["EQP2-2"]["depends_on"] == ["EQP2-1"]
    assert tasks["EQP2-2"]["status"] == "done"
    assert tasks["EQP2-3"]["depends_on"] == ["EQP2-2"]
    assert tasks["EQP2-3"]["status"] == "done"
    assert tasks["EQP2-4"]["depends_on"] == ["EQP2-3"]
    assert tasks["EQP2-4"]["status"] == "done"
    assert tasks["BOL-AUTH-SYNC"]["depends_on"] == ["EQP2-4"]
    assert tasks["BOL-AUTH-SYNC"]["status"] == "done"
    assert tasks["BAP-001"]["depends_on"] == ["BOL-AUTH-SYNC"]
    assert tasks["BAP-001"]["status"] == "done"
    assert tasks["BAR-001"]["depends_on"] == ["BAP-001"]
    assert tasks["BAR-001"]["status"] == "done"
    assert tasks["BSA-REC"]["depends_on"] == ["BAR-001"]
    assert tasks["BSA-REC"]["status"] == "done"
    assert tasks["HCV-1"]["depends_on"] == ["BSA-REC"]
    assert tasks["HCV-1"]["status"] == "done"
    assert tasks["HCV-2"]["depends_on"] == ["HCV-1"]
    assert tasks["HCV-2"]["status"] == "queued"
    assert tasks["HCV-3"]["depends_on"] == ["HCV-2"]
    assert tasks["HCV-3"]["status"] == "queued"
    assert tasks["HCV-4"]["depends_on"] == ["HCV-3"]
    assert tasks["HCV-4"]["status"] == "queued"
    assert tasks["EQ-5"]["depends_on"] == ["HCV-4"]
    assert tasks["BSA-001"]["status"] == "blocked"
