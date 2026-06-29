from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKLOG_PATH = REPO_ROOT / "state" / "QUALIFICATION_PARAMETERIZATION_BACKLOG.md"
OWNER_DECISIONS_PATH = REPO_ROOT / "state" / "owner-decisions.md"
OWNER_PACKET_PATH = REPO_ROOT / "state" / "owner-decision-packet.md"
BACKLOG_CHECK_SCRIPT = REPO_ROOT / "scripts" / "qualification_parameterization_backlog_check.py"
EXPECTED_EQ5_PLAN = "plans/2026-06-23-eq5-parameterization-backlog-check.md"
EXPECTED_EQR_PLAN = "plans/2026-06-23-eqr-residual-closeout.md"
EXPECTED_ODP1_PACKET_PLAN = "plans/2026-06-23-odp1-owner-answer-packet.md"
EXPECTED_POST_ODP1_PACKET_PLAN = "plans/2026-06-23-post-odp1-packet-routing.md"
EXPECTED_SCOPE_PURSUIT_PLAN = "plans/2026-06-26-bologna-scope-pursuit.md"
EXPECTED_BOL_SCOPE_AUTH_PLAN = "plans/2026-06-27-bol-scope-auth.md"
EXPECTED_ODP2_PACKET_PLAN = "plans/2026-06-27-odp2-owner-answer-packet.md"
EXPECTED_ODGAV_PLAN = "plans/2026-06-28-odgav-owner-answer-evaluation.md"
BACKLOG_CHECK_INPUTS = (
    ".github/workflows/ci.yml",
    "MANIFEST.md",
    EXPECTED_EQ5_PLAN,
    EXPECTED_EQR_PLAN,
    EXPECTED_ODP1_PACKET_PLAN,
    EXPECTED_POST_ODP1_PACKET_PLAN,
    EXPECTED_SCOPE_PURSUIT_PLAN,
    EXPECTED_BOL_SCOPE_AUTH_PLAN,
    EXPECTED_ODP2_PACKET_PLAN,
    EXPECTED_ODGAV_PLAN,
    "plans/README.md",
    "config/bologna_odp1_owner_answer_packet.yaml",
    "config/bol_scope_auth.yaml",
    "config/bologna_odp2_owner_answer_packet.yaml",
    "docs/runbooks/bologna_odp1_owner_answer_packet.md",
    "docs/runbooks/bol_scope_auth.md",
    "docs/runbooks/bologna_odp2_owner_answer_packet.md",
    "scripts/bologna_odp1_owner_answer_packet_check.py",
    "scripts/bol_scope_auth_check.py",
    "scripts/bologna_odp2_owner_answer_packet_check.py",
    "scripts/run_bologna_odp1_owner_answer_packet_check.ps1",
    "scripts/run_bologna_odp1_owner_answer_packet_check.sh",
    "scripts/run_bol_scope_auth_check.ps1",
    "scripts/run_bol_scope_auth_check.sh",
    "scripts/run_bologna_odp2_owner_answer_packet_check.ps1",
    "scripts/run_bologna_odp2_owner_answer_packet_check.sh",
    "scripts/qualification_parameterization_backlog_check.py",
    "scripts/run_qualification_parameterization_backlog_check.ps1",
    "scripts/run_qualification_parameterization_backlog_check.sh",
    "scripts/verify.ps1",
    "scripts/verify.sh",
    "state/EMPIRICAL_QUALIFICATION_STATUS.yaml",
    "state/PROJECT_STATE.md",
    "state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md",
    "state/owner-decisions.md",
    "state/owner-decision-packet.md",
    "config/bologna_owner_answer_intake.yaml",
    "config/qualification/qualification_targets.yaml",
    "config/qualification/source_profiles/source_quality_profile.ds-002.yaml",
    "tasks/task_queue.yaml",
)


