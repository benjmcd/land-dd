from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .review_packet import ConnectorRunReviewPacket


class ConnectorReviewDisposition(StrEnum):
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    READY_FOR_CONNECTOR_QA = "ready_for_connector_qa"
    IDEMPOTENT_NOOP = "idempotent_noop"


class ConnectorReviewPriority(StrEnum):
    NORMAL = "normal"
    HIGH = "high"


@dataclass(frozen=True)
class ConnectorReviewHandoff:
    queue_name: str
    disposition: ConnectorReviewDisposition
    priority: ConnectorReviewPriority
    title: str
    summary: str
    packet: ConnectorRunReviewPacket
    tasks: tuple[str, ...]
    signal_codes: tuple[str, ...]

    def to_review_record(self) -> dict[str, object]:
        return {
            "queue_name": self.queue_name,
            "disposition": self.disposition.value,
            "priority": self.priority.value,
            "title": self.title,
            "summary": self.summary,
            "connector_name": self.packet.connector_name,
            "ingest_run_id": str(self.packet.ingest_run_id),
            "area_id": (
                str(self.packet.area_id) if self.packet.area_id is not None else None
            ),
            "dataset_version_id": (
                str(self.packet.dataset_version_id)
                if self.packet.dataset_version_id is not None
                else None
            ),
            "retrieval_status": self.packet.retrieval_status.value,
            "review_required": self.packet.review_required,
            "evidence_created_count": self.packet.evidence_created_count,
            "evidence_skipped_count": self.packet.evidence_skipped_count,
            "source_failure_created_count": self.packet.source_failure_created_count,
            "source_failure_skipped_count": self.packet.source_failure_skipped_count,
            "signal_codes": self.signal_codes,
            "tasks": self.tasks,
        }


def build_connector_review_handoff(
    packet: ConnectorRunReviewPacket,
) -> ConnectorReviewHandoff:
    disposition = _disposition(packet)
    priority = (
        ConnectorReviewPriority.HIGH
        if disposition == ConnectorReviewDisposition.NEEDS_HUMAN_REVIEW
        else ConnectorReviewPriority.NORMAL
    )
    return ConnectorReviewHandoff(
        queue_name=_queue_name(disposition),
        disposition=disposition,
        priority=priority,
        title=_title(packet),
        summary=_summary(packet),
        packet=packet,
        tasks=packet.human_review_tasks,
        signal_codes=tuple(signal.code.value for signal in packet.signals),
    )


def _disposition(packet: ConnectorRunReviewPacket) -> ConnectorReviewDisposition:
    if packet.review_required:
        return ConnectorReviewDisposition.NEEDS_HUMAN_REVIEW
    if (
        packet.retrieval_skipped
        and packet.evidence_created_count == 0
        and packet.evidence_skipped_count > 0
    ):
        return ConnectorReviewDisposition.IDEMPOTENT_NOOP
    return ConnectorReviewDisposition.READY_FOR_CONNECTOR_QA


def _queue_name(disposition: ConnectorReviewDisposition) -> str:
    if disposition == ConnectorReviewDisposition.NEEDS_HUMAN_REVIEW:
        return "connector-human-review"
    if disposition == ConnectorReviewDisposition.IDEMPOTENT_NOOP:
        return "connector-idempotency-log"
    return "connector-quality-review"


def _title(packet: ConnectorRunReviewPacket) -> str:
    return (
        f"{packet.connector_name} {packet.retrieval_status.value} "
        f"run {str(packet.ingest_run_id)[:8]}"
    )


def _summary(packet: ConnectorRunReviewPacket) -> str:
    return (
        f"{packet.evidence_created_count} evidence created, "
        f"{packet.evidence_skipped_count} evidence skipped, "
        f"{packet.source_failure_created_count + packet.source_failure_skipped_count} "
        "source failures observed."
    )


__all__ = [
    "ConnectorReviewDisposition",
    "ConnectorReviewHandoff",
    "ConnectorReviewPriority",
    "build_connector_review_handoff",
]
