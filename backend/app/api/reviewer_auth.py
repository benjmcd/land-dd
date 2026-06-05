from collections.abc import Mapping
from dataclasses import dataclass
from hmac import compare_digest
from typing import Annotated, Optional

from fastapi import Header, HTTPException, status


@dataclass(frozen=True)
class ReviewerPrincipal:
    reviewer_id: str
    auth_scheme: str = "local_service_account"


class LocalServiceAccountReviewerAuth:
    def __init__(self, service_account_tokens: Mapping[str, str]) -> None:
        self._service_account_tokens = {
            _require_config_value(account_id, "service account id"): _require_config_value(
                token,
                "service account token",
            )
            for account_id, token in service_account_tokens.items()
        }

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
        if expected_token is None or not compare_digest(cleaned_token, expected_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="connector reviewer credentials are invalid",
            )

        return ReviewerPrincipal(reviewer_id=cleaned_reviewer_id)


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


__all__ = ["LocalServiceAccountReviewerAuth", "ReviewerPrincipal"]
