from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

EXPECTED_ACTIVE_PLAN = "plans/2026-07-02-authority-evidence-intake.md"
EXPECTED_ACTIVE_TASK = "AUTH-EVIDENCE-INTAKE"
EXPECTED_COMPLETED_PREREQUISITE = "POST-GEOLOGY-ROUTING"

EXPECTED_PRODUCTION_STREAMS = {
    "ds017_source_entitlement",
    "hosted_platform",
    "secrets_manager",
    "identity_rbac",
    "image_publication",
    "billing_cost",
    "hosted_observability",
    "bologna_pilot_scope",
    "bologna_recorded_source",
}

EXPECTED_BOL_THREAD_STATUS = {
    "ODP-BOL-001": "review_only_scope_pursuit_answered",
    "ODP-BOL-002": "missing_owner_answer",
    "ODP-BOL-003": "missing_owner_answer",
    "ODP-BOL-004": "missing_owner_answer",
}

BLOCKED_IMPLEMENTATION_BOUNDARIES = (
    "owner_answer_recording",
    "source_approval",
    "source_rights_change",
    "recorded_corpus",
    "fixture_capture",
    "db_seed",
    "report_proof",
    "schema_api_auth_ui_runtime_change",
    "ds017_approval",
    "hosted_level_10_authority",
    "qualification_pass",
    "owner_decision_unfreeze",
    "p0_unblock",
)

EXPECTED_CONFIG_STATUS = {
    "config/bologna_pilot_scope_authority.yaml": "blocked_no_pilot_scope_authority",
    "config/bol_scope_auth.yaml": "blocked_review_only_owner_answer",
    "config/bologna_source_authority_intake.yaml": "blocked_no_authority",
    "config/bologna_source_rights.yaml": "repo_local_validate_only",
    "config/bologna_recorded_source_corpus.yaml": "blocked_no_authority",
    "config/bologna_owner_answer_intake.yaml": "blocked_review_only_scope_pursuit",
    "config/bologna_odp2_owner_answer_packet.yaml": (
        "blocked_until_odp_bol_001_authority_and_missing_odp_bol_002_owner_answer"
    ),
    "config/bologna_odp2_source_rights_response_gate.yaml": (
        "blocked_until_odp_bol_001_authority_and_missing_odp_bol_002_owner_answer"
    ),
    "config/bologna_odp3_corpus_response_gate.yaml": (
        "blocked_until_odp_bol_001_odp_bol_002_and_missing_odp_bol_003_owner_answer"
    ),
    "config/bologna_odp4_db_report_proof_response_gate.yaml": (
        "blocked_until_odp_bol_001_odp_bol_002_odp_bol_003_and_missing_odp_bol_004_owner_answer"
    ),
    "config/production_authority_intake.yaml": "blocked_no_external_authority",
    "config/source_entitlements.yaml": "repo_local_validate_only",
}

EXPECTED_REQUIRED_VALIDATORS = (
    ("qualification parameterization backlog", "scripts/qualification_parameterization_backlog_check.py"),
    ("readiness matrix", "scripts/readiness_matrix_check.py"),
    ("source entitlement", "scripts/source_entitlement_check.py"),
    ("production authority intake", "scripts/production_authority_intake_check.py"),
    ("Bologna pilot scope authority", "scripts/bologna_pilot_scope_authority_check.py"),
    ("Bologna owner answer intake", "scripts/bologna_owner_answer_intake_check.py"),
    ("Bologna ODP-BOL-001 owner answer packet", "scripts/bologna_odp1_owner_answer_packet_check.py"),
    ("Bologna ODP-BOL-001 response gate", "scripts/bologna_odp1_owner_response_gate_check.py"),
    ("Bologna scope authority readiness", "scripts/bol_scope_auth_check.py"),
    ("Bologna source authority intake", "scripts/bologna_source_authority_intake_check.py"),
    ("Bologna source rights", "scripts/bologna_source_rights_check.py"),
    ("Bologna ODP-BOL-002 owner answer packet", "scripts/bologna_odp2_owner_answer_packet_check.py"),
    (
        "Bologna ODP-BOL-002 source rights response gate",
        "scripts/bologna_odp2_source_rights_response_gate_check.py",
    ),
    ("Bologna recorded source corpus", "scripts/bologna_recorded_source_corpus_check.py"),
    ("Bologna ODP-BOL-003 corpus response gate", "scripts/bologna_odp3_corpus_response_gate_check.py"),
    (
        "Bologna ODP-BOL-004 DB report proof response gate",
        "scripts/bologna_odp4_db_report_proof_response_gate_check.py",
    ),
)

