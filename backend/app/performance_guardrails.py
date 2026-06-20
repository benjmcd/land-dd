from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.core.config import Settings

EXPECTED_BASELINE_SCHEMA = "performance_baseline_v1"
EXPECTED_BASELINE_SCOPE = "selected_county_private_mvp_local"
EXPECTED_BASELINE_STATUS = "release_candidate_local_only"
EXPECTED_RESULT_SCHEMA = "load_test_result_v1"
EXPECTED_SPATIAL_SCHEMA = "spatial_query_plan_v1"
EXPECTED_SPATIAL_SCOPE = "selected_county_private_mvp_spatial_queries"
EXPECTED_SPATIAL_MODE = "validate_only_static"
EXPECTED_RUNTIME_SCHEMA = "spatial_query_plan_runtime_result_v1"
EXPECTED_QUEUE_HEALTH_PATH = "/operations/queue-health"
EXPECTED_BASELINE_CONFIG = "config/performance_baseline.yaml"
EXPECTED_SPATIAL_CONFIG = "config/spatial_query_plan.yaml"
EXPECTED_LOAD_RUNBOOK = "docs/runbooks/load_testing.md"
EXPECTED_PERFORMANCE_RUNBOOK = "docs/runbooks/performance.md"
EXPECTED_BASELINE_RUNNER = "scripts/load_test_runner.py"
EXPECTED_BASELINE_CHECKER = "scripts/performance_baseline_check.py"
EXPECTED_SPATIAL_CHECKER = "scripts/spatial_query_plan_check.py"
EXPECTED_SPATIAL_RUNTIME_CHECKER = "scripts/spatial_query_plan_runtime_check.py"
EXPECTED_VALIDATION_COMMANDS = (
    "scripts/run_performance_baseline_check.ps1",
    "scripts/run_spatial_query_plan_check.ps1",
    "scripts/run_load_test.ps1 -ValidateOnly",
)
EXPECTED_SCENARIO_IDS = {"sequential", "concurrent"}
EXPECTED_SPATIAL_REVIEW_IDS = {
    "area_parcel_intersections",
    "area_reference_feature_intersections",
    "area_observation_intersections",
}
EXPECTED_SPATIAL_INDEX_NAMES = {
    "areas_geom_gix",
    "area_versions_geom_gix",
    "parcels_geom_gix",
    "reference_features_geom_gix",
    "observations_geom_gix",
}
EXPECTED_RESULT_FIELDS = {
    "schema_version",
    "scenario",
    "base_url",
    "thresholds",
    "total_requests",
    "ok",
    "failures",
    "requests",
    "summary",
}
EXPECTED_BASELINE_FALSE_LIMITS = {
    "hosted_production_claim",
    "ci_live_load_gate",
    "committed_measured_results",
}
EXPECTED_SPATIAL_FALSE_LIMITS = {
    "opens_database_connection_by_default",
    "seeds_runtime_state",
    "generates_artifacts",
    "network_access",
    "hosted_performance_claim",
    "level_10_completion_claim",
}
EXPECTED_BACKPRESSURE_SETTINGS = (
    "ENABLE_QUEUE_BACKPRESSURE",
    "MAX_REPORT_QUEUE_DEPTH",
    "MAX_LIVE_CONNECTOR_QUEUE_DEPTH",
    "MAX_QUEUE_OLDEST_QUEUED_SECONDS",
    "MAX_QUEUE_STALE_RUNNING",
)
SETTINGS_FIELD_BY_ALIAS = {
    "ENABLE_QUEUE_BACKPRESSURE": "enable_queue_backpressure",
    "MAX_REPORT_QUEUE_DEPTH": "max_report_queue_depth",
    "MAX_LIVE_CONNECTOR_QUEUE_DEPTH": "max_live_connector_queue_depth",
    "MAX_QUEUE_OLDEST_QUEUED_SECONDS": "max_queue_oldest_queued_seconds",
    "MAX_QUEUE_STALE_RUNNING": "max_queue_stale_running",
}
REQUIRED_STATIC_FILES = (
    EXPECTED_BASELINE_CHECKER,
    EXPECTED_BASELINE_RUNNER,
    EXPECTED_LOAD_RUNBOOK,
    EXPECTED_PERFORMANCE_RUNBOOK,
    EXPECTED_SPATIAL_CHECKER,
    EXPECTED_SPATIAL_RUNTIME_CHECKER,
    "backend/app/core/config.py",
    "backend/app/operations/backpressure.py",
    "scripts/run_performance_baseline_check.ps1",
    "scripts/run_performance_baseline_check.sh",
    "scripts/run_spatial_query_plan_check.ps1",
    "scripts/run_spatial_query_plan_check.sh",
    "scripts/run_spatial_query_plan_runtime_check.ps1",
    "scripts/run_spatial_query_plan_runtime_check.sh",
)
PERFORMANCE_RUNBOOK_REQUIRED_PHRASES = (
    "Queue backpressure",
    "run_load_test.ps1 -ValidateOnly",
    "opens no database connection by default",
    "not a contractual SLO or hosted production",
)
LOAD_RUNBOOK_REQUIRED_PHRASES = (
    "not a production SLO",
    "load_test_result_v1",
    "without sending any live HTTP",
    "must not send HTTP",
)


