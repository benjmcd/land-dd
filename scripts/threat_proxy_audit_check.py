from __future__ import annotations


from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "config/threat_proxy_audit.yaml",
    "docs/runbooks/threat_proxy_audit.md",
    "docs/SECURITY.md",
    "docs/PRODUCT_SPEC.md",
    "docs/source-reviews/ds-022.md",
    "config/access_control.yaml",
    "config/private_mvp_beta_readiness.yaml",
    "docs/runbooks/access_control.md",
    "docs/runbooks/mvp_operator.md",
    "docs/runbooks/security_scan.md",
    "docs/runbooks/incident_response.md",
    "backend/app/connectors/census_tiger.py",
    "backend/app/source_registry/usage_rights.py",
    "backend/app/core/error_safety.py",
    "backend/app/api/reports.py",
    "backend/app/api/connectors.py",
    "backend/app/api/ui.py",
    "backend/app/api/ui_shared.py",
    "backend/app/api/ui_live_connector_jobs.py",
    "backend/app/api/ui_review.py",
    "backend/app/operations/recovery_preview.py",
    "backend/tests/connectors/test_census_tiger_connector.py",
    "backend/tests/api/test_census_tiger_connector_api.py",
    "backend/tests/reports/test_report_overclaim.py",
    "backend/tests/api/test_report_export.py",
    "backend/tests/private_mvp/test_mvp_regression.py",
    "backend/tests/test_ui_runtime_smoke_script.py",
    "backend/tests/source_registry/test_usage_rights.py",
    "backend/tests/api/test_api_key_auth.py",
    "backend/tests/api/test_reviewer_auth.py",
    "backend/tests/api/test_report_auth.py",
    "backend/tests/api/test_report_run_list.py",
    "backend/tests/api/test_ui_shared.py",
    "backend/tests/api/test_ui_routes.py",
    "backend/tests/api/test_usgs_tnm_connector_api.py",
    "backend/tests/api/test_ui_live_connector_jobs.py",
    "backend/tests/api/test_connector_review_queue_api.py",
    "backend/tests/api/test_ui_review_routes.py",
    "backend/tests/api/test_operations.py",
    "backend/tests/api/test_ui_operations_routes.py",
    "scripts/ui_runtime_smoke.py",
    "scripts/access_control_check.py",
    "scripts/source_readiness.py",
)

REQUIRED_RISKS = {
    "protected_class_demographic_inputs",
    "residential_steering_proxy",
    "ranking_recommendation_suitability",
    "legal_financial_overclaim",
    "source_rights_sensitive_exposure",
    "auth_access_control",
    "production_error_leakage",
}
REQUIRED_BLOCKERS = {
    "external_security_review",
    "legal_fair_housing_review",
    "hosted_idp_rbac",
    "production_error_log_review",
    "ds017_vendor_entitlement",
    "hosted_monitoring_alerting",
}
EXPECTED_LIMITS = {
    "validate_only_catalog": True,
    "adds_product_semantics": False,
    "uses_demographic_inputs": False,
    "creates_recommendations": False,
    "claims_security_review_complete": False,
    "claims_legal_review_complete": False,
    "claims_hosted_production_ready": False,
}
REQUIRED_RESIDUAL_REVIEW_ITEMS = {
    "bandit_medium_findings",
}


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


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"referenced threat/proxy artifact missing: {normalized}")