REQUIRED_FILES = (
    EXPECTED_ACTIVE_PLAN,
    "plans/README.md",
    "tasks/task_queue.yaml",
    "state/PROJECT_STATE.md",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "state/EMPIRICAL_QUALIFICATION_STATUS.yaml",
    "state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md",
    "scripts/authority_evidence_intake_check.py",
    "scripts/run_authority_evidence_intake_check.ps1",
    "scripts/run_authority_evidence_intake_check.sh",
    "scripts/verify.ps1",
    "scripts/verify.sh",
    "MANIFEST.md",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return value


def require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list):
        raise SystemExit(message)
    return value


def require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(message)
    return value.strip()


def normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def repo_path(path_text: str) -> Path:
    return ROOT / normalize_path(path_text)


def read_text(path_text: str) -> str:
    return repo_path(path_text).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must be a mapping")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require(repo_path(path_text).exists(), f"authority evidence artifact missing: {path_text}")
    for _label, path_text in EXPECTED_REQUIRED_VALIDATORS:
        require(repo_path(path_text).exists(), f"required validator missing: {path_text}")


def validate_task_routing(task_queue: dict[str, Any]) -> None:
    require(
        task_queue.get("active_plan") == EXPECTED_ACTIVE_PLAN,
        "task queue active_plan must point to authority evidence intake",
    )
    tasks = require_list(task_queue.get("tasks"), "task queue tasks must be a list")
    by_id = {
        require_text(task.get("id"), "task id missing"): require_mapping(task, "task must be a mapping")
        for task in tasks
    }
    active_ids = [task_id for task_id, task in by_id.items() if task.get("status") == "active"]
    require(
        active_ids == [EXPECTED_ACTIVE_TASK],
        f"task queue must have only {EXPECTED_ACTIVE_TASK} active, found {active_ids}",
    )
    prerequisite = require_mapping(
        by_id.get(EXPECTED_COMPLETED_PREREQUISITE),
        f"{EXPECTED_COMPLETED_PREREQUISITE} missing",
    )
    require(
        prerequisite.get("status") == "done",
        f"{EXPECTED_COMPLETED_PREREQUISITE} must remain done",
    )
    active = require_mapping(by_id.get(EXPECTED_ACTIVE_TASK), f"{EXPECTED_ACTIVE_TASK} missing")
    require(
        active.get("depends_on") == [EXPECTED_COMPLETED_PREREQUISITE],
        f"{EXPECTED_ACTIVE_TASK} dependency drifted",
    )
    require(active.get("status") == "active", f"{EXPECTED_ACTIVE_TASK} must remain active")
    require(active.get("spec") == EXPECTED_ACTIVE_PLAN, f"{EXPECTED_ACTIVE_TASK} plan drifted")
    notes = str(active.get("notes") or "")
    for phrase in (
        "cited external owner/source authority",
        "Do not record owner answers",
        "unblock P0",
        "claim Level 10 authority",
    ):
        require(phrase in notes, f"{EXPECTED_ACTIVE_TASK} notes missing boundary: {phrase}")

    blocked_tasks = {
        "BSA-001",
        "EQ-BLOCK-BOLOGNA-SCOPE",
        "EQ-BLOCK-BOLOGNA-SOURCE-RIGHTS",
        "EQ-BLOCK-BOLOGNA-CORPUS",
        "EQ-BLOCK-BOLOGNA-REPORT",
    }
    for task_id in blocked_tasks:
        task = require_mapping(by_id.get(task_id), f"{task_id} missing")
        require(task.get("status") == "blocked", f"{task_id} must remain blocked")
        require(
            "external/owner authority" in str(task.get("notes") or ""),
            f"{task_id} must cite external/owner authority",
        )


