from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from app.area_geometry.service import AreaService
from app.claims_engine.not_evaluated import (
    NOT_EVALUATED_DOMAINS,
    NOT_EVALUATED_SOURCE_NAME,
    NOT_EVALUATED_SOURCE_ORG,
    make_not_evaluated_source_failure,
)
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, IntentCode, JobStatus, ReportReviewStatus, SeverityBand
from app.domain.evidence_contracts import EvidenceContract
from app.domain.report_contracts import ReportRunContract
from app.domain.source_contracts import SourceContract
from app.evidence_ledger.service import EvidenceService
from app.reports.report_repo import InMemoryReportRunRepository, ReportRunRepository
from app.source_registry.service import SourceService
from app.source_registry.usage_rights import source_report_exposure_allowed

_ZONING_RULE_CODE = "ZONING_G001"
_ZONING_UNKNOWN_CLAIM_CODE = "ZONING_SOURCE_UNAVAILABLE_UNKNOWN"
_ZONING_SENTINEL_CAVEAT = (
    "No zoning source data was available for this area. "
    "Zoning use classification requires verification with the "
    "relevant county planning or zoning authority."
)
_ZONING_SENTINEL_VERIFICATION_TASK = (
    "Call county planning and verify permitted uses, overlays, and minimum lot size."
)
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
_NOT_EVALUATED_SOURCE_ID = UUID("00000000-0000-4000-8000-0000000007d0")
_SOURCE_APPROVED_STATUSES = frozenset({
    "approved",
    "approved_with_restrictions",
    "approved-with-restrictions",
})


class ConnectorReviewQueueItemProtocol(Protocol):
    @property
    def status(self) -> JobStatus: ...

    @property
    def payload(self) -> Mapping[str, object]: ...


