from __future__ import annotations

from uuid import UUID

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract

NOT_EVALUATED_SOURCE_NAME = "Land Diligence MVP - Unsupported Screening Categories"
NOT_EVALUATED_SOURCE_ORG = "internal"
NOT_EVALUATED_DOMAINS = (
    "soil_septic",
    "env_hazard",
    "resource_context",
    "market_context",
)

NOT_EVALUATED_CLAIM_CODES = {
    "soil_septic": "SOIL_NOT_EVALUATED",
    "env_hazard": "ENV_HAZ_NOT_EVALUATED",
    "resource_context": "RESOURCE_NOT_EVALUATED",
    "market_context": "MARKET_OUT_OF_SCOPE",
}

NOT_EVALUATED_CAVEATS = {
    "soil_septic": (
        "Soil and septic feasibility sources are not supported in this screening "
        "tool version. A perc test, county health department consultation, and "
        "septic engineer assessment are required before any septic or building "
        "determination."
    ),
    "env_hazard": (
        "Environmental hazard sources are not supported in this screening tool "
        "version. Review EPA, state environmental agency records, and appropriate "
        "professional due-diligence materials before relying on this category."
    ),
    "resource_context": (
        "Mineral, timber, water-rights, and resource-context sources are not "
        "supported in this screening tool version. Consult title, state resource "
        "records, and qualified local professionals for resource due diligence."
    ),
    "market_context": (
        "Market context was not evaluated. This screening tool provides no "
        "sales-comparison, appraisal, buyer-suitability, or financial-return "
        "guidance."
    ),
}

NOT_EVALUATED_METHOD_CODES = {
    domain: f"{domain}_not_evaluated" for domain in NOT_EVALUATED_DOMAINS
}


def make_not_evaluated_source_failure(
    *,
    area_id: UUID,
    source_id: UUID,
    domain: str,
) -> EvidenceContract:
    if domain not in NOT_EVALUATED_DOMAINS:
        raise ValueError(f"Unsupported not-evaluated domain: {domain}")

    return EvidenceContract(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code=f"{domain.upper()}_NOT_EVALUATED",
        domain=domain,
        observation=f"{domain} screening is not supported in this tool version.",
        observed_value={"not_evaluated": True, "reason": "unsupported_screening_domain"},
        method_code=NOT_EVALUATED_METHOD_CODES[domain],
        confidence=ConfidenceBand.UNKNOWN,
        caveat=NOT_EVALUATED_CAVEATS[domain],
        is_source_failure=True,
    )


__all__ = [
    "NOT_EVALUATED_CAVEATS",
    "NOT_EVALUATED_CLAIM_CODES",
    "NOT_EVALUATED_DOMAINS",
    "NOT_EVALUATED_METHOD_CODES",
    "NOT_EVALUATED_SOURCE_NAME",
    "NOT_EVALUATED_SOURCE_ORG",
    "make_not_evaluated_source_failure",
]
