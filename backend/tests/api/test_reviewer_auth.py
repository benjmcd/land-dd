from hashlib import sha256
from typing import Annotated, Any, cast

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.reviewer_auth import (
    REVIEWER_SCOPE_CONNECTOR_REVIEW,
    REVIEWER_SCOPE_CONNECTOR_RUN,
    REVIEWER_SCOPE_OPERATIONS_READ,
    REVIEWER_SCOPE_SOURCE_MANAGE,
    LocalServiceAccountReviewerAuth,
    ReviewerPrincipal,
    require_reviewer_scope,
)
from app.core.config import Settings


def _client(
    service_account_tokens: dict[str, str],
    service_account_scopes: dict[str, frozenset[str]] | None = None,
) -> TestClient:
    app = FastAPI()
    auth = LocalServiceAccountReviewerAuth(
        service_account_tokens,
        (
            service_account_scopes
            if service_account_scopes is not None
            else {"fixture-reviewer": frozenset({REVIEWER_SCOPE_CONNECTOR_REVIEW})}
        ),
    )

    @app.get("/reviewer-principal")
    def read_reviewer_principal(
        principal: Annotated[ReviewerPrincipal, Depends(auth)],
    ) -> dict[str, object]:
        return {
            "reviewer_id": principal.reviewer_id,
            "auth_scheme": principal.auth_scheme,
            "scopes": sorted(principal.scopes),
        }

    return TestClient(app)


