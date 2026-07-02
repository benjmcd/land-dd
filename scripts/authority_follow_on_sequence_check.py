from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/authority_follow_on_sequence.yaml"
PACKET_PATH = "state/PRODUCTION_AUTHORITY_PACKET.md"
PRODUCTION_INTAKE_PATH = "config/production_authority_intake.yaml"

EXPECTED_LIMITS = {
    "validate_only_sequence": True,
    "records_authority": False,
    "records_owner_answer": False,
    "approves_sources": False,
    "changes_source_rights": False,
    "captures_fixtures": False,
    "seeds_database": False,
    "proves_report": False,
    "changes_schema_api_auth_ui_runtime": False,
    "provisions_hosted_runtime": False,
    "unfreezes_qualification": False,
    "unblocks_p0": False,
    "claims_level_10": False,
}

EXPECTED_BLOCKED_BOUNDARIES = {
    "ds017_approval",
    "bologna_owner_decisions",
    "bologna_source_rights",
    "bologna_recorded_corpus",
    "bologna_db_report_proof",
    "hosted_readiness",
    "level_10_authority",
    "qualification_pass",
    "owner_decision_unfreeze",
    "p0_unblock",
}

EXPECTED_REQUIRED_BEFORE_FOLLOW_ON = {
    "cited_authority_references",
    "matching_source_catalog_updated",
    "field_level_decision_validated",
}

EXPECTED_PACKET_ONLY_LANES = {"production_workload_retention_follow_on"}

EXPECTED_LANES = {
    "ds017_source_entitlement_follow_on",
    "hosted_platform_follow_on",
    "secrets_manager_follow_on",
    "identity_rbac_follow_on",
    "image_publication_follow_on",
    "billing_cost_follow_on",
    "hosted_observability_follow_on",
    "production_workload_retention_follow_on",
    "bologna_recorded_source_pilot_follow_on",
}