class PerformanceGuardrailsError(RuntimeError):
    """Raised when performance guardrail artifacts cannot be trusted for rendering."""


@dataclass(frozen=True)
class PerformanceScenario:
    scenario_id: str
    request_count: int
    workers: int | None
    endpoints: tuple[str, ...]
    thresholds: dict[str, float]


@dataclass(frozen=True)
class SpatialIndex:
    index_name: str
    schema_name: str
    table_name: str
    column_name: str
    method: str


@dataclass(frozen=True)
class SpatialQueryReview:
    review_id: str
    required_indexes: tuple[str, ...]
    runtime_requires_target_index: str
    default_release_readiness: bool


@dataclass(frozen=True)
class BackpressureSetting:
    setting_id: str
    default_value: str
    description: str


@dataclass(frozen=True)
class PerformanceGuardrailsReadiness:
    baseline_schema_version: str
    baseline_scope: str
    baseline_status: str
    result_schema_version: str
    result_required_fields: tuple[str, ...]
    performance_scenarios: tuple[PerformanceScenario, ...]
    baseline_limits: dict[str, bool]
    spatial_schema_version: str
    spatial_scope: str
    spatial_default_mode: str
    spatial_required_indexes: tuple[SpatialIndex, ...]
    spatial_query_reviews: tuple[SpatialQueryReview, ...]
    spatial_runtime_checker: str
    spatial_runtime_output_schema_version: str
    spatial_limits: dict[str, bool]
    backpressure_settings: tuple[BackpressureSetting, ...]
    queue_health_path: str
    validation_commands: tuple[str, ...]

    @property
    def performance_scenario_ids(self) -> tuple[str, ...]:
        return tuple(scenario.scenario_id for scenario in self.performance_scenarios)

    @property
    def spatial_required_index_names(self) -> tuple[str, ...]:
        return tuple(index.index_name for index in self.spatial_required_indexes)

    @property
    def spatial_query_review_ids(self) -> tuple[str, ...]:
        return tuple(review.review_id for review in self.spatial_query_reviews)

    @property
    def backpressure_setting_ids(self) -> tuple[str, ...]:
        return tuple(setting.setting_id for setting in self.backpressure_settings)


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_performance_guardrails(
    repo_root: Path | None = None,
) -> PerformanceGuardrailsReadiness:
    root = repo_root or repo_root_from_app()
    performance_catalog = _read_yaml(root / EXPECTED_BASELINE_CONFIG)
    spatial_catalog = _read_yaml(root / EXPECTED_SPATIAL_CONFIG)
    return parse_performance_guardrails(
        performance_catalog,
        spatial_catalog,
        root=root,
    )


