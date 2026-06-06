from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

METRICS_SCHEMA_VERSION = "runtime_metrics_v1"


@dataclass
class _RouteMetric:
    method: str
    path: str
    requests_total: int = 0
    duration_total_ms: float = 0.0
    duration_max_ms: float = 0.0
    status_counts: dict[str, int] = field(default_factory=dict)

    def record(self, *, status_code: int, duration_ms: float) -> None:
        self.requests_total += 1
        self.duration_total_ms += duration_ms
        self.duration_max_ms = max(self.duration_max_ms, duration_ms)
        status_key = str(status_code)
        self.status_counts[status_key] = self.status_counts.get(status_key, 0) + 1

    def snapshot(self) -> dict[str, object]:
        average_duration = (
            self.duration_total_ms / self.requests_total if self.requests_total else 0.0
        )
        return {
            "method": self.method,
            "path": self.path,
            "requests_total": self.requests_total,
            "status_counts": dict(sorted(self.status_counts.items())),
            "duration_ms": {
                "total": round(self.duration_total_ms, 6),
                "avg": round(average_duration, 6),
                "max": round(self.duration_max_ms, 6),
            },
        }


class RuntimeMetrics:
    def __init__(self) -> None:
        self._started_at = perf_counter()
        self._lock = Lock()
        self._routes: dict[tuple[str, str], _RouteMetric] = {}

    def record_http_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        duration_ms = max(0.0, duration_seconds * 1000.0)
        key = (method.upper(), path)
        with self._lock:
            metric = self._routes.get(key)
            if metric is None:
                metric = _RouteMetric(method=key[0], path=key[1])
                self._routes[key] = metric
            metric.record(status_code=status_code, duration_ms=duration_ms)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            metrics = [
                metric
                for _, metric in sorted(
                    self._routes.items(),
                    key=lambda item: (item[0][1], item[0][0]),
                )
            ]
            requests_total = sum(metric.requests_total for metric in metrics)
            routes = [metric.snapshot() for metric in metrics]
        return {
            "schema_version": METRICS_SCHEMA_VERSION,
            "uptime_seconds": round(max(0.0, perf_counter() - self._started_at), 6),
            "http": {
                "requests_total": requests_total,
                "routes": routes,
            },
        }


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, metrics: RuntimeMetrics) -> None:
        super().__init__(app)
        self._metrics = metrics

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            self._metrics.record_http_request(
                method=request.method,
                path=_route_path(request),
                status_code=status_code,
                duration_seconds=perf_counter() - started_at,
            )


def _route_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str):
        return path
    return request.url.path
