from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from uuid import uuid4

import pytest

from app.api.report_auth import verify_report_identity_token

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "mint_report_token.py"
SECRET = "report-identity-secret-with-at-least-32-characters"


def load_mint_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("mint_report_token", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["mint_report_token"] = module
    spec.loader.exec_module(module)
    return module


def test_mint_report_token_creates_verifiable_short_lived_token() -> None:
    module = load_mint_module()
    workspace_id = uuid4()
    user_id = uuid4()

    token = module.mint_report_token(
        workspace_id=str(workspace_id),
        user_id=str(user_id),
        secret_env="REPORT_IDENTITY_TOKEN_SECRET",
        expires_minutes=5,
        environ={"REPORT_IDENTITY_TOKEN_SECRET": SECRET},
    )

    claims = verify_report_identity_token(token, secret=SECRET)
    assert claims.workspace_id == workspace_id
    assert claims.user_id == user_id
    with pytest.raises(ValueError, match="expired"):
        verify_report_identity_token(
            token,
            secret=SECRET,
            now=datetime.now(UTC) + timedelta(minutes=6),
        )


def test_mint_report_token_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    module = load_mint_module()
    workspace_id = str(uuid4())
    user_id = str(uuid4())

    old_argv = sys.argv
    sys.argv = [
        "mint_report_token.py",
        "--workspace-id",
        workspace_id,
        "--user-id",
        user_id,
        "--expires-minutes",
        "10",
        "--json",
    ]
    try:
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setenv("REPORT_IDENTITY_TOKEN_SECRET", SECRET)
            module.main()
    finally:
        sys.argv = old_argv

    payload = json.loads(capsys.readouterr().out)
    assert payload["token_type"] == "Bearer"
    assert payload["expires_in_seconds"] == 600
    assert payload["workspace_id"] == workspace_id
    assert payload["user_id"] == user_id
    assert "token" in payload


def test_mint_report_token_requires_secret_and_positive_ttl() -> None:
    module = load_mint_module()

    with pytest.raises(ValueError, match="REPORT_IDENTITY_TOKEN_SECRET"):
        module.mint_report_token(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            secret_env="REPORT_IDENTITY_TOKEN_SECRET",
            expires_minutes=5,
            environ={},
        )
    with pytest.raises(ValueError, match="expires_minutes"):
        module.mint_report_token(
            workspace_id=str(uuid4()),
            user_id=str(uuid4()),
            secret_env="REPORT_IDENTITY_TOKEN_SECRET",
            expires_minutes=0,
            environ={"REPORT_IDENTITY_TOKEN_SECRET": SECRET},
        )