def parse_performance_guardrails(
    performance_catalog: dict[str, Any],
    spatial_catalog: dict[str, Any],
    *,
    root: Path,
) -> PerformanceGuardrailsReadiness:
    for path_text in REQUIRED_STATIC_FILES:
        _require_existing(root, path_text)
    _validate_runbook_text(root)

    baseline = _parse_performance_catalog(performance_catalog, root)
    spatial = _parse_spatial_catalog(spatial_catalog, root)

    return PerformanceGuardrailsReadiness(
        baseline_schema_version=baseline["schema_version"],
        baseline_scope=baseline["scope"],
        baseline_status=baseline["status"],
        result_schema_version=baseline["result_schema_version"],
        result_required_fields=baseline["result_required_fields"],
        performance_scenarios=baseline["scenarios"],
        baseline_limits=baseline["limits"],
        spatial_schema_version=spatial["schema_version"],
        spatial_scope=spatial["scope"],
        spatial_default_mode=spatial["default_mode"],
        spatial_required_indexes=spatial["required_indexes"],
        spatial_query_reviews=spatial["query_reviews"],
        spatial_runtime_checker=spatial["runtime_checker"],
        spatial_runtime_output_schema_version=spatial["runtime_output_schema"],
        spatial_limits=spatial["limits"],
        backpressure_settings=_backpressure_settings(),
        queue_health_path=EXPECTED_QUEUE_HEALTH_PATH,
        validation_commands=EXPECTED_VALIDATION_COMMANDS,
    )


def _parse_performance_catalog(
    payload: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    schema = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_BASELINE_SCHEMA,
        "performance baseline schema",
    )
    scope = _require_exact_text(
        payload.get("scope"),
        EXPECTED_BASELINE_SCOPE,
        "performance baseline scope",
    )
    status = _require_exact_text(
        payload.get("status"),
        EXPECTED_BASELINE_STATUS,
        "performance baseline status",
    )
    runner = _require_exact_text(
        payload.get("runner"),
        EXPECTED_BASELINE_RUNNER,
        "performance runner",
    )
    _require_existing(root, runner)
    _validate_wrapper(
        _require_mapping(payload.get("wrappers"), "performance wrappers missing"),
        windows="scripts/run_load_test.ps1",
        posix="scripts/run_load_test.sh",
        root=root,
        label="performance wrappers",
    )

    evidence = _require_mapping(payload.get("evidence"), "performance evidence missing")
    result_schema = _require_exact_text(
        evidence.get("result_schema_version"),
        EXPECTED_RESULT_SCHEMA,
        "performance result schema",
    )
    result_fields = _require_text_tuple(
        evidence.get("required_fields"),
        "performance result required fields missing",
    )
    missing_fields = sorted(EXPECTED_RESULT_FIELDS - set(result_fields))
    if missing_fields:
        raise PerformanceGuardrailsError(
            f"performance result fields missing: {missing_fields}"
        )

    scenarios = _parse_performance_scenarios(payload.get("scenarios"))
    limits = _false_limit_mapping(
        payload.get("limits"),
        EXPECTED_BASELINE_FALSE_LIMITS,
        "performance baseline",
    )
    return {
        "schema_version": schema,
        "scope": scope,
        "status": status,
        "result_schema_version": result_schema,
        "result_required_fields": result_fields,
        "scenarios": scenarios,
        "limits": limits,
    }


