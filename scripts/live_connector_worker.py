from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))

from app.api.dependencies import create_db_api_services  # noqa: E402
from app.api.live_connector_jobs import (  # noqa: E402
    LiveConnectorJobRunResult,
    run_next_live_connector_job,
)
from app.core.config import Settings  # noqa: E402
from app.db.engine import get_session_factory  # noqa: E402


@dataclass(frozen=True)
class LiveConnectorWorkerSummary:
    processed: int
    succeeded: int
    failed: int
    idle: bool
    job_ids: tuple[str, ...]
    failed_job_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "processed": self.processed,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "idle": self.idle,
            "job_ids": list(self.job_ids),
            "failed_job_ids": list(self.failed_job_ids),
        }


SessionFactory = Callable[[], Any]
ServiceFactory = Callable[..., Any]
JobRunner = Callable[..., LiveConnectorJobRunResult | None]
SleepFunc = Callable[[float], None]


def run_live_connector_worker(
    *,
    worker_id: str,
    max_jobs: int,
    settings: Settings | None = None,
    object_store_root: str | Path | None = None,
    session_factory: SessionFactory | None = None,
    service_factory: ServiceFactory = create_db_api_services,
    job_runner: JobRunner = run_next_live_connector_job,
) -> LiveConnectorWorkerSummary:
    if not worker_id.strip():
        raise ValueError("worker_id is required")
    if max_jobs < 1:
        raise ValueError("max_jobs must be at least 1")

    resolved_settings = settings or Settings()
    resolved_object_store_root = object_store_root or resolved_settings.object_store_root
    resolved_session_factory = session_factory or get_session_factory()

    job_ids: list[str] = []
    failed_job_ids: list[str] = []
    succeeded = 0
    failed = 0
    idle = False

    for _ in range(max_jobs):
        with resolved_session_factory() as session:
            services = service_factory(
                session,
                object_store_root=resolved_object_store_root,
                settings=resolved_settings,
            )
            result = job_runner(services=services, worker_id=worker_id.strip())
            if result is None:
                idle = True
                break
            session.commit()

        job_id = str(result.job.job_id)
        job_ids.append(job_id)
        if result.succeeded:
            succeeded += 1
        else:
            failed += 1
            failed_job_ids.append(job_id)

    return LiveConnectorWorkerSummary(
        processed=len(job_ids),
        succeeded=succeeded,
        failed=failed,
        idle=idle,
        job_ids=tuple(job_ids),
        failed_job_ids=tuple(failed_job_ids),
    )


def run_live_connector_worker_loop(
    *,
    worker_id: str,
    max_jobs: int,
    poll_seconds: float,
    idle_polls: int | None,
    settings: Settings | None = None,
    object_store_root: str | Path | None = None,
    session_factory: SessionFactory | None = None,
    service_factory: ServiceFactory = create_db_api_services,
    job_runner: JobRunner = run_next_live_connector_job,
    sleep_func: SleepFunc = time.sleep,
) -> LiveConnectorWorkerSummary:
    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be positive")
    if idle_polls is not None and idle_polls < 1:
        raise ValueError("idle_polls must be at least 1 when bounded")

    processed = 0
    succeeded = 0
    failed = 0
    job_ids: list[str] = []
    failed_job_ids: list[str] = []
    consecutive_idle = 0
    last_idle = False

    while True:
        summary = run_live_connector_worker(
            worker_id=worker_id,
            max_jobs=max_jobs,
            settings=settings,
            object_store_root=object_store_root,
            session_factory=session_factory,
            service_factory=service_factory,
            job_runner=job_runner,
        )
        processed += summary.processed
        succeeded += summary.succeeded
        failed += summary.failed
        job_ids.extend(summary.job_ids)
        failed_job_ids.extend(summary.failed_job_ids)
        last_idle = summary.idle

        if summary.failed:
            break
        if summary.idle:
            consecutive_idle += 1
            if idle_polls is not None and consecutive_idle >= idle_polls:
                break
        else:
            consecutive_idle = 0
        if poll_seconds:
            sleep_func(poll_seconds)

    return LiveConnectorWorkerSummary(
        processed=processed,
        succeeded=succeeded,
        failed=failed,
        idle=last_idle,
        job_ids=tuple(job_ids),
        failed_job_ids=tuple(failed_job_ids),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Process queued DS-001, DS-002, DS-003, and DS-004 live connector jobs "
            "from jobs.job_queue. "
            "The worker does not schedule reports or bypass connector review."
        )
    )
    parser.add_argument(
        "--worker-id",
        default=_default_worker_id(),
        help="Non-empty worker identifier stored on leased live connector jobs.",
    )
    parser.add_argument(
        "--max-jobs",
        type=_positive_int,
        default=1,
        help="Maximum jobs to process before exiting. Defaults to one bounded job.",
    )
    parser.add_argument(
        "--object-store-root",
        default=None,
        help="Report object-store root used while constructing DB-backed services.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=_positive_float,
        default=None,
        help=(
            "Enable polling mode and sleep this many seconds between polls. "
            "Omit for the default one-shot worker behavior."
        ),
    )
    parser.add_argument(
        "--idle-polls",
        type=_non_negative_int,
        default=0,
        help=(
            "Polling mode only. Exit after this many consecutive idle polls. "
            "Use 0 for unbounded supervisor mode."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of a compact text line.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.poll_seconds is None:
            summary = run_live_connector_worker(
                worker_id=args.worker_id,
                max_jobs=args.max_jobs,
                object_store_root=args.object_store_root,
            )
        else:
            summary = run_live_connector_worker_loop(
                worker_id=args.worker_id,
                max_jobs=args.max_jobs,
                poll_seconds=args.poll_seconds,
                idle_polls=None if args.idle_polls == 0 else args.idle_polls,
                object_store_root=args.object_store_root,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"live connector worker failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary.as_dict(), sort_keys=True))
    else:
        print(
            "live connector worker: "
            f"processed={summary.processed} "
            f"succeeded={summary.succeeded} "
            f"failed={summary.failed} "
            f"idle={str(summary.idle).lower()}"
        )
    return 1 if summary.failed else 0


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _default_worker_id() -> str:
    return f"live-connector-worker:{socket.gethostname()}:{os.getpid()}"


if __name__ == "__main__":
    raise SystemExit(main())
