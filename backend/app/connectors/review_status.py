from __future__ import annotations

from dataclasses import dataclass

from .fixture_quality import ConnectorFixtureQualityProfile
from .review_handoff import (
    ConnectorReviewDisposition,
    ConnectorReviewHandoff,
)


@dataclass(frozen=True)
class ConnectorRunReviewStatus:
    handoff: ConnectorReviewHandoff
    quality_profile: ConnectorFixtureQualityProfile

    @property
    def review_required(self) -> bool:
        return (
            self.handoff.disposition == ConnectorReviewDisposition.NEEDS_HUMAN_REVIEW
            or not self.quality_profile.passed
        )

    def to_status_record(self) -> dict[str, object]:
        record = self.handoff.to_review_record()
        record["review_required"] = self.review_required
        record["quality"] = {
            "passed": self.quality_profile.passed,
            "evidence_count": self.quality_profile.evidence_count,
            "source_failure_count": self.quality_profile.source_failure_count,
            "blocking_issue_count": self.quality_profile.blocking_issue_count,
            "issues": tuple(
                {
                    "code": issue.code.value,
                    "message": issue.message,
                    "blocking": issue.blocking,
                }
                for issue in self.quality_profile.issues
            ),
        }
        return record


def build_connector_run_review_status(
    handoff: ConnectorReviewHandoff,
    quality_profile: ConnectorFixtureQualityProfile,
) -> ConnectorRunReviewStatus:
    if handoff.packet.connector_name != quality_profile.connector_name:
        raise ValueError("connector handoff and quality profile must use the same connector")
    return ConnectorRunReviewStatus(handoff=handoff, quality_profile=quality_profile)


__all__ = [
    "ConnectorRunReviewStatus",
    "build_connector_run_review_status",
]
