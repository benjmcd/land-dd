from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.dependencies import (
    ApiServices,
    RequestAuthContext,
    get_request_auth_context,
    get_services,
)
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_REPORT_RUN,
    ReviewerPrincipal,
    require_reviewer_scope,
)
from app.domain.enums import IntentCode

router = APIRouter(prefix="/operator-cases", tags=["operator-cases-private-mvp"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]
AuthDep = Annotated[RequestAuthContext, Depends(get_request_auth_context)]

_HTTP_422_UNPROCESSABLE: int = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
_MISSING = object()
_DEFAULT_REASON = "private_mvp_fixture_only"
_DEFAULT_FIXTURE_SCOPE = "private_mvp_fixture"
_DEFAULT_FIXTURE_LANGUAGE = (
    "Packaged fixture-only selected-county private MVP case; not live coverage."
)
_PRIVATE_MVP_MESSAGE = (
    "Private-MVP selected-county fixture-only coverage created. "
    "This does not use live-source production coverage."
)


class OperatorCaseSummary(BaseModel):
    case_id: str
    county: str
    state: str
    intent: str
    description: str
    connector_domains: list[str] = Field(default_factory=list)
    fixture_scope: str = _DEFAULT_FIXTURE_SCOPE
    fixture_language: str = _DEFAULT_FIXTURE_LANGUAGE
    not_evaluated_domains: list[str] = Field(default_factory=list)
    expected_unknowns: list[str] = Field(default_factory=list)
    fixture_only: bool = True


class OperatorCaseReportLinks(BaseModel):
    ui: str
    dossier_download: str
    artifact: str


class OperatorCaseReportCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer_id: str | None = None
    reason: str | None = None

    @field_validator("reviewer_id", "reason")
    @classmethod
    def _reject_blank_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class SupportedAoiReportCreateRequest(OperatorCaseReportCreateRequest):
    area_id: UUID
    intent_code: IntentCode = IntentCode.RURAL_LAND_PURCHASE


class OperatorCaseReportResponse(BaseModel):
    case_id: str
    report_run_id: UUID
    review_status: str
    status: str
    fixture_only: bool = True
    message: str = _PRIVATE_MVP_MESSAGE
    evidence_count: int | None = None
    connector_count: int | None = None
    links: OperatorCaseReportLinks


class SupportedAoiReportResponse(BaseModel):
    area_id: UUID
    county: str
    report_run_id: UUID
    review_status: str
    status: str
    fixture_only: bool = True
    message: str = _PRIVATE_MVP_MESSAGE
    evidence_count: int | None = None
    connector_count: int | None = None
    links: OperatorCaseReportLinks


@dataclass(frozen=True)
class OperatorCasesContract:
    list_selected_county_cases: Callable[[], Sequence[object]]
    get_selected_county_case: Callable[[str], object | None]
    create_selected_county_report: Callable[..., object]
    create_supported_aoi_report: Callable[..., object]


def get_reviewer_principal(
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Header(alias="X-Reviewer-Id")] = None,
    reviewer_token: Annotated[str | None, Header(alias="X-Reviewer-Token")] = None,
) -> ReviewerPrincipal:
    return services.reviewer_auth(reviewer_id=reviewer_id, reviewer_token=reviewer_token)


def resolve_operator_cases_contract() -> OperatorCasesContract:
    try:
        module = importlib.import_module("app.operator_cases")
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "selected-county private-MVP fixture service is not available "
                "in this build"
            ),
        ) from exc

    return OperatorCasesContract(
        list_selected_county_cases=cast(
            Callable[[], Sequence[object]],
            _require_callable(module, "list_selected_county_cases"),
        ),
        get_selected_county_case=cast(
            Callable[[str], object | None],
            _require_callable(module, "get_selected_county_case"),
        ),
        create_selected_county_report=_require_callable(
            module,
            "create_selected_county_report",
        ),
        create_supported_aoi_report=_require_callable(
            module,
            "create_supported_aoi_report",
        ),
    )


def list_selected_county_case_summaries() -> list[OperatorCaseSummary]:
    contract = resolve_operator_cases_contract()
    return [_coerce_case_summary(case) for case in contract.list_selected_county_cases()]


