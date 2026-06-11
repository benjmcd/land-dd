from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid5

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)

CHATHAM_ZONING_CONNECTOR_NAME = "chatham_zoning_udo_recorded"
CHATHAM_ZONING_METHOD_CODE = "chatham_udo_district_lookup"
CHATHAM_ZONING_METHOD_VERSION = "0.1.0"
CHATHAM_ZONING_UDO_URL = (
    "https://www.chathamcountync.gov/government/departments-programs-i-z/"
    "planning/special-topics/udo-unified-development-ordinance"
)
CHATHAM_ZONING_UDO_ADOPTED = "2024-11-18"
CHATHAM_ZONING_UDO_EFFECTIVE = "2025-07-01"
CHATHAM_ZONING_CAVEAT = (
    "Chatham County UDO district classification — screening only. "
    "Zoning code is sourced from county parcel/CAMA data. "
    "UDO text context is a human-reviewed recorded snapshot effective 2025-07-01. "
    "Does not constitute a zoning compliance determination, permitted-use decision, "
    "entitlement, permit eligibility finding, buildability conclusion, or legal opinion. "
    "Verify all zoning context with Chatham County Planning before any legal, "
    "permitting, construction, or financing decision."
)

_NAMESPACE = UUID("e7c3b2a1-5d4f-4a8b-9e6c-2b1a3c4d5e6f")

_VERIFY = "Verify with Chatham County Planning."
_CHATHAM_UDO_DISTRICTS: dict[str, dict[str, object]] = {
    "RA": {
        "district_name": "Rural Agricultural",
        "use_category": "agricultural_low_intensity_residential",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": f"Rural agricultural and low-intensity residential. {_VERIFY}",
    },
    "RR": {
        "district_name": "Rural Residential",
        "use_category": "low_density_residential",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": f"Low-density rural residential. {_VERIFY}",
    },
    "R-1": {
        "district_name": "Low Density Residential",
        "use_category": "low_density_residential",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": f"Low-density residential. {_VERIFY}",
    },
    "R-2": {
        "district_name": "Medium Density Residential",
        "use_category": "medium_density_residential",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": f"Medium-density residential. {_VERIFY}",
    },
    "R-3": {
        "district_name": "High Density Residential",
        "use_category": "high_density_residential",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": f"Higher-density residential. {_VERIFY}",
    },
    "MHP": {
        "district_name": "Manufactured Housing Park",
        "use_category": "manufactured_housing",
        "residential_use_screening": "ALLOWED_WITH_RESTRICTIONS",
        "udo_note": f"Manufactured housing park district. {_VERIFY}",
    },
    "B-1": {
        "district_name": "Neighborhood Business",
        "use_category": "commercial_neighborhood",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": f"Neighborhood commercial; residential compatibility needs review. {_VERIFY}",
    },
    "B-2": {
        "district_name": "General Business",
        "use_category": "commercial_general",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": f"General commercial; residential compatibility requires review. {_VERIFY}",
    },
    "I": {
        "district_name": "Industrial",
        "use_category": "industrial",
        "residential_use_screening": "UNLIKELY_VERIFY",
        "udo_note": f"Industrial; residential uses typically not permitted. {_VERIFY}",
    },
    "I-1": {
        "district_name": "Light Industrial",
        "use_category": "industrial_light",
        "residential_use_screening": "UNLIKELY_VERIFY",
        "udo_note": f"Light industrial; residential compatibility requires review. {_VERIFY}",
    },
    "I-2": {
        "district_name": "Heavy Industrial",
        "use_category": "industrial_heavy",
        "residential_use_screening": "UNLIKELY_VERIFY",
        "udo_note": f"Heavy industrial; residential uses typically not permitted. {_VERIFY}",
    },
    "PD": {
        "district_name": "Planned Development",
        "use_category": "planned_development",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": f"Planned development; uses vary by approved plan. {_VERIFY}",
    },
    "UNZONED": {
        "district_name": "Unzoned / No Zoning Designation",
        "use_category": "unzoned",
        "residential_use_screening": "NEEDS_REVIEW",
        "udo_note": (
            "No zoning designation found; area may be unzoned, in a municipality, "
            f"or in an ETJ. {_VERIFY}"
        ),
    },
}