class ConnectorReviewQueueProtocol(Protocol):
    def get_by_ingest_run_id(
        self,
        ingest_run_id: UUID,
    ) -> ConnectorReviewQueueItemProtocol | None: ...


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
        connector_review_queue: ConnectorReviewQueueProtocol | None = None,
    ) -> None:
        self._source_service = source_service
        self._area_service = area_service
        self._evidence_service = evidence_service
        self._claim_service = claim_service
        self._rule_engine = rule_engine
        self._report_repo = report_repo or InMemoryReportRunRepository()
        self._connector_review_queue = connector_review_queue

    def create_report_run(
        self,
        *,
        area_id: UUID,
        intent_code: IntentCode,
        report_run_id: UUID | None = None,
        workspace_id: UUID | None = None,
        requested_by: UUID | None = None,
    ) -> ReportRunContract:
        _require_non_empty(intent_code, "intent_code")
        if not self._area_service.area_is_registered(area_id):
            raise ValueError(f"Area '{area_id}' is not registered")

        evidence = self._with_not_evaluated_source_failures(
            area_id,
            self._approved_report_evidence(self._evidence_service.list_by_area(area_id)),
        )
        # Exclude our own sentinel from rule engine input — sentinel evidence would
        # trigger _zoning_unknown_claim at zoning's position in evaluate(), producing
        # the claim before flood claims. We always append it last ourselves below.
        rule_evidence = [e for e in evidence if not _is_zoning_sentinel(e)]
        stored_claims = [
            self._store_claim_if_needed(claim)
            for claim in self._rule_engine.evaluate(rule_evidence)
        ]
        evidence, stored_claims = self._with_zoning_sentinel_if_missing(
            area_id, evidence, stored_claims
        )
        report_run = ReportRunContract(
            report_run_id=report_run_id if report_run_id is not None else uuid4(),
            workspace_id=workspace_id,
            requested_by=requested_by,
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
            advisory_claims=_advisory_claims(stored_claims),
            verification_tasks=_verification_tasks(stored_claims),
            artifact_metadata={
                "artifact_kind": "report_run",
                "report_schema": "report_run_contract_v1",
                "validation": _validation_metadata(self._rule_engine),
                "cost_metrics": _cost_metrics(evidence, stored_claims),
            },
            finished_at=datetime.now(UTC),
        )
        return self._report_repo.add(report_run)

    def get_report_run(self, report_run_id: UUID) -> ReportRunContract | None:
        return self._report_repo.get(report_run_id)

    def get_report_run_for_workspace(
        self,
        report_run_id: UUID,
        workspace_id: UUID,
    ) -> ReportRunContract | None:
        return self._report_repo.get_for_workspace(report_run_id, workspace_id)

    def approve_report_run(
        self,
        report_run_id: UUID,
        *,
        reviewer_id: str,
        reason: str | None = None,
    ) -> ReportRunContract | None:
        return self._report_repo.update_review_status(
            report_run_id,
            new_status=ReportReviewStatus.APPROVED,
            reviewer_id=reviewer_id,
            reason=reason,
        )

    def _with_not_evaluated_source_failures(
        self,
        area_id: UUID,
        evidence: list[EvidenceContract],
    ) -> list[EvidenceContract]:
        missing_domains = [
            domain
            for domain in NOT_EVALUATED_DOMAINS
            if not any(record.domain == domain for record in evidence)
        ]
        if not missing_domains:
            return evidence

        source = self._ensure_not_evaluated_source()
        enriched_evidence = list(evidence)
        for domain in missing_domains:
            failure = make_not_evaluated_source_failure(
                area_id=area_id,
                source_id=source.source_id,
                domain=domain,
            )
            enriched_evidence.append(
                self._evidence_service.create_source_failure(
                    area_id=failure.area_id,
                    source_id=failure.source_id,
                    method_code=failure.method_code,
                    caveat=failure.caveat or "",
                    evidence_code=failure.evidence_code,
                    domain=failure.domain,
                    observation=failure.observation,
                    observed_value=_not_evaluated_failure_payload(failure),
                )
            )
        return enriched_evidence

    def _with_zoning_sentinel_if_missing(
        self,
        area_id: UUID,
        evidence: list[EvidenceContract],
        claims: list[ClaimContract],
    ) -> tuple[list[EvidenceContract], list[ClaimContract]]:
        # Real zoning evidence (non-sentinel) means the rule engine evaluated zoning.
        if any(
            record.domain == "zoning" and not _is_zoning_sentinel(record) for record in evidence
        ):
            return evidence, claims

        existing_sentinel = next(
            (record for record in evidence if _is_zoning_sentinel(record)), None
        )
        source = self._ensure_not_evaluated_source()
        if existing_sentinel is None:
            sentinel = self._evidence_service.create_source_failure(
                area_id=area_id,
                source_id=source.source_id,
                method_code="zoning_not_screened",
                caveat=_ZONING_SENTINEL_CAVEAT,
                evidence_code="ZONING_NOT_SCREENED",
                domain="zoning",
                observation=(
                    "Zoning screening was not performed; "
                    "no zoning source was connected for this report run."
                ),
                observed_value={"failure_reason": "zoning_not_screened"},
            )
            new_evidence = [*evidence, sentinel]
        else:
            sentinel = existing_sentinel
            new_evidence = evidence

        claim = self._store_claim_if_needed(
            ClaimContract(
                claim_id=_zoning_sentinel_claim_id(
                    ruleset_id=self._rule_engine.ruleset_id,
                    ruleset_version=self._rule_engine.ruleset_version,
                    area_id=area_id,
                    evidence_id=sentinel.evidence_id,
                ),
                area_id=area_id,
                claim_code=_ZONING_UNKNOWN_CLAIM_CODE,
                domain="zoning",
                assertion="Zoning source data could not be evaluated for this area.",
                user_safe_language=(
                    "Zoning/use screening remains unknown because required zoning source "
                    "evidence failed or was unavailable. This does not establish legal use, "
                    "zoning compliance, permit eligibility, or buildability."
                ),
                severity=SeverityBand.UNKNOWN,
                confidence=ConfidenceBand.UNKNOWN,
                evidence_ids=[sentinel.evidence_id],
                rule_code=_ZONING_RULE_CODE,
                ruleset_id=self._rule_engine.ruleset_id,
                ruleset_version=self._rule_engine.ruleset_version,
                verification_required=True,
                verification_task=_ZONING_SENTINEL_VERIFICATION_TASK,
            )
        )
        return new_evidence, [*claims, claim]

    def _ensure_not_evaluated_source(self) -> SourceContract:
        existing = self._source_service.get(_NOT_EVALUATED_SOURCE_ID)
        if existing is not None:
            return existing
        return self._source_service.get_or_register_by_id(
            SourceContract(
                source_id=_NOT_EVALUATED_SOURCE_ID,
                name=NOT_EVALUATED_SOURCE_NAME,
                organization=NOT_EVALUATED_SOURCE_ORG,
                source_type="internal_sentinel",
                domain="unsupported_screening_categories",
                license_status="approved",
                commercial_use_status="approved",
                redistribution_status="approved",
                cache_allowed="approved",
                export_allowed="approved",
                raw_data_allowed="approved",
                ai_use_allowed="approved",
                review_status="approved",
                notes=(
                    "Internal sentinel source for MVP screening categories that "
                    "are intentionally not evaluated."
                ),
                metadata={"source_role": "unsupported_category_sentinel"},
            )
        )

    def _approved_report_evidence(
        self,
        evidence: list[EvidenceContract],
    ) -> list[EvidenceContract]:
        return [
            record
            for record in evidence
            if self._is_report_approved_evidence(record)
        ]

    def _is_report_approved_evidence(self, evidence: EvidenceContract) -> bool:
        source = self._source_service.get(evidence.source_id)
        if source is None:
            return False
        if not source_report_exposure_allowed(source, evidence):
            return False
        if evidence.source_ingest_run_id is None:
            return True
        if source.review_status not in _SOURCE_APPROVED_STATUSES:
            return False
        if self._connector_review_queue is None:
            return False
        item = self._connector_review_queue.get_by_ingest_run_id(
            evidence.source_ingest_run_id,
        )
        if item is None or item.status != JobStatus.SUCCEEDED:
            return False
        decision = item.payload.get("review_decision")
        if not isinstance(decision, dict):
            return False
        return decision.get("action") == "approve_for_connector_qa"

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
        registered_sources = [self._source_service.get(record.source_id) for record in evidence]
        registered_sources_by_id = {
            source.source_id: source for source in registered_sources if source is not None
        }
        source_details = sorted(
            [
                {
                    "source_id": str(source.source_id),
                    "name": source.name,
                    "authority_level": source.authority_level.value,
                    "license_status": source.license_status,
                    "commercial_use_status": source.commercial_use_status,
                    "redistribution_status": source.redistribution_status,
                    "cache_allowed": source.cache_allowed,
                    "export_allowed": source.export_allowed,
                    "raw_data_allowed": source.raw_data_allowed,
                    "ai_use_allowed": source.ai_use_allowed,
                    "freshness_class": source.freshness_class,
                    "review_status": source.review_status,
                    "review_owner": source.review_owner,
                    "last_checked_at": source.last_checked_at,
                    "homepage_url": str(source.homepage_url) if source.homepage_url else None,
                }
                for source in registered_sources_by_id.values()
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
            "source_names": sorted({source.name for source in registered_sources_by_id.values()}),
            "source_details": source_details,
        }


def _unknown_claims(claims: list[ClaimContract]) -> list[ClaimContract]:
    return [claim for claim in claims if claim.severity == SeverityBand.UNKNOWN]


def _red_flag_claims(claims: list[ClaimContract]) -> list[ClaimContract]:
    return [
        claim for claim in claims if claim.severity in {SeverityBand.CRITICAL, SeverityBand.HIGH}
    ]


def _advisory_claims(claims: list[ClaimContract]) -> list[ClaimContract]:
    return [claim for claim in claims if claim.severity == SeverityBand.LOW]


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
        "advisory_count": len(_advisory_claims(claims)),
        "red_flag_count": len(_red_flag_claims(claims)),
        "verification_task_count": len(_verification_tasks(claims)),
        "estimated_total_usd_cents": 0,
        "compute_usd_cents": 0,
        "storage_usd_cents": 0,
        "llm_usd_cents": 0,
        "map_tile_usd_cents": 0,
        "geocoding_usd_cents": 0,
        "paid_data_usd_cents": 0,
        "human_review_usd_cents": 0,
        "human_review_minutes": 0,
    }


