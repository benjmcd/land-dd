from __future__ import annotations

from collections.abc import Iterable, Mapping
from urllib.parse import urlsplit, urlunsplit

REDACTED_ERROR_MESSAGE = (
    "Failure details withheld from user-facing surfaces; inspect source evidence or "
    "internal logs."
)

_SENSITIVE_ERROR_MARKERS = (
    "traceback (most recent call last)",
    'file "',
    "api_key",
    "authorization",
    "bearer ",
    "cookie",
    "database_url",
    "password",
    "raw_payload",
    "secret",
    "token",
    "x-api-key",
)
_LOCAL_PATH_MARKERS = (
    ":\\",
    "\\\\?\\",
    "/app/",
    "/home/",
    "/users/",
)
_SENSITIVE_PAYLOAD_KEY_MARKERS = (
    "api_key",
    "authorization",
    "cookie",
    "database_url",
    "password",
    "raw_payload",
    "secret",
    "token",
    "x-api-key",
)


def safe_error_message(message: str | None) -> str | None:
    if message is None:
        return None
    stripped = message.strip()
    if not stripped:
        return None
    lowered = stripped.lower()
    if (
        "\n" in stripped
        or "\r" in stripped
        or stripped[0] in "{[<"
        or any(marker in lowered for marker in _SENSITIVE_ERROR_MARKERS)
        or any(marker in lowered for marker in _LOCAL_PATH_MARKERS)
    ):
        return REDACTED_ERROR_MESSAGE
    if len(stripped) > 240:
        return f"{stripped[:237]}..."
    return stripped


def safe_url_summary(url: str | None) -> str | None:
    if url is None:
        return None
    stripped = url.strip()
    if not stripped:
        return None
    parsed = urlsplit(stripped)
    if parsed.scheme and parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    return safe_error_message(stripped)


def safe_payload_summary(
    payload: Mapping[str, object],
    *,
    allowed_keys: Iterable[str],
) -> dict[str, object]:
    summary: dict[str, object] = {}
    for key in allowed_keys:
        if key not in payload:
            continue
        value = _safe_payload_value(payload[key])
        if value is not None:
            summary[key] = value
    return summary


def safe_payload_copy(payload: Mapping[str, object]) -> dict[str, object]:
    summary: dict[str, object] = {}
    for key, value in payload.items():
        if _is_sensitive_payload_key(key):
            continue
        safe_value = _safe_payload_value(value)
        if safe_value is not None:
            summary[str(key)] = safe_value
    return summary


def _safe_payload_value(value: object) -> object | None:
    if value is None or isinstance(value, int | float | bool):
        return value
    if isinstance(value, str):
        return safe_error_message(value)
    if isinstance(value, Mapping):
        return safe_payload_copy(value)
    if isinstance(value, list | tuple):
        return [
            safe_item
            for item in value
            if (safe_item := _safe_payload_value(item)) is not None
        ]
    return None


def _is_sensitive_payload_key(key: object) -> bool:
    lowered = str(key).lower()
    return any(marker in lowered for marker in _SENSITIVE_PAYLOAD_KEY_MARKERS)


__all__ = [
    "REDACTED_ERROR_MESSAGE",
    "safe_error_message",
    "safe_payload_copy",
    "safe_payload_summary",
    "safe_url_summary",
]
