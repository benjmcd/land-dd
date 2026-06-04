from __future__ import annotations

from uuid import UUID, uuid4

from app.claims_engine.not_evaluated import (
    NOT_EVALUATED_CAVEATS,
    NOT_EVALUATED_CLAIM_CODES,
    NOT_EVALUATED_DOMAINS,
    NOT_EVALUATED_METHOD_CODES,
    make_not_evaluated_source_failure,
)
from app.claims_engine.rule_engine import (
    DEFAULT_RULESET_PATH,
    ENV_HAZARD_CONDITION,
    MARKET_CONTEXT_CONDITION,
    RESOURCE_CONTEXT_CONDITION,
    SOIL_SEPTIC_CONDITION,
    RuleEngine,
    load_ruleset,
)
from app.domain.enums import ConfidenceBand, EvidenceType, SeverityBand
from app.domain.evidence_contracts import EvidenceContract

_CONDITIONS_BY_DOMAIN = {
    "soil_septic": SOIL_SEPTIC_CONDITION,
    "env_hazard": ENV_HAZARD_CONDITION,
    "resource_context": RESOURCE_CONTEXT_CONDITION,
    "market_context": MARKET_CONTEXT_CONDITION,
}


def test_default_ruleset_declares_not_evaluated_hard_gates() -> None:
    ruleset = load_ruleset(DEFAULT_RULESET_PATH)

    for domain in NOT_EVALUATED_DOMAINS:
        rule = ruleset.hard_gate_for_condition(_CONDITIONS_BY_DOMAIN[domain])
        assert rule.domain == domain
        assert rule.claim_code == NOT_EVALUATED_CLAIM_CODES[domain]
        assert rule.severity_on_fail == SeverityBand.UNKNOWN


def test_not_evaluated_helper_creates_source_failure_evidence() -> None:
    area_id = uuid4()
    source_id = uuid4()

    for domain in NOT_EVALUATED_DOMAINS:
        evidence = make_not_evaluated_source_failure(
            area_id=area_id,
            source_id=source_id,
            domain=domain,
        )

        assert evidence.area_id == area_id
        assert evidence.source_id == source_id
        assert evidence.domain == domain
        assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
        assert evidence.is_source_failure is True
        assert evidence.method_code == NOT_EVALUATED_METHOD_CODES[domain]
        assert evidence.confidence == ConfidenceBand.UNKNOWN
        assert evidence.caveat == NOT_EVALUATED_CAVEATS[domain]


def test_rule_engine_emits_unknown_claims_from_not_evaluated_failures() -> None:
    area_id = uuid4()
    source_id = uuid4()
    failures = [
        make_not_evaluated_source_failure(
            area_id=area_id,
            source_id=source_id,
            domain=domain,
        )
        for domain in NOT_EVALUATED_DOMAINS
    ]

    first_result = RuleEngine.from_file().evaluate(failures)
    second_result = RuleEngine.from_file().evaluate(list(reversed(failures)))

    assert first_result == second_result
    claims_by_domain = {claim.domain: claim for claim in first_result}
    assert set(claims_by_domain) == set(NOT_EVALUATED_DOMAINS)

    evidence_by_domain = {evidence.domain: evidence for evidence in failures}
    for domain, claim in claims_by_domain.items():
        evidence = evidence_by_domain[domain]
        assert claim.claim_code == NOT_EVALUATED_CLAIM_CODES[domain]
        assert claim.severity == SeverityBand.UNKNOWN
        assert claim.confidence == ConfidenceBand.UNKNOWN
        assert claim.evidence_ids == [evidence.evidence_id]
        assert claim.rule_code is not None
        assert claim.ruleset_id == "homestead_mvp_v0_1"
        assert claim.ruleset_version == "0.1"
        assert claim.verification_required is True
        assert claim.verification_task is not None


def test_not_evaluated_claims_ignore_non_failure_records() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=source_id,
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="SOIL_SCREEN",
        domain="soil_septic",
        observation="Soil data placeholder.",
        observed_value={"not_evaluated": True},
        method_code="soil_placeholder",
        confidence=ConfidenceBand.UNKNOWN,
    )

    assert RuleEngine.from_file().evaluate([evidence]) == []


def test_market_context_not_evaluated_language_avoids_unsafe_market_terms() -> None:
    area_id = uuid4()
    source_id = uuid4()
    evidence = make_not_evaluated_source_failure(
        area_id=area_id,
        source_id=source_id,
        domain="market_context",
    )

    claims = RuleEngine.from_file().evaluate([evidence])

    assert len(claims) == 1
    claim = claims[0]
    combined_language = f"{claim.assertion} {claim.user_safe_language}".lower()
    for unsafe_term in ("value", "price", "invest", "neighborhood", "desirable"):
        assert unsafe_term not in combined_language


def test_not_evaluated_claims_keep_evidence_ids_sorted() -> None:
    area_id = uuid4()
    source_id = uuid4()
    first = make_not_evaluated_source_failure(
        area_id=area_id,
        source_id=source_id,
        domain="soil_septic",
    )
    second = first.model_copy(update={"evidence_id": uuid4()})

    claims = RuleEngine.from_file().evaluate([second, first])

    assert len(claims) == 1
    assert claims[0].evidence_ids == _sorted_ids([first.evidence_id, second.evidence_id])


def _sorted_ids(values: list[UUID]) -> list[UUID]:
    return sorted(values, key=str)
