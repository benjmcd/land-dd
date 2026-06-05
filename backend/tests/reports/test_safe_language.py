from __future__ import annotations

import pytest

from app.reports.safe_language import UnsafeReportLanguageError, assert_safe_report_text


def test_assert_safe_report_text_blocks_forbidden_phrases_case_insensitively() -> None:
    with pytest.raises(UnsafeReportLanguageError, match="forbidden language"):
        assert_safe_report_text(
            "The generated text says this parcel has legal access.",
            {"This parcel has legal access."},
        )


def test_assert_safe_report_text_allows_cautious_screening_language() -> None:
    assert_safe_report_text(
        "Road proximity is a physical proxy only and does not establish recorded legal access.",
        {"This parcel has legal access."},
    )