def _parse_performance_scenarios(value: Any) -> tuple[PerformanceScenario, ...]:
    scenarios: list[PerformanceScenario] = []
    for item in _require_list(value, "performance scenarios missing"):
        scenario = _require_mapping(item, "performance scenario must be a mapping")
        scenario_id = _require_text(scenario.get("id"), "performance scenario id missing")
        request_count = _require_int(
            scenario.get("request_count"),
            f"{scenario_id} request_count missing",
        )
        workers_value = scenario.get("workers")
        workers = None if workers_value is None else _require_int(
            workers_value,
            f"{scenario_id} workers invalid",
        )
        endpoints = _request_mix_endpoints(
            scenario.get("request_mix"),
            f"{scenario_id} request mix missing",
        )
        thresholds = _float_mapping(
            scenario.get("thresholds"),
            f"{scenario_id} thresholds missing",
        )
        scenarios.append(
            PerformanceScenario(
                scenario_id=scenario_id,
                request_count=request_count,
                workers=workers,
                endpoints=endpoints,
                thresholds=thresholds,
            )
        )

    scenario_ids = {scenario.scenario_id for scenario in scenarios}
    missing_scenarios = sorted(EXPECTED_SCENARIO_IDS - scenario_ids)
    if missing_scenarios:
        raise PerformanceGuardrailsError(
            f"performance scenarios missing: {missing_scenarios}"
        )
    by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    if by_id["sequential"].thresholds.get("max_request_seconds") != 5.0:
        raise PerformanceGuardrailsError("sequential max_request_seconds drifted")
    if by_id["concurrent"].workers != 8:
        raise PerformanceGuardrailsError("concurrent workers drifted")
    if by_id["concurrent"].thresholds.get("p95_seconds") != 3.0:
        raise PerformanceGuardrailsError("concurrent p95_seconds drifted")
    if by_id["concurrent"].thresholds.get("max_error_rate") != 0.1:
        raise PerformanceGuardrailsError("concurrent max_error_rate drifted")
    return tuple(sorted(scenarios, key=lambda scenario: scenario.scenario_id))