def require_phrases(text: str, phrases: tuple[str, ...], label: str) -> None:
    for phrase in phrases:
        require(phrase in text, f"{label} missing phrase: {phrase}")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_catalog() -> None:
    payload = require_mapping(
        yaml.safe_load(read_text("config/threat_proxy_audit.yaml")),
        "threat/proxy catalog must be a mapping",
    )
    require(
        payload.get("schema_version") == "threat_proxy_audit_v1",
        "unexpected threat/proxy schema",
    )
    require(
        payload.get("operator_runbook") == "docs/runbooks/threat_proxy_audit.md",
        "threat/proxy runbook mismatch",
    )
    require(
        payload.get("status") == "repo_local_validate_only",
        "threat/proxy catalog must remain validate-only",
    )
    require(
        payload.get("validation") == "scripts/run_threat_proxy_audit_check.ps1",
        "threat/proxy validation wrapper mismatch",
    )

    risks = require_non_empty_list(payload.get("risk_register"), "risk register missing")
    risk_ids: set[str] = set()
    for risk_raw in risks:
        risk = require_mapping(risk_raw, "each risk must be a mapping")
        risk_id = str(risk.get("id", ""))
        require(bool(risk_id), "risk id missing")
        require(risk_id not in risk_ids, f"duplicate risk id: {risk_id}")
        risk_ids.add(risk_id)
        require(str(risk.get("status", "")).endswith("repo_local"), f"{risk_id} status mismatch")
        controls = require_non_empty_list(risk.get("controls"), f"{risk_id} controls missing")
        for control_path in controls:
            require(isinstance(control_path, str), f"{risk_id} controls must be strings")
            require_existing(control_path)
    require(REQUIRED_RISKS == risk_ids, f"threat/proxy risk set mismatch: {sorted(risk_ids)}")

    blockers = require_non_empty_list(payload.get("external_blockers"), "external blockers missing")
    blocker_ids: set[str] = set()
    for blocker_raw in blockers:
        blocker = require_mapping(blocker_raw, "each blocker must be a mapping")
        blocker_id = str(blocker.get("id", ""))
        require(bool(blocker_id), "blocker id missing")
        require(blocker_id not in blocker_ids, f"duplicate blocker id: {blocker_id}")
        blocker_ids.add(blocker_id)
        require(blocker.get("status") == "blocked", f"{blocker_id} must remain blocked")
        authority = blocker.get("authority")
        if not isinstance(authority, str) or not authority:
            raise SystemExit(f"{blocker_id} authority missing")
        require_existing(authority)
    require(
        REQUIRED_BLOCKERS == blocker_ids,
        f"external blocker set mismatch: {sorted(blocker_ids)}",
    )

    residual_items = require_non_empty_list(
        payload.get("residual_review_items"),
        "residual review items missing",
    )
    residual_ids: set[str] = set()
    for item_raw in residual_items:
        item = require_mapping(item_raw, "each residual review item must be a mapping")
        item_id = str(item.get("id", ""))
        require(bool(item_id), "residual review item id missing")
        require(item_id not in residual_ids, f"duplicate residual review item id: {item_id}")
        residual_ids.add(item_id)
        require(
            item.get("status") == "review_debt_not_release_blocking",
            f"{item_id} status mismatch",
        )
        authority = item.get("authority")
        if not isinstance(authority, str) or not authority:
            raise SystemExit(f"{item_id} authority missing")
        require_existing(authority)
    require(
        REQUIRED_RESIDUAL_REVIEW_ITEMS == residual_ids,
        f"residual review item set mismatch: {sorted(residual_ids)}",
    )

    limits = require_mapping(payload.get("limits"), "limits missing")
    require(limits == EXPECTED_LIMITS, "threat/proxy limits changed without validator update")


