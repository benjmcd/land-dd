from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from app.domain.enums import EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)


class FixtureConnectorError(ValueError):
    """Raised when a connector fixture violates the connector contract."""


@dataclass(frozen=True)
class FloodFixtureConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]


class StaticFloodFixtureConnector:
    connector_name = "fixture_flood_static"
    domain = "flood"

    def load_fixture(self, fixture_path: str | Path) -> FloodFixtureConnectorResult:
        path = self._local_fixture_path(fixture_path)
        payload = cast(
            dict[str, Any],
            json.loads(path.read_text(encoding="utf-8")),
        )

        retrieval_run = SourceRetrievalRunContract.model_validate(
            payload.get("retrieval_run"),
        )
        evidence_inputs = tuple(
            EvidenceContract.model_validate(item)
            for item in cast(list[dict[str, Any]], payload.get("evidence", []))
        )

        self._validate_result(retrieval_run, evidence_inputs)
        return FloodFixtureConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=evidence_inputs,
        )

    def _local_fixture_path(self, fixture_path: str | Path) -> Path:
        raw_path = str(fixture_path)
        if "://" in raw_path:
            raise FixtureConnectorError("connector fixtures must be local file paths")

        path = Path(fixture_path)
        if not path.is_file():
            raise FixtureConnectorError(f"connector fixture does not exist: {path}")
        return path

    def _validate_result(
        self,
        retrieval_run: SourceRetrievalRunContract,
        evidence_inputs: tuple[EvidenceContract, ...],
    ) -> None:
        if retrieval_run.connector_name != self.connector_name:
            raise FixtureConnectorError("retrieval run connector_name mismatch")
        if not evidence_inputs:
            raise FixtureConnectorError("connector fixture must emit evidence inputs")

        for evidence in evidence_inputs:
            if evidence.domain != self.domain:
                raise FixtureConnectorError("flood connector emitted non-flood evidence")

        if retrieval_run.status == SourceRetrievalStatus.SUCCEEDED:
            if not any(
                evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
                and not evidence.is_source_failure
                for evidence in evidence_inputs
            ):
                raise FixtureConnectorError(
                    "successful flood fixture must emit spatial evidence",
                )
            return

        if retrieval_run.status in {
            SourceRetrievalStatus.FAILED,
            SourceRetrievalStatus.BLOCKED,
        }:
            if not any(
                evidence.evidence_type == EvidenceType.SOURCE_FAILURE
                and evidence.is_source_failure
                for evidence in evidence_inputs
            ):
                raise FixtureConnectorError(
                    "failed or blocked flood fixture must emit source-failure evidence",
                )
            return

        raise FixtureConnectorError(
            "flood fixture retrieval status must be succeeded, failed, or blocked",
        )
