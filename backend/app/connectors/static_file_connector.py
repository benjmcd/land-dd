from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from app.connectors.license_guard import check_connector_source_license
from app.connectors.observability import (
    ConnectorEventType,
    ConnectorObservabilityEvent,
    ConnectorRunObservabilityLog,
    new_observability_log,
)
from app.connectors.policy import DEFAULT_FIXTURE_POLICY, ConnectorPolicy
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import SourceContract, SourceRetrievalRunContract


def _utcnow() -> datetime:
    return datetime.now(UTC)


class StaticLocalFileConnectorError(ValueError):
    """Raised when the connector cannot load or validate a local fixture file."""


@dataclass(frozen=True)
class StaticLocalFileConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]
    observability_log: ConnectorRunObservabilityLog


class StaticLocalFileConnector:
    """Domain-agnostic connector that reads a local JSON fixture file.

    Used to demonstrate ConnectorPolicy + observability + license enforcement integration.
    Fixture format: {"retrieval_run": {...}, "evidence": [...]}
    """

    def __init__(
        self,
        *,
        source: SourceContract,
        policy: ConnectorPolicy = DEFAULT_FIXTURE_POLICY,
    ) -> None:
        self._source = source
        self._policy = policy

    def load(self, fixture_path: str | Path) -> StaticLocalFileConnectorResult:
        log = new_observability_log()
        ingest_run_id: UUID = self._source.source_id

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_started,
                connector_name="static_local_file",
                ingest_run_id=ingest_run_id,
                message=f"starting static local file connector for source {self._source.source_id}",
                timestamp=_utcnow(),
            )
        )

        try:
            check_connector_source_license(self._source)
        except Exception:
            log.record(
                ConnectorObservabilityEvent(
                    event_type=ConnectorEventType.run_failed,
                    connector_name="static_local_file",
                    ingest_run_id=ingest_run_id,
                    message=f"license check blocked connector run: {self._source.license_status}",
                    timestamp=_utcnow(),
                )
            )
            raise

        path = Path(fixture_path)
        if not path.is_file():
            log.record(
                ConnectorObservabilityEvent(
                    event_type=ConnectorEventType.run_failed,
                    connector_name="static_local_file",
                    ingest_run_id=ingest_run_id,
                    message=f"fixture file not found: {path}",
                    timestamp=_utcnow(),
                )
            )
            raise StaticLocalFileConnectorError(f"fixture file not found: {path}")

        payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        retrieval_run = SourceRetrievalRunContract.model_validate(
            payload.get("retrieval_run")
        )
        evidence_inputs = tuple(
            EvidenceContract.model_validate(item)
            for item in cast(list[dict[str, Any]], payload.get("evidence", []))
        )

        for ev in evidence_inputs:
            if ev.is_source_failure:
                log.record(
                    ConnectorObservabilityEvent(
                        event_type=ConnectorEventType.source_failure_stored,
                        connector_name="static_local_file",
                        ingest_run_id=ingest_run_id,
                        message=f"source failure evidence: {ev.evidence_id}",
                        timestamp=_utcnow(),
                    )
                )
            else:
                log.record(
                    ConnectorObservabilityEvent(
                        event_type=ConnectorEventType.evidence_stored,
                        connector_name="static_local_file",
                        ingest_run_id=ingest_run_id,
                        message=f"evidence stored: {ev.evidence_id}",
                        timestamp=_utcnow(),
                    )
                )

        log.record(
            ConnectorObservabilityEvent(
                event_type=ConnectorEventType.run_succeeded,
                connector_name="static_local_file",
                ingest_run_id=ingest_run_id,
                message=f"loaded {len(evidence_inputs)} evidence items from {path.name}",
                timestamp=_utcnow(),
            )
        )

        return StaticLocalFileConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=evidence_inputs,
            observability_log=log,
        )


__all__ = [
    "StaticLocalFileConnector",
    "StaticLocalFileConnectorError",
    "StaticLocalFileConnectorResult",
]
