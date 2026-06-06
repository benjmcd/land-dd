from __future__ import annotations

from collections.abc import Iterable


class UnsafeReportLanguageError(ValueError):
    """Raised when generated report text violates the product safety vocabulary."""


def assert_safe_report_text(
    text: str,
    forbidden_phrases: Iterable[str],
) -> None:
    text_lc = text.lower()
    matches = sorted(
        {
            phrase.strip()
            for phrase in forbidden_phrases
            if phrase.strip() and phrase.strip().lower() in text_lc
        }
    )
    if matches:
        raise UnsafeReportLanguageError(
            "report text contains forbidden language: "
            + ", ".join(repr(match) for match in matches)
        )


__all__ = ["UnsafeReportLanguageError", "assert_safe_report_text"]
