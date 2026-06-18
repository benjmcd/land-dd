from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MATRIX_PATH = "state/LEVEL_9_10_GATE_MATRIX.md"
MATRIX_PLAN = "plans/2026-06-18-level9-10-readiness-reconciliation.md"
PRODUCTION_AUTHORITY_PACKET_PATH = "state/PRODUCTION_AUTHORITY_PACKET.md"
ALLOWED_STATUSES = {
    "PROVEN_PRIVATE_MVP",
    "PROVEN_REPO_LOCAL",
    "VALIDATE_ONLY",
    "PARTIAL",
    "BLOCKED",
    "MISSING",
}
REQUIRED_BLOCKED_GATES = {
    "L10-OPS-006",
    "L10-SEC-010",
}
REQUIRED_STATUS_BY_GATE = {
    "L9-012": "PARTIAL",
    "L10-OPS-001": "VALIDATE_ONLY",
    "L10-OPS-002": "PARTIAL",
    "L10-OPS-004": "PARTIAL",
    "L10-OPS-006": "BLOCKED",
    "L10-OPS-007": "PARTIAL",
    "L10-OPS-008": "VALIDATE_ONLY",
    "L10-OPS-009": "VALIDATE_ONLY",
    "L10-OPS-010": "VALIDATE_ONLY",
    "L10-SEC-001": "PARTIAL",
    "L10-SEC-002": "PARTIAL",
    "L10-SEC-003": "PARTIAL",
    "L10-SEC-006": "PARTIAL",
    "L10-SEC-007": "VALIDATE_ONLY",
    "L10-SEC-009": "PARTIAL",
    "L10-SEC-010": "BLOCKED",
    "L10-DATA-001": "PARTIAL",
    "L10-DATA-002": "PARTIAL",
    "L10-DATA-003": "PARTIAL",
    "L10-DATA-005": "VALIDATE_ONLY",
    "L10-DATA-006": "VALIDATE_ONLY",
    "L10-PERF-002": "PARTIAL",
    "L10-PERF-003": "PARTIAL",
    "L10-PERF-005": "VALIDATE_ONLY",
    "L10-PERF-006": "VALIDATE_ONLY",
    "L10-PERF-007": "PARTIAL",
    "L10-PERF-008": "PARTIAL",
    "L10-PERF-010": "VALIDATE_ONLY",
    "L10-PROD-001": "PARTIAL",
    "L10-PROD-008": "PARTIAL",
}
REQUIRED_MATRIX_PHRASES = (
    "This matrix is not a completion claim for Level 10.",
    "selected-county private MVP/local operation",
    "DS-017 remains blocked",
    "config/private_mvp_beta_readiness.yaml",
    "config/release_readiness.yaml",
    "Do not start external hosted deployment work until",
    "config/hosted_deployment.yaml",
    "scripts/source_readiness.py --priority Must --json",
)
REQUIRED_PRODUCTION_AUTHORITY_PACKET_PHRASES = (
    "Must-source readiness remains `sources=8 ready=7 blocked=1`; `DS-017` is blocked.",
    "Do not implement a DS-017 connector",
    "No owner",
    "PII, raw vendor record, assessed or market value",
    "lending, appraisal",
    "Alternative unblock: DS-017 is removed or deferred from full-release Must scope",
    "Filled attestation fields are deployment evidence, not production approval",
    "secret values are not evidence and must not appear",
    "named owning",
    "rotation, escalation path",
    "Local release-candidate load results are not reused as hosted SLO proof.",
)
REQUIRED_TASK_VALIDATION_COMMANDS = (
    r"python .\scripts\readiness_matrix_check.py",
    r".\scripts\run_readiness_matrix_check.ps1",
    r"python -m pytest -q .\tests\test_readiness_matrix_artifacts.py",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing_file(path_text: str) -> None:
    require(
        (ROOT / path_text).is_file(),
        f"required readiness artifact missing: {path_text}",
    )


def current_active_plan(task_queue: str) -> str:
    for line in task_queue.splitlines():
        if line.startswith("active_plan: "):
            return line.removeprefix("active_plan: ").strip()
    raise SystemExit("tasks/task_queue.yaml must declare active_plan")


def milestone_gate_ids() -> set[str]:
    milestone = read_text("MILESTONE_MAP.md")
    return set(re.findall(r"\bL(?:9|10)-(?:[A-Z]+-)?\d{3}\b", milestone))


def matrix_rows() -> dict[str, str]:
    rows: dict[str, str] = {}
    for line_number, line in enumerate(read_text(MATRIX_PATH).splitlines(), start=1):
        if not line.startswith("| L"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        require(
            len(cells) >= 4,
            f"{MATRIX_PATH}:{line_number} gate row must have at least four columns",
        )
        gate_id = cells[0].split()[0]
        status = cells[1].strip("`")
        require(gate_id not in rows, f"duplicate readiness gate in matrix: {gate_id}")
        require(
            status in ALLOWED_STATUSES,
            f"{gate_id} has unsupported readiness status: {status}",
        )
        require(bool(cells[2]), f"{gate_id} current evidence cell must not be empty")
        require(bool(cells[3]), f"{gate_id} next action cell must not be empty")
        rows[gate_id] = status
    return rows


def validate_routing() -> None:
    require_existing_file(MATRIX_PLAN)
    plan_readme = read_text("plans/README.md")
    task_queue = read_text("tasks/task_queue.yaml")
    active_plan = current_active_plan(task_queue)
    require_existing_file(active_plan)
    require(
        active_plan in plan_readme or Path(active_plan).name in plan_readme,
        "plans/README.md must route to the task_queue active plan",
    )
    require(
        MATRIX_PLAN in task_queue,
        "tasks/task_queue.yaml must retain the Level 9/10 readiness reconciliation task",
    )
    require("id: R-001" in task_queue, "tasks/task_queue.yaml must contain task R-001")
    if active_plan != MATRIX_PLAN:
        active_plan_text = read_text(active_plan)
        require(
            MATRIX_PATH in active_plan_text,
            "active follow-on plan must cite the Level 9/10 gate matrix",
        )
        require(
            "Level 9/10" in active_plan_text,
            "active follow-on plan must preserve Level 9/10 authority context",
        )
    for command in REQUIRED_TASK_VALIDATION_COMMANDS:
        require(
            command in task_queue,
            f"tasks/task_queue.yaml must include validation command: {command}",
        )


def validate_guarded_statuses(rows: dict[str, str]) -> None:
    for gate_id, required_status in REQUIRED_STATUS_BY_GATE.items():
        require(
            rows.get(gate_id) == required_status,
            f"{gate_id} must remain {required_status} until authority changes",
        )


def validate_production_authority_packet() -> None:
    require_existing_file(PRODUCTION_AUTHORITY_PACKET_PATH)
    packet = read_text(PRODUCTION_AUTHORITY_PACKET_PATH)
    for phrase in REQUIRED_PRODUCTION_AUTHORITY_PACKET_PHRASES:
        require(
            phrase in packet,
            f"production authority packet missing phrase: {phrase}",
        )


def validate_matrix() -> None:
    require_existing_file(MATRIX_PATH)
    validate_production_authority_packet()
    validate_routing()
    matrix = read_text(MATRIX_PATH)
    for phrase in REQUIRED_MATRIX_PHRASES:
        require(phrase in matrix, f"readiness matrix missing phrase: {phrase}")

    expected_gates = milestone_gate_ids()
    rows = matrix_rows()
    missing = sorted(expected_gates - set(rows))
    unexpected = sorted(set(rows) - expected_gates)
    require(not missing, f"readiness matrix missing gates: {missing}")
    require(not unexpected, f"readiness matrix has unexpected gates: {unexpected}")
    validate_guarded_statuses(rows)

    for gate_id in REQUIRED_BLOCKED_GATES:
        require(
            rows.get(gate_id) == "BLOCKED",
            f"{gate_id} must remain BLOCKED until external authority exists",
        )


def main() -> None:
    validate_matrix()


if __name__ == "__main__":
    main()