def _validation_metadata(rule_engine: RuleEngine) -> dict[str, str]:
    return {
        "contract_name": "ReportRunContract",
        "contract_version": "report_run_contract_v1",
        "validation_profile": "fixture_report_contract_v1",
        "ruleset_id": rule_engine.ruleset_id,
        "ruleset_version": rule_engine.ruleset_version,
    }


def _not_evaluated_failure_payload(evidence: EvidenceContract) -> dict[str, object]:
    reason = evidence.observed_value.get("failure_reason") or evidence.observed_value.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        reason = "unsupported_screening_domain"
    return {"failure_reason": reason.strip()}


def _is_zoning_sentinel(evidence: EvidenceContract) -> bool:
    return evidence.domain == "zoning" and evidence.evidence_code == "ZONING_NOT_SCREENED"


def _zoning_sentinel_claim_id(
    *,
    ruleset_id: str,
    ruleset_version: str,
    area_id: UUID,
    evidence_id: UUID,
) -> UUID:
    seed = "|".join([
        "land-dd-claim",
        ruleset_id,
        ruleset_version,
        _ZONING_RULE_CODE,
        "unknown",
        str(area_id),
        str(evidence_id),
    ])
    return uuid5(NAMESPACE_URL, seed)


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


__all__ = ["ReportRunService"]
