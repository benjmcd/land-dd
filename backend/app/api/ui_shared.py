"""Shared HTML/CSS helpers for the operator UI modules.

All four UI modules (ui, ui_review, ui_operations, ui_lineage) share:
- A base CSS block (body, h1, h2, table, th/td, a, .meta, .error-page)
- An error-page builder
- A reviewer-credential form-fields helper

Zero routes are defined here.
"""
from __future__ import annotations

import html as _html

from fastapi.responses import HTMLResponse

# ---------------------------------------------------------------------------
# Base CSS — common to every operator page
# ---------------------------------------------------------------------------

BASE_CSS = (
    "body { font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto;"
    " padding: 0 1rem; }\n"
    "h1 { color: #2c3e50; } h2 { color: #34495e; border-bottom: 1px solid #eee; }\n"
    "table { border-collapse: collapse; width: 100%; }\n"
    "th, td { text-align: left; padding: 0.5rem 1rem; border-bottom: 1px solid #dee2e6; }\n"
    "th { background: #f8f9fa; }\n"
    "a { color: #2c3e50; }\n"
    ".meta { background: #f8f9fa; padding: 1rem; border-radius: 4px;"
    " font-family: monospace; font-size: 0.9rem; }\n"
    ".error-page { background: #f8d7da; border: 1px solid #f5c6cb; padding: 1rem;"
    " border-radius: 4px; }\n"
)


def build_css(*extra: str) -> str:
    """Return BASE_CSS optionally followed by additional page-specific rules."""
    if extra:
        return BASE_CSS + "\n".join(extra)
    return BASE_CSS


# ---------------------------------------------------------------------------
# Error-page builder
# ---------------------------------------------------------------------------


def error_page(
    title: str,
    message: str,
    back_url: str,
    status_code: int,
    *,
    css: str = BASE_CSS,
) -> HTMLResponse:
    """Return a minimal HTML error page with the given title, message, and back link.

    The ``css`` parameter lets callers pass a page-specific stylesheet so the
    error page matches the surrounding UI.  Defaults to BASE_CSS.
    """
    body = (
        "<!DOCTYPE html><html lang='en'>"
        "<head><meta charset='UTF-8'>"
        f"<title>{_html.escape(title)}</title>"
        f"<style>{css}</style>"
        "</head><body>"
        f"<div class='error-page'><h1>{_html.escape(title)}</h1>"
        f"<p>{_html.escape(message)}</p>"
        f"<a href='{_html.escape(back_url)}'>Back</a>"
        "</div></body></html>"
    )
    return HTMLResponse(content=body, status_code=status_code)


# ---------------------------------------------------------------------------
# Reviewer-credential form fields
# ---------------------------------------------------------------------------


def reviewer_credential_fields() -> str:
    """Return the two reviewer-credential ``<input>`` elements used in action forms.

    Produces:
        <label>Reviewer ID: <input type="text" name="reviewer_id" required
            autocomplete="off"></label>
        <label>Reviewer token: <input type="password" name="reviewer_token" required
            autocomplete="off"></label>

    The caller is responsible for wrapping these in a ``<form>``.
    """
    return (
        "<label>Reviewer ID:"
        " <input type='text' name='reviewer_id' required autocomplete='off'></label>"
        "<label>Reviewer token:"
        " <input type='password' name='reviewer_token' required autocomplete='off'></label>"
    )