def validate_policy_and_product_boundary() -> None:
    security = read_text("docs/SECURITY.md")
    product = read_text("docs/PRODUCT_SPEC.md")
    ds022 = read_text("docs/source-reviews/ds-022.md")
    private_mvp = read_text("config/private_mvp_beta_readiness.yaml")

    require_phrases(
        security,
        (
            "It may produce source-linked screening observations and verification tasks.",
            "Do not recommend, rank, score, or steer residential areas.",
            "protected-class, demographic, school-quality, neighborhood-quality",
            "residential-steering proxy features",
            "Unknown license means blocked for live/commercial use.",
        ),
        "security guardrails",
    )
    require_phrases(
        product,
        (
            "demographic/protected-class/neighborhood desirability scoring",
            "This parcel has legal access.",
            "This property has water rights.",
            "This is a good investment.",
            "This land is safe.",
            "This property is worth X.",
        ),
        "product risk language",
    )
    require_phrases(
        ds022,
        (
            "ACS demographic variables, protected-class analytics",
            "neighborhood desirability, market/investment/lending suitability",
            "residential steering",
            "This connector deliberately excludes ACS demographic data",
        ),
        "DS-022 source review",
    )
    require_phrases(
        private_mvp,
        (
            "overclaim_checks",
            "backend/tests/reports/test_report_overclaim.py",
            "good investment",
            "'worth $'",
        ),
        "private MVP overclaim gate",
    )


def validate_connector_and_report_guards() -> None:
    census = read_text("backend/app/connectors/census_tiger.py")
    census_tests = (
        read_text("backend/tests/connectors/test_census_tiger_connector.py")
        + "\n"
        + read_text("backend/tests/api/test_census_tiger_connector_api.py")
    )
    report_tests = (
        read_text("backend/tests/reports/test_report_overclaim.py")
        + "\n"
        + read_text("backend/tests/api/test_report_export.py")
        + "\n"
        + read_text("backend/tests/private_mvp/test_mvp_regression.py")
    )
    source_rights = read_text("backend/app/source_registry/usage_rights.py")
    source_rights_tests = read_text("backend/tests/source_registry/test_usage_rights.py")

    require_phrases(
        census,
        (
            "does not use ACS",
            "demographic variables",
            "protected-class characteristics",
            "neighborhood desirability",
            "residential steering signals",
            '"census_demographics_used": False',
        ),
        "Census TIGER connector",
    )
    require_phrases(
        census_tests,
        (
            'observed_value["census_demographics_used"] is False',
            "test_caveat_excludes_acs_demographic_scoring",
            "residential steering",
        ),
        "Census TIGER tests",
    )
    require_phrases(
        report_tests,
        (
            "FORBIDDEN_PHRASES",
            "You can build here",
            "This parcel has legal access",
            "This property has water rights",
            "This is a good investment",
            "This land is safe",
        ),
        "report overclaim tests",
    )
    require_phrases(
        source_rights + "\n" + source_rights_tests,
        (
            "source_report_exposure_sensitive_fields",
            "report_exposure",
            "approved-with-restrictions",
            "marketValue",
        ),
        "source-rights exposure guard",
    )


