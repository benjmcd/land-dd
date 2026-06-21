from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ProjectReadinessError(RuntimeError):
    """Raised when project readiness control-plane artifacts cannot be parsed."""


@dataclass(frozen=True)
class ProjectCheckpoint:
    title: str
    active_plan: str
    completed_task_ids: tuple[str, ...]
    blocked_terms: tuple[str, ...]
    boundary_text: str


@dataclass(frozen=True)
class GateRow:
    gate_id: str
    title: str
    status: str
    evidence: str
    next_action: str


@dataclass(frozen=True)
class GateMatrix:
    gates: tuple[GateRow, ...]
    status_counts: dict[str, int]
    blocked_gate_ids: tuple[str, ...]
    partial_gate_ids: tuple[str, ...]
    validate_only_gate_ids: tuple[str, ...]


@dataclass(frozen=True)
class TaskQueueTask:
    task_id: str
    title: str
    status: str
    spec: str | None


@dataclass(frozen=True)
class TaskQueueReadiness:
    active_plan: str
    routing_note: str
    completed_tasks: tuple[TaskQueueTask, ...]
    active_tasks: tuple[TaskQueueTask, ...]


@dataclass(frozen=True)
class ValidationReadiness:
    heading: str
    scope: str
    commands: tuple[str, ...]
    results: tuple[str, ...]
    residual_risk: str


@dataclass(frozen=True)
class ProjectReadiness:
    checkpoint: ProjectCheckpoint
    gate_matrix: GateMatrix
    task_queue: TaskQueueReadiness
    validation: ValidationReadiness


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_project_readiness(repo_root: Path | None = None) -> ProjectReadiness:
    root = repo_root or repo_root_from_app()
    return ProjectReadiness(
        checkpoint=parse_project_state((root / "state" / "PROJECT_STATE.md").read_text()),
        gate_matrix=parse_gate_matrix((root / "state" / "LEVEL_9_10_GATE_MATRIX.md").read_text()),
        task_queue=parse_task_queue((root / "tasks" / "task_queue.yaml").read_text()),
        validation=parse_validation_log((root / "state" / "VALIDATION_LOG.md").read_text()),
    )


def parse_project_state(text: str) -> ProjectCheckpoint:
    title, section = _first_current_checkpoint(text)
    active_plan = _extract_labeled_code(section, "Current implementation plan")
    task_state = _extract_labeled_paragraph(section, "Current task state")
    boundary_text = _extract_labeled_paragraph(section, "Known boundaries to preserve")
    completed_ids = tuple(sorted(set(_TASK_ID_RE.findall(task_state))))
    blocked_terms = tuple(sorted(set(_blocked_terms(section))))
    if not completed_ids:
        raise ProjectReadinessError("current task state lists no completed task ids")
    return ProjectCheckpoint(
        title=title,
        active_plan=active_plan,
        completed_task_ids=completed_ids,
        blocked_terms=blocked_terms,
        boundary_text=boundary_text,
    )


def parse_gate_matrix(text: str) -> GateMatrix:
    gates: list[GateRow] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        columns = [_normalize_cell(cell) for cell in line.strip("|").split("|")]
        if len(columns) < 4 or columns[0] in {"Gate", "---"}:
            continue
        if not columns[0].startswith("L"):
            continue
        gate_id, title = _split_gate_title(columns[0])
        gates.append(
            GateRow(
                gate_id=gate_id,
                title=title,
                status=_clean_inline_code(columns[1]),
                evidence=columns[2],
                next_action=columns[3],
            )
        )
    if not gates:
        raise ProjectReadinessError("no Level 9/10 gate rows found")
    counts = Counter(gate.status for gate in gates)
    return GateMatrix(
        gates=tuple(gates),
        status_counts=dict(counts),
        blocked_gate_ids=tuple(gate.gate_id for gate in gates if gate.status == "BLOCKED"),
        partial_gate_ids=tuple(gate.gate_id for gate in gates if gate.status == "PARTIAL"),
        validate_only_gate_ids=tuple(
            gate.gate_id for gate in gates if gate.status == "VALIDATE_ONLY"
        ),
    )