def validate_plan_and_state_text() -> None:
    plan = read_text(EXPECTED_ACTIVE_PLAN)
    normalized_plan = plan.lower()
    project_state = read_text("state/PROJECT_STATE.md")
    plans_index = read_text("plans/README.md")
    for phrase in (
        "authority evidence intake",
        "requires cited external authority evidence",
        "do not record a new owner answer",
        "qualification `pass`",
        "no new source approval",
    ):
        require(phrase in normalized_plan, f"active plan missing boundary: {phrase}")
    for phrase in (
        "Post-PR175 authority evidence guard",
        "`plans/2026-07-02-authority-evidence-intake.md`",
        "Active task is AUTH-EVIDENCE-INTAKE",
        "`P0` remains `BLOCKED`",
    ):
        require(phrase in project_state, f"project state missing boundary: {phrase}")
    require(
        "`AUTH-EVIDENCE-INTAKE` is the active authority-evidence routing posture" in plans_index,
        "plans index must name AUTH-EVIDENCE-INTAKE as active",
    )


def validate_config_statuses() -> None:
    for path_text, expected_status in EXPECTED_CONFIG_STATUS.items():
        payload = load_yaml(path_text)
        require(payload.get("status") == expected_status, f"{path_text} status drifted")


def validate_production_streams(payload: dict[str, Any]) -> None:
    streams = require_list(payload.get("authority_streams"), "authority streams must be a list")
    by_id = {
        require_text(stream.get("id"), "authority stream id missing"): require_mapping(
            stream,
            "authority stream must be a mapping",
        )
        for stream in streams
    }
    require(set(by_id) == EXPECTED_PRODUCTION_STREAMS, "authority evidence stream set drifted")
    for stream_id, stream in by_id.items():
        require(stream.get("status") == "blocked", f"{stream_id} must remain blocked")
        require(stream.get("evidence_status") == "missing", f"{stream_id} evidence changed")
        require(stream.get("authority_references") == [], f"{stream_id} references changed")
        require(
            stream.get("decision_updates_allowed") is False,
            f"{stream_id} decision updates unexpectedly allowed",
        )


def validate_bologna_owner_threads(payload: dict[str, Any]) -> None:
    threads = require_list(payload.get("bologna_decision_threads"), "Bologna threads missing")
    by_id = {
        require_text(thread.get("odp_id"), "ODP id missing"): require_mapping(
            thread,
            "Bologna thread must be a mapping",
        )
        for thread in threads
    }
    require(set(by_id) == set(EXPECTED_BOL_THREAD_STATUS), "Bologna ODP thread set drifted")
    for odp_id, expected_status in EXPECTED_BOL_THREAD_STATUS.items():
        thread = by_id[odp_id]
        require(thread.get("status") == expected_status, f"{odp_id} status drifted")
        require(thread.get("downstream_updates_allowed") is False, f"{odp_id} unlocked downstream")
        if odp_id != "ODP-BOL-001":
            require(thread.get("owner_answer_references") == [], f"{odp_id} owner answer changed")

    contract = require_mapping(
        payload.get("owner_answer_contract"),
        "owner answer contract missing",
    )
    answers = require_list(contract.get("current_owner_answers"), "owner answers must be a list")
    require(len(answers) == 1, "only the review-only ODP-BOL-001 answer may be recorded")
    answer = require_mapping(answers[0], "owner answer must be a mapping")
    require(answer.get("odp_id") == "ODP-BOL-001", "recorded owner answer ODP drifted")
    require(answer.get("answer_type") == "approve_review_only", "owner answer is not review-only")
    require(answer.get("downstream_unlocks_requested") == [], "owner answer unlocked downstream")