def _parse_spatial_catalog(
    payload: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    schema = _require_exact_text(
        payload.get("schema_version"),
        EXPECTED_SPATIAL_SCHEMA,
        "spatial query plan schema",
    )
    scope = _require_exact_text(
        payload.get("scope"),
        EXPECTED_SPATIAL_SCOPE,
        "spatial query plan scope",
    )
    default_mode = _require_exact_text(
        payload.get("default_mode"),
        EXPECTED_SPATIAL_MODE,
        "spatial query plan default mode",
    )
    ddl_authority = _require_text(payload.get("ddl_authority"), "spatial ddl missing")
    _require_existing(root, ddl_authority)
    _validate_wrapper(
        _require_mapping(payload.get("wrappers"), "spatial wrappers missing"),
        windows="scripts/run_spatial_query_plan_check.ps1",
        posix="scripts/run_spatial_query_plan_check.sh",
        root=root,
        label="spatial wrappers",
    )

    runtime = _require_mapping(payload.get("runtime_review"), "spatial runtime missing")
    runtime_checker = _require_exact_text(
        runtime.get("checker"),
        EXPECTED_SPATIAL_RUNTIME_CHECKER,
        "spatial runtime checker",
    )
    _require_existing(root, runtime_checker)
    _validate_wrapper(
        _require_mapping(runtime.get("wrappers"), "spatial runtime wrappers missing"),
        windows="scripts/run_spatial_query_plan_runtime_check.ps1",
        posix="scripts/run_spatial_query_plan_runtime_check.sh",
        root=root,
        label="spatial runtime wrappers",
    )
    runtime_output_schema = _require_exact_text(
        runtime.get("output_schema_version"),
        EXPECTED_RUNTIME_SCHEMA,
        "spatial runtime output schema",
    )

    required_indexes = _parse_spatial_indexes(payload.get("required_indexes"))
    query_reviews = _parse_spatial_query_reviews(payload.get("query_plan_reviews"))
    limits = _false_limit_mapping(
        payload.get("limits"),
        EXPECTED_SPATIAL_FALSE_LIMITS,
        "spatial query plan",
    )
    return {
        "schema_version": schema,
        "scope": scope,
        "default_mode": default_mode,
        "required_indexes": required_indexes,
        "query_reviews": query_reviews,
        "runtime_checker": runtime_checker,
        "runtime_output_schema": runtime_output_schema,
        "limits": limits,
    }


def _parse_spatial_indexes(value: Any) -> tuple[SpatialIndex, ...]:
    indexes: list[SpatialIndex] = []
    for item in _require_list(value, "spatial indexes missing"):
        index = _require_mapping(item, "spatial index must be a mapping")
        indexes.append(
            SpatialIndex(
                index_name=_require_text(index.get("name"), "spatial index name missing"),
                schema_name=_require_text(index.get("schema"), "spatial schema missing"),
                table_name=_require_text(index.get("table"), "spatial table missing"),
                column_name=_require_text(index.get("column"), "spatial column missing"),
                method=_require_exact_text(index.get("method"), "gist", "spatial method"),
            )
        )
    index_names = {index.index_name for index in indexes}
    missing_indexes = sorted(EXPECTED_SPATIAL_INDEX_NAMES - index_names)
    if missing_indexes:
        raise PerformanceGuardrailsError(
            f"spatial indexes missing required ids: {missing_indexes}"
        )
    return tuple(sorted(indexes, key=lambda index: index.index_name))


def _parse_spatial_query_reviews(value: Any) -> tuple[SpatialQueryReview, ...]:
    reviews: list[SpatialQueryReview] = []
    for item in _require_list(value, "spatial query reviews missing"):
        review = _require_mapping(item, "spatial query review must be a mapping")
        review_id = _require_text(review.get("id"), "spatial query review id missing")
        mode = _require_exact_text(
            review.get("review_mode"),
            "manual_read_only_explain",
            f"{review_id} review mode",
        )
        if mode != "manual_read_only_explain":
            raise PerformanceGuardrailsError(f"{review_id} review mode invalid")
        default_release_readiness = _require_bool(
            review.get("default_release_readiness"),
            f"{review_id} default release readiness missing",
        )
        if default_release_readiness is not False:
            raise PerformanceGuardrailsError(
                f"{review_id} must not join default release readiness"
            )
        required_indexes = _require_text_tuple(
            review.get("required_indexes"),
            f"{review_id} required indexes missing",
        )
        target_index = _require_text(
            review.get("runtime_requires_target_index"),
            f"{review_id} runtime target index missing",
        )
        if target_index not in required_indexes:
            raise PerformanceGuardrailsError(f"{review_id} target index not required")
        statement = _require_text(review.get("statement"), f"{review_id} SQL missing")
        if "EXPLAIN" not in statement or "ST_Intersects" not in statement:
            raise PerformanceGuardrailsError(f"{review_id} SQL review statement invalid")
        reviews.append(
            SpatialQueryReview(
                review_id=review_id,
                required_indexes=required_indexes,
                runtime_requires_target_index=target_index,
                default_release_readiness=default_release_readiness,
            )
        )
    review_ids = {review.review_id for review in reviews}
    missing_reviews = sorted(EXPECTED_SPATIAL_REVIEW_IDS - review_ids)
    if missing_reviews:
        raise PerformanceGuardrailsError(
            f"spatial query review missing: {missing_reviews}"
        )
    return tuple(sorted(reviews, key=lambda review: review.review_id))


def _backpressure_settings() -> tuple[BackpressureSetting, ...]:
    settings: list[BackpressureSetting] = []
    for alias in EXPECTED_BACKPRESSURE_SETTINGS:
        field_name = SETTINGS_FIELD_BY_ALIAS[alias]
        field = Settings.model_fields.get(field_name)
        if field is None or field.alias != alias:
            raise PerformanceGuardrailsError(f"backpressure setting missing: {alias}")
        settings.append(
            BackpressureSetting(
                setting_id=alias,
                default_value=str(field.default),
                description=str(field.description or ""),
            )
        )
    return tuple(settings)


def _validate_runbook_text(root: Path) -> None:
    performance = _read_text(root, EXPECTED_PERFORMANCE_RUNBOOK)
    for phrase in PERFORMANCE_RUNBOOK_REQUIRED_PHRASES:
        if phrase not in performance:
            raise PerformanceGuardrailsError(
                f"performance runbook missing phrase: {phrase}"
            )
    load_testing = _read_text(root, EXPECTED_LOAD_RUNBOOK)
    for phrase in LOAD_RUNBOOK_REQUIRED_PHRASES:
        if phrase not in load_testing:
            raise PerformanceGuardrailsError(
                f"load testing runbook missing phrase: {phrase}"
            )


def _read_yaml(path: Path) -> dict[str, Any]:
    label = _catalog_label(path)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PerformanceGuardrailsError(f"cannot read {label}") from exc
    return _require_mapping(payload, f"{label} must be a mapping")


def _read_text(root: Path, path_text: str) -> str:
    path = _resolved_repo_path(root, path_text)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PerformanceGuardrailsError(f"cannot read {path_text}") from exc


def _validate_wrapper(
    payload: dict[str, Any],
    *,
    windows: str,
    posix: str,
    root: Path,
    label: str,
) -> None:
    windows_path = _require_exact_text(payload.get("windows"), windows, f"{label} windows")
    posix_path = _require_exact_text(payload.get("posix"), posix, f"{label} posix")
    _require_existing(root, windows_path)
    _require_existing(root, posix_path)


def _require_existing(root: Path, path_text: str) -> None:
    path = _resolved_repo_path(root, path_text)
    if not path.exists():
        raise PerformanceGuardrailsError(
            f"referenced performance guardrail artifact missing: {path_text}"
        )


def _resolved_repo_path(root: Path, path_text: str) -> Path:
    if not path_text:
        raise PerformanceGuardrailsError("empty path reference")
    candidate = Path(_normalize_path(path_text))
    if candidate.is_absolute():
        raise PerformanceGuardrailsError(f"path must be repo-relative: {path_text}")
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PerformanceGuardrailsError(f"path escapes repo root: {path_text}") from exc
    return resolved


def _request_mix_endpoints(value: Any, message: str) -> tuple[str, ...]:
    endpoints: list[str] = []
    for item in _require_list(value, message):
        request = _require_mapping(item, "request mix item must be a mapping")
        method = _require_text(request.get("method"), "request method missing")
        path = _require_text(request.get("path"), "request path missing")
        if method not in {"GET", "POST"}:
            raise PerformanceGuardrailsError(f"unexpected request method: {method}")
        if not path.startswith("/"):
            raise PerformanceGuardrailsError(f"request path invalid: {path}")
        endpoints.append(path)
    return tuple(dict.fromkeys(endpoints))


def _false_limit_mapping(
    value: Any,
    expected_false_keys: set[str],
    label: str,
) -> dict[str, bool]:
    raw = _require_mapping(value, f"{label} limits missing")
    limits: dict[str, bool] = {}
    for key in expected_false_keys:
        if raw.get(key) is not False:
            message = f"{label} limit changed: {key}"
            if key in {"hosted_production_claim", "hosted_performance_claim"}:
                message = f"{label} hosted production/performance claim must remain false"
            raise PerformanceGuardrailsError(message)
        limits[key] = False
    return {key: limits[key] for key in sorted(limits)}


def _require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PerformanceGuardrailsError(message)
    return value


def _require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise PerformanceGuardrailsError(message)
    return value


def _require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PerformanceGuardrailsError(message)
    return value.strip()


def _require_exact_text(value: Any, expected: str, label: str) -> str:
    text = _require_text(value, f"{label} missing")
    if text != expected:
        raise PerformanceGuardrailsError(f"{label} must be {expected}")
    return text


def _require_text_tuple(value: Any, message: str) -> tuple[str, ...]:
    values = _require_list(value, message)
    text_values = tuple(_require_text(item, message) for item in values)
    if not text_values:
        raise PerformanceGuardrailsError(message)
    return text_values


def _require_int(value: Any, message: str) -> int:
    if not isinstance(value, int):
        raise PerformanceGuardrailsError(message)
    return value


def _require_bool(value: Any, message: str) -> bool:
    if not isinstance(value, bool):
        raise PerformanceGuardrailsError(message)
    return value


def _float_mapping(value: Any, message: str) -> dict[str, float]:
    raw = _require_mapping(value, message)
    result: dict[str, float] = {}
    for key, val in raw.items():
        if not isinstance(key, str) or not isinstance(val, (float, int)):
            raise PerformanceGuardrailsError(message)
        result[key] = float(val)
    return result


def _normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def _catalog_label(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return path.name


__all__ = [
    "BackpressureSetting",
    "PerformanceGuardrailsError",
    "PerformanceGuardrailsReadiness",
    "PerformanceScenario",
    "SpatialIndex",
    "SpatialQueryReview",
    "load_performance_guardrails",
    "parse_performance_guardrails",
]