def test_local_service_account_reviewer_auth_returns_principal() -> None:
    client = _client({"fixture-reviewer": "fixture-token"})

    response = client.get(
        "/reviewer-principal",
        headers={
            "X-Reviewer-Id": " fixture-reviewer ",
            "X-Reviewer-Token": "fixture-token",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "reviewer_id": "fixture-reviewer",
        "auth_scheme": "local_service_account",
        "scopes": [REVIEWER_SCOPE_CONNECTOR_REVIEW],
    }


def test_local_service_account_reviewer_auth_accepts_sha256_token_hash() -> None:
    digest = sha256(b"fixture-token").hexdigest()
    client = _client({"fixture-reviewer": f"sha256:{digest}"})

    response = client.get(
        "/reviewer-principal",
        headers={
            "X-Reviewer-Id": "fixture-reviewer",
            "X-Reviewer-Token": "fixture-token",
        },
    )

    assert response.status_code == 200
    assert response.json()["reviewer_id"] == "fixture-reviewer"


def test_local_service_account_reviewer_auth_rejects_missing_scope() -> None:
    client = _client(
        {"fixture-reviewer": "fixture-token"},
        {"fixture-reviewer": frozenset({REVIEWER_SCOPE_CONNECTOR_RUN})},
    )

    response = client.get(
        "/reviewer-principal",
        headers={
            "X-Reviewer-Id": "fixture-reviewer",
            "X-Reviewer-Token": "fixture-token",
        },
    )
    principal = ReviewerPrincipal(
        reviewer_id=response.json()["reviewer_id"],
        scopes=frozenset(response.json()["scopes"]),
    )

    assert response.status_code == 200
    with pytest.raises(HTTPException) as exc_info:
        require_reviewer_scope(principal, REVIEWER_SCOPE_OPERATIONS_READ)
    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail
        == f"reviewer scope is required: {REVIEWER_SCOPE_OPERATIONS_READ}"
    )


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-Reviewer-Id": "fixture-reviewer"},
        {"X-Reviewer-Token": "fixture-token"},
        {"X-Reviewer-Id": " ", "X-Reviewer-Token": "fixture-token"},
        {"X-Reviewer-Id": "fixture-reviewer", "X-Reviewer-Token": " "},
    ],
)
def test_local_service_account_reviewer_auth_rejects_missing_credentials(
    headers: dict[str, str],
) -> None:
    client = _client({"fixture-reviewer": "fixture-token"})

    response = client.get("/reviewer-principal", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "connector reviewer credentials are required"


@pytest.mark.parametrize(
    "headers",
    [
        {"X-Reviewer-Id": "unknown-reviewer", "X-Reviewer-Token": "fixture-token"},
        {"X-Reviewer-Id": "fixture-reviewer", "X-Reviewer-Token": "wrong-token"},
    ],
)
def test_local_service_account_reviewer_auth_rejects_invalid_credentials(
    headers: dict[str, str],
) -> None:
    client = _client({"fixture-reviewer": "fixture-token"})

    response = client.get("/reviewer-principal", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "connector reviewer credentials are invalid"


def test_local_service_account_reviewer_auth_fails_closed_when_unconfigured() -> None:
    client = _client({}, {})

    response = client.get(
        "/reviewer-principal",
        headers={
            "X-Reviewer-Id": "fixture-reviewer",
            "X-Reviewer-Token": "fixture-token",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "connector reviewer auth is not configured"


@pytest.mark.parametrize(
    "service_account_tokens",
    [
        {" ": "fixture-token"},
        {"fixture-reviewer": " "},
    ],
)
def test_local_service_account_reviewer_auth_rejects_blank_config(
    service_account_tokens: dict[str, str],
) -> None:
    with pytest.raises(ValueError, match="is required"):
        LocalServiceAccountReviewerAuth(
            service_account_tokens,
            {"fixture-reviewer": frozenset({REVIEWER_SCOPE_CONNECTOR_REVIEW})},
        )


def test_local_service_account_reviewer_auth_fails_closed_without_scopes() -> None:
    with pytest.raises(ValueError, match="missing reviewer id"):
        LocalServiceAccountReviewerAuth({"fixture-reviewer": "fixture-token"}, {})


def test_local_service_account_reviewer_auth_rejects_unknown_scope() -> None:
    with pytest.raises(ValueError, match="unknown scope"):
        LocalServiceAccountReviewerAuth(
            {"fixture-reviewer": "fixture-token"},
            {"fixture-reviewer": frozenset({"unknown:scope"})},
        )


def test_settings_parses_reviewer_accounts() -> None:
    settings = Settings(
        REVIEWER_ACCOUNTS=" reviewer-a : token-a , reviewer-b:token-b ",
    )

    assert settings.parsed_reviewer_accounts() == {
        "reviewer-a": "token-a",
        "reviewer-b": "token-b",
    }


def test_settings_parses_reviewer_account_token_hash_specs() -> None:
    digest = sha256(b"token-a").hexdigest().upper()
    settings = Settings(
        REVIEWER_ACCOUNTS=f" reviewer-a : sha256:{digest} ",
    )

    assert settings.parsed_reviewer_accounts() == {
        "reviewer-a": f"sha256:{digest.lower()}",
    }


def test_non_local_settings_require_hashed_reviewer_accounts_with_scopes() -> None:
    digest = sha256(b"token-a").hexdigest()
    settings = Settings(
        APP_ENV="production",
        REVIEWER_ACCOUNTS=f"reviewer-a:sha256:{digest}",
        REVIEWER_ACCOUNT_SCOPES="reviewer-a:connector:run|connector:review|source:manage",
    )

    assert settings.parsed_reviewer_accounts() == {
        "reviewer-a": f"sha256:{digest}",
    }
    assert settings.parsed_reviewer_account_scopes() == {
        "reviewer-a": frozenset(
            {
                REVIEWER_SCOPE_CONNECTOR_RUN,
                REVIEWER_SCOPE_CONNECTOR_REVIEW,
                REVIEWER_SCOPE_SOURCE_MANAGE,
            }
        )
    }


@pytest.mark.parametrize(
    "kwargs,method,match",
    [
        ({}, "parsed_reviewer_accounts", "fixture reviewer account is local-only"),
        (
            {"REVIEWER_ACCOUNTS": "reviewer-a:raw-token"},
            "parsed_reviewer_accounts",
            "sha256:<64-hex>",
        ),
        (
            {
                "REVIEWER_ACCOUNTS": "reviewer-a:sha256:" + ("a" * 64),
                "REVIEWER_ACCOUNT_SCOPES": "",
            },
            "parsed_reviewer_account_scopes",
            "explicit REVIEWER_ACCOUNT_SCOPES",
        ),
    ],
)
def test_non_local_settings_reject_fixture_or_raw_reviewer_accounts(
    kwargs: dict[str, object],
    method: str,
    match: str,
) -> None:
    settings_kwargs: dict[str, object] = {"APP_ENV": "production", **kwargs}
    settings = Settings(**cast(Any, settings_kwargs))

    with pytest.raises(ValueError, match=match):
        getattr(settings, method)()


def test_settings_parses_reviewer_account_scopes() -> None:
    settings = Settings(
        REVIEWER_ACCOUNT_SCOPES=(
            " reviewer-a : connector:run|connector:review ,"
            " reviewer-b:operations:read|source:manage "
        ),
    )

    assert settings.parsed_reviewer_account_scopes() == {
        "reviewer-a": frozenset(
            {
                REVIEWER_SCOPE_CONNECTOR_RUN,
                REVIEWER_SCOPE_CONNECTOR_REVIEW,
            }
        ),
        "reviewer-b": frozenset(
            {REVIEWER_SCOPE_OPERATIONS_READ, REVIEWER_SCOPE_SOURCE_MANAGE}
        ),
    }


@pytest.mark.parametrize(
    "reviewer_accounts,match",
    [
        ("missing-colon", "id:token"),
        (" :token", "include id and token"),
        ("reviewer: ", "include id and token"),
        ("reviewer:token,reviewer:other", "Duplicate"),
    ],
)
def test_settings_reviewer_accounts_fail_closed_for_malformed_entries(
    reviewer_accounts: str,
    match: str,
) -> None:
    settings = Settings(REVIEWER_ACCOUNTS=reviewer_accounts)

    with pytest.raises(ValueError, match=match):
        settings.parsed_reviewer_accounts()


@pytest.mark.parametrize(
    "reviewer_accounts,match",
    [
        ("reviewer:SHA256:" + ("a" * 64), "hash prefix must be lowercase"),
        ("reviewer:sha256:not-hex", "64 hex characters"),
        ("reviewer:sha256:" + ("a" * 63), "64 hex characters"),
    ],
)
def test_settings_reviewer_account_hash_specs_fail_closed_for_malformed_entries(
    reviewer_accounts: str,
    match: str,
) -> None:
    settings = Settings(REVIEWER_ACCOUNTS=reviewer_accounts)

    with pytest.raises(ValueError, match=match):
        settings.parsed_reviewer_accounts()


@pytest.mark.parametrize(
    "reviewer_account_scopes,match",
    [
        ("missing-colon", "id:scope"),
        (" :connector:run", "include id and scopes"),
        ("reviewer: ", "include id and scopes"),
        ("reviewer:connector:run,reviewer:connector:review", "Duplicate"),
    ],
)
def test_settings_reviewer_account_scopes_fail_closed_for_malformed_entries(
    reviewer_account_scopes: str,
    match: str,
) -> None:
    settings = Settings(REVIEWER_ACCOUNT_SCOPES=reviewer_account_scopes)

    with pytest.raises(ValueError, match=match):
        settings.parsed_reviewer_account_scopes()
