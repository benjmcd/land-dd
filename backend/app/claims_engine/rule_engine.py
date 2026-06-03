from __future__ import annotations

from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, EvidenceType, SeverityBand
from app.domain.evidence_contracts import EvidenceContract

DEFAULT_RULESET_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "ruleset_homestead_mvp.yaml"
)
FLOOD_HIGH_RISK_CONDITION = "material_intersection_with_high_risk_flood_zone"
ACCESS_NO_PUBLIC_ROAD_CONDITION = "no_public_road_adjacency_or_access_source_unavailable"
ZONING_INTENDED_USE_CONDITION = "intended_residential_use_prohibited_or_unknown"
WETLAND_MAPPED_CONDITION = "material_intersection_with_mapped_wetlands"
SLOPE_INSUFFICIENT_CONDITION = "insufficient_low_slope_buildable_area"
HIGH_RISK_FLOOD_ZONES = {"A", "AE", "AH", "AO", "A99", "V", "VE"}
ACCESS_ADJACENCY_TRUE_KEYS = ("public_road_adjacency", "has_public_road_adjacency")
ACCESS_NO_ADJACENCY_KEYS = ("no_public_road_adjacency",)
ACCESS_NEEDS_REVIEW_CLAIM_CODE = "ACCESS_EVIDENCE_NEEDS_REVIEW"
ACCESS_STALE_CLAIM_CODE = "ACCESS_STALE_EVIDENCE_NEEDS_REVIEW"
ZONING_ALLOWED_KEYS = ("intended_residential_use_allowed",)
ZONING_PROHIBITED_KEYS = ("intended_residential_use_prohibited",)
ZONING_NEEDS_REVIEW_CLAIM_CODE = "ZONING_EVIDENCE_NEEDS_REVIEW"
ZONING_STALE_CLAIM_CODE = "ZONING_STALE_EVIDENCE_NEEDS_REVIEW"
WETLAND_INTERSECTION_KEYS = ("intersects_mapped_wetlands",)
WETLAND_NEEDS_REVIEW_CLAIM_CODE = "WETLAND_EVIDENCE_NEEDS_REVIEW"
WETLAND_STALE_CLAIM_CODE = "WETLAND_STALE_EVIDENCE_NEEDS_REVIEW"
SLOPE_NEEDS_REVIEW_CLAIM_CODE = "SLOPE_EVIDENCE_NEEDS_REVIEW"
SLOPE_STALE_CLAIM_CODE = "SLOPE_STALE_EVIDENCE_NEEDS_REVIEW"
FLOOD_NEEDS_REVIEW_CLAIM_CODE = "FLOOD_EVIDENCE_NEEDS_REVIEW"
FLOOD_STALE_CLAIM_CODE = "FLOOD_STALE_EVIDENCE_NEEDS_REVIEW"


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
        flood_rule = self._ruleset.hard_gate_for_condition(FLOOD_HIGH_RISK_CONDITION)
        slope_rule = self._ruleset.hard_gate_for_condition(SLOPE_INSUFFICIENT_CONDITION)
        wetland_rule = self._ruleset.hard_gate_for_condition(WETLAND_MAPPED_CONDITION)
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
            stale_evidence = [
                evidence
                for evidence in area_evidence
                if _is_stale_flood_evidence(evidence)
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
        return claims

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
        user_safe_language = (
            "Zoning/use screening indicates the intended residential or homestead "
            "use is prohibited or unsupported in the fixture. This is source-linked "
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

    def _slope_insufficient_claim(
        self,
        area_id: UUID,
        rule: HardGateRule,
        evidence_records: list[EvidenceContract],
    ) -> ClaimContract:
        evidence_ids = _sorted_evidence_ids(evidence_records)
        caveat_text = _format_caveats(evidence_records)
        user_safe_language = (
            "Slope/buildability screening indicates insufficient low-slope area in "
            "the fixture. This is a screening proxy and does not determine final "
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
        user_safe_language = (
            "Mapped wetland/deepwater screening evidence intersects the area. "
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
        user_safe_language = (
            "Screening evidence indicates possible floodplain constraints; "
            "confirm flood zone, local permitting, and insurance implications."
        )
        if caveat_text:
            user_safe_language = f"{user_safe_language} Evidence caveat: {caveat_text}"

        return ClaimContract(
            claim_id=self._deterministic_claim_id("positive", rule, area_id, evidence_ids),
            area_id=area_id,
            claim_code=rule.claim_code,
            domain=rule.domain,
            assertion="Mapped screening evidence indicates high-risk flood zone intersection.",
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
    hard_gate_mappings = data.get("hard_gates")
    if not isinstance(hard_gate_mappings, list):
        raise ValueError("hard_gates must be a list")
    hard_gates = tuple(
        _hard_gate_from_mapping(mapping)
        for mapping in hard_gate_mappings
    )
    return RuleSet(ruleset_id=ruleset_id, version=version, hard_gates=hard_gates)


def _hard_gate_from_mapping(mapping: dict[str, str]) -> HardGateRule:
    return HardGateRule(
        code=_require_key(mapping, "code"),
        domain=_require_key(mapping, "domain"),
        severity_on_fail=SeverityBand(_require_key(mapping, "severity_on_fail")),
        condition=_require_key(mapping, "condition"),
        claim_code=_require_key(mapping, "claim_code"),
        verification_task=_require_key(mapping, "verification_task"),
    )


def _parse_ruleset_yaml(text: str) -> dict[str, str | list[dict[str, str]]]:
    ruleset: dict[str, str | list[dict[str, str]]] = {"hard_gates": []}
    hard_gates = ruleset["hard_gates"]
    if not isinstance(hard_gates, list):
        raise ValueError("hard_gates must be a list")

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
                hard_gates.append(current_gate)
                current_gate = None
            key, value = _split_yaml_key_value(stripped)
            section = key
            if value is not None:
                ruleset[key] = value
            continue

        if section != "hard_gates":
            continue

        if raw_line.startswith("    - "):
            if current_gate is not None:
                hard_gates.append(current_gate)
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
        hard_gates.append(current_gate)

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
    mapping: dict[str, str] | dict[str, str | list[dict[str, str]]],
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


def _is_flood_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "flood" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


def _is_stale_flood_evidence(evidence: EvidenceContract) -> bool:
    return (
        evidence.domain == "flood"
        and not _is_flood_source_failure(evidence)
        and _observed_bool(evidence.observed_value.get("source_stale"))
    )


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
    "DEFAULT_RULESET_PATH",
    "HardGateRule",
    "RuleEngine",
    "RuleSet",
    "load_ruleset",
]
