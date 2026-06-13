from __future__ import annotations

from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from app.claims_engine.not_evaluated import (
    NOT_EVALUATED_CAVEATS,
    NOT_EVALUATED_DOMAINS,
)
from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, EvidenceType, SeverityBand
from app.domain.evidence_contracts import EvidenceContract

DEFAULT_RULESET_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "ruleset_homestead_mvp.yaml"
)
FLOOD_HIGH_RISK_CONDITION = "material_intersection_with_high_risk_flood_zone"
ACCESS_NO_PUBLIC_ROAD_CONDITION = "no_public_road_adjacency_or_access_source_unavailable"
ZONING_INTENDED_USE_CONDITION = "intended_residential_use_prohibited_or_unknown"
WATER_CONTEXT_CONDITION = "no_plausible_water_context_or_source_unavailable"
WETLAND_MAPPED_CONDITION = "material_intersection_with_mapped_wetlands"
SLOPE_INSUFFICIENT_CONDITION = "insufficient_low_slope_buildable_area"
SOIL_SEPTIC_CONDITION = "soil_septic_unsupported"
ENV_HAZARD_CONDITION = "env_hazard_facility_proximity"
RESOURCE_CONTEXT_CONDITION = "resource_context_unsupported"
MARKET_CONTEXT_CONDITION = "market_context_out_of_scope"
PARCELS_NOT_EVALUATED_CONDITION = "parcels_not_evaluated"
PARCELS_SCREEN_CONDITION = "county_parcel_screen_identified"
ASSESSOR_NOT_EVALUATED_CONDITION = "assessor_not_evaluated"
NOT_EVALUATED_CONDITIONS_BY_DOMAIN = {
    "soil_septic": SOIL_SEPTIC_CONDITION,
    "resource_context": RESOURCE_CONTEXT_CONDITION,
    "market_context": MARKET_CONTEXT_CONDITION,
    "parcels": PARCELS_NOT_EVALUATED_CONDITION,
    "assessor": ASSESSOR_NOT_EVALUATED_CONDITION,
}
HIGH_RISK_FLOOD_ZONES = {"A", "AE", "AH", "AO", "A99", "V", "VE"}
ACCESS_ADJACENCY_TRUE_KEYS = ("public_road_adjacency", "has_public_road_adjacency")
ACCESS_NO_ADJACENCY_KEYS = ("no_public_road_adjacency",)
ACCESS_NEEDS_REVIEW_CLAIM_CODE = "ACCESS_EVIDENCE_NEEDS_REVIEW"
ACCESS_STALE_CLAIM_CODE = "ACCESS_STALE_EVIDENCE_NEEDS_REVIEW"
ZONING_ALLOWED_KEYS = ("intended_residential_use_allowed",)
ZONING_PROHIBITED_KEYS = ("intended_residential_use_prohibited",)
ZONING_NEEDS_REVIEW_CLAIM_CODE = "ZONING_EVIDENCE_NEEDS_REVIEW"
ZONING_STALE_CLAIM_CODE = "ZONING_STALE_EVIDENCE_NEEDS_REVIEW"
WATER_CONTEXT_KEYS = ("plausible_water_context",)
WATER_NO_CONTEXT_KEYS = ("no_plausible_water_context",)
WATER_NEEDS_REVIEW_CLAIM_CODE = "WATER_EVIDENCE_NEEDS_REVIEW"
WATER_STALE_CLAIM_CODE = "WATER_STALE_EVIDENCE_NEEDS_REVIEW"
WETLAND_INTERSECTION_KEYS = ("intersects_mapped_wetlands",)
WETLAND_NEEDS_REVIEW_CLAIM_CODE = "WETLAND_EVIDENCE_NEEDS_REVIEW"
WETLAND_STALE_CLAIM_CODE = "WETLAND_STALE_EVIDENCE_NEEDS_REVIEW"
SLOPE_NEEDS_REVIEW_CLAIM_CODE = "SLOPE_EVIDENCE_NEEDS_REVIEW"
SLOPE_STALE_CLAIM_CODE = "SLOPE_STALE_EVIDENCE_NEEDS_REVIEW"
FLOOD_NEEDS_REVIEW_CLAIM_CODE = "FLOOD_EVIDENCE_NEEDS_REVIEW"
FLOOD_STALE_CLAIM_CODE = "FLOOD_STALE_EVIDENCE_NEEDS_REVIEW"
ENV_HAZARD_PROXIMITY_KEYS = ("has_env_hazard_proximity",)
ENV_HAZARD_NO_PROXIMITY_KEYS = ("no_env_hazard_proximity",)
ENV_HAZARD_NEEDS_REVIEW_CLAIM_CODE = "ENV_EVIDENCE_NEEDS_REVIEW"
ENV_HAZARD_STALE_CLAIM_CODE = "ENV_STALE_EVIDENCE_NEEDS_REVIEW"
MINERALS_ACTIVE_CLAIM_CONDITION = "blm_active_mining_claims_present"
MINERALS_SOURCE_UNAVAILABLE_CONDITION = "minerals_source_unavailable"
MINERALS_ACTIVE_CLAIM_CODE = "MINERALS_ACTIVE_CLAIMS_001"
MINERALS_SOURCE_UNAVAILABLE_CLAIM_CODE = "MINERALS_SOURCE_UNAVAILABLE"
BROADBAND_NO_ACCESS_CONDITION = "no_broadband_service_detected"
BROADBAND_SOURCE_UNAVAILABLE_CONDITION = "broadband_source_unavailable"
BROADBAND_NO_ACCESS_CLAIM_CODE = "BROADBAND_NO_ACCESS_001"
BROADBAND_SOURCE_UNAVAILABLE_CLAIM_CODE = "BROADBAND_SOURCE_UNAVAILABLE"
SOIL_POOR_DRAINAGE_CONDITION = "soil_poor_or_hydric_drainage_detected"
SOIL_POOR_DRAINAGE_CLAIM_CODE = "SOIL_POOR_DRAINAGE_001"
_SSURGO_POOR_DRAINAGE = frozenset({
    "poorly drained", "very poorly drained", "somewhat poorly drained"
})
FLOOD_MODERATE_CONDITION = "material_intersection_with_moderate_or_undetermined_flood_zone"
FLOOD_MODERATE_CLAIM_CODE = "FLOOD_MODERATE_001"
_MODERATE_RISK_FLOOD_ZONES = frozenset({"X500", "B", "D"})
GEOLOGY_NOT_EVALUATED_CONDITION = "geologic_hazard_not_determined"
GEOLOGY_NOT_EVALUATED_CLAIM_CODE = "GEOLOGY_NOT_EVALUATED"


@dataclass(frozen=True)
class HardGateRule:
    code: str
    domain: str
    severity_on_fail: SeverityBand
    condition: str
    claim_code: str
    verification_task: str


@dataclass(frozen=True)
class RuleSet:
    ruleset_id: str
    version: str
    hard_gates: tuple[HardGateRule, ...]
    forbidden_language: frozenset[str] = frozenset()

    def hard_gate_for_condition(self, condition: str) -> HardGateRule:
        for rule in self.hard_gates:
            if rule.condition == condition:
                return rule
        raise ValueError(f"Ruleset '{self.ruleset_id}' does not define condition '{condition}'")


