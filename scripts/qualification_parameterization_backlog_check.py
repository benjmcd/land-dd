#!/usr/bin/env python3
"""Validate the EQ-5 qualification parameterization backlog boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "Missing dev dependency. Install PyYAML before running qualification backlog checks."
    ) from exc


EXPECTED_EQ5_PLAN = "plans/2026-06-23-eq5-parameterization-backlog-check.md"
EXPECTED_SCOPE_PURSUIT_PLAN = "plans/2026-06-26-bologna-scope-pursuit.md"
EXPECTED_BOL_SCOPE_AUTH_PLAN = "plans/2026-06-27-bol-scope-auth.md"
EXPECTED_ODP2_PACKET_PLAN = "plans/2026-06-27-odp2-owner-answer-packet.md"
EXPECTED_ODGAV_PLAN = "plans/2026-06-28-odgav-owner-answer-evaluation.md"
EXPECTED_MINERALS_PLAN = "plans/2026-06-29-extended-domain-minerals-fixture-ingestion.md"
EXPECTED_BROADBAND_PLAN = (
    "plans/2026-07-02-extended-domain-broadband-fixture-ingestion.md"
)
EXPECTED_ENV_HAZARD_PLAN = "plans/2026-07-02-env-fixture.md"
EXPECTED_WATER_PLAN = "plans/2026-07-02-water-fixture.md"
EXPECTED_GEOLOGY_PLAN = "plans/2026-07-02-geology-fixture.md"
EXPECTED_POST_GEOLOGY_PLAN = "plans/2026-07-02-post-geology-routing.md"
EXPECTED_AUTH_EVIDENCE_PLAN = "plans/2026-07-02-authority-evidence-intake.md"
BACKLOG_PATH = "state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md"
OWNER_DECISIONS_PATH = "state/owner-decisions.md"
OWNER_PACKET_PATH = "state/owner-decision-packet.md"
OWNER_INTAKE_PATH = "config/bologna_owner_answer_intake.yaml"
ODP1_OWNER_ANSWER_PACKET_PATH = "config/bologna_odp1_owner_answer_packet.yaml"
BOL_SCOPE_AUTH_PATH = "config/bol_scope_auth.yaml"
ODP2_OWNER_ANSWER_PACKET_PATH = "config/bologna_odp2_owner_answer_packet.yaml"
QUALIFICATION_STATUS_PATH = "state/EMPIRICAL_QUALIFICATION_STATUS.yaml"
QUALIFICATION_TARGETS_PATH = "config/qualification/qualification_targets.yaml"
SOURCE_PROFILE_PATH = "config/qualification/source_profiles/source_quality_profile.ds-002.yaml"
TASK_QUEUE_PATH = "tasks/task_queue.yaml"

EXPECTED_OWNER_DECISION_IDS = (
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
)
EXPECTED_BOL_THREADS = ("ODP-BOL-001", "ODP-BOL-002", "ODP-BOL-003", "ODP-BOL-004")
EXPECTED_SELECTED_SOURCE_PROFILE_IDS = ("DS-002",)
EXPECTED_FROZEN_BINDINGS = ("W-003", "W-011")
ODP1_OWNER_ANSWER_ID = "odp-bol-001-scope-pursuit-2026-06-26"
EXPECTED_DONE_TASKS = (
    "BOL-ODP4-GATE",
    "BOL-POST-ODP4-AUTH",
    "BOL-ODP1-PACKET",
    "BOL-POST-ODP1-PACKET",
    "BOL-SCOPE-PURSUIT",
    "BOL-SCOPE-AUTH",
    "BOL-ODP2-PACKET",
    "ODGAV-1",
    "MINERALS-FIXTURE",
    "BROADBAND-FIXTURE",
    "ENV-FIXTURE",
    "WATER-FIXTURE",
    "GEOLOGY-FIXTURE",
    "POST-GEOLOGY-ROUTING",
    "EQ-5",
)
EXPECTED_BLOCKED_TASKS = (
    "EQ-BLOCK-TARGETS",
    "EQ-BLOCK-RUBRICS",
    "EQ-BLOCK-DOMAINS",
    "EQ-BLOCK-SOURCES",
    "EQ-BLOCK-SCOPE-VERSIONS",
    "EQ-BLOCK-BOLOGNA-SCOPE",
    "EQ-BLOCK-BOLOGNA-SOURCE-RIGHTS",
    "EQ-BLOCK-BOLOGNA-CORPUS",
    "EQ-BLOCK-BOLOGNA-REPORT",
    "BSA-001",
)
EXPECTED_SCOPE_VALUES = {
    "product_scope_profile": "BOUNDED_USER_VALIDATED",
    "deployment_profile": "LOCAL_SINGLE_USER",
    "windows_native_required": True,
    "candidate_generation_enabled": False,
    "financial_modeling_enabled": False,
    "ai_llm_enabled_for_decision_relevant_output": False,
    "commercial_profile_enabled": False,
    "international_operation_enabled": False,
    "regulated_high_stakes_use_enabled": False,
    "report_contract_version": "report_run_contract_v1",
    "api_contract_version": "0.1.0",
    "normalization_schema_version": "0.1.0-alpha",
    "geometry_pipeline_version": "0.1.0-alpha",
    "source_snapshot_policy": "HASHED_RETRIEVAL_MANIFEST_PER_SOURCE",
    "data_as_of_policy": "SOURCE_DATA_AS_OF_AND_RETRIEVAL_TIMESTAMP_WITH_FRESHNESS_CAVEATS",
}
EXPECTED_INTAKE_FALSE_APPROVALS = (
    "owner_answers_complete",
    "source_authority_rights_answered",
    "recorded_corpus_answered",
    "db_report_proof_answered",
    "downstream_authority_updates_allowed",
)
EXPECTED_INTAKE_FALSE_LIMITS = (
    "records_owner_authority",
    "selects_bologna_aoi",
    "approves_sources",
    "changes_source_rights",
    "creates_recorded_fixtures",
    "creates_source_failure_fixtures",
    "runs_live_connectors",
    "mutates_database",
    "creates_runtime_artifacts",
    "creates_report_artifacts",
    "changes_report_semantics",
    "changes_source_readiness",
    "approves_ds017",
    "claims_legal_review",
    "claims_hosted_production_ready",
    "claims_level_10",
)


class QualificationParameterizationBacklogError(RuntimeError):
    """Raised when backlog control-plane inputs cannot be read safely."""


def repo_relative_path(root: Path, path_text: str) -> Path:
    normalized = path_text.replace("\\", "/")
    path = PurePosixPath(normalized)
    if normalized.startswith("/") or ":" in normalized or ".." in path.parts:
        raise QualificationParameterizationBacklogError(
            f"path must be repo-relative: {path_text}"
        )
    absolute = (root / Path(*path.parts)).resolve()
    try:
        absolute.relative_to(root.resolve())
    except ValueError as exc:
        raise QualificationParameterizationBacklogError(
            f"path escapes repo: {path_text}"
        ) from exc
    return absolute


def read_text(root: Path, path_text: str) -> str:
    path = repo_relative_path(root, path_text)
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise QualificationParameterizationBacklogError(
            f"required text file missing: {path_text}"
        ) from exc


def load_yaml(root: Path, path_text: str) -> dict[str, Any]:
    path = repo_relative_path(root, path_text)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise QualificationParameterizationBacklogError(
            f"required YAML file missing: {path_text}"
        ) from exc
    if not isinstance(payload, dict):
        raise QualificationParameterizationBacklogError(f"YAML object required: {path_text}")
    return payload


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_fragments(
    text: str,
    path_text: str,
    fragments: tuple[str, ...],
    errors: list[str],
) -> None:
    for fragment in fragments:
        if fragment not in text:
            errors.append(f"{path_text} missing expected fragment: {fragment}")


def require_mapping(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be a mapping")
        return {}
    return value


def validate_backlog(backlog: str, errors: list[str]) -> None:
    require_fragments(
        backlog,
        BACKLOG_PATH,
        (
            "Status: `P0 = BLOCKED`",
            "No AOI selection, source approval, fixture capture",
            "Owner decision consequence map: `state/owner-decision-packet.md`",
            "Bologna owner-answer intake: `config/bologna_owner_answer_intake.yaml`",
            "ODP-BOL-001 owner-answer packet:",
            "`config/bologna_odp1_owner_answer_packet.yaml`",
            "ODP-BOL-001 scope-authority readiness:",
            "`config/bol_scope_auth.yaml`",
            "ODP-BOL-002 owner-answer packet:",
            "`config/bologna_odp2_owner_answer_packet.yaml`",
            "EQ-5 consistency checker: `scripts/qualification_parameterization_backlog_check.py`",
            "## Owner Decision Blockers",
            "Active gates | 12 | BLOCKED (external/owner authority)",
            "Active DRAFT criterion contracts | 60 | BLOCKED (external/owner authority)",
            "Active DRAFT/unresolved target bindings | 49 | BLOCKED (external/owner authority)",
            "Active DRAFT judgment rubrics | 16 | BLOCKED (external/owner authority)",
            "Qualified-domain profiles still DRAFT | 8 | BLOCKED (external/owner authority)",
            "Approved source profiles selected | 1 | DS-002 only; remaining selections blocked",
            "## Controlled Owner Disposition - 2026-06-22",
            "## Bologna Priority Blockers",
        ),
        errors,
    )
    for decision_id in EXPECTED_OWNER_DECISION_IDS:
        require(f"`{decision_id}`" in backlog, f"backlog missing owner decision {decision_id}", errors)
    for source_id in EXPECTED_SELECTED_SOURCE_PROFILE_IDS:
        require(f"`{source_id}`" in backlog, f"backlog missing selected source {source_id}", errors)


def validate_owner_packet(packet: str, errors: list[str]) -> None:
    require_fragments(
        packet,
        OWNER_PACKET_PATH,
        (
            "Status: `decision-request-only`",
            "not an authority ledger",
            "does not freeze or approve anything by itself",
            "Bologna has no approved AOI",
            "This packet does not authorize:",
            "source approvals beyond DS-002",
            "fixture capture or source-failure fixtures",
            "DB seed, connector, report/API/UI/runtime proof",
        ),
        errors,
    )
    for decision_id in EXPECTED_OWNER_DECISION_IDS:
        require(f"### {decision_id} " in packet, f"owner packet missing {decision_id}", errors)


def validate_owner_decisions(decisions: str, errors: list[str]) -> None:
    require_fragments(
        decisions,
        OWNER_DECISIONS_PATH,
        (
            "## 2026-06-22 QFREEZE-1 Qualification Freeze",
            "repo-local authority ledger",
            "owner=benjmcd",
            "authority=owner directive 2026-06-22",
            "rationale=conservative defaults matching operational reality",
            "reversal=requires a new owner decision + full requalification",
            "`scope.source_profile_ids` | [`DS-002`] | APPROVED_SOURCE_PROFILE",
            "`criterion_bindings.W-003` | frozen | FROZEN_TARGET",
            "`criterion_bindings.W-011` | frozen | FROZEN_TARGET",
            "no P0 `PASS`",
            "no source approvals beyond DS-002",
            "no Bologna AOI/source authority",
            "no DB seed",
            "no report/API/UI/runtime proof",
            "no hosted authority",
        ),
        errors,
    )


def validate_owner_intake(intake: dict[str, Any], errors: list[str]) -> None:
    require(
        intake.get("status") == "blocked_review_only_scope_pursuit",
        "owner intake status drifted",
        errors,
    )

    approvals = require_mapping(intake.get("approvals"), "owner intake approvals", errors)
    require(
        approvals.get("product_aoi_scope_answered") is True,
        "owner intake approvals.product_aoi_scope_answered must reflect the review-only answer",
        errors,
    )
    for key in EXPECTED_INTAKE_FALSE_APPROVALS:
        require(approvals.get(key) is False, f"owner intake approvals.{key} must be false", errors)

    limits = require_mapping(intake.get("limits"), "owner intake limits", errors)
    require(limits.get("validate_only_intake") is True, "owner intake must remain validate-only", errors)
    for key in EXPECTED_INTAKE_FALSE_LIMITS:
        require(limits.get(key) is False, f"owner intake limits.{key} must be false", errors)

    contract = require_mapping(
        intake.get("owner_answer_contract"),
        "owner intake owner_answer_contract",
        errors,
    )
    require(
        contract.get("contract_state") == "ready_for_external_owner_answers",
        "owner answer contract state drifted",
        errors,
    )
    owner_answers = contract.get("current_owner_answers")
    require(
        isinstance(owner_answers, list) and len(owner_answers) == 1,
        "owner intake current_owner_answers must contain exactly one review-only ODP1 answer",
        errors,
    )
    if isinstance(owner_answers, list) and owner_answers:
        answer = require_mapping(owner_answers[0], "ODP1 owner answer", errors)
        require(
            answer.get("owner_answer_id") == ODP1_OWNER_ANSWER_ID,
            "ODP1 owner answer id drifted",
            errors,
        )
        require(answer.get("odp_id") == "ODP-BOL-001", "ODP1 owner answer ODP id drifted", errors)
        require(
            answer.get("answer_type") == "approve_review_only",
            "ODP1 owner answer must remain review-only",
            errors,
        )
        require(
            answer.get("downstream_unlocks_requested") == [],
            "ODP1 owner answer must not request downstream unlocks",
            errors,
        )
    require(
        contract.get("response_update_policy") == "disabled_until_complete_cited_authority",
        "owner answer response update policy drifted",
        errors,
    )

    controls = require_mapping(
        contract.get("no_overclaim_controls"),
        "owner intake no_overclaim_controls",
        errors,
    )
    for key, value in controls.items():
        require(value is True, f"owner intake no-overclaim control {key} must remain true", errors)

    threads = intake.get("bologna_decision_threads")
    if not isinstance(threads, list) or not threads:
        errors.append("owner intake bologna_decision_threads must be a non-empty list")
        return
    seen_threads = tuple(str(thread.get("odp_id")) for thread in threads if isinstance(thread, dict))
    require(seen_threads == EXPECTED_BOL_THREADS, "owner intake Bologna ODP sequence drifted", errors)
    for index, thread in enumerate(threads, start=1):
        if not isinstance(thread, dict):
            errors.append("owner intake Bologna thread must be a mapping")
            continue
        odp_id = str(thread.get("odp_id"))
        require(thread.get("sequence") == index, f"{odp_id} sequence drifted", errors)
        if odp_id == "ODP-BOL-001":
            require(
                thread.get("status") == "review_only_scope_pursuit_answered",
                f"{odp_id} status drifted",
                errors,
            )
            require(
                thread.get("owner_answer_references") == [ODP1_OWNER_ANSWER_ID],
                f"{odp_id} owner answer reference drifted",
                errors,
            )
        else:
            require(
                thread.get("status") == "missing_owner_answer",
                f"{odp_id} status must remain missing",
                errors,
            )
            require(
                thread.get("owner_answer_references") == [],
                f"{odp_id} owner answers must remain empty",
                errors,
            )
        require(thread.get("downstream_updates_allowed") is False, f"{odp_id} downstream updates must be false", errors)
        if index > 1:
            expected_prereqs = list(EXPECTED_BOL_THREADS[: index - 1])
            require(
                thread.get("prerequisite_odp_ids") == expected_prereqs,
                f"{odp_id} prerequisite sequence drifted",
                errors,
            )


def validate_odp1_owner_answer_packet(packet: dict[str, Any], errors: list[str]) -> None:
    require(
        packet.get("status") == "review_only_scope_pursuit_recorded",
        "ODP-BOL-001 owner answer packet status drifted",
        errors,
    )
    approvals = require_mapping(packet.get("approvals"), "ODP1 packet approvals", errors)
    require(
        approvals.get("owner_answer_recorded") is True,
        "ODP1 packet must record the review-only owner answer",
        errors,
    )
    for key in (
        "pilot_scope_authority_recorded",
        "product_aoi_scope_authorized",
        "downstream_authority_updates_allowed",
    ):
        require(approvals.get(key) is False, f"ODP1 packet approvals.{key} must be false", errors)

    limits = require_mapping(packet.get("limits"), "ODP1 packet limits", errors)
    require(limits.get("validate_only_answer_packet") is True, "ODP1 packet must be validate-only", errors)
    for key in (
        "records_owner_answer",
        "records_pilot_scope_authority",
        "selects_bologna_aoi",
        "approves_sources",
        "changes_source_rights",
        "creates_recorded_fixtures",
        "creates_source_failure_fixtures",
        "mutates_database",
        "creates_report_artifacts",
        "changes_report_semantics",
        "claims_level_10",
    ):
        require(limits.get(key) is False, f"ODP1 packet limits.{key} must be false", errors)

    body = require_mapping(packet.get("packet"), "ODP1 packet body", errors)
    require(body.get("odp_id") == "ODP-BOL-001", "ODP1 packet ODP id drifted", errors)
    require(
        body.get("current_owner_answer_references") == [ODP1_OWNER_ANSWER_ID],
        "ODP1 packet owner answer reference drifted",
        errors,
    )
    require(
        body.get("current_authority_record_references") == [],
        "ODP1 packet authority record references must remain empty",
        errors,
    )
    owner_template = require_mapping(body.get("owner_answer_template"), "ODP1 owner template", errors)
    require(
        owner_template.get("downstream_unlocks_requested") == [],
        "ODP1 owner answer template must not request downstream unlocks",
        errors,
    )
    authority_template = require_mapping(
        body.get("pilot_scope_authority_record_template"),
        "ODP1 authority template",
        errors,
    )
    require(
        authority_template.get("downstream_unlocks_requested") == [],
        "ODP1 authority template must not request downstream unlocks",
        errors,
    )
    policy = require_mapping(packet.get("submission_policy"), "ODP1 packet submission policy", errors)
    require(
        policy.get("downstream_updates_allowed_by_packet") is False,
        "ODP1 packet must not allow downstream updates",
        errors,
    )


def validate_odp2_owner_answer_packet(packet: dict[str, Any], errors: list[str]) -> None:
    require(
        packet.get("status")
        == "blocked_until_odp_bol_001_authority_and_missing_odp_bol_002_owner_answer",
        "ODP-BOL-002 owner-answer packet status drifted",
        errors,
    )
    approvals = require_mapping(packet.get("approvals"), "ODP2 packet approvals", errors)
    for key in (
        "owner_answer_recorded",
        "source_authority_recorded",
        "source_rights_approved",
        "downstream_authority_updates_allowed",
    ):
        require(approvals.get(key) is False, f"ODP2 packet approvals.{key} must be false", errors)

    limits = require_mapping(packet.get("limits"), "ODP2 packet limits", errors)
    require(limits.get("validate_only_answer_packet") is True, "ODP2 packet must be validate-only", errors)
    for key in (
        "records_owner_answer",
        "records_source_authority",
        "approves_sources",
        "changes_source_rights",
        "promotes_source_registry",
        "creates_recorded_fixtures",
        "creates_source_failure_fixtures",
        "mutates_database",
        "creates_report_artifacts",
        "changes_report_semantics",
        "claims_level_10",
    ):
        require(limits.get(key) is False, f"ODP2 packet limits.{key} must be false", errors)

    body = require_mapping(packet.get("packet"), "ODP2 packet body", errors)
    require(body.get("odp_id") == "ODP-BOL-002", "ODP2 packet ODP id drifted", errors)
    require(
        body.get("current_owner_answer_references") == [],
        "ODP2 packet owner answer references must remain empty",
        errors,
    )
    require(
        body.get("current_source_authority_record_references") == [],
        "ODP2 packet source authority references must remain empty",
        errors,
    )
    require(
        body.get("current_source_rights_approval_references") == [],
        "ODP2 packet source-rights references must remain empty",
        errors,
    )
    owner_template = require_mapping(body.get("owner_answer_template"), "ODP2 owner template", errors)
    require(
        owner_template.get("downstream_unlocks_requested") == [],
        "ODP2 owner answer template must not request downstream unlocks",
        errors,
    )
    authority_template = require_mapping(
        body.get("source_authority_record_template"),
        "ODP2 source authority template",
        errors,
    )
    require(
        authority_template.get("downstream_unlocks_requested") == [],
        "ODP2 source authority template must not request downstream unlocks",
        errors,
    )
    policy = require_mapping(packet.get("submission_policy"), "ODP2 packet submission policy", errors)
    require(
        policy.get("requires_odp_bol_001_cited_authority_first") is True,
        "ODP2 packet must preserve the ODP-BOL-001 prerequisite",
        errors,
    )
    require(
        policy.get("downstream_updates_allowed_by_packet") is False,
        "ODP2 packet must not allow downstream updates",
        errors,
    )


def validate_qualification_status(status: dict[str, Any], errors: list[str]) -> None:
    candidate = require_mapping(status.get("candidate"), "qualification status candidate", errors)
    for key, value in candidate.items():
        require(value is None, f"qualification candidate.{key} must remain null", errors)

    qualifications = require_mapping(status.get("qualifications"), "qualification statuses", errors)
    p0 = require_mapping(qualifications.get("p0"), "qualification p0 status", errors)
    require(p0.get("status") == "BLOCKED", "P0 must remain BLOCKED", errors)
    require(p0.get("result_path") is None, "P0 result_path must remain null", errors)
    require(
        BACKLOG_PATH in (p0.get("blocker_references") or []),
        "P0 blocker references must include the parameterization backlog",
        errors,
    )
    for name, record in qualifications.items():
        if name == "p0":
            continue
        if isinstance(record, dict):
            require(record.get("status") == "NOT_RUN", f"qualification {name} must remain NOT_RUN", errors)
            require(record.get("result_path") is None, f"qualification {name} result_path must remain null", errors)

    for section_name in ("overlays", "conditional_overlays"):
        section = require_mapping(status.get(section_name), f"qualification {section_name}", errors)
        for name, record in section.items():
            if not isinstance(record, dict):
                errors.append(f"{section_name}.{name} must be a mapping")
                continue
            require(record.get("status") == "NOT_RUN", f"{section_name}.{name} must remain NOT_RUN", errors)
            require(record.get("result_path") is None, f"{section_name}.{name} result_path must remain null", errors)
            if section_name == "conditional_overlays":
                require(record.get("applicable") is False, f"{section_name}.{name} must remain not applicable", errors)


def validate_targets(targets: dict[str, Any], errors: list[str]) -> None:
    require(targets.get("status") == "DRAFT", "qualification targets must remain globally DRAFT", errors)
    require(targets.get("frozen_at") is None, "qualification targets frozen_at must remain null", errors)
    require(targets.get("approved_by") == [], "qualification targets approved_by must remain empty", errors)

    scope = require_mapping(targets.get("scope"), "qualification target scope", errors)
    for key, expected in EXPECTED_SCOPE_VALUES.items():
        require(scope.get(key) == expected, f"scope.{key} drifted", errors)
    require(
        tuple(scope.get("source_profile_ids") or []) == EXPECTED_SELECTED_SOURCE_PROFILE_IDS,
        "scope.source_profile_ids must remain DS-002 only",
        errors,
    )
    require(
        scope.get("ruleset_versions") == {"homestead_mvp_v0_1": "0.1"},
        "scope.ruleset_versions drifted",
        errors,
    )

    bindings = require_mapping(targets.get("criterion_bindings"), "criterion_bindings", errors)
    frozen_bindings = tuple(
        criterion_id
        for criterion_id, record in bindings.items()
        if isinstance(record, dict) and record.get("status") == "FROZEN"
    )
    require(frozen_bindings == EXPECTED_FROZEN_BINDINGS, "only W-003 and W-011 may be frozen", errors)
    for criterion_id, record in bindings.items():
        if isinstance(record, dict):
            require(record.get("status") != "PASS", f"{criterion_id} must not be PASS", errors)


def validate_source_profile(profile: dict[str, Any], errors: list[str]) -> None:
    require(profile.get("source_id") == "DS-002", "source profile source_id must remain DS-002", errors)
    require(profile.get("status") == "APPROVED", "DS-002 source profile must remain APPROVED", errors)
    require(
        profile.get("approved_use_profiles") == ["BOUNDED_USER_VALIDATED"],
        "DS-002 approved use profile drifted",
        errors,
    )
    require_mapping(profile.get("authority"), "DS-002 authority", errors)
    require_mapping(profile.get("rights"), "DS-002 rights", errors)
    controls = profile.get("conditions_enforced_by")
    require(
        isinstance(controls, list) and len(controls) > 0,
        "DS-002 enforcement controls must be non-empty",
        errors,
    )


def validate_task_queue(root: Path, task_queue: dict[str, Any], errors: list[str]) -> None:
    active_plan = task_queue.get("active_plan")
    require(
        isinstance(active_plan, str)
        and active_plan.startswith("plans/")
        and active_plan.endswith(".md"),
        "task queue active_plan must point to a plan file",
        errors,
    )
    if isinstance(active_plan, str):
        require(
            active_plan == EXPECTED_AUTH_EVIDENCE_PLAN,
            "task queue active_plan must point to the authority-evidence intake plan",
            errors,
        )
        require(
            repo_relative_path(root, active_plan).is_file(),
            f"task queue active_plan file missing: {active_plan}",
            errors,
        )
    tasks = task_queue.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("task queue tasks must be a non-empty list")
        return
    by_id = {
        str(task.get("id")): task
        for task in tasks
        if isinstance(task, dict) and task.get("id")
    }
    active_ids = [task_id for task_id, task in by_id.items() if task.get("status") == "active"]
    require(
        active_ids == ["AUTH-EVIDENCE-INTAKE"],
        f"task queue must have only AUTH-EVIDENCE-INTAKE active, found {active_ids}",
        errors,
    )

    for task_id in EXPECTED_DONE_TASKS:
        task = by_id.get(task_id)
        require(task is not None, f"task queue missing {task_id}", errors)
        if task is not None:
            require(task.get("status") == "done", f"{task_id} must be done", errors)
    eq5 = by_id.get("EQ-5") or {}
    require(eq5.get("depends_on") == ["BOL-POST-ODP4-AUTH"], "EQ-5 dependency drifted", errors)
    require(eq5.get("spec") == EXPECTED_EQ5_PLAN, "EQ-5 spec must point to the EQ-5 plan", errors)
    odgav = by_id.get("ODGAV-1") or {}
    require(odgav.get("depends_on") == ["BOL-ODP2-PACKET"], "ODGAV-1 dependency drifted", errors)
    require(odgav.get("status") == "done", "ODGAV-1 must be done", errors)
    require(
        odgav.get("spec") == EXPECTED_ODGAV_PLAN,
        "ODGAV-1 spec must point to the ODGAV owner-answer evaluation plan",
        errors,
    )
    require(
        "side-effect-free synthetic owner-answer evaluators" in str(odgav.get("notes") or ""),
        "ODGAV-1 notes must preserve owner-independent synthetic evaluator scope",
        errors,
    )
    minerals = by_id.get("MINERALS-FIXTURE") or {}
    require(
        minerals.get("depends_on") == ["ODGAV-1"],
        "MINERALS-FIXTURE dependency drifted",
        errors,
    )
    require(
        minerals.get("status") == "done",
        "MINERALS-FIXTURE must be done",
        errors,
    )
    require(
        minerals.get("spec") == EXPECTED_MINERALS_PLAN,
        "MINERALS-FIXTURE spec must point to the minerals fixture-ingestion plan",
        errors,
    )
    require(
        "extended-domain fixture-ingestion proof for minerals"
        in str(minerals.get("notes") or ""),
        "MINERALS-FIXTURE notes must preserve completed minerals fixture scope",
        errors,
    )
    broadband = by_id.get("BROADBAND-FIXTURE") or {}
    require(
        broadband.get("depends_on") == ["MINERALS-FIXTURE"],
        "BROADBAND-FIXTURE dependency drifted",
        errors,
    )
    require(
        broadband.get("status") == "done",
        "BROADBAND-FIXTURE must be done",
        errors,
    )
    require(
        broadband.get("spec") == EXPECTED_BROADBAND_PLAN,
        "BROADBAND-FIXTURE spec must point to the broadband fixture-ingestion plan",
        errors,
    )
    require(
        "FCC Broadband Data Collection fixture evidence" in str(broadband.get("notes") or ""),
        "BROADBAND-FIXTURE notes must preserve FCC broadband fixture scope",
        errors,
    )
    env_hazard = by_id.get("ENV-FIXTURE") or {}
    require(
        env_hazard.get("depends_on") == ["BROADBAND-FIXTURE"],
        "ENV-FIXTURE dependency drifted",
        errors,
    )
    require(
        env_hazard.get("status") == "done",
        "ENV-FIXTURE must be done",
        errors,
    )
    require(
        env_hazard.get("spec") == EXPECTED_ENV_HAZARD_PLAN,
        "ENV-FIXTURE spec must point to the env-hazard fixture-ingestion plan",
        errors,
    )
    require(
        "EPA ECHO environmental hazard fixture evidence" in str(env_hazard.get("notes") or ""),
        "ENV-FIXTURE notes must preserve EPA ECHO fixture scope",
        errors,
    )
    water = by_id.get("WATER-FIXTURE") or {}
    require(
        water.get("depends_on") == ["ENV-FIXTURE"],
        "WATER-FIXTURE dependency drifted",
        errors,
    )
    require(
        water.get("status") == "done",
        "WATER-FIXTURE must be done",
        errors,
    )
    require(
        water.get("spec") == EXPECTED_WATER_PLAN,
        "WATER-FIXTURE spec must point to the water fixture-ingestion plan",
        errors,
    )
    require(
        "USGS water monitoring context fixture evidence" in str(water.get("notes") or ""),
        "WATER-FIXTURE notes must preserve USGS water monitoring fixture scope",
        errors,
    )
    geology = by_id.get("GEOLOGY-FIXTURE") or {}
    require(
        geology.get("depends_on") == ["WATER-FIXTURE"],
        "GEOLOGY-FIXTURE dependency drifted",
        errors,
    )
    require(
        geology.get("status") == "done",
        "GEOLOGY-FIXTURE must be done",
        errors,
    )
    require(
        geology.get("spec") == EXPECTED_GEOLOGY_PLAN,
        "GEOLOGY-FIXTURE spec must point to the geology fixture-ingestion plan",
        errors,
    )
    require(
        "NC Geological Survey 1985 geologic map-unit context fixture evidence"
        in str(geology.get("notes") or ""),
        "GEOLOGY-FIXTURE notes must preserve NCGS geology fixture scope",
        errors,
    )
    post_geology = by_id.get("POST-GEOLOGY-ROUTING") or {}
    require(
        post_geology.get("depends_on") == ["GEOLOGY-FIXTURE"],
        "POST-GEOLOGY-ROUTING dependency drifted",
        errors,
    )
    require(
        post_geology.get("status") == "done",
        "POST-GEOLOGY-ROUTING must be done",
        errors,
    )
    require(
        post_geology.get("spec") == EXPECTED_POST_GEOLOGY_PLAN,
        "POST-GEOLOGY-ROUTING spec must point to the post-geology routing plan",
        errors,
    )
    require(
        "Routing-only closeout after PR #172" in str(post_geology.get("notes") or ""),
        "POST-GEOLOGY-ROUTING notes must preserve routing-only closeout scope",
        errors,
    )
    auth_evidence = by_id.get("AUTH-EVIDENCE-INTAKE") or {}
    require(
        auth_evidence.get("depends_on") == ["POST-GEOLOGY-ROUTING"],
        "AUTH-EVIDENCE-INTAKE dependency drifted",
        errors,
    )
    require(
        auth_evidence.get("status") == "active",
        "AUTH-EVIDENCE-INTAKE must be active",
        errors,
    )
    require(
        auth_evidence.get("spec") == EXPECTED_AUTH_EVIDENCE_PLAN,
        "AUTH-EVIDENCE-INTAKE spec must point to the authority-evidence intake plan",
        errors,
    )
    require(
        "Authority-evidence posture after PR #175"
        in str(auth_evidence.get("notes") or ""),
        "AUTH-EVIDENCE-INTAKE notes must preserve authority-evidence routing scope",
        errors,
    )

    for task_id in EXPECTED_BLOCKED_TASKS:
        task = by_id.get(task_id)
        require(task is not None, f"task queue missing blocked task {task_id}", errors)
        if task is not None:
            require(task.get("status") == "blocked", f"{task_id} must remain blocked", errors)
            require(
                "external/owner authority" in str(task.get("notes") or ""),
                f"{task_id} notes must cite external/owner authority",
                errors,
            )


def validate_repo_controls(root: Path, errors: list[str]) -> None:
    controls = (
        ("scripts/verify.ps1", "qualification_parameterization_backlog_check.py"),
        ("scripts/verify.sh", "qualification_parameterization_backlog_check.py"),
        (".github/workflows/ci.yml", "Validate qualification parameterization backlog"),
        ("scripts/run_qualification_parameterization_backlog_check.ps1", "qualification_parameterization_backlog_check.py"),
        ("scripts/run_qualification_parameterization_backlog_check.sh", "qualification_parameterization_backlog_check.py"),
        ("scripts/run_bologna_odp1_owner_answer_packet_check.ps1", "bologna_odp1_owner_answer_packet_check.py"),
        ("scripts/run_bologna_odp1_owner_answer_packet_check.sh", "bologna_odp1_owner_answer_packet_check.py"),
        ("scripts/run_bol_scope_auth_check.ps1", "bol_scope_auth_check.py"),
        ("scripts/run_bol_scope_auth_check.sh", "bol_scope_auth_check.py"),
        ("scripts/run_bologna_odp2_owner_answer_packet_check.ps1", "bologna_odp2_owner_answer_packet_check.py"),
        ("scripts/run_bologna_odp2_owner_answer_packet_check.sh", "bologna_odp2_owner_answer_packet_check.py"),
        ("MANIFEST.md", "scripts/qualification_parameterization_backlog_check.py"),
        ("MANIFEST.md", "config/bologna_odp1_owner_answer_packet.yaml"),
        ("MANIFEST.md", "config/bol_scope_auth.yaml"),
        ("MANIFEST.md", "config/bologna_odp2_owner_answer_packet.yaml"),
        ("MANIFEST.md", "scripts/bologna_owner_answer_evaluator.py"),
        ("plans/README.md", EXPECTED_SCOPE_PURSUIT_PLAN),
        ("plans/README.md", EXPECTED_BOL_SCOPE_AUTH_PLAN),
        ("plans/README.md", EXPECTED_ODP2_PACKET_PLAN),
        ("plans/README.md", EXPECTED_ODGAV_PLAN),
        ("plans/README.md", EXPECTED_MINERALS_PLAN),
        ("plans/README.md", EXPECTED_BROADBAND_PLAN),
        ("plans/README.md", EXPECTED_ENV_HAZARD_PLAN),
        ("plans/README.md", EXPECTED_WATER_PLAN),
        ("plans/README.md", EXPECTED_GEOLOGY_PLAN),
        ("plans/README.md", EXPECTED_POST_GEOLOGY_PLAN),
        ("plans/README.md", EXPECTED_AUTH_EVIDENCE_PLAN),
        ("state/PROJECT_STATE.md", "Post-PR175 authority evidence guard"),
        (ODP1_OWNER_ANSWER_PACKET_PATH, "downstream_updates_allowed_by_packet: false"),
        (BOL_SCOPE_AUTH_PATH, "required_next_owner_answer_type: approve_with_cited_authority"),
        (ODP2_OWNER_ANSWER_PACKET_PATH, "requires_odp_bol_001_cited_authority_first: true"),
        ("docs/runbooks/bologna_odp1_owner_answer_packet.md", "review-only scope pursuit"),
        ("docs/runbooks/bol_scope_auth.md", "approve_with_cited_authority"),
        ("docs/runbooks/bologna_odp2_owner_answer_packet.md", "missing_pilot_scope_authority"),
        (EXPECTED_EQ5_PLAN, "## Decision log"),
        (EXPECTED_SCOPE_PURSUIT_PLAN, "## Decision log"),
        (EXPECTED_BOL_SCOPE_AUTH_PLAN, "## Decision log"),
        (EXPECTED_ODP2_PACKET_PLAN, "## Decision log"),
        (EXPECTED_ODGAV_PLAN, "## Decision log"),
        (EXPECTED_MINERALS_PLAN, "## Acceptance criteria"),
        (EXPECTED_BROADBAND_PLAN, "## Decision log"),
        (EXPECTED_ENV_HAZARD_PLAN, "## Decision log"),
        (EXPECTED_WATER_PLAN, "## Decision log"),
        (EXPECTED_GEOLOGY_PLAN, "## Decision log"),
        (EXPECTED_POST_GEOLOGY_PLAN, "## Decision log"),
        (EXPECTED_AUTH_EVIDENCE_PLAN, "## Decision log"),
    )
    for path_text, fragment in controls:
        text = read_text(root, path_text)
        require(fragment in text, f"{path_text} missing expected fragment: {fragment}", errors)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    validate_backlog(read_text(root, BACKLOG_PATH), errors)
    validate_owner_packet(read_text(root, OWNER_PACKET_PATH), errors)
    validate_owner_decisions(read_text(root, OWNER_DECISIONS_PATH), errors)
    validate_owner_intake(load_yaml(root, OWNER_INTAKE_PATH), errors)
    validate_odp1_owner_answer_packet(load_yaml(root, ODP1_OWNER_ANSWER_PACKET_PATH), errors)
    validate_odp2_owner_answer_packet(load_yaml(root, ODP2_OWNER_ANSWER_PACKET_PATH), errors)
    validate_qualification_status(load_yaml(root, QUALIFICATION_STATUS_PATH), errors)
    validate_targets(load_yaml(root, QUALIFICATION_TARGETS_PATH), errors)
    validate_source_profile(load_yaml(root, SOURCE_PROFILE_PATH), errors)
    validate_task_queue(root, load_yaml(root, TASK_QUEUE_PATH), errors)
    validate_repo_controls(root, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the EQ-5 owner-decision parameterization backlog boundary.",
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    try:
        errors = validate(root)
    except QualificationParameterizationBacklogError as exc:
        print(f"FAIL: {exc}")
        print("qualification parameterization backlog check: FAIL")
        return 1

    if errors:
        if args.json_output:
            print(json.dumps({"ok": False, "errors": errors}, indent=2, sort_keys=True))
        else:
            for error in errors:
                print(f"FAIL: {error}")
            print("qualification parameterization backlog check: FAIL")
        return 1

    if args.json_output:
        print(
            json.dumps(
                {
                    "ok": True,
                    "owner_decision_ids": list(EXPECTED_OWNER_DECISION_IDS),
                    "selected_source_profile_ids": list(EXPECTED_SELECTED_SOURCE_PROFILE_IDS),
                    "frozen_bindings": list(EXPECTED_FROZEN_BINDINGS),
                    "bologna_threads": list(EXPECTED_BOL_THREADS),
                    "eq5_plan": EXPECTED_EQ5_PLAN,
                    "active_plan": EXPECTED_AUTH_EVIDENCE_PLAN,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"owner decision blockers: {len(EXPECTED_OWNER_DECISION_IDS)}")
        print(f"selected source profiles: {', '.join(EXPECTED_SELECTED_SOURCE_PROFILE_IDS)}")
        print(f"frozen criterion bindings: {', '.join(EXPECTED_FROZEN_BINDINGS)}")
        print("P0 status: BLOCKED")
        print("qualification parameterization backlog check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