def parse_task_queue(text: str) -> TaskQueueReadiness:
    payload = yaml.safe_load(text)
    queue = _require_mapping(payload, "task queue must be a mapping")
    active_plan = _require_text(queue.get("active_plan"), "task queue active_plan missing")
    routing_note = _require_text(queue.get("routing_note"), "task queue routing_note missing")
    tasks = tuple(_task_from_mapping(raw) for raw in _require_list(queue.get("tasks")))
    completed = tuple(task for task in tasks if task.status == "done")
    active = tuple(task for task in tasks if task.status in {"active", "in_progress", "todo"})
    if not completed:
        raise ProjectReadinessError("task queue has no completed tasks")
    return TaskQueueReadiness(
        active_plan=active_plan,
        routing_note=routing_note,
        completed_tasks=completed,
        active_tasks=active,
    )


def parse_validation_log(text: str) -> ValidationReadiness:
    heading, section = _first_h2_section(text)
    commands = _first_powershell_block(section)
    results = _bullets_under_heading(section, "Results")
    scope = _paragraph_after_label(section, "Scope")
    residual_risk = _paragraph_after_label(section, "Residual risk")
    if not commands:
        raise ProjectReadinessError("latest validation section has no command block")
    return ValidationReadiness(
        heading=heading,
        scope=scope,
        commands=commands,
        results=results,
        residual_risk=residual_risk,
    )


_TASK_ID_RE = re.compile(r"`([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+)`")


def _first_current_checkpoint(text: str) -> tuple[str, str]:
    heading, section = _first_h2_section(text)
    if "current checkpoint" not in heading.lower():
        raise ProjectReadinessError("first state section is not the current checkpoint")
    return heading, section


def _first_h2_section(text: str) -> tuple[str, str]:
    match = re.search(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    if match is None:
        raise ProjectReadinessError("document has no level-two section")
    next_match = re.search(r"^##\s+", text[match.end() :], flags=re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(text)
    return match.group(1).strip(), text[match.end() : end]


def _extract_labeled_code(section: str, label: str) -> str:
    paragraph = _extract_labeled_paragraph(section, label)
    match = re.search(r"`([^`]+)`", paragraph)
    if match is None:
        raise ProjectReadinessError(f"{label} does not contain inline code")
    return match.group(1)


def _extract_labeled_paragraph(section: str, label: str) -> str:
    pattern = re.compile(rf"- \*\*{re.escape(label)}\*\*:\s*(.*?)(?=\n- \*\*|\Z)", re.DOTALL)
    match = pattern.search(section)
    if match is None:
        raise ProjectReadinessError(f"missing project state field: {label}")
    return _collapse_whitespace(match.group(1))


def _blocked_terms(section: str) -> list[str]:
    terms: list[str] = []
    for term in ("BSA-001", "DS-017", "Level 10"):
        if term in section:
            terms.append(term)
    return terms


def _normalize_cell(value: str) -> str:
    return _collapse_whitespace(value.replace("\\|", "|"))


def _split_gate_title(value: str) -> tuple[str, str]:
    parts = value.split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _clean_inline_code(value: str) -> str:
    return value.replace("`", "").strip()


def _task_from_mapping(value: Any) -> TaskQueueTask:
    task = _require_mapping(value, "task must be a mapping")
    return TaskQueueTask(
        task_id=_require_text(task.get("id"), "task id missing"),
        title=_require_text(task.get("title"), "task title missing"),
        status=_require_text(task.get("status"), "task status missing"),
        spec=task.get("spec") if isinstance(task.get("spec"), str) else None,
    )


def _first_powershell_block(section: str) -> tuple[str, ...]:
    match = re.search(r"```powershell\s*(.*?)```", section, flags=re.DOTALL)
    if match is None:
        return ()
    return tuple(
        line.strip()
        for line in match.group(1).splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def _bullets_under_heading(section: str, heading: str) -> tuple[str, ...]:
    heading_pattern = re.compile(rf"\*\*{re.escape(heading)}:\*\*\s*(.*?)(?=\n\*\*|\Z)", re.DOTALL)
    match = heading_pattern.search(section)
    if match is None:
        return ()
    return tuple(
        _collapse_whitespace(line[2:])
        for line in match.group(1).splitlines()
        if line.startswith("- ")
    )


def _paragraph_after_label(section: str, label: str) -> str:
    match = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.*?)(?=\n\*\*|\Z)", section, re.DOTALL)
    if match is None:
        return ""
    return _collapse_whitespace(match.group(1))


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProjectReadinessError(message)
    return value


def _require_list(value: Any) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ProjectReadinessError("expected non-empty list")
    return value


def _require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectReadinessError(message)
    return value.strip()
