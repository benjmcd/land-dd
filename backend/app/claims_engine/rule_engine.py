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
HIGH_RISK_FLOOD_ZONES = {"A", "AE", "AH", "AO", "A99", "V", "VE"}


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
        flood_rule = self._ruleset.hard_gate_for_condition(FLOOD_HIGH_RISK_CONDITION)
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
            if flood_positive:
                claims.append(self._flood_positive_claim(area_id, flood_rule, flood_positive))
            if flood_failures:
                claims.append(self._flood_unknown_claim(area_id, flood_rule, flood_failures))
        return claims

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


def _is_high_risk_flood_evidence(evidence: EvidenceContract) -> bool:
    if evidence.domain != "flood" or evidence.is_source_failure:
        return False
    if _observed_bool(evidence.observed_value.get("intersects_high_risk_flood_zone")):
        return True
    for zone in _observed_values(evidence.observed_value.get("flood_zone")):
        if zone.upper() in HIGH_RISK_FLOOD_ZONES:
            return True
    return False


def _is_flood_source_failure(evidence: EvidenceContract) -> bool:
    return evidence.domain == "flood" and (
        evidence.is_source_failure or evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    )


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


def _sorted_evidence_ids(evidence_records: list[EvidenceContract]) -> list[UUID]:
    return sorted(
        [evidence.evidence_id for evidence in evidence_records],
        key=str,
    )


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
