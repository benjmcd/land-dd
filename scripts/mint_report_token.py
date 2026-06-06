from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mint a short-lived report identity bearer token."
    )
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--secret-env", default="REPORT_IDENTITY_TOKEN_SECRET")
    parser.add_argument("--expires-minutes", type=int, default=60)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        token = mint_report_token(
            workspace_id=args.workspace_id,
            user_id=args.user_id,
            secret_env=args.secret_env,
            expires_minutes=args.expires_minutes,
            environ=os.environ,
        )
    except ValueError as exc:
        parser.error(str(exc))
    if args.json:
        print(
            json.dumps(
                {
                    "token": token,
                    "token_type": "Bearer",
                    "expires_in_seconds": args.expires_minutes * 60,
                    "workspace_id": args.workspace_id,
                    "user_id": args.user_id,
                },
                sort_keys=True,
            )
        )
    else:
        print(token)


def mint_report_token(
    *,
    workspace_id: str,
    user_id: str,
    secret_env: str,
    expires_minutes: int,
    environ: Mapping[str, str],
) -> str:
    if expires_minutes < 1:
        raise ValueError("expires_minutes must be at least 1")
    secret = environ.get(secret_env)
    if secret is None or not secret.strip():
        raise ValueError(f"{secret_env} must be set")
    from app.api.report_auth import create_report_identity_token

    return create_report_identity_token(
        workspace_id=UUID(workspace_id),
        user_id=UUID(user_id),
        secret=secret,
        expires_in=timedelta(minutes=expires_minutes),
    )


if __name__ == "__main__":
    main()
