from __future__ import annotations

import json

from app.domain.report_contracts import ReportRunContract


def serialize_report_artifact(report_run: ReportRunContract) -> str:
    return json.dumps(report_run.model_dump(mode="json"), indent=2, sort_keys=True)


__all__ = ["serialize_report_artifact"]
