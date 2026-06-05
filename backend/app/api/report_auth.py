from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

TOKEN_PREFIX = "land-dd-report-v1"
MIN_SECRET_LENGTH = 32
DEFAULT_TOKEN_TTL = timedelta(hours=1)


@dataclass(frozen=True)
class ReportIdentityClaims:
    workspace_id: UUID
    user_id: UUID


def create_report_identity_token(
    *,
    workspace_id: UUID,
    user_id: UUID,
    secret: str,
    expires_in: timedelta = DEFAULT_TOKEN_TTL,
    issued_at: datetime | None = None,
) -> str:
    _validate_secret(secret)
    if expires_in <= timedelta(0):
        raise ValueError("report identity token expiration must be in the future")
    now = issued_at or datetime.now(UTC)
    payload: dict[str, object] = {
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + expires_in).timestamp()),
    }
    payload_segment = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signed_part = f"{TOKEN_PREFIX}.{payload_segment}"
    signature = _sign(signed_part, secret)
    return f"{signed_part}.{signature}"


def verify_report_identity_token(
    token: str,
    *,
    secret: str,
    now: datetime | None = None,
) -> ReportIdentityClaims:
    _validate_secret(secret)
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != TOKEN_PREFIX:
        raise ValueError("invalid report identity token format")
    signed_part = f"{parts[0]}.{parts[1]}"
    expected_signature = _sign(signed_part, secret)
    if not hmac.compare_digest(parts[2], expected_signature):
        raise ValueError("invalid report identity token signature")
    payload = _decode_payload(parts[1])
    _enforce_expiration(payload, now or datetime.now(UTC))
    return ReportIdentityClaims(
        workspace_id=_required_uuid(payload, "workspace_id"),
        user_id=_required_uuid(payload, "user_id"),
    )


def _decode_payload(payload_segment: str) -> dict[str, object]:
    try:
        decoded = _base64url_decode(payload_segment)
        payload = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("invalid report identity token payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("invalid report identity token payload")
    return payload


def _enforce_expiration(payload: dict[str, object], now: datetime) -> None:
    expires_at = payload.get("exp")
    if expires_at is None:
        raise ValueError("report identity token expiration is required")
    if not isinstance(expires_at, int):
        raise ValueError("invalid report identity token expiration")
    if expires_at <= int(now.timestamp()):
        raise ValueError("report identity token expired")


def _required_uuid(payload: dict[str, object], field: str) -> UUID:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"report identity token missing {field}")
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError(f"report identity token has invalid {field}") from exc


def _sign(signed_part: str, secret: str) -> str:
    return _base64url_encode(
        hmac.new(secret.encode("utf-8"), signed_part.encode("utf-8"), hashlib.sha256).digest()
    )


def _validate_secret(secret: str) -> None:
    if len(secret.strip()) < MIN_SECRET_LENGTH:
        raise ValueError(
            f"report identity token secret must be at least {MIN_SECRET_LENGTH} characters"
        )


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _base64url_decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(f"{encoded}{padding}".encode("ascii"))


__all__ = [
    "DEFAULT_TOKEN_TTL",
    "MIN_SECRET_LENGTH",
    "ReportIdentityClaims",
    "create_report_identity_token",
    "verify_report_identity_token",
]