def validate_empty_authority_records() -> None:
    pilot = load_yaml("config/bologna_pilot_scope_authority.yaml")
    pilot_contract = require_mapping(
        pilot.get("authority_record_contract"),
        "pilot authority record contract missing",
    )
    require(
        pilot_contract.get("current_authority_records") == [],
        "pilot authority records must remain empty",
    )
    source = load_yaml("config/bologna_source_authority_intake.yaml")
    source_contract = require_mapping(
        source.get("source_authority_record_contract"),
        "source authority record contract missing",
    )
    require(
        source_contract.get("current_source_authority_records") == [],
        "source authority records must remain empty",
    )

    odp2 = require_mapping(load_yaml("config/bologna_odp2_owner_answer_packet.yaml").get("packet"), "ODP2 packet missing")
    for key in (
        "current_owner_answer_references",
        "current_source_authority_record_references",
        "current_source_rights_approval_references",
    ):
        require(odp2.get(key) == [], f"ODP2 {key} must remain empty")


def validate_qualification_status(payload: dict[str, Any]) -> None:
    qualifications = require_mapping(payload.get("qualifications"), "qualifications missing")
    p0 = require_mapping(qualifications.get("p0"), "P0 status missing")
    require(p0.get("status") == "BLOCKED", "P0 must remain BLOCKED")
    require(p0.get("result_path") is None, "P0 result path must remain null")
    for qualification_id, qualification in qualifications.items():
        if qualification_id == "p0":
            continue
        status = require_mapping(qualification, f"{qualification_id} status missing").get("status")
        require(status == "NOT_RUN", f"{qualification_id} must remain NOT_RUN")


def validate_repo_wiring() -> None:
    expected_fragments = (
        ("scripts/verify.ps1", "authority_evidence_intake_check.py"),
        ("scripts/verify.sh", "authority_evidence_intake_check.py"),
        ("MANIFEST.md", "scripts/authority_evidence_intake_check.py"),
        ("MANIFEST.md", "Authority evidence intake posture"),
        (EXPECTED_ACTIVE_PLAN, "scripts\\authority_evidence_intake_check.py"),
        ("tasks/task_queue.yaml", "scripts\\authority_evidence_intake_check.py"),
    )
    for path_text, fragment in expected_fragments:
        require(fragment in read_text(path_text), f"{path_text} missing expected fragment: {fragment}")


def load_module(path_text: str) -> ModuleType:
    path = repo_path(path_text)
    module_name = f"_authority_evidence_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load validator: {path_text}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def run_validator(label: str, path_text: str) -> None:
    module = load_module(path_text)
    main = getattr(module, "main", None)
    if not callable(main):
        raise SystemExit(f"{label} validator lacks main()")
    main_func = cast(Callable[..., int | None], main)
    args: list[str] = []
    if path_text == "scripts/qualification_parameterization_backlog_check.py":
        args = ["--root", str(ROOT)]
    elif path_text == "scripts/qualification_status_check.py":
        args = ["--root", str(ROOT)]

    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            result = main_func(args) if args else main_func()
    except SystemExit as exc:
        details = output.getvalue().strip()
        suffix = f": {details}" if details else ""
        raise SystemExit(f"{label} validator failed{suffix}") from exc
    require(result in (0, None), f"{label} validator returned {result}")


def run_required_validators() -> None:
    for label, path_text in EXPECTED_REQUIRED_VALIDATORS:
        run_validator(label, path_text)


