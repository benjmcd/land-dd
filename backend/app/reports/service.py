from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from app.area_geometry.service import AreaService
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.domain.claim_contracts import ClaimContract
from app.domain.enums import IntentCode, JobStatus, SeverityBand
from app.domain.evidence_contracts import EvidenceContract
from app.domain.report_contracts import ReportRunContract
from app.evidence_ledger.service import EvidenceService
from app.reports.report_repo import InMemoryReportRunRepository, ReportRunRepository
from app.source_registry.service import SourceService

_REPORT_ASSUMPTIONS = [
    (
        "Fixture-backed screening output; not a legal, title, insurance, "
        "lending, or investment conclusion."
    ),
    (
        "Report output is reproducible only within the recorded fixture "
        "source and ruleset versions."
    ),
]
_NO_EVIDENCE_CAVEAT = (
    "No evidence records were available for this area; report contains no "
    "due-diligence findings."
)


class ReportRunService:
    def __init__(
        self,
        *,
        source_service: SourceService,
        area_service: AreaService,
        evidence_service: EvidenceService,
        claim_service: ClaimService,
        rule_engine: RuleEngine,
        report_repo: ReportRunRepository | None = None,
    ) -> None:
        self._source_service = source_service
        self._area_service = area_service
        self._evidence_service = evidence_service
        self._claim_service = claim_service
        self._rule_engine = rule_engine
        self._report_repo = report_repo or InMemoryReportRunRepository()

    def create_report_run(
        self,
        *,
        area_id: UUID,
        intent_code: IntentCode,
    ) -> ReportRunContract:
        _require_non_empty(intent_code, "intent_code")
        if not self._area_service.area_is_registered(area_id):
            raise ValueError(f"Area '{area_id}' is not registered")

        evidence = self._evidence_service.list_by_area(area_id)
        stored_claims = [
            self._store_claim_if_needed(claim)
            for claim in self._rule_engine.evaluate(evidence)
        ]
        report_run = ReportRunContract(
            area_id=area_id,
            intent_code=intent_code,
            status=JobStatus.SUCCEEDED,
            source_manifest=self._source_manifest(evidence, stored_claims),
            assumptions=list(_REPORT_ASSUMPTIONS),
            caveats=_report_caveats(evidence),
            evidence=evidence,
            claims=stored_claims,
            unknowns=_unknown_claims(stored_claims),
            red_flags=_red_flag_claims(stored_claims),
            verification_tasks=_verification_tasks(stored_claims),
            artifact_metadata={
                "artifact_kind": "report_run",
                "report_schema": "report_run_contract_v1",
                "cost_metrics": _cost_metrics(evidence, stored_claims),
            },
            finished_at=datetime.now(UTC),
        )
        return self._report_repo.add(report_run)

    def get_report_run(self, report_run_id: UUID) -> ReportRunContract | None:
        return self._report_repo.get(report_run_id)

    def _store_claim_if_needed(self, claim: ClaimContract) -> ClaimContract:
        existing = self._claim_service.get(claim.claim_id)
        if existing is not None:
            return existing
        return self._claim_service.create_claim(claim, claim.evidence_ids)

    def _source_manifest(
        self,
        evidence: list[EvidenceContract],
        claims: list[ClaimContract],
    ) -> dict[str, object]:
        source_ids = sorted({str(record.source_id) for record in evidence})
        registered_sources = [
            self._source_service.get(record.source_id)
            for record in evidence
        ]
        source_details = sorted(
            [
                {
                    "source_id": str(source.source_id),
                    "name": source.name,
                    "authority_level": source.authority_level.value,
                    "license_status": source.license_status,
                    "commercial_use_status": source.commercial_use_status,
                    "freshness_class": source.freshness_class,
                    "review_status": source.review_status,
                    "review_owner": source.review_owner,
                    "last_checked_at": source.last_checked_at,
                }
                for source in registered_sources
                if source is not None
            ],
            key=lambda detail: cast(str, detail["source_id"]),
        )
        return {
            "source_ids": source_ids,
            "source_count": len(source_ids),
            "evidence_count": len(evidence),
            "claim_count": len(claims),
            "ruleset_id": self._rule_engine.ruleset_id,
            "ruleset_version": self._rule_engine.ruleset_version,
            "source_names": sorted(
                {
                    source.name
                    for source in registered_sources
                    if source is not None
                }
            ),
            "source_details": source_details,
        }


def _unknown_claims(claims: list[ClaimContract]) -> list[ClaimContract]:
    return [claim for claim in claims if claim.severity == SeverityBand.UNKNOWN]


def _red_flag_claims(claims: list[ClaimContract]) -> list[ClaimContract]:
    return [
        claim
        for claim in claims
        if claim.severity in {SeverityBand.CRITICAL, SeverityBand.HIGH}
    ]


def _verification_tasks(claims: list[ClaimContract]) -> list[str]:
    return sorted(
        {
            claim.verification_task.strip()
            for claim in claims
            if claim.verification_required
            and claim.verification_task is not None
            and claim.verification_task.strip()
        }
    )


def _unique_caveats(evidence: list[EvidenceContract]) -> list[str]:
    return sorted(
        {
            record.caveat.strip()
            for record in evidence
            if record.caveat is not None and record.caveat.strip()
        }
    )


def _report_caveats(evidence: list[EvidenceContract]) -> list[str]:
    caveats = _unique_caveats(evidence)
    if not evidence:
        return [_NO_EVIDENCE_CAVEAT]
    return caveats


def _cost_metrics(
    evidence: list[EvidenceContract],
    claims: list[ClaimContract],
) -> dict[str, int]:
    return {
        "evidence_count": len(evidence),
        "claim_count": len(claims),
        "unknown_count": len(_unknown_claims(claims)),
        "red_flag_count": len(_red_flag_claims(claims)),
        "verification_task_count": len(_verification_tasks(claims)),
    }


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


__all__ = ["ReportRunService"]