def _yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _copy_required_backlog_check_inputs(root: Path) -> None:
    for relative_path in BACKLOG_CHECK_INPUTS:
        source = REPO_ROOT / relative_path
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _run_backlog_check(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(BACKLOG_CHECK_SCRIPT),
            "--root",
            str(root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


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
        "EQ-5 consistency checker: `scripts/qualification_parameterization_backlog_check.py`",
        "ODP-BOL-001 owner-answer packet:",
        "`config/bologna_odp1_owner_answer_packet.yaml`",
        "ODP-BOL-001 scope-authority readiness:",
        "`config/bol_scope_auth.yaml`",
        "ODP-BOL-002 owner-answer packet:",
        "`config/bologna_odp2_owner_answer_packet.yaml`",
        "## Owner Decision Blockers",
    ):
        assert phrase in backlog

    for gate_id in ("A", "DB", "DQ", "G", "IR", "M", "P0", "Q1", "Q2", "R", "S", "W"):
        assert f"`{gate_id}`" in backlog

    for criterion_id in ("P0-014", "P0-017", "P0-025", "Q2-030", "DQ-022", "W-011"):
        assert f"`{criterion_id}`" in backlog

    for decision_id in (
        "ODP-DOM-001",
        "ODP-TGT-001",
        "ODP-RUB-001",
        "ODP-SRC-001",
        "ODP-PRO-001",
        "ODP-CON-001",
        "ODP-BOL-001",
        "ODP-BOL-002",
        "ODP-BOL-003",
        "ODP-BOL-004",
        "ODP-HOST-001",
    ):
        assert f"`{decision_id}`" in backlog


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
    assert "records one review-only `ODP-BOL-001` scope-pursuit owner answer" in backlog
    assert "keeps `ODP-BOL-002` through `ODP-BOL-004` owner answers missing" in backlog
    assert "ODP-BOL-001 owner-answer packet:" in backlog
    assert "`config/bologna_odp1_owner_answer_packet.yaml`" in backlog
    assert "ODP-BOL-001 scope-authority readiness:" in backlog
    assert "`config/bol_scope_auth.yaml`" in backlog
    assert "ODP-BOL-001 owner-response gate:" in backlog
    assert "`config/bologna_odp1_owner_response_gate.yaml`" in backlog
    assert "Bologna pilot-scope authority missing" in backlog
    assert "ODP-BOL-002 source-rights response gate:" in backlog
    assert "`config/bologna_odp2_source_rights_response_gate.yaml`" in backlog
    assert "ODP-BOL-002 owner-answer packet:" in backlog
    assert "`config/bologna_odp2_owner_answer_packet.yaml`" in backlog
    assert "Bologna source-authority/source-rights answer blocked" in backlog
    assert "ODP-BOL-003 recorded-source corpus response gate:" in backlog
    assert "`config/bologna_odp3_corpus_response_gate.yaml`" in backlog
    assert "Bologna recorded-source corpus answer blocked" in backlog
    assert "ODP-BOL-004 DB-backed report proof response gate:" in backlog
    assert "`config/bologna_odp4_db_report_proof_response_gate.yaml`" in backlog
    assert "Bologna DB-backed report proof answer blocked" in backlog


def test_task_queue_reflects_bologna_first_backlog_and_blocked_followons() -> None:
    task_queue = _yaml(REPO_ROOT / "tasks" / "task_queue.yaml")
    tasks = {task["id"]: task for task in task_queue["tasks"]}

    assert task_queue["active_plan"] == EXPECTED_ODGAV_PLAN
    active_ids = [task["id"] for task in task_queue["tasks"] if task.get("status") == "active"]
    assert active_ids == ["ODGAV-1"]
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
    assert tasks["BOL-ODP-1"]["status"] == "done"
    assert tasks["BOL-ODP-1"]["spec"] == (
        "plans/2026-06-23-bologna-owner-answer-intake.md"
    )
    assert "keeps all downstream updates blocked" in tasks["BOL-ODP-1"]["notes"]
    assert tasks["BOL-ODP1-GATE"]["depends_on"] == ["BOL-ODP-1"]
    assert tasks["BOL-ODP1-GATE"]["status"] == "done"
    assert tasks["BOL-ODP1-GATE"]["spec"] == (
        "plans/2026-06-23-bologna-odp1-owner-response-gate.md"
    )
    assert "keeping owner answers, authority records" in tasks["BOL-ODP1-GATE"]["notes"]
    assert tasks["BOL-ODP2-GATE"]["depends_on"] == ["BOL-ODP1-GATE"]
    assert tasks["BOL-ODP2-GATE"]["status"] == "done"
    assert tasks["BOL-ODP2-GATE"]["spec"] == (
        "plans/2026-06-23-bologna-odp2-source-rights-response-gate.md"
    )
    assert "ODP-BOL-001 authority as the" in tasks["BOL-ODP2-GATE"]["notes"]
    assert tasks["BOL-ODP3-GATE"]["depends_on"] == ["BOL-ODP2-GATE"]
    assert tasks["BOL-ODP3-GATE"]["status"] == "done"
    assert tasks["BOL-ODP3-GATE"]["spec"] == (
        "plans/2026-06-23-bologna-odp3-corpus-response-gate.md"
    )
    assert "ODP-BOL-001 authority and ODP-BOL-002 as unresolved prerequisites" in (
        tasks["BOL-ODP3-GATE"]["notes"]
    )
    assert tasks["BOL-ODP4-GATE"]["depends_on"] == ["BOL-ODP3-GATE"]
    assert tasks["BOL-ODP4-GATE"]["status"] == "done"
    assert tasks["BOL-ODP4-GATE"]["spec"] == (
        "plans/2026-06-23-bologna-odp4-db-report-proof-response-gate.md"
    )
    assert "ODP-BOL-001 authority, ODP-BOL-002, and" in (
        tasks["BOL-ODP4-GATE"]["notes"]
    )
    assert tasks["BOL-POST-ODP4-AUTH"]["depends_on"] == ["BOL-ODP4-GATE"]
    assert tasks["BOL-POST-ODP4-AUTH"]["status"] == "done"
    assert tasks["BOL-POST-ODP4-AUTH"]["spec"] == (
        "plans/2026-06-23-post-odp4-authority-routing.md"
    )
    assert "no DB-backed Bologna report proof can proceed" in (
        tasks["BOL-POST-ODP4-AUTH"]["notes"]
    )
    assert tasks["EQ-5"]["depends_on"] == ["BOL-POST-ODP4-AUTH"]
    assert tasks["EQ-5"]["status"] == "done"
    assert tasks["EQ-5"]["spec"] == EXPECTED_EQ5_PLAN
    assert "validate-only consistency checker" in tasks["EQ-5"]["notes"]
    assert tasks["EQ-R"]["depends_on"] == ["BPS-REQ-001"]
    assert tasks["EQ-R"]["status"] == "done"
    assert tasks["EQ-R"]["spec"] == EXPECTED_EQR_PLAN
    assert "decaying DEFER" in tasks["EQ-R"]["notes"]
    assert tasks["BOL-ODP1-PACKET"]["depends_on"] == ["EQ-R", "BOL-ODP1-GATE"]
    assert tasks["BOL-ODP1-PACKET"]["status"] == "done"
    assert tasks["BOL-ODP1-PACKET"]["spec"] == EXPECTED_ODP1_PACKET_PLAN
    assert "owner-answer packet" in tasks["BOL-ODP1-PACKET"]["notes"]
    assert tasks["BOL-POST-ODP1-PACKET"]["depends_on"] == ["BOL-ODP1-PACKET"]
    assert tasks["BOL-POST-ODP1-PACKET"]["status"] == "done"
    assert tasks["BOL-POST-ODP1-PACKET"]["spec"] == EXPECTED_POST_ODP1_PACKET_PLAN
    assert "PR #161" in tasks["BOL-POST-ODP1-PACKET"]["notes"]
    assert tasks["BOL-SCOPE-PURSUIT"]["depends_on"] == ["BOL-POST-ODP1-PACKET"]
    assert tasks["BOL-SCOPE-PURSUIT"]["status"] == "done"
    assert tasks["BOL-SCOPE-PURSUIT"]["spec"] == EXPECTED_SCOPE_PURSUIT_PLAN
    assert "approve_review_only" in tasks["BOL-SCOPE-PURSUIT"]["notes"]
    assert tasks["BOL-SCOPE-AUTH"]["depends_on"] == ["BOL-SCOPE-PURSUIT"]
    assert tasks["BOL-SCOPE-AUTH"]["status"] == "done"
    assert tasks["BOL-SCOPE-AUTH"]["spec"] == EXPECTED_BOL_SCOPE_AUTH_PLAN
    assert "approve_with_cited_authority" in tasks["BOL-SCOPE-AUTH"]["notes"]
    assert tasks["BOL-ODP2-PACKET"]["depends_on"] == ["BOL-SCOPE-AUTH", "BOL-ODP2-GATE"]
    assert tasks["BOL-ODP2-PACKET"]["status"] == "done"
    assert tasks["BOL-ODP2-PACKET"]["spec"] == EXPECTED_ODP2_PACKET_PLAN
    assert "source-rights response" in tasks["BOL-ODP2-PACKET"]["notes"]
    assert tasks["ODGAV-1"]["depends_on"] == ["BOL-ODP2-PACKET"]
    assert tasks["ODGAV-1"]["status"] == "active"
    assert tasks["ODGAV-1"]["spec"] == EXPECTED_ODGAV_PLAN
    assert "side-effect-free synthetic owner-answer evaluators" in tasks["ODGAV-1"]["notes"]
    assert "worktree-reconciliation-2026-06-28.md" in tasks["ODGAV-1"]["notes"]
    assert tasks["BSA-001"]["status"] == "blocked"


def test_qualification_parameterization_backlog_checker_passes() -> None:
    result = _run_backlog_check(REPO_ROOT)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "qualification parameterization backlog check: ok" in result.stdout


def test_qualification_parameterization_backlog_checker_fails_closed_on_owner_answer(
    tmp_path: Path,
) -> None:
    _copy_required_backlog_check_inputs(tmp_path)
    intake_path = tmp_path / "config" / "bologna_owner_answer_intake.yaml"
    intake = _yaml(intake_path)
    contract = intake["owner_answer_contract"]
    contract["current_owner_answers"].append(
        {
            "owner_answer_id": "TEST-ANSWER",
            "odp_id": "ODP-BOL-001",
            "answer_type": "approve_with_cited_authority",
            "decision_owner": "test",
            "decision_date": "2026-06-23",
            "authority_reference": "test-only",
            "answer_summary": "test-only",
            "cited_artifacts": [],
            "caveats": [],
            "downstream_unlocks_requested": [],
            "supersedes_owner_answer_ids": [],
        }
    )
    intake_path.write_text(yaml.safe_dump(intake, sort_keys=False), encoding="utf-8")

    result = _run_backlog_check(tmp_path)

    assert result.returncode == 1
    assert "current_owner_answers must contain exactly one review-only ODP1 answer" in (
        result.stdout
    )