@dataclass(frozen=True)
class ChathamZoningConnectorResult:
    retrieval_run: SourceRetrievalRunContract
    evidence_inputs: tuple[EvidenceContract, ...]


class ChathamZoningConnectorError(ValueError):
    """Raised when the Chatham Zoning connector receives an invalid request before lookup."""


class ChathamZoningRecordedConnector:
    """Recorded-fixture connector for Chatham County UDO zoning district context.

    Uses a human-reviewed snapshot of the Chatham County UDO (effective 2025-07-01).
    Does not perform live network requests. Output is screening-only and requires
    verification with Chatham County Planning before any legal or permitting decision.
    """

    connector_name = CHATHAM_ZONING_CONNECTOR_NAME
    domain = "zoning"

    def query_district(
        self,
        *,
        area_id: UUID,
        zoning_code: str | None,
        source: SourceContract,
    ) -> ChathamZoningConnectorResult:
        started_at = _utcnow()
        normalized = (zoning_code or "").strip().upper() if zoning_code else None

        ingest_run_id = _stable_uuid(
            "retrieval",
            str(source.source_id),
            str(area_id),
            normalized or "NONE",
        )

        if not normalized:
            return self._unknown_result(
                area_id=area_id,
                source=source,
                ingest_run_id=ingest_run_id,
                started_at=started_at,
                reason="no_zoning_code",
                note="No zoning code available from parcel data; context cannot be determined.",
            )

        district = _CHATHAM_UDO_DISTRICTS.get(normalized)
        if district is None:
            return self._needs_review_result(
                area_id=area_id,
                source=source,
                ingest_run_id=ingest_run_id,
                started_at=started_at,
                zoning_code=normalized,
            )

        return self._known_district_result(
            area_id=area_id,
            source=source,
            ingest_run_id=ingest_run_id,
            started_at=started_at,
            zoning_code=normalized,
            district=district,
        )

    def _known_district_result(
        self,
        *,
        area_id: UUID,
        source: SourceContract,
        ingest_run_id: UUID,
        started_at: datetime,
        zoning_code: str,
        district: dict[str, object],
    ) -> ChathamZoningConnectorResult:
        finished_at = _utcnow()
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=1,
            error_count=0,
            warning_count=0,
            log_uri=CHATHAM_ZONING_UDO_URL,
            metrics={
                "source_registry_id": source.metadata.get("source_registry_id"),
                "udo_effective": CHATHAM_ZONING_UDO_EFFECTIVE,
                "udo_adopted": CHATHAM_ZONING_UDO_ADOPTED,
                "zoning_code": zoning_code,
                "lookup_type": "recorded_fixture",
            },
        )
        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(source.source_id),
                str(area_id),
                zoning_code,
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_USE_CLASSIFICATION",
            domain=self.domain,
            observation=(
                f"Chatham County UDO zoning district lookup: code '{zoning_code}' "
                f"matches '{district['district_name']}'"
                f" (use category: {district['use_category']}). "
                "Screening only — verify with Chatham County Planning."
            ),
            observed_value={
                "zoning_code": zoning_code,
                "district_name": district["district_name"],
                "use_category": district["use_category"],
                "residential_use_screening": district["residential_use_screening"],
                "udo_note": district["udo_note"],
                "udo_effective": CHATHAM_ZONING_UDO_EFFECTIVE,
                "udo_source_url": CHATHAM_ZONING_UDO_URL,
                "lookup_type": "recorded_fixture",
            },
            source_id=source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=CHATHAM_ZONING_METHOD_CODE,
            method_version=CHATHAM_ZONING_METHOD_VERSION,
            confidence=ConfidenceBand.LOW,
            caveat=CHATHAM_ZONING_CAVEAT,
            is_source_failure=False,
            observed_at=finished_at,
            source_date=CHATHAM_ZONING_UDO_EFFECTIVE,
        )
        return ChathamZoningConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
        )

    def _needs_review_result(
        self,
        *,
        area_id: UUID,
        source: SourceContract,
        ingest_run_id: UUID,
        started_at: datetime,
        zoning_code: str,
    ) -> ChathamZoningConnectorResult:
        finished_at = _utcnow()
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=1,
            error_count=0,
            warning_count=1,
            log_uri=CHATHAM_ZONING_UDO_URL,
            metrics={
                "source_registry_id": source.metadata.get("source_registry_id"),
                "udo_effective": CHATHAM_ZONING_UDO_EFFECTIVE,
                "zoning_code": zoning_code,
                "lookup_type": "recorded_fixture",
                "warning": "zoning_code_not_in_recorded_fixture",
            },
        )
        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(source.source_id),
                str(area_id),
                zoning_code,
                "needs_review",
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_EVIDENCE_NEEDS_REVIEW",
            domain=self.domain,
            observation=(
                f"Chatham County zoning code '{zoning_code}' is not in the recorded UDO "
                "district fixture. District context cannot be determined from this connector. "
                "Verify zoning designation and permitted uses with Chatham County Planning."
            ),
            observed_value={
                "zoning_code": zoning_code,
                "district_name": None,
                "use_category": None,
                "residential_use_screening": "NEEDS_REVIEW",
                "udo_note": "Zoning code not in recorded fixture; verify with Chatham County Planning.",  # noqa: E501
                "udo_effective": CHATHAM_ZONING_UDO_EFFECTIVE,
                "udo_source_url": CHATHAM_ZONING_UDO_URL,
                "lookup_type": "recorded_fixture",
            },
            source_id=source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=CHATHAM_ZONING_METHOD_CODE,
            method_version=CHATHAM_ZONING_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=CHATHAM_ZONING_CAVEAT,
            is_source_failure=False,
            observed_at=finished_at,
            source_date=CHATHAM_ZONING_UDO_EFFECTIVE,
        )
        return ChathamZoningConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
        )

    def _unknown_result(
        self,
        *,
        area_id: UUID,
        source: SourceContract,
        ingest_run_id: UUID,
        started_at: datetime,
        reason: str,
        note: str,
    ) -> ChathamZoningConnectorResult:
        finished_at = _utcnow()
        retrieval_run = SourceRetrievalRunContract(
            ingest_run_id=ingest_run_id,
            connector_name=self.connector_name,
            status=SourceRetrievalStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            row_count=0,
            error_count=0,
            warning_count=1,
            log_uri=CHATHAM_ZONING_UDO_URL,
            metrics={
                "source_registry_id": source.metadata.get("source_registry_id"),
                "udo_effective": CHATHAM_ZONING_UDO_EFFECTIVE,
                "reason": reason,
                "lookup_type": "recorded_fixture",
            },
        )
        evidence = EvidenceContract(
            evidence_id=_stable_uuid(
                "evidence",
                str(source.source_id),
                str(area_id),
                reason,
                "unknown",
            ),
            area_id=area_id,
            evidence_type=EvidenceType.SOURCE_OBSERVATION,
            evidence_code="ZONING_UNKNOWN",
            domain=self.domain,
            observation=f"Chatham County zoning context is unknown: {note}",
            observed_value={
                "zoning_code": None,
                "district_name": None,
                "use_category": None,
                "residential_use_screening": "UNKNOWN",
                "reason": reason,
                "note": note,
                "udo_effective": CHATHAM_ZONING_UDO_EFFECTIVE,
                "udo_source_url": CHATHAM_ZONING_UDO_URL,
                "lookup_type": "recorded_fixture",
            },
            source_id=source.source_id,
            source_ingest_run_id=ingest_run_id,
            method_code=CHATHAM_ZONING_METHOD_CODE,
            method_version=CHATHAM_ZONING_METHOD_VERSION,
            confidence=ConfidenceBand.UNKNOWN,
            caveat=CHATHAM_ZONING_CAVEAT,
            is_source_failure=False,
            observed_at=finished_at,
            source_date=CHATHAM_ZONING_UDO_EFFECTIVE,
        )
        return ChathamZoningConnectorResult(
            retrieval_run=retrieval_run,
            evidence_inputs=(evidence,),
        )


def _stable_uuid(*parts: str) -> UUID:
    return uuid5(_NAMESPACE, "|".join(parts))


def _utcnow() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "CHATHAM_ZONING_CAVEAT",
    "CHATHAM_ZONING_CONNECTOR_NAME",
    "CHATHAM_ZONING_METHOD_CODE",
    "CHATHAM_ZONING_UDO_EFFECTIVE",
    "CHATHAM_ZONING_UDO_URL",
    "ChathamZoningConnectorError",
    "ChathamZoningConnectorResult",
    "ChathamZoningRecordedConnector",
]