def required_thread_fields(thread: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    for key in (
        "required_decisions",
        "required_rights_decisions",
        "required_corpus_decisions",
        "required_manifest_fields",
        "required_report_proof_fields",
    ):
        values = thread.get(key)
        if isinstance(values, list):
            fields.extend(str(value) for value in values)
    return fields


def build_summary() -> dict[str, Any]:
    task_queue = load_yaml("tasks/task_queue.yaml")
    production = load_yaml("config/production_authority_intake.yaml")
    bologna = load_yaml("config/bologna_owner_answer_intake.yaml")
    status = load_yaml("state/EMPIRICAL_QUALIFICATION_STATUS.yaml")
    pilot_authority = load_yaml("config/bologna_pilot_scope_authority.yaml")
    source_authority = load_yaml("config/bologna_source_authority_intake.yaml")
    odp2_packet = load_yaml("config/bologna_odp2_owner_answer_packet.yaml")

    tasks = require_list(task_queue.get("tasks"), "task queue tasks must be a list")
    active_tasks = [
        require_text(task.get("id"), "task id missing")
        for task in tasks
        if require_mapping(task, "task must be a mapping").get("status") == "active"
    ]

    production_streams = []
    for stream in require_list(production.get("authority_streams"), "authority streams must be a list"):
        stream_map = require_mapping(stream, "authority stream must be a mapping")
        required_evidence = require_list(
            stream_map.get("required_evidence"),
            "authority stream required_evidence must be a list",
        )
        authority_references = require_list(
            stream_map.get("authority_references"),
            "authority stream authority_references must be a list",
        )
        production_streams.append(
            {
                "id": require_text(stream_map.get("id"), "authority stream id missing"),
                "status": stream_map.get("status"),
                "evidence_status": stream_map.get("evidence_status"),
                "source_catalog": stream_map.get("source_catalog"),
                "required_evidence": required_evidence,
                "required_evidence_count": len(required_evidence),
                "authority_reference_count": len(authority_references),
                "decision_updates_allowed": stream_map.get("decision_updates_allowed"),
            }
        )

    bologna_threads = []
    for thread in require_list(bologna.get("bologna_decision_threads"), "Bologna threads missing"):
        thread_map = require_mapping(thread, "Bologna thread must be a mapping")
        owner_answer_references = require_list(
            thread_map.get("owner_answer_references"),
            "owner answer references must be a list",
        )
        required_fields = required_thread_fields(thread_map)
        bologna_threads.append(
            {
                "odp_id": require_text(thread_map.get("odp_id"), "ODP id missing"),
                "sequence": thread_map.get("sequence"),
                "status": thread_map.get("status"),
                "source_packets": thread_map.get("source_packets", []),
                "prerequisite_odp_ids": thread_map.get("prerequisite_odp_ids", []),
                "required_fields": required_fields,
                "required_field_count": len(required_fields),
                "owner_answer_reference_count": len(owner_answer_references),
                "downstream_updates_allowed": thread_map.get("downstream_updates_allowed"),
            }
        )

    qualifications = require_mapping(status.get("qualifications"), "qualifications missing")
    p0 = require_mapping(qualifications.get("p0"), "P0 status missing")
    pilot_contract = require_mapping(
        pilot_authority.get("authority_record_contract"),
        "pilot authority record contract missing",
    )
    source_contract = require_mapping(
        source_authority.get("source_authority_record_contract"),
        "source authority record contract missing",
    )
    odp2 = require_mapping(odp2_packet.get("packet"), "ODP2 packet missing")
    return {
        "schema_version": "authority_evidence_intake_summary_v1",
        "ok": True,
        "active_plan": task_queue.get("active_plan"),
        "active_task": active_tasks[0] if len(active_tasks) == 1 else None,
        "active_tasks": active_tasks,
        "completed_prerequisite": EXPECTED_COMPLETED_PREREQUISITE,
        "production_authority_status": production.get("status"),
        "production_streams": production_streams,
        "bologna_owner_answer_status": bologna.get("status"),
        "bologna_threads": bologna_threads,
        "authority_record_state": {
            "pilot_authority_record_count": len(
                require_list(
                    pilot_contract.get("current_authority_records"),
                    "pilot authority records must be a list",
                )
            ),
            "source_authority_record_count": len(
                require_list(
                    source_contract.get("current_source_authority_records"),
                    "source authority records must be a list",
                )
            ),
            "odp2_owner_answer_reference_count": len(
                require_list(
                    odp2.get("current_owner_answer_references"),
                    "ODP2 owner answer references must be a list",
                )
            ),
            "odp2_source_authority_record_reference_count": len(
                require_list(
                    odp2.get("current_source_authority_record_references"),
                    "ODP2 source authority record references must be a list",
                )
            ),
            "odp2_source_rights_approval_reference_count": len(
                require_list(
                    odp2.get("current_source_rights_approval_references"),
                    "ODP2 source rights approval references must be a list",
                )
            ),
        },
        "qualification": {
            "p0_status": p0.get("status"),
            "p0_result_path": p0.get("result_path"),
            "non_p0_statuses": {
                qualification_id: require_mapping(qualification, f"{qualification_id} status missing").get("status")
                for qualification_id, qualification in qualifications.items()
                if qualification_id != "p0"
            },
        },
        "blocked_implementation_boundaries": list(BLOCKED_IMPLEMENTATION_BOUNDARIES),
    }


def format_summary(summary: dict[str, Any]) -> str:
    production_streams = require_list(summary.get("production_streams"), "production streams missing")
    bologna_threads = require_list(summary.get("bologna_threads"), "Bologna threads missing")
    lines = [
        "authority evidence intake summary: blocked",
        f"schema_version: {summary.get('schema_version')}",
        f"active_plan: {summary.get('active_plan')}",
        f"active_task: {summary.get('active_task')}",
        f"active_tasks: {', '.join(str(task) for task in summary.get('active_tasks', []))}",
        f"completed_prerequisite: {summary.get('completed_prerequisite')}",
        f"production_authority_status: {summary.get('production_authority_status')}",
        f"bologna_owner_answer_status: {summary.get('bologna_owner_answer_status')}",
        f"p0_status: {require_mapping(summary.get('qualification'), 'qualification missing').get('p0_status')}",
        f"production_streams: {len(production_streams)}",
    ]
    for stream in production_streams:
        stream_map = require_mapping(stream, "production stream must be a mapping")
        lines.append(
            "production_stream "
            f"{stream_map.get('id')}: "
            f"status={stream_map.get('status')} "
            f"evidence_status={stream_map.get('evidence_status')} "
            f"required_evidence={stream_map.get('required_evidence_count')} "
            f"authority_references={stream_map.get('authority_reference_count')} "
            f"decision_updates_allowed={stream_map.get('decision_updates_allowed')}"
        )
    lines.append(f"bologna_threads: {len(bologna_threads)}")
    for thread in bologna_threads:
        thread_map = require_mapping(thread, "Bologna thread must be a mapping")
        lines.append(
            "bologna_thread "
            f"{thread_map.get('odp_id')}: "
            f"status={thread_map.get('status')} "
            f"required_fields={thread_map.get('required_field_count')} "
            f"owner_answer_references={thread_map.get('owner_answer_reference_count')} "
            f"downstream_updates_allowed={thread_map.get('downstream_updates_allowed')}"
        )
    authority_record_state = require_mapping(
        summary.get("authority_record_state"),
        "authority record state missing",
    )
    lines.append(
        "authority_record_state: "
        f"pilot={authority_record_state.get('pilot_authority_record_count')} "
        f"source={authority_record_state.get('source_authority_record_count')} "
        f"odp2_owner_answers={authority_record_state.get('odp2_owner_answer_reference_count')} "
        "odp2_source_authority_refs="
        f"{authority_record_state.get('odp2_source_authority_record_reference_count')} "
        "odp2_source_rights_refs="
        f"{authority_record_state.get('odp2_source_rights_approval_reference_count')}"
    )
    lines.append(
        "blocked_implementation_boundaries: "
        + ", ".join(str(boundary) for boundary in summary.get("blocked_implementation_boundaries", []))
    )
    lines.append("authority evidence intake check: ok")
    return "\n".join(lines)


def validate() -> None:
    validate_required_files()
    validate_task_routing(load_yaml("tasks/task_queue.yaml"))
    validate_plan_and_state_text()
    validate_config_statuses()
    validate_production_streams(load_yaml("config/production_authority_intake.yaml"))
    validate_bologna_owner_threads(load_yaml("config/bologna_owner_answer_intake.yaml"))
    validate_empty_authority_records()
    validate_qualification_status(load_yaml("state/EMPIRICAL_QUALIFICATION_STATUS.yaml"))
    validate_repo_wiring()
    run_required_validators()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the active authority-evidence intake composition boundary.",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", dest="json_output")
    output_group.add_argument("--summary", action="store_true", dest="summary_output")
    args = parser.parse_args(argv)
    validate()
    if args.json_output:
        print(json.dumps(build_summary(), indent=2, sort_keys=True))
    elif args.summary_output:
        print(format_summary(build_summary()))
    else:
        print("authority evidence intake check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath

    sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
