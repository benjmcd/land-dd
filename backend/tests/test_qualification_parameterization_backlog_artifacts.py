from __future__ import annotations

from pathlib import Path
from typing import Any, cast

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKLOG_PATH = REPO_ROOT / "state" / "QUALIFICATION_PARAMETERIZATION_BACKLOG.md"
OWNER_DECISIONS_PATH = REPO_ROOT / "state" / "owner-decisions.md"
OWNER_PACKET_PATH = REPO_ROOT / "state" / "owner-decision-packet.md"


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
        "Active DRAFT/unresolved target bindings | 49",
        "Active DRAFT judgment rubrics | 16",
        "Qualified-domain profiles still DRAFT | 8",
        "Approved source profiles selected | 1",
        "ruleset_versions",
    ):
        assert phrase in backlog

    for gate_id in ("A", "DB", "DQ", "G", "IR", "M", "P0", "Q1", "Q2", "R", "S", "W"):
        assert f"`{gate_id}`" in backlog

    for criterion_id in ("P0-014", "P0-017", "P0-025", "Q2-030", "DQ-022", "W-011"):
        assert f"`{criterion_id}`" in backlog


def test_owner_authorized_freeze_disposition_is_recorded() -> None:
    backlog = BACKLOG_PATH.read_text(encoding="utf-8")

    for phrase in (
        "## Controlled Owner Disposition - 2026-06-22",
        "owner=benjmcd",
        "authority=owner directive 2026-06-22",
        "authority_file=state/owner-decisions.md",
        "rationale=conservative defaults matching operational reality",
        "reversal=requires a new owner decision + full requalification",
        "`scope.product_scope_profile` | `BOUNDED_USER_VALIDATED` | FROZEN_TARGET",
        "`scope.deployment_profile` | `LOCAL_SINGLE_USER` | FROZEN_TARGET",
        "`scope.windows_native_required` | `true` | FROZEN_TARGET",
        "`scope.source_profile_ids` | [`DS-002`] | APPROVED_SOURCE_PROFILE",
        "`criterion_bindings.W-003` | frozen | FROZEN_TARGET",
        "`criterion_bindings.W-011` | frozen | FROZEN_TARGET",
    ):
        assert phrase in backlog

    for blocked_phrase in (
        "DQ/Q1/Q2/M target thresholds remain blocked",
        "domain profiles remain blocked",
        "criterion contracts and judgment rubrics remain blocked",
        "P0 remains BLOCKED",
    ):
        assert blocked_phrase in backlog


def test_owner_authorized_freeze_has_branch_local_authority_record() -> None:
    decisions = OWNER_DECISIONS_PATH.read_text(encoding="utf-8")

    for phrase in (
        "## 2026-06-22 QFREEZE-1 Qualification Freeze",
        "repo-local authority ledger",
        "owner=benjmcd",
        "authority=owner directive 2026-06-22",
        "rationale=conservative defaults matching operational reality",
        "reversal=requires a new owner decision + full requalification",
        "`scope.source_profile_ids` | [`DS-002`] | APPROVED_SOURCE_PROFILE",
        "`criterion_bindings.W-003` | frozen | FROZEN_TARGET",
        "`criterion_bindings.W-011` | frozen | FROZEN_TARGET",
        "no source approvals beyond DS-002",
        "no P0 `PASS`",
    ):
        assert phrase in decisions


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


def test_owner_decision_packet_records_consequences_without_authority() -> None:
    packet = OWNER_PACKET_PATH.read_text(encoding="utf-8")
    backlog = BACKLOG_PATH.read_text(encoding="utf-8")

    for phrase in (
        "Status: `decision-request-only`",
        "not an authority ledger",
        "does not freeze or approve anything by itself",
        "P0` remains `BLOCKED",
        "All non-P0 qualifications and overlays remain `NOT_RUN`",
        "Bologna has no approved AOI",
        "ODP-DOM-001 Domain Profile Freeze",
        "ODP-TGT-001 Active Targets And Criterion Contracts",
        "ODP-RUB-001 Judgment Rubrics",
        "ODP-SRC-001 Selected Source Profile Set",
        "ODP-PRO-001 Candidate And Evidence Protocol",
        "ODP-CON-001 Conditional Profiles",
        "ODP-BOL-001 Bologna Product And AOI Authority",
        "ODP-BOL-002 Bologna Source Authority And Rights",
        "ODP-BOL-003 Bologna Recorded-Source Corpus",
        "ODP-BOL-004 DB-Backed Bologna Report Proof",
        "ODP-HOST-001 DS-017, Hosted, And Level 10 Authority",
        "This packet does not authorize:",
        "source approvals beyond DS-002",
        "fixture capture or source-failure fixtures",
        "DB seed, connector, report/API/UI/runtime proof",
    ):
        assert phrase in packet

    for controlled_outcome in (
        "FROZEN_TARGET",
        "FROZEN_RUBRIC",
        "FROZEN_DOMAIN_PROFILE",
        "APPROVED_SOURCE_PROFILE",
        "PROFILE_EXCLUDED_WITH_EVIDENCED_NA",
        "BLOCKED_WITH_OWNER_AND_DECISION",
        "REMOVED_THROUGH_REVIEWED_FRAMEWORK_CHANGE",
    ):
        assert controlled_outcome in packet

    assert "Owner decision consequence map: `state/owner-decision-packet.md`" in backlog
    assert "decision-request-only artifact" in backlog
    assert "Bologna owner-answer intake: `config/bologna_owner_answer_intake.yaml`" in backlog
    assert "keeps all ODP-BOL owner answers missing" in backlog


def test_task_queue_reflects_bologna_first_backlog_and_blocked_followons() -> None:
    task_queue = _yaml(REPO_ROOT / "tasks" / "task_queue.yaml")
    tasks = {task["id"]: task for task in task_queue["tasks"]}

    assert task_queue["active_plan"] == "plans/2026-06-23-bologna-owner-answer-intake.md"
    active_ids = [task["id"] for task in task_queue["tasks"] if task.get("status") == "active"]
    assert active_ids == ["BOL-ODP-1"]
    assert tasks["REC-001"]["status"] == "done"
    assert tasks["BPS-001"]["status"] == "done"
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
    assert tasks["HCV-2"]["status"] == "done"
    assert tasks["HCV-3"]["depends_on"] == ["HCV-2"]
    assert tasks["HCV-3"]["status"] == "done"
    assert tasks["HCV-4"]["depends_on"] == ["HCV-3"]
    assert tasks["HCV-4"]["status"] == "done"
    assert tasks["QFREEZE-1"]["depends_on"] == ["HCV-4"]
    assert tasks["QFREEZE-1"]["status"] == "done"
    assert tasks["OWNER-DEC-1"]["depends_on"] == ["QFREEZE-1"]
    assert tasks["OWNER-DEC-1"]["status"] == "done"
    assert tasks["OWNER-DEC-1"]["spec"] == (
        "plans/2026-06-22-owner-decision-packet.md"
    )
    assert "does not authorize any additional freeze" in tasks["OWNER-DEC-1"]["notes"]
    assert tasks["BOL-ODP-1"]["depends_on"] == ["OWNER-DEC-1"]
    assert tasks["BOL-ODP-1"]["status"] == "active"
    assert tasks["BOL-ODP-1"]["spec"] == (
        "plans/2026-06-23-bologna-owner-answer-intake.md"
    )
    assert "keeps all downstream updates blocked" in tasks["BOL-ODP-1"]["notes"]
    assert tasks["EQ-5"]["depends_on"] == ["BOL-ODP-1"]
    assert tasks["BSA-001"]["status"] == "blocked"