REQUIRED_FILES = (
    CONFIG_PATH,
    PACKET_PATH,
    PRODUCTION_INTAKE_PATH,
    "docs/runbooks/production_authority_intake.md",
    "scripts/run_authority_follow_on_sequence_check.ps1",
    "scripts/run_authority_follow_on_sequence_check.sh",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return value


def require_non_empty_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
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


def require_existing(path_text: str) -> None:
    normalized = normalize_path(path_text)
    require(repo_path(normalized).exists(), f"authority follow-on artifact missing: {normalized}")


def read_text(path_text: str) -> str:
    return repo_path(path_text).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must be a mapping")


def list_set(value: Any, message: str) -> set[str]:
    return {str(item) for item in require_list(value, message)}


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def parse_follow_on_map(packet: str) -> dict[str, str]:
    marker = "## Repo-Local Follow-On Map"
    require(marker in packet, "production authority packet missing follow-on map")
    section = packet.split(marker, 1)[1].split("\n## ", 1)[0]
    rows: dict[str, str] = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 2:
            continue
        authority_received, follow_on = cells
        if authority_received in {"Authority received", "---"} or follow_on == "---":
            continue
        require(authority_received not in rows, f"duplicate follow-on map row: {authority_received}")
        rows[authority_received] = follow_on
    require(bool(rows), "production authority follow-on map has no rows")
    return rows


def production_streams() -> dict[str, dict[str, Any]]:
    payload = load_yaml(PRODUCTION_INTAKE_PATH)
    streams: dict[str, dict[str, Any]] = {}
    for raw_stream in require_non_empty_list(
        payload.get("authority_streams"),
        "production authority streams missing",
    ):
        stream = require_mapping(raw_stream, "production authority stream must be a mapping")
        stream_id = require_text(stream.get("id"), "production authority stream id missing")
        require(stream_id not in streams, f"duplicate production authority stream: {stream_id}")
        require(stream.get("status") == "blocked", f"{stream_id} must remain blocked")
        require(stream.get("evidence_status") == "missing", f"{stream_id} evidence changed")
        require(stream.get("authority_references") == [], f"{stream_id} authority changed")
        require(
            stream.get("decision_updates_allowed") is False,
            f"{stream_id} decision updates unexpectedly allowed",
        )
        streams[stream_id] = stream
    return streams


def validate_policy(payload: dict[str, Any]) -> None:
    policy = require_mapping(payload.get("sequence_policy"), "sequence policy missing")
    require(
        policy.get("authority_source") == PRODUCTION_INTAKE_PATH,
        "sequence authority source drifted",
    )
    require(
        policy.get("packet_follow_on_map") == f"{PACKET_PATH}#repo-local-follow-on-map",
        "follow-on map source drifted",
    )
    require_text(policy.get("unlock_rule"), "sequence unlock rule missing")
    require(
        list_set(
            policy.get("required_before_any_follow_on"),
            "global follow-on requirements missing",
        )
        == EXPECTED_REQUIRED_BEFORE_FOLLOW_ON,
        "global follow-on requirements drifted",
    )
    require(
        list_set(policy.get("blocked_boundaries"), "blocked boundaries missing")
        == EXPECTED_BLOCKED_BOUNDARIES,
        "blocked boundary set drifted",
    )


def validate_lane(
    lane: dict[str, Any],
    packet_rows: dict[str, str],
    stream_ids: set[str],
) -> set[str]:
    lane_id = require_text(lane.get("id"), "follow-on lane id missing")
    require(lane_id in EXPECTED_LANES, f"unexpected follow-on lane: {lane_id}")
    require(
        lane.get("status") == "blocked_waiting_for_authority",
        f"{lane_id} must remain blocked waiting for authority",
    )
    authority_received = require_text(
        lane.get("authority_received"),
        f"{lane_id} authority label missing",
    )
    repo_follow_on = require_text(
        lane.get("repo_local_follow_on"),
        f"{lane_id} follow-on text missing",
    )
    require(
        packet_rows.get(authority_received) == repo_follow_on,
        f"{lane_id} follow-on text drifted from packet",
    )
    require(
        list_set(lane.get("required_before_unblock"), f"{lane_id} requirements missing")
        == EXPECTED_REQUIRED_BEFORE_FOLLOW_ON,
        f"{lane_id} unblock requirements drifted",
    )
    require(
        lane.get("allowed_after_authority_only") is True,
        f"{lane_id} must be authority-only",
    )
    for key in ("first_allowed_repo_local_actions", "forbidden_until_authority", "source_catalogs"):
        require_non_empty_list(lane.get(key), f"{lane_id} {key} missing")
    for path_text in require_non_empty_list(lane.get("source_catalogs"), f"{lane_id} catalogs missing"):
        require_existing(require_text(path_text, f"{lane_id} catalog path missing"))

    lane_streams = list_set(lane.get("authority_streams"), f"{lane_id} streams missing")
    if lane_id in EXPECTED_PACKET_ONLY_LANES:
        require(lane_streams == set(), f"{lane_id} must stay packet-only")
        require(
            lane.get("packet_only_authority_area") is True,
            f"{lane_id} must declare packet-only authority area",
        )
    else:
        require(bool(lane_streams), f"{lane_id} must reference a production authority stream")
        require(
            lane.get("packet_only_authority_area") in (None, False),
            f"{lane_id} must not be packet-only",
        )
    require(lane_streams <= stream_ids, f"{lane_id} references unknown authority streams")
    return lane_streams


def validate_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    require(payload.get("schema_version") == "authority_follow_on_sequence_v1", "unexpected schema")
    require(
        payload.get("status") == "blocked_waiting_for_external_authority",
        "follow-on sequence must stay blocked",
    )
    require(payload.get("source_packet") == PACKET_PATH, "source packet mismatch")
    require(payload.get("source_intake") == PRODUCTION_INTAKE_PATH, "source intake mismatch")
    require(
        payload.get("operator_runbook") == "docs/runbooks/production_authority_intake.md",
        "operator runbook mismatch",
    )
    require(
        payload.get("validation") == "scripts/run_authority_follow_on_sequence_check.ps1",
        "validation wrapper mismatch",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "authority follow-on limits changed",
    )
    validate_policy(payload)

    packet_rows = parse_follow_on_map(read_text(PACKET_PATH))
    streams = production_streams()
    seen_lanes: set[str] = set()
    covered_streams: set[str] = set()
    for raw_lane in require_non_empty_list(payload.get("follow_on_lanes"), "follow-on lanes missing"):
        lane = require_mapping(raw_lane, "follow-on lane must be a mapping")
        lane_id = require_text(lane.get("id"), "follow-on lane id missing")
        require(lane_id not in seen_lanes, f"duplicate follow-on lane: {lane_id}")
        seen_lanes.add(lane_id)
        covered_streams |= validate_lane(lane, packet_rows, set(streams))
    require(seen_lanes == EXPECTED_LANES, "follow-on lane set drifted")
    require(covered_streams == set(streams), "production authority stream coverage drifted")
    require(
        set(packet_rows)
        == {
            require_text(
                require_mapping(lane, "follow-on lane must be a mapping").get("authority_received"),
                "lane authority label missing",
            )
            for lane in require_non_empty_list(payload.get("follow_on_lanes"), "lanes missing")
        },
        "packet follow-on map row set drifted",
    )
    return payload


def validate_repo_wiring() -> None:
    expected_fragments = (
        ("MANIFEST.md", "config/authority_follow_on_sequence.yaml"),
        ("MANIFEST.md", "scripts/authority_follow_on_sequence_check.py"),
        ("scripts/verify.ps1", "authority_follow_on_sequence_check.py"),
        ("scripts/verify.sh", "authority_follow_on_sequence_check.py"),
        ("scripts/authority_evidence_intake_check.py", "authority_follow_on_sequence_check.py"),
        ("plans/2026-07-02-authority-evidence-intake.md", "authority_follow_on_sequence_check.py"),
        ("tasks/task_queue.yaml", "authority_follow_on_sequence_check.py"),
        ("state/PROJECT_STATE.md", "authority_follow_on_sequence_check.py"),
    )
    for path_text, fragment in expected_fragments:
        require(fragment in read_text(path_text), f"{path_text} missing expected fragment: {fragment}")


def main() -> int:
    validate_required_files()
    validate_catalog(load_yaml(CONFIG_PATH))
    validate_repo_wiring()
    print("authority follow-on sequence check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
