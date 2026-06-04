from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.reviewer_auth import LocalServiceAccountReviewerAuth, ReviewerPrincipal


def _client(
    service_account_tokens: dict[str, str],
) -> TestClient:
    app = FastAPI()
    auth = LocalServiceAccountReviewerAuth(service_account_tokens)

    @app.get("/reviewer-principal")
    def read_reviewer_principal(
        principal: Annotated[ReviewerPrincipal, Depends(auth)],
    ) -> dict[str, str]:
        return {
            "reviewer_id": principal.reviewer_id,
            "auth_scheme": principal.auth_scheme,
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
    }


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
    client = _client({})

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
        LocalServiceAccountReviewerAuth(service_account_tokens)
