from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import ceil
from threading import Lock
from time import monotonic

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

API_KEY_HEADER = "X-API-Key"
PUBLIC_PATHS = frozenset({"/health", "/version"})


@dataclass(frozen=True)
class RateLimitConfig:
    enabled: bool
    max_requests: int
    window_seconds: int


@dataclass
class _RateLimitBucket:
    count: int
    reset_at: float


@dataclass(frozen=True)
class _RateLimitDecision:
    allowed: bool
    remaining: int
    reset_seconds: int


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, config: RateLimitConfig) -> None:
        super().__init__(app)
        if config.enabled and config.max_requests < 1:
            raise ValueError("rate limit max_requests must be at least 1")
        if config.enabled and config.window_seconds < 1:
            raise ValueError("rate limit window_seconds must be at least 1")
        self._config = config
        self._buckets: dict[str, _RateLimitBucket] = {}
        self._lock = Lock()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if (
            not self._config.enabled
            or request.scope["type"] != "http"
            or request.url.path in PUBLIC_PATHS
        ):
            return await call_next(request)

        decision = self._decide(_identity_key(request), monotonic())
        if not decision.allowed:
            return JSONResponse(
                {"detail": "rate limit exceeded"},
                status_code=429,
                headers=_rate_limit_headers(
                    limit=self._config.max_requests,
                    remaining=decision.remaining,
                    reset_seconds=decision.reset_seconds,
                    include_retry_after=True,
                ),
            )

        response = await call_next(request)
        for name, value in _rate_limit_headers(
            limit=self._config.max_requests,
            remaining=decision.remaining,
            reset_seconds=decision.reset_seconds,
            include_retry_after=False,
        ).items():
            response.headers[name] = value
        return response

    def _decide(self, identity: str, now: float) -> _RateLimitDecision:
        with self._lock:
            self._prune_expired(now)
            bucket = self._buckets.get(identity)
            if bucket is None or bucket.reset_at <= now:
                bucket = _RateLimitBucket(
                    count=0,
                    reset_at=now + self._config.window_seconds,
                )
                self._buckets[identity] = bucket

            reset_seconds = max(1, ceil(bucket.reset_at - now))
            if bucket.count >= self._config.max_requests:
                return _RateLimitDecision(
                    allowed=False,
                    remaining=0,
                    reset_seconds=reset_seconds,
                )

            bucket.count += 1
            return _RateLimitDecision(
                allowed=True,
                remaining=self._config.max_requests - bucket.count,
                reset_seconds=reset_seconds,
            )

    def _prune_expired(self, now: float) -> None:
        expired = [identity for identity, bucket in self._buckets.items() if bucket.reset_at <= now]
        for identity in expired:
            del self._buckets[identity]


def _identity_key(request: Request) -> str:
    api_key = _clean_header(request.headers.get(API_KEY_HEADER))
    if api_key is not None:
        digest = sha256(api_key.encode("utf-8")).hexdigest()
        return f"api-key:{digest}"
    if request.client is not None and request.client.host:
        return f"client:{request.client.host}"
    return "client:unknown"


def _clean_header(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _rate_limit_headers(
    *,
    limit: int,
    remaining: int,
    reset_seconds: int,
    include_retry_after: bool,
) -> dict[str, str]:
    headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_seconds),
    }
    if include_retry_after:
        headers["Retry-After"] = str(reset_seconds)
    return headers
