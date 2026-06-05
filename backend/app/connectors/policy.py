from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorPolicy:
    """Rate-limit, timeout, and retry policy for a connector run.

    All numeric fields must be non-negative. Zero means "no limit" or "no retry".
    """
    rate_limit_per_minute: int = 0
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0

    def __post_init__(self) -> None:
        if self.rate_limit_per_minute < 0:
            raise ValueError("rate_limit_per_minute must be >= 0")
        if self.timeout_seconds < 0:
            raise ValueError("timeout_seconds must be >= 0")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds must be >= 0")


DEFAULT_FIXTURE_POLICY = ConnectorPolicy(
    rate_limit_per_minute=0,
    timeout_seconds=5.0,
    max_retries=0,
    retry_backoff_seconds=0.0,
)

__all__ = ["ConnectorPolicy", "DEFAULT_FIXTURE_POLICY"]