def validate_compare_access_and_error_guards() -> None:
    runtime_smoke = read_text("scripts/ui_runtime_smoke.py")
    runtime_tests = read_text("backend/tests/test_ui_runtime_smoke_script.py")
    access_catalog = read_text("config/access_control.yaml")
    access_runbook = read_text("docs/runbooks/access_control.md")
    access_validator = read_text("scripts/access_control_check.py")
    ui_shared = read_text("backend/app/api/ui_shared.py")
    ui_shared_tests = read_text("backend/tests/api/test_ui_shared.py")
    error_safety = read_text("backend/app/core/error_safety.py")
    reports_api = read_text("backend/app/api/reports.py")
    connectors_api = read_text("backend/app/api/connectors.py")
    ui_error_surfaces = (
        read_text("backend/app/api/ui.py")
        + "\n"
        + read_text("backend/app/api/ui_live_connector_jobs.py")
        + "\n"
        + read_text("backend/app/api/ui_review.py")
    )
    error_surface_tests = (
        read_text("backend/tests/api/test_report_run_list.py")
        + "\n"
        + read_text("backend/tests/api/test_ui_routes.py")
        + "\n"
        + read_text("backend/tests/api/test_usgs_tnm_connector_api.py")
        + "\n"
        + read_text("backend/tests/api/test_ui_live_connector_jobs.py")
        + "\n"
        + read_text("backend/tests/api/test_connector_review_queue_api.py")
        + "\n"
        + read_text("backend/tests/api/test_ui_review_routes.py")
    )
    recovery_preview = read_text("backend/app/operations/recovery_preview.py")
    operations_tests = (
        read_text("backend/tests/api/test_operations.py")
        + "\n"
        + read_text("backend/tests/api/test_ui_operations_routes.py")
    )
    matrix = read_text("state/LEVEL_9_10_GATE_MATRIX.md")

    require_phrases(
        runtime_smoke + "\n" + runtime_tests,
        (
            "_contains_forbidden_compare_semantics",
            "compare API exposed ranking/recommendation keys",
            "recommendation",
            "--compare-same-area requires --operator-case-id",
        ),
        "compare/diff smoke semantics guard",
    )
    require_phrases(
        access_catalog + "\n" + access_runbook + "\n" + access_validator,
        (
            "identity_rbac_contract",
            "validate-only",
            "hosted identity provider remains blocked",
            "no production RBAC claim",
            "REVIEWER_ACCOUNT_SCOPES",
        ),
        "access-control contract",
    )
    require_phrases(
        ui_shared + "\n" + ui_shared_tests,
        (
            "html.escape",
            "test_error_page_escapes_content_and_includes_viewport_meta",
            "Message with &lt;script&gt;",
            '"<script>" not in body',
        ),
        "UI error safety",
    )
    require_phrases(
        recovery_preview + "\n" + operations_tests,
        (
            "safe_recovery_error_message",
            "RECOVERY_PREVIEW_REDACTED_ERROR_MESSAGE",
            "test_recovery_preview_redacts_sensitive_error_details_without_mutating_jobs",
            "test_ui_operations_recovery_preview_redacts_sensitive_error_details",
            "Traceback",
            "API_KEY",
            "raw_payload",
            "stored_report.error_msg == raw_report_error",
        ),
        "operations recovery error safety",
    )
    require_phrases(
        (
            error_safety
            + "\n"
            + reports_api
            + "\n"
            + connectors_api
            + "\n"
            + ui_error_surfaces
            + "\n"
            + error_surface_tests
        ),
        (
            "REDACTED_ERROR_MESSAGE",
            "safe_error_message",
            "safe_url_summary",
            "safe_payload_copy",
            "safe_payload_summary",
            "test_failed_report_api_list_and_detail_redact_error_without_mutating_job",
            "test_ui_report_run_failed_detail_redacts_error_without_mutating_job",
            "test_live_connector_job_api_sanitizes_error_and_payload_without_mutating_job",
            "test_ui_live_connector_job_detail_sanitizes_error_url_and_payload",
            "test_connector_review_queue_api_redacts_last_error_without_payload_loss",
            "test_ui_review_detail_redacts_last_error_without_hiding_failure_counts",
        ),
        "user-facing error serialization safety",
    )
    require_phrases(
        matrix,
        (
            "L10-SEC-005",
            "threat-model review",
            "L10-SEC-008",
            "production proxy-audit review",
            "L10-SEC-009",
            "hosted error/log review",
        ),
        "Level 9/10 security gate matrix",
    )


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/threat_proxy_audit.md")
    security_scan = read_text("docs/runbooks/security_scan.md")
    require_phrases(
        runbook,
        (
            "run_threat_proxy_audit_check.ps1",
            "validate-only",
            "threat_proxy_audit_v1",
            "census_demographics_used=false",
            "ranking/recommendation",
            "external security review",
            "legal fair-housing review",
            "hosted IdP/RBAC",
            "DS-017 entitlement",
            "hosted alerting",
        ),
        "threat/proxy runbook",
    )
    require_phrases(
        security_scan,
        (
            "medium severity and above",
            "HIGH or CRITICAL",
            "Medium findings are reported but do not block the build",
        ),
        "security scan runbook",
    )


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_policy_and_product_boundary()
    validate_connector_and_report_guards()
    validate_compare_access_and_error_guards()
    validate_runbook()
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