class RuleEngine:
    def __init__(self, ruleset: RuleSet) -> None:
        self._ruleset = ruleset

    @classmethod
    def from_file(cls, path: Path | None = None) -> RuleEngine:
        return cls(load_ruleset(path or DEFAULT_RULESET_PATH))

    @property
    def ruleset_id(self) -> str:
        return self._ruleset.ruleset_id

    @property
    def ruleset_version(self) -> str:
        return self._ruleset.version

    def evaluate(self, evidence_list: list[EvidenceContract]) -> list[ClaimContract]:
        access_rule = self._ruleset.hard_gate_for_condition(ACCESS_NO_PUBLIC_ROAD_CONDITION)
        zoning_rule = self._ruleset.hard_gate_for_condition(ZONING_INTENDED_USE_CONDITION)
        water_rule = self._ruleset.hard_gate_for_condition(WATER_CONTEXT_CONDITION)
        flood_rule = self._ruleset.hard_gate_for_condition(FLOOD_HIGH_RISK_CONDITION)
        slope_rule = self._ruleset.hard_gate_for_condition(SLOPE_INSUFFICIENT_CONDITION)
        wetland_rule = self._ruleset.hard_gate_for_condition(WETLAND_MAPPED_CONDITION)
        env_hazard_rule = self._ruleset.hard_gate_for_condition(ENV_HAZARD_CONDITION)
        minerals_active_rule = self._ruleset.hard_gate_for_condition(
            MINERALS_ACTIVE_CLAIM_CONDITION
        )
        minerals_unavailable_rule = self._ruleset.hard_gate_for_condition(
            MINERALS_SOURCE_UNAVAILABLE_CONDITION
        )
        broadband_no_access_rule = self._ruleset.hard_gate_for_condition(
            BROADBAND_NO_ACCESS_CONDITION
        )
        broadband_unavailable_rule = self._ruleset.hard_gate_for_condition(
            BROADBAND_SOURCE_UNAVAILABLE_CONDITION
        )
        soil_poor_drainage_rule = self._ruleset.hard_gate_for_condition(
            SOIL_POOR_DRAINAGE_CONDITION
        )
        flood_moderate_rule = self._ruleset.hard_gate_for_condition(FLOOD_MODERATE_CONDITION)
        geology_not_evaluated_rule = self._ruleset.hard_gate_for_condition(
            GEOLOGY_NOT_EVALUATED_CONDITION
        )
        not_evaluated_rules = {
            domain: self._ruleset.hard_gate_for_condition(condition)
            for domain, condition in NOT_EVALUATED_CONDITIONS_BY_DOMAIN.items()
        }
        parcel_screen_rule = self._ruleset.hard_gate_for_condition(PARCELS_SCREEN_CONDITION)
        active_evidence = sorted(
            (evidence for evidence in evidence_list if evidence.superseded_by is None),
            key=lambda evidence: (str(evidence.area_id), str(evidence.evidence_id)),
        )

        claims: list[ClaimContract] = []
        for area_id, area_evidence_iter in groupby(
            active_evidence,
            key=lambda evidence: evidence.area_id,
        ):
            area_evidence = list(area_evidence_iter)
            access_no_adjacency = [
                evidence
                for evidence in area_evidence
                if _is_access_no_adjacency_evidence(evidence)
            ]
            access_adjacency = [
                evidence
                for evidence in area_evidence
                if _is_access_adjacency_evidence(evidence)
            ]
            access_failures = [
                evidence
                for evidence in area_evidence
                if _is_access_source_failure(evidence)
            ]
            stale_access_evidence = [
                evidence
                for evidence in area_evidence
                if _is_stale_access_evidence(evidence)
            ]
            zoning_prohibited = [
                evidence
                for evidence in area_evidence
                if _is_zoning_prohibited_evidence(evidence)
            ]
            zoning_allowed = [
                evidence
                for evidence in area_evidence
                if _is_zoning_allowed_evidence(evidence)
            ]
            zoning_incomplete = [
                evidence
                for evidence in area_evidence
                if _is_incomplete_zoning_evidence(evidence)
            ]
            zoning_failures = [
                evidence
                for evidence in area_evidence
                if _is_zoning_source_failure(evidence)
            ]
            stale_zoning_evidence = [
                evidence
                for evidence in area_evidence
                if _is_stale_zoning_evidence(evidence)
            ]
            water_conflicting = [
                evidence
                for evidence in area_evidence
                if _is_conflicting_water_evidence(evidence)
            ]
            water_no_context = [
                evidence
                for evidence in area_evidence
                if _is_water_no_context_evidence(evidence)
            ]
            water_context = [
                evidence
                for evidence in area_evidence
                if _is_water_context_evidence(evidence)
            ]
            water_incomplete = [
                evidence
                for evidence in area_evidence
                if _is_incomplete_water_evidence(evidence)
            ]
            water_failures = [
                evidence
                for evidence in area_evidence
                if _is_water_source_failure(evidence)
            ]
            stale_water_evidence = [
                evidence
                for evidence in area_evidence
                if _is_stale_water_evidence(evidence)
            ]
            wetland_positive = [
                evidence
                for evidence in area_evidence
                if _is_mapped_wetland_evidence(evidence)
            ]
            wetland_negative = [
                evidence
                for evidence in area_evidence
                if _is_negative_wetland_evidence(evidence)
            ]
            wetland_failures = [
                evidence
                for evidence in area_evidence
                if _is_wetland_source_failure(evidence)
            ]
            stale_wetland_evidence = [
                evidence
                for evidence in area_evidence
                if _is_stale_wetland_evidence(evidence)
            ]
            slope_insufficient = [
                evidence
                for evidence in area_evidence
                if _is_insufficient_slope_evidence(evidence)
            ]
            slope_sufficient = [
                evidence
                for evidence in area_evidence
                if _is_sufficient_slope_evidence(evidence)
            ]
            slope_failures = [
                evidence
                for evidence in area_evidence
                if _is_slope_source_failure(evidence)
            ]
            stale_slope_evidence = [
                evidence
                for evidence in area_evidence
                if _is_stale_slope_evidence(evidence)
            ]
            flood_positive = [
                evidence
                for evidence in area_evidence
                if _is_high_risk_flood_evidence(evidence)
            ]
            flood_failures = [
                evidence
                for evidence in area_evidence
                if _is_flood_source_failure(evidence)
            ]
            flood_negative = [
                evidence
                for evidence in area_evidence
                if _is_negative_flood_evidence(evidence)
            ]
            flood_moderate = [
                evidence
                for evidence in area_evidence
                if _is_moderate_risk_flood_evidence(evidence)
            ]
            stale_evidence = [
                evidence
                for evidence in area_evidence
                if _is_stale_flood_evidence(evidence)
            ]
            soil_screening = [
                evidence
                for evidence in area_evidence
                if _is_soil_screening_evidence(evidence)
            ]
            county_parcel_screen = [
                evidence
                for evidence in area_evidence
                if _is_county_parcel_screen_evidence(evidence)
            ]
            env_hazard_proximity = [
                evidence for evidence in area_evidence
                if _is_env_hazard_proximity_evidence(evidence)
            ]
            env_hazard_no_proximity = [
                evidence for evidence in area_evidence
                if _is_env_hazard_no_proximity_evidence(evidence)
            ]
            env_hazard_conflicting = [
                evidence for evidence in area_evidence
                if _is_conflicting_env_hazard_evidence(evidence)
            ]
            env_hazard_incomplete = [
                evidence for evidence in area_evidence
                if _is_incomplete_env_hazard_evidence(evidence)
            ]
            env_hazard_failures = [
                evidence for evidence in area_evidence
                if _is_env_hazard_source_failure(evidence)
            ]
            stale_env_hazard_evidence = [
                evidence for evidence in area_evidence
                if _is_stale_env_hazard_evidence(evidence)
            ]
            minerals_active = [
                evidence for evidence in area_evidence
                if _is_minerals_active_evidence(evidence)
            ]
            minerals_failures = [
                evidence for evidence in area_evidence
                if _is_minerals_source_failure(evidence)
            ]
            broadband_no_access = [
                evidence for evidence in area_evidence
                if _is_broadband_no_access_evidence(evidence)
            ]
            broadband_failures = [
                evidence for evidence in area_evidence
                if _is_broadband_source_failure(evidence)
            ]
            soil_poor_drainage = [
                evidence for evidence in area_evidence
                if _is_soil_poor_drainage_evidence(evidence)
            ]
            geology_not_evaluated = [
                evidence for evidence in area_evidence
                if _is_geology_not_evaluated_evidence(evidence)
            ]
            if access_no_adjacency:
                claims.append(
                    self._access_no_adjacency_claim(
                        area_id,
                        access_rule,
                        access_no_adjacency,
                    )
                )
            if access_failures:
                claims.append(
                    self._access_unknown_claim(area_id, access_rule, access_failures)
                )
            if access_no_adjacency and (access_adjacency or access_failures):
                claims.append(
                    self._access_needs_review_claim(
                        area_id,
                        access_rule,
                        _dedupe_evidence_records(
                            [
                                *access_no_adjacency,
                                *access_adjacency,
                                *access_failures,
                            ]
                        ),
                    )
                )
            if stale_access_evidence:
                claims.append(
                    self._access_stale_claim(
                        area_id,
                        access_rule,
                        stale_access_evidence,
                    )
                )
            if zoning_prohibited:
                claims.append(
                    self._zoning_prohibited_claim(
                        area_id,
                        zoning_rule,
                        zoning_prohibited,
                    )
                )
            if zoning_failures:
                claims.append(
                    self._zoning_unknown_claim(area_id, zoning_rule, zoning_failures)
                )
            if zoning_incomplete or (
                zoning_prohibited and (zoning_allowed or zoning_failures)
            ):
                claims.append(
                    self._zoning_needs_review_claim(
                        area_id,
                        zoning_rule,
                        _dedupe_evidence_records(
                            [
                                *zoning_prohibited,
                                *zoning_allowed,
                                *zoning_incomplete,
                                *zoning_failures,
                            ]
                        ),
                    )
                )
            if stale_zoning_evidence:
                claims.append(
                    self._zoning_stale_claim(
                        area_id,
                        zoning_rule,
                        stale_zoning_evidence,
                    )
                )
            if water_no_context:
                claims.append(
                    self._water_no_context_claim(
                        area_id,
                        water_rule,
                        water_no_context,
                    )
                )
            if water_failures:
                claims.append(
                    self._water_unknown_claim(area_id, water_rule, water_failures)
                )
            if water_conflicting or water_incomplete or (
                water_no_context and (water_context or water_failures)
            ):
                claims.append(
                    self._water_needs_review_claim(
                        area_id,
                        water_rule,
                        _dedupe_evidence_records(
                            [
                                *water_conflicting,
                                *water_no_context,
                                *water_context,
                                *water_incomplete,
                                *water_failures,
                            ]
                        ),
                    )
                )
            if stale_water_evidence:
                claims.append(
                    self._water_stale_claim(
                        area_id,
                        water_rule,
                        stale_water_evidence,
                    )
                )
            if wetland_positive:
                claims.append(
                    self._wetland_positive_claim(
                        area_id,
                        wetland_rule,
                        wetland_positive,
                    )
                )
            if wetland_failures:
                claims.append(
                    self._wetland_unknown_claim(
                        area_id,
                        wetland_rule,
                        wetland_failures,
                    )
                )
            if wetland_positive and (wetland_negative or wetland_failures):
                claims.append(
                    self._wetland_needs_review_claim(
                        area_id,
                        wetland_rule,
                        _dedupe_evidence_records(
                            [
                                *wetland_positive,
                                *wetland_negative,
                                *wetland_failures,
                            ]
                        ),
                    )
                )
            if stale_wetland_evidence:
                claims.append(
                    self._wetland_stale_claim(
                        area_id,
                        wetland_rule,
                        stale_wetland_evidence,
                    )
                )
            if flood_positive:
                claims.append(self._flood_positive_claim(area_id, flood_rule, flood_positive))
            if slope_insufficient:
                claims.append(
                    self._slope_insufficient_claim(
                        area_id,
                        slope_rule,
                        slope_insufficient,
                    )
                )
            if slope_failures:
                claims.append(
                    self._slope_unknown_claim(area_id, slope_rule, slope_failures)
                )
            if slope_insufficient and (slope_sufficient or slope_failures):
                claims.append(
                    self._slope_needs_review_claim(
                        area_id,
                        slope_rule,
                        _dedupe_evidence_records(
                            [
                                *slope_insufficient,
                                *slope_sufficient,
                                *slope_failures,
                            ]
                        ),
                    )
                )
            if stale_slope_evidence:
                claims.append(
                    self._slope_stale_claim(
                        area_id,
                        slope_rule,
                        stale_slope_evidence,
                    )
                )
            if flood_failures:
                claims.append(self._flood_unknown_claim(area_id, flood_rule, flood_failures))
            if flood_positive and (flood_negative or flood_failures):
                claims.append(
                    self._flood_needs_review_claim(
                        area_id,
                        flood_rule,
                        _dedupe_evidence_records(
                            [*flood_positive, *flood_negative, *flood_failures]
                        ),
                    )
                )
            if stale_evidence:
                claims.append(
                    self._flood_stale_claim(area_id, flood_rule, stale_evidence)
                )
            if flood_moderate:
                claims.append(
                    self._flood_moderate_claim(area_id, flood_moderate_rule, flood_moderate)
                )
            if soil_screening:
                claims.append(
                    self._soil_screening_review_claim(
                        area_id,
                        not_evaluated_rules["soil_septic"],
                        soil_screening,
                    )
                )
            if soil_poor_drainage:
                claims.append(
                    self._soil_poor_drainage_claim(
                        area_id,
                        soil_poor_drainage_rule,
                        soil_poor_drainage,
                    )
                )
            if county_parcel_screen:
                claims.append(
                    self._parcel_screen_claim(
                        area_id,
                        parcel_screen_rule,
                        county_parcel_screen,
                    )
                )
            if env_hazard_proximity:
                claims.append(
                    self._env_hazard_proximity_claim(area_id, env_hazard_rule, env_hazard_proximity)
                )
            if env_hazard_failures:
                claims.append(
                    self._env_hazard_unknown_claim(area_id, env_hazard_rule, env_hazard_failures)
                )
            if env_hazard_conflicting or env_hazard_incomplete or (
                env_hazard_proximity and (env_hazard_no_proximity or env_hazard_failures)
            ):
                claims.append(
                    self._env_hazard_needs_review_claim(
                        area_id,
                        env_hazard_rule,
                        _dedupe_evidence_records([
                            *env_hazard_conflicting,
                            *env_hazard_proximity,
                            *env_hazard_no_proximity,
                            *env_hazard_incomplete,
                            *env_hazard_failures,
                        ]),
                    )
                )
            if stale_env_hazard_evidence:
                claims.append(
                    self._env_hazard_stale_claim(
                        area_id, env_hazard_rule, stale_env_hazard_evidence
                    )
                )
            if minerals_active:
                claims.append(
                    self._minerals_active_claim(area_id, minerals_active_rule, minerals_active)
                )
            if minerals_failures and not minerals_active:
                claims.append(
                    self._minerals_unknown_claim(
                        area_id, minerals_unavailable_rule, minerals_failures
                    )
                )
            if broadband_no_access:
                claims.append(
                    self._broadband_no_access_claim(
                        area_id, broadband_no_access_rule, broadband_no_access
                    )
                )
            if broadband_failures and not broadband_no_access:
                claims.append(
                    self._broadband_unknown_claim(
                        area_id, broadband_unavailable_rule, broadband_failures
                    )
                )
            if geology_not_evaluated:
                claims.append(
                    self._geology_not_evaluated_claim(
                        area_id, geology_not_evaluated_rule, geology_not_evaluated
                    )
                )
            for domain in NOT_EVALUATED_DOMAINS:
                not_evaluated_failures = [
                    evidence
                    for evidence in area_evidence
                    if _is_not_evaluated_source_failure(evidence, domain)
                ]
                if not_evaluated_failures:
                    claims.append(
                        self._not_evaluated_claim(
                            area_id,
                            not_evaluated_rules[domain],
                            not_evaluated_failures,
                        )
                    )
        for claim in claims:
            self._check_forbidden_language(claim)
        return claims

    def _check_forbidden_language(self, claim: ClaimContract) -> None:
        for phrase in self._ruleset.forbidden_language:
            phrase_lc = phrase.lower()
            in_assertion = phrase_lc in claim.assertion.lower()
            in_language = phrase_lc in claim.user_safe_language.lower()
            if in_assertion or in_language:
                raise ValueError(
                    f"Claim {claim.claim_code!r} contains forbidden language: {phrase!r}"
                )

    def _access_no_adjacency_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Road adjacency screening indicates no apparent public road adjacency. "
            "This is a physical proxy only and does not determine recorded legal "
            "access or easements."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("positive", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion="Screening evidence found no apparent public road adjacency.",
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _access_unknown_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Access screening remains unknown because required road/access source "
            "evidence failed or was unavailable. Road proximity does not determine "
            "recorded legal access."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("unknown", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code="ACCESS_SOURCE_UNAVAILABLE_UNKNOWN",
            domain=rule.domain,
            assertion="Access source data could not be evaluated for this area.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _access_needs_review_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Access screening evidence is conflicting or incomplete and requires "
            "human review. Road proximity is a physical proxy and does not determine "
            "recorded legal access."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("needs-review", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=ACCESS_NEEDS_REVIEW_CLAIM_CODE,
            domain=rule.domain,
            assertion="Access evidence requires human review before rule interpretation.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Resolve conflicting or incomplete access evidence before relying on "
                "this screening result."
            ),
        )

    def _access_stale_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Access screening evidence is marked stale in the fixture and should be "
            "refreshed before relying on the road-adjacency proxy."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("stale", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=ACCESS_STALE_CLAIM_CODE,
            domain=rule.domain,
            assertion="Access evidence freshness requires review.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.INFORMATIONAL,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Refresh stale access screening source evidence before final "
                "interpretation."
            ),
        )

    def _zoning_prohibited_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        zone_parts: list[str] = []
        for e in evidence_records:
            code = e.observed_value.get("zoning_code")
            name = e.observed_value.get("district_name")
            use_cat = e.observed_value.get("use_category")
            if isinstance(code, str) and code:
                label = code
                if isinstance(name, str) and name:
                    label += f" ({name})"
                if isinstance(use_cat, str) and use_cat:
                    label += f" — {use_cat}"
                zone_parts.append(label)
                break
        zone_context = f" Screened zone: {zone_parts[0]}." if zone_parts else ""
        user_safe_language = (
            f"Zoning/use screening indicates the intended residential or homestead "
            f"use is prohibited or unsupported in the fixture.{zone_context} This is source-linked "
            "screening only and does not determine final legal use, zoning "
            "compliance, permit eligibility, vested rights, or buildability."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("positive", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion=(
                "Zoning/use screening indicates intended residential or homestead "
                "use is prohibited or unsupported."
            ),
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _zoning_unknown_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Zoning/use screening remains unknown because required zoning source "
            "evidence failed or was unavailable. This does not establish legal use, "
            "zoning compliance, permit eligibility, or buildability."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("unknown", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code="ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
            domain=rule.domain,
            assertion="Zoning source data could not be evaluated for this area.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _zoning_needs_review_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Zoning/use screening evidence is conflicting or incomplete and "
            "requires human review. It does not determine final legal use, zoning "
            "compliance, permit eligibility, vested rights, or buildability."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("needs-review", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=ZONING_NEEDS_REVIEW_CLAIM_CODE,
            domain=rule.domain,
            assertion="Zoning/use evidence requires human review before rule interpretation.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Resolve conflicting or incomplete zoning/use evidence before "
                "relying on this screening result."
            ),
        )

    def _zoning_stale_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Zoning/use screening evidence is marked stale in the fixture and "
            "should be refreshed before relying on zoning/use screening results. "
            "It does not determine final legal use, zoning compliance, permit "
            "eligibility, vested rights, or buildability."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("stale", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=ZONING_STALE_CLAIM_CODE,
            domain=rule.domain,
            assertion="Zoning/use evidence freshness requires review.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.INFORMATIONAL,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Refresh stale zoning/use screening source evidence before final "
                "interpretation."
            ),
        )

    def _water_no_context_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Water-context screening indicates no plausible water context in the "
            "fixture. This is screening only and does not determine water rights, "
            "well yield or viability, lawful hauling, utility/service availability, "
            "potable water, or final water availability."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("positive", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion="Water-context screening indicates no plausible water context.",
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _water_unknown_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Water-context screening remains unknown because required water source "
            "evidence failed or was unavailable. This does not establish water "
            "rights, well yield or viability, lawful hauling, utility/service "
            "availability, potable water, or final water availability."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("unknown", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code="WATER_SOURCE_UNAVAILABLE_UNKNOWN",
            domain=rule.domain,
            assertion="Water source data could not be evaluated for this area.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _water_needs_review_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Water-context screening evidence is conflicting or incomplete and "
            "requires human review. It does not determine water rights, well yield "
            "or viability, lawful hauling, utility/service availability, potable "
            "water, or final water availability."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("needs-review", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=WATER_NEEDS_REVIEW_CLAIM_CODE,
            domain=rule.domain,
            assertion="Water-context evidence requires human review before rule interpretation.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Resolve conflicting or incomplete water-context evidence before "
                "relying on this screening result."
            ),
        )

    def _water_stale_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Water-context screening evidence is marked stale in the fixture and "
            "should be refreshed before relying on water-context screening results. "
            "It does not determine water rights, well yield or viability, lawful "
            "hauling, utility/service availability, potable water, or final water "
            "availability."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("stale", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=WATER_STALE_CLAIM_CODE,
            domain=rule.domain,
            assertion="Water-context evidence freshness requires review.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.INFORMATIONAL,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Refresh stale water-context source evidence before final "
                "interpretation."
            ),
        )

    def _slope_insufficient_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        detail_parts: list[str] = []
        for e in evidence_records:
            val = e.observed_value.get("value")
            unit = e.observed_value.get("unit")
            ratio = e.observed_value.get("low_slope_area_ratio")
            mean_slope = e.observed_value.get("mean_slope_pct")
            if isinstance(val, (int, float)) and not isinstance(val, bool) and unit == "sq_m":
                acres = float(val) / 4047.0
                detail_parts.append(f"~{acres:.2f} ac low-slope area")
            if isinstance(ratio, (int, float)) and not isinstance(ratio, bool):
                detail_parts.append(f"{float(ratio):.0%} of parcel")
            if isinstance(mean_slope, (int, float)) and not isinstance(mean_slope, bool):
                detail_parts.append(f"mean slope ~{float(mean_slope):.1f}%")
        detail = f" ({'; '.join(detail_parts)})" if detail_parts else ""
        user_safe_language = (
            f"Slope/buildability screening indicates insufficient low-slope area{detail}. "
            "This is a screening proxy and does not determine final "
            "buildability, site-plan approval, or engineering feasibility."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("positive", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion="Slope screening indicates insufficient low-slope buildable area.",
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _slope_unknown_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Slope/buildability screening remains unknown because required source "
            "evidence failed or was unavailable. This does not establish buildability."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("unknown", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code="SLOPE_SOURCE_UNAVAILABLE_UNKNOWN",
            domain=rule.domain,
            assertion="Slope source data could not be evaluated for this area.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _slope_needs_review_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Slope/buildability screening evidence is conflicting or incomplete and "
            "requires human review. The available metrics are screening proxies, not "
            "engineering or site-plan determinations."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("needs-review", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=SLOPE_NEEDS_REVIEW_CLAIM_CODE,
            domain=rule.domain,
            assertion="Slope evidence requires human review before rule interpretation.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Resolve conflicting or incomplete slope/buildability screening "
                "evidence before relying on this result."
            ),
        )

    def _slope_stale_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Slope/buildability screening evidence is marked stale in the fixture "
            "and should be refreshed before relying on low-slope area metrics."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("stale", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=SLOPE_STALE_CLAIM_CODE,
            domain=rule.domain,
            assertion="Slope evidence freshness requires review.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.INFORMATIONAL,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Refresh stale slope/buildability screening source evidence before "
                "final interpretation."
            ),
        )

    def _wetland_positive_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        seen_labels: set[str] = set()
        wetland_labels: list[str] = []
        total_area_sq_m = 0.0
        for e in evidence_records:
            area = e.observed_value.get("mapped_wetland_area_sq_m")
            if isinstance(area, (int, float)) and not isinstance(area, bool):
                total_area_sq_m += float(area)
            wclass = e.observed_value.get("wetland_class")
            wtype = e.observed_value.get("wetland_type")
            label = (
                str(wclass) if isinstance(wclass, str) and wclass
                else str(wtype) if isinstance(wtype, str) and wtype
                else None
            )
            if label and label not in seen_labels:
                seen_labels.add(label)
                wetland_labels.append(label)
        detail_parts: list[str] = [f"{len(evidence_records)} NWI feature(s) intersect"]
        if total_area_sq_m > 0:
            detail_parts.append(f"~{total_area_sq_m / 4047:.2f} mapped acres")
        if wetland_labels:
            detail_parts.append("types: " + ", ".join(wetland_labels[:3]))
        detail = "; ".join(detail_parts)
        user_safe_language = (
            f"Mapped wetland/deepwater screening evidence intersects the area ({detail}). "
            "This is screening only and is not a jurisdictional wetland determination "
            "or field delineation."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("positive", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion="Mapped wetland/deepwater screening evidence intersects the area.",
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _wetland_unknown_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Wetland screening remains unknown because required source evidence "
            "failed or was unavailable. Wetland maps are screening inputs only."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("unknown", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code="WETLAND_SOURCE_UNAVAILABLE_UNKNOWN",
            domain=rule.domain,
            assertion="Wetland source data could not be evaluated for this area.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _wetland_needs_review_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Wetland screening evidence is conflicting or incomplete and requires "
            "human review. Maps are screening inputs, not field delineations or "
            "jurisdictional determinations."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("needs-review", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=WETLAND_NEEDS_REVIEW_CLAIM_CODE,
            domain=rule.domain,
            assertion="Wetland evidence requires human review before rule interpretation.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Resolve conflicting or incomplete wetland screening evidence before "
                "relying on this result."
            ),
        )

    def _wetland_stale_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Wetland screening evidence is marked stale in the fixture and should be "
            "refreshed before relying on mapped wetland/deepwater results."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("stale", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=WETLAND_STALE_CLAIM_CODE,
            domain=rule.domain,
            assertion="Wetland evidence freshness requires review.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.INFORMATIONAL,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Refresh stale wetland screening source evidence before final "
                "interpretation."
            ),
        )

    def _flood_positive_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        zones = sorted({
            z.upper()
            for e in evidence_records
            for z in _flood_zone_values(e)
            if z.upper() in HIGH_RISK_FLOOD_ZONES
        })
        zone_str = ", ".join(zones) if zones else "high-risk"
        user_safe_language = (
            f"FEMA NFHL screening detected a high-risk flood zone ({zone_str}). "
            "This is screening only — not a flood determination or elevation "
            "certificate. Confirm current FEMA flood map panel, flood insurance "
            "requirements, and local floodplain permitting before building."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("positive", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion=(
                f"High-risk FEMA flood zone detected ({zone_str}) — "
                "confirm flood determination and insurance requirements."
            ),
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _flood_unknown_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Flood screening remains unknown because required source evidence failed "
            "or was unavailable."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("unknown", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code="FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
            domain=rule.domain,
            assertion="Flood source data could not be evaluated for this area.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _flood_needs_review_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Flood screening evidence is conflicting or incomplete and requires human "
            "review before interpreting floodplain constraints."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("needs-review", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=FLOOD_NEEDS_REVIEW_CLAIM_CODE,
            domain=rule.domain,
            assertion="Flood evidence requires human review before rule interpretation.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Resolve conflicting or incomplete flood evidence before relying on "
                "this screening result."
            ),
        )

    def _flood_stale_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Flood screening evidence is marked stale in the fixture and should be "
            "refreshed before relying on the result."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("stale", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=FLOOD_STALE_CLAIM_CODE,
            domain=rule.domain,
            assertion="Flood evidence freshness requires review.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.INFORMATIONAL,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Refresh stale flood screening source evidence before final interpretation."
            ),
        )

    def _flood_moderate_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        zones = sorted({
            z.upper()
            for e in evidence_records
            for z in _flood_zone_values(e)
            if z.upper() in _MODERATE_RISK_FLOOD_ZONES
        })
        zone_str = ", ".join(zones) if zones else "moderate/undetermined"
        user_safe_language = (
            f"FEMA NFHL screening detected a moderate or undetermined flood risk zone "
            f"({zone_str}). This is screening only — not a flood determination or elevation "
            "certificate. Verify current FEMA flood map panel, consider flood insurance "
            "implications, and confirm with local floodplain administrator before building."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"
        return ClaimContract(
            claim_id=self._deterministic_claim_id(
                "flood-moderate", rule, area_id, evidence_ids
            ),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion=(
                f"Moderate or undetermined FEMA flood zone detected ({zone_str}) — "
                "verify with floodplain administrator."
            ),
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=ConfidenceBand.LOW,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _not_evaluated_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = NOT_EVALUATED_CAVEATS[rule.domain]
        if caveat_text and caveat_text not in user_safe_language:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id(
                "not-evaluated",
                rule,
                area_id,
                evidence_ids,
            ),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion=f"{rule.domain} screening is not supported in this tool version.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _soil_screening_review_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "USDA NRCS SSURGO mapunit/component screening evidence is present for "
            "the area. This is screening only and does not determine septic approval, "
            "perc results, soil suitability, engineering feasibility, permitting, or "
            "buildability. Verify soil and septic feasibility with perc testing, "
            "county health department records, and a septic engineer."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id(
                "soil-screening-review",
                rule,
                area_id,
                evidence_ids,
            ),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion=(
                "SSURGO soil mapunit screening evidence requires professional "
                "soil/septic review."
            ),
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _soil_poor_drainage_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        drainage_vals = sorted({
            str(e.observed_value["drainage_class"]).lower()
            for e in evidence_records
            if isinstance(e.observed_value.get("drainage_class"), str)
        })
        hydric = any(
            (isinstance(e.observed_value.get("hydric_rating"), str)
             and str(e.observed_value.get("hydric_rating", "")).lower() in ("yes", "true"))
            or (e.observed_value.get("hydric_rating") is True)
            for e in evidence_records
        )
        wt_depths = [
            float(e.observed_value["water_table_depth_cm"])  # type: ignore[arg-type]
            for e in evidence_records
            if isinstance(e.observed_value.get("water_table_depth_cm"), (int, float))
            and not isinstance(e.observed_value.get("water_table_depth_cm"), bool)
        ]
        detail_parts: list[str] = []
        if drainage_vals:
            detail_parts.append("drainage class: " + ", ".join(drainage_vals))
        if hydric:
            detail_parts.append("hydric soils detected")
        if wt_depths:
            detail_parts.append(f"water table ~{min(wt_depths):.0f}cm depth")
        detail = "; ".join(detail_parts) if detail_parts else "poor/hydric drainage indicators"
        user_safe_language = (
            f"SSURGO screening detected potential soil drainage limitations ({detail}). "
            "This is screening only and does not determine septic approval, perc results, "
            "or buildability. Conduct perc testing, consult county health department, "
            "and evaluate with a licensed septic engineer before planning on-site wastewater."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"
        return ClaimContract(
            claim_id=self._deterministic_claim_id(
                "soil-poor-drainage",
                rule,
                area_id,
                evidence_ids,
            ),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion=(
                "Poorly drained or hydric soils detected in SSURGO screening — "
                "septic feasibility requires professional evaluation."
            ),
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=ConfidenceBand.LOW,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _parcel_screen_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "County GIS parcel screening evidence identified for the area. "
            "Parcel boundaries, acreage, and zoning designations from county GIS "
            "are approximate only — not a survey, not a title determination, and "
            "not a buildability or legal-access determination. Verify all parcel "
            "data with the county Register of Deeds, county GIS, and a licensed "
            "surveyor before relying on this information."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id(
                "parcel-screen",
                rule,
                area_id,
                evidence_ids,
            ),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion=(
                "County GIS parcel screening evidence identified for AOI — "
                "verify boundaries, acreage, and zoning with authoritative sources."
            ),
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.LOW,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _env_hazard_proximity_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        count_str = ""
        for e in evidence_records:
            count = e.observed_value.get("regulated_facility_count")
            if isinstance(count, (int, float)) and not isinstance(count, bool) and int(count) > 0:
                count_str = f" ({int(count)} regulated facility/facilities in proximity)"
                break
        user_safe_language = (
            f"EPA ECHO facility-proximity screening indicates regulated facilities near "
            f"the area{count_str}. A nearby regulated facility does not prove subject-property "
            "contamination, plume extent, exposure pathway, or legal liability. ECHO data "
            "may lag source entry. A Phase I/II ESA is required for regulatory and "
            "transactional environmental due diligence."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("positive", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion=(
                "Environmental hazard screening found regulated facilities "
                "in proximity to the area."
            ),
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _env_hazard_unknown_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Environmental hazard screening remains unknown because the EPA ECHO "
            "source evidence failed or was unavailable. A nearby regulated facility "
            "does not prove contamination. A Phase I/II ESA is required for regulatory "
            "and transactional environmental due diligence."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("unknown", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code="ENV_SOURCE_UNAVAILABLE_UNKNOWN",
            domain=rule.domain,
            assertion="Environmental hazard source data could not be evaluated for this area.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _env_hazard_needs_review_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Environmental hazard screening evidence is conflicting or incomplete and "
            "requires human review. A nearby regulated facility does not prove "
            "contamination. A Phase I/II ESA is required for regulatory and transactional "
            "environmental due diligence."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("needs-review", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=ENV_HAZARD_NEEDS_REVIEW_CLAIM_CODE,
            domain=rule.domain,
            assertion=(
                "Environmental hazard evidence requires human review "
                "before rule interpretation."
            ),
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Resolve conflicting or incomplete environmental hazard screening "
                "evidence before relying on this result."
            ),
        )

    def _env_hazard_stale_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Environmental hazard screening evidence is marked stale and should be "
            "refreshed before relying on facility-proximity results. A nearby regulated "
            "facility does not prove contamination."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("stale", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=ENV_HAZARD_STALE_CLAIM_CODE,
            domain=rule.domain,
            assertion="Environmental hazard evidence freshness requires review.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.INFORMATIONAL,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=(
                "Refresh stale environmental hazard screening source evidence before "
                "final interpretation."
            ),
        )

    def _minerals_active_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        count_str = ""
        case_str = ""
        for e in evidence_records:
            count = e.observed_value.get("blm_active_mining_claim_count")
            if isinstance(count, (int, float)) and not isinstance(count, bool) and int(count) > 0:
                count_str = f" ({int(count)} active claim(s))"
                name = e.observed_value.get("primary_blm_mlrs_case_name")
                serial = e.observed_value.get("primary_blm_mlrs_case_serial_number")
                if isinstance(name, str) and name:
                    serial_suffix = f" #{serial}" if isinstance(serial, str) and serial else ""
                    case_str = f" Primary: {name}{serial_suffix}."
                break
        user_safe_language = (
            f"BLM MLRS screening indicates active federal mining claims in the area bbox{count_str}.{case_str} "  # noqa: E501
            "Active mining claims may affect surface use, development rights, and access. "
            "This is a geospatial bounding-box screen only and does not determine parcel-level "
            "mineral rights ownership. Verify through title search and consult a title attorney."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("positive", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=MINERALS_ACTIVE_CLAIM_CODE,
            domain=rule.domain,
            assertion="BLM MLRS screening found active federal mining claims in the query area.",
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _minerals_unknown_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Minerals/mining screening remains unknown because BLM MLRS or USGS MRDS "
            "source data failed or was unavailable. Verify through title search and "
            "appropriate state or federal mineral records."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("unknown", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=MINERALS_SOURCE_UNAVAILABLE_CLAIM_CODE,
            domain=rule.domain,
            assertion="Minerals/mining source data could not be evaluated for this area.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _broadband_no_access_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "FCC broadband availability screening indicates no broadband providers "
            "reported for this area. FCC data may lag actual availability, especially "
            "for fixed wireless and newer deployments. Verify directly with local ISPs "
            "before relying on this area for remote work or connected farm operations."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("positive", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=BROADBAND_NO_ACCESS_CLAIM_CODE,
            domain=rule.domain,
            assertion="FCC broadband screening found no broadband service reported for this area.",
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=_lowest_confidence(evidence_records),
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _broadband_unknown_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Broadband availability screening remains unknown because FCC source data "
            "failed or was unavailable. Verify internet connectivity options with local "
            "ISPs before relying on this area for remote work or farm operations."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("unknown", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=BROADBAND_SOURCE_UNAVAILABLE_CLAIM_CODE,
            domain=rule.domain,
            assertion="Broadband availability source data could not be evaluated for this area.",
            user_safe_language=user_safe_language,
            severity=SeverityBand.UNKNOWN,
            confidence=ConfidenceBand.UNKNOWN,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _geology_not_evaluated_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        unit_parts: list[str] = []
        for e in evidence_records:
            label = e.observed_value.get("primary_geologic_unit_label")
            formation = e.observed_value.get("primary_geologic_formation")
            if isinstance(label, str) and label:
                unit_parts.append(label)
            if isinstance(formation, str) and formation and formation not in unit_parts:
                unit_parts.append(formation)
        context = f" (screened unit: {'; '.join(unit_parts[:2])})" if unit_parts else ""
        user_safe_language = (
            f"Geologic map context was retrieved for the area{context} but geologic hazard "
            "evaluation is not supported by this tool. This does not determine "
            "geologic hazard, geotechnical suitability, subsidence risk, radon "
            "potential, or engineering feasibility. Consult a licensed geologist "
            "or geotechnical engineer if geologic conditions are a concern."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"
        return ClaimContract(
            claim_id=self._deterministic_claim_id(
                "geology-not-evaluated", rule, area_id, evidence_ids
            ),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion=(
                "Geologic map context retrieved — geologic hazard determination "
                "is not supported by this tool version."
            ),
            user_safe_language=user_safe_language,
            severity=rule.severity_on_fail,
            confidence=ConfidenceBand.LOW,
            evidence_ids=evidence_ids,
            rule_code=rule.code,
            ruleset_id=self._ruleset.ruleset_id,
            ruleset_version=self._ruleset.version,
            verification_required=True,
            verification_task=rule.verification_task,
        )

    def _deterministic_claim_id(
        self,
        kind: str,
        rule: HardGateRule,
        area_id: UUID,
        evidence_ids: list[UUID],
    ) -> UUID:
        seed = "|".join(
            [
                "land-dd-claim",
                self._ruleset.ruleset_id,
                self._ruleset.version,
                rule.code,
                kind,
                str(area_id),
                *[str(evidence_id) for evidence_id in evidence_ids],
            ]
        )
        return uuid5(NAMESPACE_URL, seed)


def load_ruleset(path: Path) -> RuleSet:
    data = _parse_ruleset_yaml(path.read_text(encoding="utf-8"))
    ruleset_id = _require_key(data, "id")
    version = _require_key(data, "version")
    hard_gate_raw = data.get("hard_gates")
    if not isinstance(hard_gate_raw, list):
        raise ValueError("hard_gates must be a list")
    hard_gates_list: list[dict[str, str]] = []
    for item in hard_gate_raw:
        if not isinstance(item, dict):
            raise ValueError(f"hard_gates entry must be a mapping, got {type(item)!r}")
        hard_gates_list.append({str(k): str(v) for k, v in item.items()})
    hard_gates = tuple(_hard_gate_from_mapping(mapping) for mapping in hard_gates_list)
    forbidden_raw = data.get("forbidden_language")
    forbidden = frozenset(
        str(p)
        for p in (forbidden_raw if isinstance(forbidden_raw, list) else [])
        if isinstance(p, str) and p.strip()
    )
    return RuleSet(
        ruleset_id=ruleset_id,
        version=version,
        hard_gates=hard_gates,
        forbidden_language=forbidden,
    )


def _hard_gate_from_mapping(mapping: dict[str, str]) -> HardGateRule:
    return HardGateRule(
        code=_require_key(mapping, "code"),
        domain=_require_key(mapping, "domain"),
        severity_on_fail=SeverityBand(_require_key(mapping, "severity_on_fail")),
        condition=_require_key(mapping, "condition"),
        claim_code=_require_key(mapping, "claim_code"),
        verification_task=_require_key(mapping, "verification_task"),
    )


def _parse_ruleset_yaml(text: str) -> dict[str, object]:
    hard_gates_list: list[dict[str, str]] = []
    forbidden_language_list: list[str] = []
    ruleset: dict[str, object] = {
        "hard_gates": hard_gates_list,
        "forbidden_language": forbidden_language_list,
    }

    section = ""
    current_gate: dict[str, str] | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        stripped = raw_line.strip()
        if stripped == "ruleset:":
            section = "ruleset"
            continue

        if raw_line.startswith("  ") and not raw_line.startswith("    "):
            if current_gate is not None:
                hard_gates_list.append(current_gate)
                current_gate = None
            key, value = _split_yaml_key_value(stripped)
            section = key
            if value is not None:
                ruleset[key] = value
            continue

        if section == "forbidden_language":
            if raw_line.startswith("    - "):
                phrase = stripped.removeprefix("- ").strip("'\"")
                forbidden_language_list.append(phrase)
            continue

        if section != "hard_gates":
            continue

        if raw_line.startswith("    - "):
            if current_gate is not None:
                hard_gates_list.append(current_gate)
            current_gate = {}
            key, value = _split_yaml_key_value(stripped.removeprefix("- "))
            if value is None:
                raise ValueError(f"hard_gates entry '{key}' requires a scalar value")
            current_gate[key] = value
            continue

        if current_gate is not None and raw_line.startswith("      "):
            key, value = _split_yaml_key_value(stripped)
            if value is None:
                raise ValueError(f"hard_gates field '{key}' requires a scalar value")
            current_gate[key] = value

    if current_gate is not None:
        hard_gates_list.append(current_gate)

    return ruleset


def _split_yaml_key_value(line: str) -> tuple[str, str | None]:
    key, separator, value = line.partition(":")
    if separator == "":
        raise ValueError(f"Expected YAML key/value line, got '{line}'")
    normalized_value = value.strip()
    if not normalized_value:
        return key.strip(), None
    return key.strip(), normalized_value.strip("'\"")


def _require_key(
    mapping: dict[str, object] | dict[str, str],
    key: str,
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"ruleset field '{key}' is required")
    return value


def _is_access_no_adjacency_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "access" or _is_access_source_failure(evidence):
        return False
    if any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ACCESS_NO_ADJACENCY_KEYS
    ):
        return True
    return any(
        evidence.observed_value.get(key) is not None
        and _observed_false(evidence.observed_value.get(key))
        for key in ACCESS_ADJACENCY_TRUE_KEYS
    )


def _is_access_adjacency_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "access" or _is_access_source_failure(evidence):
        return False
    if any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ACCESS_NO_ADJACENCY_KEYS
    ):
        return False
    return any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ACCESS_ADJACENCY_TRUE_KEYS
    )


def _is_access_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "access" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_stale_access_evidence(evidence: EvidenceContract) -> bool:
    return (
        evidence.domain == "access"
        and not _is_access_source_failure(evidence)
        and _observed_bool(evidence.observed_value.get("source_stale"))
    )


def _is_zoning_prohibited_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "zoning" or _is_zoning_source_failure(evidence):
        return False
    has_prohibited_signal = any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ZONING_PROHIBITED_KEYS
    )
    has_unsupported_signal = any(
        evidence.observed_value.get(key) is not None
        and _observed_false(evidence.observed_value.get(key))
        for key in ZONING_ALLOWED_KEYS
    )
    return has_prohibited_signal or has_unsupported_signal


def _is_zoning_allowed_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "zoning" or _is_zoning_source_failure(evidence):
        return False
    if any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ZONING_PROHIBITED_KEYS
    ):
        return False
    return any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ZONING_ALLOWED_KEYS
    )


def _is_incomplete_zoning_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "zoning" or _is_zoning_source_failure(evidence):
        return False
    has_prohibited_signal = any(
        evidence.observed_value.get(key) is not None for key in ZONING_PROHIBITED_KEYS
    )
    has_allowed_signal = any(
        evidence.observed_value.get(key) is not None for key in ZONING_ALLOWED_KEYS
    )
    return not has_prohibited_signal and not has_allowed_signal


def _is_zoning_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "zoning" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_stale_zoning_evidence(evidence: EvidenceContract) -> bool:
    return (
        evidence.domain == "zoning"
        and not _is_zoning_source_failure(evidence)
        and _observed_bool(evidence.observed_value.get("source_stale"))
    )


def _is_water_no_context_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "water" or _is_water_source_failure(evidence):
        return False
    if _is_conflicting_water_evidence(evidence):
        return False
    has_no_context_signal = any(
        _observed_bool(evidence.observed_value.get(key))
        for key in WATER_NO_CONTEXT_KEYS
    )
    has_context_absence_signal = any(
        evidence.observed_value.get(key) is not None
        and _observed_false(evidence.observed_value.get(key))
        for key in WATER_CONTEXT_KEYS
    )
    return has_no_context_signal or has_context_absence_signal


def _is_water_context_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "water" or _is_water_source_failure(evidence):
        return False
    if any(
        _observed_bool(evidence.observed_value.get(key))
        for key in WATER_NO_CONTEXT_KEYS
    ):
        return False
    return any(
        _observed_bool(evidence.observed_value.get(key))
        for key in WATER_CONTEXT_KEYS
    )


def _is_incomplete_water_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "water" or _is_water_source_failure(evidence):
        return False
    has_no_context_signal = any(
        evidence.observed_value.get(key) is not None for key in WATER_NO_CONTEXT_KEYS
    )
    has_context_signal = any(
        evidence.observed_value.get(key) is not None for key in WATER_CONTEXT_KEYS
    )
    return not has_no_context_signal and not has_context_signal


def _is_conflicting_water_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "water" or _is_water_source_failure(evidence):
        return False
    has_no_context_signal = any(
        _observed_bool(evidence.observed_value.get(key))
        for key in WATER_NO_CONTEXT_KEYS
    )
    has_context_signal = any(
        _observed_bool(evidence.observed_value.get(key))
        for key in WATER_CONTEXT_KEYS
    )
    return has_no_context_signal and has_context_signal


def _is_water_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "water" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_stale_water_evidence(evidence: EvidenceContract) -> bool:
    return (
        evidence.domain == "water"
        and not _is_water_source_failure(evidence)
        and _observed_bool(evidence.observed_value.get("source_stale"))
    )


def _is_mapped_wetland_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "wetlands" or _is_wetland_source_failure(evidence):
        return False
    if any(
        _observed_bool(evidence.observed_value.get(key))
        for key in WETLAND_INTERSECTION_KEYS
    ):
        return True
    area = evidence.observed_value.get("mapped_wetland_area_sq_m")
    return _is_positive_number(area)


def _is_negative_wetland_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "wetlands" or _is_wetland_source_failure(evidence):
        return False
    if evidence.is_negative_evidence:
        return True
    if any(
        evidence.observed_value.get(key) is not None
        and _observed_false(evidence.observed_value.get(key))
        for key in WETLAND_INTERSECTION_KEYS
    ):
        return True
    area = evidence.observed_value.get("mapped_wetland_area_sq_m")
    return area is not None and _observed_number(area) == 0


def _is_wetland_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "wetlands" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_stale_wetland_evidence(evidence: EvidenceContract) -> bool:
    return (
        evidence.domain == "wetlands"
        and not _is_wetland_source_failure(evidence)
        and _observed_bool(evidence.observed_value.get("source_stale"))
    )


def _is_insufficient_slope_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "buildability" or _is_slope_source_failure(evidence):
        return False
    return _observed_bool(
        evidence.observed_value.get("insufficient_low_slope_buildable_area")
    )


def _is_sufficient_slope_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "buildability" or _is_slope_source_failure(evidence):
        return False
    if _observed_bool(
        evidence.observed_value.get("insufficient_low_slope_buildable_area")
    ):
        return False
    if _observed_false(
        evidence.observed_value.get("insufficient_low_slope_buildable_area")
    ):
        return True
    return _observed_bool(
        evidence.observed_value.get("low_slope_buildable_area_sufficient")
    )


def _is_slope_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "buildability" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_stale_slope_evidence(evidence: EvidenceContract) -> bool:
    return (
        evidence.domain == "buildability"
        and not _is_slope_source_failure(evidence)
        and _observed_bool(evidence.observed_value.get("source_stale"))
    )


def _is_high_risk_flood_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "flood" or evidence.is_source_failure:
        return False
    if _observed_bool(evidence.observed_value.get("intersects_high_risk_flood_zone")):
        return True
    for zone in _flood_zone_values(evidence):
        if zone.upper() in HIGH_RISK_FLOOD_ZONES:
            return True
    return False


def _is_negative_flood_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "flood" or _is_flood_source_failure(evidence):
        return False
    if evidence.is_negative_evidence:
        return True
    high_risk_intersection = evidence.observed_value.get("intersects_high_risk_flood_zone")
    if high_risk_intersection is not None:
        return _observed_false(high_risk_intersection)
    zones = _flood_zone_values(evidence)
    return bool(zones) and all(zone.upper() not in HIGH_RISK_FLOOD_ZONES for zone in zones)


def _is_moderate_risk_flood_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "flood" or evidence.is_source_failure:
        return False
    for zone in _flood_zone_values(evidence):
        if zone.upper() in _MODERATE_RISK_FLOOD_ZONES:
            return True
    return False


def _is_flood_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "flood" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_not_evaluated_source_failure(
    evidence: EvidenceContract,
    domain: str,
) -> bool:
    return evidence.domain == domain and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_soil_screening_evidence(evidence: EvidenceContract) -> bool:
    return (
        evidence.domain == "soil_septic"
        and not _is_not_evaluated_source_failure(evidence, "soil_septic")
        and evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
        and evidence.evidence_code == "SSURGO_SOIL_MAPUNIT_INTERSECTION"
        and _observed_bool(evidence.observed_value.get("intersects_soil_mapunit"))
    )


def _is_soil_poor_drainage_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain not in ("soil_septic", "soils") or evidence.is_source_failure:
        return False
    dc = evidence.observed_value.get("drainage_class")
    if isinstance(dc, str) and dc.lower() in _SSURGO_POOR_DRAINAGE:
        return True
    hr = evidence.observed_value.get("hydric_rating")
    if isinstance(hr, str) and hr.lower() in ("yes", "true"):
        return True
    if isinstance(hr, bool) and hr is True:
        return True
    return False


def _is_county_parcel_screen_evidence(evidence: EvidenceContract) -> bool:
    return (
        evidence.domain == "parcels"
        and not evidence.is_source_failure
        and evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
        and evidence.evidence_code == "COUNTY_PARCEL_INTERSECTION"
    )


def _is_stale_flood_evidence(evidence: EvidenceContract) -> bool:
    return (
        evidence.domain == "flood"
        and not _is_flood_source_failure(evidence)
        and _observed_bool(evidence.observed_value.get("source_stale"))
    )


def _is_env_hazard_proximity_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "env_hazard" or _is_env_hazard_source_failure(evidence):
        return False
    if _is_conflicting_env_hazard_evidence(evidence):
        return False
    has_proximity = any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ENV_HAZARD_PROXIMITY_KEYS
    )
    no_proximity_false = any(
        evidence.observed_value.get(key) is not None
        and _observed_false(evidence.observed_value.get(key))
        for key in ENV_HAZARD_NO_PROXIMITY_KEYS
    )
    return has_proximity or no_proximity_false


def _is_env_hazard_no_proximity_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "env_hazard" or _is_env_hazard_source_failure(evidence):
        return False
    if any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ENV_HAZARD_PROXIMITY_KEYS
    ):
        return False
    return any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ENV_HAZARD_NO_PROXIMITY_KEYS
    )


def _is_incomplete_env_hazard_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "env_hazard" or _is_env_hazard_source_failure(evidence):
        return False
    has_proximity_signal = any(
        evidence.observed_value.get(key) is not None
        for key in ENV_HAZARD_PROXIMITY_KEYS
    )
    has_no_proximity_signal = any(
        evidence.observed_value.get(key) is not None
        for key in ENV_HAZARD_NO_PROXIMITY_KEYS
    )
    return not has_proximity_signal and not has_no_proximity_signal


def _is_conflicting_env_hazard_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "env_hazard" or _is_env_hazard_source_failure(evidence):
        return False
    has_proximity = any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ENV_HAZARD_PROXIMITY_KEYS
    )
    has_no_proximity = any(
        _observed_bool(evidence.observed_value.get(key))
        for key in ENV_HAZARD_NO_PROXIMITY_KEYS
    )
    return has_proximity and has_no_proximity


def _is_env_hazard_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "env_hazard" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_stale_env_hazard_evidence(evidence: EvidenceContract) -> bool:
    return (
        evidence.domain == "env_hazard"
        and not _is_env_hazard_source_failure(evidence)
        and _observed_bool(evidence.observed_value.get("source_stale"))
    )


def _is_broadband_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "broadband" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_broadband_no_access_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "broadband" or _is_broadband_source_failure(evidence):
        return False
    return _observed_false(evidence.observed_value.get("has_any_broadband"))


def _is_minerals_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "minerals" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_minerals_active_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "minerals" or _is_minerals_source_failure(evidence):
        return False
    count = _observed_number(evidence.observed_value.get("blm_active_mining_claim_count"))
    return count is not None and count > 0


def _is_geology_not_evaluated_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "geology" or evidence.is_source_failure:
        return False
    return evidence.observed_value.get("geologic_hazard_determined") is False


def _flood_zone_values(evidence: EvidenceContract) -> list[str]:
    values: list[str] = []
    for key in ("flood_zone", "flood_zones", "flood_zone_code", "zone"):
        values.extend(_observed_values(evidence.observed_value.get(key)))
    return values


def _observed_values(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _observed_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return False


def _observed_false(value: object) -> bool:
    if isinstance(value, bool):
        return not value
    if isinstance(value, str):
        return value.strip().lower() in {"0", "false", "no"}
    return False


def _observed_number(value: object) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _is_positive_number(value: object) -> bool:
    number = _observed_number(value)
    return number is not None and number > 0


def _sorted_evidence_ids(evidence_records: list[EvidenceContract]) -> list[UUID]:
    return sorted(
        [evidence.evidence_id for evidence in evidence_records],
        key=str,
    )


def _dedupe_evidence_records(evidence_records: list[EvidenceContract]) -> list[EvidenceContract]:
    by_id = {evidence.evidence_id: evidence for evidence in evidence_records}
    return sorted(by_id.values(), key=lambda evidence: str(evidence.evidence_id))


def _format_caveats(evidence_records: list[EvidenceContract]) -> str:
    caveats = {
        evidence.caveat.strip()
        for evidence in evidence_records
        if evidence.caveat is not None and evidence.caveat.strip()
    }
    return "; ".join(sorted(caveats))


def _lowest_confidence(evidence_records: list[EvidenceContract]) -> ConfidenceBand:
    order = {
        ConfidenceBand.UNKNOWN: 0,
        ConfidenceBand.VERY_LOW: 1,
        ConfidenceBand.LOW: 2,
        ConfidenceBand.MEDIUM: 3,
        ConfidenceBand.HIGH: 4,
        ConfidenceBand.VERY_HIGH: 5,
    }
    return min(
        (evidence.confidence for evidence in evidence_records),
        key=lambda confidence: order[confidence],
    )


__all__ = [
    "BROADBAND_NO_ACCESS_CLAIM_CODE",
    "BROADBAND_NO_ACCESS_CONDITION",
    "BROADBAND_SOURCE_UNAVAILABLE_CLAIM_CODE",
    "BROADBAND_SOURCE_UNAVAILABLE_CONDITION",
    "DEFAULT_RULESET_PATH",
    "ENV_HAZARD_CONDITION",
    "ENV_HAZARD_NEEDS_REVIEW_CLAIM_CODE",
    "ENV_HAZARD_NO_PROXIMITY_KEYS",
    "ENV_HAZARD_PROXIMITY_KEYS",
    "ENV_HAZARD_STALE_CLAIM_CODE",
    "GEOLOGY_NOT_EVALUATED_CLAIM_CODE",
    "GEOLOGY_NOT_EVALUATED_CONDITION",
    "HardGateRule",
    "MINERALS_ACTIVE_CLAIM_CODE",
    "MINERALS_ACTIVE_CLAIM_CONDITION",
    "MINERALS_SOURCE_UNAVAILABLE_CLAIM_CODE",
    "MINERALS_SOURCE_UNAVAILABLE_CONDITION",
    "RuleEngine",
    "RuleSet",
    "load_ruleset",
]
