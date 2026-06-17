import hashlib
import hmac
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Header, HTTPException, status

from app.api.secret_specs import matches_secret_spec, normalize_secret_spec

REVIEWER_SCOPE_CONNECTOR_RUN = "connector:run"
REVIEWER_SCOPE_CONNECTOR_REVIEW = "connector:review"
REVIEWER_SCOPE_OPERATIONS_READ = "operations:read"
REVIEWER_SCOPE_REPORT_APPROVE = "report:approve"
REVIEWER_SCOPE_REPORT_RETRY = "report:retry"
REVIEWER_SCOPE_REPORT_RUN = "report:run"
REVIEWER_SCOPE_SOURCE_MANAGE = "source:manage"
REVIEWER_SESSION_BINDING_PREFIX = "land-dd-reviewer-session-binding-v1"

REVIEWER_SCOPES = frozenset(
    {
        REVIEWER_SCOPE_CONNECTOR_RUN,
        REVIEWER_SCOPE_CONNECTOR_REVIEW,
        REVIEWER_SCOPE_OPERATIONS_READ,
        REVIEWER_SCOPE_REPORT_APPROVE,
        REVIEWER_SCOPE_REPORT_RETRY,
        REVIEWER_SCOPE_REPORT_RUN,
        REVIEWER_SCOPE_SOURCE_MANAGE,
    }
)


@dataclass(frozen=True)
class ReviewerPrincipal:
    reviewer_id: str
    scopes: frozenset[str] = field(default_factory=frozenset)
    auth_scheme: str = "local_service_account"


class LocalServiceAccountReviewerAuth:
    def __init__(
        self,
        service_account_tokens: Mapping[str, str],
        service_account_scopes: Mapping[str, Iterable[str]] | None = None,
    ) -> None:
        self._service_account_tokens = {
            _require_config_value(account_id, "service account id"): normalize_secret_spec(
                token,
                "service account token",
            )
            for account_id, token in service_account_tokens.items()
        }
        configured_scopes = service_account_scopes or {}
        self._service_account_scopes = _validate_service_account_scopes(
            account_ids=frozenset(self._service_account_tokens),
            service_account_scopes=configured_scopes,
        )

    def __call__(
        self,
        reviewer_id: Annotated[str | None, Header(alias="X-Reviewer-Id")] = None,
        reviewer_token: Annotated[str | None, Header(alias="X-Reviewer-Token")] = None,
    ) -> ReviewerPrincipal:
        if not self._service_account_tokens:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="connector reviewer auth is not configured",
            )

        cleaned_reviewer_id = _clean_header(reviewer_id)
        cleaned_token = _clean_header(reviewer_token)
        if cleaned_reviewer_id is None or cleaned_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="connector reviewer credentials are required",
            )

        expected_token = self._service_account_tokens.get(cleaned_reviewer_id)
        if expected_token is None or not matches_secret_spec(cleaned_token, expected_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="connector reviewer credentials are invalid",
            )

        return ReviewerPrincipal(
            reviewer_id=cleaned_reviewer_id,
            scopes=self._service_account_scopes[cleaned_reviewer_id],
        )

    def principal_from_session(
        self,
        *,
        reviewer_id: str,
        scopes: Iterable[str],
        session_binding: str,
        signing_secret: str,
    ) -> ReviewerPrincipal:
        cleaned_reviewer_id = _clean_header(reviewer_id)
        if cleaned_reviewer_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="connector reviewer session is invalid",
            )
        configured_scopes = self._service_account_scopes.get(cleaned_reviewer_id)
        if (
            cleaned_reviewer_id not in self._service_account_tokens
            or configured_scopes is None
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="connector reviewer session is invalid",
            )
        expected_binding = self.session_binding(
            reviewer_id=cleaned_reviewer_id,
            signing_secret=signing_secret,
        )
        if not hmac.compare_digest(session_binding, expected_binding):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="connector reviewer session is invalid",
            )
        session_scopes = frozenset(
            _require_known_scope(scope, cleaned_reviewer_id) for scope in scopes
        )
        if not session_scopes or not session_scopes.issubset(configured_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="connector reviewer session scope is invalid",
            )
        return ReviewerPrincipal(
            reviewer_id=cleaned_reviewer_id,
            scopes=session_scopes,
            auth_scheme="ui_reviewer_session",
        )

    def session_binding(self, *, reviewer_id: str, signing_secret: str) -> str:
        cleaned_reviewer_id = _clean_header(reviewer_id)
        if cleaned_reviewer_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="connector reviewer session is invalid",
            )
        token_spec = self._service_account_tokens.get(cleaned_reviewer_id)
        if token_spec is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="connector reviewer session is invalid",
            )
        signing_key = hashlib.sha256(
            f"{REVIEWER_SESSION_BINDING_PREFIX}:{signing_secret}".encode()
        ).digest()
        signed_value = f"{cleaned_reviewer_id}\0{token_spec}".encode()
        return hmac.new(signing_key, signed_value, hashlib.sha256).hexdigest()


def require_reviewer_scope(principal: ReviewerPrincipal, required_scope: str) -> None:
    if required_scope not in REVIEWER_SCOPES:
        raise ValueError(f"unknown reviewer scope: {required_scope}")
    if required_scope not in principal.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"reviewer scope is required: {required_scope}",
        )


def _clean_header(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned


def _require_config_value(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    return cleaned


def _validate_service_account_scopes(
    *,
    account_ids: frozenset[str],
    service_account_scopes: Mapping[str, Iterable[str]],
) -> dict[str, frozenset[str]]:
    unknown_accounts = set(service_account_scopes) - set(account_ids)
    if unknown_accounts:
        raise ValueError(
            "REVIEWER_ACCOUNT_SCOPES references unknown reviewer id: "
            f"{sorted(unknown_accounts)[0]!r}"
        )

    validated: dict[str, frozenset[str]] = {}
    for account_id in account_ids:
        raw_scopes = service_account_scopes.get(account_id)
        if raw_scopes is None:
            raise ValueError(f"REVIEWER_ACCOUNT_SCOPES missing reviewer id: {account_id!r}")
        scopes = frozenset(_require_known_scope(scope, account_id) for scope in raw_scopes)
        if not scopes:
            raise ValueError(f"REVIEWER_ACCOUNT_SCOPES for {account_id!r} must not be empty")
        validated[account_id] = scopes
    return validated


def _require_known_scope(scope: str, account_id: str) -> str:
    cleaned = scope.strip()
    if not cleaned:
        raise ValueError(f"REVIEWER_ACCOUNT_SCOPES for {account_id!r} includes blank scope")
    if cleaned not in REVIEWER_SCOPES:
        raise ValueError(
            f"REVIEWER_ACCOUNT_SCOPES for {account_id!r} includes unknown scope: "
            f"{cleaned!r}"
        )
    return cleaned


__all__ = [
    "LocalServiceAccountReviewerAuth",
    "REVIEWER_SCOPE_CONNECTOR_REVIEW",
    "REVIEWER_SCOPE_CONNECTOR_RUN",
    "REVIEWER_SCOPE_OPERATIONS_READ",
    "REVIEWER_SCOPE_REPORT_APPROVE",
    "REVIEWER_SCOPE_REPORT_RETRY",
    "REVIEWER_SCOPE_REPORT_RUN",
    "REVIEWER_SCOPE_SOURCE_MANAGE",
    "ReviewerPrincipal",
    "require_reviewer_scope",
]