def create_selected_county_fixture_report_response(
    *,
    services: ApiServices,
    case_id: str,
    reviewer_id: str,
    reason: str | None = None,
    workspace_id: UUID | None = None,
    requested_by: UUID | None = None,
) -> OperatorCaseReportResponse:
    contract = resolve_operator_cases_contract()
    case = contract.get_selected_county_case(case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"selected-county private-MVP fixture case '{case_id}' not found",
        )

    created = contract.create_selected_county_report(
        services,
        case_id,
        reviewer_id=reviewer_id,
        reason=reason or _DEFAULT_REASON,
        workspace_id=workspace_id,
        requested_by=requested_by,
    )
    summary = _coerce_case_summary(case)
    report_run_id = _coerce_uuid(
        _first_present(created, ("report_run_id",)),
        "report_run_id",
    )
    return OperatorCaseReportResponse(
        case_id=summary.case_id,
        report_run_id=report_run_id,
        review_status=_stringify(
            _first_present(created, ("review_status",), default="approved")
        ),
        status=_stringify(
            _first_present(created, ("status",), default="succeeded")
        ),
        evidence_count=_extract_evidence_count(created),
        connector_count=len(summary.connector_domains),
        links=OperatorCaseReportLinks(
            ui=f"/ui/report-runs/{report_run_id}",
            dossier_download=f"/report-runs/{report_run_id}/dossier?download=1",
            artifact=f"/report-runs/{report_run_id}/artifact",
        ),
    )


def create_supported_aoi_fixture_report_response(
    *,
    services: ApiServices,
    area_id: UUID,
    intent_code: IntentCode,
    reviewer_id: str,
    reason: str | None = None,
    workspace_id: UUID | None = None,
    requested_by: UUID | None = None,
) -> SupportedAoiReportResponse:
    _operator_cases_mod = importlib.import_module("app.operator_cases")
    # SupportedAoiAreaNotFoundError is always present when the module loads
    # successfully; the Exception fallback is unreachable but keeps mypy happy.
    _SupportedAoiAreaNotFoundError: type[Exception] = getattr(
        _operator_cases_mod, "SupportedAoiAreaNotFoundError", Exception
    )

    contract = resolve_operator_cases_contract()
    try:
        created = contract.create_supported_aoi_report(
            services,
            area_id=area_id,
            intent_code=intent_code,
            reviewer_id=reviewer_id,
            reason=reason or _DEFAULT_REASON,
            workspace_id=workspace_id,
            requested_by=requested_by,
        )
    except _SupportedAoiAreaNotFoundError:
        # Intentionally returns 404 for both "does not exist" and "exists in another
        # workspace" — same opaque response, no existence disclosure.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="area not found",
        ) from None
    except ValueError as exc:
        raise HTTPException(
            status_code=_HTTP_422_UNPROCESSABLE,
            detail=str(exc),
        ) from exc

    report_run_id = _coerce_uuid(
        _first_present(created, ("report_run_id",)),
        "report_run_id",
    )
    return SupportedAoiReportResponse(
        area_id=area_id,
        county=_extract_supported_aoi_county(created),
        report_run_id=report_run_id,
        review_status=_stringify(
            _first_present(created, ("review_status",), default="approved")
        ),
        status=_stringify(
            _first_present(created, ("status",), default="succeeded")
        ),
        evidence_count=_extract_evidence_count(created),
        connector_count=_extract_connector_count(created),
        links=OperatorCaseReportLinks(
            ui=f"/ui/report-runs/{report_run_id}",
            dossier_download=f"/report-runs/{report_run_id}/dossier?download=1",
            artifact=f"/report-runs/{report_run_id}/artifact",
        ),
    )


@router.get("", response_model=list[OperatorCaseSummary])
def list_operator_cases() -> list[OperatorCaseSummary]:
    return list_selected_county_case_summaries()


