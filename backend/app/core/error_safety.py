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
    "apikey",
    "authorization",
    "bearer ",
    "cookie",
    "credential",
    "database_url",
    "passwd",
    "password",
    "private_key",
    "privatekey",
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
    "/workspace/",
)
_SENSITIVE_PAYLOAD_KEY_MARKERS = (
    "api_key",
    "apikey",
    "accesstoken",
    "authorization",
    "cookie",
    "credential",
    "database_url",
    "passwd",
    "password",
    "private_key",
    "privatekey",
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
    """Return a credential-free, query-free summary of *url*.

    Guarantees:
    - Never raises to the caller (fails closed to REDACTED_ERROR_MESSAGE).
    - Strips userinfo from any URL that has a netloc (scheme-relative included).
    - Re-wraps IPv6 literal hosts in [...] so the output is re-parseable.
    - Routes the sanitised URL through safe_error_message so sensitive path
      segments and markers are still redacted.
    - Broadened: handles non-http(s) schemes (ftp, etc.) identically.
    """
    if url is None:
        return None
    stripped = url.strip()
    if not stripped:
        return None
    try:
        parsed = urlsplit(stripped)
    except ValueError:
        return REDACTED_ERROR_MESSAGE

    if parsed.netloc:
        # Fail closed on any port/hostname access error (malformed port, IPv6, …)
        try:
            hostname = parsed.hostname or ""
            port = parsed.port  # raises ValueError for non-numeric / out-of-range
        except ValueError:
            return REDACTED_ERROR_MESSAGE

        # Re-wrap IPv6 literal hosts (parsed.hostname strips the brackets).
        if ":" in hostname:
            host_part = f"[{hostname}]"
        else:
            host_part = hostname

        netloc_clean = f"{host_part}:{port}" if port else host_part
        clean_url = urlunsplit((parsed.scheme, netloc_clean, parsed.path, "", ""))
        return safe_error_message(clean_url)

    # No netloc: fall back to marker-checking the raw stripped value.
    # Guard against bare "user:pass@host" shapes leaking via the fallback.
    if "@" in stripped:
        return REDACTED_ERROR_MESSAGE
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
        # Route any URL-shaped value through safe_url_summary so userinfo and
        # query params are stripped regardless of scheme (ftp://, //host, etc.).
        if "://" in value or (value.startswith("//") and "@" in value):
            return safe_url_summary(value)
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
