from __future__ import annotations

from hashlib import sha256
from hmac import compare_digest
from string import hexdigits

SHA256_SECRET_PREFIX = "sha256:"
SHA256_HEX_LENGTH = 64


def normalize_secret_spec(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    if not cleaned.lower().startswith(SHA256_SECRET_PREFIX):
        return cleaned

    algorithm, digest = cleaned.split(":", 1)
    if algorithm != "sha256":
        raise ValueError(f"{field_name} hash prefix must be lowercase sha256:")
    normalized_digest = digest.lower()
    if len(normalized_digest) != SHA256_HEX_LENGTH or any(
        char not in hexdigits for char in normalized_digest
    ):
        raise ValueError(f"{field_name} sha256 digest must be 64 hex characters")
    return f"{SHA256_SECRET_PREFIX}{normalized_digest}"


def matches_secret_spec(provided: str, expected_spec: str) -> bool:
    if expected_spec.startswith(SHA256_SECRET_PREFIX):
        provided_digest = f"{SHA256_SECRET_PREFIX}{sha256(provided.encode('utf-8')).hexdigest()}"
        return compare_digest(provided_digest, expected_spec)
    return compare_digest(provided, expected_spec)


def matches_any_secret_spec(provided: str, expected_specs: frozenset[str]) -> bool:
    return any(matches_secret_spec(provided, expected) for expected in expected_specs)


__all__ = [
    "SHA256_SECRET_PREFIX",
    "matches_any_secret_spec",
    "matches_secret_spec",
    "normalize_secret_spec",
]