@router.post(
    "/supported-aoi/report",
    response_model=SupportedAoiReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supported_aoi_report(
    body: SupportedAoiReportCreateRequest,
    services: ServicesDep,
    auth: AuthDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> SupportedAoiReportResponse:
    require_reviewer_scope(principal, REVIEWER_SCOPE_REPORT_RUN)
    reviewer_id = _authenticated_reviewer_id(principal, body)
    return create_supported_aoi_fixture_report_response(
        services=services,
        area_id=body.area_id,
        intent_code=body.intent_code,
        reviewer_id=reviewer_id,
        reason=body.reason,
        workspace_id=auth.workspace_id,
        requested_by=auth.user_id,
    )


@router.post(
    "/{case_id}/report",
    response_model=OperatorCaseReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_operator_case_report(
    case_id: str,
    services: ServicesDep,
    auth: AuthDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
    body: OperatorCaseReportCreateRequest | None = None,
) -> OperatorCaseReportResponse:
    require_reviewer_scope(principal, REVIEWER_SCOPE_REPORT_RUN)
    reviewer_id = _authenticated_reviewer_id(principal, body)
    return create_selected_county_fixture_report_response(
        services=services,
        case_id=case_id,
        reviewer_id=reviewer_id,
        reason=body.reason if body else None,
        workspace_id=auth.workspace_id,
        requested_by=auth.user_id,
    )


def _authenticated_reviewer_id(
    principal: ReviewerPrincipal,
    body: OperatorCaseReportCreateRequest | None,
) -> str:
    if body is None or body.reviewer_id is None:
        return principal.reviewer_id
    if body.reviewer_id != principal.reviewer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="body reviewer_id must match the authenticated reviewer",
        )
    return principal.reviewer_id


def _coerce_case_summary(case: object) -> OperatorCaseSummary:
    return OperatorCaseSummary(
        case_id=_require_string(_first_present(case, ("case_id",)), "case_id"),
        county=_require_string(_first_present(case, ("county",)), "county"),
        state=_require_string(_first_present(case, ("state",)), "state"),
        intent=_stringify(_first_present(case, ("intent", "intent_code"))),
        description=_require_string(
            _first_present(case, ("description",)),
            "description",
        ),
        connector_domains=_coerce_string_list(
            _first_present(
                case,
                ("connector_domains", "expected_connector_workflow_domains"),
                default=[],
            ),
            "connector_domains",
        ),
        fixture_scope=_require_string(
            _first_present(
                case,
                ("fixture_scope",),
                default=_DEFAULT_FIXTURE_SCOPE,
            ),
            "fixture_scope",
        ),
        fixture_language=_require_string(
            _first_present(
                case,
                ("fixture_language",),
                default=_DEFAULT_FIXTURE_LANGUAGE,
            ),
            "fixture_language",
        ),
        not_evaluated_domains=_coerce_string_list(
            _first_present(
                case,
                ("not_evaluated_domains", "expected_not_evaluated_domains"),
                default=[],
            ),
            "not_evaluated_domains",
        ),
        expected_unknowns=_coerce_string_list(
            _first_present(
                case,
                ("expected_unknowns",),
                default=[],
            ),
            "expected_unknowns",
        ),
        fixture_only=bool(_first_present(case, ("fixture_only",), default=True)),
    )


def _extract_evidence_count(created: object) -> int | None:
    explicit = _field_value(created, "evidence_count")
    if explicit is not _MISSING:
        return _coerce_optional_int(explicit, "evidence_count")

    evidence = _field_value(created, "evidence")
    if isinstance(evidence, Sequence) and not isinstance(evidence, str):
        return len(evidence)

    artifact_metadata = _field_value(created, "artifact_metadata")
    if isinstance(artifact_metadata, Mapping):
        cost_metrics = artifact_metadata.get("cost_metrics")
        if isinstance(cost_metrics, Mapping):
            return _coerce_optional_int(
                cost_metrics.get("evidence_count"),
                "artifact_metadata.cost_metrics.evidence_count",
            )
    return None


def _extract_connector_count(created: object) -> int | None:
    explicit = _field_value(created, "connector_count")
    if explicit is not _MISSING:
        return _coerce_optional_int(explicit, "connector_count")
    return None


def _extract_supported_aoi_county(created: object) -> str:
    profile = _field_value(created, "support_profile")
    if profile is _MISSING:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="generic AOI report returned no support profile",
        )
    return _require_string(_first_present(profile, ("county",)), "county")


def _require_callable(module: object, name: str) -> Callable[..., object]:
    fn = getattr(module, name, None)
    if callable(fn):
        return cast(Callable[..., object], fn)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "selected-county private-MVP fixture service is incomplete: "
            f"missing callable '{name}'"
        ),
    )


def _first_present(
    record: object,
    fields: tuple[str, ...],
    *,
    default: object = _MISSING,
) -> object:
    for field in fields:
        value = _field_value(record, field)
        if value is not _MISSING:
            return value
    if default is not _MISSING:
        return default
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "selected-county private-MVP fixture service returned an incomplete "
            f"payload; missing {', '.join(fields)}"
        ),
    )


def _field_value(record: object, field: str) -> object:
    if isinstance(record, Mapping) and field in record:
        return record[field]
    if hasattr(record, field):
        return getattr(record, field)
    return _MISSING


def _require_string(value: object, field_name: str) -> str:
    if isinstance(value, Enum):
        value = value.value
    if isinstance(value, str) and value.strip():
        return value
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "selected-county private-MVP fixture service returned an invalid "
            f"'{field_name}' value"
        ),
    )


def _coerce_string_list(value: object, field_name: str) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [_require_string(item, field_name) for item in value]
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "selected-county private-MVP fixture service returned an invalid "
            f"'{field_name}' list"
        ),
    )


def _coerce_uuid(value: object, field_name: str) -> UUID:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "selected-county private-MVP fixture service returned an invalid "
                    f"'{field_name}' value"
                ),
            ) from exc
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "selected-county private-MVP fixture service returned an invalid "
            f"'{field_name}' value"
        ),
    )


def _coerce_optional_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "selected-county private-MVP fixture service returned an invalid "
                f"'{field_name}' value"
            ),
        )
    if isinstance(value, int):
        return value
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "selected-county private-MVP fixture service returned an invalid "
            f"'{field_name}' value"
        ),
    )


def _stringify(value: object) -> str:
    if isinstance(value, Enum):
        value = value.value
    return _require_string(value, "string_value")
